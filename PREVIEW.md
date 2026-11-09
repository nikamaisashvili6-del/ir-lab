---
tags:
  - project/ir-lab
  - cv
created: 2026-11-09
status: preview (not built)
---

# IR Lab: Wazuh incident-response training lab (preview)

Combines two topics: central security-log collection and analysis, and a virtual incident-response training environment. Public CV project with a fake company, built in VMs.

## In one sentence
A tiny fake company network on one PC: every machine sends its security logs to Wazuh, you launch an attack with one command, an alert fires, and a step-by-step guide walks a trainee through finding and stopping it. Then one command resets the lab.

## The network
```
                 ┌──────────────── host PC (attacker scripts run here) ─────────────┐
                 │                                                                   │
   internet ── pfSense (firewall, 1 GB) ── lab LAN 10.20.0.0/24                      │
                                   ├── web01    nginx site        (768 MB)  ← target  │
                                   ├── office01 "employee" SSH box (512 MB) ← target  │
                                   └── wazuh    manager + indexer + dashboard (4 GB)  │
                 └───────────────────────────────────────────────────────────────────┘
   Total ≈ 6.3 GB RAM. VM disks on linux F (~20 GB).
```
Every target runs the Wazuh agent. pfSense sends its firewall log to Wazuh too.

## What a trainee sees
1. Opens the Wazuh dashboard: everything green.
2. Instructor runs `./lab attack ssh-bruteforce`.
3. Within a minute: alert "multiple failed SSH logins" on office01, rule ID, MITRE ATT&CK technique (T1110).
4. Trainee opens the matching guide: what this attack is, which logs prove it, how to block it (pfSense rule / fail2ban), what to write in the incident report.
5. `./lab reset` → clean lab for the next person.

## Attack scenarios (first 5)
| # | Scenario | What fires | Skill it teaches |
|---|---|---|---|
| 1 | SSH brute force | many failed logins, then a success | reading auth logs, blocking an IP |
| 2 | Port scan from outside | pfSense blocks + scan alert | firewall logs, what a scan looks like |
| 3 | New admin user created | user added to sudo group | spotting persistence |
| 4 | Web attack (SQLi / path traversal tries) | nginx access-log alerts | web logs, attack strings |
| 5 | File tampered (/etc/passwd, website files) | file-integrity alert | change detection, what changed |
Later: malware-like process, crypto-miner CPU spike, data copied out, log deletion.

## What gets built (in order)
1. **Ansible** creates and configures all VMs from code (one command rebuilds the lab).
2. **Wazuh** all-in-one install + agents on every VM + pfSense syslog.
3. **Attack scripts** (`./lab attack <name>`), safe and confined to the lab LAN.
4. **Guides** per scenario (English; Georgian version for beginners later).
5. **Reset** (VM snapshots) + **GitHub Actions** that check the Ansible/scripts on every push.
6. **README** with diagram, screenshots, a 1-minute demo GIF.

## What it shows on a CV
Wazuh (SIEM), Ansible, Linux hardening, pfSense, detection rules mapped to MITRE ATT&CK, incident response, CI. Interview story: "run attack → alert → investigate → fix".

## Bonus use
The new cyber unit (beginners) could use it for practice: Linux basics → reading logs → first incident.

## Not decided yet
- VM tool: libvirt/KVM (already installed: debian13, pfsense VMs exist) vs Vagrant.
- Guides only in the repo, or a small web page.
- linux F permanent mount needed first (fstab, sudo).
