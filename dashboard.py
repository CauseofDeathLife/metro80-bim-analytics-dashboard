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

# Importar el pipeline del DataFrame Maestro
# (asegúrate de que build_maestro.py esté en la misma carpeta)
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
# ESTILOS GLOBALES
# ─────────────────────────────────────────────────────────
st.markdown("""
<style>
    /* Fondo general */
    .main { background-color: #f0f2f6; }

    /* Tarjetas KPI */
    .kpi-card {
        background-color: #ffffff;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        border-left: 5px solid #1a56db;
        margin-bottom: 8px;
    }
    .kpi-card-green {
        background-color: #f0fdf4;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        border-left: 5px solid #16a34a;
        margin-bottom: 8px;
    }
    .kpi-card-red {
        background-color: #fff7f7;
        border-radius: 10px;
        padding: 16px 20px;
        box-shadow: 0 2px 6px rgba(0,0,0,0.08);
        border-left: 5px solid #dc2626;
        margin-bottom: 8px;
    }
    .kpi-label {
        font-size: 13px;
        color: #6b7280;
        font-weight: 500;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 26px;
        font-weight: 700;
        color: #111827;
    }
    .kpi-value-small {
        font-size: 18px;
        font-weight: 700;
        color: #111827;
    }

    /* Encabezados de sección */
    .seccion-titulo {
        font-size: 16px;
        font-weight: 700;
        color: #1e3a5f;
        padding: 8px 0 4px 0;
        border-bottom: 2px solid #1a56db;
        margin-bottom: 12px;
    }

    /* Cabecera */
    .header-box {
        background: linear-gradient(135deg, #1e3a5f 0%, #1a56db 100%);
        border-radius: 10px;
        padding: 18px 24px;
        color: white;
        margin-bottom: 20px;
    }
    .header-title {
        font-size: 22px;
        font-weight: 800;
        margin: 0;
    }
    .header-subtitle {
        font-size: 13px;
        opacity: 0.85;
        margin: 4px 0 0 0;
    }

    /* Alertas de calidad */
    .badge-critico   { background:#fee2e2; color:#991b1b; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-medio     { background:#fef9c3; color:#854d0e; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
    .badge-ok        { background:#dcfce7; color:#166534; padding:3px 10px; border-radius:12px; font-size:12px; font-weight:600; }
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

df_base = cargar_df_maestro()   # ← nunca se modifica, es la fuente de verdad


# ─────────────────────────────────────────────────────────
# FUNCIONES DE KPI
# ─────────────────────────────────────────────────────────
def fmt_m(v):   return f"{v:,.0f} m"
def fmt_cop(v): return f"$ {v:,.0f}"
def fmt_pct(v): return f"{v:.1f}%"
def fmt_und(v): return f"{int(v):,} und"

def calcular_kpis_tecnicos(df):
    cond = df[df["categoria"] == "Conduits"]
    long_demolida    = cond[cond["estado"] == "DEMOLIDO"]["cantidad"].sum()
    long_nueva       = cond[cond["estado"] == "NUEVO"]["cantidad"].sum()
    long_persistente = cond[cond["estado"] == "PERSISTENTE"]["cantidad"].sum()
    long_inicial     = long_demolida + long_persistente
    long_final       = long_nueva + long_persistente
    total_base       = long_inicial + long_nueva
    pct_intervencion = (long_demolida + long_nueva) / total_base * 100 if total_base > 0 else 0
    return {
        "long_inicial"      : long_inicial,
        "long_demolida"     : long_demolida,
        "long_nueva"        : long_nueva,
        "long_persistente"  : long_persistente,
        "long_final"        : long_final,
        "pct_intervencion"  : pct_intervencion,
    }

def calcular_kpis_economicos(df):
    costo_demol  = df["costo_demolicion"].sum()
    costo_nuevo  = df["costo_nuevo"].sum()
    inversion    = costo_demol + costo_nuevo
    return {
        "costo_demolicion"  : costo_demol,
        "costo_nuevo"       : costo_nuevo,
        "inversion_total"   : inversion,
        "pct_demol"         : costo_demol / inversion * 100 if inversion > 0 else 0,
        "pct_nuevo"         : costo_nuevo / inversion * 100 if inversion > 0 else 0,
    }

def calcular_kpis_conteo(df):
    result = {}
    for cat in ["Conduits", "Fittings", "Fixtures"]:
        sub = df[df["categoria"] == cat]
        result[cat] = {
            "demolido"   : sub[sub["estado"] == "DEMOLIDO"]["cantidad"].sum() if cat == "Conduits" else int(sub[sub["estado"] == "DEMOLIDO"]["cantidad"].sum()),
            "nuevo"      : sub[sub["estado"] == "NUEVO"]["cantidad"].sum() if cat == "Conduits" else int(sub[sub["estado"] == "NUEVO"]["cantidad"].sum()),
            "persistente": sub[sub["estado"] == "PERSISTENTE"]["cantidad"].sum() if cat == "Conduits" else int(sub[sub["estado"] == "PERSISTENTE"]["cantidad"].sum()),
        }
    return result

def calcular_kpis_calidad(df):
    total = len(df)
    # Críticos
    sin_longitud   = df[(df["categoria"] == "Conduits") & (df["cantidad"].isna() | (df["cantidad"] <= 0))].shape[0]
    sin_diametro   = df[(df["categoria"].isin(["Conduits","Fittings"])) & (df["diametro"].isin(["nan","N/A",""]))] .shape[0]
    sin_fase       = df[df["estado"] == "DESCONOCIDO"].shape[0]
    ids_duplicados = df.duplicated(subset=["id"]).sum()
    # Estandarización
    sin_precio     = (~df["precio_encontrado"]).sum()
    sin_sistema    = df["nombre_sistema"].isna().sum()
    sin_cat_sistema= df["categoria_sistema"].isna().sum()
    return {
        "total"          : total,
        # Críticos
        "sin_longitud"   : sin_longitud,
        "sin_diametro"   : sin_diametro,
        "sin_fase"       : sin_fase,
        "ids_duplicados" : ids_duplicados,
        "pct_critico"    : (sin_longitud + sin_diametro + sin_fase + ids_duplicados) / total * 100 if total > 0 else 0,
        # Estandarización
        "sin_precio"     : sin_precio,
        "sin_sistema"    : sin_sistema,
        "pct_std"        : (sin_precio) / total * 100 if total > 0 else 0,
        # No crítico
        "sin_cat_sistema": sin_cat_sistema,
        "pct_nc"         : sin_cat_sistema / total * 100 if total > 0 else 0,
    }


# ─────────────────────────────────────────────────────────
# CABECERA GLOBAL
# ─────────────────────────────────────────────────────────
st.markdown("""
<div class="header-box">
    <p class="header-title">🏗️ Sistema de Análisis BIM – Tramo 1</p>
    <p class="header-subtitle">Metro 80 Medellín · Telecomunicaciones · Datos exportados desde Autodesk Revit</p>
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 🏗️")
    st.markdown("### Sistema BIM · Tramo 1")
    st.markdown("---")
    st.markdown("**Navegación**")
    pagina = st.radio("", ["📊 Resumen Ejecutivo", "🔍 Análisis Detallado", "🧱 Integridad del Modelo"], label_visibility="collapsed")
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
    st.markdown("**Filtros activos en Análisis Detallado**")
    categorias_disp = ["Todas"] + sorted(df_base["categoria"].unique().tolist())
    filtro_cat  = st.selectbox("Categoría", categorias_disp)
    filtro_est  = st.multiselect("Estado", ["DEMOLIDO","NUEVO","PERSISTENTE"], default=["DEMOLIDO","NUEVO","PERSISTENTE"])


# Siempre recalcula desde df_base → el slider nunca acumula errores
from build_maestro import calcular_costos
df = calcular_costos(df_base.copy(), factor_demol)

# Calcular todos los KPIs
kpi_tec  = calcular_kpis_tecnicos(df)
kpi_eco  = calcular_kpis_economicos(df)
kpi_cnt  = calcular_kpis_conteo(df)
kpi_cal  = calcular_kpis_calidad(df)


# ═══════════════════════════════════════════════════════════
# PESTAÑA 1 — RESUMEN EJECUTIVO
# ═══════════════════════════════════════════════════════════
if pagina == "📊 Resumen Ejecutivo":

    # ── BLOQUE A: KPIs Técnicos ──
    st.markdown('<div class="seccion-titulo">📐 Indicadores Técnicos — Conduits</div>', unsafe_allow_html=True)
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Longitud Inicial</div>
            <div class="kpi-value">{fmt_m(kpi_tec['long_inicial'])}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card kpi-card-red">
            <div class="kpi-label">Longitud Demolida</div>
            <div class="kpi-value">{fmt_m(kpi_tec['long_demolida'])}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-card kpi-card-green">
            <div class="kpi-label">Longitud Nueva</div>
            <div class="kpi-value">{fmt_m(kpi_tec['long_nueva'])}</div>
        </div>""", unsafe_allow_html=True)
    with c4:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Longitud Final</div>
            <div class="kpi-value">{fmt_m(kpi_tec['long_final'])}</div>
        </div>""", unsafe_allow_html=True)
    with c5:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">% Intervención</div>
            <div class="kpi-value">{fmt_pct(kpi_tec['pct_intervencion'])}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BLOQUE B: KPIs Económicos ──
    st.markdown('<div class="seccion-titulo">💰 Indicadores Económicos — Proyecto Completo</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(f"""<div class="kpi-card kpi-card-red">
            <div class="kpi-label">Costo de Demolición ({int(factor_demol*100)}%)</div>
            <div class="kpi-value-small">{fmt_cop(kpi_eco['costo_demolicion'])}</div>
        </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown(f"""<div class="kpi-card kpi-card-green">
            <div class="kpi-label">Costo Nueva Construcción</div>
            <div class="kpi-value-small">{fmt_cop(kpi_eco['costo_nuevo'])}</div>
        </div>""", unsafe_allow_html=True)
    with c3:
        st.markdown(f"""<div class="kpi-card">
            <div class="kpi-label">Inversión Total del Proyecto</div>
            <div class="kpi-value-small">{fmt_cop(kpi_eco['inversion_total'])}</div>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BLOQUE C: Visualización Narrativa ──
    st.markdown('<div class="seccion-titulo">📈 Visualización de Progreso</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    # Gráfico 1: Comparativo Inicial vs Final
    with col1:
        fig1 = go.Figure(data=[
            go.Bar(name="Inicial", x=["Inicial"], y=[kpi_tec["long_inicial"]],
                   marker_color="#1a56db", text=[f"{kpi_tec['long_inicial']:,.0f} m"],
                   textposition="outside"),
            go.Bar(name="Final",   x=["Final"],   y=[kpi_tec["long_final"]],
                   marker_color="#60a5fa", text=[f"{kpi_tec['long_final']:,.0f} m"],
                   textposition="outside"),
        ])
        fig1.update_layout(
            title="Comparativo: Inicial vs Final",
            barmode="group", height=360,
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(t=40, b=20, l=20, r=20),
            showlegend=True,
            yaxis_title="Metros",
            yaxis=dict(range=[0, max(kpi_tec["long_inicial"], kpi_tec["long_final"]) * 1.18]),
        )
        st.plotly_chart(fig1, use_container_width=True)

    # Gráfico 2: Demolido vs Nuevo
    with col2:
        fig2 = go.Figure(data=[
            go.Bar(name="Demolido", x=["Demolido"], y=[kpi_tec["long_demolida"]],
                   marker_color="#64748b", text=[f"{kpi_tec['long_demolida']:,.0f} m"],
                   textposition="outside"),
            go.Bar(name="Nuevo",    x=["Nuevo"],    y=[kpi_tec["long_nueva"]],
                   marker_color="#1a56db", text=[f"{kpi_tec['long_nueva']:,.0f} m"],
                   textposition="outside"),
        ])
        fig2.update_layout(
            title="Demolido vs Nuevo (Conduits)",
            barmode="group", height=360,
            plot_bgcolor="white", paper_bgcolor="white",
            margin=dict(t=40, b=20, l=20, r=20),
            yaxis_title="Metros",
            yaxis=dict(range=[0, max(kpi_tec["long_demolida"], kpi_tec["long_nueva"]) * 1.18]),
        )
        st.plotly_chart(fig2, use_container_width=True)

    # Gráfico 3: Distribución de inversión
    with col3:
        fig3 = go.Figure(data=[go.Pie(
            labels=["Demolición", "Nueva Construcción"],
            values=[kpi_eco["costo_demolicion"], kpi_eco["costo_nuevo"]],
            marker_colors=["#64748b", "#1a56db"],
            hole=0.4,
            textinfo="label+percent",
        )])
        fig3.update_layout(
            title="Distribución de Inversión",
            height=320,
            paper_bgcolor="white",
            margin=dict(t=40, b=20, l=20, r=20),
        )
        st.plotly_chart(fig3, use_container_width=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── BLOQUE D: Conteo por categoría ──
    st.markdown('<div class="seccion-titulo">🔢 Conteo de Elementos por Categoría y Estado</div>', unsafe_allow_html=True)
    col1, col2, col3 = st.columns(3)

    for col, cat_name in zip([col1, col2, col3], ["Conduits", "Fittings", "Fixtures"]):
        data = kpi_cnt[cat_name]
        unidad = "m" if cat_name == "Conduits" else "und"
        with col:
            st.markdown(f"**{cat_name}**")
            fig = go.Figure(data=[go.Bar(
                x=["Demolido", "Nuevo", "Persistente"],
                y=[data["demolido"], data["nuevo"], data["persistente"]],
                marker_color=["#64748b", "#1a56db", "#93c5fd"],
                text=[f"{data['demolido']:,.0f}", f"{data['nuevo']:,.0f}", f"{data['persistente']:,.0f}"],
                textposition="outside",
            )])
            fig.update_layout(
                height=250,
                plot_bgcolor="white", paper_bgcolor="white",
                margin=dict(t=20, b=20, l=10, r=10),
                showlegend=False,
                yaxis_title=unidad,
            )
            st.plotly_chart(fig, use_container_width=True)


# ═══════════════════════════════════════════════════════════
# PESTAÑA 2 — ANÁLISIS DETALLADO
# ═══════════════════════════════════════════════════════════
elif pagina == "🔍 Análisis Detallado":

    # Aplicar filtros del sidebar
    df_filtrado = df.copy()
    if filtro_cat != "Todas":
        df_filtrado = df_filtrado[df_filtrado["categoria"] == filtro_cat]
    if filtro_est:
        df_filtrado = df_filtrado[df_filtrado["estado"].isin(filtro_est)]

    st.markdown(f"**Mostrando {len(df_filtrado):,} de {len(df):,} elementos** · Categoría: `{filtro_cat}` · Estados: `{', '.join(filtro_est)}`")
    st.markdown("<br>", unsafe_allow_html=True)

    # ── KPIs rápidos del filtro ──
    st.markdown('<div class="seccion-titulo">📐 KPIs del Filtro Activo</div>', unsafe_allow_html=True)
    c1, c2, c3, c4 = st.columns(4)
    cond_f = df_filtrado[df_filtrado["categoria"] == "Conduits"]
    with c1:
        st.metric("Total Elementos", f"{len(df_filtrado):,}")
    with c2:
        st.metric("Longitud (Conduits)", fmt_m(cond_f["cantidad"].sum()))
    with c3:
        st.metric("Costo Nueva Const.", fmt_cop(df_filtrado["costo_nuevo"].sum()))
    with c4:
        st.metric("Costo Demolición", fmt_cop(df_filtrado["costo_demolicion"].sum()))

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Gráficos de exploración ──
    st.markdown('<div class="seccion-titulo">📊 Análisis por Tipo</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    # Longitud por tipo (solo Conduits)
    with col1:
        cond_tipo = df_filtrado[df_filtrado["categoria"] == "Conduits"].groupby(["type","estado"])["cantidad"].sum().reset_index()
        if not cond_tipo.empty:
            fig = px.bar(cond_tipo, x="type", y="cantidad", color="estado",
                         color_discrete_map={"DEMOLIDO":"#64748b","NUEVO":"#1a56db","PERSISTENTE":"#93c5fd"},
                         title="Longitud (m) por Tipo de Conduit",
                         labels={"cantidad":"Metros","type":"Tipo"},
                         barmode="group")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=350,
                              margin=dict(t=40, b=40, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

    # Costo por tipo
    with col2:
        costo_tipo = df_filtrado.groupby(["type","estado"]).agg(
            costo=("costo_total","sum")
        ).reset_index()
        top10 = costo_tipo.groupby("type")["costo"].sum().nlargest(10).index
        costo_tipo = costo_tipo[costo_tipo["type"].isin(top10)]
        if not costo_tipo.empty:
            fig = px.bar(costo_tipo, x="type", y="costo", color="estado",
                         color_discrete_map={"DEMOLIDO":"#64748b","NUEVO":"#1a56db","PERSISTENTE":"#93c5fd"},
                         title="Costo Total (COP) por Tipo — Top 10",
                         labels={"costo":"COP","type":"Tipo"},
                         barmode="stack")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=350,
                              margin=dict(t=40, b=40, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

    st.markdown('<div class="seccion-titulo">📏 Análisis por Diámetro</div>', unsafe_allow_html=True)
    col1, col2 = st.columns(2)

    # Longitud por diámetro
    with col1:
        cond_diam = df_filtrado[df_filtrado["categoria"] == "Conduits"].groupby(["diametro","estado"])["cantidad"].sum().reset_index()
        if not cond_diam.empty:
            fig = px.bar(cond_diam, x="diametro", y="cantidad", color="estado",
                         color_discrete_map={"DEMOLIDO":"#64748b","NUEVO":"#1a56db","PERSISTENTE":"#93c5fd"},
                         title="Longitud (m) por Diámetro",
                         labels={"cantidad":"Metros","diametro":"Diámetro"},
                         barmode="group")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=350,
                              margin=dict(t=40, b=40, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

    # Costo por diámetro
    with col2:
        costo_diam = df_filtrado[df_filtrado["diametro"] != "N/A"].groupby(["diametro","estado"]).agg(
            costo=("costo_total","sum")
        ).reset_index()
        if not costo_diam.empty:
            fig = px.bar(costo_diam, x="diametro", y="costo", color="estado",
                         color_discrete_map={"DEMOLIDO":"#64748b","NUEVO":"#1a56db","PERSISTENTE":"#93c5fd"},
                         title="Costo Total (COP) por Diámetro",
                         labels={"costo":"COP","diametro":"Diámetro"},
                         barmode="stack")
            fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=350,
                              margin=dict(t=40, b=40, l=20, r=20))
            st.plotly_chart(fig, use_container_width=True)

    # ── Tabla dinámica ──
    st.markdown('<div class="seccion-titulo">📋 Tabla Dinámica Detallada</div>', unsafe_allow_html=True)

    tabla = df_filtrado[[
        "categoria","family","type","diametro","estado","cantidad","unidad",
        "precio_unitario","costo_nuevo","costo_demolicion","costo_total"
    ]].copy()
    tabla["precio_unitario"] = tabla["precio_unitario"].apply(lambda x: f"$ {x:,.0f}" if pd.notna(x) else "—")
    tabla["costo_nuevo"]     = tabla["costo_nuevo"].apply(lambda x: f"$ {x:,.0f}")
    tabla["costo_demolicion"]= tabla["costo_demolicion"].apply(lambda x: f"$ {x:,.0f}")
    tabla["costo_total"]     = tabla["costo_total"].apply(lambda x: f"$ {x:,.0f}")
    tabla["cantidad"]        = tabla["cantidad"].apply(lambda x: f"{x:,.2f}")

    tabla.columns = ["Categoría","Familia","Tipo","Diámetro","Estado","Cantidad",
                     "Unidad","Precio Unitario","Costo Nuevo","Costo Demolición","Costo Total"]

    st.dataframe(tabla, use_container_width=True, height=400)

    # Descargar filtrado
    csv = df_filtrado.to_csv(index=False).encode("utf-8")
    st.download_button("⬇️ Descargar datos filtrados (CSV)", csv,
                       "datos_filtrados_tramo1.csv", "text/csv")


# ═══════════════════════════════════════════════════════════
# PESTAÑA 3 — INTEGRIDAD DEL MODELO
# ═══════════════════════════════════════════════════════════
elif pagina == "🧱 Integridad del Modelo":

    st.markdown('<div class="seccion-titulo">🔎 Auditoría de Calidad del Modelo BIM</div>', unsafe_allow_html=True)

    q = kpi_cal

    # ── Nivel Crítico ──
    st.markdown("#### 🔴 Nivel Crítico — Bloquea cálculos")
    c1, c2, c3, c4 = st.columns(4)
    metricas_crit = [
        (c1, "Sin longitud válida",  q["sin_longitud"],  q["sin_longitud"]/q["total"]*100),
        (c2, "Sin diámetro válido",  q["sin_diametro"],  q["sin_diametro"]/q["total"]*100),
        (c3, "Sin fase definida",    q["sin_fase"],      q["sin_fase"]/q["total"]*100),
        (c4, "IDs duplicados",       q["ids_duplicados"],q["ids_duplicados"]/q["total"]*100),
    ]
    for col, label, val, pct in metricas_crit:
        color = "🔴" if val > 0 else "🟢"
        with col:
            st.metric(f"{color} {label}", f"{val:,}", f"{pct:.2f}% del total")

    st.markdown("<br>", unsafe_allow_html=True)

    # Score crítico visual
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
        st.markdown("- 🔴 **0–60** → Modelo NO confiable, revisar en Revit")
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
    with c1:
        st.metric("🟡 Elementos sin precio asignado", f"{q['sin_precio']:,}",
                  f"{q['sin_precio']/q['total']*100:.2f}% del total")
    with c2:
        st.metric("🟡 Elementos sin nombre de sistema", f"{q['sin_sistema']:,}",
                  f"{q['sin_sistema']/q['total']*100:.2f}% del total")

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Nivel No Crítico ──
    st.markdown("#### 🔵 Nivel No Crítico — Campos decorativos / informativos")
    st.metric("🔵 Sin Categoría de Sistema", f"{q['sin_cat_sistema']:,}",
              f"{q['sin_cat_sistema']/q['total']*100:.2f}% del total")

    st.markdown("---")

    # ── Distribución de integridad por categoría ──
    st.markdown('<div class="seccion-titulo">📊 Distribución del Modelo por Categoría y Estado</div>', unsafe_allow_html=True)

    dist = df.groupby(["categoria","estado"]).size().reset_index(name="count")
    fig = px.bar(dist, x="categoria", y="count", color="estado",
                 color_discrete_map={"DEMOLIDO":"#64748b","NUEVO":"#1a56db","PERSISTENTE":"#93c5fd","DESCONOCIDO":"#dc2626"},
                 title="Elementos por Categoría y Estado",
                 labels={"count":"Cantidad de Elementos","categoria":"Categoría"},
                 barmode="stack", text_auto=True)
    fig.update_layout(plot_bgcolor="white", paper_bgcolor="white", height=380,
                      margin=dict(t=40, b=20, l=20, r=20))
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabla de elementos con problemas ──
    problemas = df[~df["precio_encontrado"]]
    if len(problemas) > 0:
        st.markdown('<div class="seccion-titulo">⚠️ Elementos sin precio asignado</div>', unsafe_allow_html=True)
        st.dataframe(
            problemas[["categoria","family","type","diametro","estado","cantidad"]],
            use_container_width=True
        )
    else:
        st.success("✅ Todos los elementos tienen precio asignado en el maestro.")

    # Resumen final
    st.markdown("---")
    st.markdown("##### 📋 Resumen General del Modelo")
    resumen = pd.DataFrame({
        "Categoría"   : ["Conduits", "Fittings", "Fixtures", "**TOTAL**"],
        "Total Elem." : [
            len(df[df["categoria"]=="Conduits"]),
            len(df[df["categoria"]=="Fittings"]),
            len(df[df["categoria"]=="Fixtures"]),
            len(df)
        ],
        "Con Precio"  : [
            df[(df["categoria"]=="Conduits") & df["precio_encontrado"]].shape[0],
            df[(df["categoria"]=="Fittings") & df["precio_encontrado"]].shape[0],
            df[(df["categoria"]=="Fixtures") & df["precio_encontrado"]].shape[0],
            df[df["precio_encontrado"]].shape[0],
        ],
        "Sin Precio"  : [
            df[(df["categoria"]=="Conduits") & ~df["precio_encontrado"]].shape[0],
            df[(df["categoria"]=="Fittings") & ~df["precio_encontrado"]].shape[0],
            df[(df["categoria"]=="Fixtures") & ~df["precio_encontrado"]].shape[0],
            df[~df["precio_encontrado"]].shape[0],
        ],
    })
    st.dataframe(resumen, use_container_width=True, hide_index=True)
