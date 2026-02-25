"""
=========================================================
SISTEMA DE ANÁLISIS BIM – TRAMO 1 | Metro 80, Medellín
=========================================================
Dashboard principal — Streamlit + Plotly
Ejecutar con:  streamlit run dashboard.py
=========================================================
"""

import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from build_maestro import construir_dataframe_maestro, FACTOR_DEMOLICION

# ─────────────────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Sistema de Análisis BIM – Tramo 1",
    page_icon="🏗️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ─────────────────────────────────────────────────────────
# ESTILOS GLOBALES — paleta azul unificada
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    .main { background-color: #f0f2f6; }

    /* ── Tarjetas KPI — mismo tamaño en todas las pestañas ── */
    .kpi-card, .kpi-card-alt, .kpi-card-muted {
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        margin-bottom: 8px;
    }
    .kpi-card       { background:#ffffff; border-left: 5px solid #1a56db; }
    .kpi-card-alt   { background:#eef4ff; border-left: 5px solid #1a56db; }
    .kpi-card-muted { background:#f1f5f9; border-left: 5px solid #64748b; }

    .kpi-label {
        font-size: 13px;
        color: #6b7280;
        font-weight: 500;
        margin-bottom: 4px;
    }
    /* Un único tamaño de valor para TODOS los KPIs en todas las pestañas */
    .kpi-value {
        font-size: 22px;
        font-weight: 700;
        color: #111827;
        line-height: 1.3;
    }

    /* ── Cabecera principal ── */
    .header-box {
        background: linear-gradient(135deg, #1e3a5f 0%, #1a56db 100%);
        border-radius: 10px;
        padding: 24px 32px;
        color: white;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 32px;
        font-weight: 900;
        margin: 0;
        letter-spacing: -0.5px;
        line-height: 1.2;
    }
    .header-subtitle {
        font-size: 14px;
        opacity: 0.85;
        margin: 8px 0 0 0;
    }

    /* ── Encabezados de sección ── */
    .seccion-titulo {
        font-size: 16px;
        font-weight: 700;
        color: #1e3a5f;
        padding: 8px 0 4px 0;
        border-bottom: 2px solid #1a56db;
        margin-bottom: 12px;
    }

    /* ── Slider: forzar azul via variable CSS primaria de Streamlit ── */
    :root {
        --primary-color: #1a56db !important;
    }
    [data-testid="stSlider"] [role="slider"] {
        background-color: #1a56db !important;
        border-color:     #1a56db !important;
    }
    [data-testid="stSlider"] [data-baseweb="slider"] > div > div:first-child > div {
        background-color: #1a56db !important;
    }
    [data-testid="stSlider"] p,
    [data-testid="stSlider"] label {
        color: #1e3a5f !important;
    }

    /* ── Radio buttons: azul ── */
    [data-testid="stRadio"] [data-baseweb="radio"] div:first-child {
        border-color: #1a56db !important;
        background-color: #1a56db !important;
    }
    [data-testid="stRadio"] label:has(input:checked) [data-baseweb="radio"] div:first-child {
        background-color: #1a56db !important;
        border-color: #1a56db !important;
    }
    [data-baseweb="tag"] {
        background-color: #1a56db !important;
        border-color: #1a56db !important;
        color: white !important;
    }
    [data-baseweb="tag"] span { color: white !important; }

    /* ── Alertas de calidad ── */
    .badge-critico { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-medio   { background:#fef9c3; color:#854d0e; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-ok      { background:#dcfce7; color:#166534; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }

    /* ── Pestañas de navegación: negrita y tamaño correcto ── */
    button[data-baseweb="tab"] p {
        font-size: 18px !important;
        font-weight: 700 !important;
        letter-spacing: -0.2px;
    }
    button[data-baseweb="tab"][aria-selected="true"] p {
        color: #1a56db !important;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# CARGA DE DATOS (cacheada)
# ─────────────────────────────────────────────────────────
@st.cache_data(show_spinner="Cargando y procesando datos BIM...")
def cargar_df_maestro():
    base = os.path.dirname(os.path.abspath(__file__))
    rutas = {
        "conduits_inicial" : os.path.join(base, "Tramo1_Conduits_EstadoInicial.xlsx"),
        "conduits_final"   : os.path.join(base, "Tramo1_Conduits_EstadoFinal.xlsx"),
        "fittings_inicial" : os.path.join(base, "Tramo1_Fittings_EstadoInicial.xlsx"),
        "fittings_final"   : os.path.join(base, "Tramo1_Fittings_EstadoFinal.xlsx"),
        "fixtures_inicial" : os.path.join(base, "Tramo1_Fixtures_EstadoInicial.xlsx"),
        "fixtures_final"   : os.path.join(base, "Tramo1_Fixtures_EstadoFinal.xlsx"),
        "maestro_precios"  : os.path.join(base, "Maestro_Precios_Tramo1.xlsx"),
    }
    return construir_dataframe_maestro(rutas)

df_base = cargar_df_maestro()   # fuente de verdad — nunca se modifica


# ─────────────────────────────────────────────────────────
# FUNCIONES DE FORMATO Y KPIs
# ─────────────────────────────────────────────────────────
def fmt_m(v):   return f"{v:,.0f} m"
def fmt_cop(v): return f"$ {v:,.0f}"
def fmt_pct(v): return f"{v:.1f}%"

def kpi_card(label, value, estilo=""):
    """Genera HTML de tarjeta KPI con estilo unificado para todas las pestañas."""
    clase = f"kpi-card{'-'+estilo if estilo else ''}"
    return f"""<div class="{clase}">
        <div class="kpi-label">{label}</div>
        <div class="kpi-value">{value}</div>
    </div>"""

def calcular_kpis_tecnicos(df):
    cond = df[df["categoria"] == "Conduits"]
    long_demolida    = cond[cond["estado"] == "DEMOLIDO"]["cantidad"].sum()
    long_nueva       = cond[cond["estado"] == "NUEVO"]["cantidad"].sum()
    long_persistente = cond[cond["estado"] == "PERSISTENTE"]["cantidad"].sum()
    long_inicial     = long_demolida + long_persistente
    long_final       = long_nueva + long_persistente
    total_base       = long_inicial + long_nueva
    pct_intervencion = (long_demolida + long_nueva) / total_base * 100 if total_base > 0 else 0
    return dict(long_inicial=long_inicial, long_demolida=long_demolida,
                long_nueva=long_nueva, long_persistente=long_persistente,
                long_final=long_final, pct_intervencion=pct_intervencion)

def calcular_kpis_economicos(df):
    costo_demol = df["costo_demolicion"].sum()
    costo_nuevo = df["costo_nuevo"].sum()
    inversion   = costo_demol + costo_nuevo
    return dict(costo_demolicion=costo_demol, costo_nuevo=costo_nuevo,
                inversion_total=inversion,
                pct_demol=costo_demol/inversion*100 if inversion>0 else 0,
                pct_nuevo=costo_nuevo/inversion*100 if inversion>0 else 0)

def calcular_kpis_conteo(df):
    result = {}
    for cat in ["Conduits", "Fittings", "Fixtures"]:
        sub = df[df["categoria"] == cat]
        es_longitud = (cat == "Conduits")
        result[cat] = {
            "demolido"   : sub[sub["estado"]=="DEMOLIDO"]["cantidad"].sum() if es_longitud else int(sub[sub["estado"]=="DEMOLIDO"]["cantidad"].sum()),
            "nuevo"      : sub[sub["estado"]=="NUEVO"]["cantidad"].sum() if es_longitud else int(sub[sub["estado"]=="NUEVO"]["cantidad"].sum()),
            "persistente": sub[sub["estado"]=="PERSISTENTE"]["cantidad"].sum() if es_longitud else int(sub[sub["estado"]=="PERSISTENTE"]["cantidad"].sum()),
        }
    return result

def calcular_kpis_calidad(df):
    total = len(df)
    sin_longitud    = df[(df["categoria"]=="Conduits") & (df["cantidad"].isna() | (df["cantidad"]<=0))].shape[0]
    sin_diametro    = df[(df["categoria"].isin(["Conduits","Fittings"])) & (df["diametro"].isin(["nan","N/A",""]))].shape[0]
    sin_fase        = df[df["estado"]=="DESCONOCIDO"].shape[0]
    ids_duplicados  = df.duplicated(subset=["id"]).sum()
    sin_precio      = (~df["precio_encontrado"]).sum()
    sin_sistema     = df["nombre_sistema"].isna().sum()
    sin_cat_sistema = df["categoria_sistema"].isna().sum()
    return dict(total=total,
                sin_longitud=sin_longitud, sin_diametro=sin_diametro,
                sin_fase=sin_fase, ids_duplicados=ids_duplicados,
                pct_critico=(sin_longitud+sin_diametro+sin_fase+ids_duplicados)/total*100 if total>0 else 0,
                sin_precio=sin_precio, sin_sistema=sin_sistema,
                pct_std=sin_precio/total*100 if total>0 else 0,
                sin_cat_sistema=sin_cat_sistema,
                pct_nc=sin_cat_sistema/total*100 if total>0 else 0)


# ─────────────────────────────────────────────────────────
# FUNCIÓN UNIVERSAL DE LAYOUT PARA GRÁFICOS DE BARRAS
# Aplica siempre el margen superior correcto para que los números
# nunca se corten — funciona para barras grouped Y stacked.
# ─────────────────────────────────────────────────────────
COLORES = {
    "DEMOLIDO"           : "#64748b",
    "NUEVO"              : "#1a56db",
    "PERSISTENTE"        : "#93c5fd",
    "Demolición"         : "#64748b",
    "Nueva Construcción" : "#1a56db",
    "DESCONOCIDO"        : "#ef4444",
}

def barra_con_margen(fig, altura=350, margen_pct=0.20):
    """
    Aplica estilo y margen superior universal a cualquier figura de barras.
    Funciona tanto para barmode='group' como 'stack'.
    """
    from collections import defaultdict
    barmode = fig.layout.barmode or "group"
    max_y = 0

    if barmode == "stack":
        sumas = defaultdict(float)
        for trace in fig.data:
            if hasattr(trace, "x") and hasattr(trace, "y") and trace.x is not None and trace.y is not None:
                for xi, yi in zip(trace.x, trace.y):
                    if yi is not None:
                        sumas[str(xi)] += float(yi)
        if sumas:
            max_y = max(sumas.values())
    else:  # group o sin barmode
        for trace in fig.data:
            if hasattr(trace, "y") and trace.y is not None:
                vals = [v for v in trace.y if v is not None]
                if vals:
                    max_y = max(max_y, max(vals))

    rango_y = [0, max_y * (1 + margen_pct)] if max_y > 0 else [0, 1]

    fig.update_layout(
        height=altura,
        plot_bgcolor="white",
        paper_bgcolor="white",
        margin=dict(t=50, b=40, l=20, r=20),
        yaxis=dict(range=rango_y),
        font=dict(family="sans-serif"),
        hovermode="x unified",   # muestra tooltip al pasar por la columna, incluso en barras de 1px
    )
    return fig


# ─────────────────────────────────────────────────────────
# CABECERA GLOBAL (visible en todas las pestañas)
# ─────────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
    <p style="font-size:34px; font-weight:900; margin:0; color:white; letter-spacing:-0.5px; line-height:1.2;">
        🏗️ Sistema de Análisis BIM – Tramo 1
    </p>
    <p style="font-size:14px; opacity:0.85; margin:8px 0 0 0; color:white;">
        Metro 80 Medellín &nbsp;·&nbsp; Telecomunicaciones &nbsp;·&nbsp; Datos exportados desde Autodesk Revit
    </p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗️")
    st.markdown("**Sistema BIM · Tramo 1**")
    st.markdown("---")
    st.markdown("**Configuración**")
    factor_demol = st.slider(
        "Factor costo demolición (%)",
        min_value=10, max_value=40, value=25, step=5,
        help="Porcentaje del valor del elemento nuevo que cuesta demolerlo"
    ) / 100
    st.markdown("---")
    if st.button("🔄 Actualizar datos"):
        st.cache_data.clear()
        st.rerun()
    st.caption("Úsalo si reemplazas los archivos Excel por una versión nueva.")
    st.markdown("---")
    st.markdown("**Filtros · Análisis Detallado**")
    categorias_disp = ["Todas"] + sorted(df_base["categoria"].unique().tolist())
    filtro_cat = st.selectbox("Categoría", categorias_disp)
    filtro_est = st.multiselect(
        "Estado",
        options=["DEMOLIDO", "NUEVO", "PERSISTENTE"],
        format_func=lambda x: {"DEMOLIDO": "Demolido", "NUEVO": "Proyectado", "PERSISTENTE": "Existente a Mantener"}[x],
        default=["DEMOLIDO", "NUEVO", "PERSISTENTE"]
    )
    # Filtro por Tipo — se actualiza dinámicamente según Categoría seleccionada
    tipos_disp_raw = sorted(df_base[
        df_base["categoria"] == filtro_cat if filtro_cat != "Todas" else df_base["categoria"].notna()
    ]["type"].unique().tolist())
    filtro_tipo = st.multiselect(
        "Tipo / Familia",
        options=tipos_disp_raw,
        default=[],
        placeholder="Todos los tipos",
        help="Filtra por tipo o familia específica. Si no seleccionas nada, se muestran todos."
    )


# Recalcular SIEMPRE desde df_base → el slider nunca acumula errores
from build_maestro import calcular_costos
df = calcular_costos(df_base.copy(), factor_demol)

kpi_tec = calcular_kpis_tecnicos(df)
kpi_eco = calcular_kpis_economicos(df)
kpi_cnt = calcular_kpis_conteo(df)
kpi_cal = calcular_kpis_calidad(df)

# ─────────────────────────────────────────────────────────
# NAVEGACIÓN POR PESTAÑAS
# ─────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["📊 Resumen Ejecutivo", "🔍 Análisis Detallado", "🧱 Integridad del Modelo"])

# ═══════════════════════════════════════════════════════════
# PESTAÑA 1 — RESUMEN EJECUTIVO
# ═══════════════════════════════════════════════════════════
with tab1:

    # ── Bloque A: KPIs Técnicos ──
    st.markdown('<div class="seccion-titulo">📐 Indicadores Técnicos — Conduits</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:  st.markdown(kpi_card("Longitud Inicial",  fmt_m(kpi_tec["long_inicial"])),          unsafe_allow_html=True)
    with c2:  st.markdown(kpi_card("Longitud Demolida", fmt_m(kpi_tec["long_demolida"]), "muted"), unsafe_allow_html=True)
    with c3:  st.markdown(kpi_card("Longitud Nueva",    fmt_m(kpi_tec["long_nueva"]),   "alt"),   unsafe_allow_html=True)
    with c4:  st.markdown(kpi_card("Longitud Final",    fmt_m(kpi_tec["long_final"])),            unsafe_allow_html=True)
    with c5:  st.markdown(kpi_card("% Intervención",    fmt_pct(kpi_tec["pct_intervencion"])),    unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Bloque B: KPIs Económicos ──
    st.markdown('<div class="seccion-titulo">💰 Indicadores Económicos — Proyecto Completo</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:  st.markdown(kpi_card(f"Costo Demolición ({int(factor_demol*100)}%)", fmt_cop(kpi_eco["costo_demolicion"]), "muted"), unsafe_allow_html=True)
    with c2:  st.markdown(kpi_card("Costo Nueva Construcción",                     fmt_cop(kpi_eco["costo_nuevo"]),      "alt"),   unsafe_allow_html=True)
    with c3:  st.markdown(kpi_card("Inversión Total del Proyecto",                 fmt_cop(kpi_eco["inversion_total"])),           unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Bloque C: Visualización de Progreso ──
    st.markdown('<div class="seccion-titulo">📈 Visualización de Progreso</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    with col1:
        fig1 = go.Figure([
            go.Bar(name="Inicial", x=["Inicial"], y=[kpi_tec["long_inicial"]],
                   marker_color="#1a56db",
                   text=[f"{kpi_tec['long_inicial']:,.0f} m"], textposition="outside"),
            go.Bar(name="Final", x=["Final"], y=[kpi_tec["long_final"]],
                   marker_color="#60a5fa",
                   text=[f"{kpi_tec['long_final']:,.0f} m"], textposition="outside"),
        ])
        fig1.update_layout(title="Comparativo: Inicial vs Final", barmode="group",
                           showlegend=True, yaxis_title="Metros")
        st.plotly_chart(barra_con_margen(fig1), use_container_width=True)

    with col2:
        fig2 = go.Figure([
            go.Bar(name="Demolido", x=["Demolido"], y=[kpi_tec["long_demolida"]],
                   marker_color="#64748b",
                   text=[f"{kpi_tec['long_demolida']:,.0f} m"], textposition="outside"),
            go.Bar(name="Nuevo", x=["Nuevo"], y=[kpi_tec["long_nueva"]],
                   marker_color="#1a56db",
                   text=[f"{kpi_tec['long_nueva']:,.0f} m"], textposition="outside"),
        ])
        fig2.update_layout(title="Demolido vs Nuevo (Conduits)", barmode="group",
                           yaxis_title="Metros")
        st.plotly_chart(barra_con_margen(fig2), use_container_width=True)

    with col3:
        fig3 = go.Figure([go.Pie(
            labels=["Demolición", "Nueva Construcción"],
            values=[kpi_eco["costo_demolicion"], kpi_eco["costo_nuevo"]],
            marker_colors=["#64748b", "#1a56db"],
            hole=0.4, textinfo="label+percent",
        )])
        fig3.update_layout(title="Distribución de Inversión", height=350,
                           paper_bgcolor="white", margin=dict(t=50, b=20, l=20, r=20))
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Bloque D: Conteo por categoría ──
    st.markdown('<div class="seccion-titulo">🔢 Conteo de Elementos por Categoría y Estado</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    for col, cat_name in zip([col1, col2, col3], ["Conduits", "Fittings", "Fixtures"]):
        data   = kpi_cnt[cat_name]
        unidad = "m" if cat_name == "Conduits" else "und"
        vals   = [data["demolido"], data["nuevo"], data["persistente"]]
        with col:
            st.markdown(f"**{cat_name}**")
            fig = go.Figure([go.Bar(
                x=["Demolido", "Nuevo", "Persistente"], y=vals,
                marker_color=["#64748b", "#1a56db", "#93c5fd"],
                text=[f"{v:,.0f}" for v in vals], textposition="outside",
                hovertemplate="<b>%{x}</b><br>%{y:,.0f} " + unidad + "<extra></extra>",
            )])
            fig.update_layout(showlegend=False, yaxis_title=unidad)
            st.plotly_chart(barra_con_margen(fig, altura=280), use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PESTAÑA 2 — ANÁLISIS DETALLADO
# ═══════════════════════════════════════════════════════════
with tab2:

    df_filtrado = df.copy()
    if filtro_cat != "Todas":
        df_filtrado = df_filtrado[df_filtrado["categoria"] == filtro_cat]
    if filtro_est:
        df_filtrado = df_filtrado[df_filtrado["estado"].isin(filtro_est)]
    if filtro_tipo:
        df_filtrado = df_filtrado[df_filtrado["type"].isin(filtro_tipo)]

    etiq_est = [{"DEMOLIDO":"Demolido","NUEVO":"Proyectado","PERSISTENTE":"Existente a Mantener"}.get(e,e) for e in filtro_est]
    etiq_tipo = ", ".join(filtro_tipo) if filtro_tipo else "Todos"
    st.markdown(f"**Mostrando {len(df_filtrado):,} de {len(df):,} elementos** · "
                f"Categoría: `{filtro_cat}` · Estados: `{', '.join(etiq_est)}` · Tipo: `{etiq_tipo}`")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPIs del filtro activo — mismas tarjetas HTML que Pestaña 1 ──
    st.markdown('<div class="seccion-titulo">📐 KPIs del Filtro Activo</div>', unsafe_allow_html=True)
    cond_f = df_filtrado[df_filtrado["categoria"] == "Conduits"]
    c1, c2, c3, c4 = st.columns(4)
    with c1:  st.markdown(kpi_card("Total Elementos",     f"{len(df_filtrado):,}"),                                unsafe_allow_html=True)
    with c2:  st.markdown(kpi_card("Longitud (Conduits)", fmt_m(cond_f["cantidad"].sum())),                        unsafe_allow_html=True)
    with c3:  st.markdown(kpi_card("Costo Nueva Const.",  fmt_cop(df_filtrado["costo_nuevo"].sum()),      "alt"),  unsafe_allow_html=True)
    with c4:  st.markdown(kpi_card("Costo Demolición",    fmt_cop(df_filtrado["costo_demolicion"].sum()), "muted"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Análisis por Tipo ──
    st.markdown('<div class="seccion-titulo">📊 Análisis por Tipo</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    with col1:
        cond_tipo = (df_filtrado[df_filtrado["categoria"] == "Conduits"]
                     .groupby(["type","estado"])["cantidad"].sum().reset_index())
        if not cond_tipo.empty:
            fig = px.bar(cond_tipo, x="type", y="cantidad", color="estado",
                         color_discrete_map=COLORES,
                         title="Longitud (m) por Tipo de Conduit",
                         labels={"cantidad":"Metros","type":"Tipo","estado":"Estado"},
                         barmode="group")
            fig.update_traces(
                hovertemplate="<b>Tipo:</b> %{x}<br><b>Longitud:</b> %{y:,.1f} m<extra>%{fullData.name}</extra>"
            )
            st.plotly_chart(barra_con_margen(fig), use_container_width=True)

    with col2:
        costo_tipo = df_filtrado.groupby(["type","estado"]).agg(
            costo=("costo_total","sum"),
            cantidad=("cantidad","sum"),
            elementos=("id","count")
        ).reset_index()
        top10 = costo_tipo.groupby("type")["costo"].sum().nlargest(10).index
        costo_tipo = costo_tipo[costo_tipo["type"].isin(top10)]
        if not costo_tipo.empty:
            fig = px.bar(costo_tipo, x="type", y="costo", color="estado",
                         color_discrete_map=COLORES,
                         title="Costo Total (COP) por Tipo — Top 10",
                         labels={"costo":"COP","type":"Tipo","estado":"Estado"},
                         barmode="stack",
                         custom_data=["elementos","cantidad"])
            fig.update_traces(
                hovertemplate=(
                    "<b>Tipo:</b> %{x}<br>"
                    "<b>Estado:</b> %{fullData.name}<br>"
                    "<b>Elementos:</b> %{customdata[0]:,}<br>"
                    "<b>Cantidad:</b> %{customdata[1]:,.1f}<br>"
                    "<b>Costo:</b> $ %{y:,.0f}"
                    "<extra></extra>"
                )
            )
            st.plotly_chart(barra_con_margen(fig), use_container_width=True)

    # ── Análisis por Diámetro ──
    st.markdown('<div class="seccion-titulo">📏 Análisis por Diámetro</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)
    orden_diam = ['1"','2"','3"','4"']

    with col1:
        cond_diam = (df_filtrado[df_filtrado["categoria"] == "Conduits"]
                     .groupby(["diametro","estado"])["cantidad"].sum().reset_index())
        if not cond_diam.empty:
            fig = px.bar(cond_diam, x="diametro", y="cantidad", color="estado",
                         color_discrete_map=COLORES,
                         title="Longitud (m) por Diámetro",
                         labels={"cantidad":"Metros","diametro":"Diámetro","estado":"Estado"},
                         barmode="group",
                         category_orders={"diametro": orden_diam})
            fig.update_traces(
                hovertemplate="<b>Diámetro:</b> %{x}<br><b>Longitud:</b> %{y:,.1f} m<extra>%{fullData.name}</extra>"
            )
            fig.update_layout(xaxis=dict(type="category"))
            st.plotly_chart(barra_con_margen(fig), use_container_width=True)

    with col2:
        costo_diam = (df_filtrado[df_filtrado["diametro"] != "N/A"]
                      .groupby(["diametro","estado"]).agg(
                          costo=("costo_total","sum"),
                          elementos=("id","count"),
                          cantidad=("cantidad","sum")
                      ).reset_index())
        if not costo_diam.empty:
            fig = px.bar(costo_diam, x="diametro", y="costo", color="estado",
                         color_discrete_map=COLORES,
                         title="Costo Total (COP) por Diámetro",
                         labels={"costo":"COP","diametro":"Diámetro","estado":"Estado"},
                         barmode="stack",
                         category_orders={"diametro": orden_diam},
                         custom_data=["elementos","cantidad"])
            fig.update_traces(
                hovertemplate=(
                    "<b>Diámetro:</b> %{x}<br>"
                    "<b>Estado:</b> %{fullData.name}<br>"
                    "<b>Elementos:</b> %{customdata[0]:,}<br>"
                    "<b>Cantidad:</b> %{customdata[1]:,.1f}<br>"
                    "<b>Costo:</b> $ %{y:,.0f}"
                    "<extra></extra>"
                )
            )
            fig.update_layout(xaxis=dict(type="category"))
            st.plotly_chart(barra_con_margen(fig), use_container_width=True)

    # ── Tabla dinámica ──
    st.markdown('<div class="seccion-titulo">📋 Tabla Dinámica Detallada</div>', unsafe_allow_html=True)
    tabla = df_filtrado[[
        "categoria","family","type","diametro","estado","cantidad","unidad",
        "precio_unitario","costo_nuevo","costo_demolicion","costo_total"
    ]].copy()
    tabla["precio_unitario"]  = tabla["precio_unitario"].apply(lambda x: f"$ {x:,.0f}" if pd.notna(x) else "—")
    tabla["costo_nuevo"]      = tabla["costo_nuevo"].apply(lambda x: f"$ {x:,.0f}")
    tabla["costo_demolicion"] = tabla["costo_demolicion"].apply(lambda x: f"$ {x:,.0f}")
    tabla["costo_total"]      = tabla["costo_total"].apply(lambda x: f"$ {x:,.0f}")
    tabla["cantidad"]         = tabla["cantidad"].apply(lambda x: f"{x:,.2f}")
    tabla.columns = ["Categoría","Familia","Tipo","Diámetro","Estado","Cantidad",
                     "Unidad","Precio Unitario","Costo Nuevo","Costo Demolición","Costo Total"]
    st.dataframe(tabla, use_container_width=True, height=400)
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar datos filtrados (CSV)", csv,
                       "datos_filtrados_tramo1.csv", "text/csv")


# ═══════════════════════════════════════════════════════════
# PESTAÑA 3 — INTEGRIDAD DEL MODELO
# ═══════════════════════════════════════════════════════════
with tab3:

    st.markdown('<div class="seccion-titulo">🔎 Auditoría de Calidad del Modelo BIM</div>', unsafe_allow_html=True)
    q = kpi_cal

    # ── Nivel Crítico ──
    st.markdown("#### 🔴 Nivel Crítico — Bloquea cálculos")
    c1, c2, c3, c4 = st.columns(4)
    metricas_crit = [
        (c1, "Sin longitud válida",  q["sin_longitud"],  q["sin_longitud"]/q["total"]*100),
        (c2, "Sin diámetro válido",  q["sin_diametro"],  q["sin_diametro"]/q["total"]*100),
        (c3, "Sin fase definida",    q["sin_fase"],       q["sin_fase"]/q["total"]*100),
        (c4, "IDs duplicados",       q["ids_duplicados"], q["ids_duplicados"]/q["total"]*100),
    ]
    for col, label, val, pct in metricas_crit:
        icono = "🔴" if val > 0 else "🟢"
        with col:
            st.markdown(kpi_card(f"{icono} {label}", f"{val:,}  ({pct:.2f}%)"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # Score crítico (gauge)
    score_crit = max(0, 100 - q["pct_critico"])
    fig_gauge = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=score_crit,
        title={"text": "Score Integridad Crítica", "font": {"size": 16}},
        delta={"reference": 100, "increasing": {"color": "#16a34a"}},
        gauge={
            "axis": {"range": [0, 100]},
            "bar": {"color": "#1a56db"},
            "steps": [
                {"range": [0, 60],   "color": "#fee2e2"},
                {"range": [60, 85],  "color": "#fef9c3"},
                {"range": [85, 100], "color": "#dcfce7"},
            ],
            "threshold": {"line": {"color": "red", "width": 4}, "thickness": 0.75, "value": 85}
        }
    ))
    fig_gauge.update_layout(height=280, margin=dict(t=40, b=20, l=40, r=40), paper_bgcolor="white")

    col1, col2 = st.columns([1, 2])
    with col1:
        st.plotly_chart(fig_gauge, use_container_width=True)
    with col2:
        st.markdown("**Interpretación del Score Crítico:**")
        st.markdown("- 🟢 **85–100** → Modelo listo para análisis")
        st.markdown("- 🟡 **60–85** → Requiere correcciones antes de usar")
        st.markdown("- 🔴 **0–60**  → Modelo NO confiable, revisar en Revit")
        st.markdown(f"\nScore actual: **{score_crit:.1f}/100**")
        if score_crit >= 85:
            st.success("✅ El modelo supera el umbral de calidad crítica.")
        elif score_crit >= 60:
            st.warning("⚠️ El modelo tiene problemas que deben corregirse.")
        else:
            st.error("❌ El modelo tiene problemas críticos graves.")

    st.markdown("---")

    # ── Nivel Estandarización ──
    st.markdown("#### 🟡 Nivel Estandarización — Afecta costos y análisis")
    c1, c2 = st.columns(2)
    with c1:  st.markdown(kpi_card("🟡 Sin precio asignado",   f"{q['sin_precio']:,}  ({q['sin_precio']/q['total']*100:.2f}%)",  "muted"), unsafe_allow_html=True)
    with c2:  st.markdown(kpi_card("🟡 Sin nombre de sistema", f"{q['sin_sistema']:,}  ({q['sin_sistema']/q['total']*100:.2f}%)", "muted"), unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Nivel No Crítico ──
    st.markdown("#### 🔵 Nivel No Crítico — Campos informativos")
    st.markdown(kpi_card("🔵 Sin Categoría de Sistema",
                         f"{q['sin_cat_sistema']:,}  ({q['sin_cat_sistema']/q['total']*100:.2f}%)"),
                unsafe_allow_html=True)

    st.markdown("---")

    # ── Distribución del modelo — 3 gráficos separados (uno por categoría) ──
    st.markdown('<div class="seccion-titulo">📊 Distribución del Modelo por Categoría y Estado</div>', unsafe_allow_html=True)
    dist = df.groupby(["categoria","estado"]).size().reset_index(name="count")

    col1, col2, col3 = st.columns(3)
    for col, cat_name in zip([col1, col2, col3], ["Conduits", "Fittings", "Fixtures"]):
        sub = dist[dist["categoria"] == cat_name].copy()
        unidad = "elementos"
        vals_por_estado = {row["estado"]: row["count"] for _, row in sub.iterrows()}
        with col:
            st.markdown(f"**{cat_name}**")
            estados  = ["DEMOLIDO", "NUEVO", "PERSISTENTE"]
            vals     = [vals_por_estado.get(e, 0) for e in estados]
            fig = go.Figure([go.Bar(
                x=estados, y=vals,
                marker_color=["#64748b", "#1a56db", "#93c5fd"],
                text=[f"{v:,}" for v in vals],
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>%{y:,} elementos<extra></extra>",
            )])
            fig.update_layout(showlegend=False, yaxis_title="Elementos",
                              title=cat_name)
            st.plotly_chart(barra_con_margen(fig, altura=300), use_container_width=True)

    # ── Tabla de problemas ──
    problemas = df[~df["precio_encontrado"]]
    if len(problemas) > 0:
        st.markdown('<div class="seccion-titulo">⚠️ Elementos sin precio asignado</div>', unsafe_allow_html=True)
        st.dataframe(problemas[["categoria","family","type","diametro","estado","cantidad"]],
                     use_container_width=True)
    else:
        st.success("✅ Todos los elementos tienen precio asignado en el maestro.")

    # ── Resumen final ──
    st.markdown("---")
    st.markdown("##### 📋 Resumen General del Modelo")
    resumen = pd.DataFrame({
        "Categoría"   : ["Conduits","Fittings","Fixtures","**TOTAL**"],
        "Total Elem." : [len(df[df["categoria"]==c]) for c in ["Conduits","Fittings","Fixtures"]] + [len(df)],
        "Con Precio"  : [df[(df["categoria"]==c)&df["precio_encontrado"]].shape[0] for c in ["Conduits","Fittings","Fixtures"]] + [df[df["precio_encontrado"]].shape[0]],
        "Sin Precio"  : [df[(df["categoria"]==c)&~df["precio_encontrado"]].shape[0] for c in ["Conduits","Fittings","Fixtures"]] + [df[~df["precio_encontrado"]].shape[0]],
    })
    st.dataframe(resumen, use_container_width=True, hide_index=True)
