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
        Scenario("ssh-bruteforce", "ssh_bruteforce", "office01", ("5760", "5763", "5715"), "T1110"),
        Scenario("port-scan", "port_scan", "wazuh", ("87701", "87702"), "T1046"),
        Scenario("new-admin", "new_admin", "office01", ("5902",), "T1136.001"),
        Scenario("web-attack", "web_attack", "web01", ("31103", "31104"), "T1190"),
        Scenario("file-tamper", "file_tamper", "office01", ("550",), "T1565.001"),
    )
}
