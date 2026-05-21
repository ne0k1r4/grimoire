# Changelog

All notable changes to GRIMOIRE are documented here.

---

## [2.1.0] — 2026-05-20

### Added
- **WRAITH v2.1** — 4 new capabilities:
  - Certificate Transparency enumeration via crt.sh
  - Subdomain takeover detection — 30 service fingerprints (GitHub Pages, Heroku, Vercel, Netlify, AWS S3, Azure, Fastly, and more)
  - WAF / CDN fingerprinting — Cloudflare, Akamai, AWS WAF, Imperva, Sucuri, F5 BIG-IP, Fastly, Barracuda, ModSecurity
  - Shodan host intelligence — open ports, banners, CVEs, CPEs (API key required)
- **SENTINEL v1.0** — new blue team detection module:
  - `auth.log` parser — brute force, SSH failures, sudo abuse, new accounts
  - `syslog` parser — suspicious processes, rootkit indicators, SUID changes
  - Apache/Nginx access log parser — SQLi, XSS, path traversal, web shells, scanners
  - Windows Event Log parser (`.evtx`) — 17 critical Event IDs
  - Custom log parser — regex-based detection on any log format
  - IOC scanner — AbuseIPDB + VirusTotal with offline fallback
  - 6-rule anomaly detection engine
  - Live tail mode — real-time log monitoring
  - `--scan`, `--watch`, `--ioc` CLI flags

### Fixed
- `reverse_dns()` in WRAITH now catches `socket.gaierror` in addition to `socket.herror`
- All modules now support `--help` / `-h` flags with full usage documentation
- Anomaly engine IP extraction fixed — ANSI color codes no longer break regex parsing

### Changed
- `full_scan` in WRAITH now automatically runs crt.sh, WAF detection, and takeover checks
- WRAITH scan summary updated to show WAF and takeover results
- Version bumped to 2.1.0

---

## [2.0.0] — 2026-05-01

### Added
- Initial release of GRIMOIRE unified operator suite
- **Core** — TUI dashboard (curses), CLI dispatcher, op log
- **Wraith v2.0** — DNS, WHOIS, SSL/TLS, HTTP fingerprinting, subdomain probe, port probe, geolocation, report export
- **Forge** — 15 reverse shell templates, 5 encoders, 3 obfuscators, listener generator
- **Voxcrypt** — LSB image/audio steganography, ZWC text injection, XOR-SHA256 cipher with HMAC integrity
- **Phantom** — pivot tracker, SSH/Chisel/Ligolo command generator, ASCII chain map
- **Sovereign** — multi-session C2 TCP listener, per-session logging
- **Codex** — target journal, risk scoring, findings, markdown report export
- **Vault** — KeePassXC CLI wrapper
- **Web** — local Flask dashboard with live op log

---
