import datetime
from typing import List, Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_store import init_db, read_actions, read_occurrences

# ---------------------------------------------------------
# Configuração da Página e Design Corporativo
# ---------------------------------------------------------
st.set_page_config(
    page_title="PDCA Logístico | Ocorrências & Ações",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilo Corporativo Moderno (Paleta Slate & Navy Executiva)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
    background-color: #0b0f19;
    color: #f1f5f9;
}

.block-container {
    max-width: 1600px;
    padding-top: 1.5rem;
    padding-bottom: 3rem;
}

/* Sidebar Styling */
[data-testid="stSidebar"] {
    background-color: #0f172a;
    border-right: 1px solid rgba(148, 163, 184, 0.15);
}
[data-testid="stSidebarUserContent"] {
    padding: 1.25rem 1rem;
}

/* Header Banner */
.corp-header {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 12px;
    padding: 1.5rem 2rem;
    margin-bottom: 1.8rem;
    box-shadow: 0 4px 20px -2px rgba(0, 0, 0, 0.35);
}
.corp-title {
    font-size: 2rem;
    font-weight: 800;
    color: #ffffff;
    margin: 0 0 0.4rem 0;
    letter-spacing: -0.02em;
}
.corp-subtitle {
    font-size: 0.98rem;
    color: #94a3b8;
    margin: 0;
}

/* KPI Cards */
.kpi-container {
    background: linear-gradient(145deg, #1e293b 0%, #172033 100%);
    border: 1px solid rgba(148, 163, 184, 0.18);
    border-radius: 12px;
    padding: 1.25rem 1.4rem;
    box-shadow: 0 4px 12px rgba(0,0,0,0.2);
    position: relative;
    overflow: hidden;
}
.kpi-container::before {
    content: "";
    position: absolute;
    top: 0; left: 0; right: 0; height: 3px;
    background: linear-gradient(90deg, #0284c7, #38bdf8);
}
.kpi-title {
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
    color: #94a3b8;
    margin-bottom: 0.4rem;
}
.kpi-value {
    font-size: 2.1rem;
    font-weight: 800;
    color: #f8fafc;
    letter-spacing: -0.03em;
    line-height: 1.1;
}
.kpi-sub {
    font-size: 0.82rem;
    color: #64748b;
    margin-top: 0.35rem;
}

/* Section Cards */
.section-card {
    background-color: #111827;
    border: 1px solid rgba(148, 163, 184, 0.16);
    border-radius: 12px;
    padding: 1.4rem;
    margin-bottom: 1.5rem;
}

/* Action Impact Badges */
.badge-action {
    display: inline-block;
    padding: 0.2rem 0.6rem;
    border-radius: 6px;
    font-size: 0.8rem;
    font-weight: 600;
}
.badge-planned { background: #3b2a0c; color: #f59e0b; border: 1px solid #78350f; }
.badge-ongoing { background: #1e1b4b; color: #a78bfa; border: 1px solid #4338ca; }
.badge-done { background: #062d22; color: #34d399; border: 1px solid #065f46; }

/* Tabs customization */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background-color: transparent;
}
.stTabs [data-baseweb="tab"] {
    background-color: #1e293b;
    border-radius: 8px 8px 0 0;
    padding: 10px 20px;
    color: #94a3b8;
    font-weight: 600;
    border: 1px solid rgba(148, 163, 184, 0.15);
    border-bottom: none;
}
.stTabs [aria-selected="true"] {
    background-color: #0284c7 !important;
    color: #ffffff !important;
}
</style>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# Carregamento de Dados
# ---------------------------------------------------------
init_db()
occurrences = read_occurrences()
actions = read_actions()

# ---------------------------------------------------------
# Barra Lateral - Filtros Corporativos
# ---------------------------------------------------------
with st.sidebar:
    st.markdown("### ⚙️ Painel de Controle")
    
    # 1. Granularidade Temporal
    granularity = st.radio(
        "Unidade de Tempo",
        options=["📅 Semanal (Data Início)", "🗓️ Mensal"],
        index=0,
        help="Semanal exibe a data exata DD/MM/AAAA de início de cada semana. Mensal agrupa por Mês/Ano com barras mais largas."
    )
    is_monthly = (granularity == "🗓️ Mensal")
    
    # 2. Janela Temporal (Recorte)
    if not is_monthly:
        time_window = st.selectbox(
            "Janela de Análise",
            options=["Últimas 8 semanas (Alta Nitidez)", "Últimas 12 semanas", "Últimas 16 semanas", "Últimas 4 semanas", "Todo o período histórico"],
            index=0,
            help="Reduzir para 8 ou 12 semanas aumenta a largura das barras do Gantt, facilitando a identificação imediata dos valores."
        )
    else:
        time_window = st.selectbox(
            "Janela de Análise",
            options=["Últimos 6 meses (Alta Nitidez)", "Últimos 12 meses", "Todo o período histórico"],
            index=0,
            help="Visão mensal com excelente espaçamento e leitura de valores."
        )

    st.markdown("---")
    
    # 3. Tipos de Ocorrência
    selected_types = st.multiselect(
        "Tipo de Ocorrência",
        options=["Dano", "Falta"],
        default=["Dano", "Falta"]
    )
    
    # 4. Modo de Exibição de Filiais
    branches_all = sorted(occurrences["filial"].unique())
    branch_mode = st.radio(
        "Filtrar Filiais",
        options=["Top 5 com mais ocorrências", "Top 10 com mais ocorrências", "Todas as Filiais", "Personalizada"],
        index=0,
        help="Focar nas Top 5 ou Top 10 filiais oferece a melhor visibilidade executiva sem poluição de dados."
    )
    
    if branch_mode == "Personalizada":
        selected_branches = st.multiselect("Selecione as Filiais", branches_all, default=branches_all[:5])
    elif branch_mode == "Top 5 com mais ocorrências":
        top_branches = (
            occurrences[occurrences["type"].isin(selected_types)]
            .groupby("filial")["quantity"].sum()
            .nlargest(5).index.tolist()
        )
        selected_branches = top_branches if top_branches else branches_all[:5]
    elif branch_mode == "Top 10 com mais ocorrências":
        top_branches = (
            occurrences[occurrences["type"].isin(selected_types)]
            .groupby("filial")["quantity"].sum()
            .nlargest(10).index.tolist()
        )
        selected_branches = top_branches if top_branches else branches_all[:10]
    else:
        selected_branches = branches_all

    st.markdown("---")
    with st.expander("➕ Cadastrar Nova Ação no PDCA", expanded=False):
        with st.form("form_nova_acao_sidebar", clear_on_submit=True):
            st.markdown("<small style='color:#94a3b8;'>Cadastre uma ação para acompanhar o impacto nas ocorrências da filial:</small>", unsafe_allow_html=True)
            form_filial = st.selectbox("Filial da Ação", branches_all)
            form_action = st.text_area("Descrição da Ação", placeholder="Ex.: Treinamento de conferência e auditoria de carga")
            form_date = st.date_input("Data de Início", value=datetime.date.today())
            form_status = st.selectbox("Status da Ação", ["Planejada", "Em andamento", "Concluída"], index=1)
            btn_save = st.form_submit_button("Salvar Ação no PDCA", use_container_width=True)
            if btn_save:
                if form_action.strip():
                    from data_store import save_action
                    save_action(form_filial, form_action, str(form_date), form_status)
                    st.success("✅ Ação salva com sucesso!")
                    st.rerun()
                else:
                    st.error("Preencha a descrição da ação.")

    st.info("💡 Você também pode cadastrar ações pelo portal web em Python rodando `python site.py`.")

# ---------------------------------------------------------
# Pré-processamento Temporal dos Dados
# ---------------------------------------------------------
df = occurrences[
    occurrences["filial"].isin(selected_branches) & 
    occurrences["type"].isin(selected_types)
].copy()

if is_monthly:
    # Agrupamento Mensal
    df["period_start"] = df["date"].dt.to_period("M").dt.start_time
    # Término do mês
    df["period_end"] = df["period_start"] + pd.offsets.MonthEnd(1) + pd.Timedelta(days=1)
    df["period_label"] = df["period_start"].dt.strftime("%m/%Y")
    df["period_header"] = df["period_start"].dt.strftime("%b/%Y").str.capitalize()
else:
    # Agrupamento Semanal (Início na Segunda-feira)
    df["period_start"] = df["date"].dt.to_period("W-MON").dt.start_time
    df["period_end"] = df["period_start"] + pd.Timedelta(days=7)
    # Exibe a data de início da semana em formato brasileiro DD/MM/AAAA
    df["period_label"] = df["period_start"].dt.strftime("%d/%m/%Y")
    df["period_header"] = df["period_start"].dt.strftime("%d/%m/%Y")

# Aplicar Janela de Tempo
all_periods = sorted(df["period_start"].unique())
if not df.empty and all_periods:
    if "4 semanas" in time_window:
        cutoff = all_periods[-4] if len(all_periods) >= 4 else all_periods[0]
        df = df[df["period_start"] >= cutoff]
    elif "8 semanas" in time_window:
        cutoff = all_periods[-8] if len(all_periods) >= 8 else all_periods[0]
        df = df[df["period_start"] >= cutoff]
    elif "12 semanas" in time_window:
        cutoff = all_periods[-12] if len(all_periods) >= 12 else all_periods[0]
        df = df[df["period_start"] >= cutoff]
    elif "16 semanas" in time_window:
        cutoff = all_periods[-16] if len(all_periods) >= 16 else all_periods[0]
        df = df[df["period_start"] >= cutoff]
    elif "6 meses" in time_window:
        cutoff = all_periods[-6] if len(all_periods) >= 6 else all_periods[0]
        df = df[df["period_start"] >= cutoff]
    elif "12 meses" in time_window:
        cutoff = all_periods[-12] if len(all_periods) >= 12 else all_periods[0]
        df = df[df["period_start"] >= cutoff]

# ---------------------------------------------------------
# Cabeçalho Principal do Dashboard
# ---------------------------------------------------------
st.markdown(f"""
<div class="corp-header">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 10px;">
        <div>
            <h1 class="corp-title">Diagrama de Gantt & Painel Executivo PDCA</h1>
            <p class="corp-subtitle">Acompanhamento de ocorrências (Dano e Falta) e impacto direto das ações de melhoria contínua por filial</p>
        </div>
        <div style="text-align: right;">
            <span style="background: rgba(2, 132, 199, 0.2); color: #38bdf8; border: 1px solid #0284c7; padding: 4px 10px; border-radius: 20px; font-size: 0.8rem; font-weight: 600;">
                Visão { "Mensal" if is_monthly else "Semanal com Data de Início" }
            </span>
            <div style="color: #64748b; font-size: 0.78rem; margin-top: 4px;">Recorte: {time_window}</div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------------------------
# KPIs Executivos
# ---------------------------------------------------------
total_qty = int(df["quantity"].sum()) if not df.empty else 0
falta_qty = int(df[df["type"] == "Falta"]["quantity"].sum()) if not df.empty else 0
dano_qty = int(df[df["type"] == "Dano"]["quantity"].sum()) if not df.empty else 0
action_count = len(actions) if not actions.empty else 0
active_actions = len(actions[actions["status"] == "Em andamento"]) if not actions.empty else 0

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Total de Ocorrências</div>
        <div class="kpi-value">{total_qty:,.0f}</div>
        <div class="kpi-sub">Filiais analisadas: <b>{len(selected_branches)}</b></div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

with kpi_col2:
    st.markdown(f"""
    <div class="kpi-container" style="border-top-color: #0284c7;">
        <div class="kpi-title">Faltas Registradas</div>
        <div class="kpi-value" style="color: #38bdf8;">{falta_qty:,.0f}</div>
        <div class="kpi-sub">{(falta_qty / total_qty * 100 if total_qty else 0):.1f}% do volume total</div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

with kpi_col3:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Danos Registrados</div>
        <div class="kpi-value" style="color: #fb923c;">{dano_qty:,.0f}</div>
        <div class="kpi-sub">{(dano_qty / total_qty * 100 if total_qty else 0):.1f}% do volume total</div>
    </div>
    """.replace(",", "."), unsafe_allow_html=True)

with kpi_col4:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Ações no Ciclo PDCA</div>
        <div class="kpi-value" style="color: #a78bfa;">{action_count}</div>
        <div class="kpi-sub"><b>{active_actions}</b> em andamento na rotina</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Preparação dos Dados para o Diagrama de Gantt Integrado
# ---------------------------------------------------------
if df.empty:
    st.warning("⚠️ Não foram encontradas ocorrências para os filtros e janela selecionados.")
else:
    # 1. Dados de Ocorrências Agrupados por Período
    gantt_occ = (
        df.groupby(["filial", "type", "period_start", "period_end", "period_label"], as_index=False)["quantity"]
        .sum()
    )
    gantt_occ["task"] = gantt_occ["filial"] + " · " + gantt_occ["type"]
    gantt_occ["category"] = gantt_occ["type"]
    gantt_occ["value_num"] = gantt_occ["quantity"]
    # Formatação limpa dos valores numéricos dentro das barras
    gantt_occ["label"] = gantt_occ["quantity"].map(lambda v: f"{v:,.0f}".replace(",", ".") if v > 0 else "")
    gantt_occ["action_details"] = ""

    # 2. Dados de Ações (PDCA) Integradas no Gantt
    action_rows = []
    if not actions.empty:
        # Filtrar ações pertencentes às filiais selecionadas
        rel_actions = actions[actions["filial"].isin(selected_branches)].copy()
        rel_actions["start_dt"] = pd.to_datetime(rel_actions["start_date"], errors="coerce")
        rel_actions = rel_actions.dropna(subset=["start_dt"])
        
        # Duração visual da barra de ação (14 dias para semanal, 30 dias para mensal)
        action_duration = pd.Timedelta(days=30 if is_monthly else 14)
        
        for _, act in rel_actions.iterrows():
            act_start = act["start_dt"]
            act_end = act_start + action_duration
            
            # Verificar se a ação está dentro da janela temporal selecionada
            min_period = df["period_start"].min()
            max_period = df["period_end"].max()
            if act_start <= max_period and act_end >= min_period:
                action_rows.append({
                    "filial": act["filial"],
                    "type": "Ação PDCA",
                    "period_start": act_start,
                    "period_end": act_end,
                    "period_label": act_start.strftime("%d/%m/%Y"),
                    "quantity": 0,
                    "value_num": 0,
                    "task": f"{act['filial']} · 🎯 AÇÃO: {act['action'][:40]}",
                    "category": f"Ação ({act['status']})",
                    "label": f"🎯 {act['status']}",
                    "action_details": f"<b>Ação:</b> {act['action']}<br><b>Status:</b> {act['status']}<br><b>Início:</b> {act_start.strftime('%d/%m/%Y')}"
                })

    gantt_combined = pd.concat([gantt_occ, pd.DataFrame(action_rows)], ignore_index=True) if action_rows else gantt_occ

    # Ordenação das Tarefas no Eixo Y (Agrupa Ocorrências e Ações por Filial)
    tasks_sorted = sorted(
        gantt_combined["task"].unique(),
        key=lambda x: (x.split(" · ")[0], 0 if "Falta" in x else (1 if "Dano" in x else 2))
    )

    # Cores Corporativas Oficiais
    color_map = {
        "Falta": "#0284c7",               # Azul Corporativo Escuro
        "Dano": "#f97316",                # Laranja Alerta
        "Ação (Planejada)": "#eab308",    # Âmbar Dourado
        "Ação (Em andamento)": "#8b5cf6", # Roxo Executivo / Destaque
        "Ação (Concluída)": "#10b981"     # Verde Esmeralda
    }

    # Períodos Únicos para o Eixo X
    unique_starts = sorted(df["period_start"].unique())
    if is_monthly:
        tick_labels = [d.strftime("%m/%Y") for d in unique_starts]
        axis_title = "Mês de Referência (Mês / Ano)"
    else:
        # Data de início da semana em formato brasileiro
        tick_labels = [d.strftime("%d/%m/%Y") for d in unique_starts]
        axis_title = "Data de Início da Semana (DD/MM/AAAA)"

    # ---------------------------------------------------------
    # Visualização em Abas: Gantt vs Matriz de Valores
    # ---------------------------------------------------------
    tab_gantt, tab_matrix, tab_impact = st.tabs([
        "📊 Diagrama de Gantt com Ações Destacadas",
        "📑 Matriz Executiva de Valores (Célula a Célula)",
        "🎯 Análise de Impacto PDCA (Antes vs Depois)"
    ])

    with tab_gantt:
        st.markdown(f"**Visualização Temporal das Ocorrências e Marcos de Ação ({len(selected_branches)} filiais no recorte)**")
        
        # Criação do Timeline Plotly
        fig = px.timeline(
            gantt_combined,
            x_start="period_start",
            x_end="period_end",
            y="task",
            color="category",
            text="label",
            color_discrete_map=color_map,
            category_orders={"task": tasks_sorted}
        )

        # Personalização dos Rótulos Internos e Contraste
        fig.update_traces(
            textposition="inside",
            insidetextanchor="middle",
            textfont=dict(size=11, color="#ffffff", family="Inter, Arial Black"),
            marker_line_color="rgba(255,255,255,0.25)",
            marker_line_width=1,
            opacity=0.95
        )

        # Formatação do Eixo X (Datas no Topo)
        fig.update_xaxes(
            title=dict(text=axis_title, font=dict(color="#cbd5e1", size=12)),
            tickmode="array",
            tickvals=unique_starts,
            ticktext=tick_labels,
            side="top",
            showgrid=True,
            gridcolor="#1e293b",
            gridwidth=1,
            tickfont=dict(size=10.5, color="#cbd5e1")
        )

        # Formatação do Eixo Y (Tarefas por Filial)
        fig.update_yaxes(
            autorange="reversed",
            title=dict(text="Filial & Tipo / Ação PDCA", font=dict(color="#cbd5e1", size=12)),
            showgrid=True,
            gridcolor="#1e293b",
            tickfont=dict(size=11, color="#f1f5f9"),
            ticksuffix="   "
        )

        # Altura dinâmica proporcional à quantidade de tarefas
        chart_height = max(520, 160 + len(tasks_sorted) * 36)
        
        fig.update_layout(
            height=chart_height,
            margin=dict(l=20, r=20, t=90, b=25),
            plot_bgcolor="#0b0f19",
            paper_bgcolor="#111827",
            font=dict(family="Inter, sans-serif", color="#f8fafc"),
            bargap=0.28,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.10,
                xanchor="center",
                x=0.5,
                title_text="",
                font=dict(size=11, color="#e2e8f0"),
                itemsizing="constant"
            )
        )

        # Tooltips customizados ricos
        for trace in fig.data:
            trace_name = trace.name
            if "Ação" in trace_name:
                trace.hovertemplate = (
                    "<b>%{y}</b><br>"
                    "<b>Período:</b> %{x|%d/%m/%Y}<br>"
                    "<b>Status:</b> " + trace_name + "<br>"
                    "<extra></extra>"
                )
            else:
                unit_label = "Mês" if is_monthly else "Semana com início em"
                trace.hovertemplate = (
                    "<b>%{y}</b><br>"
                    f"<b>{unit_label}:</b> %{{x|%d/%m/%Y}}<br>"
                    "<b>Quantidade:</b> %{text} unidades<br>"
                    "<extra></extra>"
                )

        st.plotly_chart(fig, use_container_width=True)
        st.caption("📌 *Dica Executiva:* As linhas com o ícone 🎯 representam as ações cadastradas no PDCA para aquela filial específica.")

    with tab_matrix:
        st.markdown("### 📑 Matriz Executiva de Ocorrências (Valores por Período)")
        st.markdown("Identificação rápida e sem esforço de qualquer valor exato por período e filial.")
        
        # Pivot table com ordenação correta das colunas temporais
        pivot_df = gantt_occ.pivot_table(
            index=["filial", "type"],
            columns="period_label",
            values="quantity",
            aggfunc="sum",
            fill_value=0
        )
        
        # Ordenar colunas pela ordem cronológica
        col_order = [d.strftime("%m/%Y" if is_monthly else "%d/%m/%Y") for d in unique_starts]
        existing_cols = [c for c in col_order if c in pivot_df.columns]
        pivot_df = pivot_df[existing_cols]

        # Adicionar coluna de Total
        pivot_df["Total Período"] = pivot_df.sum(axis=1)
        pivot_df = pivot_df.sort_values(by="Total Período", ascending=False)

        # Formatação para exibição amigável
        formatted_matrix = pivot_df.map(lambda v: f"{v:,.0f}".replace(",", ".")) if hasattr(pivot_df, "map") else pivot_df.applymap(lambda v: f"{v:,.0f}".replace(",", "."))
        
        st.dataframe(
            formatted_matrix,
            use_container_width=True,
            height=min(600, 100 + len(formatted_matrix) * 38)
        )
        
        # Download da Matriz em CSV
        csv_data = pivot_df.to_csv(sep=";", decimal=",").encode("utf-8-sig")
        st.download_button(
            label="📥 Exportar Matriz de Valores em CSV",
            data=csv_data,
            file_name=f"matriz_ocorrencias_{'mensal' if is_monthly else 'semanal'}.csv",
            mime="text/csv"
        )

    with tab_impact:
        st.markdown("### 🎯 Avaliação de Impacto das Ações no PDCA (Antes vs Depois)")
        st.markdown("Medição do impacto real que cada ação implementada gerou sobre o volume de Danos e Faltas.")
        
        if actions.empty:
            st.info("ℹ️ Nenhuma ação cadastrada no banco de dados. Cadastre ações no site (`http://localhost:5000`) para ver a comparação de impacto.")
        else:
            rel_actions = actions[actions["filial"].isin(selected_branches)].copy()
            if rel_actions.empty:
                st.info("ℹ️ Nenhuma ação registrada especificamente para as filiais selecionadas nos filtros.")
            else:
                rel_actions["start_dt"] = pd.to_datetime(rel_actions["start_date"], errors="coerce")
                
                impact_results = []
                for _, act in rel_actions.iterrows():
                    f_name = act["filial"]
                    act_date = act["start_dt"]
                    act_desc = act["action"]
                    act_status = act["status"]
                    
                    if pd.isna(act_date):
                        continue

                    # Filtrar dados históricos daquela filial específica
                    f_occ = occurrences[occurrences["filial"] == f_name].copy()
                    
                    # Janela de 4 semanas (28 dias) antes e depois
                    window_days = 28
                    before_data = f_occ[(f_occ["date"] >= act_date - pd.Timedelta(days=window_days)) & (f_occ["date"] < act_date)]
                    after_data = f_occ[(f_occ["date"] >= act_date) & (f_occ["date"] <= act_date + pd.Timedelta(days=window_days))]
                    
                    total_before = before_data["quantity"].sum()
                    total_after = after_data["quantity"].sum()
                    
                    falta_before = before_data[before_data["type"] == "Falta"]["quantity"].sum()
                    falta_after = after_data[after_data["type"] == "Falta"]["quantity"].sum()
                    
                    dano_before = before_data[before_data["type"] == "Dano"]["quantity"].sum()
                    dano_after = after_data[after_data["type"] == "Dano"]["quantity"].sum()
                    
                    if total_before > 0:
                        var_pct = ((total_after - total_before) / total_before) * 100
                        if var_pct < 0:
                            status_badge = f"🟢 Redução de {abs(var_pct):.1f}%"
                        elif var_pct == 0:
                            status_badge = "⚪ Estável"
                        else:
                            status_badge = f"🔴 Aumento de +{var_pct:.1f}%"
                    else:
                        var_pct = None
                        status_badge = "🟡 Em monitoramento inicial"
                        
                    impact_results.append({
                        "Filial": f_name,
                        "Ação PDCA": act_desc,
                        "Data Início": act_date.strftime("%d/%m/%Y"),
                        "Status": act_status,
                        "Falta (Antes / Depois)": f"{falta_before:,.0f} → {falta_after:,.0f}".replace(",", "."),
                        "Dano (Antes / Depois)": f"{dano_before:,.0f} → {dano_after:,.0f}".replace(",", "."),
                        "Total Antes": f"{total_before:,.0f}".replace(",", "."),
                        "Total Depois": f"{total_after:,.0f}".replace(",", "."),
                        "Resultado / Variação": status_badge
                    })
                
                if impact_results:
                    st.dataframe(pd.DataFrame(impact_results), use_container_width=True, hide_index=True)
                else:
                    st.write("Sem registros suficientes para calcular o impacto antes e depois.")

# ---------------------------------------------------------
# Check · Evolução Temporal com Marcadores de Ações
# ---------------------------------------------------------
st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
st.subheader("📈 Check · Evolução Temporal & Inflexão das Ações")

if not df.empty:
    trend = df.groupby(["period_start", "type"], as_index=False)["quantity"].sum()
    
    line_fig = px.line(
        trend,
        x="period_start",
        y="quantity",
        color="type",
        markers=True,
        color_discrete_map={"Falta": "#0284c7", "Dano": "#f97316"}
    )
    
    # Adicionar linhas verticais para marcar as ações implementadas
    if not actions.empty:
        rel_actions = actions[actions["filial"].isin(selected_branches)].copy()
        rel_actions["start_dt"] = pd.to_datetime(rel_actions["start_date"], errors="coerce")
        min_p = df["period_start"].min()
        max_p = df["period_start"].max()
        
        for _, act in rel_actions.dropna(subset=["start_dt"]).iterrows():
            act_dt = act["start_dt"]
            if min_p <= act_dt <= max_p + pd.Timedelta(days=7):
                line_fig.add_vline(
                    x=act_dt,
                    line_width=1.5,
                    line_dash="dash",
                    line_color="#a78bfa"
                )
                line_fig.add_annotation(
                    x=act_dt,
                    y=trend["quantity"].max() * 0.95,
                    text=f"🎯 {act['filial']}: {act['action'][:22]}...",
                    showarrow=True,
                    arrowhead=1,
                    arrowcolor="#a78bfa",
                    font=dict(size=10, color="#f1f5f9"),
                    bgcolor="#1e1b4b",
                    bordercolor="#8b5cf6",
                    borderwidth=1,
                    borderpad=3
                )

    line_fig.update_layout(
        height=380,
        margin=dict(l=20, r=20, t=25, b=25),
        plot_bgcolor="#0b0f19",
        paper_bgcolor="#111827",
        font=dict(family="Inter, sans-serif", color="#cbd5e1"),
        xaxis_title=axis_title,
        yaxis_title="Quantidade de Ocorrências",
        legend_title_text=""
    )
    line_fig.update_traces(line=dict(width=3))
    line_fig.update_xaxes(
        showgrid=True,
        gridcolor="#1e293b",
        tickformat="%m/%Y" if is_monthly else "%d/%m/%Y"
    )
    line_fig.update_yaxes(showgrid=True, gridcolor="#1e293b")
    
    st.plotly_chart(line_fig, use_container_width=True)

# ---------------------------------------------------------
# Tabela de Ações Cadastradas
# ---------------------------------------------------------
with st.expander("📋 Ver Tabela Completa de Ações Registradas"):
    if not actions.empty:
        st.dataframe(actions, use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma ação cadastrada até o momento.")
