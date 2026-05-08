from pathlib import Path

import pandas as pd
import streamlit as st


def render_guide_and_glossary() -> None:
    st.title("Ecuador Export Opportunities Dashboard")
    st.caption("Guide and glossary for the V1 Opportunity Analysis page (HS92 4-digit).")

    st.markdown("## What This Dashboard Does")
    st.markdown(
        """
The **Opportunity Analysis** page ranks HS92 4-digit products by combining two dimensions:

- **Feasibility**: how realistic it is for Ecuador to compete now.
- **Attractiveness**: how valuable the opportunity is if Ecuador expands in that product.

You can:
- Filter products by market size, RCA, sector, growth, density percentile, and Ecuador export floor.
- Reweight each component of feasibility and attractiveness.
- Rebalance overall strategy between feasibility and attractiveness.
- Explore a ranked product table and sector treemap.
"""
    )

    st.markdown("## How Scores Are Built")
    st.markdown(
        """
- Component variables are normalized (z-score) for score construction.
- **Feasibility Index** combines: transformed RCA, density, effective exporters, WNAI percentile.
- **Attractiveness Index** combines: PCI, COG, global market growth (5y), potential market size share.
- **Combined Opportunity Score** rebalances feasibility and attractiveness by your strategic slider, then rescales to 0-1 for ranking.
"""
    )

    st.markdown("## Variable Glossary (Main Page)")
    glossary = pd.DataFrame(
        [
            {"Variable": "HS4", "Meaning": "HS92 4-digit product code", "Where Used": "Scatter, table, treemap", "Unit / Scale": "Code"},
            {"Variable": "Product", "Meaning": "Short product description", "Where Used": "Scatter, table, treemap", "Unit / Scale": "Text"},
            {"Variable": "Sector", "Meaning": "Product sector classification", "Where Used": "Filters, color encoding", "Unit / Scale": "Category"},
            {"Variable": "Raw RCA", "Meaning": "Revealed comparative advantage based on export shares", "Where Used": "Filter, table, tooltip", "Unit / Scale": "Ratio"},
            {"Variable": "Transformed RCA", "Meaning": "Bounded RCA transformation used in feasibility construction", "Where Used": "Feasibility index", "Unit / Scale": "0-1"},
            {"Variable": "Density (Raw)", "Meaning": "Product-space relatedness to existing capabilities", "Where Used": "Table, tooltip", "Unit / Scale": "Continuous"},
            {"Variable": "Density Percentile", "Meaning": "Relative density rank across products", "Where Used": "Filter, table, tooltip", "Unit / Scale": "0-1"},
            {"Variable": "Effective Exporters", "Meaning": "Effective number of exporters (inverse concentration)", "Where Used": "Feasibility, table, tooltip", "Unit / Scale": "Count-like index"},
            {"Variable": "WNAI Percentile", "Meaning": "Weighted Network Alignment percentile rank for Ecuador", "Where Used": "Feasibility, table", "Unit / Scale": "0-100"},
            {"Variable": "WNAI Lead", "Meaning": "Ecuador WNAI percentile minus median of top competitors", "Where Used": "Table", "Unit / Scale": "Percentile points"},
            {"Variable": "PCI", "Meaning": "Product Complexity Index", "Where Used": "Attractiveness, table, tooltip", "Unit / Scale": "Continuous"},
            {"Variable": "COG", "Meaning": "Complexity outlook gain metric", "Where Used": "Attractiveness, table, tooltip", "Unit / Scale": "Continuous"},
            {"Variable": "Global Market Growth % (5y)", "Meaning": "5-year CAGR of global trade for the product", "Where Used": "Attractiveness, filters, table", "Unit / Scale": "Percent"},
            {"Variable": "Ecuador Export Growth % (5y)", "Meaning": "5-year CAGR of Ecuador exports for the product", "Where Used": "Filter, table, tooltip", "Unit / Scale": "Percent"},
            {"Variable": "Ecuador Current Exports (M USD)", "Meaning": "Ecuador exports of the product in 2024", "Where Used": "Filter, table", "Unit / Scale": "Million USD"},
            {"Variable": "Ecuador Exporter Rank (2024)", "Meaning": "Ecuador’s global rank by export value for the product", "Where Used": "Table", "Unit / Scale": "Rank"},
            {"Variable": "Absolute Market Share Change (pp)", "Meaning": "Ecuador global share change from 2020 to 2024", "Where Used": "Table", "Unit / Scale": "Percentage points"},
            {"Variable": "Global Market Share", "Meaning": "Product share in total world trade (2024)", "Where Used": "Tooltip, table", "Unit / Scale": "Percent"},
            {"Variable": "Total Trade (B USD)", "Meaning": "Global product trade in 2024", "Where Used": "Filter, tooltip, table, treemap option", "Unit / Scale": "Billion USD"},
            {"Variable": "Potential Market Size (B USD)", "Meaning": "Distance-feasible demand proxy aggregated for the product", "Where Used": "Table, treemap option, tooltip", "Unit / Scale": "Billion USD"},
            {"Variable": "Potential-to-Market Ratio", "Meaning": "Potential market size divided by total market size", "Where Used": "Table, tooltip", "Unit / Scale": "Percent"},
            {"Variable": "Distance Travelled", "Meaning": "Import-weighted partner distance metric", "Where Used": "Dot-size option, tooltip", "Unit / Scale": "Distance index"},
            {"Variable": "Feasibility Index", "Meaning": "Weighted score of feasibility components", "Where Used": "Scatter X-axis, table", "Unit / Scale": "0-1"},
            {"Variable": "Attractiveness Index", "Meaning": "Weighted score of attractiveness components", "Where Used": "Scatter Y-axis, table", "Unit / Scale": "0-1"},
            {"Variable": "Combined Opportunity Score", "Meaning": "Final ranking score after strategic balance", "Where Used": "Ranking and treemap hover", "Unit / Scale": "0-1"},
        ]
    )
    st.dataframe(glossary, use_container_width=True, hide_index=True)


st.set_page_config(
    page_title="Ecuador Opportunities",
    page_icon=":bar_chart:",
    layout="wide",
)

pages = [
    st.Page(render_guide_and_glossary, title="Guide and glossary", icon=":material/menu_book:", default=True),
    st.Page(Path("pages/1_Opportunity_Analysis.py"), title="Opportunity Analysis", icon=":material/insights:"),
]
pg = st.navigation(pages, position="sidebar", expanded=True)
pg.run()
