import io
import json
import pytest
from tools import fetch_mapgenie as fetch


def test_embedded_json_is_decoded_without_execution(synthetic_map):
    html='<script>window.mapData = '+json.dumps(synthetic_map)+'; malicious();</script>'
    assert fetch.parse_embedded(html) == synthetic_map
    with pytest.raises(ValueError):fetch.parse_embedded('<html>challenge</html>')
    with pytest.raises(ValueError):fetch.parse_embedded('window.mapData = {"map":{}};')


def test_one_request_per_realm_and_cache(tmp_path,synthetic_map):
    calls=[]
    def opener(req,timeout):
        calls.append(req)
        return io.BytesIO(json.dumps(synthetic_map).encode())
    first=fetch.fetch_realm('midgard',tmp_path,opener)
    assert fetch.fetch_realm('midgard',tmp_path,opener) == first
    assert len(calls) == 1
    assert calls[0].full_url == 'https://mapgenie.io/api/v1/maps/473/data'
    assert '@' not in calls[0].get_header('User-agent')


def test_failed_download_is_cached_and_never_bypasses_challenge(tmp_path):
    calls=[]
    def challenge(req,timeout):calls.append(req);return io.BytesIO(b'<html>captcha</html>')
    for _ in range(2):
        with pytest.raises(ValueError):fetch.fetch_realm('midgard',tmp_path,challenge)
    assert len(calls) == 1
    assert not (tmp_path/'midgard.json').exists()


def test_wrong_realm_is_rejected(tmp_path,synthetic_map):
    with pytest.raises(ValueError):
        fetch.fetch_realm('alfheim',tmp_path,lambda *a,**k:io.BytesIO(json.dumps(synthetic_map).encode()))
