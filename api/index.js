const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const ACTIONS_PATH = path.join(ROOT, 'actions.json');
const DEFAULT_DURATION_DAYS = 14;

function readActions() {
  if (!fs.existsSync(ACTIONS_PATH)) return [];
  try {
    return JSON.parse(fs.readFileSync(ACTIONS_PATH, 'utf8'));
  } catch (error) {
    return [];
  }
}

// Soma dias em uma data ISO (YYYY-MM-DD) mantendo o fuso local do formulário.
function addDaysIso(isoDate, days) {
  const parts = String(isoDate || '').split('-').map(Number);
  if (parts.length !== 3 || parts.some((value) => !Number.isFinite(value))) return '';
  const date = new Date(parts[0], parts[1] - 1, parts[2] + days);
  const pad = (value) => String(value).padStart(2, '0');
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}`;
}

// Garante que a tratativa tenha período válido (término posterior ao início).
function normalizePeriod(startDate, endDate) {
  const start = String(startDate || '').trim();
  const end = String(endDate || '').trim();
  return { start, end: end && end > start ? end : addDaysIso(start, DEFAULT_DURATION_DAYS) };
}

module.exports = (req, res) => {
  if (req.method === 'POST') {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      const form = new URLSearchParams(body);
      const filial = (form.get('filial') || '').trim();
      const action = (form.get('action') || '').trim();
      const status = (form.get('status') || 'Planejada').trim();
      const period = normalizePeriod(form.get('start_date'), form.get('end_date'));

      if (filial && action && period.start) {
        const actions = readActions();
        actions.push({
          id: Date.now(),
          filial,
          action,
          start_date: period.start,
          end_date: period.end,
          status,
          created_at: new Date().toISOString()
        });
        fs.writeFileSync(ACTIONS_PATH, JSON.stringify(actions, null, 2), 'utf8');
      }

      res.writeHead(303, { Location: '/' });
      res.end();
    });
    return;
  }

  res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
  res.end('<html><body><h1>PDCA API</h1></body></html>');
};
