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
    st.caption("Brief definitions plus interpretation guidance for the key technical variables.")
    glossary = pd.DataFrame(
        [
            {"Variable": "Raw RCA", "Brief Definition": "Revealed Comparative Advantage: Ecuador's export share in a product divided by the world's export share in that product.", "How to Read It": "Greater than 1 = Ecuador is relatively specialized; less than 1 = weaker specialization.", "Unit / Scale": "Ratio"},
            {"Variable": "Transformed RCA", "Brief Definition": "Rescaled RCA used only inside the feasibility formula to keep scores comparable with other components.", "How to Read It": "Higher means stronger contribution to feasibility after transformation.", "Unit / Scale": "Bounded index"},
            {"Variable": "Density (Raw)", "Brief Definition": "Product-space proximity to Ecuador's current capabilities.", "How to Read It": "Higher means the product is closer to what Ecuador already knows how to export.", "Unit / Scale": "Continuous"},
            {"Variable": "Density Percentile", "Brief Definition": "Relative rank of density across products.", "How to Read It": "0.80 means denser than 80% of products in the sample.", "Unit / Scale": "0-1"},
            {"Variable": "Effective Exporters", "Brief Definition": "Effective number of competing exporters in that product (competition breadth).", "How to Read It": "Higher usually implies a broader competitive field.", "Unit / Scale": "Count-like index"},
            {"Variable": "WNAI Percentile", "Brief Definition": "Weighted Network Alignment Index percentile for Ecuador versus major exporters in each product.", "How to Read It": "Higher percentile = Ecuador's trade network is better aligned with high-value demand hubs.", "Unit / Scale": "0-100"},
            {"Variable": "WNAI Lead", "Brief Definition": "Ecuador's WNAI percentile minus the median percentile of top competitors.", "How to Read It": "Positive = Ecuador leads peers; negative = Ecuador trails peers.", "Unit / Scale": "Percentile points"},
            {"Variable": "PCI", "Brief Definition": "Product Complexity Index: sophistication level of the product based on global export structures.", "How to Read It": "Higher often signals stronger long-term upgrading potential.", "Unit / Scale": "Continuous"},
            {"Variable": "COG", "Brief Definition": "Complexity Outlook Gain proxy: potential capability gain from moving into the product.", "How to Read It": "Higher suggests larger strategic learning/upgrading potential.", "Unit / Scale": "Continuous"},
            {"Variable": "Global Market Growth % (5y)", "Brief Definition": "5-year compound annual growth of world trade in the product.", "How to Read It": "Positive and higher values indicate faster-expanding global demand.", "Unit / Scale": "Percent per year"},
            {"Variable": "Country Export Growth % (5y)", "Brief Definition": "5-year compound annual growth of Ecuador's exports in the product.", "How to Read It": "Higher means Ecuador is scaling faster in that product.", "Unit / Scale": "Percent per year"},
            {"Variable": "Country Current Exports (M USD)", "Brief Definition": "Ecuador's export value in 2024 for the product.", "How to Read It": "Higher means a larger current export base.", "Unit / Scale": "Million USD"},
            {"Variable": "Country Exporter Rank (2024)", "Brief Definition": "Ecuador's global rank among exporters of that product by value.", "How to Read It": "Lower rank number is better (e.g., 3 is better than 20).", "Unit / Scale": "Rank"},
            {"Variable": "Absolute Market Share Change (pp)", "Brief Definition": "Change in Ecuador's world market share from 2020 to 2024.", "How to Read It": "Positive = Ecuador gained share; negative = lost share.", "Unit / Scale": "Percentage points"},
            {"Variable": "Global Market Share", "Brief Definition": "Product's share in total world trade (2024).", "How to Read It": "Higher means the product is more important in global trade.", "Unit / Scale": "Percent"},
            {"Variable": "Total Trade (B USD)", "Brief Definition": "Total world trade value of the product in 2024.", "How to Read It": "Higher means a larger global market.", "Unit / Scale": "Billion USD"},
            {"Variable": "Potential Market Size (B USD)", "Brief Definition": "Accessible demand proxy based on Ecuador's network-positioned market reach.", "How to Read It": "Higher suggests more demand is realistically reachable.", "Unit / Scale": "Billion USD"},
            {"Variable": "Potential-to-Market Ratio", "Brief Definition": "Potential market size divided by total global market size.", "How to Read It": "Higher means a larger share of world demand appears structurally reachable.", "Unit / Scale": "Percent"},
            {"Variable": "Feasibility Index", "Brief Definition": "Composite score from transformed RCA, density, effective exporters, and WNAI percentile.", "How to Read It": "Higher means easier/less risky entry given current capabilities and network.", "Unit / Scale": "0-1"},
            {"Variable": "Attractiveness Index", "Brief Definition": "Composite score from PCI, COG, global growth, and potential market size share.", "How to Read It": "Higher means stronger upside and strategic value.", "Unit / Scale": "0-1"},
            {"Variable": "Combined Opportunity Score", "Brief Definition": "Final score that blends feasibility and attractiveness using user-defined balance and weights.", "How to Read It": "Higher = better overall opportunity under current strategy settings.", "Unit / Scale": "0-1"},
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
