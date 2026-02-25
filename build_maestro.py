"""
=========================================================
SISTEMA DE ANÁLISIS BIM – TRAMO 1 | Metro 80, Medellín
=========================================================
Paso 1: Construcción del DataFrame Maestro Consolidado

Autor: Datos exportados desde Revit
=========================================================
"""

import pandas as pd
import numpy as np
import os

# ─────────────────────────────────────────────────────────
# 0. CONFIGURACIÓN DE RUTAS
# ─────────────────────────────────────────────────────────
# Cambia BASE_DIR a la carpeta donde tienes tus Excel
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

RUTAS = {
    "conduits_inicial" : os.path.join(BASE_DIR, "Tramo1_Conduits_EstadoInicial.xlsx"),
    "conduits_final"   : os.path.join(BASE_DIR, "Tramo1_Conduits_EstadoFinal.xlsx"),
    "fittings_inicial" : os.path.join(BASE_DIR, "Tramo1_Fittings_EstadoInicial.xlsx"),
    "fittings_final"   : os.path.join(BASE_DIR, "Tramo1_Fittings_EstadoFinal.xlsx"),
    "fixtures_inicial" : os.path.join(BASE_DIR, "Tramo1_Fixtures_EstadoInicial.xlsx"),
    "fixtures_final"   : os.path.join(BASE_DIR, "Tramo1_Fixtures_EstadoFinal.xlsx"),
    "maestro_precios"  : os.path.join(BASE_DIR, "Maestro_Precios_Tramo1.xlsx"),
}

# Factor de costo de demolición (25% del valor del elemento nuevo)
FACTOR_DEMOLICION = 0.25


# ─────────────────────────────────────────────────────────
# 1. CARGA DE ARCHIVOS
# ─────────────────────────────────────────────────────────
def cargar_datos(rutas: dict) -> dict:
    """Carga todos los Excel y retorna un diccionario de DataFrames."""
    datos = {}
    for nombre, ruta in rutas.items():
        datos[nombre] = pd.read_excel(ruta)
        print(f"  ✓ {nombre:20s} → {datos[nombre].shape[0]:,} filas")
    return datos


# ─────────────────────────────────────────────────────────
# 2. NORMALIZACIÓN GENERAL
# ─────────────────────────────────────────────────────────
def normalizar_texto(serie: pd.Series) -> pd.Series:
    """Limpia espacios y estandariza mayúsculas/minúsculas."""
    return serie.astype(str).str.strip()


# ─────────────────────────────────────────────────────────
# 3. PROCESAMIENTO POR CATEGORÍA
# ─────────────────────────────────────────────────────────

def procesar_conduits(df_inicial: pd.DataFrame, df_final: pd.DataFrame) -> pd.DataFrame:
    """
    Procesa tuberías (Conduits).
    
    - Unidad de cantidad: longitud en metros (columna 'Length')
    - Join con maestro: por Type + Diameter(Trade Size)
    - Estado:
        * Inicial + Phase Demolished = 'Demolición' → DEMOLIDO
        * Final   + Phase Created   = 'Nueva Construcción' → NUEVO
        * Final   + Phase Created   = 'Existente'          → PERSISTENTE
    """
    #  Diagnóstico de unidades de Length
    # Revit puede exportar en mm, cm, ft o m según la plantilla de exportación.
    # Para telecomunicaciones urbanas, el promedio por elemento debería ser < 50 m.
    length_vals = pd.to_numeric(df_final["Length"], errors="coerce").dropna()
    if len(length_vals) > 0:
        length_mean = length_vals.mean()
        length_max  = length_vals.max()
        print(f"  📏 Length conduits: media={length_mean:.1f}  max={length_max:.1f}")
        if length_mean > 500:
            print(f"     ⚠️  Media muy alta — posibles mm en lugar de m en el Excel de Revit.")

    registros = []

    # --- DEMOLIDOS (vienen del estado inicial) ---
    demolidos = df_inicial[df_inicial["Phase Demolished"] == "Demolición"].copy()
    for _, fila in demolidos.iterrows():
        registros.append({
            "categoria"   : "Conduits",
            "family"      : normalizar_texto(pd.Series([fila["Family"]]))[0],
            "type"        : normalizar_texto(pd.Series([fila["Type"]]))[0],
            "diametro"    : normalizar_texto(pd.Series([fila["Diameter(Trade Size)"]]))[0],
            "nombre_sistema": fila.get("NombreSistema", None),
            "categoria_sistema": fila.get("CategoriaSistema", None),
            "estado"      : "DEMOLIDO",
            "cantidad"    : fila["Length"],  # metros
            "unidad"      : "ML",
        })

    # --- NUEVOS y PERSISTENTES (vienen del estado final) ---
    for _, fila in df_final.iterrows():
        fase = str(fila.get("Phase Created", "")).strip()
        if fase == "Nueva Construcción":
            estado = "NUEVO"
        elif fase == "Existente":
            estado = "PERSISTENTE"
        else:
            estado = "DESCONOCIDO"  # para auditoría

        registros.append({
            "categoria"   : "Conduits",
            "family"      : normalizar_texto(pd.Series([fila["Family"]]))[0],
            "type"        : normalizar_texto(pd.Series([fila["Type"]]))[0],
            "diametro"    : normalizar_texto(pd.Series([fila["Diameter(Trade Size)"]]))[0],
            "nombre_sistema": fila.get("NombreSistema", None),
            "categoria_sistema": fila.get("CategoriaSistema", None),
            "estado"      : estado,
            "cantidad"    : fila["Length"],  # metros
            "unidad"      : "ML",
        })

    return pd.DataFrame(registros)


def procesar_fittings(df_inicial: pd.DataFrame, df_final: pd.DataFrame) -> pd.DataFrame:
    """
    Procesa accesorios (Fittings: codos, etc.).
    
    - Unidad de cantidad: unidades (columna 'Count', siempre = 1 por fila)
    - Join con maestro: por Family + Size
    """
    registros = []

    # --- DEMOLIDOS ---
    demolidos = df_inicial[df_inicial["Phase Demolished"] == "Demolición"].copy()
    for _, fila in demolidos.iterrows():
        registros.append({
            "categoria"   : "Fittings",
            "family"      : normalizar_texto(pd.Series([fila["Family"]]))[0],
            "type"        : normalizar_texto(pd.Series([fila["Type"]]))[0],
            "diametro"    : normalizar_texto(pd.Series([fila["Size"]]))[0],
            "nombre_sistema": fila.get("NombreSistema", None),
            "categoria_sistema": fila.get("CategoriaSistema", None),
            "estado"      : "DEMOLIDO",
            "cantidad"    : fila.get("Count", 1),
            "unidad"      : "UND",
        })

    # --- NUEVOS y PERSISTENTES ---
    for _, fila in df_final.iterrows():
        fase = str(fila.get("Phase Created", "")).strip()
        if fase == "Nueva Construcción":
            estado = "NUEVO"
        elif fase == "Existente":
            estado = "PERSISTENTE"
        else:
            estado = "DESCONOCIDO"

        registros.append({
            "categoria"   : "Fittings",
            "family"      : normalizar_texto(pd.Series([fila["Family"]]))[0],
            "type"        : normalizar_texto(pd.Series([fila["Type"]]))[0],
            "diametro"    : normalizar_texto(pd.Series([fila["Size"]]))[0],
            "nombre_sistema": fila.get("NombreSistema", None),
            "categoria_sistema": fila.get("CategoriaSistema", None),
            "estado"      : estado,
            "cantidad"    : fila.get("Count", 1),
            "unidad"      : "UND",
        })

    return pd.DataFrame(registros)


def procesar_fixtures(df_inicial: pd.DataFrame, df_final: pd.DataFrame) -> pd.DataFrame:
    """
    Procesa equipos puntuales (Fixtures: cajas, cámaras, postes).
    
    - Unidad de cantidad: unidades (columna 'Count', siempre = 1 por fila)
    - Join con maestro: solo por Family (no tienen diámetro)
    - Nota: diámetro se deja como 'N/A'
    """
    registros = []

    # --- DEMOLIDOS ---
    demolidos = df_inicial[df_inicial["Phase Demolished"] == "Demolición"].copy()
    for _, fila in demolidos.iterrows():
        registros.append({
            "categoria"   : "Fixtures",
            "family"      : normalizar_texto(pd.Series([fila["Family"]]))[0],
            "type"        : normalizar_texto(pd.Series([fila["Type"]]))[0],
            "diametro"    : "N/A",
            "nombre_sistema": fila.get("NombreSistema", None),
            "categoria_sistema": fila.get("CategoriaSistema", None),
            "estado"      : "DEMOLIDO",
            "cantidad"    : fila.get("Count", 1),
            "unidad"      : "UND",
        })

    # --- NUEVOS y PERSISTENTES ---
    for _, fila in df_final.iterrows():
        fase = str(fila.get("Phase Created", "")).strip()
        if fase == "Nueva Construcción":
            estado = "NUEVO"
        elif fase == "Existente":
            estado = "PERSISTENTE"
        else:
            estado = "DESCONOCIDO"

        registros.append({
            "categoria"   : "Fixtures",
            "family"      : normalizar_texto(pd.Series([fila["Family"]]))[0],
            "type"        : normalizar_texto(pd.Series([fila["Type"]]))[0],
            "diametro"    : "N/A",
            "nombre_sistema": fila.get("NombreSistema", None),
            "categoria_sistema": fila.get("CategoriaSistema", None),
            "estado"      : estado,
            "cantidad"    : fila.get("Count", 1),
            "unidad"      : "UND",
        })

    return pd.DataFrame(registros)


# ─────────────────────────────────────────────────────────
# 4. JOIN CON MAESTRO DE PRECIOS
# ─────────────────────────────────────────────────────────

def preparar_maestro(df_maestro: pd.DataFrame) -> pd.DataFrame:
    """
    Prepara el maestro de precios para el join.
    Normaliza nombres y crea las claves de unión.
    """
    df = df_maestro.copy()
    df["Familia"]        = df["Familia"].astype(str).str.strip()
    df["Tipo"]           = df["Tipo"].astype(str).str.strip()
    df["Tamaño_Diametro"] = df["Tamaño_Diametro"].astype(str).str.strip()

    # Clave para Conduits y Fittings: Tipo + Diámetro
    df["key_tipo_diam"] = df["Tipo"] + "|" + df["Tamaño_Diametro"]
    # Clave para Fixtures: solo Familia
    df["key_familia"]   = df["Familia"]

    return df[["Categoria", "Familia", "Tipo", "Tamaño_Diametro",
               "Unidad", "Precio_Unitario_COP",
               "key_tipo_diam", "key_familia"]]


def asignar_precios(df_consolidado: pd.DataFrame,
                    df_maestro_prep: pd.DataFrame) -> pd.DataFrame:
    """
    Une el DataFrame consolidado con el maestro de precios.
    
    Estrategia:
    - Conduits y Fittings → join por (type + diametro)
    - Fixtures→ join por (family)
    """
    df = df_consolidado.copy()

    # Crear clave de join en el consolidado
    df["key_tipo_diam"] = df["type"] + "|" + df["diametro"]
    df["key_familia"]   = df["family"]

    # Separar el maestro en dos lookup tables
    lookup_tipo_diam = df_maestro_prep.set_index("key_tipo_diam")["Precio_Unitario_COP"].to_dict()
    lookup_familia   = df_maestro_prep.set_index("key_familia")["Precio_Unitario_COP"].to_dict()

    def obtener_precio(fila):
        if fila["categoria"] in ("Conduits", "Fittings"):
            return lookup_tipo_diam.get(fila["key_tipo_diam"], np.nan)
        else:  # Fixtures
            return lookup_familia.get(fila["key_familia"], np.nan)

    df["precio_unitario"] = df.apply(obtener_precio, axis=1)

    # Registrar si el precio fue encontrado (útil para auditoría)
    df["precio_encontrado"] = df["precio_unitario"].notna()

    return df


# ─────────────────────────────────────────────────────────
# 5. CÁLCULO DE COSTOS
# ─────────────────────────────────────────────────────────

def _validar_y_limpiar(df: pd.DataFrame) -> pd.DataFrame:
    """
    Valida tipos numéricos y detecta valores imposibles ANTES de calcular costos.
    Registra en consola qué filas fueron corregidas. No elimina filas, solo las
    marca como NaN para que no contaminen los cálculos.

    Umbrales para telecomunicaciones urbanas (Metro Medellín):
      - Conduit individual > 2 000 m→ probable error de unidades (mm en vez de m)
      - Precio unitario > 5 000 M COP → valor claramente imposible
    """
    df = df.copy()

    # ── Coerción de tipos ──
    df["cantidad"]        = pd.to_numeric(df["cantidad"],        errors="coerce")
    df["precio_unitario"] = pd.to_numeric(df["precio_unitario"], errors="coerce")

    # ── Longitudes imposibles (Conduits) ──
    UMBRAL_ML = 2_000
    mask_ml = (df["categoria"] == "Conduits") & df["cantidad"].notna() & (df["cantidad"] > UMBRAL_ML)
    if mask_ml.sum() > 0:
        print(f"\n  ⚠️  {mask_ml.sum()} conduits con longitud > {UMBRAL_ML} m — posible error de unidades en Revit")
        print(df[mask_ml][["id","family","type","diametro","cantidad"]].head(5).to_string(index=False))
        df.loc[mask_ml, "cantidad"] = np.nan
        df.loc[mask_ml, "dato_corregido"] = True

    # ── Precios unitarios imposibles ──
    UMBRAL_PU = 5_000_000_000
    mask_pu = df["precio_unitario"].notna() & (df["precio_unitario"] > UMBRAL_PU)
    if mask_pu.sum() > 0:
        print(f"\n  ⚠️  {mask_pu.sum()} elementos con precio_unitario > $5 000 M COP — se anulan")
        df.loc[mask_pu, "precio_unitario"] = np.nan
        df.loc[mask_pu, "dato_corregido"] = True

    if "dato_corregido" not in df.columns:
        df["dato_corregido"] = False

    return df


def calcular_costos(df: pd.DataFrame, factor_demolicion: float = 0.25) -> pd.DataFrame:
    """
    Calcula los costos según el estado de cada elemento.

    - NUEVO→ costo_nuevo = cantidad × precio_unitario
    - DEMOLIDO→ costo_demolicion = cantidad × precio_unitario × factor_demolicion
    - PERSISTENTE → ambos costos = 0 (no genera inversión nueva)

    Incluye validación de datos para evitar overflows por errores de unidades en Revit.
    """
    df = _validar_y_limpiar(df)

    # Inicializar columnas en cero
    df["costo_nuevo"]      = 0.0
    df["costo_demolicion"] = 0.0

    mask_nuevo    = df["estado"] == "NUEVO"
    mask_demolido = df["estado"] == "DEMOLIDO"

    df.loc[mask_nuevo, "costo_nuevo"] = (
        (df.loc[mask_nuevo, "cantidad"] * df.loc[mask_nuevo, "precio_unitario"])
        .fillna(0.0)
    )
    df.loc[mask_demolido, "costo_demolicion"] = (
        (df.loc[mask_demolido, "cantidad"]
         * df.loc[mask_demolido, "precio_unitario"]
         * factor_demolicion)
        .fillna(0.0)
    )

    df["costo_total"] = df["costo_nuevo"] + df["costo_demolicion"]

    # Redondear costos a pesos enteros (COP)
    df["costo_nuevo"] = df["costo_nuevo"].round(0)
    df["costo_demolicion"] = df["costo_demolicion"].round(0)
    df["costo_total"] = df["costo_total"].round(0)

    # Reporte de rango para auditoría
    print(f"  📊 costo_total por elemento → "
          f"min=${df['costo_total'].min():,.0f}  "
          f"max=${df['costo_total'].max():,.0f}  "
          f"suma=${df['costo_total'].sum():,.0f}")

    return df


# ─────────────────────────────────────────────────────────
# 6. CONSTRUCCIÓN FINAL DEL DATAFRAME MAESTRO
# ─────────────────────────────────────────────────────────

def construir_dataframe_maestro(rutas: dict,
                                 factor_demolicion: float = FACTOR_DEMOLICION
                                 ) -> pd.DataFrame:
    """
    Función principal. Ejecuta todo el pipeline y retorna
    el DataFrame Maestro Consolidado listo para el dashboard.
    """
    print("\n📂 Cargando archivos...")
    datos = cargar_datos(rutas)

    print("\n🔧 Procesando categorías...")
    df_conduits = procesar_conduits(datos["conduits_inicial"], datos["conduits_final"])
    print(f"  ✓ Conduits  → {len(df_conduits):,} registros")

    df_fittings = procesar_fittings(datos["fittings_inicial"], datos["fittings_final"])
    print(f"  ✓ Fittings  → {len(df_fittings):,} registros")

    df_fixtures = procesar_fixtures(datos["fixtures_inicial"], datos["fixtures_final"])
    print(f"  ✓ Fixtures  → {len(df_fixtures):,} registros")

    # Unir las 3 categorías
    df_consolidado = pd.concat([df_conduits, df_fittings, df_fixtures],
                                ignore_index=True)
    df_consolidado["id"] = df_consolidado.index + 1  # ID único

    print(f"\n🔗 Total elementos consolidados: {len(df_consolidado):,}")

    print("\n💲 Asignando precios del maestro...")
    maestro_prep = preparar_maestro(datos["maestro_precios"])
    df_consolidado = asignar_precios(df_consolidado, maestro_prep)

    sin_precio = df_consolidado[~df_consolidado["precio_encontrado"]]
    if len(sin_precio) > 0:
        print(f"  ⚠️  {len(sin_precio):,} elementos sin precio encontrado")
        combos_faltantes = sin_precio.groupby(["categoria","family","type","diametro"]).size().reset_index(name="count")
        print(combos_faltantes.to_string(index=False))
    else:
        print("  ✓ Todos los elementos tienen precio asignado")

    print(f"\n💰 Calculando costos (factor demolición = {factor_demolicion*100:.0f}%)...")
    df_consolidado = calcular_costos(df_consolidado, factor_demolicion)

    # Ordenar columnas finales
    # Calcular costos aquí para que dato_corregido exista antes de ordenar columnas
    columnas_orden = [
        "id", "categoria", "family", "type", "diametro",
        "nombre_sistema", "categoria_sistema",
        "estado", "cantidad", "unidad",
        "precio_unitario", "precio_encontrado",
        "costo_nuevo", "costo_demolicion", "costo_total",
        "dato_corregido",
    ]
    # Asegurar que dato_corregido exista (se crea en calcular_costos)
    if "dato_corregido" not in df_consolidado.columns:
        df_consolidado["dato_corregido"] = False
    df_consolidado = df_consolidado[columnas_orden]

    return df_consolidado


# ─────────────────────────────────────────────────────────
# 7. RESUMEN DE KPIs (verificación rápida)
# ─────────────────────────────────────────────────────────

def imprimir_resumen_kpis(df: pd.DataFrame):
    """Imprime un resumen de los KPIs principales para verificar."""
    print("\n" + "="*55)
    print("  📊 RESUMEN KPIs – TRAMO 1")
    print("="*55)

    conduits = df[df["categoria"] == "Conduits"]

    # KPIs Técnicos (longitudes en metros)
    long_inicial  = conduits[conduits["estado"].isin(["DEMOLIDO", "PERSISTENTE"])]["cantidad"].sum()
    # Nota: longitud inicial = demolidos + persistentes (lo que había antes)
    # En realidad lo más correcto es sumar todo lo del estado inicial
    # pero aquí aproximamos: demolidos + lo que se mantiene
    long_demolida = conduits[conduits["estado"] == "DEMOLIDO"]["cantidad"].sum()
    long_nueva    = conduits[conduits["estado"] == "NUEVO"]["cantidad"].sum()
    long_persistente = conduits[conduits["estado"] == "PERSISTENTE"]["cantidad"].sum()
    long_final    = long_nueva + long_persistente
    pct_intervencion = (long_demolida + long_nueva) / (long_inicial + long_nueva) * 100 if (long_inicial + long_nueva) > 0 else 0

    print(f"\n  📐 TÉCNICOS (Conduits)")
    print(f"  Longitud Inicial    : {long_inicial:>12,.2f} m")
    print(f"  Longitud Demolida   : {long_demolida:>12,.2f} m")
    print(f"  Longitud Nueva      : {long_nueva:>12,.2f} m")
    print(f"  Longitud Persistente: {long_persistente:>12,.2f} m")
    print(f"  Longitud Final      : {long_final:>12,.2f} m")
    print(f"  % Intervención      : {pct_intervencion:>11.1f}%")

    # KPIs Económicos (todo el proyecto)
    costo_demol = df["costo_demolicion"].sum()
    costo_nuevo = df["costo_nuevo"].sum()
    inversion_total = costo_demol + costo_nuevo

    print(f"\n  💰 ECONÓMICOS (todas las categorías)")
    print(f"  Costo Demolición    : $ {costo_demol:>15,.0f}")
    print(f"  Costo Nueva Const.  : $ {costo_nuevo:>15,.0f}")
    print(f"  Inversión Total     : $ {inversion_total:>15,.0f}")

    # Conteo de estados
    print(f"\n  🔢 CONTEO POR ESTADO")
    print(df.groupby(["categoria", "estado"])["id"].count().to_string())
    print("="*55)


# ─────────────────────────────────────────────────────────
# 8. EJECUCIÓN PRINCIPAL
# ─────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("🏗️  SISTEMA DE ANÁLISIS BIM – TRAMO 1")
    print("   Construyendo DataFrame Maestro Consolidado...\n")

    df_maestro = construir_dataframe_maestro(RUTAS)

    imprimir_resumen_kpis(df_maestro)

    # Guardar el DataFrame maestro como Excel (para revisión)
    output_path = os.path.join(BASE_DIR, "DataFrame_Maestro_Tramo1.xlsx")
    df_maestro.to_excel(output_path, index=False)
    print(f"\n  ✅ DataFrame Maestro guardado en:\n     {output_path}")
    print(f"\n  Total filas: {len(df_maestro):,}")
    print(f"  Columnas   : {list(df_maestro.columns)}")
