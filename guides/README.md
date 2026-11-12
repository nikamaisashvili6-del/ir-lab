# Trainee guides

Five hands-on incident walk-throughs. Each one follows the same loop the lab is built
around: **run the attack → find the alert → investigate → contain and fix → write it up.**

Work them in order; they build from noisy-and-obvious to quiet-and-sneaky.

| # | Guide | Attack | MITRE | Skill it teaches |
|---|---|---|---|---|
| 1 | [SSH brute force](01-ssh-bruteforce.md) | `ssh-bruteforce` | T1110 | Reading auth logs, spotting a password-guess, blocking a source |
| 2 | [Port scan](02-port-scan.md) | `port-scan` | T1046 | What recon looks like, firewall logs, attack surface |
| 3 | [New admin account](03-new-admin.md) | `new-admin` | T1136.001 | Spotting persistence, auditing who can log in |
| 4 | [Web attack](04-web-attack.md) | `web-attack` | T1190 | Web logs, injection signatures, scanner traffic |
| 5 | [File tampering](05-file-tamper.md) | `file-tamper` | T1565.001 | File-integrity monitoring, detecting change |

**Before you start:** open the Wazuh dashboard at `https://10.21.0.30`
(`admin` / password in `.lab/secrets.yml`) and confirm everything is green with
`./lab status`. After each exercise, run `./lab reset` to return the lab to a clean state
for the next person.

For the *why* behind every service and command — and how each attack maps to a real
breach — read [`../docs/field-guide.md`](../docs/field-guide.md).
