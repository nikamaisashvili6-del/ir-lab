#!/usr/bin/env python3
"""Install config.xml on pfSense over SSH and reboot it.

The first push happens on a fresh clone, which still has the default password.
Later pushes use the lab key that the config installs.
"""

import sys

import paramiko

HOST = "10.21.0.1"
DEFAULT_PASSWORD = "pfsense"


def connect(key_path: str) -> paramiko.SSHClient:
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    common = {"username": "admin", "timeout": 15, "allow_agent": False, "look_for_keys": False}
    try:
        client.connect(HOST, key_filename=key_path, **common)
    except paramiko.AuthenticationException:
        client.connect(HOST, password=DEFAULT_PASSWORD, **common)
    return client


def main(config_path: str, key_path: str) -> int:
    client = connect(key_path)
    stdin, stdout, _ = client.exec_command("cat > /cf/conf/config.xml", timeout=30)
    with open(config_path, "rb") as config:
        stdin.write(config.read())
    stdin.channel.shutdown_write()
    if stdout.channel.recv_exit_status() != 0:
        print("could not write config.xml", file=sys.stderr)
        return 1
    client.exec_command(
        "rm -f /tmp/config.cache /cf/conf/trigger_initial_wizard; /sbin/shutdown -r now",
        timeout=30,
    )
    client.close()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
