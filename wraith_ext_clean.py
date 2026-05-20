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