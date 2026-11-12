# 4 · Web attack — SQLi + path traversal (T1190)

## Run it
```bash
./lab attack web-attack
./lab check  web-attack
```
The script fires a series of malicious HTTP requests at web01 with a `sqlmap/1.8`
User-Agent — SQL injection and path traversal, the two most common ways a public web app
gets broken. Real attackers run automated tools (sqlmap, Burp, Nikto) that spray thousands
of these at every exposed site, constantly.

## Find the alert
On agent **web01**:

| Rule | Level | Meaning |
|---|---|---|
| **31103** | 7 | `SQL injection attempt` |
| **31104** | 6 | `Common web attack` (path traversal, etc.) |
| **31101** | 5 | `Web server 400 error code` |

Real log line behind rule 31104:
```
10.19.0.1 - - [12/Nov/2026:18:54:02 +0000] "GET /index.php?page=../../../../etc/shadow HTTP/1.1" 404 162 "-" "sqlmap/1.8"
```

## Investigate
1. **What were they trying to read or run?** Read the URLs. `UNION SELECT username,password
   FROM users` is trying to dump credentials; `../../../../etc/shadow` is trying to read
   password hashes off disk; `DROP TABLE` is trying to destroy data.
2. **Did anything succeed?** Check the HTTP status codes. `404`/`400` means the payload
   missed. A `200` on an injection URL — or an unusually large response — means it may have
   *worked*, and you've potentially lost whatever that query returned.
3. **Who?** The `sqlmap/1.8` User-Agent and the source IP. A real attacker may fake the
   User-Agent, but the payloads themselves are the giveaway.

## Contain and fix
- **The real fix is in the code:** parameterised queries / prepared statements so user
  input can never be executed as SQL. A WAF in front helps but is not a substitute.
- **Validate and canonicalise file paths** — never build a path from raw user input — to
  kill traversal.
- **Block the source** and, if any payload returned `200`, treat it as a data breach:
  assume what that query could reach is compromised and rotate it.
- **Alert on scanner User-Agents and injection signatures**, and patch public apps fast —
  they're scanned within minutes of going live.

## Write it up
> At 18:54 web01 received SQL-injection and path-traversal requests from 10.19.0.1
> (`sqlmap/1.8`), caught by Wazuh 31103/31104. All returned 404/400 — no payload
> succeeded. Source blocked. Recommend code review for parameterised queries and a WAF.

Then `./lab reset`.
