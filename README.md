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

## Exclusão de tratativas

- No portal (`site.js`), cada linha da tabela tem um botão **✕** que apaga a tratativa (com confirmação), via `POST /actions/delete`.
- Todas as gravações em `actions.json` são **atômicas** (ficheiro temporário + rename), pelo lado do site e do dashboard (`data_store.py`), evitando corrupção do JSON.

## Melhorias aplicadas

- **Cache de dados**: o Streamlit usa `@st.cache_data` com invalidação por `mtime` dos CSVs/`actions.json` (não relê os ~21 MB a cada interação); o `site.js` faz o mesmo para a lista de filiais.
- **IDs únicos e monotónicos** (`Date.now` vs. contador), agora compatíveis entre `site.js` e `data_store.py`.
- **Validação e limites** nos POSTs: corpo máximo de 64 KB, truncagem de campos (`filial` 150 / `ação` 2000 caracteres) e status restrito a `Planejada` / `Em andamento` / `Concluída`.
- **Banner de erro** no portal quando a gravação falha (`/?erro=gravacao`).
- **KPIs corrigidos**: a formatação de milhares já não altera o HTML (nomes de filial com vírgula ficam intactos).
- Constante única `DEFAULT_DURATION_DAYS = 14` partilhada entre o dashboard, o site e o `data_store.py`.

## Limitação na Vercel

O sistema de ficheiros da função serverless é **efémero**: no deploy da Vercel, alterações feitas via `api/index.js` são perdidas entre invocações. Para persistência real em produção, migrar `actions.json` para um armazenamento externo (Blob/KV/base de dados). O uso local (`node site.js`) não é afetado.
