# web dashboard — flask
# serves on localhost:1337

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
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="GRIMOIRE Unified Operator Suite local dashboard. Track engagement logs, active modules, and target databases.">
  <title>GRIMOIRE v2.0 — Operator Dashboard</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #06060a;
      --card-bg: rgba(15, 15, 24, 0.65);
      --border: rgba(230, 57, 70, 0.12);
      --border-hover: rgba(230, 57, 70, 0.35);
      --primary: #f4f4f6;
      --secondary: #a0a0ab;
      --dim: #52525b;
      --red: #e63946;
      --red-glow: rgba(230, 57, 70, 0.3);
      --green: #10b981;
      --green-glow: rgba(16, 185, 129, 0.2);
      --yellow: #f59e0b;
      --cyan: #06b6d4;
      --font-sans: 'Plus Jakarta Sans', sans-serif;
      --font-serif: 'Cinzel', serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background: var(--bg);
      color: var(--primary);
      font-family: var(--font-sans);
      font-size: 13px;
      line-height: 1.5;
      min-height: 100vh;
      overflow-x: hidden;
    }

    ::-webkit-scrollbar {
      width: 6px;
      height: 6px;
    }
    ::-webkit-scrollbar-track {
      background: rgba(10, 10, 15, 0.8);
    }
    ::-webkit-scrollbar-thumb {
      background: rgba(230, 57, 70, 0.3);
      border-radius: 3px;
    }
    ::-webkit-scrollbar-thumb:hover {
      background: var(--red);
    }

    header {
      background: rgba(10, 10, 15, 0.8);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      justify-content: space-between;
      align-items: center;
      position: sticky;
      top: 0;
      z-index: 100;
    }

    .brand {
      display: flex;
      flex-direction: column;
    }

    .logo {
      color: var(--primary);
      font-family: var(--font-serif);
      font-size: 20px;
      font-weight: 700;
      letter-spacing: 5px;
      text-shadow: 0 0 15px rgba(230, 57, 70, 0.4);
      display: flex;
      align-items: center;
      gap: 10px;
    }

    .logo span {
      color: var(--red);
    }

    .meta {
      color: var(--dim);
      font-size: 11px;
      font-weight: 400;
      margin-top: 2px;
      letter-spacing: 0.5px;
    }

    nav {
      display: flex;
      gap: 8px;
    }

    nav a {
      color: var(--secondary);
      text-decoration: none;
      padding: 8px 16px;
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      border-radius: 6px;
      border: 1px solid transparent;
      transition: all 0.2s ease;
    }

    nav a:hover, nav a.active {
      color: var(--primary);
      background: rgba(230, 57, 70, 0.08);
      border-color: rgba(230, 57, 70, 0.15);
    }

    .layout {
      display: grid;
      grid-template-columns: 240px 1fr;
      height: calc(100vh - 57px);
    }

    .sidebar {
      background: rgba(8, 8, 12, 0.95);
      border-right: 1px solid var(--border);
      overflow-y: auto;
      padding: 16px 0;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .sidebar-section-title {
      color: var(--red);
      font-size: 10px;
      font-weight: 700;
      letter-spacing: 2px;
      padding: 0 16px 6px;
      text-transform: uppercase;
      border-bottom: 1px solid rgba(255, 255, 255, 0.03);
      margin-bottom: 6px;
    }

    .sidebar-list {
      display: flex;
      flex-direction: column;
    }

    .mod-link {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 10px 16px;
      color: var(--secondary);
      text-decoration: none;
      font-size: 12px;
      font-weight: 500;
      letter-spacing: 0.5px;
      border-left: 3px solid transparent;
      transition: all 0.2s ease;
    }

    .mod-link:hover, .mod-link.active {
      color: var(--primary);
      background: rgba(230, 57, 70, 0.05);
      border-left-color: var(--red);
    }

    .badge {
      font-size: 9px;
      font-weight: 700;
      color: var(--green);
      background: rgba(16, 185, 129, 0.08);
      border: 1px solid rgba(16, 185, 129, 0.2);
      padding: 1px 5px;
      border-radius: 4px;
      letter-spacing: 0.5px;
    }

    .risk-badge {
      font-size: 9px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }

    .risk-CRITICAL { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.25); color: #ef4444; }
    .risk-HIGH { background: rgba(220, 38, 38, 0.1); border: 1px solid rgba(220, 38, 38, 0.25); color: #dc2626; }
    .risk-MEDIUM { background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.25); color: #f59e0b; }
    .risk-LOW { background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.25); color: #06b6d4; }
    .risk-INFO { background: rgba(160, 160, 171, 0.08); border: 1px solid rgba(160, 160, 171, 0.15); color: var(--secondary); }

    .main {
      overflow-y: auto;
      display: flex;
      flex-direction: column;
    }

    .topbar {
      background: rgba(10, 10, 15, 0.5);
      border-bottom: 1px solid var(--border);
      padding: 12px 24px;
      display: flex;
      flex-wrap: wrap;
      gap: 16px;
      align-items: center;
    }

    .stat-card {
      background: rgba(255, 255, 255, 0.02);
      border: 1px solid rgba(255, 255, 255, 0.04);
      padding: 6px 12px;
      border-radius: 6px;
      font-size: 11px;
      font-weight: 500;
      color: var(--secondary);
    }

    .stat-card span {
      color: var(--primary);
      font-weight: 600;
      margin-left: 6px;
      font-family: var(--font-mono);
    }

    .clock {
      margin-left: auto;
      color: var(--red);
      font-family: var(--font-mono);
      font-weight: 600;
      font-size: 12px;
      letter-spacing: 1px;
      background: rgba(230, 57, 70, 0.06);
      border: 1px solid rgba(230, 57, 70, 0.15);
      padding: 4px 10px;
      border-radius: 6px;
    }

    .content {
      padding: 24px;
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .panel {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
      transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
      display: flex;
      flex-direction: column;
    }

    .panel:hover {
      border-color: var(--border-hover);
      box-shadow: 0 8px 30px rgba(230, 57, 70, 0.06);
    }

    .panel-header {
      padding: 14px 20px;
      border-bottom: 1px solid var(--border);
      display: flex;
      justify-content: space-between;
      align-items: center;
    }

    .panel-title {
      font-family: var(--font-serif);
      color: var(--red);
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 2px;
    }

    .panel-meta {
      color: var(--dim);
      font-size: 11px;
    }

    .panel-body {
      padding: 20px;
      overflow-x: auto;
    }

    .table-container {
      width: 100%;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }

    th {
      padding: 10px 16px;
      font-weight: 600;
      color: var(--secondary);
      font-size: 11px;
      letter-spacing: 1px;
      text-transform: uppercase;
      border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    }

    td {
      padding: 12px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.03);
      color: var(--primary);
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:hover td {
      background: rgba(255, 255, 255, 0.01);
    }

    .status-text {
      font-weight: 600;
      font-size: 11px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }

    .st-ACTIVE { color: var(--red); }
    .st-WATCHING { color: var(--yellow); }
    .st-OWNED { color: var(--green); }
    .st-CLOSED { color: var(--dim); }
    .st-PENDING { color: var(--cyan); }

    .grid-2 {
      display: grid;
      grid-template-columns: 1fr 1.2fr;
      gap: 20px;
    }

    .modules-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
      gap: 12px;
    }

    .module-card {
      background: rgba(255, 255, 255, 0.015);
      border: 1px solid rgba(255, 255, 255, 0.03);
      border-radius: 8px;
      padding: 14px;
      transition: all 0.2s ease;
      cursor: pointer;
      display: flex;
      flex-direction: column;
      gap: 6px;
    }

    .module-card:hover {
      background: rgba(230, 57, 70, 0.03);
      border-color: rgba(230, 57, 70, 0.2);
      transform: translateY(-2px);
    }

    .module-name {
      color: var(--primary);
      font-family: var(--font-serif);
      font-weight: 700;
      font-size: 13px;
      letter-spacing: 1px;
    }

    .module-desc {
      color: var(--secondary);
      font-size: 10.5px;
      line-height: 1.3;
    }

    .module-status {
      display: flex;
      align-items: center;
      gap: 5px;
      color: var(--green);
      font-size: 9px;
      font-weight: 700;
      letter-spacing: 0.5px;
      margin-top: auto;
    }

    .status-dot {
      width: 5px;
      height: 5px;
      background: var(--green);
      border-radius: 50%;
      box-shadow: 0 0 8px var(--green);
    }

    .oplog-container {
      font-family: var(--font-mono);
      font-size: 11.5px;
      max-height: 280px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 8px;
      padding-right: 6px;
    }

    .log-entry {
      padding: 6px 10px;
      background: rgba(255, 255, 255, 0.01);
      border-radius: 4px;
      border-left: 3px solid var(--border);
      display: flex;
      gap: 12px;
      align-items: flex-start;
    }

    .log-ts {
      color: var(--red);
      font-weight: 500;
      flex-shrink: 0;
    }

    .log-mod {
      color: var(--secondary);
      font-weight: 600;
      text-transform: uppercase;
      font-size: 10.5px;
      flex-shrink: 0;
      width: 75px;
    }

    .log-msg {
      color: var(--primary);
      word-break: break-all;
    }

    .log-CRITICAL { border-left-color: #ef4444; background: rgba(239, 68, 68, 0.03); }
    .log-WARN { border-left-color: var(--yellow); background: rgba(245, 158, 11, 0.03); }
    .log-ERROR { border-left-color: var(--red); background: rgba(230, 57, 70, 0.03); }

    footer {
      padding: 16px;
      color: var(--dim);
      font-size: 11px;
      text-align: center;
      border-top: 1px solid var(--border);
      background: rgba(8, 8, 12, 0.95);
      letter-spacing: 0.5px;
    }

    footer strong {
      color: var(--red);
      font-weight: 600;
    }

    .pulse {
      animation: pulse-glow 2s infinite ease-in-out;
    }

    @keyframes pulse-glow {
      0%, 100% { opacity: 1; }
      50% { opacity: 0.4; }
    }
  </style>
</head>
<body>
  <header>
    <div class="brand">
      <h1 class="logo">G R I M O I R E<span>.</span></h1>
      <div class="meta">v2.1.0 &nbsp;·&nbsp; Unified Operator Suite</div>
    </div>
    <nav>
      <a href="/" class="active" id="nav-dashboard">Dashboard</a>
      <a href="/codex" id="nav-codex">Codex</a>
      <a href="/api/sysinfo" target="_blank" id="nav-api">API Status</a>
    </nav>
  </header>

  <main class="layout">
    <aside class="sidebar">
      <div>
        <div class="sidebar-section-title">Suite Modules</div>
        <div class="sidebar-list">
          <a class="mod-link active" href="/" id="link-dash">Dashboard</a>
          <a class="mod-link" href="/codex" id="link-codex">Codex Targets</a>
          <a class="mod-link" href="#" id="link-wraith">Wraith Recon <span class="badge">Live</span></a>
          <a class="mod-link" href="#" id="link-vox">Voxcrypt Stego <span class="badge">Live</span></a>
          <a class="mod-link" href="#" id="link-forge">Forge Payload <span class="badge">Live</span></a>
          <a class="mod-link" href="#" id="link-phantom">Phantom Pivot <span class="badge">Live</span></a>
          <a class="mod-link" href="#" id="link-sov">Sovereign C2 <span class="badge">Live</span></a>
        </div>
      </div>
      <div>
        <div class="sidebar-section-title">Recent Targets</div>
        <div class="sidebar-list" id="sidebar-targets">
          {% for t in targets[:6] %}
          <a class="mod-link" href="#" id="target-side-{{ loop.index }}">
            <span style="overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:110px;">{{ t.name }}</span>
            <span class="risk-badge risk-{{ t.risk|default('LOW') }}" style="font-size:8px;padding:1px 4px;">{{ t.risk|default('?') }}</span>
          </a>
          {% endfor %}
        </div>
      </div>
    </aside>

    <div class="main">
      <section class="topbar">
        <div class="stat-card" id="stat-host">HOST<span>{{ host }}</span></div>
        <div class="stat-card" id="stat-ip">IP<span>{{ ip }}</span></div>
        <div class="stat-card" id="stat-cpu">CPU<span id="cpu">{{ cpu }}</span></div>
        <div class="stat-card" id="stat-ram">RAM<span>{{ ram }}</span></div>
        <div class="stat-card" id="stat-net">NET<span>↑{{ net_up }} ↓{{ net_down }}</span></div>
        <div class="stat-card" id="stat-uptime">UPTIME<span>{{ uptime }}</span></div>
        <div class="clock" id="clock">00:00:00</div>
      </section>

      <section class="content">
        <!-- Active Targets Panel -->
        <div class="panel">
          <div class="panel-header">
            <h2 class="panel-title">Codex Active Targets</h2>
            <div class="panel-meta" id="codex-count">{{ targets|length }} tracked target(s)</div>
          </div>
          <div class="panel-body">
            <div class="table-container">
              <table>
                <thead>
                  <tr>
                    <th style="width: 50px;">Index</th>
                    <th>Target Name</th>
                    <th>Risk Rating</th>
                    <th>Status</th>
                    <th>Notes Summary</th>
                  </tr>
                </thead>
                <tbody id="targets-table-body">
                  {% if targets %}
                  {% for t in targets %}
                  <tr>
                    <td style="color: var(--dim);">{{ loop.index }}</td>
                    <td style="font-weight: 500;">{{ t.name }}</td>
                    <td><span class="risk-badge risk-{{ t.risk|default('LOW') }}">{{ t.risk|default('?') }}</span></td>
                    <td><span class="status-text st-{{ t.status }}">{{ t.status }}</span></td>
                    <td style="color: var(--secondary); font-size: 12px;">{{ t.notes[:65] }}{% if t.notes|length > 65 %}...{% endif %}</td>
                  </tr>
                  {% endfor %}
                  {% else %}
                  <tr>
                    <td colspan="5" style="color: var(--dim); text-align: center; padding: 24px;">No active targets. Run 'grimoire codex' in the CLI to register.</td>
                  </tr>
                  {% endif %}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        <div class="grid-2">
          <!-- Modules Status -->
          <div class="panel">
            <div class="panel-header">
              <h2 class="panel-title">Operator Modules</h2>
              <div class="panel-meta">Capabilities</div>
            </div>
            <div class="panel-body">
              <div class="modules-grid">
                {% for m in modules %}
                <div class="module-card">
                  <div class="module-name">{{ m.name }}</div>
                  <div class="module-desc">{{ m.desc }}</div>
                  <div class="module-status">
                    <div class="status-dot pulse"></div>
                    <span>ACTIVE</span>
                  </div>
                </div>
                {% endfor %}
              </div>
            </div>
          </div>

          <!-- Op Log -->
          <div class="panel">
            <div class="panel-header">
              <h2 class="panel-title">Operational Log</h2>
              <div class="panel-meta">Timeline</div>
            </div>
            <div class="panel-body">
              <div class="oplog-container" id="oplog">
                {% for e in oplog %}
                <div class="log-entry log-{{ e.level|default('INFO') }}">
                  <span class="log-ts">[{{ e.ts }}]</span>
                  <span class="log-mod">[{{ e.module|upper }}]</span>
                  <span class="log-msg">{{ e.msg }}</span>
                </div>
                {% endfor %}
              </div>
            </div>
          </div>
        </div>
      </section>
    </div>
  </main>

  <footer>
    GRIMOIRE v2.1.0 &nbsp;·&nbsp; Engineered by <strong>Light (Neok1ra)</strong> &nbsp;·&nbsp; The Death Note of the digital world
  </footer>

  <script>
    // Live Clock
    function tick() {
      const now = new Date();
      document.getElementById('clock').textContent = now.toTimeString().slice(0, 8);
    }
    setInterval(tick, 1000);
    tick();

    // Auto-refresh stats and oplog
    function refreshData() {
      // Refresh Op Log
      fetch('/api/oplog')
        .then(r => r.json())
        .then(data => {
          const el = document.getElementById('oplog');
          if (!el) return;
          el.innerHTML = data.slice(-20).reverse().map(e => {
            const lvl = e.level || 'INFO';
            return `<div class="log-entry log-${lvl}">
              <span class="log-ts">[${e.ts}]</span>
              <span class="log-mod">[${e.module.toUpperCase()}]</span>
              <span class="log-msg">${e.msg}</span>
            </div>`;
          }).join('');
        })
        .catch(() => {});

      // Refresh CPU
      fetch('/api/sysinfo')
        .then(r => r.json())
        .then(data => {
          const cpuEl = document.getElementById('cpu');
          if (cpuEl && data.cpu) {
            cpuEl.textContent = data.cpu;
          }
        })
        .catch(() => {});
    }

    setInterval(refreshData, 5000);
  </script>
</body>
</html>"""

CODEX_TEMPLATE = r"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="GRIMOIRE targets journal - active intelligence catalog.">
  <title>GRIMOIRE — Codex targets</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Cinzel:wght@500;700&family=Plus+Jakarta+Sans:wght@300;400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #06060a;
      --card-bg: rgba(15, 15, 24, 0.65);
      --border: rgba(230, 57, 70, 0.12);
      --border-hover: rgba(230, 57, 70, 0.35);
      --primary: #f4f4f6;
      --secondary: #a0a0ab;
      --dim: #52525b;
      --red: #e63946;
      --green: #10b981;
      --yellow: #f59e0b;
      --cyan: #06b6d4;
      --font-sans: 'Plus Jakarta Sans', sans-serif;
      --font-serif: 'Cinzel', serif;
      --font-mono: 'JetBrains Mono', monospace;
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      background: var(--bg);
      color: var(--primary);
      font-family: var(--font-sans);
      font-size: 13px;
      line-height: 1.5;
      padding: 30px;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      gap: 20px;
    }

    .back-btn {
      color: var(--secondary);
      text-decoration: none;
      font-size: 11px;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 1px;
      display: inline-flex;
      align-items: center;
      gap: 6px;
      transition: color 0.2s ease;
      width: fit-content;
    }

    .back-btn:hover {
      color: var(--red);
    }

    h1 {
      font-family: var(--font-serif);
      color: var(--primary);
      font-size: 28px;
      font-weight: 700;
      letter-spacing: 8px;
      text-shadow: 0 0 15px rgba(230, 57, 70, 0.4);
      margin-top: 10px;
    }

    h1 span {
      color: var(--red);
    }

    .sub {
      color: var(--secondary);
      font-size: 12px;
      margin-bottom: 20px;
      letter-spacing: 0.5px;
    }

    .panel {
      background: var(--card-bg);
      backdrop-filter: blur(12px);
      -webkit-backdrop-filter: blur(12px);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: 0 4px 30px rgba(0, 0, 0, 0.4);
      padding: 24px;
      overflow-x: auto;
      flex: 1;
    }

    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
    }

    th {
      padding: 12px 16px;
      font-weight: 600;
      color: var(--secondary);
      font-size: 11px;
      letter-spacing: 1.5px;
      text-transform: uppercase;
      border-bottom: 1.5px solid var(--border);
    }

    td {
      padding: 14px 16px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.04);
      color: var(--primary);
    }

    tr:last-child td {
      border-bottom: none;
    }

    tr:hover td {
      background: rgba(255, 255, 255, 0.015);
    }

    .risk-badge {
      font-size: 9px;
      font-weight: 700;
      padding: 2px 6px;
      border-radius: 4px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
      display: inline-block;
    }

    .risk-CRITICAL { background: rgba(239, 68, 68, 0.1); border: 1px solid rgba(239, 68, 68, 0.25); color: #ef4444; }
    .risk-HIGH { background: rgba(220, 38, 38, 0.1); border: 1px solid rgba(220, 38, 38, 0.25); color: #dc2626; }
    .risk-MEDIUM { background: rgba(245, 158, 11, 0.1); border: 1px solid rgba(245, 158, 11, 0.25); color: #f59e0b; }
    .risk-LOW { background: rgba(6, 182, 212, 0.1); border: 1px solid rgba(6, 182, 212, 0.25); color: #06b6d4; }
    .risk-INFO { background: rgba(160, 160, 171, 0.08); border: 1px solid rgba(160, 160, 171, 0.15); color: var(--secondary); }

    .status-text {
      font-weight: 600;
      font-size: 11px;
      letter-spacing: 0.5px;
      text-transform: uppercase;
    }

    .st-ACTIVE { color: var(--red); }
    .st-WATCHING { color: var(--yellow); }
    .st-OWNED { color: var(--green); }
    .st-CLOSED { color: var(--dim); }
    .st-PENDING { color: var(--cyan); }

    .tag {
      background: rgba(255, 255, 255, 0.03);
      border: 1px solid rgba(255, 255, 255, 0.06);
      color: var(--secondary);
      padding: 1px 6px;
      border-radius: 4px;
      font-size: 10px;
      font-family: var(--font-mono);
      margin-right: 4px;
      display: inline-block;
    }

    footer {
      padding-top: 20px;
      color: var(--dim);
      font-size: 11px;
      text-align: center;
      border-top: 1px solid var(--border);
      letter-spacing: 0.5px;
    }

    footer strong {
      color: var(--red);
    }
  </style>
</head>
<body>
  <a href="/" class="back-btn" id="btn-back">← Back to Dashboard</a>
  <h1 id="heading-codex">C O D E X<span>.</span></h1>
  <div class="sub">Grimoire Active Intel Ledger &nbsp;·&nbsp; Target Database</div>

  <div class="panel">
    <table>
      <thead>
        <tr>
          <th style="width: 60px;">Index</th>
          <th>ID</th>
          <th>Target Name</th>
          <th>Risk Rating</th>
          <th>Status</th>
          <th>Tags</th>
          <th>Added Date</th>
        </tr>
      </thead>
      <tbody>
        {% for t in targets %}
        <tr>
          <td style="color: var(--dim);">{{ loop.index }}</td>
          <td style="font-family: var(--font-mono); font-size: 11px; color: var(--secondary);">{{ t.id }}</td>
          <td style="font-weight: 600;">{{ t.name }}</td>
          <td><span class="risk-badge risk-{{ t.risk|default('LOW') }}">{{ t.risk|default('?') }}</span></td>
          <td><span class="status-text st-{{ t.status }}">{{ t.status }}</span></td>
          <td>
            {% for tag in t.tags %}
            <span class="tag">{{ tag }}</span>
            {% else %}
            <span style="color: var(--dim); font-size: 11px;">-</span>
            {% endfor %}
          </td>
          <td style="color: var(--secondary); font-size: 12px;">{{ t.added }}</td>
        </tr>
        {% else %}
        <tr>
          <td colspan="7" style="color: var(--dim); text-align: center; padding: 32px;">No targets registered in codex database.</td>
        </tr>
        {% endfor %}
      </tbody>
    </table>
  </div>

  <footer>
    GRIMOIRE v2.1.0 &nbsp;·&nbsp; Engineered by <strong>Light (Neok1ra)</strong>
  </footer>
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

    print(f"\n  {GRN}[*] GRIMOIRE v2.1 web UI → http://{host}:{port}{RESET}")
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
