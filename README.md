# IR Lab — a Wazuh incident-response training range

A tiny fake company on a single PC. Every machine ships its security logs to a Wazuh
SIEM. You launch a real attack with one command, watch the alert fire in the dashboard,
investigate it, and reset the lab for the next person — all from code.

It is built for two audiences: as a **portfolio project** whose interview story is
*"run attack → alert → investigate → fix"*, and as a **training range** for people new to
blue-team work.

```
                 internet (NAT)
                      │
              irlab-wan  10.19.0.0/24
                      │
                 ┌────┴─────┐
                 │ pfSense  │   firewall · router · DHCP · DNS · syslog→Wazuh
                 └────┬─────┘
          LAN  10.20.0.0/24  (attacks arrive here, through the firewall)
          ┌───────────┼───────────┐
      web01         office01      wazuh
    10.20.0.10    10.20.0.20    10.20.0.30
    web server    workstation   SIEM: manager + indexer + dashboard
          └───────────┼───────────┘
          mgmt  10.21.0.0/24  (out-of-band; bypasses the firewall)
                      │
                   host PC  ←  ./lab, Ansible, dashboard, attack scripts
```

Every target runs the Wazuh agent; pfSense forwards its firewall log to Wazuh as well.
The **management network** is deliberately separate so that blocking the attacker — the
whole lesson — never locks the instructor out of the lab.

## What it demonstrates

Wazuh (SIEM) · Ansible (infra from code) · pfSense · libvirt/KVM · Linux hardening ·
detection rules mapped to **MITRE ATT&CK** · incident response · CI. The entire lab stands
up from one command, and every attack is confined to the lab network by a hard guardrail.

## Quickstart

```bash
./lab up                    # build or start the whole lab (first run also snapshots it)
./lab status                # VMs, agents, and whether the dashboard is up
./lab attack ssh-bruteforce # run a scenario
./lab check ssh-bruteforce  # confirm its alert actually fired in Wazuh
./lab reset                 # revert every VM to its clean snapshot
```

Dashboard: `https://10.21.0.30` (reached over the management network).

## The five scenarios

| Scenario | MITRE | What the attacker does | What Wazuh catches |
|---|---|---|---|
| `ssh-bruteforce` | **T1110** | Password-guesses SSH on office01 through the firewall | Failed-login flood, then a success from the same IP |
| `port-scan` | **T1046** | `nmap` sweeps the LAN; pfSense drops most of it | Firewall drop-flood correlated into a scan alert |
| `new-admin` | **T1136.001** | Creates a local account and adds it to `sudo` | New user + privileged-group change |
| `web-attack` | **T1190** | SQL injection + path traversal at web01 | Web-log signatures (SQLi / traversal / scanner UA) |
| `file-tamper` | **T1565.001** | Appends a uid-0 line to `/etc/passwd`, defaces the site | File-integrity (FIM) checksum-changed alert |

Each one runs in seconds and the alert appears within about a minute.

## How detection flows

```
 attack → target host → wazuh-agent → wazuh-manager (decoders + rules) → indexer → dashboard
 scan   → pfSense drop → syslog ───────────────┘
```

Agents watch the endpoints (logs, file integrity); pfSense watches the wire. Both feed the
manager, where rules turn raw events into severity-rated, ATT&CK-tagged alerts.

## Learn the offence to build the defence

The deep dive — **[`docs/field-guide.md`](docs/field-guide.md)** — explains every service
and every command line by line: what each attack looks like in a *real* breach, how the
five scenarios chain into a full intrusion (and map onto attacking a real server), and how
a defender detects and stops each step.

## Repo layout

```
lab                 one entry point: up / status / attack / check / reset / down / destroy
ansible/            roles that build the host, pfSense, the VMs, and Wazuh from code
attacks/            the five scenarios (+ guard.py: refuses any target outside the lab)
tests/              unit tests for the lab logic and attack guardrails
docs/field-guide.md services, commands, real-world translation, and defence
.github/workflows/  CI: yamllint, ansible-lint, playbook syntax, unit tests
```

## Safety

The lab cannot reach the home network or the internet beyond NAT, and the attack scripts
refuse any destination outside `10.20.0.0/24` / `10.21.0.0/24`. Everything here runs
against machines built for it. The same commands aimed at a system you don't own are a
crime — keep them in the lab.
