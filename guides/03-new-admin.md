# 3 · New admin account (T1136.001)

## Run it
```bash
./lab attack new-admin
./lab check  new-admin
```
This one simulates an attacker *already inside* office01. It runs:
```bash
sudo useradd -m -s /bin/bash svc-backup
sudo usermod -aG sudo svc-backup
```
It creates a new account named to look like a harmless service account (`svc-backup`) and
makes it an administrator. This is **persistence** — a way back in that survives the
password change or patch that might close the original hole.

## Find the alert
On agent **office01**:

| Rule | Level | Meaning |
|---|---|---|
| **5902** | — | `New user added to the system` |
| **5403** | 4 | `First time user executed sudo` — the attacker escalating |
| **550**  | 7 | `Integrity checksum changed` — because `/etc/passwd` was edited |

Real log line behind rule 5902:
```
office01 useradd[2358]: new user: name=svc-backup, UID=1002, GID=1002, home=/home/svc-backup, shell=/bin/bash
```

> Note: rule 5902 only fires because the agent reads `/var/log/auth.log`. The default
> Wazuh agent reads *journald*, which doesn't match the "new user" rule — the lab adds the
> `auth.log` input in `roles/wazuh_agent/templates/ossec-extra.conf.j2` so this detection
> works. Without it you'd still catch the attack via **550** (passwd changed) and **5403**
> (sudo used), just less specifically.

## Investigate
1. **Who is this account?** No ticket, no ping in chat — a privileged account nobody
   created is a compromise until proven otherwise.
2. **How was it made?** The `sudo` log right before it shows *which* existing account ran
   `useradd`. That account is the attacker's current foothold — your real problem.
3. **What else can log in?** Enumerate everything: `/etc/passwd`, `sudo`/`wheel` group
   membership, and `~/.ssh/authorized_keys` for every user. Persistence often comes in
   pairs.

## Contain and fix
- **Disable, don't just delete** the account first (`usermod -L`, `passwd -l`) so you can
  still investigate it, then remove it: `sudo userdel -r svc-backup`.
- **Find and evict the foothold** — the account that *ran* the useradd. Deleting
  `svc-backup` without finding how it got created means the attacker just makes another.
- **Alert on account creation and privileged-group changes** going forward. These events
  are rare in normal operations, so they're cheap, low-noise, high-value alerts.

## Write it up
> At 18:51 a new local account `svc-backup` was created on office01 and added to `sudo`
> (Wazuh 5902/5403, FIM 550), by `labadmin` via `sudo useradd`. Account removed; the
> labadmin foothold investigated as the entry point. Recommend alerting on all account
> creation and auditing existing privileged accounts.

Then `./lab reset`.
