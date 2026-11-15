from pathlib import Path
from tools.check_clean import inspect_file, check


def test_tracked_release_is_clean():
    files,issues=check()
    assert files, 'Stage files before checking the public release'
    assert issues == []


def test_scanner_detects_private_material():
    samples=[('x.py', ('Z'+':/private/a').encode()),
             ('x.txt', ('ban'+'13').encode()),
             ('x.txt', ('7656'+'0000000000001').encode()),
             ('x.txt', ('gh'+'o_'+'a'*25).encode()),
             ('cache/pins/midgard.json',b'{}'),('data/ru_names.json',b'{}'),
             ('data/favors_map.json',b'{"description":"borrowed prose"}')]
    for name,content in samples:
        assert inspect_file(name,content), name


def test_geometry_and_approved_screenshot_are_allowed():
    assert inspect_file('data/own.json',b'{"matrix":[[0.12345678901234567,1,2]]}') == []
    assert inspect_file('docs/screenshot.png',b'PNG application screenshot') == []


def test_png_metadata_is_scanned_but_compressed_pixels_are_not_text():
    import io
    from PIL import Image, PngImagePlugin
    metadata=PngImagePlugin.PngInfo();metadata.add_text('description','Q'+':/private')
    data=io.BytesIO();Image.new('RGB',(8,8)).save(data,'PNG',pnginfo=metadata)
    assert 'absolute Windows path' in inspect_file('docs/screenshot.png',data.getvalue())
    safe=io.BytesIO();Image.new('RGB',(8,8)).save(safe,'PNG')
    assert inspect_file('docs/screenshot.png',safe.getvalue()) == []
    assert inspect_file('docs/screenshot.png',safe.getvalue()+b'trailing')
    metadata=PngImagePlugin.PngInfo();metadata.add_itxt('key','safe',tkey='Q'+':/private')
    data=io.BytesIO();Image.new('RGB',(8,8)).save(data,'PNG',pnginfo=metadata)
    assert 'absolute Windows path' in inspect_file('docs/screenshot.png',data.getvalue())
