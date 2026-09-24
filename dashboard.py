import datetime
from typing import Tuple
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_store import (
    DEFAULT_DURATION_DAYS,
    actions_mtime,
    init_db,
    read_actions,
    read_occurrences,
    save_action,
    source_mtime,
)

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
# Carregamento de Dados (cache por mtime: evita reler os ~21 MB de CSV a cada
# interação; o cache invalida-se sozinho quando os CSVs ou o actions.json mudam)
# ---------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_occurrences(mtime: float) -> pd.DataFrame:
    return read_occurrences()


@st.cache_data(show_spinner=False)
def load_actions(mtime: float) -> pd.DataFrame:
    return read_actions()


init_db()
occurrences = load_occurrences(source_mtime())
actions = load_actions(actions_mtime())

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
    
    # 4. Filial em Foco (uma por vez)
    branches_all = sorted(occurrences["filial"].unique())
    if not branches_all:
        st.error("Nenhuma filial encontrada nas bases de PPM Dano / NC Falta.")
        st.stop()

    ranking = (
        occurrences[occurrences["type"].isin(selected_types)]
        .groupby("filial")["quantity"].sum()
        .sort_values(ascending=False)
    )
    ranked_branches = [branch for branch in ranking.index.tolist() if branch in branches_all] or branches_all

    foco_filial = st.selectbox(
        "🎯 Filial em Foco (uma por vez)",
        options=ranked_branches,
        index=0,
        help="O diagrama exibe sempre uma filial por vez. As filiais aparecem ordenadas pelo volume de PPM Dano + NC Falta."
    )
    st.caption("Visão individual: PPM Dano × NC Falta × tratativas do período.")

    st.markdown("---")
    with st.expander("➕ Cadastrar Nova Tratativa no PDCA", expanded=False):
        with st.form("form_nova_tratativa_sidebar", clear_on_submit=True):
            st.markdown("<small style='color:#94a3b8;'>Cadastre a tratativa e o período para acompanhar o impacto no PPM Dano e no NC Falta da filial:</small>", unsafe_allow_html=True)
            form_filial = st.selectbox("Filial da Tratativa", branches_all)
            form_action = st.text_area("Descrição da Tratativa", placeholder="Ex.: Treinamento de conferência e auditoria de carga")
            form_start = st.date_input("Data de Início", value=datetime.date.today())
            form_end = st.date_input("Data Final", value=datetime.date.today() + datetime.timedelta(days=DEFAULT_DURATION_DAYS))
            form_status = st.selectbox("Status da Tratativa", ["Planejada", "Em andamento", "Concluída"], index=1)
            btn_save = st.form_submit_button("Salvar Tratativa no PDCA", use_container_width=True)
            if btn_save:
                if not form_action.strip():
                    st.error("Preencha a descrição da tratativa.")
                elif form_end < form_start:
                    st.error("A data final precisa ser igual ou posterior à data de início.")
                else:
                    save_action(form_filial, form_action, str(form_start), str(form_end), form_status)
                    st.success("✅ Tratativa salva com sucesso!")
                    st.rerun()

    st.info("💡 As tratativas também podem ser cadastradas pelo portal web em `node site.js` (http://localhost:5000). É o `site.js` que alimenta esta lista.")


# ---------------------------------------------------------
# Pré-processamento Temporal dos Dados (filial em foco)
# ---------------------------------------------------------
df = occurrences[
    (occurrences["filial"] == foco_filial) &
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
            <h1 class="corp-title">Impacto das Tratativas no PPM Dano & NC Falta</h1>
            <p class="corp-subtitle">Filial em foco: <b style="color:#38bdf8;">{foco_filial}</b> · Diagrama de Gantt do PDCA com o período real de cada tratativa (início → término)</p>
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

# Tratativas registradas para a filial em foco (alimentadas pelo site.js / actions.json)
filial_actions = actions[actions["filial"] == foco_filial].copy() if not actions.empty else actions.copy()
active_actions = len(actions[actions["status"] == "Em andamento"]) if not actions.empty else 0

# ---------------------------------------------------------
# Janela de referência do impacto (tratativa mais antiga da filial)
# ---------------------------------------------------------
IMPACT_WINDOW_DAYS = 28
impact_ref_date = None
if not filial_actions.empty:
    impact_dates = pd.to_datetime(filial_actions["start_date"], errors="coerce").dropna()
    if not impact_dates.empty:
        impact_ref_date = impact_dates.min()

dano_before = falta_before = dano_after = falta_after = 0
if impact_ref_date is not None:
    filial_history = occurrences[occurrences["filial"] == foco_filial]
    before_slice = filial_history[
        (filial_history["date"] >= impact_ref_date - pd.Timedelta(days=IMPACT_WINDOW_DAYS)) &
        (filial_history["date"] < impact_ref_date)
    ]
    after_slice = filial_history[
        (filial_history["date"] >= impact_ref_date) &
        (filial_history["date"] <= impact_ref_date + pd.Timedelta(days=IMPACT_WINDOW_DAYS))
    ]
    dano_before = int(before_slice[before_slice["type"] == "Dano"]["quantity"].sum())
    falta_before = int(before_slice[before_slice["type"] == "Falta"]["quantity"].sum())
    dano_after = int(after_slice[after_slice["type"] == "Dano"]["quantity"].sum())
    falta_after = int(after_slice[after_slice["type"] == "Falta"]["quantity"].sum())


def format_variation(before: float, after: float) -> Tuple[str, str]:
    """Compara o volume antes e depois das tratativas e devolve (texto, cor)."""
    if before <= 0:
        return "Sem base de comparação no período anterior", "#94a3b8"
    variation = ((after - before) / before) * 100
    if variation < -0.5:
        return f"▼ {abs(variation):.1f}% de redução no período", "#34d399"
    if variation > 0.5:
        return f"▲ +{variation:.1f}% de aumento no período", "#f87171"
    return "● Estável no período", "#94a3b8"


def fmt_int(value: float) -> str:
    """Formata inteiros com ponto de milhar sem tocar no restante HTML."""
    return f"{value:,.0f}".replace(",", ".")


dano_delta_text, dano_delta_color = format_variation(dano_before, dano_after)
falta_delta_text, falta_delta_color = format_variation(falta_before, falta_after)
dano_numbers = f"{dano_before:,.0f} → {dano_after:,.0f}".replace(",", ".")
falta_numbers = f"{falta_before:,.0f} → {falta_after:,.0f}".replace(",", ".")

kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)

with kpi_col1:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Total de Ocorrências</div>
        <div class="kpi-value">{fmt_int(total_qty)}</div>
        <div class="kpi-sub">Filial em foco: <b>{foco_filial}</b></div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col2:
    st.markdown(f"""
    <div class="kpi-container" style="border-top-color: #0284c7;">
        <div class="kpi-title">NC Falta Registrado</div>
        <div class="kpi-value" style="color: #38bdf8;">{fmt_int(falta_qty)}</div>
        <div class="kpi-sub">{(falta_qty / total_qty * 100 if total_qty else 0):.1f}% do volume da filial</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col3:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">PPM Dano Registrado</div>
        <div class="kpi-value" style="color: #fb923c;">{fmt_int(dano_qty)}</div>
        <div class="kpi-sub">{(dano_qty / total_qty * 100 if total_qty else 0):.1f}% do volume da filial</div>
    </div>
    """, unsafe_allow_html=True)

with kpi_col4:
    st.markdown(f"""
    <div class="kpi-container">
        <div class="kpi-title">Tratativas no Ciclo PDCA</div>
        <div class="kpi-value" style="color: #a78bfa;">{len(filial_actions)}</div>
        <div class="kpi-sub"><b>{active_actions}</b> em andamento no total do ciclo</div>
    </div>
    """, unsafe_allow_html=True)

# ---------------------------------------------------------
# Impacto das Tratativas no PPM Dano e no NC Falta
# ---------------------------------------------------------
st.markdown("<div style='height: 1rem;'></div>", unsafe_allow_html=True)
impact_col1, impact_col2 = st.columns(2)

with impact_col1:
    st.markdown(f"""
    <div class="kpi-container" style="border-top-color: #f97316;">
        <div class="kpi-title">PPM Dano · {IMPACT_WINDOW_DAYS} dias antes → depois</div>
        <div class="kpi-value" style="color: #fb923c; font-size: 1.8rem;">{dano_numbers}</div>
        <div class="kpi-sub" style="color: {dano_delta_color}; font-weight: 600;">{dano_delta_text}</div>
    </div>
    """, unsafe_allow_html=True)

with impact_col2:
    st.markdown(f"""
    <div class="kpi-container" style="border-top-color: #0284c7;">
        <div class="kpi-title">NC Falta · {IMPACT_WINDOW_DAYS} dias antes → depois</div>
        <div class="kpi-value" style="color: #38bdf8; font-size: 1.8rem;">{falta_numbers}</div>
        <div class="kpi-sub" style="color: {falta_delta_color}; font-weight: 600;">{falta_delta_text}</div>
    </div>
    """, unsafe_allow_html=True)

if impact_ref_date is None:
    st.caption("ℹ️ Cadastre a primeira tratativa da filial (portal `node site.js` ou barra lateral) para liberar a leitura de antes × depois.")
else:
    st.caption(
        f"📌 Referência: tratativa mais antiga da filial em {impact_ref_date.strftime('%d/%m/%Y')} · "
        f"janelas de {IMPACT_WINDOW_DAYS} dias antes e depois dessa data."
    )

st.markdown("<div style='height: 1.2rem;'></div>", unsafe_allow_html=True)

# ---------------------------------------------------------
# Preparação dos Dados para o Diagrama de Gantt (Filial em Foco)
# ---------------------------------------------------------
if df.empty:
    st.warning("⚠️ Não foram encontradas ocorrências para a filial em foco e a janela selecionadas.")
else:
    # 1. Ocorrências agrupadas por período -> linhas "PPM Dano" e "NC Falta"
    gantt_occ = (
        df.groupby(["type", "period_start", "period_end", "period_label"], as_index=False)["quantity"]
        .sum()
    )
    unique_starts = sorted(pd.to_datetime(gantt_occ["period_start"].dropna().unique()))
    gantt_occ["filial"] = foco_filial
    gantt_occ["task"] = gantt_occ["type"].map({"Dano": "PPM Dano", "Falta": "NC Falta"}).fillna(gantt_occ["type"])
    gantt_occ["category"] = gantt_occ["task"]
    # Valores formatados para exibição dentro das barras
    gantt_occ["label"] = gantt_occ["quantity"].map(lambda v: f"{v:,.0f}".replace(",", ".") if v > 0 else "")
    gantt_occ["seg_start"] = gantt_occ["period_start"]
    gantt_occ["seg_end"] = gantt_occ["period_end"]
    # Data exibida acima de cada barra (mesmo padrão da referência visual)
    gantt_occ["date_label"] = gantt_occ["period_label"]
    gantt_occ["hover"] = gantt_occ.apply(
        lambda row: (
            f"<b>{row['task']}</b><br>"
            f"<b>Período:</b> {row['seg_start']:%d/%m/%Y} → {row['seg_end']:%d/%m/%Y}<br>"
            f"<b>Quantidade:</b> {row['label'] or 0} unidades<extra></extra>"
        ),
        axis=1
    )

    # 2. Tratativas (PDCA) da filial: barra dupla (concluído x restante) + marcos
    today = pd.Timestamp.today().normalize()
    default_duration = pd.Timedelta(days=30 if is_monthly else DEFAULT_DURATION_DAYS)
    segments = gantt_occ[["task", "category", "seg_start", "seg_end", "label", "hover"]].copy()
    milestones = []
    task_order = [task for task in ["NC Falta", "PPM Dano"] if task in set(gantt_occ["task"])]

    if not filial_actions.empty:
        filial_actions["start_dt"] = pd.to_datetime(filial_actions["start_date"], errors="coerce")
        if "end_date" in filial_actions.columns:
            filial_actions["end_dt"] = pd.to_datetime(filial_actions["end_date"], errors="coerce")
        else:
            filial_actions["end_dt"] = pd.NaT
        filial_actions = filial_actions.dropna(subset=["start_dt"]).sort_values("start_dt")

        used_names = {}
        action_tasks = []
        for _, act in filial_actions.iterrows():
            act_start = act["start_dt"]
            act_end = act["end_dt"]
            if pd.isna(act_end) or act_end <= act_start:
                act_end = act_start + default_duration

            base_name = f"🎯 {str(act['action']).strip()[:26]}"
            used_names[base_name] = used_names.get(base_name, 0) + 1
            task_name = base_name if used_names[base_name] == 1 else f"{base_name} ({used_names[base_name]})"

            concluded_end = min(max(today, act_start), act_end)
            if act["status"] == "Concluída":
                concluded_end = act_end

            hover_txt = (
                f"<b>{task_name}</b><br><b>Tratativa:</b> {act['action']}<br>"
                f"<b>Período:</b> {act_start:%d/%m/%Y} → {act_end:%d/%m/%Y}<br>"
                f"<b>Status:</b> {act['status']}<extra></extra>"
            )

            if concluded_end > act_start:
                segments.loc[len(segments)] = {
                    "task": task_name, "category": "Concluído",
                    "seg_start": act_start, "seg_end": concluded_end,
                    "label": "", "hover": hover_txt,
                }
            if act_end > concluded_end:
                segments.loc[len(segments)] = {
                    "task": task_name, "category": "Restante",
                    "seg_start": max(concluded_end, act_start), "seg_end": act_end,
                    "label": "", "hover": hover_txt,
                }

            # Marcos (milestones) de início e término da tratativa
            milestones.append({"task": task_name, "x": act_start, "text": "▶", "hover": f"<b>Início da tratativa</b><br>{act_start:%d/%m/%Y}<extra></extra>"})
            milestones.append({"task": task_name, "x": act_end, "text": "🏁", "hover": f"<b>Término da tratativa</b><br>{act_end:%d/%m/%Y}<extra></extra>"})
            action_tasks.append(task_name)

        # Linha-resumo do ciclo completo (todas as tratativas da filial)
        if action_tasks:
            action_segments = segments[segments["task"].isin(action_tasks)]
            ciclo_start = action_segments["seg_start"].min()
            ciclo_end = action_segments["seg_end"].max()
            ciclo_done_end = min(max(today, ciclo_start), ciclo_end)
            ciclo_name = "🧩 Ciclo PDCA (todas as tratativas)"
            ciclo_hover = (
                f"<b>{ciclo_name}</b><br><b>Fase:</b> Ação (Do)<br>"
                f"<b>Período total:</b> {ciclo_start:%d/%m/%Y} → {ciclo_end:%d/%m/%Y}<extra></extra>"
            )
            if ciclo_done_end > ciclo_start:
                segments.loc[len(segments)] = {
                    "task": ciclo_name, "category": "Concluído",
                    "seg_start": ciclo_start, "seg_end": ciclo_done_end,
                    "label": "", "hover": ciclo_hover,
                }
            if ciclo_end > ciclo_done_end:
                segments.loc[len(segments)] = {
                    "task": ciclo_name, "category": "Restante",
                    "seg_start": max(ciclo_done_end, ciclo_start), "seg_end": ciclo_end,
                    "label": "", "hover": ciclo_hover,
                }
            milestones.append({"task": ciclo_name, "x": ciclo_start, "text": "▶", "hover": f"<b>Início do ciclo PDCA</b><br>{ciclo_start:%d/%m/%Y}<extra></extra>"})
            milestones.append({"task": ciclo_name, "x": ciclo_end, "text": "🏁", "hover": f"<b>Término do ciclo PDCA</b><br>{ciclo_end:%d/%m/%Y}<extra></extra>"})
            task_order = [ciclo_name] + task_order + action_tasks

    milestone_df = pd.DataFrame(milestones) if milestones else pd.DataFrame(columns=["task", "x", "text", "hover"])

    # Cores: indicadores da filial + barra dupla das tratativas (concluído x restante)
    color_map = {
        "NC Falta": "#0284c7",     # Azul corporativo
        "PPM Dano": "#f97316",     # Laranja alerta
        "Concluído": "#1e3a8a",    # Azul profundo (período já executado)
        "Restante": "#93c5fd",     # Azul claro (período ainda a executar)
    }

    # Eixo X CATEGÓRICO (sem vazio): cada período vira uma coluna discreta.
    # Motivo: as ocorrências (ex.: 2025) e as tratativas (ex.: 2026) ficam em
    # épocas distintas; um eixo de data contínuo cria um "deserto" no meio e
    # esmaga as barras. Com categorias, só existem as colunas com dados.
    # Ordem cronológica das colunas de ocorrência (não lexical).
    occ_order = (
        gantt_occ[["period_label", "seg_start"]]
        .drop_duplicates()
        .sort_values("seg_start")
    )
    occ_periods = occ_order["period_label"].tolist()
    # Rótulos das tratativas (início E fim) no mesmo idioma do eixo
    seg_starts = pd.to_datetime(segments["seg_start"])
    seg_ends = pd.to_datetime(segments["seg_end"])
    fmt = "%m/%Y" if is_monthly else "%d/%m/%Y"
    act_labels = sorted(
        set(seg_starts.dt.strftime(fmt).tolist()) | set(seg_ends.dt.strftime(fmt).tolist())
    )
    categories = occ_periods + [lbl for lbl in act_labels if lbl not in occ_periods]
    if is_monthly:
        axis_title = "Mês de Referência (Mês / Ano)"
    else:
        axis_title = "Período (DD/MM/AAAA de início)"
    pos_of = {label: idx for idx, label in enumerate(categories)}
    # Posição de cada segmento no eixo categórico (centro da coluna = pos).
    # Largura proporcional à duração: ocorrências = 0.9 coluna;
    # tratativas = nº de colunas atravessadas (mín. 0.9).
    avg_days = 30.4 if is_monthly else 7.0
    segments = segments.reset_index(drop=True)
    seg_starts = pd.to_datetime(segments["seg_start"])
    seg_ends = pd.to_datetime(segments["seg_end"])
    segments["pos_label"] = seg_starts.dt.strftime(fmt)
    segments["x_pos"] = segments["pos_label"].map(pos_of).fillna(0).astype(float)
    durations = ((seg_ends - seg_starts).dt.total_seconds() / 86400.0 / avg_days).fillna(0)
    segments["x_width"] = 0.9
    occ_mask = segments["category"].isin(["NC Falta", "PPM Dano"]).to_numpy()
    widths = (durations.to_numpy() + 1.0).clip(min=0.9, max=6.0)
    segments.loc[~occ_mask, "x_width"] = widths[~occ_mask]
    milestone_df = milestone_df.copy() if not milestone_df.empty else milestone_df
    if not milestone_df.empty:
        milestone_df["pos_label"] = pd.to_datetime(milestone_df["x"]).dt.strftime(fmt)
        milestone_df["x_pos"] = milestone_df["pos_label"].map(pos_of).fillna(0).astype(float)

    # ---------------------------------------------------------
    # Visualização em Abas: Gantt vs Matriz de Valores
    # ---------------------------------------------------------
    tab_gantt, tab_matrix, tab_impact = st.tabs([
        "📊 Gantt do PPM Dano × NC Falta × Tratativas",
        "📑 Matriz Executiva de Valores (Célula a Célula)",
        "🎯 Impacto das Tratativas (Antes × Depois)"
    ])

    with tab_gantt:
        st.markdown(f"**{foco_filial} · PPM Dano × NC Falta × tratativas do PDCA (barra escura = período executado, barra clara = período restante)**")

        # Barras do Gantt em EIXO CATEGÓRICO (cada período = 1 coluna).
        # x = largura da barra, base = início da coluna. Sem "deserto" temporal.
        total_rows = len(task_order)
        row_of = {task: total_rows - 1 - position for position, task in enumerate(task_order)}

        def _wrap_label(name: str, width: int = 22) -> str:
            words, lines, current = str(name).split(), [], ""
            for word in words:
                candidate = f"{current} {word}".strip()
                if len(candidate) > width and current:
                    lines.append(current)
                    current = word
                else:
                    current = candidate
            if current:
                lines.append(current)
            return "<br>".join(lines)

        wrapped_labels = [_wrap_label(task) for task in task_order]

        fig = go.Figure()
        for category, color in color_map.items():
            subset = segments[segments["category"] == category]
            if subset.empty:
                continue
            fig.add_trace(go.Bar(
                x=subset["x_width"],
                base=subset["x_pos"] - subset["x_width"] / 2,
                y=subset["task"].map(lambda name: row_of.get(name, 0)),
                orientation="h",
                name=category,
                marker=dict(color=color, line=dict(color="rgba(255,255,255,0.25)", width=1)),
                opacity=0.95,
                text=subset["label"],
                textposition="inside",
                insidetextanchor="middle",
                textfont=dict(size=11, color="#ffffff"),
                customdata=subset["hover"],
                hovertemplate="%{customdata}"
            ))

        # Datas exibidas acima de cada barra de ocorrência (padrão da referência visual)
        # Desativado o rótulo duplicado sobre a barra: o eixo X do topo já exibe
        # as datas, evitando sobreposição com os ticks.
        occ_labels = []

        # Marcos (milestones) de início e término das tratativas
        if not milestone_df.empty:
            fig.add_trace(go.Scatter(
                x=milestone_df["x_pos"],
                y=milestone_df["task"].map(lambda name: row_of.get(name, 0)),
                mode="markers+text",
                marker=dict(symbol="diamond", size=9, color="#facc15", line=dict(color="#0b0f19", width=1)),
                text=milestone_df["text"],
                textposition="top center",
                textfont=dict(size=8, color="#facc15"),
                name="📌 Marcos de início/término",
                customdata=milestone_df["hover"],
                hovertemplate="%{customdata}"
            ))

        # Formatação do Eixo X CATEGÓRICO (sem vazio, sem sobreposição)
        # Cada coluna = 1 período com dados; tratativas entram como colunas extras.
        max_labels = 14
        cat_step = -(-len(categories) // max_labels) if categories else 1
        visible_vals = list(range(0, len(categories), cat_step))
        visible_text = [categories[i] for i in visible_vals]
        fig.update_xaxes(
            title=dict(text=axis_title, font=dict(color="#cbd5e1", size=12)),
            type="category",
            categoryorder="array",
            categoryarray=list(range(len(categories))),
            tickmode="array",
            tickvals=visible_vals,
            ticktext=visible_text,
            tickangle=45,
            side="top",
            showgrid=True,
            gridcolor="#1e293b",
            gridwidth=1,
            tickfont=dict(size=10.5, color="#cbd5e1")
        )

        # Formatação do Eixo Y (linha de cima = Ciclo PDCA, seguida de indicadores e tratativas)
        fig.update_yaxes(
            tickmode="array",
            tickvals=[row_of[task] for task in task_order],
            ticktext=wrapped_labels,
            range=[-0.6, total_rows - 0.4],
            automargin=False,
            title=dict(text="Indicador / Tratativa", font=dict(color="#cbd5e1", size=12)),
            showgrid=True,
            gridcolor="#1e293b",
            tickfont=dict(size=11, color="#f1f5f9")
        )

        # Altura dinâmica proporcional à quantidade de linhas exibidas
        chart_height = max(560, 190 + len(task_order) * 52)

        fig.update_layout(
            height=chart_height,
            margin=dict(l=210, r=25, t=170, b=30),
            plot_bgcolor="#0b0f19",
            paper_bgcolor="#111827",
            font=dict(family="Inter, sans-serif", color="#f8fafc"),
            bargap=0.28,
            bargroupgap=0.05,
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

        # Tooltips customizados: cada segmento carrega o seu próprio texto de detalhe
        for trace in fig.data:
            if trace.type == "bar":
                trace.hovertemplate = "%{customdata}"
            elif trace.name == "📌 Marcos do período":
                trace.hovertemplate = "%{customdata}"
            else:
                trace.hovertemplate = "%{text}<extra></extra>"

        st.plotly_chart(fig, use_container_width=True)
        st.caption(
            "📌 *Leitura do gráfico:* cada tratativa aparece com o período real (início → término), "
            "dividida em **período executado** (azul escuro) e **período restante** (azul claro). "
            "Os losangos 🟡 marcam o início e o término de cada tratativa."
        )
        if segments.empty:
            st.info("Sem dados para exibir no período selecionado.")

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
        st.markdown(f"### 🎯 Impacto das Tratativas no PPM Dano e no NC Falta · {foco_filial}")
        st.markdown("Cada tratativa é comparada com a janela imediatamente anterior de mesmo tamanho (mínimo de 14 dias).")

        if filial_actions.empty:
            st.info("ℹ️ Nenhuma tratativa cadastrada para a filial em foco. Registre as ações no portal web (`node site.js` → http://localhost:5000) ou pela barra lateral do painel.")
        else:
            impact_actions = filial_actions.copy()
            impact_actions["start_dt"] = pd.to_datetime(impact_actions["start_date"], errors="coerce")
            impact_actions["end_dt"] = pd.to_datetime(impact_actions["end_date"], errors="coerce")
            impact_actions = impact_actions.dropna(subset=["start_dt"]).sort_values("start_dt")

            filial_history = occurrences[occurrences["filial"] == foco_filial]

            def badge(before_value: float, after_value: float) -> str:
                if before_value <= 0:
                    return "🟡 Em monitoramento inicial"
                delta = ((after_value - before_value) / before_value) * 100
                if delta < -0.5:
                    return f"🟢 Redução de {abs(delta):.1f}%"
                if delta > 0.5:
                    return f"🔴 Aumento de +{delta:.1f}%"
                return "⚪ Estável"

            impact_results = []
            for _, act in impact_actions.iterrows():
                act_date = act["start_dt"]
                act_end = act["end_dt"] if pd.notna(act["end_dt"]) and act["end_dt"] > act_date else act_date + pd.Timedelta(days=DEFAULT_DURATION_DAYS)
                janela = max((act_end - act_date).days, DEFAULT_DURATION_DAYS)

                before_data = filial_history[
                    (filial_history["date"] >= act_date - pd.Timedelta(days=janela)) &
                    (filial_history["date"] < act_date)
                ]
                after_data = filial_history[
                    (filial_history["date"] >= act_date) &
                    (filial_history["date"] <= act_end)
                ]

                falta_before = int(before_data[before_data["type"] == "Falta"]["quantity"].sum())
                falta_after = int(after_data[after_data["type"] == "Falta"]["quantity"].sum())
                dano_before = int(before_data[before_data["type"] == "Dano"]["quantity"].sum())
                dano_after = int(after_data[after_data["type"] == "Dano"]["quantity"].sum())

                impact_results.append({
                    "Tratativa PDCA": act["action"],
                    "Início": act_date.strftime("%d/%m/%Y"),
                    "Término": act_end.strftime("%d/%m/%Y"),
                    "Status": act["status"],
                    "PPM Dano (Antes)": dano_before,
                    "PPM Dano (Depois)": dano_after,
                    "Impacto Dano": badge(dano_before, dano_after),
                    "NC Falta (Antes)": falta_before,
                    "NC Falta (Depois)": falta_after,
                    "Impacto Falta": badge(falta_before, falta_after),
                })

            if impact_results:
                st.dataframe(pd.DataFrame(impact_results), use_container_width=True, hide_index=True)

                res_col1, res_col2 = st.columns(2)
                with res_col1:
                    st.markdown(f"""
                    <div class="kpi-container" style="border-top-color: #f97316;">
                        <div class="kpi-title">PPM Dano · consolidado da filial</div>
                        <div class="kpi-value" style="color:#fb923c; font-size:1.8rem;">{dano_numbers}</div>
                        <div class="kpi-sub" style="color:{dano_delta_color}; font-weight:600;">{dano_delta_text}</div>
                    </div>
                    """, unsafe_allow_html=True)
                with res_col2:
                    st.markdown(f"""
                    <div class="kpi-container" style="border-top-color: #0284c7;">
                        <div class="kpi-title">NC Falta · consolidado da filial</div>
                        <div class="kpi-value" style="color:#38bdf8; font-size:1.8rem;">{falta_numbers}</div>
                        <div class="kpi-sub" style="color:{falta_delta_color}; font-weight:600;">{falta_delta_text}</div>
                    </div>
                    """, unsafe_allow_html=True)

                st.caption(
                    f"Consolidado calculado com janelas de {IMPACT_WINDOW_DAYS} dias antes e depois da tratativa mais antiga da filial."
                )
            else:
                st.write("Sem registros suficientes para calcular o impacto antes e depois.")

# ---------------------------------------------------------
# Check · Evolução Temporal com o Período das Tratativas
# ---------------------------------------------------------
st.markdown("<div style='height: 1.5rem;'></div>", unsafe_allow_html=True)
st.subheader(f"📈 Check · Evolução do PPM Dano & NC Falta · {foco_filial}")

if not df.empty:
    trend = df.groupby(["period_start", "type"], as_index=False)["quantity"].sum()
    trend["indicador"] = trend["type"].map({"Dano": "PPM Dano", "Falta": "NC Falta"}).fillna(trend["type"])

    line_fig = px.line(
        trend,
        x="period_start",
        y="quantity",
        color="indicador",
        markers=True,
        color_discrete_map={"NC Falta": "#0284c7", "PPM Dano": "#f97316"}
    )

    # Faixa do período de cada tratativa + marco de início
    if not filial_actions.empty:
        rel_actions = filial_actions.copy()
        rel_actions["start_dt"] = pd.to_datetime(rel_actions["start_date"], errors="coerce")
        rel_actions["end_dt"] = pd.to_datetime(rel_actions["end_date"], errors="coerce")
        min_p = df["period_start"].min()
        max_p = df["period_start"].max()
        y_top = trend["quantity"].max()

        for _, act in rel_actions.dropna(subset=["start_dt"]).iterrows():
            act_dt = act["start_dt"]
            act_end_dt = act["end_dt"] if pd.notna(act["end_dt"]) and act["end_dt"] > act_dt else act_dt + pd.Timedelta(days=DEFAULT_DURATION_DAYS)
            if act_dt <= max_p + pd.Timedelta(days=7) and act_end_dt >= min_p - pd.Timedelta(days=7):
                line_fig.add_vrect(
                    x0=act_dt,
                    x1=act_end_dt,
                    fillcolor="#8b5cf6",
                    opacity=0.12,
                    line_width=0,
                    layer="below"
                )
                line_fig.add_vline(x=act_dt, line_width=1.4, line_dash="dash", line_color="#a78bfa")
                line_fig.add_annotation(
                    x=act_dt,
                    y=y_top * 0.95,
                    text=f"🎯 {act['action'][:26]}",
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
        yaxis_title="Quantidade de Itens (PPM Dano / NC Falta)",
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
    st.caption("A faixa lilás indica o período (início → término) de cada tratativa cadastrada pelo `site.js`.")

# ---------------------------------------------------------
# Tabela de Tratativas Cadastradas
# ---------------------------------------------------------
with st.expander("📋 Ver Tabela Completa de Tratativas Registradas"):
    if not actions.empty:
        tabela_acoes = actions.copy()
        tabela_acoes = tabela_acoes.rename(columns={
            "filial": "Filial",
            "action": "Tratativa",
            "start_date": "Início",
            "end_date": "Término",
            "status": "Status",
        })
        colunas = [c for c in ["Filial", "Tratativa", "Início", "Término", "Status"] if c in tabela_acoes.columns]
        st.dataframe(tabela_acoes[colunas], use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma tratativa cadastrada até o momento.")
