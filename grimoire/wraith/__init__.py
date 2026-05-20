# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE v2.0 — wraith/__init__.py
#  Passive Recon Engine
#
#  Developer  : Light
#  Alias      : Neok1ra
#  GitHub     : https://github.com/ne0k1r4
#  Tool       : GRIMOIRE — The Death Note of the digital world
#
#  Features:
#    DNS resolution (A/AAAA/MX), Reverse DNS
#    SSL/TLS cert inspection + SANs
#    WHOIS lookup
#    IP geolocation + ASN
#    Subdomain wordlist probe
#    HTTP header fingerprinting
#    Tech stack detection (server, framework, CMS)
#    robots.txt + security.txt harvesting
#    Open port probe (top 20 ports)
#    Markdown/HTML report export
# ═══════════════════════════════════════════════════════════════

import socket, ssl, json, urllib.request, urllib.parse
import re, sys, subprocess
from datetime import datetime
from ..utils import C, section, ReportBuilder, ts

BANNER = f"""
{C.RED}{C.BOLD}  ╔══════════════════════════════════════════════╗
  ║  W R A I T H  v2.0  —  Passive Recon        ║
  ║  Developer: Light (Neok1ra)                  ║
  ╚══════════════════════════════════════════════╝{C.RESET}
  {C.DIM}DNS · WHOIS · Certs · HTTP · Tech · Ports · Reports{C.RESET}
"""

TOP_PORTS = [21,22,23,25,53,80,110,143,443,445,
             465,587,993,995,1433,3306,3389,5432,6379,8080]

TECH_SIGNATURES = {
    "Apache":       ("server", re.compile(r"Apache", re.I)),
    "Nginx":        ("server", re.compile(r"nginx", re.I)),
    "IIS":          ("server", re.compile(r"IIS", re.I)),
    "LiteSpeed":    ("server", re.compile(r"LiteSpeed", re.I)),
    "Caddy":        ("server", re.compile(r"Caddy", re.I)),
    "PHP":          ("x-powered-by", re.compile(r"PHP", re.I)),
    "ASP.NET":      ("x-powered-by", re.compile(r"ASP\.NET", re.I)),
    "Express":      ("x-powered-by", re.compile(r"Express", re.I)),
    "WordPress":    ("x-pingback",   re.compile(r"xmlrpc", re.I)),
    "Drupal":       ("x-generator",  re.compile(r"Drupal", re.I)),
    "Cloudflare":   ("server",       re.compile(r"cloudflare", re.I)),
    "AWS":          ("server",       re.compile(r"AmazonS3|awselb", re.I)),
}


# ── DNS ───────────────────────────────────────────────────────

def dns_lookup(domain: str) -> dict:
    section("DNS RESOLUTION")
    results = {"A": [], "AAAA": [], "MX": []}
    for rtype, fam in [("A", socket.AF_INET), ("AAAA", socket.AF_INET6)]:
        try:
            ips = list({r[4][0] for r in socket.getaddrinfo(domain, None, fam)})
            results[rtype] = ips
            for ip in ips:
                print(f"  {C.CYAN}{rtype:<6}{C.RESET} {ip}")
        except socket.gaierror:
            print(f"  {C.DIM}{rtype:<6} no record{C.RESET}")
    try:
        out = subprocess.check_output(["nslookup", "-type=MX", domain],
                                      stderr=subprocess.DEVNULL, timeout=5).decode()
        for line in out.splitlines():
            if "mail exchanger" in line.lower():
                results["MX"].append(line.strip())
                print(f"  {C.CYAN}MX    {C.RESET} {line.strip()}")
    except Exception:
        pass
    return results


def reverse_dns(ip: str) -> str:
    section("REVERSE DNS")
    if not ip:
        print(f"  {C.DIM}No IP to resolve{C.RESET}")
        return ""
    try:
        host = socket.gethostbyaddr(ip)[0]
        print(f"  {C.CYAN}{ip}{C.RESET} => {host}")
        return host
    except (socket.herror, socket.gaierror):
        print(f"  {C.DIM}No PTR record for {ip}{C.RESET}")
        return ""


# ── SSL / TLS ─────────────────────────────────────────────────

def cert_info(domain: str, port: int = 443) -> dict:
    section("SSL / TLS CERTIFICATE")
    result = {}
    try:
        ctx = ssl.create_default_context()
        with socket.create_connection((domain, port), timeout=5) as s:
            with ctx.wrap_socket(s, server_hostname=domain) as ss:
                cert = ss.getpeercert()
                result["cipher"]  = ss.cipher()[0]
                result["version"] = ss.version()
        subject = dict(x[0] for x in cert.get("subject", []))
        issuer  = dict(x[0] for x in cert.get("issuer",  []))
        sans    = [v for t, v in cert.get("subjectAltName", []) if t == "DNS"]
        result.update({"subject": subject.get("commonName","?"),
                       "issuer":  issuer.get("organizationName","?"),
                       "not_before": cert.get("notBefore","?"),
                       "not_after":  cert.get("notAfter","?"),
                       "sans": sans})
        print(f"  {C.CYAN}Subject  {C.RESET} {result['subject']}")
        print(f"  {C.CYAN}Issuer   {C.RESET} {result['issuer']}")
        print(f"  {C.CYAN}Valid    {C.RESET} {result['not_before']}  →  {result['not_after']}")
        print(f"  {C.CYAN}TLS      {C.RESET} {result['version']}  /  {result['cipher']}")
        print(f"  {C.CYAN}SANs     {C.RESET} {', '.join(sans[:12])}")
        if len(sans) > 12:
            print(f"  {C.DIM}         ... and {len(sans)-12} more{C.RESET}")
    except Exception as e:
        print(f"  {C.YELLOW}[!] Cert error: {e}{C.RESET}")
    return result


# ── HTTP fingerprinting ───────────────────────────────────────

def http_fingerprint(domain: str) -> dict:
    section("HTTP FINGERPRINT")
    result = {"headers": {}, "tech": [], "status": None, "redirect": None}
    for scheme in ("https", "http"):
        url = f"{scheme}://{domain}"
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (GRIMOIRE/2.0; Neok1ra)",
            })
            with urllib.request.urlopen(req, timeout=6) as r:
                result["status"]  = r.status
                result["headers"] = dict(r.headers)
                result["redirect"]= r.url if r.url != url else None
            break
        except urllib.error.HTTPError as e:
            result["status"] = e.code
            result["headers"] = dict(e.headers)
            break
        except Exception:
            continue

    if not result["headers"]:
        print(f"  {C.DIM}[No HTTP response]{C.RESET}")
        return result

    print(f"  {C.CYAN}Status   {C.RESET} {result['status']}")
    if result["redirect"]:
        print(f"  {C.CYAN}Redirect {C.RESET} {result['redirect']}")

    interesting = ["server","x-powered-by","x-generator","x-pingback",
                   "content-security-policy","strict-transport-security",
                   "x-frame-options","x-content-type-options","set-cookie",
                   "cf-ray","via","x-cache"]
    for h in interesting:
        val = result["headers"].get(h) or result["headers"].get(h.title())
        if val:
            print(f"  {C.CYAN}{h:<28}{C.RESET} {val[:80]}")

    # tech detection
    for tech, (header, pattern) in TECH_SIGNATURES.items():
        val = result["headers"].get(header, "") or result["headers"].get(header.title(), "")
        if pattern.search(val):
            result["tech"].append(tech)
    if result["tech"]:
        print(f"  {C.CYAN}Tech Stack{C.RESET}       {C.GREEN}{', '.join(result['tech'])}{C.RESET}")

    return result


# ── robots.txt / security.txt ─────────────────────────────────

def harvest_special_files(domain: str) -> dict:
    section("ROBOTS.TXT / SECURITY.TXT")
    out = {}
    for path, key in [("/robots.txt","robots"), ("/.well-known/security.txt","security")]:
        for scheme in ("https", "http"):
            url = f"{scheme}://{domain}{path}"
            try:
                req = urllib.request.Request(url, headers={"User-Agent": "GRIMOIRE/2.0"})
                with urllib.request.urlopen(req, timeout=5) as r:
                    if r.status == 200:
                        content = r.read(4096).decode(errors="replace")
                        out[key] = content
                        print(f"\n  {C.GREEN}[{path}]{C.RESET}")
                        for line in content.splitlines()[:20]:
                            if line.strip() and not line.startswith("#"):
                                print(f"  {C.DIM}  {line}{C.RESET}")
                break
            except Exception:
                continue
        if key not in out:
            print(f"  {C.DIM}{path} — not found{C.RESET}")
    return out


# ── Port probe ────────────────────────────────────────────────

def port_probe(host: str, ports: list = None, timeout: float = 0.8) -> dict:
    section(f"OPEN PORT PROBE (top {len(ports or TOP_PORTS)})")
    ports  = ports or TOP_PORTS
    open_p = []
    for port in ports:
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(timeout)
            r = s.connect_ex((host, port))
            s.close()
            if r == 0:
                try:
                    svc = socket.getservbyport(port)
                except OSError:
                    svc = "unknown"
                print(f"  {C.GREEN}OPEN{C.RESET}  {port:<6} {svc}")
                open_p.append({"port": port, "service": svc})
        except Exception:
            pass
    if not open_p:
        print(f"  {C.DIM}[No open ports found in probe list]{C.RESET}")
    return {"open": open_p}


# ── WHOIS ─────────────────────────────────────────────────────

def whois_lookup(domain: str) -> str:
    section("WHOIS")
    try:
        out = subprocess.check_output(["whois", domain],
                                      stderr=subprocess.DEVNULL, timeout=10).decode(errors="replace")
        keys = ["Registrar:","Creation Date:","Updated Date:","Expiry Date:",
                "Registrant","Name Server:","Admin","Tech"]
        shown = set()
        for line in out.splitlines():
            for k in keys:
                if line.strip().lower().startswith(k.lower()) and k not in shown:
                    print(f"  {C.CYAN}{line.strip()}{C.RESET}")
                    shown.add(k)
        return out
    except FileNotFoundError:
        print(f"  {C.DIM}[whois not installed]{C.RESET}")
        return ""
    except Exception as e:
        print(f"  {C.YELLOW}[!] {e}{C.RESET}")
        return ""


# ── IP geolocation ────────────────────────────────────────────

def ip_info(ip: str) -> dict:
    section("IP GEOLOCATION / ASN")
    try:
        req = urllib.request.Request(f"https://ipapi.co/{ip}/json/",
                                     headers={"User-Agent": "GRIMOIRE/2.0"})
        with urllib.request.urlopen(req, timeout=6) as r:
            data = json.loads(r.read())
        for f in ["ip","org","asn","city","region","country_name","timezone","latitude","longitude"]:
            if data.get(f):
                print(f"  {C.CYAN}{f:<16}{C.RESET} {data[f]}")
        return data
    except Exception as e:
        print(f"  {C.YELLOW}[!] IP info: {e}{C.RESET}")
        return {}


# ── Subdomain probe ───────────────────────────────────────────

def subdomain_probe(domain: str) -> list:
    section("SUBDOMAIN PROBE")
    wordlist = [
        "www","mail","ftp","smtp","pop","imap","webmail","admin","portal",
        "vpn","dev","staging","test","api","cdn","static","assets","media",
        "img","images","video","mobile","m","app","apps","dashboard","manage",
        "ns1","ns2","mx","mail2","blog","docs","wiki","support","help","status",
        "monitor","git","gitlab","ci","jenkins","jira","confluence","shop",
        "store","pay","payments","billing","auth","sso","login","beta","prod",
        "secure","remote","cloud","backup","db","database","mysql","redis",
        "kafka","elastic","kibana","grafana","prometheus","vault","k8s","dev2",
    ]
    found = []
    print(f"  {C.DIM}Probing {len(wordlist)} subdomains...{C.RESET}")
    for sub in wordlist:
        fqdn = f"{sub}.{domain}"
        try:
            ip = socket.gethostbyname(fqdn)
            print(f"  {C.GREEN}FOUND{C.RESET}  {fqdn:<45} {ip}")
            found.append({"fqdn": fqdn, "ip": ip})
        except socket.gaierror:
            pass
    if not found:
        print(f"  {C.DIM}[No subdomains resolved]{C.RESET}")
    return found


# ── Full scan ─────────────────────────────────────────────────

def full_scan(target: str, save_report: bool = False) -> dict:
    print(BANNER)
    print(f"  {C.BOLD}Target : {C.RED}{target}{C.RESET}  |  {C.DIM}{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{C.RESET}\n")
    from ..core.oplog import log
    log(f"Wraith scan: {target}", "wraith")

    try:
        ip = socket.gethostbyname(target)
    except socket.gaierror:
        ip = target

    report_data = {"target": target, "ip": ip, "ts": ts()}
    report_data["dns"]    = dns_lookup(target)
    report_data["cert"]   = cert_info(target)
    report_data["http"]   = http_fingerprint(target)
    report_data["files"]  = harvest_special_files(target)
    report_data["whois"]  = whois_lookup(target)
    report_data["ipinfo"] = ip_info(ip)
    report_data["ports"]  = port_probe(ip)
    report_data["rdns"]   = reverse_dns(ip)
    report_data["subs"]   = subdomain_probe(target)

    section("SCAN COMPLETE")
    print(f"  {C.GREEN}Wraith v2.0 scan finished: {target}{C.RESET}")
    print(f"  {C.DIM}Open ports : {len(report_data['ports']['open'])}{C.RESET}")
    print(f"  {C.DIM}Subdomains : {len(report_data['subs'])}{C.RESET}")
    print(f"  {C.DIM}Tech stack : {', '.join(report_data['http'].get('tech',[])) or 'unknown'}{C.RESET}")

    if save_report:
        from pathlib import Path
        rb = ReportBuilder(f"Wraith Recon: {target}")
        rb.add_section("Target", f"`{target}` / `{ip}`")
        if report_data["dns"]["A"]:
            rb.add_section("DNS (A)", "\n".join(report_data["dns"]["A"]))
        if report_data["cert"]:
            c = report_data["cert"]
            rb.add_section("Certificate", f"Subject: {c.get('subject')}\nIssuer: {c.get('issuer')}\nExpiry: {c.get('not_after')}")
        if report_data["http"].get("tech"):
            rb.add_section("Tech Stack", ", ".join(report_data["http"]["tech"]))
        if report_data["ports"]["open"]:
            rb.add_table("Open Ports",
                ["Port","Service"],
                [[p["port"], p["service"]] for p in report_data["ports"]["open"]])
        if report_data["subs"]:
            rb.add_table("Subdomains",
                ["FQDN","IP"],
                [[s["fqdn"], s["ip"]] for s in report_data["subs"]])
        out_dir = Path.home() / ".grimoire" / "reports"
        saved = rb.save(str(out_dir / f"wraith_{target}_{datetime.now().strftime('%Y%m%d_%H%M')}"), "md")
        print(f"\n  {C.GREEN}[+] Report saved: {saved}{C.RESET}")

    log(f"Wraith scan complete: {target}", "wraith")
    return report_data


def _interactive():
    print(BANNER)
    print(f"  {C.DIM}Commands: scan <target> | scan <target> --report | dns | cert | http | ports | sub | exit{C.RESET}\n")
    while True:
        try:
            raw = input(f"  {C.RED}wraith>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Closing Wraith]")
            break
        if not raw: continue
        parts = raw.split()
        cmd   = parts[0].lower()
        if cmd in ("exit","quit","q"): break
        elif cmd == "scan" and len(parts) >= 2:
            save = "--report" in parts
            full_scan(parts[1], save_report=save)
        elif cmd == "dns"   and len(parts) >= 2: dns_lookup(parts[1])
        elif cmd == "cert"  and len(parts) >= 2: cert_info(parts[1])
        elif cmd == "http"  and len(parts) >= 2: http_fingerprint(parts[1])
        elif cmd == "ports" and len(parts) >= 2: port_probe(parts[1])
        elif cmd == "sub"   and len(parts) >= 2: subdomain_probe(parts[1])
        elif cmd == "ip"    and len(parts) >= 2: ip_info(parts[1])
        else:
            print(f"  {C.DIM}Try: scan <target> [--report] | dns | cert | http | ports | sub | exit{C.RESET}")


def cli_main(args):
    if not args:
        _interactive()
        return
    if "--help" in args or "-h" in args:
        print(f"""
  {C.RED}{C.BOLD}WRAITH — Passive Recon{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire wraith                     interactive mode
    grimoire wraith <target>            full passive recon scan
    grimoire wraith <target> --report   scan + save markdown report

  {C.DIM}Examples:{C.RESET}
    grimoire wraith example.com
    grimoire wraith example.com --report
""")
        return
    full_scan(args[0], save_report="--report" in args)

def launch(): _interactive()
