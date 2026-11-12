# 1 · SSH brute force (T1110)

## Run it
```bash
./lab attack ssh-bruteforce
./lab check  ssh-bruteforce     # confirms the alert fired
```
The script connects to office01's SSH service *through the firewall* and tries a list of
passwords for the user `jdoe`, then the real one. In the real world an attacker points
`hydra -l jdoe -P rockyou.txt ssh://<target>` at any exposed SSH port and lets it run.

## Find the alert
In the dashboard (Security events, agent **office01**) you'll see a burst of alerts.
The ones that matter:

| Rule | Level | Meaning |
|---|---|---|
| **5760** | 5 | `sshd: authentication failed` — one wrong password |
| **5551** | 10 | `PAM: Multiple failed logins in a small period of time` |
| **5763** | 10 | `sshd: brute force trying to get access to the system` |

Real log line behind rule 5760:
```
Nov 12 18:48:25 office01 sshd[2179]: Failed password for jdoe from 10.19.0.1 port 38852 ssh2
```

## Investigate
Ask three questions:
1. **Who?** The `from 10.19.0.1` field is the source. One IP producing dozens of failures
   in seconds is not a person fat-fingering a password.
2. **Did they get in?** Search the same agent for a **successful** login
   (`sshd: authentication success`, rule 5715) from that same IP right after the flood.
   A success immediately after a failure storm is the signature of a *cracked* password —
   that is the alert that should wake someone up, not the failures.
3. **What account?** Here it's `jdoe`. Note it for the write-up.

## Contain and fix
- **Block the source** at pfSense (or `fail2ban`), but remember the attacker reaches the
  lab through the firewall — the management network keeps you connected while you do it.
- **Reset the cracked account's password** and force a rotation.
- **Kill password auth:** set `PasswordAuthentication no` in `sshd_config` and use keys.
  Now there is nothing to guess and this attack simply cannot happen.
- **Add rate-limiting / fail2ban** so a wordlist never finishes.

## Write it up
> At 18:48 office01 logged a brute-force pattern (Wazuh 5763/5551) against user `jdoe`
> from 10.19.0.1 — ~N failures in Ms, followed by a success at 18:48:38. Source blocked,
> `jdoe` password reset, password auth disabled on office01. Root cause: weak password on
> an SSH-exposed account.

Then `./lab reset`.
