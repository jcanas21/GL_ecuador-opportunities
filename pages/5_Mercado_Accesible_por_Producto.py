import pandas as pd
import plotly.express as px
import streamlit as st
from branding import render_dashboard_header

from data_utils import load_accessible_market_destinations_by_product, load_top_exporters_for_product_markets
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


def build_country_name_map() -> dict[str, str]:
    gm = px.data.gapminder()[["iso_alpha", "country"]].drop_duplicates().copy()
    mapping = dict(zip(gm["iso_alpha"], gm["country"]))
    mapping.update(
        {
            "ARE": "Emiratos Arabes Unidos",
            "ARM": "Armenia",
            "AZE": "Azerbaiyan",
            "BLR": "Belarus",
            "CYP": "Chipre",
            "EST": "Estonia",
            "GEO": "Georgia",
            "KAZ": "Kazajistan",
            "KGZ": "Kirguistan",
            "LAO": "Laos",
            "LTU": "Lituania",
            "LVA": "Letonia",
            "MDA": "Moldavia",
            "MKD": "Macedonia del Norte",
            "PNG": "Papua Nueva Guinea",
            "QAT": "Qatar",
            "RUS": "Rusia",
            "TJK": "Tayikistan",
            "TKM": "Turkmenistan",
            "UKR": "Ucrania",
            "UZB": "Uzbekistan",
        }
    )
    return mapping


PRESET_SOURCES = {
    "Página 2 · Intensivo": ("page2", "Intensivo"),
    "Página 2 · Apuestas Estratégicas (legacy)": ("page2", "Apuestas Estratégicas (legacy)"),
    "Página 3 · Candidatos seleccionados": ("page3", "Candidatos seleccionados"),
}


render_dashboard_header(
    "Mercado Accesible por Producto",
    "Seleccione un producto proveniente de un preset y explore su mercado accesible por país de destino.",
)

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
country_name_map = build_country_name_map()
dest_df["continent"] = dest_df["importer_iso"].map(continent_map).fillna("Otros")
dest_df = dest_df[dest_df["continent"].isin(CONTINENT_COLORS.keys())].copy()
if dest_df.empty:
    st.info("No se pudo asignar continente a los destinos accesibles de este producto.")
    st.stop()

dest_df["country_label"] = dest_df["importer_iso"]
dest_df["country_name"] = dest_df["importer_iso"].map(country_name_map).fillna(dest_df["importer_iso"])
dest_df["accessible_market_imports_b"] = pd.to_numeric(dest_df["accessible_market_imports"], errors="coerce").fillna(0.0) / 1_000_000_000
dest_df["accessible_market_imports_m"] = dest_df["accessible_market_imports"] / 1_000_000
total_accessible_b = float(dest_df["accessible_market_imports_b"].sum())
dest_df["share"] = dest_df["accessible_market_imports_b"] / total_accessible_b if total_accessible_b > 0 else 0.0
dest_df["market_option_label"] = dest_df["importer_iso"] + " - " + dest_df["country_name"]

metric1, metric2, metric3 = st.columns(3)
metric1.metric("Producto seleccionado", selected_hs4)
metric2.metric("Mercado accesible total (miles de millones USD)", f"{total_accessible_b:,.1f}")
metric3.metric("Destinos accesibles", f"{dest_df['importer_iso'].nunique():,}")

dl1, dl2 = st.columns(2)
dl1.download_button(
    "Descargar datos del mercado accesible",
    data=dest_df[["importer_iso", "country_name", "continent", "accessible_market_imports", "accessible_market_imports_b", "share"]]
    .to_csv(index=False)
    .encode("utf-8-sig"),
    file_name=f"mercado_accesible_{selected_hs4}_2024.csv",
    mime="text/csv",
    use_container_width=True,
)

selected_market_iso = None
selected_market_name = "Todos los mercados accesibles"
selected_importers = tuple(dest_df["importer_iso"].astype(str).str.upper().tolist())

continent_order = ["Africa", "America", "Asia", "Europa", "Oceania"]
dest_df["continent"] = pd.Categorical(dest_df["continent"], categories=continent_order, ordered=True)
dest_df = dest_df.sort_values(["continent", "accessible_market_imports_b"], ascending=[True, False]).reset_index(drop=True)

fig = px.treemap(
    dest_df,
    path=["country_label"],
    values="accessible_market_imports_b",
    color="continent",
    color_discrete_map=CONTINENT_COLORS,
    custom_data=["importer_iso", "country_name", "continent", "accessible_market_imports_b", "accessible_market_imports_m", "share"],
)
fig.update_traces(
    textfont=dict(color="white", size=16),
    texttemplate="<b>%{label}</b><br>$%{customdata[4]:,.0f}M",
    hovertemplate=(
        "País: %{customdata[1]} (%{customdata[0]})<br>"
        "Continente: %{customdata[2]}<br>"
        "Mercado accesible: %{customdata[3]:.1f} B USD<br>"
        "Participación: %{customdata[5]:.1%}<extra></extra>"
    ),
    marker=dict(line=dict(color="rgba(255,255,255,0.65)", width=0.8)),
    tiling=dict(pad=3),
    sort=False,
)
fig.update_layout(
    title=f"Treemap del mercado accesible para {selected_product_label} | Fuente: {source_label}",
    margin=dict(t=70, l=8, r=8, b=48),
    height=880,
    legend_title_text="Continente",
    legend=dict(orientation="h", yanchor="top", y=-0.03, xanchor="center", x=0.5),
)
st.plotly_chart(fig, use_container_width=True)

market_options = ["Todos los mercados accesibles"] + dest_df["market_option_label"].tolist()
selected_market_option = st.selectbox(
    "Mercado para treemap de competidores",
    market_options,
    index=0,
    key=f"market_selector_{selected_hs4}",
)
if selected_market_option != "Todos los mercados accesibles":
    selected_market_iso = selected_market_option.split(" - ", 1)[0].strip().upper()
    selected_importers = (selected_market_iso,)
    row = dest_df.loc[dest_df["importer_iso"] == selected_market_iso].head(1)
    if not row.empty:
        selected_market_name = f"{row.iloc[0]['country_name']} ({selected_market_iso})"

st.caption(f"Mercado seleccionado para treemap de competidores: **{selected_market_name}**")

competitors_df = load_top_exporters_for_product_markets(selected_hs4, selected_importers, focus_year=2024, top_n=20).copy()
competitors_df["exporter_name"] = competitors_df["exporter_iso"].map(country_name_map).fillna(competitors_df["exporter_iso"])
competitors_df["continent"] = competitors_df["exporter_iso"].map(continent_map).fillna("Otros")
competitors_df = competitors_df[competitors_df["continent"].isin(CONTINENT_COLORS.keys())].copy()
competitors_df["exporter_label"] = competitors_df["exporter_iso"]

if competitors_df.empty:
    st.info("No hay datos de exportadores para el mercado seleccionado.")
    st.stop()

comp_total_m = float(competitors_df["export_value_m"].sum())
comp1, comp2, comp3 = st.columns(3)
comp1.metric("Exportadores mostrados", f"{len(competitors_df):,}")
comp2.metric("Exportaciones acumuladas (M USD)", f"{comp_total_m:,.1f}")
comp3.metric("Cobertura del top 20", f"{competitors_df['market_share'].sum():.1%}")

dl2.download_button(
    "Descargar datos de competidores",
    data=competitors_df[["rank", "exporter_iso", "exporter_name", "continent", "export_value", "export_value_m", "market_share"]]
    .to_csv(index=False)
    .encode("utf-8-sig"),
    file_name=f"competidores_{selected_hs4}_{selected_market_iso or 'todos'}_2024.csv",
    mime="text/csv",
    use_container_width=True,
)

fig_comp = px.treemap(
    competitors_df,
    path=["exporter_label"],
    values="export_value_m",
    color="continent",
    color_discrete_map=CONTINENT_COLORS,
    custom_data=["exporter_iso", "exporter_name", "continent", "export_value_m", "market_share", "rank"],
)
fig_comp.update_traces(
    textfont=dict(color="white", size=16),
    texttemplate="<b>%{label}</b><br>$%{customdata[3]:,.0f}M",
    hovertemplate=(
        "Exportador: %{customdata[1]} (%{customdata[0]})<br>"
        "Continente: %{customdata[2]}<br>"
        "Exportaciones al mercado: %{customdata[3]:.1f} M USD<br>"
        "Participación en el mercado: %{customdata[4]:.1%}<br>"
        "Ranking: %{customdata[5]}<extra></extra>"
    ),
    marker=dict(line=dict(color="rgba(255,255,255,0.65)", width=0.8)),
    tiling=dict(pad=3),
    sort=False,
)
fig_comp.update_layout(
    title=f"Treemap de competidores para {selected_market_name} | Producto {selected_product_label}",
    margin=dict(t=70, l=8, r=8, b=48),
    height=880,
    legend_title_text="Continente",
    legend=dict(orientation="h", yanchor="top", y=-0.03, xanchor="center", x=0.5),
)
st.plotly_chart(fig_comp, use_container_width=True)
