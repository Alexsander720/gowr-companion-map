"""Read-only GoWR calibration; does NOT launch the game. Python standard library.

Offline: --diff s1.json s2.json s3.json
Live: --snapshot s1.json --phase still  (then move / turn in gameplay)
Interactive: no mode flag. 60-second total budget including prompts.

Three phases are settled observations: still >=2s, move 5-15 metres, then
rotate camera >=20 degrees in place and stop. Avoid menus/photo mode/cutscenes.
Behavior cannot by itself prove actor identity: output is a proposal until
the owner explicitly selects --confirm-position ID --confirm-yaw ID.
Yaw convention: +Z=0, +X=90, Y up (coordinate convention still needs live proof).
Exit codes: 0 snapshots/owner-confirmed export, 2 no match/ambiguity, 3 error.
"""
from __future__ import annotations

import argparse
import ast
import collections
import ctypes as C
from ctypes import wintypes as W
import hashlib
import difflib
import json
import math
import os
from pathlib import Path
import pprint
import queue
import struct
import sys
import threading
import time

if __package__:
    from .analyze_gowr_binary import PE, DEFAULT_EXE, DEFAULT_OUT
else:
    from analyze_gowr_binary import PE, DEFAULT_EXE, DEFAULT_OUT

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path: sys.path.insert(0, str(ROOT))
from paths import USER
SAFE_ACCESS_MASK = 0x0410
BUILD = (46685144,1750707527)
VERIFIED_OUT = USER / 'probe/gowr_verified_pointers.json'


def open_readonly(api,pid):
    handle=api.OpenProcess(SAFE_ACCESS_MASK,False,pid)
    if not handle:
        raise OSError('OpenProcess(0x0410) failed')
    return handle


def valid_pointer(value):
    return 0x10000<=value<=0x7fffffffffff and value%8==0


def valid_xyz(v):
    return len(v)==3 and all(math.isfinite(x) and abs(x)<=200000 for x in v) and any(abs(x)>1e-4 for x in v)


def yaw_forward(v):
    if len(v)!=3 or not all(math.isfinite(x) for x in v): return None
    norm=math.sqrt(sum(x*x for x in v))
    if not .85<=norm<=1.15 or math.hypot(v[0],v[2])<.1: return None
    return math.degrees(math.atan2(v[0],v[2]))%360


def yaw_quaternion(q):
    if len(q)!=4 or not all(math.isfinite(x) for x in q): return None
    n=sum(x*x for x in q)
    if not .95<=n<=1.05:return None
    x,y,z,w=(x/math.sqrt(n) for x in q)
    return yaw_forward((2*(x*z+w*y),2*(y*z-w*x),1-2*(x*x+y*y)))


def matrix_pose(m,layout):
    if len(m)!=16 or not all(math.isfinite(x) and abs(x)<=200000 for x in m):return None
    if layout.endswith('_column'):m=[m[r+4*c] for r in range(4) for c in range(4)]
    if max(abs(m[i]) for i in (3,7,11))>.02 or abs(m[15]-1)>.02:return None
    axes=[m[i:i+3] for i in (0,4,8)]
    if any(abs(sum(x*x for x in a)-1)>.05 for a in axes):return None
    if any(abs(sum(a*b for a,b in zip(axes[i],axes[j])))>.03 for i,j in ((0,1),(0,2),(1,2))):return None
    cross=(axes[0][1]*axes[1][2]-axes[0][2]*axes[1][1],axes[0][2]*axes[1][0]-axes[0][0]*axes[1][2],axes[0][0]*axes[1][1]-axes[0][1]*axes[1][0])
    if sum(a*b for a,b in zip(cross,axes[2]))<.95:return None
    pos=tuple(m[12:15]);forward=axes[2]
    if layout.startswith('view_'):
        # Invert rigid world->view: world translation = -t * transpose(R).
        pos=tuple(-sum(m[12+j]*axes[i][j] for j in range(3)) for i in range(3))
        forward=(m[2],m[6],m[10])
    yaw=yaw_forward(forward)
    return (pos,yaw) if valid_xyz(pos) and yaw is not None else None


def resolve(memory,start,chain):
    cur=start
    for offset in chain:
        raw=memory.read(cur,8)
        if len(raw)!=8:return None
        ptr=struct.unpack('<Q',raw)[0]
        if not valid_pointer(ptr):return None
        cur=ptr+offset
    return cur


def walk_graph(memory,base,roots,depth=4,window=1024,max_nodes=512,deadline=None):
    if not 0<=depth<=4:raise ValueError('depth must be 0..4')
    pending=collections.deque((r['rva'],[],base+r['rva']) for r in roots)
    seen=set();nodes=[];truncated=False
    while pending:
        if len(nodes)>=max_nodes or (deadline is not None and time.monotonic()>=deadline):
            truncated=True;break
        rva,chain,addr=pending.popleft()
        if addr in seen:continue
        seen.add(addr)
        raw=memory.read(addr,window)
        if not raw:continue
        nodes.append(dict(rva=rva,chain=chain,address=addr))
        if len(chain)==depth:continue
        for off in range(0,len(raw)-7,8):
            ptr=struct.unpack_from('<Q',raw,off)[0]
            if valid_pointer(ptr) and ptr not in seen:
                # Each chain offset is added AFTER its dereference, as gow_memory.resolve_chain.
                # Current address may contain the next pointer at off; fold off into previous offset.
                if chain:
                    child=chain[:-1]+[chain[-1]+off,0];root=rva
                else:
                    root=rva+off;child=[0]
                pending.append((root,child,ptr))
    return nodes,dict(nodes=len(nodes),truncated=truncated,pending=len(pending),depth=depth,window=window)


def field_id(f):
    return f"{f['rva']:x}:"+','.join(f'{x:x}' for x in f['chain'])+f":{f['offset']:x}:{f['kind']}"


def field_value(raw,off,kind):
    try:
        if kind=='xyz':
            v=struct.unpack_from('<3f',raw,off);return list(v) if valid_xyz(v) else None
        if kind in ('forward','forward_neg'):
            v=struct.unpack_from('<3f',raw,off)
            return yaw_forward(tuple(-x for x in v) if kind=='forward_neg' else v)
        if kind=='quaternion':return yaw_quaternion(struct.unpack_from('<4f',raw,off))
        if kind.startswith('matrix_'):
            v=matrix_pose(struct.unpack_from('<16f',raw,off),kind[7:])
            return dict(xyz=list(v[0]),yaw=v[1]) if v else None
    except struct.error:pass
    return None


def discover_fields(memory,nodes,window=1024,max_fields=40000,deadline=None):
    fields={}
    for n in nodes:
        if deadline is not None and time.monotonic()>=deadline:break
        raw=memory.read(n['address'],window)
        for off in range(0,len(raw)-11,4):
            for kind in ('xyz','forward','quaternion'):
                v=field_value(raw,off,kind)
                if v is not None:
                    f=dict(rva=n['rva'],chain=n['chain'],offset=off,kind=kind)
                    fields[field_id(f)]=f
            if off%16==0 and off+64<=len(raw):
                for layout in ('world_row','world_column','view_row','view_column'):
                    kind='matrix_'+layout
                    if field_value(raw,off,kind) is not None:
                        f=dict(rva=n['rva'],chain=n['chain'],offset=off,kind=kind)
                        fields[field_id(f)]=f
            if len(fields)>=max_fields:return fields
    return fields


def seed_fields(memory,base,inventory):
    fields={};nodes=[]
    for seed in inventory.get('semantic_seeds',[]):
        addr=resolve(memory,base+seed['rva'],seed['chain'])
        if addr is None:continue
        nodes.append(dict(rva=seed['rva'],chain=seed['chain'],address=addr,role=seed['role']))
        if 'position_offset' not in seed:continue
        if 'frame_chain' in seed:
            field={k:v for k,v in seed.items() if k not in ('evidence','note','status','position_offset')}
            field.update(offset=seed['position_offset'],kind='player_position')
            fields[field_id(field)]=field
            local=dict(rva=seed['rva'],chain=seed['chain'],offset=seed['position_offset'],kind='xyz',role='player_local_not_world')
            fields[field_id(local)]=local
            continue
        for kind,off in [('xyz',seed['position_offset']),('forward_neg' if seed['forward_sign']==-1 else 'forward',seed['forward_offset'])]:
            f=dict(rva=seed['rva'],chain=seed['chain'],offset=off,kind=kind,role=seed['role'])
            fields[field_id(f)]=f
    return fields,nodes


def scan_data_matrices(memory,base,sections,deadline,max_fields=1024):
    """16-byte aligned rigid matrices / listener pos+forward in writable image.

    Budgeted full .data including zero-fill; skips unreadable pages. No heap scan.
    Returns coverage explicitly: a partial scan never means absence of matrices.
    """
    fields={};scanned=0;requested=0;truncated=False;unreadable=0
    for s in sections:
        if s['name'] not in ('.data','.bss'):continue
        end=s['rva']+s['virtual_size']
        for rva in range(s['rva'],end,4096):
            if time.monotonic()>=deadline:return fields,dict(bytes_read=scanned,bytes_requested=requested,truncated=True,unreadable_pages=unreadable)
            size=min(4096+64,end-rva);requested+=size
            raw=memory.read(base+rva,size);scanned+=len(raw)
            if len(raw)<min(4096,end-rva):unreadable+=1
            for off in range(0,len(raw)-63,16):
                m=struct.unpack_from('<16f',raw,off)
                # Fast rejection of zero-filled BSS before more expensive validation.
                if abs(m[15]-1)>.02 or not math.isfinite(m[15]):continue
                for layout in ('world_row','world_column','view_row','view_column'):
                    if matrix_pose(m,layout):
                        f=dict(rva=rva+off,chain=[],offset=0,kind='matrix_'+layout)
                        fields[field_id(f)]=f
                # Listener contiguous padded position + forward hypothesis.
                # Independently scanned below even when no affine matrix exists.
                if len(fields)>=max_fields:truncated=True;break
            if len(fields)>=max_fields:break
            for off in range(0,len(raw)-31,16):
                if field_value(raw,off,'xyz') is not None and field_value(raw,off+16,'forward') is not None:
                    for k,o in [('xyz',off),('forward',off+16)]:
                        f=dict(rva=rva+off,chain=[],offset=o-off,kind=k)
                        fields[field_id(f)]=f
                    if len(fields)>=max_fields:truncated=True;break
            if truncated:break
    return fields,dict(bytes_read=scanned,bytes_requested=requested,truncated=truncated,unreadable_pages=unreadable)


def angle_delta(a,b):return abs((a-b+180)%360-180)


def phase_values(frames):
    # Filters feed one-key frame sequences; require complete reads, not survivors only.
    vals=[next(iter(f['values'].values()),None) for f in frames]
    if len(vals)<4 or frames[-1]['t']-frames[0]['t']<1.5 or any(v is None for v in vals):return None
    return vals


def position_behavior(phases,units_per_metre=1):
    values=[phase_values(f) for f in phases]
    if any(v is None for v in values):return {'pass':False,'reason':'missing/too few samples'}
    if not all(valid_xyz(v) for phase in values for v in phase):return {'pass':False,'reason':'invalid xyz'}
    centers=[tuple(sum(v[j] for v in vs)/len(vs) for j in range(3)) for vs in values]
    spreads=[max(math.dist(v,c) for v in vs)/units_per_metre for vs,c in zip(values,centers)]
    moved=math.dist(centers[0],centers[1])/units_per_metre
    orbit=math.dist(centers[1],centers[2])/units_per_metre
    return {'pass':max(spreads)<=.08 and 4<=moved<=20 and orbit<=.12,'moved_metres':moved,'turn_drift_metres':orbit,'spread_metres':spreads,'centers':centers}


def yaw_behavior(phases):
    values=[phase_values(f) for f in phases]
    if any(v is None for v in values) or not all(isinstance(v,(int,float)) and math.isfinite(v) for vs in values for v in vs):return {'pass':False,'reason':'invalid/missing yaw samples'}
    centers=[math.degrees(math.atan2(sum(math.sin(math.radians(x)) for x in vs),sum(math.cos(math.radians(x)) for x in vs)))%360 for vs in values]
    spread=[max(angle_delta(v,c) for v in vs) for vs,c in zip(values,centers)]
    rotation=angle_delta(centers[1],centers[2])
    return {'pass':max(spread)<=2 and 20<=rotation<=160,'turned_degrees':rotation,'spread_degrees':spread,'centers':centers}


def compare_snapshots(snaps,units_per_metre=1):
    if len(snaps)!=3:raise ValueError('requires three snapshots')
    for i,s in enumerate(snaps):
        if s.get('schema')!=1 or s.get('phase')!=('still','move','turn')[i] or not s.get('frames'):
            raise ValueError('snapshots need schema=1, phases still/move/turn, sample series')
        if tuple(s.get('build',()))!=BUILD or not s.get('process') or not s.get('fields'):
            raise ValueError('missing build/process/fields')
        times=[f['t'] for f in s['frames']]
        if not all(isinstance(t,(int,float)) and math.isfinite(t) and t>=0 for t in times) or any(a>=b for a,b in zip(times,times[1:])):
            raise ValueError('sample timestamps must be finite and strictly increasing')
        if not math.isfinite(s['captured_unix']):raise ValueError('invalid capture timestamp')
    if any(s['process']!=snaps[0]['process'] or s['binary_sha256']!=snaps[0]['binary_sha256'] or s['candidate_sha256']!=snaps[0]['candidate_sha256'] for s in snaps):
        raise ValueError('different process lifetime/build/candidate inventory')
    if any(snaps[i]['captured_unix']>=snaps[i+1]['captured_unix'] for i in (0,1)):
        raise ValueError('phase order is not chronological')
    if not math.isfinite(units_per_metre) or units_per_metre<=0:raise ValueError('invalid units per metre')
    common=set.intersection(*(set(s['fields']) for s in snaps));positions=[];yaws=[]
    non_world_addresses=set()
    for s in snaps:
        for key,f in s['fields'].items():
            if f.get('role') in ('camera_not_kratos','player_local_not_world') and f['kind']=='xyz':
                for frame in s['frames']:
                    address=frame.get('addresses',{}).get(key)
                    if isinstance(address,int):
                        # Sliding float3 windows can reuse only X/Y or Y/Z and still
                        # track a walk. They are aliases of the protected source too.
                        non_world_addresses.update(address+delta for delta in (-8,-4,0,4,8))
    for key in sorted(common):
        f=snaps[0]['fields'][key]
        if any(s['fields'][key]!=f for s in snaps):continue
        addresses=[frame.get('addresses',{}).get(key) for s in snaps for frame in s['frames']]
        if not all(isinstance(a,int) and a>=0x10000 for a in addresses) or len(set(addresses))!=1:continue
        components=('xyz','yaw') if f['kind'].startswith('matrix_') else (('xyz',) if f['kind']=='player_position' else (f['kind'],))
        if f['kind']=='player_position':
            guards=[frame.get('guards',{}).get(key) for s in snaps for frame in s['frames']]
            if any(not isinstance(g,dict) or g.get('mode') not in ('identity','cached_frame') or
                   not isinstance(g.get('frame_address'),int) or not valid_pointer(g['frame_address']) or
                   g.get('point_address')!=addresses[0] or not isinstance(g.get('kind'),int) or
                   (g['mode']=='cached_frame' and (not isinstance(g.get('stamp'),int) or g['stamp']<=0)) for g in guards):continue
            if len({(g['frame_address'],g['mode'],g['kind']) for g in guards})!=1:continue
        for component in components:
            if component=='xyz' and f.get('role') in ('camera_not_kratos','player_local_not_world'):continue
            if component=='xyz' and f['kind']!='player_position' and (addresses[0] in non_world_addresses or (f['kind']=='matrix_world_row' and addresses[0]+48 in non_world_addresses)):continue
            phases=[]
            for s in snaps:
                frames=[]
                for frame in s['frames']:
                    val=frame['values'].get(key)
                    if f['kind'].startswith('matrix_'):val=val.get(component) if isinstance(val,dict) else None
                    frames.append(dict(t=frame['t'],values={key:val}))
                phases.append(frames)
            result=position_behavior(phases,units_per_metre) if component=='xyz' else yaw_behavior(phases)
            if result['pass']:
                item=dict(id=key,field=f,behavior=result)
                if f['kind']=='player_position':
                    item['guards']=[frame['guards'][key] for s in snaps for frame in s['frames']]
                    modes={g.get('cache_freshness','identity') for g in item['guards']}
                    item['cache_freshness']='revision_chain_validated' if modes<={'identity','revision_chain_validated'} else 'not_independently_proven'
                (positions if component=='xyz' else yaws).append(item)
    positions.sort(key=lambda item:(item['field']['kind']!='player_position',item['id']))
    yaws.sort(key=lambda item:(item['field'].get('role')!='camera_not_kratos',item['field']['kind']!='forward_neg',item['id']))
    return dict(schema=1,status='behavioral_candidates_require_owner_identity_check',positions=positions,yaws=yaws,
                build=list(BUILD),binary_sha256=snaps[0]['binary_sha256'],process=snaps[0]['process'],
                units_per_metre=units_per_metre,coverage=[s.get('coverage',{}) for s in snaps],
                caveat='Three phases cannot exclude every NPC, camera pivot, UI value or mirrored transform. No automatic semantic verification.')


def loaded_header_key(buf):
    """SHA256 заголовка PE в форме, одинаковой для диска и загруженного модуля.

    Сырые 4096 байт в памяти не совпадут с файлом никогда: ASLR переписывает
    OptionalHeader.ImageBase, SteamStub (секция .bind) обнуляет её флаги, а
    после SizeOfHeaders на диске уже код секций, в памяти — нули. Сравниваем
    только [0, SizeOfHeaders) с обнулёнными ImageBase и флагами .bind.
    """
    b=bytearray(buf[:4096])
    if len(b)<0x200 or b[:2]!=b'MZ':return None
    pe=struct.unpack_from('<I',b,0x3c)[0]
    if pe+0x108>len(b) or b[pe:pe+4]!=b'PE\x00\x00':return None
    opt=pe+24;nsec=struct.unpack_from('<H',b,pe+6)[0];sopt=struct.unpack_from('<H',b,pe+20)[0]
    soh=struct.unpack_from('<I',b,opt+60)[0]
    if struct.unpack_from('<H',b,opt)[0]!=0x20b or not 0x200<=soh<=len(b):return None
    b[opt+24:opt+32]=bytes(8)
    for i in range(nsec):
        o=opt+sopt+40*i
        if o+40<=len(b) and bytes(b[o:o+8]).rstrip(b'\x00')==b'.bind':b[o+36:o+40]=bytes(4)
    return hashlib.sha256(bytes(b[:soh])).hexdigest()


def inventory_loaded_key(inventory):
    """Ключ загруженного заголовка из exe описи (только если файл тот же)."""
    try:
        head=Path(inventory['binary']['path']).read_bytes()[:4096]
    except (OSError,KeyError,TypeError):return None
    if hashlib.sha256(head).hexdigest()!=inventory['binary'].get('header_sha256'):return None
    return loaded_header_key(head)


def proposal(position,yaw,header_sha,loaded_key=None):
    p=position['field'];y=yaw['field']
    # Matrix translation is not always directly readable XYZ (view matrices need inverse).
    direct=p['kind']=='xyz' or p['kind']=='matrix_world_row'
    offset=p['offset']+(48 if p['kind']=='matrix_world_row' else 0)
    return dict(version='owner-calibrated XYZ/Yaw only',header_sha256=header_sha,loaded_header_key=loaded_key,module_name='GoWR.exe',
                kratos_anchor_offset=p['rva'],kratos_chain=p['chain'],
                offsets=dict(pos_x=offset,pos_y=offset+4,pos_z=offset+8) if direct else {},
                position_source=p,yaw_source=y,yaw_convention='+Z=0,+X=90,Y-up',
                integration_ready=False,
                integration_note='gow_memory currently also requires HP/rage fields and has no yaw reader. Do not retain guessed HP/rage/boss fields; consumer adaptation is a separate step.')


def read_configured_sample(reader,base,config):
    """Consumer adapter for a confirmed configuration. Never opens a process.

    A current header and current values are required on every call; no last-good
    point or unverified HP/rage fields are returned. Uses either read or read_raw.
    """
    unavailable=lambda reason:dict(available=False,reason=reason)
    if config.get('calibration_status')!='owner_confirmed_behavioral_chain':
        return unavailable('pointer calibration is not owner-confirmed')
    class Adapter:
        def read(self,address,size):
            method=getattr(reader,'read_raw',None) or getattr(reader,'read',None)
            return (method(address,size) or b'') if method else b''
    memory=Adapter()
    try:
        header=memory.read(base,4096)
        if len(header)!=4096 or not config.get('loaded_header_key') or loaded_header_key(header)!=config['loaded_header_key']:
            return unavailable('loaded module fingerprint differs from confirmed build')
        fields={'position':config['position_source'],'yaw':config['yaw_source']}
        guards={};values,addresses=read_fields(memory,base,fields,guards)
        point=values.get('position');yaw=values.get('yaw')
        if isinstance(point,dict):point=point.get('xyz')
        if isinstance(yaw,dict):yaw=yaw.get('yaw')
        if point is None or not valid_xyz(point) or not isinstance(yaw,(int,float)) or not math.isfinite(yaw):
            return unavailable('confirmed position/yaw sources are unreadable or invalid')
        if guards.get('position',{}).get('mode')=='cached_frame' and guards['position'].get('cache_freshness')!='revision_chain_validated':
            return unavailable('parent-frame cache freshness is unproven')
        return dict(available=True,reason='ok',xyz=list(point),yaw_deg=yaw%360,guards=guards,addresses=addresses)
    except (OSError,KeyError,TypeError,ValueError,struct.error):
        return unavailable('confirmed pointer source is unavailable or invalid')


def render_consumer_patch(source,config):
    """Generate (unified diff, patched source) in memory; never writes gow_memory.py.

    The patch replaces one known-build entry and adds a return branch before the
    old actor/HP reader, preserving the caller's fingerprint checks and finally.
    Refuses unknown source structure rather than guessing insertion locations.
    """
    tree=ast.parse(source);entry=None;function=None
    for node in tree.body:
        if isinstance(node,ast.FunctionDef) and node.name=='read_live_telemetry':function=node
        target=node.target if isinstance(node,ast.AnnAssign) else (node.targets[0] if isinstance(node,ast.Assign) and len(node.targets)==1 else None)
        if isinstance(target,ast.Name) and target.id=='KNOWN_BUILDS' and isinstance(node.value,ast.Dict):
            for key,value in zip(node.value.keys,node.value.values):
                try:matches=ast.literal_eval(key)==BUILD
                except (ValueError,TypeError):matches=False
                if matches:entry=value
    if entry is None or function is None:raise ValueError('consumer source lacks target known-build entry or reader function')
    anchors=[node for node in ast.walk(function) if isinstance(node,ast.Assign) and
             any(isinstance(target,ast.Name) and target.id=='anchor' for target in node.targets) and
             isinstance(node.value,ast.BinOp) and 'kratos_anchor_offset' in ast.unparse(node.value)]
    if len(anchors)!=1:raise ValueError('consumer source lacks a unique supported actor anchor')
    if any(isinstance(node,ast.Constant) and node.value=='probe_sources' for node in ast.walk(function)):
        raise ValueError('consumer source already has a probe branch; review instead of duplicating')
    raw=source.encode('utf-8');lines=raw.splitlines(keepends=True);starts=[0]
    for line in lines:starts.append(starts[-1]+len(line))
    entry_start=starts[entry.lineno-1]+entry.col_offset;entry_end=starts[entry.end_lineno-1]+entry.end_col_offset
    anchor=anchors[0];insert_at=starts[anchor.lineno-1]
    indent=' '*anchor.col_offset
    branch='''if build_cfg.get("probe_sources"):
    from tools.gow_live_pointer_probe import read_configured_sample
    sample = read_configured_sample(reader, reader.base_address, build_cfg)
    if not sample["available"]:
        res["reason"] = sample["reason"]
        return res
    x, y, z = sample["xyz"]
    radar = normalize_coordinates(active_realm, x, y, z)
    point = {"x": x, "y": y, "z": z, "yaw_deg": sample["yaw_deg"],
             "pct_x": radar.get("pct_x"), "pct_y": radar.get("pct_y")}
    res.update(available=True, reason="ok", radar=radar,
               position=dict(point), kratos=dict(point), combat=None,
               boss=None, cooldowns={}, source_guards=sample["guards"])
    return res

'''
    branch=''.join(indent+line+'\n' if line else '\n' for line in branch.splitlines())
    edits=[(entry_start,entry_end,pprint.pformat(config,sort_dicts=False,width=96).encode('utf-8')),
           (insert_at,insert_at,branch.encode('utf-8'))]
    for start,end,replacement in sorted(edits,reverse=True):raw=raw[:start]+replacement+raw[end:]
    patched=raw.decode('utf-8');ast.parse(patched)
    patch=''.join(difflib.unified_diff(source.splitlines(keepends=True),patched.splitlines(keepends=True),fromfile='a/gow_memory.py',tofile='b/gow_memory.py'))
    return patch,patched


class ReadOnlyProcess:
    def __init__(self,pid=None):
        if os.name!='nt' or C.sizeof(C.c_void_p)!=8:raise OSError('64-bit Windows Python required')
        self.api=C.WinDLL('kernel32',use_last_error=True);self.handle=None
        self.calls=0;self.bytes_read=0;self.failed_reads=0;self.deadline=None
        api=self.api
        api.OpenProcess.argtypes=[W.DWORD,W.BOOL,W.DWORD];api.OpenProcess.restype=W.HANDLE
        api.ReadProcessMemory.argtypes=[W.HANDLE,C.c_void_p,C.c_void_p,C.c_size_t,C.POINTER(C.c_size_t)];api.ReadProcessMemory.restype=W.BOOL
        api.CloseHandle.argtypes=[W.HANDLE];api.CloseHandle.restype=W.BOOL
        api.CreateToolhelp32Snapshot.argtypes=[W.DWORD,W.DWORD];api.CreateToolhelp32Snapshot.restype=W.HANDLE
        class ProcessEntry(C.Structure):
            _fields_=[('dwSize',W.DWORD),('cntUsage',W.DWORD),('th32ProcessID',W.DWORD),('th32DefaultHeapID',C.c_size_t),('th32ModuleID',W.DWORD),('cntThreads',W.DWORD),('th32ParentProcessID',W.DWORD),('pcPriClassBase',W.LONG),('dwFlags',W.DWORD),('szExeFile',W.WCHAR*260)]
        class ModuleEntry(C.Structure):
            _fields_=[('dwSize',W.DWORD),('th32ModuleID',W.DWORD),('th32ProcessID',W.DWORD),('GlblcntUsage',W.DWORD),('ProccntUsage',W.DWORD),('modBaseAddr',C.c_void_p),('modBaseSize',W.DWORD),('hModule',W.HMODULE),('szModule',W.WCHAR*256),('szExePath',W.WCHAR*260)]
        def inventory(flags,pid,entry,first,next_):
            fn=getattr(api,first);fn.argtypes=[W.HANDLE,C.POINTER(entry)];fn.restype=W.BOOL
            nxt=getattr(api,next_);nxt.argtypes=fn.argtypes;nxt.restype=W.BOOL
            snap=api.CreateToolhelp32Snapshot(flags,pid)
            if snap in (None,C.c_void_p(-1).value):raise OSError('Toolhelp snapshot failed')
            try:
                e=entry();e.dwSize=C.sizeof(e);ok=fn(snap,C.byref(e));result=[]
                while ok:
                    result.append(entry.from_buffer_copy(e));ok=nxt(snap,C.byref(e))
                return result
            finally:api.CloseHandle(snap)
        matches=[e.th32ProcessID for e in inventory(2,0,ProcessEntry,'Process32FirstW','Process32NextW') if e.szExeFile.lower()=='gowr.exe' and (pid is None or pid==e.th32ProcessID)]
        if len(matches)!=1:raise OSError(f'Expected one running GoWR.exe, found {len(matches)}. Game is never launched by this tool.')
        self.pid=matches[0]
        modules=inventory(8|16,self.pid,ModuleEntry,'Module32FirstW','Module32NextW')
        module=next((m for m in modules if m.szModule.lower()=='gowr.exe'),None)
        if module is None:raise OSError('GoWR.exe module not found')
        self.base=module.modBaseAddr;self.path=Path(module.szExePath);self.module_size=module.modBaseSize
        self.handle=open_readonly(api,self.pid)
        try:
            api.GetProcessTimes.argtypes=[W.HANDLE]+[C.POINTER(W.FILETIME)]*4;api.GetProcessTimes.restype=W.BOOL
            times=[W.FILETIME() for _ in range(4)]
            if not api.GetProcessTimes(self.handle,*(C.byref(t) for t in times)):raise OSError('GetProcessTimes failed')
            self.identity=dict(pid=self.pid,creation_time=(times[0].dwHighDateTime<<32)|times[0].dwLowDateTime,module_base=self.base)
        except BaseException:
            self.close();raise

    def read(self,address,size):
        if size<=0 or size>131072 or address<0x10000 or address+size>0x800000000000:return b''
        result=[];remaining=size
        while remaining:
            if self.calls>=100000 or self.bytes_read+remaining>256*1024*1024 or (self.deadline and time.monotonic()>=self.deadline):break
            chunk=min(remaining,4096-(address&4095))
            self.calls+=1;buf=C.create_string_buffer(chunk);got=C.c_size_t()
            ok=self.api.ReadProcessMemory(self.handle,C.c_void_p(address),buf,chunk,C.byref(got))
            self.bytes_read+=got.value
            if not ok:self.failed_reads+=1
            result.append(buf.raw[:got.value])
            if got.value!=chunk:break
            address+=chunk;remaining-=chunk
        # Return only a contiguous readable prefix. A hole never becomes zero-filled data.
        return b''.join(result)

    def close(self):
        if self.handle:self.api.CloseHandle(self.handle);self.handle=None

    def __enter__(self):return self
    def __exit__(self,*_):self.close()


def validate_parent_revisions(memory,frame,field):
    """Read-only counterpart of helper's revision checks; never takes its locks."""
    needed=('frame_lock_offset','ancestor_stamp_offset','ancestor_next_offset','ancestor_flags_offset','ancestor_byte_flags_offset','ancestor_lock_offset')
    if not all(key in field for key in needed):return None
    stamp_addr=frame+field['frame_stamp_offset'];stamp=memory.read(stamp_addr,16)
    frame_lock=frame+field['frame_lock_offset']
    if len(stamp)!=16 or memory.read(frame_lock,4)!=bytes(4):return None
    changed,computed=struct.unpack('<QQ',stamp)
    if computed==0 or computed<changed:return None
    link_addr=frame+field['frame_parent_offset'];first=memory.read(link_addr,8)
    if len(first)!=8:return None
    current=struct.unpack('<Q',first)[0];seen=set();observed=[]
    while current:
        if not valid_pointer(current) or current in seen or len(seen)>=16:return None
        seen.add(current)
        def take(offset,size):
            address=current+field[offset];data=memory.read(address,size)
            if len(data)!=size:return None
            observed.append((address,data));return data
        flags=take('ancestor_flags_offset',4);byte_flags=take('ancestor_byte_flags_offset',1);link=take('ancestor_next_offset',8)
        if flags is None or byte_flags is None or link is None:return None
        flags=struct.unpack('<I',flags)[0];next_node=struct.unpack('<Q',link)[0]
        # Same bypass used by the helper for flagged traversal links.
        bypass=bool(flags&(1<<29) and byte_flags[0]&8 and next_node)
        if not bypass:
            lock=take('ancestor_lock_offset',4);revision=take('ancestor_stamp_offset',16)
            if lock!=bytes(4) or revision is None or computed<struct.unpack_from('<Q',revision)[0]:return None
            if flags&(1<<30):break
        current=next_node
    if any(memory.read(address,len(data))!=data for address,data in observed):return None
    if memory.read(link_addr,8)!=first or memory.read(stamp_addr,16)!=stamp or memory.read(frame_lock,4)!=bytes(4):return None
    return dict(cache_freshness='revision_chain_validated',cache_revision=computed,ancestor_count=len(seen))


def read_player_position(memory,base,field):
    """Evaluate the statically derived point/frame expression without calling game code.

    Double-reads and the helper's own/ancestor revision predicates reject stale
    or torn cached frames. Final actor identity still requires owner calibration.
    """
    failure=(None,None,{})
    context=resolve(memory,base+field['rva'],field['chain'])
    frame=resolve(memory,base+field['rva'],field['frame_chain'])
    if context is None or frame is None:return failure
    point_addr=context+field['offset'];raw_point=memory.read(point_addr,16)
    raw_kind=memory.read(frame+field['frame_kind_offset'],4)
    if len(raw_point)!=16 or len(raw_kind)!=4:return failure
    point=struct.unpack('<4f',raw_point);kind=struct.unpack('<i',raw_kind)[0]
    if not all(math.isfinite(v) for v in point) or abs(point[3]-1)>.02:return failure
    guard=dict(mode='identity',frame_address=frame,kind=kind,point_address=point_addr)
    parent_addr=None;raw_parent=None;flag_addr=None;raw_flag=None;active=False
    if kind in (2,3,4):
        parent_addr=frame+field['frame_parent_offset' if kind in (2,3) else 'frame_other_parent_offset']
        raw_parent=memory.read(parent_addr,8)
        if len(raw_parent)!=8:return failure
        parent=struct.unpack('<Q',raw_parent)[0]
        if parent:
            if not valid_pointer(parent):return failure
            active=True
            if kind==4:
                flag_addr=parent+field['frame_other_flag_offset'];raw_flag=memory.read(flag_addr,1)
                if len(raw_flag)!=1:return failure
                active=bool(raw_flag[0]&1)
    stamp=None
    if active:
        stamp_size=16 if 'frame_lock_offset' in field else 8
        if stamp_size==16 and memory.read(frame+field['frame_lock_offset'],4)!=bytes(4):return failure
        stamp=memory.read(frame+field['frame_stamp_offset'],stamp_size)
        matrix=memory.read(frame+field['frame_matrix_offset'],64)
        if len(stamp)!=stamp_size or not any(stamp) or len(matrix)!=64:return failure
        m=struct.unpack('<16f',matrix)
        if not all(math.isfinite(v) and abs(v)<=200000 for v in m):return failure
        if any(abs(m[i])>.02 for i in (3,7,11)) or abs(m[15]-1)>.02:return failure
        det=m[0]*(m[5]*m[10]-m[6]*m[9])-m[1]*(m[4]*m[10]-m[6]*m[8])+m[2]*(m[4]*m[9]-m[5]*m[8])
        if abs(det)<1e-6:return failure
        xyz=tuple(sum(point[i]*m[4*i+j] for i in range(4)) for j in range(3))
        guard.update(mode='cached_frame',stamp=struct.unpack_from('<Q',stamp)[0],cache_freshness='not_proven')
        if stamp_size==16:
            checked=validate_parent_revisions(memory,frame,field)
            if checked is None:return failure
            guard.update(checked)
    else:xyz=point[:3]
    if not valid_xyz(xyz):return failure
    if memory.read(point_addr,16)!=raw_point or memory.read(frame+field['frame_kind_offset'],4)!=raw_kind:return failure
    if parent_addr is not None and memory.read(parent_addr,8)!=raw_parent:return failure
    if flag_addr is not None and memory.read(flag_addr,1)!=raw_flag:return failure
    if stamp is not None:
        if memory.read(frame+field['frame_stamp_offset'],len(stamp))!=stamp or memory.read(frame+field['frame_matrix_offset'],64)!=matrix:return failure
        if len(stamp)==16 and memory.read(frame+field['frame_lock_offset'],4)!=bytes(4):return failure
    if resolve(memory,base+field['rva'],field['chain'])!=context or resolve(memory,base+field['rva'],field['frame_chain'])!=frame:return failure
    return list(xyz),point_addr,guard


def read_fields(memory,base,fields,guards_out=None):
    groups=collections.defaultdict(list)
    values={};addresses={}
    for key,f in fields.items():
        if f['kind']=='player_position':
            value,addr,guard=read_player_position(memory,base,f)
            if value is not None:
                values[key]=value;addresses[key]=addr
                if guards_out is not None:guards_out[key]=guard
        else:groups[(f['rva'],tuple(f['chain']))].append((key,f))
    for (rva,chain),items in groups.items():
        addr=resolve(memory,base+rva,chain)
        if addr is None:continue
        size=max(f['offset']+(64 if f['kind'].startswith('matrix_') else 16) for _,f in items)
        raw=memory.read(addr,size)
        for key,f in items:
            v=field_value(raw,f['offset'],f['kind'])
            if v is not None:values[key]=v;addresses[key]=addr+f['offset']
    return values,addresses


def sample(memory,fields,seconds=2,interval=.4):
    frames=[];start=time.monotonic()
    while time.monotonic()-start<=seconds+.02:
        now=time.monotonic();guards={};v,addresses=read_fields(memory,memory.base,fields,guards)
        frames.append(dict(t=now-start,values=v,addresses=addresses,guards=guards))
        remaining=interval-(time.monotonic()-now)
        if remaining>0:time.sleep(min(remaining,max(0,seconds+.021-(time.monotonic()-start))))
        if memory.deadline and time.monotonic()>=memory.deadline:break
    return frames


def prompt_until(message,deadline):
    print(message,flush=True);result=queue.Queue()
    def get_input():
        try:result.put(input())
        except EOFError:result.put(None)
    threading.Thread(target=get_input,daemon=True).start()
    try:value=result.get(timeout=max(.01,deadline-time.monotonic()))
    except queue.Empty:raise TimeoutError('60-second session deadline while awaiting owner input')
    if value is None:raise ValueError('interactive mode needs terminal; use --snapshot for automation')


def write_json(path,value):
    path.parent.mkdir(parents=True,exist_ok=True)
    # JSON disallows NaN/Inf; consumers never have to guess how to parse them.
    path.write_text(json.dumps(value,ensure_ascii=False,indent=2,allow_nan=False),encoding='utf-8')


def export_comparison(args,snaps,inventory):
    inventory_sha=hashlib.sha256(args.candidates.read_bytes()).hexdigest()
    if any(s.get('binary_sha256')!=inventory['binary']['sha256'] or s.get('candidate_sha256')!=inventory_sha for s in snaps):
        raise ValueError('snapshot fingerprint differs from supplied candidate inventory')
    result=compare_snapshots(snaps,args.units_per_metre)
    if bool(args.confirm_position)!=bool(args.confirm_yaw):raise ValueError('confirm both position and yaw IDs together')
    if args.confirm_position:
        p=next((x for x in result['positions'] if x['id']==args.confirm_position),None)
        y=next((x for x in result['yaws'] if x['id']==args.confirm_yaw),None)
        if not p or not y:raise ValueError('selected IDs did not pass behavioral tests')
        result['config']=proposal(p,y,inventory['binary']['header_sha256'],inventory_loaded_key(inventory))
        result['config'].update(probe_sources=True,calibration_status='owner_confirmed_behavioral_chain',
                                integration_ready=True,integration_requires_patch=True,
                                integration_note='Apply the generated consumer patch after reviewing this live calibration; no consumer file was modified.')
        consumer_source=(ROOT/'gow_memory.py').read_text(encoding='utf-8')
        result['consumer_source_sha256']=hashlib.sha256(consumer_source.encode('utf-8')).hexdigest()
        try:
            patch,patched_source=render_consumer_patch(consumer_source,result['config'])
        except ValueError as exc:
            # Ветка probe_sources уже внедрена (повторная калибровка): новый
            # конфиг сохраняется, KNOWN_BUILDS обновляется вручную по выводу.
            if 'already has a probe branch' not in str(exc):raise
            patch,patched_source='',None
            result['config']['integration_requires_patch']=False
            result['config']['integration_note']='Consumer already has the probe branch; update KNOWN_BUILDS from this config.'
        result['consumer_patch']=patch or None
        result['consumer_patched_sha256']=hashlib.sha256(patched_source.encode('utf-8')).hexdigest() if patched_source else None
        result['status']='owner_confirmed_behavioral_chain'
        result['owner_confirmation']='Owner selected XYZ of Kratos and camera yaw after inspecting samples. Not independent semantic proof.'
        write_json(args.verified_out,result)
        print(f'KNOWN_BUILDS[{BUILD!r}] = '+pprint.pformat(result['config'],sort_dicts=False))
        if patch:print(patch)
        print(f'Saved owner-confirmed calibration: {args.verified_out}')
        return 0
    write_json(args.result,result)
    print(json.dumps(dict(status=result['status'],position_count=len(result['positions']),yaw_count=len(result['yaws']),positions=[x['id'] for x in result['positions'][:20]],yaws=[x['id'] for x in result['yaws'][:20]],result=str(args.result)),indent=2))
    if len(result['positions'])==len(result['yaws'])==1:
        print('PROPOSAL ONLY; owner identity confirmation required:')
        print(f'KNOWN_BUILDS[{BUILD!r}] = '+pprint.pformat(proposal(result['positions'][0],result['yaws'][0],inventory['binary']['header_sha256'],inventory_loaded_key(inventory)),sort_dicts=False))
    return 2


def main(argv=None):
    ap=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
    mode=ap.add_mutually_exclusive_group();mode.add_argument('--snapshot',type=Path);mode.add_argument('--diff',nargs=3,type=Path)
    ap.add_argument('--phase',choices=['still','move','turn'],default='still')
    ap.add_argument('--candidates',type=Path,default=DEFAULT_OUT);ap.add_argument('--pid',type=int)
    ap.add_argument('--depth',type=int,choices=range(5),default=4);ap.add_argument('--window',type=int,default=1024)
    ap.add_argument('--max-nodes',type=int,default=512);ap.add_argument('--max-roots',type=int,default=256)
    ap.add_argument('--units-per-metre',type=float,default=1);ap.add_argument('--seconds',type=float,default=2)
    ap.add_argument('--reuse',type=Path,help='reuse first snapshot field inventory; recommended for phase 2 and 3')
    ap.add_argument('--result',type=Path,default=USER / 'probe/result.json')
    ap.add_argument('--session-dir',type=Path,default=USER / 'probe/session')
    ap.add_argument('--verified-out',type=Path,default=VERIFIED_OUT)
    ap.add_argument('--confirm-position');ap.add_argument('--confirm-yaw')
    global BUILD
    args=ap.parse_args(argv)
    if not 64<=args.window<=8192 or not 1<=args.max_nodes<=4096 or not 1<=args.max_roots<=4096 or not 2<=args.seconds<=5:ap.error('window 64..8192; max-nodes/roots 1..4096; seconds 2..5')
    if not math.isfinite(args.units_per_metre) or args.units_per_metre<=0:ap.error('units-per-metre must be finite and positive')
    try:
        inventory=json.loads(args.candidates.read_text(encoding='utf-8'))
        BUILD = (inventory['binary']['size'], inventory['binary']['timestamp'])
        if args.diff:
            snaps=[json.loads(p.read_text(encoding='utf-8')) for p in args.diff]
            return export_comparison(args,snaps,inventory)
        deadline=time.monotonic()+60
        with ReadOnlyProcess(args.pid) as memory:
            disk=memory.path.read_bytes();pe=PE(disk);sha=hashlib.sha256(disk).hexdigest()
            if (len(disk),pe.timestamp)!=BUILD or sha!=inventory['binary']['sha256'] or memory.module_size!=pe.image_size:raise ValueError('running module/disk/candidates build mismatch')
            hdr=memory.read(memory.base,4096)
            if (len(hdr)!=4096 or hashlib.sha256(disk[:4096]).hexdigest()!=inventory['binary']['header_sha256']
                    or loaded_header_key(hdr) is None or loaded_header_key(hdr)!=loaded_header_key(disk[:4096])):raise ValueError('loaded module header differs from inventory')
            memory.deadline=deadline
            coverage={}
            if args.reuse:
                prev=json.loads(args.reuse.read_text(encoding='utf-8'))
                if prev['process']!=memory.identity or prev['binary_sha256']!=sha or prev['candidate_sha256']!=hashlib.sha256(args.candidates.read_bytes()).hexdigest():raise ValueError('reuse from different process/build/inventory')
                fields=prev['fields'];coverage=dict(reused=str(args.reuse))
            else:
                # Work budget reserves time for sampling and owner movement.
                roots=inventory['candidates'][:args.max_roots]
                nodes,coverage['graph']=walk_graph(memory,memory.base,roots,args.depth,args.window,args.max_nodes,min(deadline,time.monotonic()+5))
                seeded,seed_nodes=seed_fields(memory,memory.base,inventory)
                nodes=seed_nodes+nodes
                fields=discover_fields(memory,nodes,args.window,deadline=min(deadline,time.monotonic()+5))
                extra,coverage['data_scan']=scan_data_matrices(memory,memory.base,inventory['sections'],min(deadline,time.monotonic()+6))
                fields.update(extra);fields.update(seeded);coverage['fields']=len(fields)
                coverage['semantic_seeds_resolved']=len(seed_nodes)
                coverage['fields_potentially_truncated']=len(fields)>=40000
            def take(phase):
                captured=time.time();frames=sample(memory,fields,args.seconds)
                return dict(schema=1,phase=phase,build=list(BUILD),binary_sha256=sha,candidate_sha256=hashlib.sha256(args.candidates.read_bytes()).hexdigest(),
                            captured_unix=captured,process=memory.identity,fields=fields,frames=frames,coverage=coverage,
                            io=dict(read_calls=memory.calls,bytes_read=memory.bytes_read,failed_reads=memory.failed_reads),access_mask=SAFE_ACCESS_MASK)
            if args.snapshot:
                snap=take(args.phase);write_json(args.snapshot,snap)
                print(json.dumps(dict(saved=str(args.snapshot),phase=args.phase,fields=len(fields),frames=len(snap['frames']),coverage=coverage,io=snap['io']),indent=2))
                return 0 if fields and len(snap['frames'])>=4 and snap['frames'][-1]['t']-snap['frames'][0]['t']>=1.5 else 2
            snaps=[]
            instructions=['Фаза 1: стойте на месте, камеру не трогайте. Enter — снять 2 секунды.',
                          'Фаза 2: пройдите 5–15 м, остановитесь, камеру не вращайте. Enter — снимок.',
                          'Фаза 3: Кратос стоит. Поверните камеру на 20–160 градусов и отпустите стик. Enter — снимок.']
            for phase,message in zip(('still','move','turn'),instructions):
                prompt_until(message,deadline-args.seconds)
                snap=take(phase);snaps.append(snap);write_json(args.session_dir/f'{phase}.json',snap)
            return export_comparison(args,snaps,inventory)
    except (OSError,ValueError,KeyError,TimeoutError,struct.error) as exc:
        print(f'PROBE ERROR: {exc}',file=sys.stderr);return 3


if __name__=='__main__':
    raise SystemExit(main())
