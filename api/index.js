const fs = require('node:fs');
const path = require('node:path');

const ROOT = path.join(__dirname, '..');
const ACTIONS_PATH = path.join(ROOT, 'actions.json');

function readActions() {
  if (!fs.existsSync(ACTIONS_PATH)) return [];
  try {
    return JSON.parse(fs.readFileSync(ACTIONS_PATH, 'utf8'));
  } catch (error) {
    return [];
  }
}

module.exports = (req, res) => {
  if (req.method === 'POST') {
    let body = '';
    req.on('data', (chunk) => { body += chunk; });
    req.on('end', () => {
      const form = new URLSearchParams(body);
      const filial = (form.get('filial') || '').trim();
      const action = (form.get('action') || '').trim();
      const startDate = (form.get('start_date') || '').trim();
      const status = (form.get('status') || 'Planejada').trim();

      if (filial && action && startDate) {
        const actions = readActions();
        actions.push({ id: Date.now(), filial, action, start_date: startDate, status, created_at: new Date().toISOString() });
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
