import json
import subprocess
from types import SimpleNamespace

F = "/run/media/hannibal/linux F"


def facl(path, extra=""):
    return f"# file: {path}\nuser::rwx\n{extra}group::r-x\nmask::r-x\nother::---\n"


def fake_getfacl(lab_cli, monkeypatch, outputs):
    def run(argv, **_):
        return SimpleNamespace(stdout=outputs[argv[-1]], returncode=0)

    monkeypatch.setattr(lab_cli.subprocess, "run", run)


def test_acl_ok_needs_both_directories(lab_cli, monkeypatch):
    good = "user:libvirt-qemu:--x\n"
    fake_getfacl(lab_cli, monkeypatch, {F: facl(F, good), "/run/media/hannibal": facl("p", good)})
    assert lab_cli.acl_ok(F) is True
    fake_getfacl(lab_cli, monkeypatch, {F: facl(F, good), "/run/media/hannibal": facl("p")})
    assert lab_cli.acl_ok(F) is False


def test_acl_ok_respects_effective_mask(lab_cli, monkeypatch):
    masked = "user:libvirt-qemu:--x\t#effective:---\n"
    good = "user:libvirt-qemu:--x\n"
    fake_getfacl(lab_cli, monkeypatch, {F: facl(F, good), "/run/media/hannibal": facl("p", masked)})
    assert lab_cli.acl_ok(F) is False


def test_run_ansible_passes_spaced_path_as_one_value(lab_cli, monkeypatch):
    calls = []

    def run(argv, **kwargs):
        calls.append((argv, kwargs))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(lab_cli, "find_mount", lambda: F)
    monkeypatch.setattr(lab_cli.subprocess, "run", run)
    assert lab_cli.run_ansible(["host"]) == 0
    argv, kwargs = calls[0]
    assert json.loads(argv[argv.index("-e") + 1]) == {"lab_root": f"{F}/ir-lab"}
    assert argv[argv.index("--tags") + 1] == "host"
    assert str(kwargs["cwd"]).endswith("/ansible")


def test_run_ansible_without_tags_runs_everything(lab_cli, monkeypatch):
    calls = []
    monkeypatch.setattr(lab_cli, "find_mount", lambda: F)
    monkeypatch.setattr(
        lab_cli.subprocess, "run", lambda argv, **_: calls.append(argv) or SimpleNamespace(returncode=0)
    )
    lab_cli.run_ansible()
    assert "--tags" not in calls[0]


def test_ensure_venv_installs_pins_only_when_missing(lab_cli, monkeypatch, tmp_path):
    calls = []
    monkeypatch.setattr(lab_cli, "VENV", tmp_path / "venv")
    monkeypatch.setattr(
        lab_cli.subprocess, "run", lambda argv, **_: calls.append([str(a) for a in argv])
    )
    lab_cli.ensure_venv()
    assert calls[0][1:3] == ["-m", "venv"]
    assert calls[1][-2:] == ["-r", str(lab_cli.ROOT / "requirements.txt")]

    calls.clear()
    (tmp_path / "venv" / "bin").mkdir(parents=True)
    (tmp_path / "venv" / "bin" / "ansible-playbook").touch()
    lab_cli.ensure_venv()
    assert calls == []


def test_up_stops_with_hint_when_acl_gone_after_reboot(lab_cli, monkeypatch, capsys, tmp_path):
    ran = []
    monkeypatch.setattr(lab_cli, "find_mount", lambda: str(tmp_path))
    monkeypatch.setattr(lab_cli, "acl_ok", lambda _: False)
    monkeypatch.setattr(lab_cli, "mem_available_gb", lambda: 8.0)
    monkeypatch.setattr(lab_cli, "run_ansible", lambda *a: ran.append(a) or 0)
    assert lab_cli.main(["up"]) == 1
    out = capsys.readouterr().out
    assert "setfacl -m u:libvirt-qemu:x" in out and "Traceback" not in out
    assert ran == []


def test_up_tags_are_split_and_forwarded(lab_cli, monkeypatch, tmp_path):
    seen = []
    monkeypatch.setattr(lab_cli, "find_mount", lambda: str(tmp_path))
    monkeypatch.setattr(lab_cli, "acl_ok", lambda _: True)
    monkeypatch.setattr(lab_cli, "mem_available_gb", lambda: 8.0)
    monkeypatch.setattr(lab_cli, "preflight", lambda *a: [])
    monkeypatch.setattr(lab_cli, "ensure_venv", lambda: None)
    monkeypatch.setattr(lab_cli, "run_ansible", lambda tags=None: seen.append(tags) or 0)
    assert lab_cli.main(["up", "--tags", "host,base"]) == 0
    assert seen == [["host", "base"]]
