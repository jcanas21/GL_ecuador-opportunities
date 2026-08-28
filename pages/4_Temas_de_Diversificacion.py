"""Los temas como unidad de política: qué contiene cada uno y cuánto pesa.

Agrupa las oportunidades de los dos márgenes en los seis temas y las muestra en
un treemap de dos niveles y en dos tablas descargables. No define método propio:
consume los presets de las páginas 2 y 3 y el mapa de temas del repositorio.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st
from branding import render_dashboard_header

from preset_utils import build_page2_recommendations, build_page3_recommendations

# colores tomados de la paleta de sectores del tablero, uno por tema
THEME_COLORS = {
    "Alimentos y agroindustria": "#e5c21a",
    "Textiles, confección y muebles": "#7bc8a4",
    "Forestal, madera y papel": "#caa46b",
    "Química, salud y cuidado personal": "#b07ac9",
    "Construcción y materiales": "#c9656b",
    "Maquinaria y equipo eléctrico": "#6e8fc3",
}


def _envolver(texto: str, ancho: int = 18) -> str:
    """Parte la etiqueta en renglones, como en los treemaps de las otras páginas."""
    palabras = str(texto).split()
    if not palabras:
        return str(texto)
    lineas, actual = [], palabras[0]
    for w in palabras[1:]:
        if len(actual) + 1 + len(w) <= ancho:
            actual = f"{actual} {w}"
        else:
            lineas.append(actual)
            actual = w
    lineas.append(actual)
    return "<br>".join(lineas)


@st.cache_data(show_spinner=False)
def load_temas() -> pd.DataFrame:
    path = Path(__file__).resolve().parents[1] / "data" / "input" / "hs4_temas.csv"
    if not path.exists():
        return pd.DataFrame(columns=["hs4", "tema"])
    t = pd.read_csv(path, dtype={"hs4": str})
    t["hs4"] = t["hs4"].astype(str).str.zfill(4)
    t["tema"] = t["tema"].fillna("").astype(str).str.strip()
    return t.drop_duplicates("hs4")


@st.cache_data(show_spinner=False)
def load_cartera() -> pd.DataFrame:
    """Las oportunidades de ambos márgenes, con su tema, en un solo cuadro."""
    p2 = build_page2_recommendations("Margen Intensivo").copy()
    p2["margen"] = "Intensivo"
    p2 = p2.rename(columns={"page2_sector": "sector", "page2_score": "puntaje",
                            "page2_rank": "rango", "raw_rca": "rca"})
    p3 = build_page3_recommendations("Margen Extensivo").copy()
    p3["margen"] = "Extensivo"
    p3 = p3.rename(columns={"page3_sector": "sector", "page3_score": "puntaje",
                            "page3_rank": "rango", "candidate_raw_rca": "rca"})

    cols = ["hs4", "product_name_short", "sector", "margen", "rango", "puntaje", "rca",
            "pci", "cog", "accessible_market_size_b", "accessible_market_growth_5y"]
    c = pd.concat([p2[cols], p3[cols]], ignore_index=True)
    if c.empty:
        return c
    c["hs4"] = c["hs4"].astype(str).str.zfill(4)
    c = c.merge(load_temas(), on="hs4", how="left")
    c["tema"] = c["tema"].fillna("Sin tema asignado")
    c["crecimiento_pct"] = pd.to_numeric(c["accessible_market_growth_5y"], errors="coerce") * 100
    c["etiqueta"] = c["hs4"] + " · " + c["product_name_short"].astype(str)
    return c


render_dashboard_header(
    "Temas de Diversificación",
    "Los seis temas que agrupan las oportunidades de ambos márgenes, con su composición y su peso de mercado.",
)

cartera = load_cartera()
if cartera.empty:
    st.warning("No hay oportunidades disponibles con los presets vigentes.")
    st.stop()

resumen = (
    cartera.groupby("tema", as_index=False)
    .apply(lambda g: pd.Series({
        "Productos": int(len(g)),
        "Intensivo": int((g["margen"] == "Intensivo").sum()),
        "Extensivo": int((g["margen"] == "Extensivo").sum()),
        "Mercado accesible (USD mil M)": g["accessible_market_size_b"].sum(),
        "Crecimiento ponderado (%)": (
            (g["crecimiento_pct"] * g["accessible_market_size_b"]).sum() / g["accessible_market_size_b"].sum()
            if g["accessible_market_size_b"].sum() > 0 else 0.0
        ),
        "Complejidad media": g["pci"].mean(),
    }), include_groups=False)
    .sort_values("Mercado accesible (USD mil M)", ascending=False)
    .reset_index(drop=True)
    .rename(columns={"tema": "Tema"})
)
# el apply devuelve todo como float: los conteos vuelven a entero para que la
# tabla no muestre seis decimales en columnas que cuentan productos
for col in ("Productos", "Intensivo", "Extensivo"):
    resumen[col] = resumen[col].astype(int)

m1, m2, m3 = st.columns(3)
m1.metric("Temas", f"{cartera['tema'].nunique()}")
m2.metric("Oportunidades", f"{len(cartera)}")
m3.metric("Mercado accesible (USD mil M)", f"{cartera['accessible_market_size_b'].sum():,.1f}")

# ── treemap de dos niveles ──────────────────────────────────────────────────
st.subheader("Composición de los temas")
st.caption(
    "Cada bloque es un tema y cada recuadro interior un producto. El área es proporcional "
    "al mercado accesible. Haga clic en un tema para abrirlo y en el título para volver."
)

cartera["etiqueta_env"] = cartera["etiqueta"].map(_envolver)

fig = px.treemap(
    cartera,
    path=["tema", "etiqueta_env"],
    values="accessible_market_size_b",
    color="tema",
    color_discrete_map=THEME_COLORS,
    hover_data={
        "margen": True,
        "sector": True,
        "puntaje": ":.3f",
        "accessible_market_size_b": ":.3f",
        "crecimiento_pct": ":.1f",
        "pci": ":.3f",
        "tema": False,
        "etiqueta_env": False,
    },
    title=(
        f"Oportunidades por tema (n = {len(cartera)} productos en {cartera['tema'].nunique()} temas | "
        f"Mercado Accesible total = {cartera['accessible_market_size_b'].sum():,.1f} B USD) "
        "| tamaño = mercado accesible (miles de millones USD) | color = tema"
    ),
)
fig.update_traces(
    textinfo="label",
    textfont=dict(size=18, color="#ffffff"),
    marker=dict(line=dict(width=1, color="rgba(255,255,255,0.45)")),
)
fig.update_layout(margin=dict(t=60, l=10, r=10, b=95), height=700)
st.plotly_chart(fig, use_container_width=True)

# ── tabla por tema ──────────────────────────────────────────────────────────
st.subheader("Resumen por tema")
st.dataframe(
    resumen.style.format({
        "Mercado accesible (USD mil M)": "{:,.1f}",
        "Crecimiento ponderado (%)": "{:,.1f}",
        "Complejidad media": "{:,.2f}",
    }),
    use_container_width=True, hide_index=True,
)
st.download_button(
    "Descargar el resumen por tema",
    data=resumen.to_csv(index=False).encode("utf-8-sig"),
    file_name="temas_resumen.csv", mime="text/csv", use_container_width=True,
)

# ── tabla de productos ──────────────────────────────────────────────────────
st.subheader("Oportunidades por tema")
temas_elegidos = st.multiselect(
    "Temas", sorted(cartera["tema"].unique()), default=sorted(cartera["tema"].unique())
)
detalle = cartera[cartera["tema"].isin(temas_elegidos)].copy()

tabla = (
    detalle[["tema", "margen", "rango", "hs4", "product_name_short", "sector", "puntaje",
             "rca", "pci", "cog", "accessible_market_size_b", "crecimiento_pct"]]
    .sort_values(["tema", "margen", "rango"])
    .rename(columns={
        "tema": "Tema", "margen": "Margen", "rango": "Rango en su margen", "hs4": "HS4",
        "product_name_short": "Producto", "sector": "Sector", "puntaje": "Puntaje",
        "rca": "RCA", "pci": "Complejidad", "cog": "Potencial de reconfiguración",
        "accessible_market_size_b": "Mercado accesible (USD mil M)",
        "crecimiento_pct": "Crecimiento del mercado (%)",
    })
    .reset_index(drop=True)
)
st.caption(
    f"{len(tabla)} oportunidades. El puntaje se normaliza dentro de cada margen, "
    "de modo que no es comparable entre el intensivo y el extensivo."
)
st.dataframe(
    tabla.style.format({
        "Puntaje": "{:,.3f}", "RCA": "{:,.2f}", "Complejidad": "{:,.2f}",
        "Potencial de reconfiguración": "{:,.3f}",
        "Mercado accesible (USD mil M)": "{:,.2f}", "Crecimiento del mercado (%)": "{:,.1f}",
    }),
    use_container_width=True, hide_index=True, height=520,
)
st.download_button(
    "Descargar las oportunidades por tema",
    data=tabla.to_csv(index=False).encode("utf-8-sig"),
    file_name="temas_oportunidades.csv", mime="text/csv", use_container_width=True,
)
