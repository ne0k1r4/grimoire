# ═══════════════════════════════════════════════════════════════
#  GRIMOIRE v2.0 — web/__init__.py
#  Local Web Dashboard — Flask
#
#  Developer  : Light
#  Alias      : Neok1ra
#  GitHub     : https://github.com/ne0k1r4
#  Tool       : GRIMOIRE — The Death Note of the digital world
# ═══════════════════════════════════════════════════════════════

import os

RED   = "\033[91m"
DIM   = "\033[2m"
BOLD  = "\033[1m"
RESET = "\033[0m"
GRN   = "\033[92m"
YLW   = "\033[93m"

HTML_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>GRIMOIRE v2.0 — Neok1ra Operator Dashboard</title>
<style>
  :root {
    --bg:#0a0000; --bg2:#120000; --bg3:#1a0000;
    --red:#cc0000; --red2:#ff2222; --cream:#e8d5c4;
    --dim:#6a5a52; --border:#2a0000; --green:#22aa44;
    --yellow:#ccaa00; --cyan:#00aacc;
    --font:'Courier New',Courier,monospace;
  }
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--cream);font-family:var(--font);font-size:13px;min-height:100vh}
  ::-webkit-scrollbar{width:4px} ::-webkit-scrollbar-track{background:var(--bg2)}
  ::-webkit-scrollbar-thumb{background:var(--red)}
  header{background:var(--bg2);border-bottom:1px solid var(--red);padding:10px 20px;display:flex;justify-content:space-between;align-items:center}
  .logo{color:var(--red2);font-size:18px;font-weight:bold;letter-spacing:6px;text-shadow:0 0 12px #ff000055}
  .meta{color:var(--dim);font-size:10px;margin-top:2px}
  nav a{color:var(--dim);text-decoration:none;margin-left:18px;font-size:11px;letter-spacing:2px;text-transform:uppercase;transition:color .15s}
  nav a:hover{color:var(--red2)}
  .layout{display:grid;grid-template-columns:200px 1fr;height:calc(100vh - 44px)}
  .sidebar{background:var(--bg2);border-right:1px solid var(--border);overflow-y:auto}
  .sidebar-section{padding:10px 0}
  .sidebar-title{color:var(--red);font-size:9px;letter-spacing:3px;padding:4px 14px 6px;border-bottom:1px solid var(--border)}
  .mod-link{display:block;padding:8px 14px;color:var(--dim);text-decoration:none;font-size:11px;letter-spacing:1px;border-left:2px solid transparent;transition:all .15s;display:flex;justify-content:space-between;align-items:center}
  .mod-link:hover,.mod-link.active{color:var(--cream);border-left-color:var(--red);background:rgba(200,0,0,0.07)}
  .badge{font-size:9px;color:var(--green);border:1px solid var(--green);padding:1px 5px;border-radius:2px;letter-spacing:1px}
  .main{overflow-y:auto;display:flex;flex-direction:column}
  .topbar{background:var(--bg2);border-bottom:1px solid var(--border);padding:8px 16px;display:flex;flex-wrap:wrap;gap:20px;align-items:center}
  .stat{font-size:11px;color:var(--dim)} .stat span{color:var(--cream)}
  .content{padding:16px;flex:1}
  .grid2{display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:14px}
  .panel{background:var(--bg2);border:1px solid var(--border);margin-bottom:14px}
  .ph{padding:7px 12px;border-bottom:1px solid var(--border);color:var(--red);font-size:10px;letter-spacing:3px;font-weight:bold;display:flex;justify-content:space-between;align-items:center}
  .ph .count{color:var(--dim);font-size:10px;font-weight:normal;letter-spacing:0}
  .pb{padding:10px 12px}
  .entry{padding:6px 0;border-bottom:1px solid var(--border);display:grid;grid-template-columns:28px 1fr 80px 80px 1fr;gap:6px;align-items:center;font-size:11px}
  .entry:last-child{border:none}
  .risk-CRITICAL{color:#ff2222;font-weight:bold} .risk-HIGH{color:#cc0000}
  .risk-MEDIUM{color:#ccaa00} .risk-LOW{color:#00aacc} .risk-INFO{color:var(--dim)}
  .st-ACTIVE{color:#ff2222} .st-WATCHING{color:#ccaa00} .st-OWNED{color:#22aa44}
  .st-CLOSED{color:var(--dim)} .st-PENDING{color:#00aacc}
  .log-line{font-size:10px;padding:2px 0;border-bottom:1px solid rgba(40,0,0,.4);white-space:nowrap;overflow:hidden;text-overflow:ellipsis}
  .log-line:last-child{border:none}
  .log-ts{color:var(--red)} .log-mod{color:var(--cream);font-size:9px}
  .mods-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(160px,1fr));gap:10px}
  .mc{background:var(--bg);border:1px solid var(--border);padding:12px;cursor:pointer;transition:border-color .15s}
  .mc:hover{border-color:var(--red)}
  .mc-name{color:var(--red2);font-weight:bold;font-size:12px;letter-spacing:2px}
  .mc-desc{color:var(--dim);font-size:10px;margin-top:3px}
  .mc-live{color:var(--green);font-size:9px;margin-top:6px;letter-spacing:1px}
  .port-badge{display:inline-block;background:var(--bg3);border:1px solid var(--border);color:var(--cyan);font-size:10px;padding:1px 6px;margin:2px;border-radius:2px}
  .sub-entry{font-size:10px;padding:2px 0;color:var(--dim)} .sub-entry span{color:var(--cream)}
  footer{padding:6px 16px;color:var(--dim);font-size:10px;border-top:1px solid var(--border);background:var(--bg2);text-align:center}
  .pulse{animation:pulse 2s infinite} @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
</style>
</head>
<body>
<header>
  <div>
    <div class="logo">G R I M O I R E</div>
    <div class="meta">v2.0.0 &nbsp;·&nbsp; Developer: Light (Neok1ra) &nbsp;·&nbsp; github.com/ne0k1r4</div>
  </div>
  <nav>
    <a href="/" class="active">Dashboard</a>
    <a href="/codex">Codex</a>
    <a href="/api/sysinfo" target="_blank">API</a>
  </nav>
</header>
<div class="layout">
  <aside class="sidebar">
    <div class="sidebar-section">
      <div class="sidebar-title">MODULES</div>
      <a class="mod-link active" href="/">DASHBOARD</a>
      <a class="mod-link" href="/codex">CODEX <span class="badge">LIVE</span></a>
      <a class="mod-link" href="#">WRAITH <span class="badge">LIVE</span></a>
      <a class="mod-link" href="#">VOXCRYPT <span class="badge">LIVE</span></a>
      <a class="mod-link" href="#">FORGE <span class="badge">LIVE</span></a>
      <a class="mod-link" href="#">VAULT <span class="badge">LIVE</span></a>
      <a class="mod-link" href="#">PHANTOM <span class="badge">LIVE</span></a>
      <a class="mod-link" href="#">SOVEREIGN <span class="badge">LIVE</span></a>
    </div>
    <div class="sidebar-section">
      <div class="sidebar-title">RECON TARGETS</div>
      {% for t in targets[:8] %}
      <a class="mod-link" href="#">
        <span style="font-size:10px">{{ t.name[:16] }}</span>
        <span class="risk-{{ t.risk|default('LOW') }}" style="font-size:9px">{{ t.risk|default('?') }}</span>
      </a>
      {% endfor %}
    </div>
  </aside>
  <div class="main">
    <div class="topbar">
      <div class="stat">HOST <span>{{ host }}</span></div>
      <div class="stat">IP <span>{{ ip }}</span></div>
      <div class="stat">CPU <span id="cpu">{{ cpu }}</span></div>
      <div class="stat">RAM <span>{{ ram }}</span></div>
      <div class="stat">↑<span>{{ net_up }}</span> ↓<span>{{ net_down }}</span></div>
      <div class="stat">UP <span>{{ uptime }}</span></div>
      <div class="stat" style="margin-left:auto;color:var(--red)" id="clock"></div>
    </div>
    <div class="content">
      <!-- targets -->
      <div class="panel">
        <div class="ph">CODEX — TARGETS <span class="count">{{ targets|length }} total</span></div>
        <div class="pb">
          {% if targets %}
          {% for t in targets %}
          <div class="entry">
            <span style="color:var(--dim)">{{ loop.index }}</span>
            <span>{{ t.name }}</span>
            <span class="risk-{{ t.risk|default('LOW') }}">{{ t.risk|default('?') }}</span>
            <span class="st-{{ t.status }}">{{ t.status }}</span>
            <span style="color:var(--dim);font-size:10px">{{ t.notes[:35] }}</span>
          </div>
          {% endfor %}
          {% else %}
          <div style="color:var(--dim);padding:8px 0;font-size:11px">No targets. Run <code>grimoire codex add</code></div>
          {% endif %}
        </div>
      </div>
      <div class="grid2">
        <!-- modules -->
        <div class="panel">
          <div class="ph">MODULES</div>
          <div class="pb">
            <div class="mods-grid">
              {% for m in modules %}
              <div class="mc">
                <div class="mc-name">{{ m.name }}</div>
                <div class="mc-desc">{{ m.desc }}</div>
                <div class="mc-live pulse">● LIVE</div>
              </div>
              {% endfor %}
            </div>
          </div>
        </div>
        <!-- oplog -->
        <div class="panel">
          <div class="ph">OP LOG <span class="count">last 20</span></div>
          <div class="pb" id="oplog">
            {% for e in oplog %}
            <div class="log-line">
              <span class="log-ts">[{{ e.ts }}]</span>
              <span class="log-mod"> [{{ e.module|upper }}] </span>
              {{ e.msg }}
            </div>
            {% endfor %}
          </div>
        </div>
      </div>
    </div>
  </div>
</div>
<footer>
  GRIMOIRE v2.0.0 &nbsp;·&nbsp; Developer: <strong style="color:var(--red)">Light (Neok1ra)</strong>
  &nbsp;·&nbsp; github.com/ne0k1r4 &nbsp;·&nbsp; The Death Note of the digital world
</footer>
<script>
  // live clock
  function tick(){
    const now=new Date();
    document.getElementById('clock').textContent=
      now.toTimeString().slice(0,8);
  }
  setInterval(tick,1000); tick();

  // auto-refresh oplog every 10s
  setInterval(()=>{
    fetch('/api/oplog').then(r=>r.json()).then(data=>{
      const el=document.getElementById('oplog');
      if(!el) return;
      el.innerHTML=data.slice(-20).map(e=>
        `<div class="log-line"><span class="log-ts">[${e.ts}]</span> <span class="log-mod">[${e.module.toUpperCase()}]</span> ${e.msg}</div>`
      ).join('');
    }).catch(()=>{});
  },10000);
</script>
</body>
</html>"""

CODEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>GRIMOIRE — Codex</title>
<style>
  :root{--bg:#0a0000;--bg2:#120000;--red:#cc0000;--red2:#ff2222;--cream:#e8d5c4;--dim:#6a5a52;--border:#2a0000;--green:#22aa44;--yellow:#ccaa00;--cyan:#00aacc;--font:'Courier New',monospace}
  *{box-sizing:border-box;margin:0;padding:0}
  body{background:var(--bg);color:var(--cream);font-family:var(--font);font-size:13px;padding:20px}
  h1{color:var(--red2);letter-spacing:6px;margin-bottom:4px}
  .sub{color:var(--dim);font-size:11px;margin-bottom:20px}
  table{width:100%;border-collapse:collapse}
  th{color:var(--red);font-size:10px;letter-spacing:2px;padding:8px;border-bottom:1px solid var(--border);text-align:left}
  td{padding:8px;border-bottom:1px solid var(--border);font-size:12px}
  .risk-CRITICAL{color:#ff2222;font-weight:bold} .risk-HIGH{color:#cc0000}
  .risk-MEDIUM{color:#ccaa00} .risk-LOW{color:#00aacc} .risk-INFO{color:var(--dim)}
  .st-ACTIVE{color:#ff2222} .st-WATCHING{color:#ccaa00} .st-OWNED{color:#22aa44}
  .st-CLOSED{color:var(--dim)}
  a{color:var(--dim);text-decoration:none} a:hover{color:var(--red2)}
  footer{margin-top:20px;color:var(--dim);font-size:10px;text-align:center;border-top:1px solid var(--border);padding-top:10px}
</style>
</head>
<body>
<a href="/">← Dashboard</a>
<h1 style="margin-top:12px">C O D E X</h1>
<div class="sub">Developer: Light (Neok1ra) · github.com/ne0k1r4</div>
<table>
<tr><th>#</th><th>ID</th><th>TARGET</th><th>RISK</th><th>STATUS</th><th>TAGS</th><th>NOTES</th><th>ADDED</th></tr>
{% for t in targets %}
<tr>
  <td style="color:var(--dim)">{{ loop.index }}</td>
  <td style="color:var(--dim);font-size:10px">{{ t.id }}</td>
  <td>{{ t.name }}</td>
  <td class="risk-{{ t.risk|default('LOW') }}">{{ t.risk|default('?') }}</td>
  <td class="st-{{ t.status }}">{{ t.status }}</td>
  <td style="color:var(--dim);font-size:10px">{{ t.tags|join(', ') }}</td>
  <td style="color:var(--dim);font-size:10px">{{ t.notes[:40] }}</td>
  <td style="color:var(--dim);font-size:10px">{{ t.added }}</td>
</tr>
{% else %}
<tr><td colspan="8" style="color:var(--dim);padding:16px">No targets yet.</td></tr>
{% endfor %}
</table>
<footer>GRIMOIRE v2.0.0 · Developer: Light (Neok1ra) · The Death Note of the digital world</footer>
</body>
</html>"""


def launch(host: str = "127.0.0.1", port: int = 1337):
    try:
        from flask import Flask, jsonify, render_template_string
    except Exception as e:
        import sys as _sys, subprocess as _sub
        print(f"  {YLW}[!] Flask import error — {type(e).__name__}: {e}{RESET}")
        print(f"  {YLW}    Try: pip install --force-reinstall flask jinja2 --break-system-packages{RESET}")
        r = _sub.run([_sys.executable, "-m", "pip", "show", "flask"], capture_output=True, text=True)
        loc = [l for l in r.stdout.splitlines() if l.startswith("Location:")]
        print(f"  {YLW}    Flask: {loc[0] if loc else 'not found'}{RESET}")
        return

    from ..core.sysinfo import get_all as get_sys
    from ..core.oplog   import get_recent
    from ..codex        import _load as load_codex

    app = Flask(__name__)
    app.secret_key = os.urandom(16)

    MODULES_META = [
        {"name": "CODEX",     "desc": "Target journal"},
        {"name": "WRAITH",    "desc": "Passive recon"},
        {"name": "VOXCRYPT",  "desc": "Stego engine"},
        {"name": "FORGE",     "desc": "Payload generator"},
        {"name": "VAULT",     "desc": "Credential manager"},
        {"name": "PHANTOM",   "desc": "Pivot tracker"},
        {"name": "SOVEREIGN", "desc": "C2 manager"},
    ]

    @app.route("/")
    def index():
        s = get_sys()
        return render_template_string(HTML_TEMPLATE,
            host=s["host"], ip=s["ip"], cpu=s["cpu"],
            ram=f"{s['ram_used']}/{s['ram_total']}",
            net_up=s["net_up"], net_down=s["net_down"],
            uptime=s["uptime"],
            targets=load_codex(), modules=MODULES_META,
            oplog=get_recent(20), version="2.0.0")

    @app.route("/codex")
    def codex_page():
        return render_template_string(CODEX_TEMPLATE, targets=load_codex())

    @app.route("/api/sysinfo")
    def api_sysinfo(): return jsonify(get_sys())

    @app.route("/api/targets")
    def api_targets(): return jsonify(load_codex())

    @app.route("/api/oplog")
    def api_oplog(): return jsonify(get_recent(50))

    print(f"\n  {GRN}[*] GRIMOIRE v2.0 web UI → http://{host}:{port}{RESET}")
    print(f"  {GRN}    Developer: Light (Neok1ra) — github.com/ne0k1r4{RESET}")
    print(f"  {YLW}    Press Ctrl+C to stop.{RESET}\n")
    import logging
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    app.run(host=host, port=port, debug=False, use_reloader=False)


def cli_main(args):
    port = 1337
    if args:
        try: port = int(args[0])
        except ValueError: pass
    launch(port=port)
