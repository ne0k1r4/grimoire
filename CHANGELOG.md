# Changelog

All notable changes to GRIMOIRE are documented here.

## [2.1.0] — 2026-05-29

### Added
- Wraith v2.1: crt.sh certificate transparency enumeration
- Wraith v2.1: subdomain takeover detection (30 service fingerprints)
- Wraith v2.1: WAF / CDN fingerprinting with probe requests
- Wraith v2.1: Shodan host intelligence lookup
- Sentinel module: auth.log / syslog / web / EVTX / custom log parsers
- Sentinel module: offline IOC scanner + anomaly engine
- `--help` output for every module
- config.example.json for API keys

### Fixed
- `wraith reverse_dns` crash on empty IP
- Sentinel IP extraction in the anomaly engine

## [2.0.0] — 2026-03-23

### Added
- Initial release
- TUI dashboard (curses) with live system stats and oplog
- Core: banner, oplog, sysinfo, report builder
- Wraith: passive recon (DNS, WHOIS, SSL, HTTP fingerprint, ports, subdomains)
- Forge: payload generator (15 shells, encoders, obfuscation)
- Voxcrypt: LSB steganography engine
- Phantom: pivot tracker
- Sovereign: C2 session manager
- Codex: target journal
- Vault: KeePassXC wrapper
- Web dashboard (Flask, localhost:1337)
- Arsenal Omega: Ghost Hollow, Silicon Death, Data Harvester
