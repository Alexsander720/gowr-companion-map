"""Download public map data once per realm. No login, challenge solving or retries.

The current website loads /api/v1/maps/<id>/data from its public client.
Older pages contain window.mapData; parse_embedded also supports those exports.
Downloaded material belongs exclusively in the user's cache.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
import time
import urllib.error
import urllib.request

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from paths import PINS, atomic_json

MAP_IDS = {'sindris-house': 468, 'vanaheim': 469, 'alfheim': 470, 'niflheim': 471,
           'muspelheim': 472, 'midgard': 473, 'svartalfheim': 474, 'jotunheim': 475,
           'helheim': 476, 'asgard': 482}
USER_AGENT = 'gowr-companion-map/0.1 (local fan companion)'
REQUIRED = {'map', 'maps', 'regions', 'locations'}


def validate(data, realm=None):
    if not isinstance(data, dict) or not REQUIRED <= data.keys():
        raise ValueError('Map data schema changed')
    if not isinstance(data['locations'], list) or not isinstance(data['maps'], list):
        raise ValueError('Invalid map data lists')
    if not isinstance(data['map'], dict):
        raise ValueError('Invalid map identity')
    if realm and (data['map'].get('slug') != realm or data['map'].get('id') != MAP_IDS[realm]):
        raise ValueError('Response belongs to a different realm')
    for p in data['locations']:
        if not isinstance(p, dict) or not {'id', 'latitude', 'longitude'} <= p.keys():
            raise ValueError('Invalid location')
        try:
            lat, lng = float(p['latitude']), float(p['longitude'])
        except (ValueError, TypeError) as exc:
            raise ValueError('Invalid location coordinates') from exc
        if not (-90 <= lat <= 90 and -180 <= lng <= 180):
            raise ValueError('Invalid location coordinates')
    return data


def parse_embedded(html):
    """Decode JSON without evaluating any JavaScript from a remote page."""
    match = re.search(r'(?:window\.)?mapData\s*=\s*', html)
    if not match:
        raise ValueError('No embedded map data')
    data, _ = json.JSONDecoder().raw_decode(html[match.end():])
    return validate(data)


def fetch_realm(realm, cache_dir=None, opener=None):
    if realm not in MAP_IDS:
        raise ValueError('Unknown realm')
    root = Path(cache_dir or PINS)
    target = root / (realm + '.json')
    if target.is_file():
        return validate(json.loads(target.read_text(encoding='utf-8')), realm)
    # Record failures too: normal launches do not hammer a blocked upstream.
    status_file = root / (realm + '.status.json')
    if status_file.is_file():
        status = json.loads(status_file.read_text(encoding='utf-8'))
        if not isinstance(status, dict):
            raise ValueError('Invalid download status marker; use --retry')
        if not status.get('retry_requested'):
            raise ValueError('Previous download failed; use --retry after checking connectivity')
    url = f'https://mapgenie.io/api/v1/maps/{MAP_IDS[realm]}/data'
    request = urllib.request.Request(url, headers={'User-Agent': USER_AGENT, 'Accept': 'application/json'})
    try:
        with (opener or urllib.request.urlopen)(request, timeout=20) as response:
            raw = response.read(16 * 1024 * 1024 + 1)
        if len(raw) > 16 * 1024 * 1024:
            raise ValueError('Response too large')
        data = validate(json.loads(raw), realm)
        atomic_json(target, data)
        atomic_json(status_file, {'ok': True, 'url': url, 'locations': len(data['locations'])})
        return data
    except (OSError, ValueError) as exc:
        # Do not retain remote error pages, credentials, or challenge payloads.
        atomic_json(status_file, {'ok': False, 'error': type(exc).__name__})
        raise ValueError('Map download unavailable; continuing without these pins') from exc


def prepare(cache_dir=None, notify=print):
    results = {}
    for realm in MAP_IDS:
        target = Path(cache_dir or PINS) / (realm + '.json')
        cached = target.is_file()
        status_file = target.with_suffix('.status.json')
        blocked = status_file.is_file()
        if blocked:
            try:
                status = json.loads(status_file.read_text(encoding='utf-8'))
                blocked = not isinstance(status, dict) or not status.get('retry_requested')
            except (OSError, ValueError):
                pass
        try:
            data = fetch_realm(realm, cache_dir)
            results[realm] = len(data['locations'])
            notify(f'{realm}: {results[realm]} ({"cache" if cached else "download"})')
        except ValueError as exc:
            results[realm] = None
            notify(f'{realm}: {exc}')
        if not cached and not blocked:
            time.sleep(0.5)
    return results


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--realm', choices=MAP_IDS)
    parser.add_argument('--retry', action='store_true', help='Retry failed downloads; cached maps stay cached')
    args = parser.parse_args(argv)
    if args.retry:
        # Reset only our own failure marker by replacing it with no marker decision.
        # fetch_realm accepts a marker with retry_requested to allow one retry.
        for realm in ([args.realm] if args.realm else MAP_IDS):
            status = PINS / (realm + '.status.json')
            if status.is_file() and not (PINS / (realm + '.json')).exists():
                atomic_json(status, {'retry_requested': True})
    if args.realm:
        data = fetch_realm(args.realm)
        print(args.realm, len(data['locations']))
    else:
        prepare()
    from tools.build_gow_ru_names import build_names
    build_names()


if __name__ == '__main__':
    main()
