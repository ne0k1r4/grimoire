<div align="center">

```
  ██████╗ ██████╗ ██╗███╗   ███╗ ██████╗ ██╗██████╗ ███████╗
 ██╔════╝ ██╔══██╗██║████╗ ████║██╔═══██╗██║██╔══██╗██╔════╝
 ██║  ███╗██████╔╝██║██╔████╔██║██║   ██║██║██████╔╝█████╗
 ██║   ██║██╔══██╗██║██║╚██╔╝██║██║   ██║██║██╔══██╗██╔══╝
 ╚██████╔╝██║  ██║██║██║ ╚═╝ ██║╚██████╔╝██║██║  ██║███████╗
  ╚═════╝ ╚═╝  ╚═╝╚═╝╚═╝     ╚═╝ ╚═════╝ ╚═╝╚═╝  ╚═╝╚══════╝
```

*"I will write your name in this book."*

[![Version](https://img.shields.io/badge/version-2.1.0-cc0000?style=for-the-badge&labelColor=0a0000)](https://github.com/ne0k1r4/grimoire/releases)
[![Python](https://img.shields.io/badge/python-3.8+-cc0000?style=for-the-badge&logo=python&logoColor=white&labelColor=0a0000)](https://python.org)
[![License](https://img.shields.io/badge/license-MIT-cc0000?style=for-the-badge&labelColor=0a0000)](LICENSE)
[![Platform](https://img.shields.io/badge/platform-Linux-cc0000?style=for-the-badge&labelColor=0a0000)](https://archlinux.org)
[![Author](https://img.shields.io/badge/author-ne0k1r4-cc0000?style=for-the-badge&labelColor=0a0000)](https://github.com/ne0k1r4)

**A modular Death Note-themed operator suite.**  
Passive recon · Payload generation · Steganography · Pivot tracking · C2 · Blue team detection.

</div>

---

## Modules

| Module | Command | Description |
|--------|---------|-------------|
| 🖥️ **Core** | `grimoire` | TUI dashboard · CLI dispatcher · op log |
| 👁️ **Wraith** | `grimoire wraith` | Passive recon · crt.sh · WAF detection · subdomain takeover · Shodan |
| 💣 **Forge** | `grimoire forge` | 15 reverse shells · 5 encoders · 3 obfuscators · listener gen |
| 🕸️ **Voxcrypt** | `grimoire voxcrypt` | LSB PNG/WAV stego · ZWC text · XOR-SHA256 cipher |
| 🌐 **Phantom** | `grimoire phantom` | Pivot tracker · SSH/Chisel/Ligolo cmd gen · ASCII chain map |
| ☠️ **Sovereign** | `grimoire sovereign` | C2 listener · multi-session · command history · disk logs |
| 📓 **Codex** | `grimoire codex` | Target journal · risk scoring · findings · MD report |
| 🛡️ **Sentinel** | `grimoire sentinel` | Log analysis · IOC scanner · anomaly detection · live tail |
| 🔐 **Vault** | `grimoire vault` | KeePassXC CLI wrapper · credential search |
| 🌍 **Web** | `grimoire web` | Local Flask dashboard · live op log · `/api/*` endpoints |

---

## Install

```bash
git clone git@github.com:ne0k1r4/grimoire.git
cd grimoire
pip install -e . --break-system-packages
```

> Pure Python stdlib — no heavy dependencies. Flask required only for `grimoire web`.

---

## Quick Start

```bash
grimoire                              # TUI dashboard
grimoire wraith target.com            # passive recon
grimoire wraith target.com --report   # recon + markdown report
grimoire forge                        # payload generator
grimoire sentinel --ioc 1.2.3.4       # IOC reputation check
grimoire sentinel --scan /var/log     # log analysis
grimoire sentinel --watch /var/log/auth.log  # live tail
grimoire codex                        # target journal
grimoire phantom                      # pivot tracker
grimoire sovereign                    # C2 listener
grimoire voxcrypt                     # steganography
```

---

## Module Details

<details>
<summary><b>👁️ WRAITH v2.1 — Passive Recon</b></summary>
<br>

No active scanning. All passive intelligence gathering.

- DNS resolution (A / AAAA / MX) + Reverse DNS
- SSL/TLS certificate inspection (SANs, issuer, cipher, expiry)
- HTTP header fingerprinting + tech stack detection
- `robots.txt` and `security.txt` harvesting
- IP geolocation + ASN lookup via ipinfo.io
- WHOIS lookup
- Top-20 TCP port probe
- 70-word subdomain enumeration
- **Certificate Transparency** enumeration via crt.sh
- **Subdomain Takeover** detection — 30 known service fingerprints
- **WAF / CDN fingerprinting** — Cloudflare, Akamai, AWS WAF, Imperva, Sucuri, F5, Fastly, Barracuda, ModSecurity
- **Shodan** host intelligence — ports, banners, CVEs (API key required)
- Markdown + HTML report export

```bash
grimoire wraith target.com
grimoire wraith target.com --report
# Interactive: crt | waf | takeover | shodan <ip>
```

</details>

<details>
<summary><b>🛡️ SENTINEL v1.0 — Blue Team Detection</b></summary>
<br>

Log analysis, threat intelligence, and anomaly detection.

**Log Parsers:**
- `auth.log` — brute force, SSH failures, invalid users, sudo abuse, new accounts
- `syslog` / `messages` — suspicious processes, cron abuse, rootkit indicators, SUID changes
- Apache / Nginx access logs — SQLi, XSS, path traversal, web shells, scanners, 404 floods
- Windows Event Logs (`.evtx`) — 17 Event IDs including 4625, 4672, 4720, 7045, 1102
- Custom log files — regex-based anomaly detection on any format

**IOC Scanner:**
- AbuseIPDB — IP reputation (free API key, 1000 checks/day)
- VirusTotal — IP / domain / hash lookup (free API key, 4 req/min)
- Offline fallback — known malicious IP ranges, DGA domain detection, malware hash DB

**Anomaly Detection (6 rules):**
- Brute force aggregation — 5+ failures from same IP
- Privilege escalation — failed auth followed by sudo
- Reverse shell patterns in logs
- Account creation combined with group modification
- Web attack patterns — web shells + SQLi chains
- Audit log cleared (Windows Event 1102)

```bash
grimoire sentinel --ioc 185.220.101.1        # IOC check
grimoire sentinel --scan /var/log --report   # full scan
grimoire sentinel --watch /var/log/auth.log  # live tail

# API keys in ~/.grimoire/config.json:
# { "abuseipdb_api_key": "...", "virustotal_api_key": "..." }
```

</details>

<details>
<summary><b>💣 FORGE — Payload Generator</b></summary>
<br>

**15 shell templates:**  
`bash_tcp` · `bash_udp` · `python3_tcp` · `python3_pty` · `python3_win` ·
`nc_mkfifo` · `nc_e` · `socat_tcp` · `socat_tty` · `php_proc` · `perl_tcp` ·
`ruby_tcp` · `awk` · `powershell` · `java`

**5 encoders:** `base64` · `base64_exec` · `hex` · `url` · `unicode`

**3 obfuscators:** `bash_var` · `ps_char` · `b64_exec`

Listener command generator + save-to-file (`~/.grimoire/payloads/`)

</details>

<details>
<summary><b>🕸️ VOXCRYPT — Steganography Engine</b></summary>
<br>

- **LSB encoding** into PNG/BMP images and WAV audio
- **Zero-width character** injection into plain text
- **XOR-SHA256 stream cipher** with zlib compression
- **HMAC-SHA256 integrity verification** — detects tampering

</details>

<details>
<summary><b>🌐 PHANTOM — Pivot Tracker</b></summary>
<br>

- Track pivot hops: source, destination, type, status, notes
- SSH command generator — `-L` local, `-R` remote, `-D` SOCKS5
- Chisel and Ligolo command templates
- ASCII chain map of the full pivot path
- Status: `PENDING → ACTIVE → BROKEN → CLOSED`

</details>

<details>
<summary><b>☠️ SOVEREIGN — C2 Manager</b></summary>
<br>

- TCP listener with multi-session support
- Per-session command history and disk logging (`~/.grimoire/sessions/`)
- `interact <sid>` to drop into a live shell
- Session rename, background, kill

</details>

<details>
<summary><b>📓 CODEX — Target Journal</b></summary>
<br>

- Add targets with risk scoring (`CRITICAL / HIGH / MEDIUM / LOW / INFO`)
- Log findings per target with timestamps and tags
- Status history: `WATCHING → ACTIVE → OWNED → CLOSED`
- Export full engagement report to Markdown

</details>

---

## Data Locations

```
~/.grimoire/
├── config.json         API keys (Shodan, AbuseIPDB, VirusTotal)
├── codex.json          targets and findings
├── oplog.json          operation log (last 2000 entries)
├── phantom.json        pivot map
├── payloads/           forge-generated payloads
├── reports/            wraith + codex + sentinel exports
└── sessions/           sovereign shell session logs
```

---

## Architecture

```
grimoire/
├── core/               TUI · CLI dispatcher · banner · sysinfo · oplog
├── utils/              color engine · ReportBuilder · uid helpers
├── wraith/             passive recon engine
├── forge/              payload generator
├── voxcrypt/           steganography engine
├── phantom/            network pivot tracker
├── sovereign/          C2 session manager
├── codex/              target journal
├── sentinel/           blue team detection engine
├── vault/              KeePassXC wrapper
└── web/                Flask local dashboard
```

---

## TUI Keybinds

| Key | Action |
|-----|--------|
| `↑` `↓` | Navigate modules |
| `ENTER` | Launch module |
| `H` | Toggle help |
| `R` | Refresh system stats |
| `Q` | Quit |

---

## Changelog

See [CHANGELOG.md](CHANGELOG.md)

---

## Disclaimer

For authorized penetration testing, CTF use, and educational purposes only.  
The developer is not responsible for misuse of this tool.

---

<div align="center">
<br>
<i>"From here, I will change the world." — Light Yagami</i>
<br><br>

[![GitHub](https://img.shields.io/badge/github.com%2Fne0k1r4-cc0000?style=flat-square&labelColor=0a0000&logo=github&logoColor=white)](https://github.com/ne0k1r4)

</div>
