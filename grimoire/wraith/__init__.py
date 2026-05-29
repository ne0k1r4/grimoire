# wraith — passive recon engine
# dns, whois, ssl, http fingerprinting, subdomain enum
# crt.sh, subdomain takeover, waf detection, shodan


import socket, ssl, json, urllib.request, urllib.parse
import re, sys, subprocess
from datetime import datetime
from ..utils import C, section, ReportBuilder, ts

BANNER = f"""
{C.RED}{C.BOLD}  ╔══════════════════════════════════════════════╗
  ║  W R A I T H  v2.1  —  Passive Recon        ║
  ║  Developer: Light (Neok1ra)                  ║
  ╚══════════════════════════════════════════════╝{C.RESET}
  {C.DIM}DNS · WHOIS · Certs · HTTP · Ports · crt.sh · WAF · Takeover · Shodan{C.RESET}
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


# ── Subdomain probing ─────────────────────────────────────────

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
    report_data["crt"]      = crtsh_enum(target)
    report_data["waf"]      = waf_detect(target)
    report_data["takeover"] = subdomain_takeover(target, subdomains=[s["fqdn"] for s in report_data["subs"]])

    section("SCAN COMPLETE")
    print(f"  {C.GREEN}Wraith v2.1 scan finished: {target}{C.RESET}")
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
    print(f"  {C.DIM}Commands: scan | dns | cert | http | ports | sub | ip | crt | takeover | waf | shodan | exit{C.RESET}\n")
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
        elif cmd == "ip"       and len(parts) >= 2: ip_info(parts[1])
        elif cmd == "crt"      and len(parts) >= 2: crtsh_enum(parts[1])
        elif cmd == "takeover" and len(parts) >= 2: subdomain_takeover(parts[1])
        elif cmd == "waf"      and len(parts) >= 2: waf_detect(parts[1])
        elif cmd == "shodan"   and len(parts) >= 2:
            key = parts[2] if len(parts) >= 3 else None
            shodan_lookup(parts[1], api_key=key)
        else:
            print(f"  {C.DIM}Commands: scan <t> [--report] | dns | cert | http | ports | sub | ip | crt | takeover | waf | shodan <ip> [key]{C.RESET}")


def cli_main(args):
    if not args:
        _interactive()
        return
    if "--help" in args or "-h" in args:
        print(f"""
  {C.RED}{C.BOLD}WRAITH v2.1 — Passive Recon{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire wraith                     interactive mode
    grimoire wraith <target>            full passive recon scan
    grimoire wraith <target> --report   scan + save markdown report

  {C.DIM}Interactive commands:{C.RESET}
    scan <target> [--report]    full recon scan
    dns <target>                DNS A/AAAA/MX lookup
    cert <target>               SSL/TLS cert + SANs
    http <target>               HTTP headers + tech stack
    ports <target>              top-20 port probe
    sub <target>                subdomain wordlist probe
    ip <ip>                     geolocation + ASN
    crt <domain>                crt.sh CT log enumeration
    waf <domain>                WAF / CDN fingerprinting
    takeover <domain>           subdomain takeover detection
    shodan <ip> [key]           Shodan host intelligence

  {C.DIM}Examples:{C.RESET}
    grimoire wraith example.com --report
""")
        return
    full_scan(args[0], save_report="--report" in args)

def launch(): _interactive()


# ==============================================================
# WRAITH v2.1 EXTENSIONS
# crt.sh · Subdomain Takeover · WAF Detection · Shodan
# ==============================================================

def crtsh_enum(domain: str) -> list:
    """Enumerate subdomains via crt.sh certificate transparency logs."""
    section("CERTIFICATE TRANSPARENCY (crt.sh)")
    found = set()
    try:
        url = f"https://crt.sh/?q=%.{domain}&output=json"
        req = urllib.request.Request(url, headers={"User-Agent": "GRIMOIRE/2.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
        for entry in data:
            names = entry.get("name_value", "")
            for name in names.splitlines():
                name = name.strip().lstrip("*.")
                if name.endswith(f".{domain}") or name == domain:
                    found.add(name)
        found = sorted(found)
        if found:
            print(f"  {C.GREEN}Found {len(found)} subdomains via CT logs:{C.RESET}\n")
            for sub in found:
                try:
                    ip = socket.gethostbyname(sub)
                    print(f"  {C.CYAN}{sub:<45}{C.RESET} {ip}")
                except socket.gaierror:
                    print(f"  {C.DIM}{sub:<45} (unresolved){C.RESET}")
        else:
            print(f"  {C.DIM}No subdomains found in CT logs{C.RESET}")
    except Exception as e:
        print(f"  {C.YELLOW}[!] crt.sh error: {e}{C.RESET}")
    return list(found)


# ══════════════════════════════════════════════════════════════
# 2. Subdomain Takeover Detection
# ══════════════════════════════════════════════════════════════

# Fingerprints: (service_name, cname_pattern, body_fingerprint)
TAKEOVER_FINGERPRINTS = {
    "GitHub Pages":       (re.compile(r"github\.io", re.I),
                           "There isn't a GitHub Pages site here"),
    "Heroku":             (re.compile(r"heroku\.com|herokudns\.com", re.I),
                           "No such app"),
    "Netlify":            (re.compile(r"netlify\.app|netlify\.com", re.I),
                           "Not Found - Request ID"),
    "AWS S3":             (re.compile(r"s3\.amazonaws\.com|s3-website", re.I),
                           "NoSuchBucket"),
    "AWS CloudFront":     (re.compile(r"cloudfront\.net", re.I),
                           "ERROR: The request could not be satisfied"),
    "Azure":              (re.compile(r"azurewebsites\.net|azure\.com", re.I),
                           "404 Web Site not found"),
    "Fastly":             (re.compile(r"fastly\.net", re.I),
                           "Fastly error: unknown domain"),
    "Ghost":              (re.compile(r"ghost\.io", re.I),
                           "The thing you were looking for is no longer here"),
    "Cargo":              (re.compile(r"cargocollective\.com", re.I),
                           "404 Not Found"),
    "Tumblr":             (re.compile(r"tumblr\.com", re.I),
                           "There's nothing here"),
    "Shopify":            (re.compile(r"myshopify\.com", re.I),
                           "Sorry, this shop is currently unavailable"),
    "Webflow":            (re.compile(r"webflow\.io", re.I),
                           "The page you are looking for doesn't exist"),
    "Surge.sh":           (re.compile(r"surge\.sh", re.I),
                           "project not found"),
    "Zendesk":            (re.compile(r"zendesk\.com", re.I),
                           "Help Center Closed"),
    "Freshdesk":          (re.compile(r"freshdesk\.com", re.I),
                           "May be this is still fresh!"),
    "HubSpot":            (re.compile(r"hubspot\.net|hs-sites\.com", re.I),
                           "Domain not found"),
    "Intercom":           (re.compile(r"intercom\.io", re.I),
                           "This page is reserved for artistic"),
    "Unbounce":           (re.compile(r"unbouncepages\.com", re.I),
                           "The requested URL was not found"),
    "Readme.io":          (re.compile(r"readme\.io", re.I),
                           "Project doesnt exist"),
    "Bitbucket":          (re.compile(r"bitbucket\.io", re.I),
                           "Repository not found"),
    "Squarespace":        (re.compile(r"squarespace\.com", re.I),
                           "No Such Account"),
    "Strikingly":         (re.compile(r"strikingly\.com", re.I),
                           "But if you're looking to build your own"),
    "Fly.io":             (re.compile(r"fly\.dev|fly\.io", re.I),
                           "404 - Not Found"),
    "Render":             (re.compile(r"onrender\.com", re.I),
                           "Service not found"),
    "Vercel":             (re.compile(r"vercel\.app", re.I),
                           "The deployment could not be found"),
    "Firebase":           (re.compile(r"firebaseapp\.com|web\.app", re.I),
                           "Firebase App Not Found"),
    "WP Engine":          (re.compile(r"wpengine\.com", re.I),
                           "The site you were looking for couldn't be found"),
    "Pantheon":           (re.compile(r"pantheonsite\.io", re.I),
                           "404 error unknown site"),
    "Acquia":             (re.compile(r"acquia-sites\.com", re.I),
                           "If you are an Acquia Cloud customer"),
    "Kinsta":             (re.compile(r"kinsta\.cloud", re.I),
                           "No Site For Domain"),
}

def _get_cname(domain: str) -> str:
    """Get CNAME record for a domain."""
    try:
        out = urllib.request.urlopen(
            f"https://dns.google/resolve?name={domain}&type=CNAME",
            timeout=5
        ).read().decode()
        data = json.loads(out)
        for ans in data.get("Answer", []):
            if ans.get("type") == 5:  # CNAME type
                return ans.get("data", "").rstrip(".")
    except Exception:
        pass
    return ""

def _fetch_body(domain: str, timeout: int = 5) -> str:
    """Fetch HTTP body for fingerprinting."""
    for scheme in ("https", "http"):
        try:
            req = urllib.request.Request(
                f"{scheme}://{domain}",
                headers={"User-Agent": "GRIMOIRE/2.0"}
            )
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read(4096).decode(errors="replace")
        except Exception:
            continue
    return ""

def subdomain_takeover(domain: str, subdomains: list = None) -> list:
    """
    Check subdomains for potential takeover vulnerabilities.
    Checks CNAME dangling + body fingerprinting against 30 known services.
    """
    section("SUBDOMAIN TAKEOVER DETECTION")
    vulnerable = []

    if not subdomains:
        # Quick probe of common subdomains
        wordlist = ["www","mail","dev","staging","test","api","cdn","static",
                    "assets","media","app","dashboard","portal","beta","shop",
                    "store","blog","docs","support","help","status","git"]
        subdomains = []
        print(f"  {C.DIM}Probing {len(wordlist)} subdomains for dangling CNAMEs...{C.RESET}\n")
        for sub in wordlist:
            fqdn = f"{sub}.{domain}"
            try:
                socket.gethostbyname(fqdn)
                subdomains.append(fqdn)
            except socket.gaierror:
                # Unresolvable — check if CNAME points somewhere (dangling)
                cname = _get_cname(fqdn)
                if cname:
                    subdomains.append(fqdn)
    else:
        print(f"  {C.DIM}Checking {len(subdomains)} subdomains for takeover...{C.RESET}\n")

    for fqdn in subdomains:
        cname = _get_cname(fqdn)
        if not cname:
            continue

        # Check CNAME against known takeover fingerprints
        for service, (cname_pattern, body_fingerprint) in TAKEOVER_FINGERPRINTS.items():
            if cname_pattern.search(cname):
                # CNAME matches — now check body
                body = _fetch_body(fqdn)
                if body_fingerprint.lower() in body.lower():
                    print(f"  {C.RED}{C.BOLD}[VULNERABLE]{C.RESET} {fqdn}")
                    print(f"  {C.CYAN}  Service  {C.RESET} {service}")
                    print(f"  {C.CYAN}  CNAME    {C.RESET} {cname}")
                    print(f"  {C.CYAN}  Signal   {C.RESET} {body_fingerprint[:60]}\n")
                    vulnerable.append({
                        "fqdn": fqdn, "service": service,
                        "cname": cname, "fingerprint": body_fingerprint
                    })
                else:
                    print(f"  {C.YELLOW}[POSSIBLE]{C.RESET}  {fqdn}")
                    print(f"  {C.DIM}  Service: {service} | CNAME: {cname} (body mismatch){C.RESET}\n")
                break

    if not vulnerable:
        print(f"  {C.GREEN}No confirmed takeover vulnerabilities found{C.RESET}")
    else:
        print(f"  {C.RED}{C.BOLD}[!] {len(vulnerable)} vulnerable subdomain(s) found!{C.RESET}")

    return vulnerable


# ══════════════════════════════════════════════════════════════
# 3. WAF Detection
# ══════════════════════════════════════════════════════════════

WAF_SIGNATURES = {
    "Cloudflare": {
        "headers": [
            ("server",    re.compile(r"cloudflare", re.I)),
            ("cf-ray",    re.compile(r".+", re.I)),
            ("cf-cache-status", re.compile(r".+", re.I)),
        ],
        "cookies": re.compile(r"__cfduid|cf_clearance|__cf_bm", re.I),
        "body":    re.compile(r"cloudflare|cf-ray", re.I),
    },
    "AWS WAF / CloudFront": {
        "headers": [
            ("x-amz-cf-id",  re.compile(r".+", re.I)),
            ("x-amz-cf-pop", re.compile(r".+", re.I)),
            ("server",       re.compile(r"CloudFront", re.I)),
        ],
        "cookies": re.compile(r"AWSALB|AWSALBCORS", re.I),
        "body":    re.compile(r"Request blocked|aws-waf", re.I),
    },
    "Akamai": {
        "headers": [
            ("server",        re.compile(r"AkamaiGHost", re.I)),
            ("x-check-cacheable", re.compile(r".+", re.I)),
            ("x-akamai-transformed", re.compile(r".+", re.I)),
        ],
        "cookies": re.compile(r"ak_bmsc|bm_sz|_abck", re.I),
        "body":    re.compile(r"akamai|Reference ID:", re.I),
    },
    "Imperva / Incapsula": {
        "headers": [
            ("x-iinfo",    re.compile(r".+", re.I)),
            ("x-cdn",      re.compile(r"Imperva|Incapsula", re.I)),
        ],
        "cookies": re.compile(r"incap_ses|visid_incap", re.I),
        "body":    re.compile(r"incapsula|imperva|Request unsuccessful", re.I),
    },
    "Sucuri": {
        "headers": [
            ("x-sucuri-id",     re.compile(r".+", re.I)),
            ("x-sucuri-cache",  re.compile(r".+", re.I)),
            ("server",          re.compile(r"Sucuri", re.I)),
        ],
        "cookies": re.compile(r"sucuri_cloudproxy_uuid", re.I),
        "body":    re.compile(r"sucuri|Access Denied - Sucuri", re.I),
    },
    "ModSecurity": {
        "headers": [
            ("server", re.compile(r"mod_security|NOYB", re.I)),
        ],
        "cookies": re.compile(r"^$"),  # no cookie sig
        "body":    re.compile(r"ModSecurity|This error was generated by Mod_Security", re.I),
    },
    "F5 BIG-IP ASM": {
        "headers": [
            ("server",       re.compile(r"BigIP|BIG-IP", re.I)),
            ("x-cnection",   re.compile(r".+", re.I)),
            ("set-cookie",   re.compile(r"BIGipServer|TS[0-9a-f]{8}", re.I)),
        ],
        "cookies": re.compile(r"BIGipServer|TS[0-9a-f]{8}", re.I),
        "body":    re.compile(r"Request Rejected|The requested URL was rejected", re.I),
    },
    "Barracuda": {
        "headers": [
            ("server", re.compile(r"barracuda", re.I)),
        ],
        "cookies": re.compile(r"barra_counter_session|BNI__BARRACUDA", re.I),
        "body":    re.compile(r"barracuda|Barracuda Networks", re.I),
    },
    "Fastly": {
        "headers": [
            ("via",           re.compile(r"varnish|fastly", re.I)),
            ("x-served-by",   re.compile(r"cache-", re.I)),
            ("x-cache",       re.compile(r"HIT|MISS", re.I)),
            ("x-fastly-request-id", re.compile(r".+", re.I)),
        ],
        "cookies": re.compile(r"^$"),
        "body":    re.compile(r"fastly|Varnish cache server", re.I),
    },
    "Nginx WAF": {
        "headers": [
            ("server", re.compile(r"nginx", re.I)),
            ("x-nf-request-id", re.compile(r".+", re.I)),
        ],
        "cookies": re.compile(r"^$"),
        "body":    re.compile(r"nginx|400 Bad Request", re.I),
    },
}

def waf_detect(domain: str) -> dict:
    """
    Detect WAF/CDN by analyzing response headers, cookies, and body.
    Also probes with a malicious payload to trigger WAF signatures.
    """
    section("WAF / CDN DETECTION")
    result = {"waf": None, "confidence": None, "signals": []}

    # Normal request
    normal_headers = {}
    normal_cookies = ""
    normal_body    = ""

    for scheme in ("https", "http"):
        try:
            req = urllib.request.Request(
                f"{scheme}://{domain}",
                headers={"User-Agent": "Mozilla/5.0 (GRIMOIRE/2.0)"}
            )
            with urllib.request.urlopen(req, timeout=6) as r:
                normal_headers = {k.lower(): v for k, v in r.headers.items()}
                normal_cookies = normal_headers.get("set-cookie", "")
                normal_body    = r.read(8192).decode(errors="replace")
            break
        except urllib.error.HTTPError as e:
            normal_headers = {k.lower(): v for k, v in e.headers.items()}
            normal_cookies = normal_headers.get("set-cookie", "")
            try:
                normal_body = e.read(8192).decode(errors="replace")
            except Exception:
                pass
            break
        except Exception:
            continue

    # Probe request — crafted to trigger WAF
    probe_headers = {}
    probe_body    = ""
    probe_status  = None
    probe_url     = f"https://{domain}/?id=1'%20OR%201=1--&cmd=<script>alert(1)</script>"
    try:
        req = urllib.request.Request(probe_url, headers={
            "User-Agent": "() { :; }; echo Content-Type: text/plain; echo; echo GRIMOIRE_WAF_TEST",
            "X-Forwarded-For": "' OR 1=1--",
        })
        with urllib.request.urlopen(req, timeout=6) as r:
            probe_status  = r.status
            probe_headers = {k.lower(): v for k, v in r.headers.items()}
            probe_body    = r.read(4096).decode(errors="replace")
    except urllib.error.HTTPError as e:
        probe_status  = e.code
        probe_headers = {k.lower(): v for k, v in e.headers.items()}
        try:
            probe_body = e.read(4096).decode(errors="replace")
        except Exception:
            pass
    except Exception:
        pass

    # Score each WAF
    scores = {}
    for waf_name, sigs in WAF_SIGNATURES.items():
        score = 0
        signals = []

        for header_name, pattern in sigs["headers"]:
            val = normal_headers.get(header_name, "") or probe_headers.get(header_name, "")
            if val and pattern.search(val):
                score += 2
                signals.append(f"header:{header_name}={val[:40]}")

        cookie_val = normal_cookies or probe_headers.get("set-cookie", "")
        if cookie_val and sigs["cookies"].search(cookie_val):
            score += 3
            signals.append(f"cookie:{cookie_val[:40]}")

        for body in (normal_body, probe_body):
            if body and sigs["body"].search(body):
                score += 2
                signals.append("body fingerprint")
                break

        if score > 0:
            scores[waf_name] = (score, signals)

    if scores:
        best = max(scores, key=lambda k: scores[k][0])
        score, signals = scores[best]
        confidence = "HIGH" if score >= 5 else ("MEDIUM" if score >= 3 else "LOW")
        result = {"waf": best, "confidence": confidence, "signals": signals}

        color = C.RED if confidence == "HIGH" else (C.YELLOW if confidence == "MEDIUM" else C.DIM)
        print(f"  {color}{C.BOLD}WAF Detected: {best}{C.RESET}")
        print(f"  {C.CYAN}Confidence{C.RESET}  {confidence}  (score: {score})")
        print(f"  {C.CYAN}Signals   {C.RESET}  {' | '.join(signals[:4])}")

        # Show other candidates
        others = [(k, v[0]) for k, v in scores.items() if k != best and v[0] >= 2]
        if others:
            print(f"  {C.DIM}Also possible: {', '.join(f'{k} ({s})' for k, s in others)}{C.RESET}")
    else:
        print(f"  {C.GREEN}No WAF/CDN detected{C.RESET}  {C.DIM}(or well-hidden){C.RESET}")

    # Probe result
    if probe_status and probe_status in (403, 406, 429, 503):
        print(f"  {C.YELLOW}[+] Probe triggered HTTP {probe_status} — WAF blocking confirmed{C.RESET}")
        result["blocked"] = True
    elif probe_status:
        print(f"  {C.DIM}Probe response: HTTP {probe_status}{C.RESET}")

    return result


# ══════════════════════════════════════════════════════════════
# 4. Shodan Lookup
# ══════════════════════════════════════════════════════════════

def shodan_lookup(ip: str, api_key: str = None) -> dict:
    """
    Query Shodan for host intelligence — open ports, banners, CVEs, tags.
    Requires a Shodan API key. Store in ~/.grimoire/config.json or pass directly.
    """
    section("SHODAN HOST INTELLIGENCE")

    # Load API key from config if not passed
    if not api_key:
        from pathlib import Path
        config_file = Path.home() / ".grimoire" / "config.json"
        if config_file.exists():
            try:
                cfg = json.loads(config_file.read_text())
                api_key = cfg.get("shodan_api_key")
            except Exception:
                pass

    if not api_key:
        print(f"  {C.YELLOW}[!] No Shodan API key found.{C.RESET}")
        print(f"  {C.DIM}Add it to ~/.grimoire/config.json:{C.RESET}")
        print(f'  {C.DIM}{{"shodan_api_key": "YOUR_KEY_HERE"}}{C.RESET}')
        print(f"  {C.DIM}Or get a free key at: https://account.shodan.io{C.RESET}")
        return {}

    try:
        url = f"https://api.shodan.io/shodan/host/{ip}?key={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "GRIMOIRE/2.0"})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())

        # Summary
        print(f"  {C.CYAN}IP          {C.RESET} {data.get('ip_str', ip)}")
        print(f"  {C.CYAN}Hostnames   {C.RESET} {', '.join(data.get('hostnames', [])) or 'none'}")
        print(f"  {C.CYAN}Country     {C.RESET} {data.get('country_name','?')} ({data.get('country_code','?')})")
        print(f"  {C.CYAN}City        {C.RESET} {data.get('city','?')}")
        print(f"  {C.CYAN}Org         {C.RESET} {data.get('org','?')}")
        print(f"  {C.CYAN}ISP         {C.RESET} {data.get('isp','?')}")
        print(f"  {C.CYAN}ASN         {C.RESET} {data.get('asn','?')}")
        print(f"  {C.CYAN}Last Update {C.RESET} {data.get('last_update','?')}")
        print(f"  {C.CYAN}Tags        {C.RESET} {', '.join(data.get('tags', [])) or 'none'}")

        # Open ports + banners
        ports = data.get("ports", [])
        if ports:
            print(f"\n  {C.RED}Open Ports ({len(ports)}):{C.RESET}")
            for svc in data.get("data", [])[:15]:
                port    = svc.get("port", "?")
                proto   = svc.get("transport", "tcp")
                product = svc.get("product", "")
                version = svc.get("version", "")
                banner  = svc.get("data", "").strip().splitlines()[0][:60] if svc.get("data") else ""
                cpes    = svc.get("cpe", [])
                line = f"  {C.GREEN}{port}/{proto:<6}{C.RESET} {product} {version}"
                if banner:
                    line += f"  {C.DIM}| {banner}{C.RESET}"
                print(line)
                if cpes:
                    print(f"  {C.DIM}  CPE: {', '.join(cpes[:2])}{C.RESET}")

        # CVEs
        vulns = data.get("vulns", {})
        if vulns:
            print(f"\n  {C.RED}{C.BOLD}CVEs ({len(vulns)}):{C.RESET}")
            for cve_id, cve_info in list(vulns.items())[:10]:
                cvss = cve_info.get("cvss", "?")
                summary = cve_info.get("summary", "")[:70]
                color = C.RED if float(cvss or 0) >= 7 else C.YELLOW
                print(f"  {color}{cve_id:<20}{C.RESET} CVSS:{cvss}  {C.DIM}{summary}{C.RESET}")
            if len(vulns) > 10:
                print(f"  {C.DIM}  ... and {len(vulns)-10} more{C.RESET}")
        else:
            print(f"\n  {C.DIM}No CVEs recorded by Shodan{C.RESET}")

        return data

    except urllib.error.HTTPError as e:
        if e.code == 401:
            print(f"  {C.RED}[!] Invalid Shodan API key{C.RESET}")
        elif e.code == 404:
            print(f"  {C.DIM}No Shodan data for {ip}{C.RESET}")
        else:
            print(f"  {C.YELLOW}[!] Shodan error: HTTP {e.code}{C.RESET}")
        return {}
    except Exception as e:
        print(f"  {C.YELLOW}[!] Shodan error: {e}{C.RESET}")
        return {}


# ══════════════════════════════════════════════════════════════