"""Attack modules: shape, safety guard, and one-line failures."""

import importlib
import importlib.resources
import inspect

import paramiko
import pytest

from attacks import mgmt
from attacks.__main__ import main as attacks_main
from attacks.guard import OutOfLabError
from attacks.mgmt import TargetUnreachable, ssh_run
from attacks.registry import SCENARIOS


def test_every_scenario_module_has_run():
    for s in SCENARIOS.values():
        assert callable(importlib.import_module(f"attacks.{s.module}").run)


def test_no_module_takes_a_target():
    for s in SCENARIOS.values():
        run = importlib.import_module(f"attacks.{s.module}").run
        assert not inspect.signature(run).parameters


def test_ssh_run_guards_before_connecting(monkeypatch):
    def boom(*a, **k):
        raise AssertionError("SSHClient must not be built for an outside host")

    monkeypatch.setattr(paramiko, "SSHClient", boom)
    with pytest.raises(OutOfLabError):
        ssh_run("8.8.8.8", "id")


def test_ssh_run_maps_timeout_to_unreachable(monkeypatch):
    class Client:
        def set_missing_host_key_policy(self, _): pass
        def connect(self, *a, **k): raise TimeoutError("timed out")
        def close(self): pass

    monkeypatch.setattr(mgmt.paramiko, "SSHClient", Client)
    with pytest.raises(TargetUnreachable):
        ssh_run("10.21.0.20", "id")


def test_runner_unreachable_is_one_line_exit_1(monkeypatch, capsys):
    module = importlib.import_module("attacks.ssh_bruteforce")

    def down():
        raise TargetUnreachable("office01 (10.20.0.20) did not answer on port 22")

    monkeypatch.setattr(module, "run", down)
    assert attacks_main(["ssh-bruteforce"]) == 1
    err = capsys.readouterr().err
    assert "office01" in err and "Traceback" not in err
    assert len(err.strip().splitlines()) == 1


def test_runner_unknown_scenario_exits_2(capsys):
    assert attacks_main(["nope"]) == 2


def test_wordlist_ends_with_the_real_password_absent():
    # The real password is tried separately, last, so the wordlist must not contain it.
    words = (importlib.resources.files("attacks") / "wordlist.txt").read_text().split()
    assert len(words) >= 10 and "Summer2026!" not in words
