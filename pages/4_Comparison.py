import numpy as np
import plotly.express as px
import streamlit as st

from preset_utils import (
    PAGE2_PRESETS,
    PAGE3_PRESETS,
    build_page2_recommendations,
    build_page3_recommendations,
)


COMPARE_GROUP_COLORS = {
    "Superposición": "#2f5d74",
    "Solo preset de la Página 2": "#b07ac9",
    "Solo preset de la Página 3": "#74c5c6",
}


st.title("Comparación")
st.caption("Compare las recomendaciones producidas por los perfiles vigentes de la Página 2 y la Página 3.")

csel1, csel2 = st.columns(2)
page2_preset = csel1.selectbox("Perfil de la Página 2", list(PAGE2_PRESETS.keys()), index=0)
page3_preset = csel2.selectbox("Perfil de la Página 3", list(PAGE3_PRESETS.keys()), index=0)

page2_df = build_page2_recommendations(page2_preset)
page3_df = build_page3_recommendations(page3_preset)

if page2_df.empty and page3_df.empty:
    st.warning("No hay datos de comparación disponibles para los presets seleccionados.")
    st.stop()

comparison = page2_df.merge(
    page3_df,
    on="hs4",
    how="outer",
    suffixes=("_page2", "_page3"),
)

comparison["product_name_short"] = comparison["product_name_short_page2"].combine_first(comparison["product_name_short_page3"])
comparison["sector"] = comparison["page2_sector"].combine_first(comparison["page3_sector"]).fillna("Otros")
comparison["accessible_market_size_b"] = comparison["accessible_market_size_b_page2"].combine_first(
    comparison["accessible_market_size_b_page3"]
)
comparison["accessible_market_growth_5y"] = comparison["accessible_market_growth_5y_page2"].combine_first(
    comparison["accessible_market_growth_5y_page3"]
)
comparison["pci"] = comparison["pci_page2"].combine_first(comparison["pci_page3"])
comparison["cog"] = comparison["cog_page2"].combine_first(comparison["cog_page3"])
comparison["dai_percentile"] = comparison["page2_dai_pct"].combine_first(comparison["page3_dai_pct"])
comparison["dai_raw"] = comparison["page2_dai_raw"].combine_first(comparison["page3_dai_raw"])

in_page2 = comparison["page2_rank"].notna()
in_page3 = comparison["page3_rank"].notna()
comparison["comparison_group"] = np.select(
    [in_page2 & in_page3, in_page2 & ~in_page3, ~in_page2 & in_page3],
    ["Superposición", "Solo preset de la Página 2", "Solo preset de la Página 3"],
    default="Sin clasificar",
)
comparison["best_rank"] = comparison[["page2_rank", "page3_rank"]].min(axis=1, skipna=True)
comparison = comparison.sort_values(
    ["comparison_group", "best_rank", "accessible_market_size_b"],
    ascending=[True, True, False],
).reset_index(drop=True)

summary = comparison["comparison_group"].value_counts().rename_axis("comparison_group").reset_index(name="count")

c1, c2, c3, c4 = st.columns(4)
c1.metric(page2_preset, f"{len(page2_df):,}")
c2.metric(page3_preset, f"{len(page3_df):,}")
c3.metric("Superposición", f"{int((comparison['comparison_group'] == 'Superposición').sum()):,}")
c4.metric("Unión de recomendaciones", f"{len(comparison):,}")

fig = px.bar(
    summary,
    x="comparison_group",
    y="count",
    color="comparison_group",
    color_discrete_map=COMPARE_GROUP_COLORS,
    title=f"Superposición de recomendaciones: {page2_preset} vs {page3_preset}",
)
fig.update_layout(showlegend=False, xaxis_title="", yaxis_title="Productos")
st.plotly_chart(fig, use_container_width=True)

view = st.selectbox(
    "Vista de comparación",
    ["Todas las recomendaciones", "Solo superposición", f"Solo {page2_preset}", f"Solo {page3_preset}"],
    index=0,
)

view_map = {
    "Todas las recomendaciones": comparison,
    "Solo superposición": comparison[comparison["comparison_group"] == "Superposición"],
    f"Solo {page2_preset}": comparison[comparison["comparison_group"] == "Solo preset de la Página 2"],
    f"Solo {page3_preset}": comparison[comparison["comparison_group"] == "Solo preset de la Página 3"],
}
table = view_map[view].copy()
table["accessible_market_growth_5y"] = table["accessible_market_growth_5y"] * 100

st.subheader("Tabla comparativa de recomendaciones")
st.dataframe(
    table[
        [
            "comparison_group",
            "hs4",
            "product_name_short",
            "sector",
            "page2_rank",
            "page2_score",
            "page3_rank",
            "page3_score",
            "accessible_market_size_b",
            "accessible_market_growth_5y",
            "dai_percentile",
            "dai_raw",
            "pci",
            "cog",
        ]
    ],
    use_container_width=True,
    hide_index=True,
    column_config={
        "comparison_group": st.column_config.TextColumn("Grupo de comparación"),
        "hs4": st.column_config.TextColumn("HS4"),
        "product_name_short": st.column_config.TextColumn("Producto"),
        "sector": st.column_config.TextColumn("Sector"),
        "page2_rank": st.column_config.NumberColumn(f"Ranking {page2_preset}", format="%.0f"),
        "page2_score": st.column_config.NumberColumn(f"Puntaje {page2_preset}", format="%.4f"),
        "page3_rank": st.column_config.NumberColumn(f"Ranking {page3_preset}", format="%.0f"),
        "page3_score": st.column_config.NumberColumn(f"Puntaje {page3_preset}", format="%.4f"),
        "accessible_market_size_b": st.column_config.NumberColumn("Tamaño del mercado accesible (miles de millones USD)", format="%.3f"),
        "accessible_market_growth_5y": st.column_config.NumberColumn("Crecimiento del mercado accesible % (5 años)", format="%.2f%%"),
        "dai_percentile": st.column_config.NumberColumn("Percentil DAI", format="%.1f"),
        "dai_raw": st.column_config.NumberColumn("DAI (bruto)", format="%.3f"),
        "pci": st.column_config.NumberColumn("PCI", format="%.3f"),
        "cog": st.column_config.NumberColumn("COG", format="%.3f"),
    },
)

overlap = comparison[comparison["comparison_group"] == "Superposición"].copy()
if not overlap.empty:
    overlap["rank_gap"] = overlap["page3_rank"] - overlap["page2_rank"]
    st.subheader("Diagnóstico de superposición")
    st.dataframe(
        overlap[
            [
                "hs4",
                "product_name_short",
                "sector",
                "page2_rank",
                "page3_rank",
                "rank_gap",
                "accessible_market_size_b",
                "dai_percentile",
                "dai_raw",
            ]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "hs4": st.column_config.TextColumn("HS4"),
            "product_name_short": st.column_config.TextColumn("Producto"),
            "sector": st.column_config.TextColumn("Sector"),
            "page2_rank": st.column_config.NumberColumn(f"Ranking {page2_preset}", format="%.0f"),
            "page3_rank": st.column_config.NumberColumn(f"Ranking {page3_preset}", format="%.0f"),
            "rank_gap": st.column_config.NumberColumn(f"Brecha de ranking ({page3_preset} - {page2_preset})", format="%.0f"),
            "accessible_market_size_b": st.column_config.NumberColumn("Tamaño del mercado accesible (miles de millones USD)", format="%.3f"),
            "dai_percentile": st.column_config.NumberColumn("Percentil DAI", format="%.1f"),
            "dai_raw": st.column_config.NumberColumn("DAI (bruto)", format="%.3f"),
        },
    )
else:
    st.info("No hay productos superpuestos entre las dos listas de recomendaciones seleccionadas.")
