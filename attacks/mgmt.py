"""SSH into lab VMs as labadmin, for the 'already inside' scenarios."""

import socket
from pathlib import Path

import paramiko

from attacks.guard import assert_in_lab

KEY = Path(__file__).resolve().parent.parent / ".lab" / "id_ed25519"

# Management addresses: these bypass the firewall on purpose (see the design).
OFFICE01 = "10.21.0.20"
WEB01 = "10.21.0.10"


class TargetUnreachable(Exception):
    """The VM didn't answer in time: it's down, or the trainee already blocked us."""


# NoValidConnectionsError and socket.timeout are both OSErrors; listed for the reader.
NETWORK_ERRORS = (socket.timeout, paramiko.ssh_exception.NoValidConnectionsError, OSError)


def ssh_run(host: str, command: str, timeout: int = 30) -> str:
    """Run a command on a lab VM and return its output. Checks the host first."""
    assert_in_lab(host)
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        client.connect(host, username="labadmin", key_filename=str(KEY), timeout=10,
                       allow_agent=False, look_for_keys=False)
        _, stdout, stderr = client.exec_command(command, timeout=timeout)
        output = stdout.read().decode()
        if stdout.channel.recv_exit_status() != 0:
            raise RuntimeError(f"{host}: {stderr.read().decode().strip() or 'command failed'}")
        return output
    except NETWORK_ERRORS as exc:
        raise TargetUnreachable(f"{host} did not answer on port 22") from exc
    finally:
        client.close()
