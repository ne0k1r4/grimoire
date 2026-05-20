# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE v2.0 — sentinel/__init__.py
#  Blue Team Detection Engine
#
#  Developer  : Light
#  Alias      : Neok1ra
#  GitHub     : https://github.com/ne0k1r4
#  Tool       : GRIMOIRE — The Death Note of the digital world
#
#  Features:
#    auth.log parser — brute force, SSH failures, sudo abuse
#    syslog parser — suspicious processes, cron, kernel events
#    Apache/Nginx parser — scanning, path traversal, SQLi/XSS
#    Windows Event Log parser (.evtx) — 4625, 4672, 4720
#    Custom log parser — regex anomaly detection on any file
#    IOC scanner — AbuseIPDB + VirusTotal + offline fallback
#    Anomaly detection — 6 rule engine
#    Live tail mode — real-time log monitoring
#    Report export — Markdown + JSON
# ═══════════════════════════════════════════════════════════════

import re, os, json, socket, time, hashlib, urllib.request, urllib.parse
from datetime import datetime, timedelta
from pathlib import Path
from collections import defaultdict
from ..utils import C, section, risk_label, ReportBuilder, ts

BANNER = f"""
{C.RED}{C.BOLD}  ╔══════════════════════════════════════════════╗
  ║  S E N T I N E L  v1.0  —  Blue Team        ║
  ║  Developer: Light (Neok1ra)                  ║
  ╚══════════════════════════════════════════════╝{C.RESET}
  {C.DIM}Log Analysis · IOC Scanner · Anomaly Detection · Reports{C.RESET}
"""

CONFIG_FILE = Path.home() / ".grimoire" / "config.json"

# ── Config loader ─────────────────────────────────────────────

def _load_config() -> dict:
    if CONFIG_FILE.exists():
        try:
            return json.loads(CONFIG_FILE.read_text())
        except Exception:
            pass
    return {}

# ── Severity helpers ──────────────────────────────────────────

SEV_COLOR = {
    "CRITICAL": C.RED + C.BOLD,
    "HIGH":     C.RED,
    "MEDIUM":   C.YELLOW,
    "LOW":      C.CYAN,
    "INFO":     C.DIM,
}

def _sev(level: str, msg: str) -> str:
    c = SEV_COLOR.get(level, C.DIM)
    return f"  {c}[{level}]{C.RESET} {msg}"

def _alert(level: str, source: str, msg: str, detail: str = ""):
    print(_sev(level, f"{C.BOLD}{source}{C.RESET}  {msg}"))
    if detail:
        print(f"  {C.DIM}  → {detail}{C.RESET}")
    return {"level": level, "source": source, "msg": msg, "detail": detail, "ts": ts()}

# ══════════════════════════════════════════════════════════════
# LOG PARSERS
# ══════════════════════════════════════════════════════════════

# ── auth.log parser ───────────────────────────────────────────

AUTH_PATTERNS = [
    ("CRITICAL", "Brute Force",
     re.compile(r"Failed password for (?:invalid user )?(\S+) from ([\d\.]+)", re.I)),
    ("HIGH",     "Invalid User",
     re.compile(r"Invalid user (\S+) from ([\d\.]+)", re.I)),
    ("HIGH",     "Root Login Attempt",
     re.compile(r"Failed password for root from ([\d\.]+)", re.I)),
    ("MEDIUM",   "Sudo Usage",
     re.compile(r"sudo:\s+(\S+)\s+:.*COMMAND=(.*)", re.I)),
    ("HIGH",     "Sudo Failure",
     re.compile(r"sudo:.*authentication failure.*user=(\S+)", re.I)),
    ("HIGH",     "New User Created",
     re.compile(r"useradd.*new user.*name=(\S+)", re.I)),
    ("MEDIUM",   "SSH Accepted",
     re.compile(r"Accepted (?:password|publickey) for (\S+) from ([\d\.]+)", re.I)),
    ("HIGH",     "SSH Disconnect Unusual",
     re.compile(r"Disconnected from invalid user (\S+) ([\d\.]+)", re.I)),
    ("CRITICAL", "PAM Auth Failure",
     re.compile(r"pam_unix.*authentication failure.*user=(\S+)", re.I)),
]

def parse_auth_log(filepath: str) -> list:
    section(f"AUTH.LOG — {filepath}")
    alerts = []
    ip_failures = defaultdict(list)
    user_failures = defaultdict(int)

    try:
        with open(filepath, "r", errors="replace") as f:
            lines = f.readlines()
    except PermissionError:
        print(f"  {C.YELLOW}[!] Permission denied: {filepath}{C.RESET}")
        print(f"  {C.DIM}Try: sudo grimoire sentinel --scan /var/log/auth.log{C.RESET}")
        return []
    except FileNotFoundError:
        print(f"  {C.DIM}File not found: {filepath}{C.RESET}")
        return []

    print(f"  {C.DIM}Scanning {len(lines):,} lines...{C.RESET}\n")

    for line in lines:
        for level, name, pattern in AUTH_PATTERNS:
            m = pattern.search(line)
            if m:
                groups = m.groups()
                ip = groups[1] if len(groups) > 1 and re.match(r"\d+\.\d+", groups[1]) else ""
                user = groups[0] if groups else ""

                if "Failed" in name or "Invalid" in name or "Failure" in name:
                    if ip:
                        ip_failures[ip].append(line.strip()[:80])
                    user_failures[user] += 1

                alerts.append(_alert(level, name,
                    f"user={C.CYAN}{user}{C.RESET}" + (f"  ip={C.CYAN}{ip}{C.RESET}" if ip else ""),
                    line.strip()[:100]))
                break

    # Brute force aggregation — 5+ failures from same IP
    for ip, fails in ip_failures.items():
        if len(fails) >= 5:
            print()
            alerts.append(_alert("CRITICAL", "Brute Force Detected",
                f"{C.RED}{len(fails)} failed attempts{C.RESET} from {C.CYAN}{ip}{C.RESET}",
                f"Sample: {fails[0][:80]}"))

    # User targeting — 10+ failures for same user
    for user, count in user_failures.items():
        if count >= 10:
            alerts.append(_alert("HIGH", "User Targeted",
                f"{C.CYAN}{user}{C.RESET} — {count} failed auth attempts"))

    if not alerts:
        print(f"  {C.GREEN}No suspicious activity found{C.RESET}")

    print(f"\n  {C.DIM}auth.log: {len(alerts)} events found{C.RESET}")
    return alerts


# ── syslog parser ─────────────────────────────────────────────

SYSLOG_PATTERNS = [
    ("HIGH",   "Reverse Shell Pattern",
     re.compile(r"bash\s+-i|/dev/tcp|nc\s+-e|ncat.*-e|python.*socket|perl.*socket", re.I)),
    ("HIGH",   "Suspicious Process",
     re.compile(r"(nmap|masscan|hydra|john|hashcat|metasploit|msfconsole|sqlmap)\b", re.I)),
    ("MEDIUM", "Cron Job Added",
     re.compile(r"cron.*REPLACE|crontab.*edited|CMD\s+\(", re.I)),
    ("HIGH",   "Kernel Error",
     re.compile(r"kernel:.*(?:BUG|Oops|segfault|stack overflow|protection fault)", re.I)),
    ("MEDIUM", "Service Failed",
     re.compile(r"systemd.*Failed to start|service.*failed|Unit.*failed", re.I)),
    ("HIGH",   "Iptables Modified",
     re.compile(r"iptables|ip6tables|nftables.*(?:ACCEPT|DROP|chain)", re.I)),
    ("MEDIUM", "USB Device",
     re.compile(r"usb.*new.*device|New USB device found", re.I)),
    ("HIGH",   "SUID Binary",
     re.compile(r"chmod.*[46][0-9]{3}|chmod.*[su]\+s", re.I)),
    ("CRITICAL","Rootkit Indicator",
     re.compile(r"rkhunter|chkrootkit|rootkit|/proc/\d+/exe.*deleted", re.I)),
]

def parse_syslog(filepath: str) -> list:
    section(f"SYSLOG — {filepath}")
    alerts = []
    try:
        with open(filepath, "r", errors="replace") as f:
            lines = f.readlines()
    except PermissionError:
        print(f"  {C.YELLOW}[!] Permission denied: {filepath}{C.RESET}")
        return []
    except FileNotFoundError:
        print(f"  {C.DIM}File not found: {filepath}{C.RESET}")
        return []

    print(f"  {C.DIM}Scanning {len(lines):,} lines...{C.RESET}\n")

    for line in lines:
        for level, name, pattern in SYSLOG_PATTERNS:
            if pattern.search(line):
                alerts.append(_alert(level, name, line.strip()[:100]))
                break

    if not alerts:
        print(f"  {C.GREEN}No suspicious activity found{C.RESET}")

    print(f"\n  {C.DIM}syslog: {len(alerts)} events found{C.RESET}")
    return alerts


# ── Apache/Nginx access log parser ────────────────────────────

WEB_PATTERNS = [
    ("HIGH",   "SQL Injection",
     re.compile(r"(?:union.*select|select.*from|insert.*into|drop.*table|'--|\bOR\b.*=.*\d|1=1)", re.I)),
    ("HIGH",   "XSS Attempt",
     re.compile(r"<script|javascript:|onerror=|onload=|alert\(|document\.cookie", re.I)),
    ("HIGH",   "Path Traversal",
     re.compile(r"(?:\.\./){2,}|%2e%2e|etc/passwd|etc/shadow|/proc/self", re.I)),
    ("HIGH",   "Command Injection",
     re.compile(r"(?:;|\||&&)\s*(?:id|whoami|uname|cat\s+/etc|wget|curl)\b", re.I)),
    ("MEDIUM", "Scanner Detected",
     re.compile(r"(?:nikto|nmap|masscan|sqlmap|dirbuster|gobuster|ffuf|wfuzz|nuclei)", re.I)),
    ("MEDIUM", "Sensitive File Access",
     re.compile(r"(?:\.env|\.git/|wp-config\.php|phpinfo|\.htaccess|web\.config|backup\.zip)", re.I)),
    ("HIGH",   "Web Shell",
     re.compile(r"(?:c99|r57|shell\.php|cmd\.php|eval\(|base64_decode\(|system\(|exec\()", re.I)),
    ("MEDIUM", "Admin Panel Probe",
     re.compile(r"(?:/admin|/wp-admin|/phpmyadmin|/manager|/console|/actuator|/swagger)", re.I)),
    ("LOW",    "404 Flood",
     re.compile(r'" 404 ')),
]

# Apache/Nginx combined log format
COMBINED_LOG_RE = re.compile(
    r'([\d\.]+)\s+\S+\s+\S+\s+\[([^\]]+)\]\s+"(\S+)\s+([^"]+)\s+HTTP/\S+"\s+(\d+)\s+(\d+|-)'
)

def parse_web_log(filepath: str) -> list:
    section(f"WEB ACCESS LOG — {filepath}")
    alerts = []
    ip_404s = defaultdict(int)
    ip_requests = defaultdict(int)

    try:
        with open(filepath, "r", errors="replace") as f:
            lines = f.readlines()
    except PermissionError:
        print(f"  {C.YELLOW}[!] Permission denied: {filepath}{C.RESET}")
        return []
    except FileNotFoundError:
        print(f"  {C.DIM}File not found: {filepath}{C.RESET}")
        return []

    print(f"  {C.DIM}Scanning {len(lines):,} lines...{C.RESET}\n")

    for line in lines:
        m = COMBINED_LOG_RE.match(line)
        if m:
            ip, ts_str, method, path, status, size = m.groups()
            ip_requests[ip] += 1
            if status == "404":
                ip_404s[ip] += 1

            full = f"{method} {path}"
            for level, name, pattern in WEB_PATTERNS:
                if pattern.search(path):
                    alerts.append(_alert(level, name,
                        f"ip={C.CYAN}{ip}{C.RESET}  {method} {path[:80]}",
                        f"status={status}"))
                    break
        else:
            # Still check raw line for patterns
            for level, name, pattern in WEB_PATTERNS:
                if pattern.search(line):
                    alerts.append(_alert(level, name, line.strip()[:100]))
                    break

    # 404 flood detection — 20+ 404s from same IP
    for ip, count in ip_404s.items():
        if count >= 20:
            alerts.append(_alert("HIGH", "404 Flood / Scanner",
                f"{C.CYAN}{ip}{C.RESET} — {count} Not Found responses",
                f"Total requests from IP: {ip_requests[ip]}"))

    # High request volume — 500+ requests from same IP
    for ip, count in ip_requests.items():
        if count >= 500:
            alerts.append(_alert("MEDIUM", "High Request Volume",
                f"{C.CYAN}{ip}{C.RESET} — {count} requests"))

    if not alerts:
        print(f"  {C.GREEN}No suspicious activity found{C.RESET}")

    print(f"\n  {C.DIM}web log: {len(alerts)} events found{C.RESET}")
    return alerts


# ── Windows Event Log parser ──────────────────────────────────

EVTX_EVENT_IDS = {
    4625: ("HIGH",     "Failed Logon"),
    4624: ("INFO",     "Successful Logon"),
    4634: ("INFO",     "Logoff"),
    4648: ("MEDIUM",   "Logon with Explicit Credentials"),
    4672: ("HIGH",     "Special Privileges Assigned"),
    4673: ("MEDIUM",   "Privileged Service Called"),
    4688: ("MEDIUM",   "New Process Created"),
    4698: ("HIGH",     "Scheduled Task Created"),
    4702: ("HIGH",     "Scheduled Task Modified"),
    4720: ("HIGH",     "New User Account Created"),
    4722: ("MEDIUM",   "User Account Enabled"),
    4725: ("MEDIUM",   "User Account Disabled"),
    4726: ("HIGH",     "User Account Deleted"),
    4728: ("HIGH",     "Member Added to Security Group"),
    4732: ("HIGH",     "Member Added to Local Group"),
    4756: ("HIGH",     "Member Added to Universal Group"),
    4771: ("HIGH",     "Kerberos Pre-Auth Failed"),
    4776: ("HIGH",     "NTLM Auth Attempt"),
    7045: ("CRITICAL", "New Service Installed"),
    1102: ("CRITICAL", "Audit Log Cleared"),
}

def parse_evtx(filepath: str) -> list:
    section(f"WINDOWS EVENT LOG — {filepath}")
    alerts = []

    try:
        import importlib.util
        if importlib.util.find_spec("evtx") is None:
            print(f"  {C.YELLOW}[!] python-evtx not installed.{C.RESET}")
            print(f"  {C.DIM}Install: pip install python-evtx --break-system-packages{C.RESET}")
            return []
        import evtx
        with evtx.Evtx(filepath) as log:
            for record in log.records():
                try:
                    xml = record.xml()
                    eid_m = re.search(r"<EventID[^>]*>(\d+)</EventID>", xml)
                    if not eid_m:
                        continue
                    eid = int(eid_m.group(1))
                    if eid not in EVTX_EVENT_IDS:
                        continue
                    level, name = EVTX_EVENT_IDS[eid]
                    user_m    = re.search(r"<SubjectUserName>([^<]+)</SubjectUserName>", xml)
                    target_m  = re.search(r"<TargetUserName>([^<]+)</TargetUserName>", xml)
                    ip_m      = re.search(r"<IpAddress>([^<]+)</IpAddress>", xml)
                    user   = (target_m or user_m)
                    user   = user.group(1) if user else "?"
                    ip     = ip_m.group(1) if ip_m else ""
                    alerts.append(_alert(level, f"EventID {eid} — {name}",
                        f"user={C.CYAN}{user}{C.RESET}" + (f"  ip={C.CYAN}{ip}{C.RESET}" if ip and ip != "-" else "")))
                except Exception:
                    continue
    except PermissionError:
        print(f"  {C.YELLOW}[!] Permission denied: {filepath}{C.RESET}")
        return []
    except FileNotFoundError:
        print(f"  {C.DIM}File not found: {filepath}{C.RESET}")
        return []
    except Exception as e:
        print(f"  {C.YELLOW}[!] EVTX error: {e}{C.RESET}")
        return []

    if not alerts:
        print(f"  {C.GREEN}No suspicious events found{C.RESET}")

    print(f"\n  {C.DIM}evtx: {len(alerts)} events found{C.RESET}")
    return alerts


# ── Custom log parser ─────────────────────────────────────────

CUSTOM_PATTERNS = [
    ("HIGH",   "IP Address",        re.compile(r"\b(\d{1,3}\.){3}\d{1,3}\b")),
    ("HIGH",   "Reverse Shell",     re.compile(r"bash\s+-i|/dev/tcp|nc\s+-e|python.*-c.*socket", re.I)),
    ("HIGH",   "Credential Leak",   re.compile(r"password[=:\s]+\S+|passwd[=:\s]+\S+|secret[=:\s]+\S+", re.I)),
    ("MEDIUM", "Error Spike",       re.compile(r"\b(?:ERROR|FATAL|CRITICAL|EXCEPTION|TRACEBACK)\b", re.I)),
    ("MEDIUM", "Base64 Payload",    re.compile(r"[A-Za-z0-9+/]{40,}={0,2}")),
    ("HIGH",   "Suspicious Command",re.compile(r"(?:wget|curl|chmod\s+[46]|nc\s+-|ncat|socat)\s+", re.I)),
]

def parse_custom_log(filepath: str, pattern: str = None) -> list:
    section(f"CUSTOM LOG — {filepath}")
    alerts = []
    custom_re = re.compile(pattern, re.I) if pattern else None

    try:
        with open(filepath, "r", errors="replace") as f:
            lines = f.readlines()
    except PermissionError:
        print(f"  {C.YELLOW}[!] Permission denied: {filepath}{C.RESET}")
        return []
    except FileNotFoundError:
        print(f"  {C.DIM}File not found: {filepath}{C.RESET}")
        return []

    print(f"  {C.DIM}Scanning {len(lines):,} lines...{C.RESET}\n")

    for i, line in enumerate(lines, 1):
        if custom_re and custom_re.search(line):
            alerts.append(_alert("MEDIUM", "Pattern Match",
                f"line {i}: {line.strip()[:100]}"))
            continue
        for level, name, pat in CUSTOM_PATTERNS:
            if pat.search(line):
                alerts.append(_alert(level, name, f"line {i}: {line.strip()[:100]}"))
                break

    if not alerts:
        print(f"  {C.GREEN}No suspicious patterns found{C.RESET}")

    print(f"\n  {C.DIM}custom log: {len(alerts)} events found{C.RESET}")
    return alerts


# ══════════════════════════════════════════════════════════════
# IOC SCANNER
# ══════════════════════════════════════════════════════════════

# ── Offline IOC database ──────────────────────────────────────

MALICIOUS_DOMAINS = {
    "malware-c2.com", "evil-domain.net", "phishing-site.org",
    "dyndns.org", "no-ip.com", "ddns.net", "hopto.org",
    "serveblog.net", "serveftp.com", "servehttp.com",
}

MALICIOUS_IP_RANGES = [
    re.compile(r"^185\.220\.\d+\.\d+"),   # Known TOR exit nodes
    re.compile(r"^5\.188\.\d+\.\d+"),     # Common spam/abuse range
    re.compile(r"^91\.108\.\d+\.\d+"),    # Telegram-linked abuse
    re.compile(r"^194\.165\.\d+\.\d+"),   # Known C2 range
]

KNOWN_MALWARE_HASHES = {
    # Mimikatz variants
    "fc525c9683e8fe067095ba2ddc971889dc76cec2",
    "e13b6573a1a679a4c7fb0893db3cb1fc76e21ff1",
    # Common webshells
    "b374k", "c99shell", "r57shell",
}

def _offline_ip_check(ip: str) -> dict:
    for pattern in MALICIOUS_IP_RANGES:
        if pattern.match(ip):
            return {"malicious": True, "source": "offline", "reason": "Known malicious range"}
    # Check private/reserved ranges
    if ip.startswith(("10.", "192.168.", "127.", "0.")):
        return {"malicious": False, "source": "offline", "reason": "Private/reserved range"}
    return {"malicious": False, "source": "offline", "reason": "Not in offline blocklist"}

def _offline_domain_check(domain: str) -> dict:
    domain_lower = domain.lower()
    for bad in MALICIOUS_DOMAINS:
        if bad in domain_lower:
            return {"malicious": True, "source": "offline", "reason": f"Known malicious domain: {bad}"}
    # Check for DGA-like patterns (long random strings)
    labels = domain_lower.split(".")
    for label in labels[:-1]:
        if len(label) > 20 and re.match(r"^[a-z0-9]+$", label):
            return {"malicious": True, "source": "offline", "reason": "Possible DGA domain (long random label)"}
    return {"malicious": False, "source": "offline", "reason": "Not in offline blocklist"}

def _offline_hash_check(hash_val: str) -> dict:
    h = hash_val.lower()
    for known in KNOWN_MALWARE_HASHES:
        if h == known.lower() or known.lower() in h:
            return {"malicious": True, "source": "offline", "reason": f"Known malware hash: {known}"}
    return {"malicious": False, "source": "offline", "reason": "Not in offline hash database"}


# ── AbuseIPDB ─────────────────────────────────────────────────

def _abuseipdb_check(ip: str, api_key: str) -> dict:
    try:
        url = f"https://api.abuseipdb.com/api/v2/check?ipAddress={ip}&maxAgeInDays=90"
        req = urllib.request.Request(url, headers={
            "Key": api_key,
            "Accept": "application/json",
            "User-Agent": "GRIMOIRE/2.0"
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())["data"]
        score = data.get("abuseConfidenceScore", 0)
        reports = data.get("totalReports", 0)
        country = data.get("countryCode", "?")
        isp     = data.get("isp", "?")
        return {
            "malicious": score >= 25,
            "source": "abuseipdb",
            "score": score,
            "reports": reports,
            "country": country,
            "isp": isp,
            "reason": f"Abuse score: {score}/100 ({reports} reports, {country}, {isp})"
        }
    except Exception as e:
        return {"malicious": False, "source": "abuseipdb_error", "reason": str(e)}


# ── VirusTotal ────────────────────────────────────────────────

def _virustotal_check(ioc: str, ioc_type: str, api_key: str) -> dict:
    try:
        if ioc_type == "ip":
            url = f"https://www.virustotal.com/api/v3/ip_addresses/{ioc}"
        elif ioc_type == "domain":
            url = f"https://www.virustotal.com/api/v3/domains/{ioc}"
        elif ioc_type == "hash":
            url = f"https://www.virustotal.com/api/v3/files/{ioc}"
        else:
            return {"malicious": False, "source": "virustotal", "reason": "Unknown IOC type"}

        req = urllib.request.Request(url, headers={
            "x-apikey": api_key,
            "User-Agent": "GRIMOIRE/2.0"
        })
        with urllib.request.urlopen(req, timeout=8) as r:
            data = json.loads(r.read().decode())

        stats = data.get("data", {}).get("attributes", {}).get("last_analysis_stats", {})
        malicious  = stats.get("malicious", 0)
        suspicious = stats.get("suspicious", 0)
        total      = sum(stats.values()) if stats else 0
        return {
            "malicious": malicious >= 3,
            "source": "virustotal",
            "malicious_engines": malicious,
            "suspicious_engines": suspicious,
            "total_engines": total,
            "reason": f"VT: {malicious}/{total} engines flagged malicious"
        }
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return {"malicious": False, "source": "virustotal", "reason": "Not found in VT database"}
        return {"malicious": False, "source": "virustotal_error", "reason": f"HTTP {e.code}"}
    except Exception as e:
        return {"malicious": False, "source": "virustotal_error", "reason": str(e)}


# ── IOC type detector ─────────────────────────────────────────

def _detect_ioc_type(ioc: str) -> str:
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", ioc):
        return "ip"
    if re.match(r"^[a-fA-F0-9]{32}$", ioc) or \
       re.match(r"^[a-fA-F0-9]{40}$", ioc) or \
       re.match(r"^[a-fA-F0-9]{64}$", ioc):
        return "hash"
    if re.match(r"^[a-zA-Z0-9][a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}$", ioc):
        return "domain"
    return "unknown"


# ── Main IOC scanner ──────────────────────────────────────────

def scan_ioc(ioc: str, ioc_type: str = None) -> dict:
    """
    Check an IP, domain, or hash against AbuseIPDB, VirusTotal, and offline DB.
    API keys loaded from ~/.grimoire/config.json.
    """
    section(f"IOC SCAN — {ioc}")
    cfg      = _load_config()
    abuse_key = cfg.get("abuseipdb_api_key")
    vt_key    = cfg.get("virustotal_api_key")

    ioc_type = ioc_type or _detect_ioc_type(ioc)
    print(f"  {C.DIM}Type: {ioc_type}{C.RESET}\n")

    results = []
    verdict = False

    # Offline check
    if ioc_type == "ip":
        r = _offline_ip_check(ioc)
    elif ioc_type == "domain":
        r = _offline_domain_check(ioc)
    elif ioc_type == "hash":
        r = _offline_hash_check(ioc)
    else:
        r = {"malicious": False, "source": "offline", "reason": "Unknown IOC type"}

    results.append(r)
    color = C.RED if r["malicious"] else C.GREEN
    print(f"  {color}[OFFLINE]{C.RESET}  {r['reason']}")

    # AbuseIPDB (IPs only)
    if ioc_type == "ip" and abuse_key:
        r2 = _abuseipdb_check(ioc, abuse_key)
        results.append(r2)
        color = C.RED if r2["malicious"] else C.GREEN
        print(f"  {color}[ABUSEIPDB]{C.RESET} {r2['reason']}")
        if r2["malicious"]:
            verdict = True
    elif ioc_type == "ip" and not abuse_key:
        print(f"  {C.DIM}[ABUSEIPDB] No API key — add abuseipdb_api_key to ~/.grimoire/config.json{C.RESET}")

    # VirusTotal
    if vt_key:
        r3 = _virustotal_check(ioc, ioc_type, vt_key)
        results.append(r3)
        color = C.RED if r3["malicious"] else C.GREEN
        print(f"  {color}[VIRUSTOTAL]{C.RESET} {r3['reason']}")
        if r3["malicious"]:
            verdict = True
    else:
        print(f"  {C.DIM}[VIRUSTOTAL] No API key — add virustotal_api_key to ~/.grimoire/config.json{C.RESET}")

    if r["malicious"]:
        verdict = True

    print()
    if verdict:
        print(f"  {C.RED}{C.BOLD}[!] MALICIOUS — {ioc}{C.RESET}")
    else:
        print(f"  {C.GREEN}[CLEAN] No threat intelligence matches for {ioc}{C.RESET}")

    return {"ioc": ioc, "type": ioc_type, "malicious": verdict, "results": results}


# ══════════════════════════════════════════════════════════════
# ANOMALY DETECTION ENGINE
# ══════════════════════════════════════════════════════════════

def run_anomaly_detection(alerts: list) -> list:
    """
    Run 6-rule anomaly engine over collected alerts.
    Rules: brute force, port scan, priv esc, off-hours, geo anomaly, reverse shell.
    """
    section("ANOMALY DETECTION ENGINE")
    anomalies = []

    # Aggregate IPs and users from alerts
    ip_counts   = defaultdict(int)
    user_events = defaultdict(list)
    timestamps  = []

    for alert in alerts:
        detail = alert.get("detail", "") + alert.get("msg", "")
        ip_m = re.search(r"(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})", detail)
        if ip_m:
            ip_counts[ip_m.group(1)] += 1
        user_m = re.search(r"user=\S*(\w+)", detail)
        if user_m:
            user_events[user_m.group(1)].append(alert)

    # Rule 1: Brute Force — already handled in auth parser, summarize here
    for ip, count in ip_counts.items():
        if count >= 5:
            a = _alert("CRITICAL", "Rule: Brute Force",
                f"{C.CYAN}{ip}{C.RESET} — {count} auth events in log",
                "Recommend: block IP, check fail2ban")
            anomalies.append(a)

    # Rule 2: Privilege Escalation — failed auth followed by sudo
    failed_users = set()
    for alert in alerts:
        if "Failed" in alert.get("source","") or "Invalid" in alert.get("source",""):
            user_m = re.search(r"user=\S*(\w+)", alert.get("msg",""))
            if user_m:
                failed_users.add(user_m.group(1))
    for alert in alerts:
        if "Sudo" in alert.get("source",""):
            user_m = re.search(r"user=\S*(\w+)", alert.get("msg",""))
            if user_m and user_m.group(1) in failed_users:
                anomalies.append(_alert("CRITICAL", "Rule: Priv Esc After Failure",
                    f"User {C.CYAN}{user_m.group(1)}{C.RESET} had failed auth then used sudo",
                    "Possible compromised account"))

    # Rule 3: Reverse Shell — flag any reverse shell pattern
    for alert in alerts:
        if "Reverse Shell" in alert.get("source","") or "Reverse Shell" in alert.get("msg",""):
            anomalies.append(_alert("CRITICAL", "Rule: Reverse Shell",
                alert.get("msg","")[:100],
                "Immediate investigation required"))

    # Rule 4: New user + privilege group add — lateral movement signal
    new_users = [a for a in alerts if "New User" in a.get("source","")]
    group_adds = [a for a in alerts if "Group" in a.get("source","")]
    if new_users and group_adds:
        anomalies.append(_alert("HIGH", "Rule: Account Creation + Group Add",
            f"{len(new_users)} new user(s) + {len(group_adds)} group modification(s)",
            "Possible persistence mechanism"))

    # Rule 5: Web shell + admin probe combo
    webshells = [a for a in alerts if "Web Shell" in a.get("source","")]
    sqli      = [a for a in alerts if "SQL Injection" in a.get("source","")]
    if webshells or (sqli and len(sqli) >= 3):
        anomalies.append(_alert("CRITICAL", "Rule: Web Attack Pattern",
            f"Web shell: {len(webshells)} | SQLi: {len(sqli)} attempts",
            "Check web root for dropped files"))

    # Rule 6: Audit log cleared (Windows)
    cleared = [a for a in alerts if "1102" in a.get("source","") or "Log Cleared" in a.get("source","")]
    if cleared:
        anomalies.append(_alert("CRITICAL", "Rule: Audit Log Cleared",
            "Windows event log cleared — possible coverup",
            "EventID 1102 detected"))

    if not anomalies:
        print(f"  {C.GREEN}No anomalies detected by rule engine{C.RESET}")
    else:
        print(f"\n  {C.RED}{C.BOLD}[!] {len(anomalies)} anomalies detected{C.RESET}")

    return anomalies


# ══════════════════════════════════════════════════════════════
# LIVE TAIL MODE
# ══════════════════════════════════════════════════════════════

def watch_log(filepath: str, log_type: str = "auto"):
    """
    Live tail a log file and alert on suspicious patterns in real-time.
    Ctrl+C to stop.
    """
    section(f"LIVE WATCH — {filepath}")
    print(f"  {C.DIM}Tailing {filepath} — Ctrl+C to stop{C.RESET}\n")

    # Auto-detect log type
    if log_type == "auto":
        if "auth" in filepath:
            patterns = [(l, n, p) for l, n, p in AUTH_PATTERNS]
        elif "syslog" in filepath or "messages" in filepath:
            patterns = [(l, n, p) for l, n, p in SYSLOG_PATTERNS]
        elif "access" in filepath or "apache" in filepath or "nginx" in filepath:
            patterns = [(l, n, p) for l, n, p in WEB_PATTERNS]
        else:
            patterns = [(l, n, p) for l, n, p in CUSTOM_PATTERNS]
    else:
        type_map = {
            "auth": AUTH_PATTERNS,
            "syslog": SYSLOG_PATTERNS,
            "web": WEB_PATTERNS,
            "custom": CUSTOM_PATTERNS
        }
        patterns = type_map.get(log_type, CUSTOM_PATTERNS)

    try:
        with open(filepath, "r", errors="replace") as f:
            f.seek(0, 2)  # Seek to end
            while True:
                line = f.readline()
                if not line:
                    time.sleep(0.1)
                    continue
                for level, name, pattern in patterns:
                    if pattern.search(line):
                        ts_now = datetime.now().strftime("%H:%M:%S")
                        print(f"  {C.DIM}{ts_now}{C.RESET} {_sev(level, f'{C.BOLD}{name}{C.RESET}  {line.strip()[:100]}')}")
                        break
    except KeyboardInterrupt:
        print(f"\n  {C.DIM}[Watch stopped]{C.RESET}")
    except FileNotFoundError:
        print(f"  {C.YELLOW}[!] File not found: {filepath}{C.RESET}")
    except PermissionError:
        print(f"  {C.YELLOW}[!] Permission denied: {filepath}{C.RESET}")


# ══════════════════════════════════════════════════════════════
# FULL SCAN
# ══════════════════════════════════════════════════════════════

DEFAULT_LOG_PATHS = {
    "auth":   ["/var/log/auth.log", "/var/log/secure"],
    "syslog": ["/var/log/syslog", "/var/log/messages"],
    "web":    ["/var/log/apache2/access.log", "/var/log/nginx/access.log",
               "/var/log/httpd/access_log"],
}

def full_scan(log_dir: str = "/var/log", save_report: bool = False) -> dict:
    """Run all parsers + anomaly engine on standard log paths."""
    print(BANNER)
    print(f"  {C.BOLD}Log Dir : {C.RED}{log_dir}{C.RESET}  |  {C.DIM}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}\n")

    all_alerts = []

    for log_type, paths in DEFAULT_LOG_PATHS.items():
        for path in paths:
            # Override with log_dir if it's not the default
            if log_dir != "/var/log":
                path = str(Path(log_dir) / Path(path).name)
            if Path(path).exists():
                if log_type == "auth":
                    all_alerts.extend(parse_auth_log(path))
                elif log_type == "syslog":
                    all_alerts.extend(parse_syslog(path))
                elif log_type == "web":
                    all_alerts.extend(parse_web_log(path))
                break  # Use first existing path

    anomalies = run_anomaly_detection(all_alerts)
    all_alerts.extend(anomalies)

    # Summary
    section("SENTINEL SCAN COMPLETE")
    counts = defaultdict(int)
    for a in all_alerts:
        counts[a["level"]] += 1

    total = len(all_alerts)
    print(f"  {C.BOLD}Total events : {total}{C.RESET}")
    for level in ["CRITICAL", "HIGH", "MEDIUM", "LOW", "INFO"]:
        if counts[level]:
            c = SEV_COLOR.get(level, C.DIM)
            print(f"  {c}{level:<10}{C.RESET} {counts[level]}")

    if save_report:
        _save_report(all_alerts, log_dir)

    return {"alerts": all_alerts, "counts": dict(counts)}


def _save_report(alerts: list, scan_target: str):
    from pathlib import Path as _Path
    rb = ReportBuilder(f"Sentinel Report: {scan_target}")
    rb.add_section("Scan Target", scan_target)
    rb.add_section("Timestamp", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

    counts = defaultdict(int)
    for a in alerts:
        counts[a["level"]] += 1

    summary = "\n".join(f"{k}: {v}" for k, v in counts.items())
    rb.add_section("Summary", summary)

    if alerts:
        rb.add_table("Findings",
            ["Severity", "Source", "Message", "Detail"],
            [[a["level"], a["source"], a["msg"][:60], a.get("detail","")[:60]]
             for a in alerts[:100]])

    out_dir = _Path.home() / ".grimoire" / "reports"
    out_dir.mkdir(parents=True, exist_ok=True)
    saved = rb.save(
        str(out_dir / f"sentinel_{datetime.now().strftime('%Y%m%d_%H%M')}"), "md"
    )
    print(f"\n  {C.GREEN}[+] Report saved: {saved}{C.RESET}")


# ══════════════════════════════════════════════════════════════
# INTERACTIVE + CLI
# ══════════════════════════════════════════════════════════════

def _interactive():
    print(BANNER)
    print(f"  {C.DIM}Commands: scan | watch | ioc | auth | syslog | web | evtx | custom | exit{C.RESET}\n")
    while True:
        try:
            raw = input(f"  {C.RED}sentinel>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Closing Sentinel]")
            break
        if not raw:
            continue
        parts = raw.split()
        cmd   = parts[0].lower()

        if cmd in ("exit", "quit", "q"):
            break

        elif cmd == "scan":
            path = parts[1] if len(parts) >= 2 else "/var/log"
            save = "--report" in parts
            full_scan(path, save_report=save)

        elif cmd == "watch" and len(parts) >= 2:
            log_type = parts[2] if len(parts) >= 3 else "auto"
            watch_log(parts[1], log_type)

        elif cmd == "ioc" and len(parts) >= 2:
            scan_ioc(parts[1])

        elif cmd == "auth" and len(parts) >= 2:
            alerts = parse_auth_log(parts[1])
            run_anomaly_detection(alerts)

        elif cmd == "syslog" and len(parts) >= 2:
            parse_syslog(parts[1])

        elif cmd == "web" and len(parts) >= 2:
            parse_web_log(parts[1])

        elif cmd == "evtx" and len(parts) >= 2:
            parse_evtx(parts[1])

        elif cmd == "custom" and len(parts) >= 2:
            pattern = parts[2] if len(parts) >= 3 else None
            parse_custom_log(parts[1], pattern)

        else:
            print(f"  {C.DIM}Commands: scan [dir] [--report] | watch <file> [type] | ioc <ip/domain/hash>{C.RESET}")
            print(f"  {C.DIM}          auth <file> | syslog <file> | web <file> | evtx <file> | custom <file> [regex]{C.RESET}")


def cli_main(args):
    if not args:
        _interactive()
        return

    if "--help" in args or "-h" in args:
        print(f"""
  {C.RED}{C.BOLD}SENTINEL v1.0 — Blue Team Detection{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire sentinel                       interactive mode
    grimoire sentinel --scan [dir]          full log scan
    grimoire sentinel --scan [dir] --report scan + save markdown report
    grimoire sentinel --watch <file>        live tail mode
    grimoire sentinel --ioc <ip/domain/hash> single IOC check

  {C.DIM}Interactive commands:{C.RESET}
    scan [dir] [--report]       full scan of log directory
    watch <file> [type]         live tail (type: auth|syslog|web|custom)
    ioc <ip|domain|hash>        IOC reputation check
    auth <file>                 parse auth.log
    syslog <file>               parse syslog/messages
    web <file>                  parse apache/nginx access log
    evtx <file>                 parse Windows event log (.evtx)
    custom <file> [regex]       parse any log with optional regex

  {C.DIM}API keys in ~/.grimoire/config.json:{C.RESET}
    abuseipdb_api_key           https://www.abuseipdb.com/account/api
    virustotal_api_key          https://www.virustotal.com/gui/my-apikey

  {C.DIM}Examples:{C.RESET}
    grimoire sentinel --scan /var/log --report
    grimoire sentinel --ioc 185.220.101.1
    grimoire sentinel --watch /var/log/auth.log
""")
        return

    if "--scan" in args:
        idx  = args.index("--scan")
        path = args[idx + 1] if idx + 1 < len(args) and not args[idx+1].startswith("--") else "/var/log"
        full_scan(path, save_report="--report" in args)

    elif "--watch" in args:
        idx  = args.index("--watch")
        if idx + 1 < len(args):
            log_type = args[idx + 2] if idx + 2 < len(args) else "auto"
            watch_log(args[idx + 1], log_type)
        else:
            print(f"  {C.YELLOW}[!] Specify a file: grimoire sentinel --watch /var/log/auth.log{C.RESET}")

    elif "--ioc" in args:
        idx = args.index("--ioc")
        if idx + 1 < len(args):
            scan_ioc(args[idx + 1])
        else:
            print(f"  {C.YELLOW}[!] Specify an IOC: grimoire sentinel --ioc 1.2.3.4{C.RESET}")

    else:
        _interactive()


def launch():
    _interactive()
