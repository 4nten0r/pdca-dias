# PDCA de reclamações

Aplicação local em duas partes:

- `dashboard.py`: painel Streamlit com Gantt executivo corporativo, datas reais (`DD/MM/AAAA`), visão mensal, matriz de valores e análise de impacto PDCA.
- `site.py` (ou `site.js`): formulário web em `http://localhost:5000` para registrar ações no PDCA.
- **Dica:** Agora você também pode cadastrar ações diretamente dentro do próprio Streamlit, pela barra lateral!

Os CSVs continuam sendo a base histórica. As ações são persistidas em `actions.json`, criado automaticamente e compartilhado.

## Executar

No PowerShell, dentro desta pasta:

### 1. Iniciar o Dashboard Streamlit:
```powershell
streamlit run dashboard.py
```
O dashboard abrirá em `http://localhost:8501`. Na barra lateral, você pode cadastrar ações diretamente ou navegar pelo Gantt.

### 2. (Opcional) Iniciar o site de registro de ações em Python:
Se quiser abrir o formulário web na porta 5000:
```powershell
python site.py
```
*Não é necessário ter o Node.js instalado; o `site.py` funciona nativamente em Python puro.*

O dashboard abre em `http://localhost:8501`.

## Regra do Gantt

Como o formulário pede somente o período de início, cada ação aparece no Gantt com uma janela visual de sete dias. O impacto operacional é acompanhado no gráfico semanal, que soma `qtd_reclamada` da base de dano e `cantidad_itens` da base de falta por filial.
