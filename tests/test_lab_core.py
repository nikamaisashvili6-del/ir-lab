import json


def no_sleep(_):
    return None


def test_preflight_unmounted(lab_cli):
    assert lab_cli.preflight(None, 0, 8, True, False)


def test_preflight_missing_acl(lab_cli):
    assert lab_cli.preflight("/f", 30, 8, False, False)


def test_preflight_low_disk_first_build_only(lab_cli):
    assert any("25" in p for p in lab_cli.preflight("/f", 24, 8, True, True))
    assert lab_cli.preflight("/f", 24, 8, False, True) == []


def test_preflight_low_memory(lab_cli):
    assert any("6.5" in p for p in lab_cli.preflight("/f", 30, 6, False, True))


def test_setup_hint_when_unmounted_names_commands(lab_cli):
    hint = lab_cli.setup_hint(None)
    assert "udisksctl mount -b /dev/disk/by-uuid/aae55af8-a3c4-4fad-ac70-4dfa00506615" in hint
    assert "setfacl -m u:libvirt-qemu:x" in hint


def test_setup_hint_quotes_space(lab_cli):
    hint = lab_cli.setup_hint("/run/media/hannibal/linux F")
    assert "'/run/media/hannibal/linux F'" in hint


def test_up_unmounted_exits_1_without_traceback(lab_cli, monkeypatch, capsys):
    monkeypatch.setattr(lab_cli, "find_mount", lambda: None)
    assert lab_cli.main(["up"]) == 1
    assert "udisksctl" in capsys.readouterr().out


def test_check_without_attack_exits_2(lab_cli):
    assert lab_cli.check("port-scan", query_fn=lambda *_: [{}], sleep=no_sleep) == 2


def test_check_after_clear_state_exits_2(lab_cli):
    lab_cli.record_attack("port-scan", "2026-11-09T10:00:00Z")
    lab_cli.clear_state()
    assert lab_cli.check("port-scan", query_fn=lambda *_: [{}], sleep=no_sleep) == 2


def test_check_found_and_timeout(lab_cli):
    lab_cli.record_attack("port-scan", "2026-11-09T10:00:00Z")
    assert (
        lab_cli.check("port-scan", query_fn=lambda *_: [{"rule": {}}], sleep=no_sleep)
        == 0
    )
    assert (
        lab_cli.check("port-scan", query_fn=lambda *_: [], sleep=no_sleep, timeout=0)
        == 1
    )


def test_check_queries_the_scenarios_rules_since_attack_start(lab_cli):
    lab_cli.record_attack("ssh-bruteforce", "2026-11-09T10:00:00Z")
    seen = []

    def query(rule_ids, agent, since):
        seen.append((tuple(rule_ids), agent, since))
        return [{"rule": {}}]

    lab_cli.check("ssh-bruteforce", query_fn=query, sleep=no_sleep)
    assert seen == [(("5760", "5763", "5715"), "office01", "2026-11-09T10:00:00Z")]


def test_query_filters_rules_agent_and_time(lab_cli):
    body = json.dumps(
        lab_cli.build_alert_query(("5763",), "office01", "2026-11-09T10:00:00Z")
    )
    assert "5763" in body and "office01" in body and "2026-11-09T10:00:00Z" in body


def test_unknown_scenario_exits_2_and_lists_names(lab_cli, capsys):
    assert lab_cli.main(["attack", "nope"]) == 2
    assert "ssh-bruteforce" in capsys.readouterr().out
