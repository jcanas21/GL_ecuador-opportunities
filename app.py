from pathlib import Path

import pandas as pd
import streamlit as st


def render_guide_and_glossary() -> None:
    st.title("Ecuador Export Opportunities Dashboard")
    st.caption("Guide and glossary for the V1 dashboard pages (HS92 4-digit).")

    st.markdown("## Page 2: Opportunity Analysis")
    st.markdown(
        """
The **Opportunity Analysis** page (Page 2) ranks HS92 4-digit products by combining two dimensions:

- **Feasibility**: how realistic it is for Ecuador to compete now.
- **Attractiveness**: how valuable the opportunity is if Ecuador expands in that product.

You can:
- Filter products by accessible market size, RCA, sector, accessible-market growth, density percentile, and Ecuador export floor.
- Reweight each component of feasibility and attractiveness.
- Rebalance overall strategy between feasibility and attractiveness.
- Explore a ranked product table and sector treemap.
"""
    )

    st.markdown("## Page 3: Anchored Proximity Analysis")
    st.markdown(
        """
The **Anchored Proximity Analysis** page starts from a set of anchor products and maps the candidate products that are most proximate to them.

You can:
- Filter anchor-candidate links by sector, proximity rank, accessible market, anchor density percentile, and anchor sections.
- Visualize the network as a **Sankey chart** from anchors to candidates.
- Rank candidate products using the same feasibility-versus-attractiveness logic used in the main dashboard.
- Explore a candidate table and a candidate treemap sized by **Accessible Market**.
"""
    )

    st.markdown("## Page 4: Comparison")
    st.markdown(
        """
The **Comparison** page contrasts the preset recommendations produced by:

- **Apuestas Estrategicas** from Page 2
- **Top Anchored Candidates** from Page 3

You can:
- See how much the two recommendation lists overlap.
- Identify products that appear only in one methodology.
- Compare preset ranks, accessible market size, WNAI, PCI and COG side by side.
"""
    )

    st.markdown("## How Scores Are Built")
    st.markdown(
        """
- Component variables are normalized (z-score) for score construction.
- **Feasibility Index** combines: RCA continuous, density, effective exporters, WNAI percentile.
- **Attractiveness Index** combines: PCI, COG, accessible market growth (5y), accessible market size.
- **Combined Opportunity Score** rebalances feasibility and attractiveness by your strategic slider, then rescales to 0-1 for ranking.
"""
    )

    st.markdown("## Variable Glossary (Main Page)")
    st.caption("Brief definitions plus interpretation guidance for the key technical variables.")
    glossary = pd.DataFrame(
        [
            {"Variable": "RCA", "Brief Definition": "Revealed Comparative Advantage: Ecuador's export share in a product divided by the world's export share in that product.", "How to Read It": "Greater than 1 = Ecuador is relatively specialized; less than 1 = weaker specialization.", "Unit / Scale": "Ratio"},
            {"Variable": "RCA Continuous", "Brief Definition": "Continuous RCA signal used inside the feasibility score. In the complexity pipeline, the RCA-based continuous input is the transformed version of raw RCA.", "How to Read It": "Higher means stronger revealed specialization without collapsing the signal to a binary threshold.", "Unit / Scale": "Continuous"},
            {"Variable": "Density (Raw)", "Brief Definition": "Product-space proximity to Ecuador's current capabilities.", "How to Read It": "Higher means the product is closer to what Ecuador already knows how to export.", "Unit / Scale": "Continuous"},
            {"Variable": "Density Percentile", "Brief Definition": "Relative rank of Ecuador's density vs other countries for the same product (year 2024).", "How to Read It": "Calculation by product: percentile = (rank_density - 1) / (N - 1), where rank uses average rank for ties and N is number of countries in that product. 0.80 means Ecuador is above ~80% of countries in that product's density.", "Unit / Scale": "0-1"},
            {"Variable": "Distance Travelled", "Brief Definition": "Weighted average bilateral distance travelled by product, using bilateral export values between origin x and destination y as weights.", "How to Read It": "Higher means exports of that product are concentrated in farther destination markets.", "Unit / Scale": "Distance units (from bilateral distance file)"},
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
            {"Variable": "Accessible Market Size (B USD)", "Brief Definition": "Accessible demand proxy based on Ecuador's network-positioned market reach.", "How to Read It": "Higher suggests more demand is realistically reachable.", "Unit / Scale": "Billion USD"},
            {"Variable": "Accessible-to-Market Ratio", "Brief Definition": "Accessible market size divided by total global market size.", "How to Read It": "Higher means a larger share of world demand appears structurally reachable.", "Unit / Scale": "Percent"},
            {"Variable": "Feasibility Index", "Brief Definition": "Composite score from RCA continuous, density, effective exporters, and WNAI percentile.", "How to Read It": "Higher means easier/less risky entry given current capabilities and network.", "Unit / Scale": "0-1"},
            {"Variable": "Attractiveness Index", "Brief Definition": "Composite score from PCI, COG, accessible market growth, and accessible market size.", "How to Read It": "Higher means stronger upside and strategic value.", "Unit / Scale": "0-1"},
            {"Variable": "Combined Opportunity Score", "Brief Definition": "Final score that blends feasibility and attractiveness using user-defined balance and weights.", "How to Read It": "Higher = better overall opportunity under current strategy settings.", "Unit / Scale": "0-1"},
        ]
    )
    st.dataframe(glossary, use_container_width=True, hide_index=True)

    st.markdown("## Algebra and Interpretation")
    st.markdown("### Density Percentile")
    st.latex(r"\mathrm{DensityPercentile}_{z,i} = \frac{\mathrm{rank}_i(Density_{z,i})-1}{N_i-1}")
    st.markdown("- `z`: country (Ecuador in this dashboard), `i`: product.")
    st.markdown("- `rank_i(Density_{z,i})`: rank of Ecuador's density within the cross-country distribution for product `i` (average rank for ties).")
    st.markdown("- `N_i`: number of countries available for product `i`.")
    st.markdown("- Interpretation: 0.80 means Ecuador's density is above roughly 80% of countries for that same product.")

    st.markdown("### Distance Travelled (by product)")
    st.latex(r"\mathrm{DistanceTravelled}_i = \sum_y \left( Distance_{x,y} \times \frac{X_{x,y,i}}{\sum_y X_{x,y,i}} \right)")
    st.markdown("- `X_{x,y,i}`: bilateral exports of product `i` from origin `x` to destination `y`.")
    st.markdown("- Interpretation: weighted average distance travelled by product, where bilateral export value is the weight.")

    st.markdown("### Accessible Market Size")
    st.latex(
        r"\mathrm{AccessibleMarket}_{z,i} = \sum_{y \in \mathcal{A}_{z,i}} M_{i,y}"
    )
    st.latex(
        r"\mathcal{A}_{z,i} = \left\{ y : Distance_{z,y} \le \mathrm{DistanceTravelled}_{z,i}\ \mathrm{or}\ X_{z,y,i} \ge 100{,}000{,}000 \right\}"
    )
    st.markdown("- `z`: exporter, `i`: product, `y`: destination market.")
    st.markdown("- A market is accessible if it is within the product's observed distance profile **or** if the exporter already sells at least USD 100M of that product to that partner.")
    st.markdown("- Interpretation: total demand in markets that are geographically reachable or already commercially proven at meaningful scale.")

    st.markdown("### WNAI (Weighted Network Alignment Index)")
    st.latex(
        r"\mathrm{WNAI}_{z,i} = \sum_y \left[ \left( \frac{X_{z,y}/M_y}{X_z/WT} \right) \times \left( \frac{M_{i,y}}{M_y} \right) \times GDPShare_y \right]"
    )
    st.markdown("- `z`: exporter (Ecuador in this dashboard), `i`: product, `y`: partner market.")
    st.markdown("- First term: relative pipe thickness (where exporter over-indexes vs world average).")
    st.markdown("- Second term: product relevance in each partner's import basket.")
    st.markdown("- Third term: partner economic weight.")
    st.markdown("- Interpretation: higher WNAI means Ecuador's strongest trade links are better aligned with large, product-relevant markets.")


st.set_page_config(
    page_title="Ecuador Opportunities",
    page_icon=":bar_chart:",
    layout="wide",
)

pages = [
    st.Page(render_guide_and_glossary, title="Guide and glossary", icon=":material/menu_book:", default=True),
    st.Page(Path("pages/1_Opportunity_Analysis.py"), title="Opportunity Analysis", icon=":material/insights:"),
    st.Page(Path("pages/3_Anchored_Proximity_Analysis.py"), title="Anchored Proximity Analysis", icon=":material/account_tree:"),
    st.Page(Path("pages/4_Comparison.py"), title="Comparison", icon=":material/compare_arrows:"),
]
pg = st.navigation(pages, position="sidebar", expanded=True)
pg.run()
