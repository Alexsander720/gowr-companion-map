from types import SimpleNamespace
from tools import bootstrap


def test_offline_bootstrap_never_invokes_pip(monkeypatch):
    monkeypatch.setattr(bootstrap.importlib.util,'find_spec',lambda name:object())
    def forbidden(*args,**kwargs):raise AssertionError('pip must not run offline')
    assert bootstrap.prepare(offline=True,runner=forbidden) == 0
    monkeypatch.setattr(bootstrap.importlib.util,'find_spec',lambda name:None)
    assert bootstrap.prepare(offline=True,runner=forbidden) == 1


def test_requirements_receipt_skips_repeat_installs(monkeypatch,tmp_path):
    monkeypatch.setattr(bootstrap.sys,'prefix',str(tmp_path))
    monkeypatch.setattr(bootstrap.importlib.util,'find_spec',lambda name:object())
    calls=[]
    def runner(command):calls.append(command);return SimpleNamespace(returncode=0)
    assert bootstrap.prepare(runner=runner) == 0
    assert bootstrap.prepare(runner=runner) == 0
    assert len(calls)==1
