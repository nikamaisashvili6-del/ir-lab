# 2 · Port scan (T1046)

## Run it
```bash
./lab attack port-scan
```
The script runs `nmap -sT -Pn -T4 --top-ports 100 10.20.0.0/27` from the attacker side —
knocking on the 100 most common ports of every host at the start of the LAN. pfSense drops
most of it. This is pure reconnaissance: mapping what's alive and what's listening before
committing to an attack. A real adversary does exactly this, often from a throwaway host.

## Find the alert

> ⚠️ **Known gap in this build.** Scan detection depends on pfSense forwarding its firewall
> log to Wazuh, which is **not wired up yet**. Wazuh is listening for syslog on
> `10.20.0.30:514`, but pfSense is not configured to send its `filterlog` there, so the
> dropped-packet flood from this scan does not currently raise an alert. This is the one
> scenario whose detection still needs finishing — see the field guide. The attack itself
> runs correctly; the detection is the open task.

**To finish it** (future work): enable Remote Logging on pfSense → point it at
`10.20.0.30:514` → include the firewall events. Wazuh's built-in pfSense/`pf` decoders then
turn the drop-flood into firewall alerts (rule family 4150x) which a scan-correlation rule
escalates.

## Investigate (what you *would* do)
A port scan shows up as **many blocked connections from one source to many ports in a short
window**. The questions:
1. **Where from?** An external source scanning the perimeter is background noise of the
   internet. An **internal** host scanning its neighbours is a red flag — that's an
   attacker who already has a foothold doing lateral reconnaissance.
2. **What did they find open?** Cross-reference the scanned ports with what's actually
   exposed. Every open port is a door you're choosing to leave unlocked.

## Contain and fix
- **Default-deny** at the firewall so scans find almost nothing (pfSense already drops most
  here — that's why so little reaches the hosts).
- **Alert on scan patterns**, and treat internal-to-internal scanning as a priority
  incident.
- **Shrink the attack surface:** close or firewall every port that doesn't need to be open.

## Write it up
> Host 10.19.0.1 performed a TCP connect scan of 10.20.0.0/27 (top-100 ports). pfSense
> dropped the traffic; no service was reached. Recommend wiring pfSense firewall logs into
> Wazuh so future scans alert, and reviewing exposed ports.

Then `./lab reset`.
