"""Scenario definitions. Standard library only, because ./lab imports this."""

from dataclasses import dataclass


@dataclass(frozen=True)
class Scenario:
    name: str
    module: str
    agent: str
    rule_ids: tuple[str, ...]
    technique: str


SCENARIOS: dict[str, Scenario] = {
    s.name: s
    for s in (
        # Rule IDs confirmed by running each attack live against the lab (2026-11-12).
        Scenario("ssh-bruteforce", "ssh_bruteforce", "office01", ("5760", "5763", "5551"), "T1110"),
        # port-scan detection depends on pfSense forwarding its firewall log to Wazuh,
        # which is not wired up yet — see docs/field-guide.md. These IDs do not fire today.
        Scenario("port-scan", "port_scan", "wazuh", ("4151", "4152"), "T1046"),
        # 5902 = new user added (needs the auth.log input); 5403 = first sudo, the fallback.
        Scenario("new-admin", "new_admin", "office01", ("5902", "5403"), "T1136.001"),
        Scenario("web-attack", "web_attack", "web01", ("31103", "31104"), "T1190"),
        Scenario("file-tamper", "file_tamper", "office01", ("550",), "T1565.001"),
    )
}
