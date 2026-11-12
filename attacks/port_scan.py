"""T1046: scan the top 100 ports across the start of the lab LAN. pfSense drops most."""

import shutil
import subprocess

from attacks.guard import assert_in_lab
from attacks.mgmt import TargetUnreachable

RANGE = "10.20.0.0/27"


def run() -> None:
    assert_in_lab(RANGE)
    if shutil.which("nmap") is None:
        raise TargetUnreachable("nmap is not installed on this PC")
    try:
        subprocess.run(
            ["nmap", "-sT", "-Pn", "-T4", "--max-retries", "1", "--top-ports", "100", RANGE],
            check=False, timeout=300,
        )
    except subprocess.TimeoutExpired as exc:
        raise TargetUnreachable(f"nmap on {RANGE} took over 5 minutes") from exc
