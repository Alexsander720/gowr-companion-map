"""All tests use synthetic local files; real game/saves and external network are disabled."""
import os
from pathlib import Path
import tempfile
import pytest

_user = tempfile.TemporaryDirectory(prefix='gowr-tests-')
os.environ['GOWR_DATA_DIR'] = _user.name
import paths
paths.GAME_DIR = Path(_user.name) / 'absent-game'


@pytest.fixture(autouse=True)
def isolate(monkeypatch, tmp_path):
    import urllib.request
    def forbidden(*args, **kwargs):
        raise AssertionError('External network is forbidden in tests')
    monkeypatch.setattr(urllib.request, 'urlopen', forbidden)
    monkeypatch.setattr(paths, 'GAME_DIR', tmp_path / 'absent-game')
    from gow_story import load_story_strings
    load_story_strings.cache_clear()
    import gow_pins
    monkeypatch.setattr(gow_pins, 'PINS', tmp_path / 'pins')
    gow_pins.PINS.mkdir()
    gow_pins._read_cached.cache_clear()
    yield
    load_story_strings.cache_clear()


@pytest.fixture
def synthetic_map():
    return {'maps': [{'id': 473, 'slug': 'midgard'}], 'map': {'id': 473, 'slug': 'midgard'},
            'regions': [], 'locations': [
                {'id': 1, 'category_id': 7100, 'title': 'Synthetic bird', 'latitude': '0.7', 'longitude': '-0.7',
                 'description': 'See [Synthetic cache [2]](https://mapgenie.io/test?locationIds=2)'},
                {'id': 2, 'category_id': 7107, 'title': 'Synthetic cache', 'latitude': '0.71', 'longitude': '-0.69',
                 'description': None},
            ]}
