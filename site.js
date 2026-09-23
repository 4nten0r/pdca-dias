const fs = require('node:fs');
const http = require('node:http');
const path = require('node:path');
const { URL } = require('node:url');

const ROOT = __dirname;
const ACTIONS_PATH = path.join(ROOT, 'actions.json');
const PORT = process.env.PORT || 5000;
const DASHBOARD_URL = process.env.DASHBOARD_URL || 'http://localhost:8501';

function readActions() {
  if (!fs.existsSync(ACTIONS_PATH)) return [];
  try {
    return JSON.parse(fs.readFileSync(ACTIONS_PATH, 'utf8'));
  } catch (error) {
    console.error('Não foi possível ler actions.json:', error.message);
    return [];
  }
}

function saveAction(action) {
  const actions = readActions();
  actions.push({ id: Date.now(), ...action, created_at: new Date().toISOString() });
  fs.writeFileSync(ACTIONS_PATH, JSON.stringify(actions, null, 2), 'utf8');
}

function escapeHtml(value) {
  return String(value).replace(/[&<>'"]/g, (character) => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', "'": '&#39;', '"': '&quot;'
  }[character]));
}

function readBranches() {
  const branches = new Set(readActions().map((item) => item.filial));
  for (const file of ['base_pronta.csv', 'base_falta_pronta.csv']) {
    const filePath = path.join(ROOT, file);
    if (!fs.existsSync(filePath)) continue;
    try {
      const content = fs.readFileSync(filePath, 'latin1');
      const lines = content.split(/\r?\n/).slice(1);
      const filialIndex = file === 'base_pronta.csv' ? 10 : 6;
      lines.forEach((line) => {
        const fields = line.split(';');
        if (fields[filialIndex]) branches.add(fields[filialIndex].trim());
      });
    } catch (err) {
      console.warn(`Aviso ao ler ${file}:`, err.message);
    }
  }
  return [...branches].filter(Boolean).sort();
}

function renderPage(alertMsg = '') {
  const actions = readActions().sort((a, b) => b.start_date.localeCompare(a.start_date));
  const branches = readBranches();
  const today = new Date().toISOString().slice(0, 10);

  const totalCount = actions.length;
  const ongoingCount = actions.filter((a) => a.status === 'Em andamento').length;
  const doneCount = actions.filter((a) => a.status === 'Concluída').length;

  const rows = actions.length
    ? actions.map((item) => {
        let badgeClass = 'badge-plan';
        if (item.status === 'Em andamento') badgeClass = 'badge-prog';
        if (item.status === 'Concluída') badgeClass = 'badge-done';

        const dateParts = (item.start_date || '').split('-');
        const formattedDate = dateParts.length === 3 ? `${dateParts[2]}/${dateParts[1]}/${dateParts[0]}` : item.start_date;

        return `<tr>
          <td data-label="Filial"><strong>${escapeHtml(item.filial)}</strong></td>
          <td data-label="Ação" class="td-action">${escapeHtml(item.action)}</td>
          <td data-label="Início">${escapeHtml(formattedDate)}</td>
          <td data-label="Status"><span class="badge ${badgeClass}">${escapeHtml(item.status)}</span></td>
        </tr>`;
      }).join('')
    : '<tr><td colspan="4" class="empty-state">Nenhuma ação cadastrada até o momento. Preencha o formulário ao lado para iniciar.</td></tr>';

  const options = branches.map((branch) => `<option value="${escapeHtml(branch)}">`).join('');

  return `<!doctype html>
<html lang="pt-BR">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
  <meta name="theme-color" content="#0f172a">
  <title>PDCA | Registro de Ações</title>
  <style>
    :root {
      --bg: #f8fafc;
      --card-bg: #ffffff;
      --text-main: #0f172a;
      --text-muted: #64748b;
      --border: #e2e8f0;
      --border-focus: #0284c7;
      --primary: #0284c7;
      --primary-hover: #0369a1;
      --header-bg: #0f172a;
      --badge-plan-bg: #fef3c7;
      --badge-plan-text: #b45309;
      --badge-plan-border: #fde68a;
      --badge-prog-bg: #ede9fe;
      --badge-prog-text: #6d28d9;
      --badge-prog-border: #ddd6fe;
      --badge-done-bg: #d1fae5;
      --badge-done-text: #047857;
      --badge-done-border: #a7f3d0;
      --radius: 12px;
      --radius-sm: 8px;
      --shadow: 0 4px 20px -2px rgba(15, 23, 42, 0.08);
      --shadow-sm: 0 1px 3px rgba(15, 23, 42, 0.06);
    }

    * { box-sizing: border-box; -webkit-tap-highlight-color: transparent; }
    
    body {
      margin: 0;
      background-color: var(--bg);
      color: var(--text-main);
      font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
      line-height: 1.5;
      -webkit-font-smoothing: antialiased;
    }

    /* Top Nav Bar */
    .top-nav {
      background-color: var(--header-bg);
      color: #ffffff;
      padding: 14px 20px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    }
    .top-nav-inner {
      max-width: 1280px;
      margin: 0 auto;
      display: flex;
      justify-content: space-between;
      align-items: center;
      gap: 12px;
      flex-wrap: wrap;
    }
    .logo-badge {
      display: flex;
      align-items: center;
      gap: 10px;
      font-weight: 700;
      font-size: 1.05rem;
      letter-spacing: -0.01em;
    }
    .logo-icon {
      background: linear-gradient(135deg, #0284c7, #38bdf8);
      color: #ffffff;
      padding: 6px 10px;
      border-radius: 8px;
      font-size: 0.9rem;
      font-weight: 800;
    }
    .btn-dashboard {
      background: rgba(255, 255, 255, 0.1);
      color: #ffffff;
      text-decoration: none;
      font-size: 0.88rem;
      font-weight: 600;
      padding: 8px 14px;
      border-radius: 8px;
      border: 1px solid rgba(255, 255, 255, 0.2);
      transition: all 0.2s ease;
      display: inline-flex;
      align-items: center;
      gap: 6px;
    }
    .btn-dashboard:hover {
      background: rgba(255, 255, 255, 0.2);
      border-color: rgba(255, 255, 255, 0.35);
    }

    /* Page Container */
    main {
      max-width: 1280px;
      margin: 0 auto;
      padding: 24px 16px 48px;
    }
    @media (min-width: 768px) {
      main { padding: 36px 24px 64px; }
    }

    /* Page Hero */
    .hero {
      margin-bottom: 24px;
    }
    .hero-eyebrow {
      color: var(--primary);
      font-size: 0.8rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.08em;
      margin-bottom: 6px;
    }
    .hero h1 {
      font-size: clamp(1.6rem, 4vw, 2.3rem);
      font-weight: 800;
      color: var(--text-main);
      margin: 0 0 8px;
      letter-spacing: -0.02em;
      line-height: 1.2;
    }
    .hero p {
      color: var(--text-muted);
      font-size: 1rem;
      margin: 0;
      max-width: 760px;
    }

    /* KPI Summary Strip */
    .kpi-strip {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(140px, 1fr));
      gap: 12px;
      margin-bottom: 24px;
    }
    .kpi-chip {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      padding: 12px 16px;
      box-shadow: var(--shadow-sm);
    }
    .kpi-chip-title {
      font-size: 0.72rem;
      text-transform: uppercase;
      font-weight: 700;
      color: var(--text-muted);
      letter-spacing: 0.05em;
    }
    .kpi-chip-value {
      font-size: 1.5rem;
      font-weight: 800;
      color: var(--text-main);
      margin-top: 2px;
    }

    /* Responsive App Grid */
    .app-layout {
      display: grid;
      grid-template-columns: 1fr;
      gap: 24px;
      align-items: start;
    }
    @media (min-width: 960px) {
      .app-layout {
        grid-template-columns: 380px 1fr;
        gap: 28px;
      }
    }

    /* Cards */
    .card {
      background: var(--card-bg);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      overflow: hidden;
    }
    .card-header {
      padding: 18px 20px;
      border-bottom: 1px solid var(--border);
      background: #fafbfc;
      display: flex;
      justify-content: space-between;
      align-items: center;
    }
    .card-title {
      font-size: 1.05rem;
      font-weight: 700;
      color: var(--text-main);
      margin: 0;
    }
    .card-body {
      padding: 20px;
    }

    /* Form Ergonomics (Mobile Touch-Friendly) */
    .form-group {
      margin-bottom: 16px;
    }
    label {
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      text-transform: uppercase;
      letter-spacing: 0.05em;
      color: #334155;
      margin-bottom: 6px;
    }
    input, textarea, select {
      width: 100%;
      min-height: 46px;
      padding: 10px 14px;
      border: 1px solid var(--border);
      border-radius: var(--radius-sm);
      background: #ffffff;
      color: var(--text-main);
      font-size: 16px; /* Prevents auto-zoom on iOS */
      font-family: inherit;
      transition: border-color 0.15s, box-shadow 0.15s;
    }
    input:focus, textarea:focus, select:focus {
      outline: none;
      border-color: var(--border-focus);
      box-shadow: 0 0 0 3px rgba(2, 132, 199, 0.15);
    }
    textarea {
      min-height: 95px;
      resize: vertical;
      line-height: 1.45;
    }
    .btn-submit {
      width: 100%;
      min-height: 48px;
      background: var(--primary);
      color: #ffffff;
      border: none;
      border-radius: var(--radius-sm);
      font-size: 1rem;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 2px 6px rgba(2, 132, 199, 0.3);
      transition: background-color 0.15s, transform 0.1s;
      margin-top: 8px;
      display: flex;
      justify-content: center;
      align-items: center;
      gap: 8px;
    }
    .btn-submit:hover {
      background: var(--primary-hover);
    }
    .btn-submit:active {
      transform: scale(0.99);
    }

    /* Status Badges */
    .badge {
      display: inline-block;
      padding: 4px 10px;
      border-radius: 20px;
      font-size: 0.76rem;
      font-weight: 700;
      letter-spacing: 0.02em;
    }
    .badge-plan { background: var(--badge-plan-bg); color: var(--badge-plan-text); border: 1px solid var(--badge-plan-border); }
    .badge-prog { background: var(--badge-prog-bg); color: var(--badge-prog-text); border: 1px solid var(--badge-prog-border); }
    .badge-done { background: var(--badge-done-bg); color: var(--badge-done-text); border: 1px solid var(--badge-done-border); }

    /* Desktop Table Styling */
    .table-container {
      overflow-x: auto;
      -webkit-overflow-scrolling: touch;
    }
    table {
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.92rem;
    }
    th {
      background: #fafbfc;
      color: var(--text-muted);
      font-size: 0.75rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.06em;
      padding: 12px 14px;
      border-bottom: 1px solid var(--border);
    }
    td {
      padding: 14px;
      border-bottom: 1px solid var(--border);
      vertical-align: middle;
    }
    tr:last-child td {
      border-bottom: none;
    }
    tr:hover td {
      background: #f8fafc;
    }
    .td-action {
      max-width: 320px;
      word-break: break-word;
    }
    .empty-state {
      text-align: center;
      padding: 48px 16px;
      color: var(--text-muted);
      font-size: 0.95rem;
    }

    /* Mobile Responsive Card Transformation for Table (< 768px) */
    @media (max-width: 767px) {
      .table-container {
        padding: 0;
      }
      table, thead, tbody, th, td, tr {
        display: block;
      }
      thead {
        display: none; /* Hide standard headers on mobile */
      }
      tbody tr {
        background: #ffffff;
        border: 1px solid var(--border);
        border-radius: var(--radius-sm);
        margin: 12px 16px;
        padding: 12px 14px;
        box-shadow: var(--shadow-sm);
      }
      tbody td {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding: 8px 0;
        border-bottom: 1px dashed #f1f5f9;
        font-size: 0.9rem;
      }
      tbody td:last-child {
        border-bottom: none;
      }
      tbody td::before {
        content: attr(data-label);
        font-weight: 700;
        font-size: 0.75rem;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.05em;
        margin-right: 12px;
      }
      tbody td.td-action {
        flex-direction: column;
        align-items: flex-start;
        gap: 4px;
        max-width: 100%;
      }
      tbody td.td-action::before {
        margin-bottom: 2px;
      }
    }
  </style>
</head>
<body>
  <nav class="top-nav">
    <div class="top-nav-inner">
      <div class="logo-badge">
        <span class="logo-icon">PDCA</span>
        <span>Gestão Logística de Ocorrências</span>
      </div>
      <a href="${escapeHtml(DASHBOARD_URL)}" target="_blank" class="btn-dashboard">
        📊 Abrir Dashboard Gantt ↗
      </a>
    </div>
  </nav>

  <main>
    <div class="hero">
      <div class="hero-eyebrow">Melhoria Contínua & Ações</div>
      <h1>Registro de Ações do PDCA</h1>
      <p>Cadastre as ações de intervenção operacional por filial. O dashboard cruza automaticamente cada ação com o volume de dano e falta no Diagrama de Gantt.</p>
    </div>

    <div class="kpi-strip">
      <div class="kpi-chip">
        <div class="kpi-chip-title">Total de Ações</div>
        <div class="kpi-chip-value">${totalCount}</div>
      </div>
      <div class="kpi-chip">
        <div class="kpi-chip-title">Em Andamento</div>
        <div class="kpi-chip-value" style="color: #6d28d9;">${ongoingCount}</div>
      </div>
      <div class="kpi-chip">
        <div class="kpi-chip-title">Concluídas</div>
        <div class="kpi-chip-value" style="color: #047857;">${doneCount}</div>
      </div>
    </div>

    <div class="app-layout">
      <!-- Formulário de Cadastro -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">➕ Nova Ação</h2>
        </div>
        <div class="card-body">
          <form method="post" action="/actions">
            <div class="form-group">
              <label for="filial">Filial Responsável</label>
              <input id="filial" name="filial" list="filiais" required placeholder="Digite ou selecione a filial" autocomplete="off">
              <datalist id="filiais">${options}</datalist>
            </div>

            <div class="form-group">
              <label for="action">Descrição da Ação</label>
              <textarea id="action" name="action" required placeholder="Ex.: Reforço de auditoria e conferência de saída de cargas"></textarea>
            </div>

            <div class="form-group">
              <label for="start_date">Data de Início da Ação</label>
              <input id="start_date" name="start_date" type="date" value="${today}" required>
            </div>

            <div class="form-group">
              <label for="status">Status</label>
              <select id="status" name="status">
                <option value="Planejada">🟡 Planejada</option>
                <option value="Em andamento" selected>🟣 Em andamento</option>
                <option value="Concluída">🟢 Concluída</option>
              </select>
            </div>

            <button type="submit" class="btn-submit">
              Adicionar ao Ciclo PDCA
            </button>
          </form>
        </div>
      </div>

      <!-- Lista de Ações Cadastradas -->
      <div class="card">
        <div class="card-header">
          <h2 class="card-title">📋 Ações Cadastradas (${totalCount})</h2>
        </div>
        <div class="table-container">
          <table class="responsive-table">
            <thead>
              <tr>
                <th>Filial</th>
                <th>Ação</th>
                <th>Início</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              ${rows}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </main>
</body>
</html>`;
}

function handleRequest(request, response) {
  const requestUrl = new URL(request.url, `http://${request.headers.host}`);
  if (request.method === 'GET' && (requestUrl.pathname === '/' || requestUrl.pathname === '/index.html')) {
    response.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    response.end(renderPage());
    return;
  }
  if (request.method === 'POST' && requestUrl.pathname === '/actions') {
    let body = '';
    request.on('data', (chunk) => { body += chunk; });
    request.on('end', () => {
      const form = new URLSearchParams(body);
      const filial = form.get('filial') || '';
      const action = form.get('action') || '';
      const startDate = form.get('start_date') || '';
      const status = form.get('status') || 'Planejada';

      if (filial.trim() && action.trim() && startDate.trim()) {
        saveAction({
          filial: filial.trim(),
          action: action.trim(),
          start_date: startDate.trim(),
          status: status.trim()
        });
      }

      response.writeHead(303, { Location: '/' });
      response.end();
    });
    return;
  }
  response.writeHead(404, { 'Content-Type': 'text/plain; charset=utf-8' });
  response.end('Página não encontrada');
}

if (require.main === module) {
  const server = http.createServer(handleRequest);
  server.listen(PORT, () => console.log(`Site PDCA em http://localhost:${PORT}`));
}

module.exports = handleRequest;
