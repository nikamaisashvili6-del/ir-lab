import xml.etree.ElementTree as ET
from pathlib import Path

import jinja2
import pytest

TEMPLATE = Path(__file__).resolve().parent.parent / "ansible/roles/pfsense/templates/config.xml.j2"


@pytest.fixture
def text():
    env = jinja2.Environment(undefined=jinja2.StrictUndefined)
    return env.from_string(TEMPLATE.read_text()).render(
        pfsense_admin_bcrypt="$2b$10$examplehash", lab_pubkey_b64="c3NoLWtleQ=="
    )


@pytest.fixture
def cfg(text):
    return ET.fromstring(text)


def rules(cfg, interface):
    return [r for r in cfg.findall("filter/rule") if r.findtext("interface") == interface]


def test_interfaces_are_in_their_final_roles(cfg):
    assert cfg.findtext("interfaces/wan/if") == "vtnet0"
    assert cfg.findtext("interfaces/lan/if") == "vtnet1"
    assert cfg.findtext("interfaces/opt1/if") == "vtnet2"


def test_addresses(cfg):
    assert cfg.findtext("interfaces/wan/ipaddr") == "10.19.0.2"
    assert cfg.findtext("interfaces/wan/subnet") == "24"
    assert cfg.findtext("interfaces/lan/ipaddr") == "10.20.0.1"
    assert cfg.findtext("interfaces/opt1/ipaddr") == "10.21.0.1"


def test_wan_gateway_is_the_host(cfg):
    name = cfg.findtext("interfaces/wan/gateway")
    item = next(g for g in cfg.findall("gateways/gateway_item") if g.findtext("name") == name)
    assert item.findtext("gateway") == "10.19.0.1"
    assert cfg.findtext("gateways/defaultgw4") == name


def test_wan_does_not_block_private_ranges(cfg):
    assert cfg.find("interfaces/wan/blockpriv") is None


def test_wan_passes_only_the_two_exposed_services(cfg):
    got = {
        (r.findtext("type"), r.findtext("protocol"), r.findtext("destination/address"), r.findtext("destination/port"))
        for r in rules(cfg, "wan")
    }
    assert got == {("pass", "tcp", "10.20.0.20", "22"), ("pass", "tcp", "10.20.0.10", "80")}


def test_default_block_is_logged(cfg):
    assert cfg.find("syslog/nologdefaultblock") is None


def test_firewall_events_go_to_wazuh(cfg):
    assert cfg.find("syslog/enable") is not None
    assert cfg.findtext("syslog/remoteserver") == "10.20.0.30:514"
    assert cfg.find("syslog/filter") is not None


def test_management_reaches_only_the_firewall_itself(cfg):
    mgmt = rules(cfg, "opt1")
    assert mgmt
    assert {r.findtext("destination/network") for r in mgmt} == {"(self)"}


def test_ssh_key_and_password_come_from_variables(cfg):
    admin = cfg.find("system/user")
    assert admin.findtext("bcrypt-hash") == "$2b$10$examplehash"
    assert admin.findtext("authorizedkeys") == "c3NoLWtleQ=="


def test_no_private_key_in_public_template():
    assert "<prv>" not in TEMPLATE.read_text()
