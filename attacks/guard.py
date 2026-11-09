"""The one check every attack destination must pass."""

import ipaddress

LAB_NETS = (
    ipaddress.ip_network("10.20.0.0/24"),
    ipaddress.ip_network("10.21.0.0/24"),
)


class OutOfLabError(Exception):
    """A destination is not inside the lab."""


def assert_in_lab(dest: str) -> str:
    """Return dest if it is an IP or CIDR wholly inside the lab, else raise."""
    try:
        net = ipaddress.ip_network(dest, strict=True)
    except ValueError as exc:
        raise OutOfLabError(f"not a lab address: {dest!r}") from exc
    if net.version == 4 and any(net.subnet_of(lab) for lab in LAB_NETS):
        return dest
    raise OutOfLabError(f"outside the lab: {dest!r}")
