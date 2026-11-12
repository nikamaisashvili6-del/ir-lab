"""Lifecycle commands with virsh replaced by a fake that records calls."""

import pytest

MUTATING = {"destroy", "shutdown", "start", "snapshot-revert", "snapshot-create-as",
            "undefine", "net-destroy", "net-undefine", "pool-destroy", "pool-undefine"}


class FakeVirsh:
    def __init__(self, lab_cli):
        self.calls = []
        self.started = []
        self.snapshots = {d: ["clean"] for d in lab_cli.BOOT_ORDER}
        self.state = {d: "running" for d in lab_cli.BOOT_ORDER}

    def __call__(self, *args, check=True):
        self.calls.append(args)
        cmd, rest = args[0], args[1:]
        if cmd == "snapshot-list":
            return "\n".join(self.snapshots.get(rest[0], []))
        if cmd == "domstate":
            return self.state.get(rest[0], "shut off")
        if cmd in ("destroy", "shutdown"):
            self.state[rest[0]] = "shut off"
        if cmd == "start":
            self.started.append(rest[0])
            self.state[rest[0]] = "running"
        if cmd == "list":
            return "\n".join(["pfsense", "debian13", *self.state])
        if cmd == "net-list":
            return "default\nirlab-wan\nirlab-lan\nirlab-mgmt"
        if cmd == "pool-list":
            return "DCO1\ndefault\nirlab"
        return ""

    def called(self, cmd):
        return any(c[0] == cmd for c in self.calls)

    def mutating_calls(self):
        return [c for c in self.calls if c[0] in MUTATING]


@pytest.fixture
def fake_virsh(lab_cli, monkeypatch):
    fake = FakeVirsh(lab_cli)
    monkeypatch.setattr(lab_cli, "virsh", fake)
    monkeypatch.setattr(lab_cli, "wait_agents", lambda timeout=420: True)
    monkeypatch.setattr(lab_cli.time, "sleep", lambda _: None)
    return fake


def test_reset_missing_snapshot_stops_nothing(lab_cli, fake_virsh):
    fake_virsh.snapshots["irlab-web01"] = []
    assert lab_cli.reset() == 1
    assert fake_virsh.mutating_calls() == []


def test_reset_boots_in_order_and_clears_state(lab_cli, fake_virsh):
    lab_cli.record_attack("port-scan", "2026-11-09T10:00:00Z")
    assert lab_cli.reset() == 0
    assert fake_virsh.started == list(lab_cli.BOOT_ORDER)
    assert lab_cli.load_state()["attacks"] == {}


def test_reset_reverts_every_vm(lab_cli, fake_virsh):
    lab_cli.reset()
    reverted = [c[1] for c in fake_virsh.calls if c[0] == "snapshot-revert"]
    assert reverted == list(lab_cli.BOOT_ORDER)


def test_reset_fails_when_agents_never_report(lab_cli, fake_virsh, monkeypatch):
    monkeypatch.setattr(lab_cli, "wait_agents", lambda timeout=420: False)
    assert lab_cli.reset() == 1


def test_destroy_targets_only_prefixed(lab_cli):
    t = lab_cli.destroy_targets(
        ["pfsense", "debian13", "irlab-web01", "irlabx"],
        ["default", "irlab-wan", "vlan-10"],
        ["DCO1", "irlab", "irlab-old"],
    )
    assert t == {"domains": ["irlab-web01"], "networks": ["irlab-wan"], "pools": ["irlab"]}


@pytest.mark.parametrize("typed", ["", "y", "yes", "DESTROY ", "destroy now"])
def test_destroy_needs_exact_word(lab_cli, fake_virsh, typed):
    assert lab_cli.destroy(confirm_fn=lambda _: typed) == 1
    assert fake_virsh.mutating_calls() == []


def test_destroy_never_touches_other_vms(lab_cli, fake_virsh, monkeypatch):
    monkeypatch.setattr(lab_cli, "find_mount", lambda: None)
    assert lab_cli.destroy(confirm_fn=lambda _: "destroy") == 0
    touched = {c[1] for c in fake_virsh.mutating_calls()}
    assert touched and all(name.startswith("irlab") for name in touched)


def test_snapshot_taken_only_when_missing(lab_cli, fake_virsh):
    fake_virsh.snapshots["irlab-wazuh"] = []
    lab_cli.take_clean_snapshots()
    made = [c[1] for c in fake_virsh.calls if c[0] == "snapshot-create-as"]
    assert made == ["irlab-wazuh"]
