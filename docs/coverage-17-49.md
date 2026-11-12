# Coverage check — topics #17 and #49

This lab combines two course topics. Below is what each one asks for, what the lab
delivers, and what is still open. Status as of 2026-11-12, confirmed by running every
scenario live against the lab.

- ✅ done · 🟡 partial · ⬜ not done

## #17 — Central security-log collection and analysis

| Point | Status | Where / note |
|---|---|---|
| Collect logs centrally from every host | ✅ | Wazuh agents on web01 + office01; manager on the wazuh VM |
| Endpoint logs (auth, sudo, processes) | ✅ | journald + `/var/log/auth.log` inputs; confirmed via live attacks |
| File-integrity monitoring | ✅ | syscheck on `/etc/passwd` and `/var/www/html` (fires rule 550) |
| Web-server logs | ✅ | nginx access log forwarded from web01 (fires 31103/31104) |
| **Firewall logs** | 🟡 | Wazuh **listens** for pfSense syslog on `10.20.0.30:514`, but pfSense is **not yet sending** its firewall log — so the port-scan drops don't alert. **One open task.** |
| Analysis: decoders, rules, severities | ✅ | Built-in ruleset; alerts carry rule ID + level |
| Mapped to MITRE ATT&CK | ✅ | Each scenario tagged (T1110, T1046, T1136.001, T1190, T1565.001) |
| Searchable storage | ✅ | Wazuh indexer (OpenSearch) |
| Retention policy | ✅ | 7-day ISM delete policy on alert indices |
| Dashboard for analysts | ✅ | `https://10.21.0.30` |
| Secure agent enrolment | ✅ | Password-protected enrolment on 1514/1515 |

**#17 verdict:** essentially complete. The single gap is **wiring pfSense's own firewall
log into Wazuh** so network-level events (scans, blocked traffic) alert like the host ones
already do.

## #49 — Incident-response training lab

| Point | Status | Where / note |
|---|---|---|
| Isolated multi-VM environment | ✅ | pfSense + web01 + office01 + wazuh, cannot reach home/internet |
| Built entirely from code | ✅ | `./lab up` (Ansible); one pfSense base install is the only manual step |
| Attack scenarios | ✅ | 5 scenarios, each one command (`./lab attack <name>`) |
| Attacks confined to the lab | ✅ | `attacks/guard.py` refuses any target outside the lab subnets |
| Each attack raises a detectable alert | 🟡 | **4 of 5 fire** (ssh-bruteforce, new-admin, web-attack, file-tamper). port-scan pending the firewall-log task above. |
| Confirm an alert fired | ✅ | `./lab check <name>` |
| Trainee walk-throughs (investigate → fix) | ✅ | `guides/01…05` — the run→alert→investigate→fix loop with real log lines |
| Concept / defence reference | ✅ | `docs/field-guide.md` |
| Reset to a clean state | ✅ | `./lab reset` reverts VM snapshots |
| CI on every push | ✅ | yamllint, ansible-lint, playbook syntax, 58 unit tests — green |
| README with diagram | ✅ | `README.md` |
| **README screenshots + 1-min demo GIF** | ⬜ | Diagram is in; **screenshots of a fired alert and a short demo GIF are still missing.** |
| Visual dashboard of the attacks | ✅ | `docs/attack-range.html` (bonus, beyond spec) |

**#49 verdict:** the training loop is complete and works end to end. Two things remain:
**port-scan detection** (same firewall-log task as #17) and **README screenshots + a demo
GIF** for presentation.

## Still to add (the whole list)

1. **Wire pfSense firewall logs into Wazuh** — enable Remote Logging on pfSense → Wazuh
   `:514`. Fixes port-scan detection and closes the one real #17 gap. *(highest value)*
2. **README screenshots + 1-minute demo GIF** — a fired alert in the dashboard and the
   `attack → alert → reset` loop. Pure presentation, but it's what a reviewer sees first.
3. **Smaller hardening (optional):**
   - The pre-flight RAM check blocks a re-run when the lab is already up — make it skip the
     check when the VMs are already running.
   - Bump the wazuh VM disk for cold rebuilds so the installer's CVE download completes
     before the role disables vulnerability detection.

Everything else the two topics ask for is built, tested, and confirmed live.
