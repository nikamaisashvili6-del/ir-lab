# 5 · File tampering (T1565.001)

## Run it
```bash
./lab attack file-tamper
./lab check  file-tamper
```
An attacker already inside does two things:
```bash
# office01 — a hidden root-equivalent account
echo 'sysupdate:x:0:0::/root:/bin/bash' >> /etc/passwd
# web01 — deface the site
echo '<!-- owned -->' >> /var/www/html/index.html
```
The `sysupdate` line has **UID 0** — it *is* root under an innocent name. (In the lab it
has no password so it can't actually log in; the point is the file change and the alert.)

## Find the alert
Detection here is by **change**, not by signature — you don't need to know the specific
attack, only that a protected file moved. On agent **office01** (and web01):

| Rule | Level | Meaning |
|---|---|---|
| **550** | 7 | `Integrity checksum changed` (File Integrity Monitoring / syscheck) |

Real alert behind rule 550:
```
File '/var/www/html/index.html' modified
Mode: realtime
Changed attributes: size,mtime,md5,sha1,sha256
```

This works because the lab tells the agent to watch `/etc/passwd` (and `/var/www/html` on
web01) in real time — see `roles/wazuh_agent/templates/ossec-extra.conf.j2`.

## Investigate
1. **What changed, exactly?** Wazuh reports the file and that its checksum changed. For
   `/etc/passwd`, diff it against a known-good baseline and read the new line:
   `sysupdate:x:0:0:...` — a second UID-0 account is a backdoor, full stop.
2. **When, and by whom?** The timestamp plus the `sudo`/auth logs around it tell you which
   account made the change — again, your real foothold.
3. **Is this the only change?** An attacker who edits `/etc/passwd` has root; check cron,
   SSH keys, systemd units, and the web root for anything else they planted.

## Contain and fix
- **Revert the file** from a known-good baseline (`./lab reset` does this for you here).
- **Remove the backdoor line** and any account it created; **find the foothold** that had
  root to make the change.
- **Keep FIM on everything that should be static:** `/etc/passwd`, `/etc/shadow`,
  `authorized_keys`, web roots, cron, binaries.
- **Serve web content read-only** (rebuild-and-replace, never edit in place) so defacement
  can't persist.

## Write it up
> At 18:5x FIM (Wazuh 550) flagged `/etc/passwd` modified on office01 and
> `/var/www/html/index.html` on web01. The passwd change added a UID-0 account
> (`sysupdate`) — a backdoor. Files reverted from baseline, backdoor removed, foothold
> investigated. Recommend read-only web content and keeping FIM on all critical paths.

Then `./lab reset`.
