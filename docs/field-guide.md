# IR Lab field guide — services, attacks, and how to defend

This is the blue-team companion to the lab. It explains every moving part: what each
service does and why it's there, every command the attacks run line by line, what that
same action looks like in a **real** breach, and how a defender detects and stops it.

The lab is deliberately small — one PC pretending to be a tiny company — but every
technique here is the real thing, scaled down. If you understand how the attacker gets
in and what trace they leave, you know where to put the tripwire. That is the whole
point: **you learn defence by watching the offence land.**

> Everything in this guide runs against machines you own, inside an isolated network
> that cannot reach the internet or your home LAN. The same commands pointed at a
> system you don't own are a crime. Keep them in the lab.

---

## 1. The company on one PC

```
                 internet (NAT)
                      │
              irlab-wan  10.19.0.0/24
                      │
                 ┌────┴─────┐
                 │ pfSense  │  firewall / router / DHCP / DNS
                 └────┬─────┘
          LAN  10.20.0.0/24 (irlab-lan)
          ┌───────────┼───────────┐
      web01         office01      wazuh
    10.20.0.10    10.20.0.20    10.20.0.30
    web server    workstation   SIEM (all-in-one)
          └───────────┼───────────┘
          mgmt 10.21.0.0/24 (irlab-mgmt, firewall-bypassing)
                      │
                   host PC  ← Ansible, dashboard, ./lab, attacks launch here
```

Two networks on purpose:

- **LAN (10.20.0.0/24)** is where the company lives and where attacks arrive, *through*
  pfSense. This is the "internet-facing" side in miniature.
- **Management (10.21.0.0/24)** is an out-of-band network that bypasses the firewall.
  It exists so that when a trainee blocks the attacker, they don't also lock out the
  instructor, Ansible, or the Wazuh dashboard. In the real world this is your
  **jump host / OOB management VLAN** — the network you keep clean so you can always
  reach a box even while it's under attack.

---

## 2. The services, and their real-world equivalents

### pfSense — the firewall / router
**In the lab:** the only door between the attacker's side and the company LAN. It does
NAT, hands out DHCP leases, resolves DNS (unbound), and — crucially — logs every packet
it drops. Those drop logs are shipped by syslog to Wazuh.

**Real world:** this is your perimeter firewall (Palo Alto, Fortinet, OPNsense, a cloud
security group). Its logs are the first place a network scan or a brute-force flood shows
up, because the noise hits the edge before it ever reaches a server. A firewall that
isn't sending logs to your SIEM is a camera that isn't recording.

**Why it matters for defence:** most of what an attacker does first — scanning, probing
closed ports — is *only* visible at the firewall. Rules 4100x/local firewall rules on the
Wazuh side turn "pfSense dropped 100 packets from one IP in 10 seconds" into one alert.

### Wazuh — the SIEM (all-in-one)
Wazuh is four services on one VM:

| Component | Job | Real-world equivalent |
|---|---|---|
| **wazuh-manager** | Receives agent logs, runs them through decoders + rules, raises alerts, enrols agents (ports 1514/1515), can run active responses | The detection brain — Splunk ES, Elastic Security, Sentinel analytics |
| **wazuh-indexer** | Stores every alert (it's OpenSearch under the hood), makes them searchable | The log store / data lake |
| **wazuh-dashboard** | The web UI you log into at `https://10.21.0.30` | The analyst's console |
| **filebeat** | Ships alerts from the manager into the indexer | The pipeline/forwarder |

**Real world:** a SIEM is where logs from everywhere land so that one analyst can see the
whole picture instead of SSH-ing into ten boxes. The lab's version is tiny, but the shape
is identical: **agents → manager (rules) → indexer (storage) → dashboard (humans).**

**A decoder** pulls fields out of a raw log line (this is the source IP, this is the
username). **A rule** says "when a decoded event looks like *this*, raise an alert at
*this* severity." Detection engineering — the actual job — is mostly writing and tuning
rules so the real attacks fire and the daily noise doesn't.

### wazuh-agent (on web01 and office01)
A small program on each protected machine. It:
- tails logs (`/var/log/auth.log`, the web server log) and forwards them,
- runs **FIM / syscheck** — it fingerprints important files and reports when one changes,
- runs **rootcheck** — looks for rootkit-like signs,
- holds a TLS connection to the manager on 1514.

**Real world:** this is your EDR / endpoint agent (CrowdStrike, Defender, osquery,
auditd+forwarder). It's how you see what happens *inside* a host — a new user, a modified
system file, a failed login — things the firewall never sees because they never crossed
the wire.

### web01 — the web server
A small order web app on port 80, reachable from the LAN through pfSense. It's the
**public-facing application** — the thing with an open port to the world, which is how a
huge share of real breaches start.

### office01 — the workstation
A Linux box with SSH and a normal user (`jdoe`). It stands in for an **employee machine
or a Linux server with remote login** — the target of password guessing and, once an
attacker is inside, of persistence and tampering.

---

## 3. The five attacks, line by line

Each scenario below has: the command(s), what every part does, the **real-world story**,
and **how you defend**. Run one with `./lab attack <name>`, then watch it in the
dashboard or confirm with `./lab check <name>`.

---

### 3.1 SSH brute force — `ssh-bruteforce` · MITRE **T1110**

**What the lab runs** (`attacks/ssh_bruteforce.py`): it opens SSH to office01 at
`10.20.0.20` *through the firewall*, as user `jdoe`, and tries a list of passwords one by
one, then finally the correct one (`Summer2026!`) to simulate a successful crack.

```python
client.connect(TARGET, username="jdoe", password=password, ...)
```
Each wrong password is a failed authentication; the final right one is a successful login
from the same IP that just failed ten times.

**The real-world story:** an attacker finds an SSH port exposed to the internet (Shodan
lists millions). They point a tool like **hydra** or **medusa** at it with a wordlist of
common passwords (`rockyou.txt` has 14 million). If any account uses a weak password,
they're in — and now they have a legitimate shell, no exploit required. This is one of the
most common ways servers get owned, precisely because it's boring and works.

Real command an attacker would use:
```bash
hydra -l jdoe -P rockyou.txt ssh://target
```

**What Wazuh sees:** a burst of `sshd` authentication failures (rule **5760** — SSH
authentication failed), escalated to a brute-force pattern (**5763 / 5712** — multiple
failures from one source), and then a **successful** login (**5715**) from that same IP.
The successful login *right after* a failure flood is the tell that the guess worked.

**How you defend:**
- **Keys, not passwords.** Set `PasswordAuthentication no` and the whole attack becomes
  impossible — there's nothing to guess.
- **fail2ban / rate limiting.** Ban an IP after N failures so the wordlist never finishes.
- **MFA** on SSH.
- **Alert on the pattern**, not just the failures: failure-flood *followed by* success is
  a near-certain compromise and should page someone.
- **Don't expose SSH to the internet** — put it behind a VPN or a jump host.

---

### 3.2 Port scan — `port-scan` · MITRE **T1046**

**What the lab runs** (`attacks/port_scan.py`):
```bash
nmap -sT -Pn -T4 --max-retries 1 --top-ports 100 10.20.0.0/27
```
- `-sT` — full TCP connect scan (completes the handshake; no raw-socket privilege needed).
- `-Pn` — skip host discovery; treat every address as up (hosts behind a firewall often
  don't answer pings, so this avoids missing them).
- `-T4` — fast timing.
- `--top-ports 100` — the 100 most common ports instead of all 65,535.
- `10.20.0.0/27` — the first 32 addresses of the LAN.

pfSense **drops most of this**, which is the point: the scan mostly hits the firewall, and
the firewall logs the drops.

**The real-world story:** reconnaissance. Before attacking, an adversary maps what's
alive and what's listening — which IPs answer, which ports are open, what software is
behind them. It's the digital equivalent of a burglar walking down the street trying door
handles. A scan by itself breaks nothing, but a scan from an unexpected source is often
the first visible move of an intrusion, and it tells you *you're being cased*.

**What Wazuh sees:** pfSense's firewall drop logs arrive by syslog. Wazuh correlates
"many blocked connections from one source in a short window" into a port-scan alert
(firewall/`pf` rules in the 4100x range plus scan-correlation rules). One noisy host
hitting dozens of closed ports lights up as a single high-signal event.

**How you defend:**
- **Default-deny** at the firewall so scans find almost nothing (as pfSense does here).
- **Alert on scan patterns**, and treat an internal host scanning its neighbours as a
  strong lateral-movement signal — that's not casual, that's an attacker already inside.
- **Reduce attack surface**: every closed port is one the attacker can't use. Only expose
  what must be exposed.

---

### 3.3 New admin account — `new-admin` · MITRE **T1136.001**

**What the lab runs** (`attacks/new_admin.py`), as an attacker already on office01:
```bash
sudo useradd -m -s /bin/bash svc-backup
sudo usermod -aG sudo svc-backup
```
- `useradd -m` — create the user `svc-backup` with a home directory.
- `-s /bin/bash` — give it a login shell.
- `usermod -aG sudo` — add it to the `sudo` group, i.e. **make it an administrator.**

The name `svc-backup` is chosen to look like a boring service account — attackers pick
names that blend in.

**The real-world story:** **persistence.** Once an attacker has a foothold, their first
worry is losing it — the password they cracked might get changed, the bug they exploited
might get patched. So they create their own account, ideally one that looks legitimate, so
they can walk back in through the front door any time. A hidden admin account is one of
the most common persistence mechanisms, and one of the most overlooked during cleanup —
teams patch the hole but forget to check *who can log in now.*

**What Wazuh sees:** the agent reads `/var/log/auth.log` and raises **5902** (new user
added) and a group-change event when the account joins `sudo`. A new privileged account
nobody filed a ticket for is a five-alarm event.

**How you defend:**
- **Alert on every account creation and every addition to a privileged group** — these are
  rare in normal operations, so the false-positive rate is low and the signal is gold.
- **Centralise identity** (LDAP/AD) so local accounts stand out as anomalies.
- **During incident response, always enumerate accounts** (`/etc/passwd`, group
  memberships, SSH `authorized_keys`) — eviction isn't done until you've checked who can
  still get in.
- **Least privilege:** fewer people/accounts with sudo means fewer ways to abuse it.

---

### 3.4 Web attack — `web-attack` · MITRE **T1190**

**What the lab runs** (`attacks/web_attack.py`): a series of malicious HTTP requests to
web01 with a `sqlmap/1.8` User-Agent, including SQL injection and path traversal:
```
GET /order?id=1' OR '1'='1
GET /order?id=1 UNION SELECT username,password FROM users--
GET /order?id=1; DROP TABLE orders--
GET /../../../../etc/passwd
GET /static/..%2f..%2f..%2fetc%2fpasswd
GET /index.php?page=../../../../etc/shadow
```
- The `'  OR '1'='1` and `UNION SELECT` strings are **SQL injection** — they try to make
  the database return data it shouldn't (like every user's password) or run commands.
- `DROP TABLE` tries to destroy data.
- `../../../../etc/passwd` is **path traversal** — climbing out of the web root to read
  system files. `..%2f` is the URL-encoded version, used to slip past naive filters.
- The `sqlmap` User-Agent is the calling card of the most popular automated SQLi tool.

**The real-world story:** attacking the **public-facing application** — the single biggest
category of real breaches, because web apps are, by definition, reachable by everyone.
SQL injection can dump an entire customer database; path traversal can leak credentials
and config; both can lead to full server takeover. Automated scanners (sqlmap, Burp,
Nikai/Nikto) fire thousands of these payloads at every exposed site, constantly.

**What Wazuh sees:** the web server log is forwarded to the agent, and Wazuh's web rules
fire on the signatures — **31103** (SQL injection pattern in a URL), **31104 / 31106**
(common web attack / path traversal), often tagged by the `sqlmap` User-Agent too. A
spray of 400/500 responses with injection strings is unmistakable.

**How you defend:**
- **Parameterised queries / prepared statements** — the actual fix for SQLi. The app
  stops treating input as code.
- **A WAF** in front of the app to drop known payloads (defence in depth, not a substitute
  for fixing the code).
- **Validate and canonicalise paths**; never build a file path from raw user input.
- **Alert on scanner User-Agents and injection signatures**, and **patch fast** — public
  apps are scanned within minutes of going live.

---

### 3.5 File tampering — `file-tamper` · MITRE **T1565.001**

**What the lab runs** (`attacks/file_tamper.py`), as an attacker already inside:
```bash
# on office01 — a hidden uid-0 (root-equivalent) account
echo 'sysupdate:x:0:0::/root:/bin/bash' | sudo tee -a /etc/passwd
# on web01 — deface the website
echo '<!-- owned -->' | sudo tee -a /var/www/html/index.html
```
- Appending `sysupdate:x:0:0:...` to `/etc/passwd` creates an account with **uid 0** — it
  *is* root, just under a different name. (In the lab it has no password so it can't
  actually log in; the point is the file change and the alert.)
- Appending to `index.html` stands in for **defacement / tampering** with served content.

**The real-world story:** **data and system manipulation.** Attackers alter files to plant
backdoors (a uid-0 line, a cron job, a modified SSH config), to deface sites for publicity,
or to quietly change data — a payroll figure, a shipping address, a log entry they're
erasing. The common thread: a file that should be static suddenly isn't, and if you're not
watching integrity, you never notice until the damage is done.

**What Wazuh sees:** **FIM / syscheck** fingerprinted these files when the agent started.
When their checksums change, the agent raises **550** (integrity checksum changed) — and
because `/etc/passwd` is a flagged critical file, it's high severity. This is detection by
*change*, not by signature: you don't need to know the specific attack, only that a
protected file moved.

**How you defend:**
- **File Integrity Monitoring** on the files that should never change on their own:
  `/etc/passwd`, `/etc/shadow`, `authorized_keys`, web roots, cron directories, binaries.
- **Immutable / read-only** deployment for things like web content (serve from a
  read-only mount or rebuild-and-replace, never edit in place).
- **Alert on changes to critical files immediately**, and keep **known-good baselines** so
  you can diff and restore.
- **Investigate the *how*:** a changed `/etc/passwd` means something already had root —
  the file change is the symptom; find the foothold.

---

## 4. From lab to a real server: the full attack chain

The five scenarios above are isolated snapshots. In a real intrusion they chain together,
and the same ideas apply directly to attacking (and therefore defending) a server such as
a Windows box. This is the exact shape of the Kali-vs-Windows-Server exercise run on your
own kit — mapped to defence:

| Stage | Lab scenario | Real tools (own-kit practice) | What a defender watches for |
|---|---|---|---|
| **Recon** | port-scan | `nmap`, `netexec` (nxc) host sweep | Scans at the firewall; internal host scanning peers |
| **Enumeration** | — | `enum4linux-ng`, `nxc smb`, share listing | Anonymous SMB/LDAP enumeration, null sessions |
| **Access** | ssh-bruteforce | `hydra`, `nxc` password spray, `evil-winrm` | Auth-failure floods, success-after-failure, logins at odd hours |
| **Credential theft** | — | `impacket secretsdump`, LSASS dumping | Access to SAM/LSASS, shadow-copy abuse |
| **Lateral movement** | — | pass-the-hash, `psexec`/`wmiexec`, PtH | New service installs, remote exec, auth with hashes |
| **Persistence** | new-admin | create account, add to admins, scheduled task | New privileged accounts, new services/tasks |
| **Impact** | file-tamper, web-attack | deface, encrypt, alter data | File-integrity alerts, mass changes, unexpected writes |

**The defender's reading of this:** you don't need to catch every step — you need
**tripwires at the stages that are rare in normal life.** Nobody legitimately creates a
new admin account at 3am right after a login that followed 200 failures. Each individual
step might be explainable; the *chain* is not. A good SIEM setup turns the chain into a
story, and your job is to make sure each link raises something.

---

## 5. The `./lab` command reference

| Command | What it does |
|---|---|
| `./lab up` | Build or start the whole lab from code (and take clean snapshots on first build) |
| `./lab status` | Show VM states, agent status, and whether the dashboard is up |
| `./lab attack <name>` | Run one scenario (`ssh-bruteforce`, `port-scan`, `new-admin`, `web-attack`, `file-tamper`) |
| `./lab check <name>` | Confirm the scenario's alert actually fired in Wazuh |
| `./lab reset` | Revert every VM to its clean snapshot — undoes all attacks for the next person |
| `./lab down` | Shut the VMs down, keep everything |
| `./lab destroy` | Remove the whole lab (VMs, networks, disks) — asks for confirmation |

The attacks refuse to run against anything outside `10.20.0.0/24` / `10.21.0.0/24`
(`attacks/guard.py`) — a hard guardrail so a typo can never send traffic off the lab.

---

## 6. If you remember five things

1. **The firewall sees recon; the endpoint sees the breach.** You need both feeding the
   SIEM, or you're half-blind.
2. **Failure-flood then success = compromise.** The success is the alert, not the failures.
3. **New privileged accounts and changed critical files are rare and loud** — the cheapest,
   highest-value alerts you can build.
4. **Fix the cause, not the symptom.** A defaced page or a rogue account means something
   already had access; find it.
5. **Least privilege and least surface** beat detection every time — the attack you make
   impossible needs no alert.
