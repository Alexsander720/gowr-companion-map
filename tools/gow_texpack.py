"""Read-only extractor of God of War Ragnarok (PC) textures from *.texpack.

The PC port keeps the PS5 data layout: every texture is a GNF v4 header plus a
256 KiB-page tiled payload stored *uncompressed* in exec/wad/pc_le/*.texpack.
A WAD texture entry `TX_<name>_<HASH16>` names the texture by that 64-bit hash.

Format reference (independently checked here against the installed files):
https://github.com/MorseTheCode/GodOfWarTool/blob/main/gow_unified_backend.py
(GowRagnarok_Texpack, _build_ragnarok_gnf, _convert_ps5_gnf_to_dds).
Nothing is written to the game directory; only numpy + Pillow are needed.
"""
from __future__ import annotations

from functools import lru_cache
import io
import json
import struct
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import wad_dir
TEXPACK_DIR = wad_dir()
NO_BLOCK = 0xFFFFFFFFFFFFFFFF

# GNF format id -> (dxgi, bytes per block, block w, block h)
PS5_FORMATS = {
    7: (56, 2, 1, 1), 8: (58, 2, 1, 1), 13: (54, 2, 1, 1),
    65: (11, 8, 1, 1), 66: (13, 8, 1, 1), 71: (10, 8, 1, 1),
    169: (71, 8, 4, 4), 170: (72, 8, 4, 4), 171: (74, 16, 4, 4), 172: (75, 16, 4, 4),
    173: (77, 16, 4, 4), 174: (78, 16, 4, 4), 175: (80, 8, 4, 4), 176: (81, 8, 4, 4),
    177: (83, 16, 4, 4), 178: (84, 16, 4, 4), 179: (95, 16, 4, 4), 180: (96, 16, 4, 4),
    181: (98, 16, 4, 4), 182: (99, 16, 4, 4),
}
DXGI_NAMES = {56: 'R16_UNORM', 58: 'R16_SNORM', 54: 'R16_FLOAT', 11: 'R16G16B16A16_UNORM',
              13: 'R16G16B16A16_SNORM', 10: 'R16G16B16A16_FLOAT', 71: 'BC1', 72: 'BC1_SRGB',
              74: 'BC2', 75: 'BC2_SRGB', 77: 'BC3', 78: 'BC3_SRGB', 80: 'BC4', 81: 'BC4_SNORM',
              83: 'BC5', 84: 'BC5_SNORM', 95: 'BC6H_UF16', 96: 'BC6H_SF16', 98: 'BC7',
              99: 'BC7_SRGB'}


def texture_hash(name):
    return int(name.rsplit('_', 1)[1], 16)


def _read_blocks(f, first, table_start, count):
    table_end = table_start + count * 32
    blocks, seen, cur = [], set(), first
    while cur != NO_BLOCK and cur not in seen:
        if not table_start <= cur <= table_end - 32:
            return []
        seen.add(cur)
        f.seek(cur)
        v = struct.unpack('<IIQBBHHHQ', f.read(32))
        blocks.insert(0, dict(block_offset=v[0], raw_size=v[1], block_size=v[2], mip_start=v[3],
                              mip_end=v[4], toc_index=v[5], width=v[6], height=v[7]))
        cur = v[8]
    return blocks


@lru_cache(maxsize=2)
def _texpack_toc_index(dir_str: str, stamp: tuple) -> dict[int, tuple[str, int, int, int]]:
    """Build an in-memory hash -> (pack_path, first_block, block_table, block_count) index."""
    index: dict[int, tuple[str, int, int, int]] = {}
    packs = sorted(Path(dir_str).glob('*.texpack'), key=lambda p: (p.name != 'root.texpack', p.name))
    for pack in packs:
        pack_str = str(pack)
        with pack.open('rb') as f:
            f.seek(0x20)
            _, block_count, block_table, tex_count = struct.unpack('<IIII', f.read(16))
            f.seek(0x38)
            table = f.read(tex_count * 24)
            for h, _user, first in struct.iter_unpack('<QQQ', table):
                if h not in index:
                    index[h] = (pack_str, first, block_table, block_count)
    return index


def find_textures(hashes, texpack_dir=None):
    texpack_dir = Path(texpack_dir) if texpack_dir else wad_dir()
    """hash -> {'texpack': path, 'blocks': [...]} for the first texpack holding it."""
    wanted = set(hashes)
    if not wanted or not texpack_dir.is_dir():
        return {}
    packs = sorted(texpack_dir.glob('*.texpack'), key=lambda p: (p.name != 'root.texpack', p.name))
    if not packs:
        return {}
    stamp = tuple((p.name, p.stat().st_size, p.stat().st_mtime_ns) for p in packs)
    index = _texpack_toc_index(str(texpack_dir), stamp)
    by_pack: dict[str, list[tuple[int, int, int, int]]] = {}
    for h in wanted:
        rec = index.get(h)
        if rec:
            pack_str, first, block_table, block_count = rec
            by_pack.setdefault(pack_str, []).append((h, first, block_table, block_count))
    found = {}
    for pack_str, items in by_pack.items():
        pack = Path(pack_str)
        with pack.open('rb') as f:
            for h, first, block_table, block_count in items:
                blocks = _read_blocks(f, first, block_table, block_count)
                if blocks:
                    found[h] = dict(texpack=pack, blocks=blocks)
    return found


def build_gnf(entry):
    blocks = sorted(entry['blocks'], key=lambda b: (b['mip_start'], b['mip_end'],
                                                     b['width'] * b['height'], b['block_offset']))
    with entry['texpack'].open('rb') as f:
        header_block = None
        for b in blocks:
            f.seek((b['block_offset'] << 4) + 4)
            if struct.unpack('<I', f.read(4))[0] != 0x20:
                header_block = b
                break
        if header_block is None:
            raise ValueError('GNF header block not found')
        base = header_block['block_offset'] << 4
        f.seek(base + 4)
        header_payload = struct.unpack('<I', f.read(4))[0]
        f.seek(base + 16)
        header = bytearray(f.read(0x100))
        if header[:4] != b'GNF ':
            raise ValueError('Invalid GNF header')
        parts = []
        for b in blocks:
            bb = b['block_offset'] << 4
            f.seek(bb + 4)
            p0, p1 = struct.unpack('<II', f.read(8))
            size = b['raw_size']
            if p1 > p0:
                size = min(size, p1 - p0)
            f.seek(bb + p0)
            parts.append(f.read(size))
    payload = b''.join(parts)
    file_size = struct.unpack_from('<I', header, 0x0C)[0]
    data_size = struct.unpack_from('<I', header, 0x2C)[0]
    payload_offset = file_size - data_size if file_size > data_size else 0x100
    largest = max(blocks, key=lambda b: b['width'] * b['height'])
    if largest['width'] and largest['height']:
        sw = largest['width'] - 1
        fw = struct.unpack_from('<I', header, 0x14)[0]
        dw = struct.unpack_from('<I', header, 0x18)[0]
        fw = (fw & ~0x000FFFFF) | 0xC
        fw = (fw & ~(0x3 << 30)) | ((sw & 0x3) << 30)
        dw = (dw & ~0xFFF) | ((sw >> 2) & 0xFFF)
        dw = (dw & ~(0x3FFF << 14)) | (((largest['height'] - 1) & 0x3FFF) << 14)
        struct.pack_into('<I', header, 0x14, fw & 0xFFFFFFFF)
        struct.pack_into('<I', header, 0x18, dw & 0xFFFFFFFF)
    size = max(file_size, payload_offset + len(payload))
    struct.pack_into('<I', header, 0x0C, size)
    out = bytearray(size)
    out[:0x100] = header
    out[payload_offset:payload_offset + len(payload)] = payload
    return bytes(out)


def gnf_info(gnf):
    fw, dw, mw = struct.unpack_from('<III', gnf, 0x14)
    fmt = (fw >> 20) & 0x1FF
    return dict(format=fmt, dxgi=PS5_FORMATS.get(fmt, (None,))[0],
                width=(((dw & 0xFFF) << 2) | ((fw >> 30) & 3)) + 1,
                height=((dw >> 14) & 0x3FFF) + 1, mips=((mw >> 16) & 0xF) + 1)


def _align(v, a):
    return (v + a - 1) & ~(a - 1)


def _tile_offsets(columns, rows, bpb):
    x = np.arange(columns, dtype=np.uint64)[None, :]
    y = np.arange(rows, dtype=np.uint64)[:, None]
    if bpb == 8:
        pw, ph = 32, 16
        lx, ly = x & 31, y & 15
        el = ((lx & 1) | ((ly & 1) << 1) | (((ly >> 1) & 1) << 2) | (((lx >> 1) & 1) << 3)
              | (((lx >> 2) & 1) << 4) | (((ly >> 2) & 1) << 5) | (((lx >> 3) & 1) << 6)
              | (((ly >> 3) & 1) << 7) | (((lx >> 4) & 1) << 8))
    else:
        pw, ph = 16, 16
        lx, ly = x & 15, y & 15
        el = ((ly & 1) | (((ly >> 1) & 1) << 1) | ((lx & 1) << 2) | (((lx >> 1) & 1) << 3)
              | (((ly >> 2) & 1) << 4) | (((lx >> 2) & 1) << 5) | (((ly >> 3) & 1) << 6)
              | (((lx >> 3) & 1) << 7))
    page_cols = (columns + pw - 1) // pw
    return ((y // ph) * page_cols + x // pw) * 4096 + el * bpb


def top_mip_linear(gnf):
    """Return (info, linear top-mip bytes) after PS5 detiling."""
    info = gnf_info(gnf)
    if info['format'] not in PS5_FORMATS:
        raise ValueError(f"Unsupported GNF format {info['format']}")
    _, bpb, bw, bh = PS5_FORMATS[info['format']]
    w, h, mips = info['width'], info['height'], info['mips']
    file_size = struct.unpack_from('<I', gnf, 0x0C)[0]
    data_size = struct.unpack_from('<I', gnf, 0x2C)[0]
    start = file_size - data_size if file_size > data_size else gnf[4] + 8
    tiled = np.frombuffer(gnf[start:start + data_size], dtype=np.uint8)
    sizes = []
    for m in range(mips):
        cols = _align(max(w >> m, 1), bw) // bw
        rows = _align(max(h >> m, 1), bh) // bh
        micro = 8 if bpb == 8 else 4 if bpb == 16 else 8
        sizes.append(_align(((cols + micro - 1) // micro) * rows * micro * bpb, 256))
    tail = mips - 1
    for m in range(mips):
        if max(max(w >> m, 1), max(h >> m, 1)) <= 512:
            tail = m
            break
    offs = [0] * mips
    po = 0x200 if bpb == 16 else 0x100
    for m in range(mips - 1, tail - 1, -1):
        if po and sizes[m] >= 0x400:
            po = _align(po, min(sizes[m], 0x1000))
        offs[m] = po
        po += sizes[m]
    po = _align(po, 0x1000)
    for m in range(tail - 1, -1, -1):
        offs[m] = po
        po += sizes[m]
    cols = _align(w, bw) // bw
    rows = _align(h, bh) // bh
    idx = offs[0] + _tile_offsets(cols, rows, bpb)[..., None] + np.arange(bpb, dtype=np.uint64)
    valid = idx < tiled.size
    out = np.zeros(idx.shape, dtype=np.uint8)
    out[valid] = tiled[idx[valid]]
    return info, out.tobytes(), float(valid.mean())


def _dds(width, height, dxgi, linear):
    hdr = bytearray(b'DDS ')
    hdr += struct.pack('<7I11I', 124, 0x000A1007, height, width, len(linear), 0, 1, *([0] * 11))
    hdr += struct.pack('<II4s5I', 32, 4, b'DX10', 0, 0, 0, 0, 0)
    hdr += struct.pack('<5I', 0x1000, 0, 0, 0, 0)
    hdr += struct.pack('<5I', dxgi, 3, 0, 1, 0)
    return bytes(hdr) + linear


def decode(gnf):
    """-> (info, numpy array). R16 formats give uint16/float HxW; BCn give RGBA uint8."""
    info, linear, coverage = top_mip_linear(gnf)
    info['payload_coverage'] = coverage
    dxgi, w, h = info['dxgi'], info['width'], info['height']
    if dxgi == 56:
        return info, np.frombuffer(linear, '<u2').reshape(h, w)
    if dxgi == 58:
        return info, np.frombuffer(linear, '<i2').reshape(h, w)
    if dxgi == 54:
        return info, np.frombuffer(linear, '<f2').reshape(h, w).astype(np.float32)
    if dxgi in (10, 11, 13):
        dt = {10: '<f2', 11: '<u2', 13: '<i2'}[dxgi]
        return info, np.frombuffer(linear, dt).reshape(h, w, 4)
    if dxgi in (95, 96):
        try:
            import imagecodecs
        except ImportError:
            decoder_dir = Path(__file__).resolve().parents[1] / 'cache' / 'decoder'
            if decoder_dir.is_dir() and str(decoder_dir) not in sys.path:
                sys.path.insert(0, str(decoder_dir))
            import imagecodecs
        return info, imagecodecs.bcn_decode(linear, 6 if dxgi == 95 else -6,
                                            shape=(h, w, 3)).astype(np.float32)
    from PIL import Image
    srgb_free = {72: 71, 75: 74, 78: 77, 99: 98}.get(dxgi, dxgi)  # same bits, Pillow lacks *_SRGB
    img = Image.open(io.BytesIO(_dds(w, h, srgb_free, linear)))
    img.load()
    return info, np.asarray(img)


def extract(names, texpack_dir=None):
    hashes = {texture_hash(n): n for n in names}
    found = find_textures(hashes, texpack_dir)
    result = {}
    for h, n in hashes.items():
        if h not in found:
            result[n] = None
            continue
        gnf = build_gnf(found[h])
        info, arr = decode(gnf)
        info.update(texpack=found[h]['texpack'].name, dxgi_name=DXGI_NAMES.get(info['dxgi']))
        result[n] = (info, arr)
    return result


if __name__ == '__main__':
    for n, r in extract(sys.argv[1:]).items():
        print(n, None if r is None else json.dumps({k: v for k, v in r[0].items()}),
              None if r is None else (r[1].shape, str(r[1].dtype)))
