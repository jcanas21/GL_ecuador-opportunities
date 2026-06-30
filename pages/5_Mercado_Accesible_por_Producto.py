import pandas as pd
import plotly.express as px
import streamlit as st

from data_utils import load_accessible_market_destinations_by_product
from preset_utils import (
    PAGE2_PRESETS,
    PAGE3_PRESETS,
    build_page2_recommendations,
    build_page3_recommendations,
)


CONTINENT_COLORS = {
    "Africa": "#773bd8",
    "America": "#9e4643",
    "Asia": "#6bc285",
    "Europa": "#5780b7",
    "Oceania": "#f2bc67",
}

MANUAL_CONTINENT_BY_ISO3 = {
    "ARE": "Asia",
    "ARM": "Asia",
    "AZE": "Asia",
    "BLR": "Europa",
    "CYP": "Europa",
    "EST": "Europa",
    "GEO": "Asia",
    "KAZ": "Asia",
    "KGZ": "Asia",
    "LAO": "Asia",
    "LTU": "Europa",
    "LVA": "Europa",
    "MDA": "Europa",
    "MKD": "Europa",
    "PNG": "Oceania",
    "QAT": "Asia",
    "RUS": "Europa",
    "TJK": "Asia",
    "TKM": "Asia",
    "UKR": "Europa",
    "UZB": "Asia",
}


def build_continent_map() -> dict[str, str]:
    gm = px.data.gapminder()[["iso_alpha", "continent"]].drop_duplicates().copy()
    gm["continent"] = gm["continent"].replace({"Americas": "America", "Europe": "Europa"})
    mapping = dict(zip(gm["iso_alpha"], gm["continent"]))
    mapping.update(MANUAL_CONTINENT_BY_ISO3)
    return mapping


PRESET_SOURCES = {
    "Página 2 · Intensivo": ("page2", "Intensivo"),
    "Página 2 · Apuestas Estratégicas (legacy)": ("page2", "Apuestas Estratégicas (legacy)"),
    "Página 3 · Candidatos seleccionados": ("page3", "Candidatos seleccionados"),
}


st.title("Mercado Accesible por Producto")
st.caption("Seleccione un producto proveniente de un preset y explore su mercado accesible por país de destino.")

source_label = st.selectbox("Origen del producto", list(PRESET_SOURCES.keys()), index=0)
source_type, preset_name = PRESET_SOURCES[source_label]

if source_type == "page2":
    preset_df = build_page2_recommendations(preset_name)
else:
    preset_df = build_page3_recommendations(preset_name)

if preset_df.empty:
    st.warning("No hay productos disponibles para el preset seleccionado.")
    st.stop()

product_options = (
    preset_df[["hs4", "product_name_short"]]
    .drop_duplicates()
    .sort_values(["hs4", "product_name_short"])
    .reset_index(drop=True)
)
product_options["product_label"] = product_options["hs4"].astype(str).str.zfill(4) + " - " + product_options["product_name_short"].astype(str)
product_label_to_hs4 = dict(zip(product_options["product_label"], product_options["hs4"]))

selected_product_label = st.selectbox("Producto", product_options["product_label"].tolist(), index=0)
selected_hs4 = product_label_to_hs4[selected_product_label]

dest_df = load_accessible_market_destinations_by_product(selected_hs4, focus_year=2024).copy()
if dest_df.empty:
    st.info("Este producto no tiene mercados accesibles positivos en el archivo detallado disponible.")
    st.stop()

continent_map = build_continent_map()
dest_df["continent"] = dest_df["importer_iso"].map(continent_map).fillna("Otros")
dest_df = dest_df[dest_df["continent"].isin(CONTINENT_COLORS.keys())].copy()
if dest_df.empty:
    st.info("No se pudo asignar continente a los destinos accesibles de este producto.")
    st.stop()

dest_df["country_label"] = dest_df["importer_iso"]
dest_df["accessible_market_imports_b"] = pd.to_numeric(dest_df["accessible_market_imports"], errors="coerce").fillna(0.0) / 1_000_000_000
total_accessible_b = float(dest_df["accessible_market_imports_b"].sum())
dest_df["share"] = dest_df["accessible_market_imports_b"] / total_accessible_b if total_accessible_b > 0 else 0.0

metric1, metric2, metric3 = st.columns(3)
metric1.metric("Producto seleccionado", selected_hs4)
metric2.metric("Mercado accesible total (miles de millones USD)", f"{total_accessible_b:,.1f}")
metric3.metric("Destinos accesibles", f"{dest_df['importer_iso'].nunique():,}")

continent_order = ["Africa", "America", "Asia", "Europa", "Oceania"]
dest_df["continent"] = pd.Categorical(dest_df["continent"], categories=continent_order, ordered=True)
dest_df = dest_df.sort_values(["continent", "accessible_market_imports_b"], ascending=[True, False]).reset_index(drop=True)

fig = px.treemap(
    dest_df,
    path=["continent", "country_label"],
    values="accessible_market_imports_b",
    color="continent",
    color_discrete_map=CONTINENT_COLORS,
    custom_data=["importer_iso", "accessible_market_imports_b", "share"],
)
fig.update_traces(
    textfont=dict(color="white", size=16),
    texttemplate="%{label}<br>%{value:.1f} B",
    hovertemplate=(
        "Continente: %{parent}<br>"
        "País: %{customdata[0]}<br>"
        "Mercado accesible: %{customdata[1]:.1f} B USD<br>"
        "Participación: %{customdata[2]:.1%}<extra></extra>"
    ),
    marker=dict(line=dict(color="white", width=1)),
)
fig.update_layout(
    title=f"Treemap del mercado accesible para {selected_product_label} | Fuente: {source_label}",
    margin=dict(t=70, l=10, r=10, b=10),
    height=850,
    legend_title_text="Continente",
)
st.plotly_chart(fig, use_container_width=True)

st.dataframe(
    dest_df[["continent", "importer_iso", "accessible_market_imports_b", "share"]],
    use_container_width=True,
    hide_index=True,
    column_config={
        "continent": st.column_config.TextColumn("Continente"),
        "importer_iso": st.column_config.TextColumn("País"),
        "accessible_market_imports_b": st.column_config.NumberColumn("Mercado accesible (miles de millones USD)", format="%.1f"),
        "share": st.column_config.NumberColumn("Participación", format="%.2f%%"),
    },
)
