# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE v2.0 — core/sysinfo.py
#  System stats — stdlib only, zero deps
#
#  Developer  : Light
#  Alias      : Neok1ra
#  GitHub     : https://github.com/ne0k1r4
#  Tool       : GRIMOIRE — The Death Note of the digital world
# ═══════════════════════════════════════════════════════════════

import os, time, platform, socket, struct

_prev_net  = None
_prev_time = None
_cpu_prev  = (None, None)


def _read_cpu():
    try:
        with open("/proc/stat") as f: line = f.readline()
        fields = list(map(int, line.split()[1:]))
        return sum(fields), fields[3]
    except: return None, None


def get_cpu_percent() -> str:
    global _cpu_prev
    total, idle = _read_cpu()
    if total is None: return "N/A"
    prev_total, prev_idle = _cpu_prev
    _cpu_prev = (total, idle)
    if prev_total is None: return "..."
    dt = total - prev_total
    di = idle  - prev_idle
    if dt == 0: return "0.0%"
    return f"{100.0*(1-di/dt):.1f}%"


def get_ram() -> dict:
    try:
        info = {}
        with open("/proc/meminfo") as f:
            for line in f:
                k, v = line.split(":")
                info[k.strip()] = int(v.strip().split()[0])
        total = info.get("MemTotal", 0)
        avail = info.get("MemAvailable", 0)
        used  = total - avail
        fmt   = lambda kb: f"{kb/1024/1024:.1f}G"
        return {"used": fmt(used), "total": fmt(total), "pct": f"{100*used/total:.0f}%"}
    except: return {"used":"?","total":"?","pct":"?"}


def get_net_io() -> dict:
    global _prev_net, _prev_time
    try:
        stats = {}
        with open("/proc/net/dev") as f: lines = f.readlines()[2:]
        for line in lines:
            parts = line.split(); iface = parts[0].rstrip(":")
            if iface == "lo": continue
            stats[iface] = (int(parts[1]), int(parts[9]))
        now = time.time()
        if _prev_net is None:
            _prev_net = stats; _prev_time = now
            return {"up":"...","down":"..."}
        dt = now - _prev_time
        if dt <= 0: return {"up":"...","down":"..."}
        tr = sum(v[0] for v in stats.values())
        ts = sum(v[1] for v in stats.values())
        pr = sum(v[0] for v in _prev_net.values())
        ps = sum(v[1] for v in _prev_net.values())
        _prev_net = stats; _prev_time = now
        h = lambda kbs: f"{kbs/1024:.1f}M/s" if kbs > 1024 else f"{kbs:.1f}K/s"
        return {"down": h((tr-pr)/1024/dt), "up": h((ts-ps)/1024/dt)}
    except: return {"up":"?","down":"?"}


def get_uptime() -> str:
    try:
        with open("/proc/uptime") as f: secs = float(f.read().split()[0])
        return f"{int(secs//3600)}h {int((secs%3600)//60)}m"
    except: return "?"


def get_all() -> dict:
    ram = get_ram()
    net = get_net_io()
    try:    host = socket.gethostname()
    except: host = "unknown"
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80)); ip = s.getsockname()[0]; s.close()
    except: ip = "127.0.0.1"
    return {
        "cpu":       get_cpu_percent(),
        "ram_used":  ram["used"],
        "ram_total": ram["total"],
        "ram_pct":   ram["pct"],
        "net_up":    net["up"],
        "net_down":  net["down"],
        "host":      host,
        "ip":        ip,
        "uptime":    get_uptime(),
        "os":        platform.system(),
    }
