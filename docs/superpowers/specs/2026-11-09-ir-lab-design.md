# IR Lab: design

Status: draft for review. Nothing is built yet. Source: `PREVIEW.md`.

## Intent

A tiny fake company on one PC, for two audiences: a public CV project whose interview story is "run attack → alert → investigate → fix", and practice for beginners in the new cyber unit. Every machine sends its security logs to Wazuh. An instructor launches an attack with one command, an alert fires, a Markdown guide walks the trainee through it, and one command resets the lab.

## Goals

- `./lab up` builds the whole lab from code, apart from one pfSense base install (see "pfSense").
- Five scenarios: SSH brute force, port scan, new admin user, web attack, file tampering.
- Each alert appears within about a minute of the attack.
- `./lab reset` returns the lab to a clean state for the next person.
- CI checks the Ansible and scripts on every push.
- README with diagram, screenshots and a one-minute demo GIF.

## Non-goals (for now)

The "later" scenarios (malware-like process, miner, exfiltration, log deletion), the Georgian guides, a web page for guides, and any grading of what the trainee did.

## Anti-goals: it fails if any of these happen, even if it works

- It changes the existing VMs (`pfsense`, `debian13`, `win11`, `win2k22`), networks or storage pools.
- It touches the personal files on linux F, or fills that drive.
- Anything in the lab is reachable from the home network or the internet.
- An attack script can send traffic to anything outside the lab.
- Blocking the attacker, which is the lesson, locks the instructor out of the lab.

## Decisions

**Yours:** plain libvirt; guides as Markdown in the repo; `lab check` only confirms the alert fired; VM disks on linux F, mounted once with udisksctl (no fstab, no per-boot handling); the topology, RAM sizes and scenarios in `PREVIEW.md`.

**My calls, please check them:** everything else in this document. The ones most worth your attention are the management network, the pfSense base step and the cold snapshots.

## What the machine survey found

| Finding | Effect on the design |
|---|---|
| linux F has 30 GB free of 117 GB, and holds 82 GB of personal files | The lab gets a disk budget and a free-space check. |
| F mounts at `/run/media/hannibal/linux F`. The parent directories admit only `hannibal`. | The `libvirt-qemu` user cannot reach VM disks there until it gets an ACL. See "Disks". |
| 14 GB RAM, 8.5 GB available right now | The 6.3 GB lab fits, with about 2 GB to spare. `./lab up` checks first. |
| The existing `pfsense` VM has one NIC, 4 GB RAM and its disk on the root drive | Not reusable. The lab gets its own. |
| Existing networks use 10.10.x, 192.168.100/122, and 172.17-20 | 10.19, 10.20 and 10.21 are free. |
| Ansible and `cloud-localds` missing; `virt-install`, `xorriso`, `pipx`, `nmap` present | Ansible goes in a project venv. `virt-install --cloud-init` replaces `cloud-localds`. |
| sudo needs a password | The one-time setup step (see "Disks") prompts the user. |

## Network

The blueprint has the attacker and the instructor on the same host. If both reach the lab the same way, a trainee who blocks the attacker's IP also cuts off Ansible and the dashboard. So this design adds one network the blueprint doesn't have: a management network that bypasses the firewall.

```
 host PC
  ├─ 10.19.0.1 ── irlab-wan (NAT to internet) ── 10.19.0.2 pfSense WAN    ← attacks arrive here
  └─ 10.21.0.254 ─ irlab-mgmt (ports isolated) ─┬ .1  pfSense              ← Ansible, dashboard, lab check
                                                ├ .10 web01
                                                ├ .20 office01
                                                └ .30 wazuh

 pfSense LAN 10.20.0.1 ── irlab-lan (no host address) ─┬ .10 web01    nginx        768 MB
                                                       ├ .20 office01 SSH          512 MB
                                                       └ .30 wazuh    all-in-one   4 GB
 pfSense 1 GB. Total 6.3 GB.
```

- `irlab-wan` declares a libvirt static route, so the host reaches 10.20.0.0/24 through pfSense. No sudo needed, and attacks really cross the firewall.
- `irlab-lan` has no host address, so nothing can sidestep pfSense on that network.
- `irlab-mgmt` uses isolated ports, so VMs cannot talk to each other over it. Only the host can reach them. It has no route out.
- All libvirt objects are prefixed `irlab-` and the pool is `irlab`, so they cannot collide with what exists.
- Dashboard: `https://10.21.0.30`. It is only reachable from the host.
- pfSense WAN: "block private networks" off, because its WAN is a private range. Allowed from WAN: office01:22 and web01:80. Everything else is dropped and logged.

## Disks

- Lab files live in `linux F/ir-lab/`: one Debian cloud base image, linked-clone qcow2 disks, the pfSense base image.
- F is mounted once with udisksctl during setup, and `libvirt-qemu` gets traverse-only ACLs on `linux F` and `/run/media/hannibal` in the same step (one sudo prompt). This is a one-time project, so the user decided `./lab` does not handle reboots: it does not mount F or ask for sudo.
- If the PC does reboot, `./lab up` stops with a clear message and prints the mount and ACL commands to run by hand.
- `./lab` finds the path with `findmnt` rather than hardcoding it. The path contains a space, so everything must quote it.
- Budget, estimated: about 15-17 GB used. Thin virtual sizes: wazuh 20 GB, pfSense 8 GB, web01 and office01 6 GB each. `./lab up` refuses to start below 25 GB free on first build. Wazuh indices are deleted after 7 days.
- All VMs boot BIOS, not UEFI, because libvirt internal snapshots don't work with UEFI firmware.

## pfSense

The pfSense installer is interactive and the image can't be redistributed in a public repo, so this is the one part that can't be fully automated cheaply.

- **Once only:** `docs/pfsense-base.md` walks through installing from the ISO into `irlab-pfsense-base`, about 10 minutes by hand: assign three interfaces, set the management IP, enable SSH. The result stays on F as a base image.
- **Everything after is code:** Ansible templates a complete `config.xml` (interfaces, firewall rules, logging, remote syslog to wazuh), copies it over the management network, and reboots.
- You need to supply a pfSense CE ISO. I found none in `~/Downloads`.

## Machines and Wazuh

- web01 and office01 are Debian 13 cloud images configured through cloud-init and Ansible. wazuh uses Debian 13 if the current Wazuh release supports it, otherwise Debian 12. The first build step confirms this.
- Wazuh all-in-one at a pinned version, indexer heap capped at about 1.5 GB. Wazuh recommends 8 GB for this role, so 4 GB is below that. It should be fine for three sources, and is the first thing to raise if the dashboard struggles.
- Agents on web01 and office01. pfSense sends filter logs by syslog (UDP 514) to wazuh, accepted only from 10.20.0.1.
- Agent config that the defaults don't cover: collect the nginx access log, and turn on real-time file integrity for `/etc/passwd` and the web root. The default integrity scan runs every 12 hours, which would break the "within a minute" goal.
- Secrets are generated per build into a gitignored `.lab/` directory. The only password in the repo is office01's deliberately weak one, which is part of the exercise.

## The `lab` command

One Python file, standard library only, at the repo root.

| Command | What it does |
|---|---|
| `./lab up` | Preflight checks, then runs Ansible to create and configure everything, then takes the `clean` snapshot. Safe to re-run. |
| `./lab status` | Shows VMs, agents, and whether the dashboard answers. |
| `./lab attack <name>` | Runs one scenario and records its start time. |
| `./lab check <name>` | Asks Wazuh for the expected alert since that start time, waiting up to 2 minutes. Exit 0 if it fired, 1 if not. It does not check the trainee's fix. |
| `./lab reset` | Stops all VMs, reverts to `clean`, boots them in order, waits for agents to report. |
| `./lab down` | Shuts VMs down and keeps everything. |
| `./lab destroy` | Removes only `irlab-*` objects and `linux F/ir-lab/`, after confirmation. |

**Reset uses cold snapshots**, taken with VMs shut off. Memory snapshots would add about 6 GB to a tight drive and restore every VM with a stale clock, which scrambles the log timelines trainees are learning to read. The cost is a slower reset, estimated at 3-5 minutes while Wazuh starts.

Ansible runs from a project `.venv` with pinned versions, created by `./lab up`, so it needs no sudo and installs nothing globally. It calls `virsh` and `virt-install` directly, which avoids compiling libvirt Python bindings.

## Scenarios

Rule IDs below are from memory of the default ruleset. The build confirms each against the pinned Wazuh version, and `lab check` uses the confirmed ones.

| # | Name | How it runs | Expected alert | ATT&CK |
|---|---|---|---|---|
| 1 | `ssh-bruteforce` | Host tries a small wordlist against office01 through pfSense, then succeeds | 5760, 5763 (brute force), then 5715 (success) | T1110 |
| 2 | `port-scan` | `nmap -sT` from host at the LAN range | pfSense drops, 87701 / 87702 | T1046 |
| 3 | `new-admin` | Over management SSH on office01: add a user, add to sudo | 5902, group-change rules | T1136.001 |
| 4 | `web-attack` | SQLi and path-traversal requests at web01 through pfSense | 31103, 31104 | T1190 |
| 5 | `file-tamper` | Over management SSH: change `/etc/passwd` and a site file | 550 | T1565.001 |

Scenarios 3 and 5 simulate an attacker who is already inside, which is why they run over management SSH.

The SSH attack uses `paramiko` from the project venv, because `lab` itself stays standard-library only and `sshpass`/`hydra` would need sudo to install. fail2ban is preinstalled on office01 and disabled, so turning it on is the trainee's fix.

**Safety guard:** one function checks every destination against 10.20.0.0/24 and 10.21.0.0/24, and aborts otherwise. It has unit tests. Attack scripts take a scenario name and no target argument.

## Guides

`guides/0N-<name>.md`, in English, one per scenario, all with the same sections: what this attack is; what you'll see in the dashboard (rule ID, ATT&CK technique); which logs prove it; how to stop it (pfSense rule, fail2ban, or restoring the file); what to write in the incident report. Plus a shared report template.

## Repo layout

```
lab                 the CLI
ansible/            playbooks, roles (host, pfsense, base, wazuh, web01, office01), config.xml template
attacks/            one Python module per scenario
guides/             Markdown guides and report template
docs/               pfsense-base.md, this design
tests/              unit tests for the lab CLI and safety guard
.github/workflows/  CI
```

## Testing

- CI, no VMs: `ansible-lint`, `yamllint`, Python unit tests. GitHub runners can't run this lab, so CI covers static checks only.
- Real acceptance on this PC: from a fresh build, each scenario's `attack` then `check` returns 0 within the time limit. Then `reset`, then all five pass again. Finally, confirm the existing VMs, networks and personal files on F are unchanged, and that blocking the attacker in pfSense leaves the dashboard reachable.

## Build order

1. Host: venv, networks, pool, F mount and ACLs. First test: boot one small VM from F, because AppArmor's handling of a `/run/media` disk path is unverified.
2. pfSense base image (your 10 minutes), then `config.xml` from code.
3. Debian VMs, Wazuh, agents, pfSense syslog.
4. `lab` CLI and snapshots/reset.
5. The five scenarios, confirming each rule ID.
6. Guides.
7. CI and README. Screenshots and the GIF come from the running lab.

## Open risks

- **AppArmor and `/run/media`:** not verified. Step 1 tests it first. If libvirt refuses that path, the likely fix is a small local AppArmor rule, which needs sudo.
- **Memory:** 2 GB of headroom assumes today's host load. Heavy apps running alongside would push the lab into swap.
- **Size estimates and reset time** are estimates until the first build.

Git publishing (remote, public repo) is not part of the build unless you ask for it.
