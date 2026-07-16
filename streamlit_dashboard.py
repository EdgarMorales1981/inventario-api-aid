import os
from pathlib import Path
from datetime import datetime

import requests
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


# =====================================================
# CONFIGURACIÓN GENERAL
# =====================================================

API_URL = os.getenv(
    "INVENTARIO_API_URL",
    "https://inventario-api-aid.onrender.com"
)

LOGO_AID = Path("desktop/assets/aid_for_life_blue.png")
LOGO_LUCHEMOS = Path("desktop/assets/luchemos logo.png")

st.set_page_config(
    page_title="Dashboard Inventario AID",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded"
)


# =====================================================
# ESTILOS
# =====================================================

st.markdown(
    """
    <style>
        .stApp {
            background-color: #f4f6f8;
        }

        .block-container {
            padding-top: 1.2rem;
            padding-bottom: 2rem;
        }

        .header-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fbff 100%);
            border: 1px solid #e5e7eb;
            border-radius: 24px;
            padding: 26px 30px;
            margin-bottom: 24px;
            box-shadow: 0 8px 26px rgba(0, 0, 0, 0.05);
        }

        .logo-box {
            background-color: #ffffff;
            border: 1px solid #eef2f7;
            border-radius: 18px;
            padding: 12px;
            height: 135px;
            display: flex;
            align-items: center;
            justify-content: center;
        }

        .logo-placeholder {
            background-color: #f9fafb;
            border: 1px dashed #d1d5db;
            border-radius: 18px;
            padding: 18px;
            text-align: center;
            color: #9ca3af;
            font-size: 13px;
        }

        .main-title {
            font-size: 38px;
            font-weight: 900;
            color: #1877f2;
            text-align: center;
            margin: 0;
            line-height: 1.1;
        }

        .subtitle {
            font-size: 15px;
            color: #6b7280;
            text-align: center;
            margin-top: 10px;
            line-height: 1.5;
        }

        .system-badge {
            display: inline-block;
            background-color: #e7f3ff;
            color: #1877f2;
            border: 1px solid #bfdbfe;
            border-radius: 999px;
            padding: 7px 14px;
            font-size: 13px;
            font-weight: 700;
            margin-bottom: 12px;
        }

        .title-center {
            text-align: center;
            padding-top: 8px;
        }

        .section-title {
            font-size: 22px;
            font-weight: 850;
            color: #111827;
            margin-top: 20px;
            margin-bottom: 12px;
        }

        .small-note {
            color: #6b7280;
            font-size: 13px;
        }

        div[data-testid="stMetric"] {
            background-color: #ffffff;
            border: 1px solid #e5e7eb;
            padding: 18px;
            border-radius: 16px;
            box-shadow: 0 6px 16px rgba(0,0,0,0.04);
        }

        div[data-testid="stMetricLabel"] {
            font-size: 14px;
            color: #6b7280;
        }

        div[data-testid="stMetricValue"] {
            font-size: 28px;
            font-weight: 850;
            color: #111827;
        }

        .footer {
            text-align: center;
            color: #9ca3af;
            font-size: 13px;
            margin-top: 30px;
            padding: 16px;
        }
    </style>
    """,
    unsafe_allow_html=True
)


# =====================================================
# FUNCIONES DE API
# =====================================================

def normalizar_respuesta(payload):
    if isinstance(payload, dict) and "data" in payload:
        return payload.get("data") or []

    if isinstance(payload, list):
        return payload

    return []


@st.cache_data(ttl=60, show_spinner=False)
def consultar_api(endpoint: str):
    url = f"{API_URL}{endpoint}"

    response = requests.get(url, timeout=30)
    response.raise_for_status()

    return response.json()


def cargar_datos():
    errores = []

    try:
        insumos_json = consultar_api("/insumos/")
        insumos = normalizar_respuesta(insumos_json)
    except Exception as error:
        insumos = []
        errores.append(f"Insumos: {error}")

    try:
        recepciones_json = consultar_api("/recepciones/")
        recepciones = normalizar_respuesta(recepciones_json)
    except Exception as error:
        recepciones = []
        errores.append(f"Recepciones: {error}")

    try:
        despachos_json = consultar_api("/despachos/")
        despachos = normalizar_respuesta(despachos_json)
    except Exception as error:
        despachos = []
        errores.append(f"Despachos: {error}")

    return insumos, recepciones, despachos, errores


# =====================================================
# TRANSFORMACIÓN DE DATOS
# =====================================================

def crear_dataframe(lista):
    if not lista:
        return pd.DataFrame()

    return pd.DataFrame(lista)


def convertir_numerico(df, columnas):
    for columna in columnas:
        if columna in df.columns:
            df[columna] = pd.to_numeric(df[columna], errors="coerce").fillna(0)

    return df


def convertir_fecha(df, columnas):
    for columna in columnas:
        if columna in df.columns:
            df[columna] = pd.to_datetime(
                df[columna],
                errors="coerce",
                utc=True
            ).dt.tz_convert(None)

    return df


def normalizar_bool(valor):
    if isinstance(valor, bool):
        return valor

    texto = str(valor).strip().lower()

    if texto in ["true", "1", "activo", "yes", "si", "sí"]:
        return True

    if texto in ["false", "0", "inactivo", "no"]:
        return False

    return True


def preparar_insumos(df):
    if df.empty:
        return df

    df = convertir_numerico(df, ["cantidad"])
    df = convertir_fecha(df, ["fecha_vencimiento", "created_at"])

    if "categoria" not in df.columns:
        df["categoria"] = "sin_categoria"

    if "presentacion" not in df.columns:
        df["presentacion"] = ""

    if "unidad_medida" not in df.columns:
        df["unidad_medida"] = ""

    if "descripcion" not in df.columns:
        df["descripcion"] = ""

    if "activo" not in df.columns:
        if "status" in df.columns:
            df["activo"] = df["status"].astype(str).str.lower().eq("activo")
        else:
            df["activo"] = True

    df["activo"] = df["activo"].apply(normalizar_bool)

    return df


def preparar_recepciones(df):
    if df.empty:
        return df

    df = convertir_numerico(df, ["cantidad", "stock_anterior", "stock_nuevo"])
    df = convertir_fecha(df, ["fecha_recepcion", "created_at"])

    if "fecha_recepcion" not in df.columns and "created_at" in df.columns:
        df["fecha_recepcion"] = df["created_at"]

    if "status" not in df.columns:
        df["status"] = "recibido"

    return df


def preparar_despachos(df):
    if df.empty:
        return df

    df = convertir_fecha(df, ["fecha_despacho", "fecha_cierre", "created_at"])

    if "fecha_despacho" not in df.columns and "created_at" in df.columns:
        df["fecha_despacho"] = df["created_at"]

    if "status" not in df.columns:
        df["status"] = ""

    return df


def construir_items_despachados(despachos):
    filas = []

    for despacho in despachos:
        despacho_id = despacho.get("id")
        codigo = despacho.get("codigo_despacho")
        fecha = despacho.get("fecha_despacho") or despacho.get("created_at")
        entregado_a = despacho.get("entregado_a")
        despachado_por = despacho.get("despachado_por")
        status = despacho.get("status")

        items = despacho.get("items") or []

        for item in items:
            filas.append({
                "despacho_id": despacho_id,
                "codigo_despacho": codigo,
                "fecha_despacho": fecha,
                "entregado_a": entregado_a,
                "despachado_por": despachado_por,
                "status_despacho": status,
                "item_id": item.get("id"),
                "insumo_id": item.get("insumo_id"),
                "nombre": item.get("nombre"),
                "unidad_medida": item.get("unidad_medida"),
                "cantidad": item.get("cantidad"),
                "presentacion": item.get("presentacion"),
                "categoria": item.get("categoria"),
                "stock_anterior": item.get("stock_anterior"),
                "stock_nuevo": item.get("stock_nuevo"),
            })

    df = pd.DataFrame(filas)

    if df.empty:
        return df

    df = convertir_numerico(
        df,
        ["cantidad", "stock_anterior", "stock_nuevo"]
    )

    df = convertir_fecha(df, ["fecha_despacho"])

    return df


def formato_numero(valor):
    try:
        return f"{float(valor):,.0f}"
    except Exception:
        return "0"


# =====================================================
# HEADER CORREGIDO CON LOGOS
# =====================================================

st.markdown('<div class="header-card">', unsafe_allow_html=True)

col_logo_aid, col_titulo, col_logo_luchemos = st.columns([1.2, 3.8, 1.2])

with col_logo_aid:
    st.markdown('<div class="logo-box">', unsafe_allow_html=True)

    if LOGO_AID.exists():
        st.image(str(LOGO_AID), width=180)
    else:
        st.markdown(
            '<div class="logo-placeholder">Logo Aid For Life no encontrado</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

with col_titulo:
    st.markdown(
        """
        <div class="title-center">
            <div class="system-badge">Sistema de Inventario Humanitario</div>
            <h1 class="main-title">Dashboard de Inventario</h1>
            <p class="subtitle">
                Visualización ejecutiva de insumos, recepciones, despachos,
                stock actual, movimientos, alertas y trazabilidad operativa.
            </p>
        </div>
        """,
        unsafe_allow_html=True
    )

with col_logo_luchemos:
    st.markdown('<div class="logo-box">', unsafe_allow_html=True)

    if LOGO_LUCHEMOS.exists():
        st.image(str(LOGO_LUCHEMOS), width=170)
    else:
        st.markdown(
            '<div class="logo-placeholder">Logo Luchemos por la Vida no encontrado</div>',
            unsafe_allow_html=True
        )

    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)


# =====================================================
# SIDEBAR
# =====================================================

st.sidebar.title("Panel de control")
st.sidebar.caption("Dashboard solo de visualización")

if st.sidebar.button("🔄 Recargar datos"):
    st.cache_data.clear()
    st.rerun()

st.sidebar.markdown("---")
st.sidebar.success("Datos conectados correctamente")

umbral_stock_bajo = st.sidebar.number_input(
    "Umbral de stock bajo",
    min_value=0,
    value=5,
    step=1
)

dias_vencimiento = st.sidebar.number_input(
    "Alerta de vencimiento en días",
    min_value=1,
    value=90,
    step=1
)


# =====================================================
# CARGA DE DATOS
# =====================================================

with st.spinner("Consultando API y preparando dashboard..."):
    insumos_raw, recepciones_raw, despachos_raw, errores = cargar_datos()

df_insumos = preparar_insumos(crear_dataframe(insumos_raw))
df_recepciones = preparar_recepciones(crear_dataframe(recepciones_raw))
df_despachos = preparar_despachos(crear_dataframe(despachos_raw))
df_items_despachados = construir_items_despachados(despachos_raw)

if errores:
    st.warning("Algunos datos no pudieron cargarse:")
    for error in errores:
        st.write(f"- {error}")


# =====================================================
# FILTROS
# =====================================================

st.sidebar.markdown("---")
st.sidebar.subheader("Filtros")

categorias_disponibles = []

if not df_insumos.empty and "categoria" in df_insumos.columns:
    categorias_disponibles = sorted(
        df_insumos["categoria"].dropna().astype(str).unique().tolist()
    )

categorias_seleccionadas = st.sidebar.multiselect(
    "Categoría",
    options=categorias_disponibles,
    default=categorias_disponibles
)

texto_busqueda = st.sidebar.text_input(
    "Buscar insumo",
    placeholder="Nombre, descripción, presentación..."
)

solo_activos = st.sidebar.checkbox(
    "Mostrar solo insumos activos",
    value=True
)

df_insumos_filtrado = df_insumos.copy()

if not df_insumos_filtrado.empty:
    if categorias_seleccionadas and "categoria" in df_insumos_filtrado.columns:
        df_insumos_filtrado = df_insumos_filtrado[
            df_insumos_filtrado["categoria"].astype(str).isin(categorias_seleccionadas)
        ]

    if solo_activos and "activo" in df_insumos_filtrado.columns:
        df_insumos_filtrado = df_insumos_filtrado[
            df_insumos_filtrado["activo"] == True
        ]

    if texto_busqueda:
        texto = texto_busqueda.lower().strip()

        columnas_busqueda = [
            columna for columna in [
                "nombre",
                "descripcion",
                "presentacion",
                "categoria",
                "unidad_medida"
            ]
            if columna in df_insumos_filtrado.columns
        ]

        mascara = pd.Series(False, index=df_insumos_filtrado.index)

        for columna in columnas_busqueda:
            mascara = mascara | df_insumos_filtrado[columna].astype(str).str.lower().str.contains(
                texto,
                na=False
            )

        df_insumos_filtrado = df_insumos_filtrado[mascara]


# =====================================================
# MÉTRICAS PRINCIPALES
# =====================================================

total_insumos = len(df_insumos_filtrado)

stock_total = (
    df_insumos_filtrado["cantidad"].sum()
    if "cantidad" in df_insumos_filtrado.columns and not df_insumos_filtrado.empty
    else 0
)

total_categorias = (
    df_insumos_filtrado["categoria"].nunique()
    if "categoria" in df_insumos_filtrado.columns and not df_insumos_filtrado.empty
    else 0
)

total_recepciones = len(df_recepciones)

cantidad_recibida = (
    df_recepciones["cantidad"].sum()
    if "cantidad" in df_recepciones.columns and not df_recepciones.empty
    else 0
)

total_despachos = len(df_despachos)
total_items_despachados = len(df_items_despachados)

cantidad_despachada = (
    df_items_despachados["cantidad"].sum()
    if "cantidad" in df_items_despachados.columns and not df_items_despachados.empty
    else 0
)

stock_bajo = 0

if not df_insumos_filtrado.empty and "cantidad" in df_insumos_filtrado.columns:
    stock_bajo = len(
        df_insumos_filtrado[df_insumos_filtrado["cantidad"] <= umbral_stock_bajo]
    )


st.markdown('<div class="section-title">Resumen general</div>', unsafe_allow_html=True)

m1, m2, m3, m4 = st.columns(4)

m1.metric("Insumos registrados", formato_numero(total_insumos))
m2.metric("Stock total actual", formato_numero(stock_total))
m3.metric("Categorías", formato_numero(total_categorias))
m4.metric("Stock bajo", formato_numero(stock_bajo))

m5, m6, m7, m8 = st.columns(4)

m5.metric("Recepciones", formato_numero(total_recepciones))
m6.metric("Cantidad recibida", formato_numero(cantidad_recibida))
m7.metric("Despachos", formato_numero(total_despachos))
m8.metric("Cantidad despachada", formato_numero(cantidad_despachada))


# =====================================================
# GRÁFICOS DE INVENTARIO
# =====================================================

st.markdown('<div class="section-title">Inventario actual</div>', unsafe_allow_html=True)

col1, col2 = st.columns(2)

with col1:
    if not df_insumos_filtrado.empty and "categoria" in df_insumos_filtrado.columns:
        stock_categoria = (
            df_insumos_filtrado
            .groupby("categoria", as_index=False)["cantidad"]
            .sum()
            .sort_values("cantidad", ascending=False)
        )

        fig = px.bar(
            stock_categoria,
            x="categoria",
            y="cantidad",
            text_auto=True,
            title="Stock total por categoría"
        )

        fig.update_layout(
            xaxis_title="Categoría",
            yaxis_title="Cantidad",
            height=420
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay datos de inventario para graficar.")

with col2:
    if not df_insumos_filtrado.empty and "categoria" in df_insumos_filtrado.columns:
        conteo_categoria = (
            df_insumos_filtrado
            .groupby("categoria", as_index=False)
            .size()
            .rename(columns={"size": "total"})
            .sort_values("total", ascending=False)
        )

        fig = px.pie(
            conteo_categoria,
            names="categoria",
            values="total",
            hole=0.45,
            title="Distribución de insumos por categoría"
        )

        fig.update_layout(height=420)

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay categorías disponibles.")


col3, col4 = st.columns(2)

with col3:
    if not df_insumos_filtrado.empty:
        top_stock = (
            df_insumos_filtrado
            .sort_values("cantidad", ascending=False)
            .head(15)
        )

        fig = px.bar(
            top_stock,
            x="cantidad",
            y="nombre",
            orientation="h",
            text_auto=True,
            title="Top 15 insumos con mayor stock"
        )

        fig.update_layout(
            yaxis_title="Insumo",
            xaxis_title="Cantidad",
            height=520,
            yaxis={"categoryorder": "total ascending"}
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay insumos disponibles.")

with col4:
    if not df_insumos_filtrado.empty:
        stock_bajo_df = (
            df_insumos_filtrado[df_insumos_filtrado["cantidad"] <= umbral_stock_bajo]
            .sort_values("cantidad", ascending=True)
            .head(15)
        )

        if not stock_bajo_df.empty:
            fig = px.bar(
                stock_bajo_df,
                x="cantidad",
                y="nombre",
                orientation="h",
                text_auto=True,
                title=f"Insumos con stock bajo ≤ {umbral_stock_bajo}"
            )

            fig.update_layout(
                yaxis_title="Insumo",
                xaxis_title="Cantidad",
                height=520,
                yaxis={"categoryorder": "total ascending"}
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("No hay insumos por debajo del umbral de stock bajo.")
    else:
        st.info("No hay insumos disponibles.")


# =====================================================
# MOVIMIENTOS
# =====================================================

st.markdown('<div class="section-title">Movimientos de inventario</div>', unsafe_allow_html=True)

col5, col6 = st.columns(2)

with col5:
    if not df_recepciones.empty and "fecha_recepcion" in df_recepciones.columns:
        entradas_fecha = (
            df_recepciones
            .dropna(subset=["fecha_recepcion"])
            .assign(fecha=lambda x: x["fecha_recepcion"].dt.date)
            .groupby("fecha", as_index=False)["cantidad"]
            .sum()
            .sort_values("fecha")
        )

        if not entradas_fecha.empty:
            fig = px.bar(
                entradas_fecha,
                x="fecha",
                y="cantidad",
                text_auto=True,
                title="Recepciones por fecha"
            )

            fig.update_layout(
                xaxis_title="Fecha",
                yaxis_title="Cantidad recibida",
                height=420
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay fechas de recepción disponibles.")
    else:
        st.info("No hay recepciones para graficar.")

with col6:
    if not df_items_despachados.empty and "fecha_despacho" in df_items_despachados.columns:
        salidas_fecha = (
            df_items_despachados
            .dropna(subset=["fecha_despacho"])
            .assign(fecha=lambda x: x["fecha_despacho"].dt.date)
            .groupby("fecha", as_index=False)["cantidad"]
            .sum()
            .sort_values("fecha")
        )

        if not salidas_fecha.empty:
            fig = px.bar(
                salidas_fecha,
                x="fecha",
                y="cantidad",
                text_auto=True,
                title="Despachos por fecha"
            )

            fig.update_layout(
                xaxis_title="Fecha",
                yaxis_title="Cantidad despachada",
                height=420
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay fechas de despacho disponibles.")
    else:
        st.info("No hay despachos para graficar.")


col7, col8 = st.columns(2)

with col7:
    if not df_items_despachados.empty:
        top_salidas = (
            df_items_despachados
            .groupby("nombre", as_index=False)["cantidad"]
            .sum()
            .sort_values("cantidad", ascending=False)
            .head(15)
        )

        fig = px.bar(
            top_salidas,
            x="cantidad",
            y="nombre",
            orientation="h",
            text_auto=True,
            title="Top 15 insumos más despachados"
        )

        fig.update_layout(
            yaxis_title="Insumo",
            xaxis_title="Cantidad despachada",
            height=520,
            yaxis={"categoryorder": "total ascending"}
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay ítems despachados.")

with col8:
    entradas_producto = pd.DataFrame(columns=["nombre", "entradas"])
    salidas_producto = pd.DataFrame(columns=["nombre", "salidas"])

    if not df_recepciones.empty and "nombre" in df_recepciones.columns:
        entradas_producto = (
            df_recepciones
            .groupby("nombre", as_index=False)["cantidad"]
            .sum()
            .rename(columns={"cantidad": "entradas"})
        )

    if not df_items_despachados.empty and "nombre" in df_items_despachados.columns:
        salidas_producto = (
            df_items_despachados
            .groupby("nombre", as_index=False)["cantidad"]
            .sum()
            .rename(columns={"cantidad": "salidas"})
        )

    if not entradas_producto.empty or not salidas_producto.empty:
        movimiento_producto = pd.merge(
            entradas_producto,
            salidas_producto,
            on="nombre",
            how="outer"
        ).fillna(0)

        movimiento_producto["movimiento_total"] = (
            movimiento_producto["entradas"] + movimiento_producto["salidas"]
        )

        movimiento_producto = (
            movimiento_producto
            .sort_values("movimiento_total", ascending=False)
            .head(15)
        )

        fig = go.Figure()

        fig.add_trace(
            go.Bar(
                x=movimiento_producto["nombre"],
                y=movimiento_producto["entradas"],
                name="Entradas"
            )
        )

        fig.add_trace(
            go.Bar(
                x=movimiento_producto["nombre"],
                y=movimiento_producto["salidas"],
                name="Salidas"
            )
        )

        fig.update_layout(
            title="Entradas vs salidas por insumo",
            xaxis_title="Insumo",
            yaxis_title="Cantidad",
            barmode="group",
            height=520,
            xaxis_tickangle=-45
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay movimientos disponibles.")


# =====================================================
# ESTADO DE DESPACHOS
# =====================================================

st.markdown('<div class="section-title">Control de despachos</div>', unsafe_allow_html=True)

col9, col10 = st.columns(2)

with col9:
    if not df_despachos.empty and "status" in df_despachos.columns:
        status_despachos = (
            df_despachos
            .groupby("status", as_index=False)
            .size()
            .rename(columns={"size": "total"})
            .sort_values("total", ascending=False)
        )

        fig = px.bar(
            status_despachos,
            x="status",
            y="total",
            text_auto=True,
            title="Despachos por status"
        )

        fig.update_layout(
            xaxis_title="Status",
            yaxis_title="Cantidad",
            height=400
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay despachos para graficar.")

with col10:
    if not df_items_despachados.empty and "entregado_a" in df_items_despachados.columns:
        entregas_destino = (
            df_items_despachados
            .groupby("entregado_a", as_index=False)["cantidad"]
            .sum()
            .sort_values("cantidad", ascending=False)
            .head(10)
        )

        fig = px.bar(
            entregas_destino,
            x="cantidad",
            y="entregado_a",
            orientation="h",
            text_auto=True,
            title="Top destinos / beneficiarios por cantidad despachada"
        )

        fig.update_layout(
            yaxis_title="Destino",
            xaxis_title="Cantidad",
            height=400,
            yaxis={"categoryorder": "total ascending"}
        )

        st.plotly_chart(fig, use_container_width=True)
    else:
        st.info("No hay destinos de despacho disponibles.")


# =====================================================
# ALERTAS
# =====================================================

st.markdown('<div class="section-title">Alertas operativas</div>', unsafe_allow_html=True)

alerta1, alerta2 = st.columns(2)

with alerta1:
    st.subheader("Stock bajo")

    if not df_insumos_filtrado.empty:
        tabla_stock_bajo = (
            df_insumos_filtrado[df_insumos_filtrado["cantidad"] <= umbral_stock_bajo]
            .sort_values("cantidad", ascending=True)
        )

        columnas_stock = [
            columna for columna in [
                "id",
                "nombre",
                "cantidad",
                "unidad_medida",
                "presentacion",
                "categoria",
                "activo"
            ]
            if columna in tabla_stock_bajo.columns
        ]

        if not tabla_stock_bajo.empty:
            st.dataframe(
                tabla_stock_bajo[columnas_stock],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success("No hay insumos con stock bajo.")
    else:
        st.info("No hay insumos para evaluar stock bajo.")

with alerta2:
    st.subheader("Vencimientos próximos")

    if not df_insumos_filtrado.empty and "fecha_vencimiento" in df_insumos_filtrado.columns:
        hoy = pd.Timestamp(datetime.now().date())
        limite = hoy + pd.Timedelta(days=int(dias_vencimiento))

        vencimientos = df_insumos_filtrado[
            (df_insumos_filtrado["fecha_vencimiento"].notna()) &
            (df_insumos_filtrado["fecha_vencimiento"] <= limite)
        ].copy()

        if not vencimientos.empty:
            vencimientos["dias_para_vencer"] = (
                vencimientos["fecha_vencimiento"] - hoy
            ).dt.days

            vencimientos = vencimientos.sort_values("fecha_vencimiento", ascending=True)

            columnas_vencimiento = [
                columna for columna in [
                    "id",
                    "nombre",
                    "cantidad",
                    "fecha_vencimiento",
                    "dias_para_vencer",
                    "categoria"
                ]
                if columna in vencimientos.columns
            ]

            st.dataframe(
                vencimientos[columnas_vencimiento],
                use_container_width=True,
                hide_index=True
            )
        else:
            st.success(f"No hay vencimientos en los próximos {dias_vencimiento} días.")
    else:
        st.info("No hay columna de fecha de vencimiento disponible.")


# =====================================================
# TABLAS DETALLADAS
# =====================================================

st.markdown('<div class="section-title">Detalle de datos</div>', unsafe_allow_html=True)

tab1, tab2, tab3, tab4 = st.tabs([
    "📦 Insumos",
    "📥 Recepciones",
    "📤 Despachos",
    "🧾 Ítems despachados"
])

with tab1:
    st.subheader("Listado de insumos")

    if not df_insumos_filtrado.empty:
        columnas = [
            columna for columna in [
                "id",
                "nombre",
                "descripcion",
                "unidad_medida",
                "presentacion",
                "cantidad",
                "categoria",
                "fecha_vencimiento",
                "activo",
                "created_at"
            ]
            if columna in df_insumos_filtrado.columns
        ]

        st.dataframe(
            df_insumos_filtrado[columnas],
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay insumos para mostrar.")

with tab2:
    st.subheader("Historial de recepciones")

    if not df_recepciones.empty:
        columnas = [
            columna for columna in [
                "id",
                "insumo_id",
                "nombre",
                "cantidad",
                "presentacion",
                "stock_anterior",
                "stock_nuevo",
                "recibido_por",
                "status",
                "observacion",
                "fecha_recepcion",
                "created_at"
            ]
            if columna in df_recepciones.columns
        ]

        if "fecha_recepcion" in columnas:
            ordenar_por = "fecha_recepcion"
        elif "created_at" in columnas:
            ordenar_por = "created_at"
        else:
            ordenar_por = columnas[0]

        st.dataframe(
            df_recepciones[columnas].sort_values(
                by=ordenar_por,
                ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay recepciones para mostrar.")

with tab3:
    st.subheader("Historial de despachos")

    if not df_despachos.empty:
        columnas = [
            columna for columna in [
                "id",
                "codigo_despacho",
                "entregado_a",
                "despachado_por",
                "observacion",
                "status",
                "qr_activo",
                "fecha_despacho",
                "fecha_cierre",
                "created_at"
            ]
            if columna in df_despachos.columns
        ]

        if "fecha_despacho" in columnas:
            ordenar_por = "fecha_despacho"
        elif "created_at" in columnas:
            ordenar_por = "created_at"
        else:
            ordenar_por = columnas[0]

        st.dataframe(
            df_despachos[columnas].sort_values(
                by=ordenar_por,
                ascending=False
            ),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("No hay despachos para mostrar.")

    with tab4:
        st.subheader("Detalle de ítems despachados")

        if not df_items_despachados.empty:
            columnas = [
                columna for columna in [
                    "despacho_id",
                    "codigo_despacho",
                    "fecha_despacho",
                    "entregado_a",
                    "despachado_por",
                    "insumo_id",
                    "nombre",
                    "cantidad",
                    "unidad_medida",
                    "presentacion",
                    "categoria",
                    "stock_anterior",
                    "stock_nuevo",
                    "status_despacho"
                ]
                if columna in df_items_despachados.columns
            ]

            if "fecha_despacho" in columnas:
                ordenar_por = "fecha_despacho"
            else:
                ordenar_por = columnas[0]

            st.dataframe(
                df_items_despachados[columnas].sort_values(
                    by=ordenar_por,
                    ascending=False
                ),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No hay ítems despachados para mostrar.")

# =====================================================
# PIE
# =====================================================

st.markdown(
    """
    <div class="footer">
        Sistema interno de visualización de inventario · Aid For Life · Luchemos por la Vida
    </div>
    """,
    unsafe_allow_html=True
)