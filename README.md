# PDCA de reclamações (PPM Dano × NC Falta)

Aplicação local em duas partes:

- `dashboard.py`: painel Streamlit **de uma filial por vez**, com diagrama de Gantt do PPM Dano × NC Falta, barras duplas das tratativas (período executado × período restante), marcos de início/término e análise de impacto antes × depois.
- `site.js`: portal Node.js em `http://localhost:5000` para registrar as tratativas (filial, descrição, **data de início e data final** e status). É este portal que alimenta o dashboard.
- Você também pode cadastrar tratativas diretamente dentro do próprio Streamlit, pela barra lateral.

Os CSVs continuam sendo a base histórica. As tratativas são persistidas em `actions.json`, criado automaticamente e compartilhado entre o site, o dashboard e a função serverless (`api/index.js`).

## Executar

No PowerShell, dentro desta pasta:

### 1. Iniciar o site de registro de tratativas (obrigatório para o dashboard):
```powershell
node site.js
```
Abre em `http://localhost:5000`. Também disponível pelos atalhos `run_site.ps1` e `iniciar_site.bat`.

### 2. Iniciar o Dashboard Streamlit:
```powershell
streamlit run dashboard.py
```
O dashboard abrirá em `http://localhost:8501`.

## Regra do Gantt

- Cada tratativa é projetada exatamente no intervalo informado (`start_date` → `end_date`); quando a data final não é preenchida, o sistema assume **início + 14 dias**.
- A barra é dividida em **período executado** (azul escuro, até hoje) e **período restante** (azul claro), com marcos ◆ no início e no término.
- O dashboard exibe **uma filial por vez**: as linhas `PPM Dano` e `NC Falta` mostram o volume de `qtd_reclamada` (dano) e `cantidad_itens` (falta) por período, e o impacto das tratativas é medido comparando janelas de mesmo tamanho antes × depois.
