import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from data_utils import (
    load_opportunity_dataset,
    normalize_0_1,
)


st.title("Opportunity Analysis")
st.caption("Calibrate index components, rebalance feasibility vs attractiveness, and explore product opportunities.")

df = load_opportunity_dataset()
if df.empty:
    st.warning("No data available for year 2024 / ECU in complexity_ecu_2024.csv.")
    st.stop()

pci_static_min = float(pd.to_numeric(df["pci"], errors="coerce").min())
pci_static_max = float(pd.to_numeric(df["pci"], errors="coerce").max())
if not np.isfinite(pci_static_min):
    pci_static_min = 0.0
if not np.isfinite(pci_static_max):
    pci_static_max = 1.0
if pci_static_max <= pci_static_min:
    pci_static_max = pci_static_min + 1e-6

# Static-but-robust color bounds for PCI to improve contrast in treemaps.
# Using global quantiles (from full dataset) keeps comparability across filters
# while avoiding extreme tails flattening most colors.
pci_series_all = pd.to_numeric(df["pci"], errors="coerce").replace([np.inf, -np.inf], np.nan).dropna()
if pci_series_all.empty:
    pci_color_min = pci_static_min
    pci_color_max = pci_static_max
else:
    pci_color_min = float(pci_series_all.quantile(0.02))
    pci_color_max = float(pci_series_all.quantile(0.98))
    if not np.isfinite(pci_color_min):
        pci_color_min = pci_static_min
    if not np.isfinite(pci_color_max):
        pci_color_max = pci_static_max
    if pci_color_max <= pci_color_min:
        pci_color_min = pci_static_min
        pci_color_max = pci_static_max

FEAS_COLS = ["rca_transformed_z", "density_z", "eff_num_exp_z", "alignment_weighted_percentile_z"]
ATTR_COLS = ["pci_z", "cog_z", "accessible_market_growth_5y_z", "accessible_market_size_mm"]
# Defensive schema guard for cached/legacy datasets.
for col in FEAS_COLS + ATTR_COLS + ["accessible_market_growth_5y"]:
    if col not in df.columns:
        df[col] = 0.0
SECTOR_COLORS = {
    "Services": "#b23c6f",
    "Textiles": "#7bc8a4",
    "Agriculture": "#e5c21a",
    "Stone": "#caa46b",
    "Minerals": "#a88b7d",
    "Metals": "#c9656b",
    "Chemicals": "#b07ac9",
    "Vehicles": "#7a6cc3",
    "Machinery": "#6e8fc3",
    "Electronics": "#74c5c6",
    "Other": "#2f5d74",
}


def weighted_index(frame: pd.DataFrame, cols: list[str], weights: list[float]) -> pd.Series:
    weight_sum = float(sum(weights))
    if weight_sum <= 0:
        return frame[cols].mean(axis=1)
    arr = np.column_stack([frame[c].to_numpy() for c in cols])
    w = np.array(weights, dtype=float)
    return pd.Series((arr * w).sum(axis=1) / weight_sum, index=frame.index)


defaults = {
    "w_rca": 0.00,
    "w_density": 0.70,
    "w_eff_num_exp": 0.00,
    "w_alignment_hv": 0.30,
    "w_pci": 0.35,
    "w_cog": 0.35,
    "w_growth": 0.15,
    "w_market_size": 0.15,
    "strategic_balance": 0.50,
}
for k, v in defaults.items():
    st.session_state.setdefault(k, v)

trade_max = float(df["total_trade_b"].max()) if not df.empty else 0.0
ecu_export_max = float(df["ecu_total_trade_b"].max()) if not df.empty else 0.0
ecu_export_max_m = ecu_export_max * 1000
density_pct_min_data = float(pd.to_numeric(df["density_percentile"], errors="coerce").min()) if not df.empty else 0.0
density_pct_max_data = float(pd.to_numeric(df["density_percentile"], errors="coerce").max()) if not df.empty else 1.0
density_pct_min_data = max(density_pct_min_data, 0.0)
density_pct_max_data = max(density_pct_max_data, 0.0)
if density_pct_max_data < density_pct_min_data:
    density_pct_min_data, density_pct_max_data = density_pct_max_data, density_pct_min_data
if density_pct_max_data == density_pct_min_data:
    density_pct_max_data += 0.01
density_pct_upper_bound = round(density_pct_max_data + 0.01, 2)

rca_min_data = float(pd.to_numeric(df["raw_rca"], errors="coerce").min()) if not df.empty else 0.0
rca_max_data = float(pd.to_numeric(df["raw_rca"], errors="coerce").max()) if not df.empty else 1.0
if not np.isfinite(rca_min_data):
    rca_min_data = 0.0
if not np.isfinite(rca_max_data):
    rca_max_data = 1.0
if rca_max_data < rca_min_data:
    rca_min_data, rca_max_data = rca_max_data, rca_min_data
if rca_max_data == rca_min_data:
    rca_max_data = rca_min_data + 0.01
rca_step = 0.01
rca_upper_bound = float(rca_max_data + rca_step)
sector_options = sorted(x for x in df["sector"].dropna().astype(str).unique())
product_options_df = (
    df[["hs4", "product_name_short"]]
    .dropna(subset=["hs4"])
    .copy()
    .assign(
        hs4_code=lambda d: d["hs4"].astype(str).str.zfill(4),
        product_name_short=lambda d: d["product_name_short"].fillna("").astype(str).str.strip(),
    )
    .drop_duplicates(subset=["hs4_code"])
    .sort_values("hs4_code")
)
product_options_df["hs4_label"] = product_options_df["hs4_code"] + " - " + product_options_df["product_name_short"]
product_label_to_code = dict(zip(product_options_df["hs4_label"], product_options_df["hs4_code"]))
size_choices = {
    "Accessible market size (B USD)": "accessible_market_size_b",
    "Accessible market growth (5y)": "accessible_market_growth_5y",
    "RCA": "raw_rca",
}

if "trade_min" not in st.session_state:
    st.session_state["trade_min"] = 0.0
if "ecu_export_min_m" not in st.session_state:
    prev_b = float(st.session_state.get("ecu_export_min", 0.0))
    st.session_state["ecu_export_min_m"] = prev_b * 1000
if "rca_max_filter" not in st.session_state:
    prior = st.session_state.get("rca_range", (rca_min_data, rca_max_data))
    prior_max = float(prior[1]) if isinstance(prior, (tuple, list)) and len(prior) == 2 else float(rca_max_data)
    st.session_state["rca_max_filter"] = max(0.0, prior_max)
if "rca_min_filter" not in st.session_state:
    prior = st.session_state.get("rca_range", (rca_min_data, rca_max_data))
    prior_min = float(prior[0]) if isinstance(prior, (tuple, list)) and len(prior) == 2 else 0.0
    st.session_state["rca_min_filter"] = max(0.0, prior_min)
st.session_state["rca_min_filter"] = max(0.0, float(st.session_state.get("rca_min_filter", 0.0)))
st.session_state["rca_max_filter"] = max(
    float(st.session_state["rca_min_filter"]),
    min(float(st.session_state.get("rca_max_filter", rca_upper_bound)), rca_upper_bound),
)
if "selected_sectors" not in st.session_state:
    st.session_state["selected_sectors"] = sector_options
if "excluded_product_labels" not in st.session_state:
    st.session_state["excluded_product_labels"] = []
if "above_accessible_growth_only" not in st.session_state:
    st.session_state["above_accessible_growth_only"] = False
if "size_label" not in st.session_state:
    st.session_state["size_label"] = "Accessible market growth (5y)"
if "density_pct_range" not in st.session_state:
    st.session_state["density_pct_range"] = (density_pct_min_data, density_pct_upper_bound)
if "rows_to_display" not in st.session_state:
    st.session_state["rows_to_display"] = 60
if "ignore_density_filter" not in st.session_state:
    st.session_state["ignore_density_filter"] = False
st.sidebar.header("Preset Profiles")
excluded_hs4_preset_codes = {"2711", "2710", "7108", "2709", "2713", "2701", "2603", "2616"}
excluded_labels_by_code = (
    product_options_df[product_options_df["hs4_code"].isin(excluded_hs4_preset_codes)]
    .sort_values("hs4_code")["hs4_label"]
    .tolist()
)


def _apply_profile(profile_name: str) -> None:
    # Common rules across all profiles
    st.session_state["trade_min"] = 2.0
    st.session_state["ecu_export_min_m"] = 0.0
    st.session_state["above_accessible_growth_only"] = True
    st.session_state["selected_sectors"] = sector_options
    st.session_state["excluded_product_labels"] = excluded_labels_by_code
    st.session_state["density_pct_range"] = (float(density_pct_min_data), float(density_pct_upper_bound))
    st.session_state["ignore_density_filter"] = False

    if profile_name == "intensive":
        # Consolidadas
        st.session_state["rca_min_filter"] = 1.00
        st.session_state["rca_max_filter"] = float(rca_upper_bound)
        st.session_state["ignore_density_filter"] = True
        st.session_state["strategic_balance"] = 0.80
        st.session_state["w_rca"] = 0.00
        st.session_state["w_density"] = 0.00
        st.session_state["w_eff_num_exp"] = 0.00
        st.session_state["w_alignment_hv"] = 1.00
        st.session_state["w_pci"] = 0.50
        st.session_state["w_cog"] = 0.00
        st.session_state["w_growth"] = 0.25
        st.session_state["w_market_size"] = 0.25
        st.session_state["rows_to_display"] = 20

    elif profile_name == "extensive_low_hanging":
        # Emergentes
        st.session_state["rca_min_filter"] = 0.30
        st.session_state["rca_max_filter"] = 0.99
        st.session_state["strategic_balance"] = 0.50
        st.session_state["w_rca"] = 0.35
        st.session_state["w_density"] = 0.35
        st.session_state["w_eff_num_exp"] = 0.00
        st.session_state["w_alignment_hv"] = 0.30
        st.session_state["w_pci"] = 0.35
        st.session_state["w_cog"] = 0.35
        st.session_state["w_growth"] = 0.15
        st.session_state["w_market_size"] = 0.15
        st.session_state["rows_to_display"] = 20

    elif profile_name == "extensive_strategic":
        # Apuestas Estrategicas
        st.session_state["rca_min_filter"] = 0.00
        st.session_state["rca_max_filter"] = 0.29
        st.session_state["density_pct_range"] = (
            max(0.30, float(density_pct_min_data)),
            min(0.40, float(density_pct_upper_bound)),
        )
        st.session_state["strategic_balance"] = 0.70
        st.session_state["w_rca"] = 0.00
        st.session_state["w_density"] = 0.70
        st.session_state["w_eff_num_exp"] = 0.00
        st.session_state["w_alignment_hv"] = 0.30
        st.session_state["w_pci"] = 0.30
        st.session_state["w_cog"] = 0.35
        st.session_state["w_growth"] = 0.15
        st.session_state["w_market_size"] = 0.15
        st.session_state["rows_to_display"] = 20

    elif profile_name == "extensive_balanced":
        # Balanceado
        st.session_state["rca_min_filter"] = 0.00
        st.session_state["rca_max_filter"] = 0.99
        st.session_state["density_pct_range"] = (
            max(0.30, float(density_pct_min_data)),
            min(0.40, float(density_pct_upper_bound)),
        )
        st.session_state["strategic_balance"] = 0.50
        st.session_state["w_rca"] = 0.20
        st.session_state["w_density"] = 0.30
        st.session_state["w_eff_num_exp"] = 0.00
        st.session_state["w_alignment_hv"] = 0.30
        st.session_state["w_pci"] = 0.30
        st.session_state["w_cog"] = 0.35
        st.session_state["w_growth"] = 0.15
        st.session_state["w_market_size"] = 0.15
        st.session_state["rows_to_display"] = 40


if st.sidebar.button("Consolidadas", use_container_width=True):
    _apply_profile("intensive")
    st.rerun()
if st.sidebar.button("Emergentes", use_container_width=True):
    _apply_profile("extensive_low_hanging")
    st.rerun()
if st.sidebar.button("Apuestas Estrategicas", use_container_width=True):
    _apply_profile("extensive_strategic")
    st.rerun()
if st.sidebar.button("Balanceado", use_container_width=True):
    _apply_profile("extensive_balanced")
    st.rerun()

st.sidebar.header("Filters")

if st.sidebar.button("Reset all filters"):
    st.session_state["trade_min"] = 0.0
    st.session_state["ecu_export_min_m"] = 0.0
    st.session_state["rca_min_filter"] = 0.0
    st.session_state["rca_max_filter"] = float(rca_upper_bound)
    st.session_state["density_pct_range"] = (float(density_pct_min_data), float(density_pct_upper_bound))
    st.session_state["selected_sectors"] = sector_options
    st.session_state["excluded_product_labels"] = []
    st.session_state["above_accessible_growth_only"] = False
    st.session_state["size_label"] = "Accessible market growth (5y)"
    st.session_state["rows_to_display"] = 60
    st.session_state["ignore_density_filter"] = False

size_label = st.sidebar.selectbox("Dot size variable", list(size_choices.keys()), key="size_label")
min_dot_size = 4
max_dot_size = 20

trade_min = st.sidebar.number_input(
    "Minimum accessible trade (Billion USD)",
    min_value=0.0,
    max_value=float(max(df["accessible_market_size_b"].max() if not df.empty else 0.0, 0.1)),
    step=0.01,
    format="%.2f",
    key="trade_min",
    help="Type the minimum accessible market threshold directly.",
)

ecu_export_min_m = st.sidebar.number_input(
    "Minimum Ecuador exports (Million USD)",
    min_value=0.0,
    max_value=float(max(ecu_export_max_m, 1.0)),
    step=1.0,
    format="%.0f",
    key="ecu_export_min_m",
    help="Type the minimum Ecuador exported value threshold directly.",
)
ecu_export_min_b = ecu_export_min_m / 1000

rca_min_filter = st.sidebar.number_input(
    "Minimum RCA",
    min_value=0.0,
    step=float(rca_step),
    format="%.3f" if rca_step < 0.01 else ("%.2f" if rca_step < 0.1 else "%.1f"),
    key="rca_min_filter",
    help="Keep products with raw RCA greater than or equal to this value (inclusive lower bound).",
)
rca_max_filter = st.sidebar.number_input(
    "Maximum RCA",
    min_value=float(rca_min_filter),
    max_value=float(rca_upper_bound),
    step=float(rca_step),
    format="%.3f" if rca_step < 0.01 else ("%.2f" if rca_step < 0.1 else "%.1f"),
    key="rca_max_filter",
    help="Keep products with raw RCA strictly less than this value (exclusive upper bound).",
)

density_pct_range = st.sidebar.slider(
    "Density percentile range",
    min_value=float(density_pct_min_data),
    max_value=float(density_pct_upper_bound),
    step=0.01,
    format="%.2f",
    key="density_pct_range",
)

selected_sectors = st.sidebar.multiselect(
    "Sector",
    options=sector_options,
    default=st.session_state["selected_sectors"],
    key="selected_sectors",
)
excluded_product_labels = st.sidebar.multiselect(
    "Exclude products (HS4)",
    options=product_options_df["hs4_label"].tolist(),
    default=st.session_state["excluded_product_labels"],
    key="excluded_product_labels",
    help="Exclude one or more HS4 products from the analysis.",
)
excluded_hs4_codes = {product_label_to_code[label] for label in excluded_product_labels}

above_accessible_growth_only = st.sidebar.toggle(
    "AM CAGR (5y) > 1%",
    value=st.session_state["above_accessible_growth_only"],
    key="above_accessible_growth_only",
)

st.sidebar.header("Dimension Balance")
strategic_balance = st.sidebar.slider(
    "Feasibility (100%) = 0 | Attractiveness (100%) = 1",
    0.0,
    1.0,
    float(st.session_state["strategic_balance"]),
    0.05,
    key="strategic_balance",
)

st.sidebar.header("Weight Controls")
st.sidebar.caption("Each index is a weighted average of normalized components.")
if st.sidebar.button("Reset Weights"):
    for k, v in defaults.items():
        st.session_state[k] = v

with st.sidebar.expander("Feasibility Components", expanded=True):
    w_rca = st.slider("RCA Continuous weight", 0.0, 1.0, float(st.session_state["w_rca"]), 0.05, key="w_rca")
    w_density = st.slider("Density weight", 0.0, 1.0, float(st.session_state["w_density"]), 0.05, key="w_density")
    w_eff_num_exp = st.slider(
        "Effective exporters weight", 0.0, 1.0, float(st.session_state["w_eff_num_exp"]), 0.05, key="w_eff_num_exp"
    )
    w_alignment_hv = st.slider(
        "WNAI weight",
        0.0,
        1.0,
        float(st.session_state["w_alignment_hv"]),
        0.05,
        key="w_alignment_hv",
    )

with st.sidebar.expander("Attractiveness Components", expanded=True):
    w_pci = st.slider("PCI weight", 0.0, 1.0, float(st.session_state["w_pci"]), 0.05, key="w_pci")
    w_cog = st.slider("COG weight", 0.0, 1.0, float(st.session_state["w_cog"]), 0.05, key="w_cog")
    w_growth = st.slider(
        "Accessible market growth (5y) weight", 0.0, 1.0, float(st.session_state["w_growth"]), 0.05, key="w_growth"
    )
    w_market_size = st.slider(
        "Accessible market size weight", 0.0, 1.0, float(st.session_state["w_market_size"]), 0.05, key="w_market_size"
    )

flt = df.copy()
flt["accessible_market_size_mm"] = normalize_0_1(pd.to_numeric(flt["accessible_market_size"], errors="coerce").fillna(0.0))
flt["feasibility_raw"] = weighted_index(
    flt,
    FEAS_COLS,
    [w_rca, w_density, w_eff_num_exp, w_alignment_hv],
)
flt["attractiveness_raw"] = weighted_index(
    flt,
    ATTR_COLS,
    [w_pci, w_cog, w_growth, w_market_size],
)
# Renormalize post-aggregation so final indexes remain bounded in [0, 1].
flt["feasibility_index"] = normalize_0_1(flt["feasibility_raw"])
flt["attractiveness_index"] = normalize_0_1(flt["attractiveness_raw"])
flt["combined_raw"] = ((1 - strategic_balance) * flt["feasibility_index"]) + (
    strategic_balance * flt["attractiveness_index"]
)
flt["combined_score"] = normalize_0_1(flt["combined_raw"])

flt = flt[flt["accessible_market_size_b"] >= trade_min]
flt = flt[flt["ecu_total_trade_b"] >= ecu_export_min_b]
flt = flt[flt["raw_rca"] >= float(rca_min_filter)]
effective_rca_upper = float(rca_max_filter)
# With the [lower, upper) rule, when the selected upper bound is at (or above)
# the observed data max, make it open-ended to avoid dropping the max record by
# floating-point/session rounding artifacts.
if effective_rca_upper >= float(rca_max_data):
    effective_rca_upper = float(rca_max_data + rca_step)
flt = flt[flt["raw_rca"] < effective_rca_upper]
density_lo = round(min(density_pct_range), 2)
density_hi = round(max(density_pct_range), 2)
if not st.session_state.get("ignore_density_filter", False):
    _density_pct_2d = pd.to_numeric(flt["density_percentile"], errors="coerce").fillna(0.0).round(2)
    effective_density_hi = density_hi
    if effective_density_hi >= round(float(density_pct_max_data), 2):
        effective_density_hi = round(float(density_pct_upper_bound), 2)
    flt = flt[
        (_density_pct_2d >= density_lo)
        & (_density_pct_2d < effective_density_hi)
    ]
if selected_sectors:
    flt = flt[flt["sector"].isin(selected_sectors)]
if excluded_hs4_codes:
    flt = flt[~flt["hs4"].astype(str).str.zfill(4).isin(excluded_hs4_codes)]
if above_accessible_growth_only:
    flt = flt[flt["accessible_market_growth_5y"] > 0.01]

if flt.empty:
    st.warning("No products match the current filters.")
    st.stop()

size_col = size_choices[size_label]
size_raw = pd.to_numeric(flt[size_col], errors="coerce").fillna(0).clip(lower=0)
size_norm = normalize_0_1(size_raw)
flt["dot_size"] = min_dot_size + (size_norm * (max_dot_size - min_dot_size))

c1, c2, c3 = st.columns(3)
c1.metric("Products shown", f"{len(flt):,} / {len(df):,}")
c2.metric("Avg Feasibility", f"{flt['feasibility_index'].mean():.3f}")
c3.metric("Avg Attractiveness", f"{flt['attractiveness_index'].mean():.3f}")
st.caption(
    f"Active filters: accessible trade >= {trade_min:.2f} BUSD, "
    f"ECU exports >= {ecu_export_min_m:.0f} MUSD, "
    f"RCA in [{float(rca_min_filter):.3f}, {float(rca_max_filter):.3f}], "
    f"density percentile in [{density_lo:.2f}, {density_hi:.2f}], "
    f"{len(selected_sectors)} sectors, "
    f"{len(excluded_hs4_codes)} excluded products, "
    f"AM CAGR (5y) > 1%={above_accessible_growth_only}."
)

hover_cols = [
    "raw_rca",
    "rca_transformed",
    "pci",
    "cog",
    "density",
    "eff_num_exp",
    "distance_travelled",
    "density_percentile",
    "market_growth_5y",
    "accessible_market_growth_5y",
    "ecu_export_growth_5y",
    "market_size_share",
    "market_size_b",
    "accessible_market_size_b",
    "accessible_market_to_market_ratio",
    "total_trade_b",
]

fig = go.Figure()
for sector, grp in flt.groupby("sector", sort=False):
    customdata = np.column_stack(
        [grp["hs4"], grp["product_name_short"]] + [pd.to_numeric(grp[c], errors="coerce").fillna(0.0) for c in hover_cols]
    )
    fig.add_trace(
        go.Scatter(
            x=grp["feasibility_index"],
            y=grp["attractiveness_index"],
            mode="markers",
            name=sector,
            marker=dict(
                size=grp["dot_size"],
                color=SECTOR_COLORS.get(sector, "#6b7280"),
                opacity=0.78,
                line=dict(width=0.5, color="#1f2f46"),
            ),
            customdata=customdata,
            hovertemplate=(
                "<b>%{customdata[1]}</b><br>"
                "HS4: %{customdata[0]}<br>"
                "Feasibility: %{x:.3f}<br>"
                "Attractiveness: %{y:.3f}<br>"
                "RCA: %{customdata[2]:.3f}<br>"
                "RCA Continuous: %{customdata[3]:.3f}<br>"
                "PCI: %{customdata[4]:.3f}<br>"
                "COG: %{customdata[5]:.3f}<br>"
                "Density: %{customdata[6]:.3f}<br>"
                "Effective exporters: %{customdata[7]:.2f}<br>"
                "Distance travelled: %{customdata[8]:.2f}<br>"
                "Density percentile: %{customdata[9]:.2f}<br>"
                "Global market growth (5y): %{customdata[10]:.3%}<br>"
                "Accessible market growth (5y): %{customdata[11]:.3%}<br>"
                "Ecuador export growth (5y): %{customdata[12]:.3%}<br>"
                "Global market share: %{customdata[13]:.3%}<br>"
                "Market size (B USD): %{customdata[14]:.3f}<br>"
                "Accessible market size (B USD): %{customdata[15]:.3f}<br>"
                "Accessible-to-market ratio: %{customdata[16]:.3%}<br>"
                "Total trade (B USD): %{customdata[17]:.3f}<extra></extra>"
            ),
        )
    )

fig.update_layout(
    title="Feasibility vs Attractiveness (HS92, 2024)",
    template="plotly_white",
    xaxis_title="Feasibility",
    yaxis_title="Attractiveness",
    legend_title="Sector",
    margin=dict(t=60, l=20, r=20, b=20),
)
diag_min = float(min(flt["feasibility_index"].min(), flt["attractiveness_index"].min()))
diag_max = float(max(flt["feasibility_index"].max(), flt["attractiveness_index"].max()))
fig.add_shape(
    type="line",
    x0=diag_min,
    y0=diag_min,
    x1=diag_max,
    y1=diag_max,
    line=dict(color="rgba(220, 38, 38, 0.55)", width=2, dash="dash"),
)
st.plotly_chart(
    fig,
    use_container_width=True,
)

st.subheader("Top Product Rankings")
search_text = st.text_input("Search product name", placeholder="Type to filter...")
top_n = st.slider("Rows to display", min_value=10, max_value=300, step=10, key="rows_to_display")

table = flt.copy()
if search_text:
    mask = table["product_name_short"].astype(str).str.contains(search_text, case=False, na=False)
    table = table[mask]

table = table.sort_values("combined_score", ascending=False).reset_index(drop=True)
table["rank"] = np.arange(1, len(table) + 1)

display_cols = [
    "rank",
    "hs4",
    "product_name_short",
    "sector",
    "combined_score",
    "attractiveness_index",
    "feasibility_index",
    "raw_rca",
    "density",
    "density_percentile",
    "pci",
    "cog",
    "eff_num_exp",
    "ecu_exporter_rank",
    "alignment_weighted_percentile",
    "alignment_lead_weighted",
    "distance_travelled",
    "market_growth_5y",
    "accessible_market_growth_5y",
    "ecu_export_growth_5y",
    "ecu_total_trade",
    "market_share_change_abs",
    "market_size_share",
    "accessible_market_size",
    "accessible_market_to_market_ratio",
    "total_trade_b",
]
table_display = (
    table[display_cols]
    .head(top_n)
    .assign(
        market_growth_5y=lambda d: d["market_growth_5y"] * 100,
        accessible_market_growth_5y=lambda d: d["accessible_market_growth_5y"] * 100,
        ecu_export_growth_5y=lambda d: d["ecu_export_growth_5y"] * 100,
        ecu_total_trade=lambda d: d["ecu_total_trade"] / 1_000_000,
        market_share_change_abs=lambda d: d["market_share_change_abs"] * 100,
        market_size_share=lambda d: d["market_size_share"] * 100,
        accessible_market_size=lambda d: d["accessible_market_size"] / 1_000_000_000,
        accessible_market_to_market_ratio=lambda d: d["accessible_market_to_market_ratio"] * 100,
    )
)


def _lead_color(value: float) -> str:
    v = pd.to_numeric(value, errors="coerce")
    if pd.isna(v):
        return ""
    if float(v) > 0:
        return "color: #16a34a;"
    if float(v) < 0:
        return "color: #dc2626;"
    return ""


table_styler = table_display.style.map(
    _lead_color,
    subset=["alignment_lead_weighted"],
)

st.dataframe(
    table_styler,
    use_container_width=True,
    hide_index=True,
    column_config={
        "rank": st.column_config.NumberColumn("Rank", format="%.0f"),
        "hs4": st.column_config.TextColumn("HS4"),
        "product_name_short": st.column_config.TextColumn("Product"),
        "sector": st.column_config.TextColumn("Sector"),
        "combined_score": st.column_config.NumberColumn("Combined Opportunity Score", format="%.4f"),
        "attractiveness_index": st.column_config.NumberColumn("Attractiveness Index", format="%.4f"),
        "feasibility_index": st.column_config.NumberColumn("Feasibility Index", format="%.4f"),
        "raw_rca": st.column_config.NumberColumn("RCA", format="%.3f"),
        "pci": st.column_config.NumberColumn("PCI", format="%.3f"),
        "cog": st.column_config.NumberColumn("COG", format="%.3f"),
        "eff_num_exp": st.column_config.NumberColumn("Effective Exporters", format="%.2f"),
        "ecu_exporter_rank": st.column_config.NumberColumn("Country Exporter Rank (2024)", format="%.0f"),
        "alignment_weighted_percentile": st.column_config.NumberColumn("WNAI Percentile", format="%.1f"),
        "alignment_lead_weighted": st.column_config.NumberColumn("WNAI Lead", format="%.1f"),
        "density": st.column_config.NumberColumn("Density (Raw)", format="%.6f"),
        "density_percentile": st.column_config.NumberColumn("Density Percentile", format="%.2f"),
        "distance_travelled": st.column_config.NumberColumn("Distance Travelled", format="%.2f"),
        "market_growth_5y": st.column_config.NumberColumn("Global Market Growth % (5y)", format="%.2f%%"),
        "accessible_market_growth_5y": st.column_config.NumberColumn("Accessible Market Growth % (5y)", format="%.2f%%"),
        "ecu_export_growth_5y": st.column_config.NumberColumn("Country Export Growth % (5y)", format="%.2f%%"),
        "ecu_total_trade": st.column_config.NumberColumn("Country Current Exports (M USD)", format="%.2f"),
        "market_share_change_abs": st.column_config.NumberColumn("Absolute Market Share Change (pp)", format="%.2f"),
        "market_size_share": st.column_config.NumberColumn("Global Market Share", format="%.2f%%"),
        "accessible_market_size": st.column_config.NumberColumn("Accessible Market Size (B USD)", format="%.3f"),
        "accessible_market_to_market_ratio": st.column_config.NumberColumn("Accessible-to-Market Ratio", format="%.2f%%"),
        "total_trade_b": st.column_config.NumberColumn("Total Trade (B USD)", format="%.3f"),
    },
)

st.subheader("Opportunity Summary by Sector")
treemap_size_options = {
    "Accessible market size (B USD)": "accessible_market_size",
    "Accessible market growth (5y)": "accessible_market_growth_5y",
    "Market size (B USD)": "total_trade_b",
    "Combined Opportunity Score": "combined_score",
    "Density Percentile": "density_percentile",
    "Frequency": "frequency",
}
st.session_state.setdefault("treemap_size_metric_v1", "Accessible market size (B USD)")
treemap_size_label = st.selectbox(
    "Treemap size variable",
    options=list(treemap_size_options.keys()),
    key="treemap_size_metric_v1",
)
treemap_value_col = treemap_size_options[treemap_size_label]
treemap_color_options = {
    "Sector": "sector",
    "PCI (raw)": "pci",
}
st.session_state.setdefault("treemap_color_metric_v1", "Sector")
treemap_color_label = st.selectbox(
    "Treemap color variable",
    options=list(treemap_color_options.keys()),
    key="treemap_color_metric_v1",
)
treemap_color_col = treemap_color_options[treemap_color_label]

treemap_df = table_display[
    [
        "sector",
        "hs4",
        "product_name_short",
        "combined_score",
        "total_trade_b",
        "accessible_market_size",
        "accessible_market_growth_5y",
        "density_percentile",
        "pci",
    ]
].copy()
treemap_df["sector"] = treemap_df["sector"].fillna("Sin sector")
treemap_df["product_label"] = (
    treemap_df["hs4"].astype(str).str.zfill(4) + " - " + treemap_df["product_name_short"].astype(str)
)


def _wrap_treemap_label(text: str, width: int = 18) -> str:
    words = str(text).split()
    if not words:
        return str(text)
    lines: list[str] = []
    current = words[0]
    for w in words[1:]:
        if len(current) + 1 + len(w) <= width:
            current = f"{current} {w}"
        else:
            lines.append(current)
            current = w
    lines.append(current)
    return "<br>".join(lines)


treemap_df["product_label_wrapped"] = treemap_df["product_label"].map(_wrap_treemap_label)
treemap_df["frequency"] = 1.0
treemap_df["pci_for_color"] = pd.to_numeric(treemap_df["pci"], errors="coerce").clip(pci_color_min, pci_color_max)

if treemap_df.empty:
    st.info("No products available for the treemap under the current filters.")
else:
    if treemap_size_label == "Market size (B USD)":
        st.metric(
            label="Total Market Size (B USD) shown",
            value=f"{treemap_df['total_trade_b'].sum():,.3f}",
        )
    else:
        st.metric(
            label="Accessible Market Size (B USD) shown",
            value=f"{treemap_df['accessible_market_size'].sum():,.3f}",
        )

    pci_colorscale = [
        (0.0, "rgb(227, 159, 96)"),
        (0.278697, "rgb(231, 173, 120)"),
        (0.338965, "rgb(235, 188, 143)"),
        (0.398272, "rgb(240, 202, 168)"),
        (0.448314, "rgb(244, 217, 191)"),
        (0.493999, "rgb(248, 231, 215)"),
        (0.494099, "rgb(192, 228, 225)"),
        (0.533691, "rgb(154, 211, 207)"),
        (0.571435, "rgb(116, 195, 189)"),
        (0.606597, "rgb(77, 178, 171)"),
        (0.661681, "rgb(40, 162, 153)"),
        (1.0, "rgb(2, 146, 135)"),
    ]

    treemap_color_kwargs = {}
    if treemap_color_col == "sector":
        treemap_color_kwargs = {
            "color": "sector",
            "color_discrete_map": SECTOR_COLORS,
        }
    else:
        treemap_color_kwargs = {
            "color": "pci_for_color",
            "color_continuous_scale": pci_colorscale,
            "range_color": (pci_color_min, pci_color_max),
        }

    treemap = px.treemap(
        treemap_df,
        path=["sector", "product_label_wrapped"],
        values=treemap_value_col,
        **treemap_color_kwargs,
        hover_data={
            "combined_score": ":.3f",
            "total_trade_b": ":.3f",
            "accessible_market_size": ":.3f",
            "accessible_market_growth_5y": ":.3f",
            "density_percentile": ":.2f",
            "pci": ":.3f",
            "pci_for_color": False,
            "product_label": True,
            "sector": False,
            "product_label_wrapped": False,
        },
        title=f"Opportunity treemap (n = {len(treemap_df)} products shown) | size = {treemap_size_label} | color = {treemap_color_label}",
    )
    treemap.update_traces(
        textinfo="label",
        textfont=dict(size=18, color="#ffffff"),
        marker=dict(line=dict(width=1, color="rgba(255,255,255,0.45)")),
    )
    treemap.update_layout(
        margin=dict(t=60, l=10, r=10, b=95),
    )
    if treemap_color_col == "sector":
        treemap.update_layout(
            legend=dict(
                orientation="h",
                yanchor="top",
                y=-0.12,
                xanchor="center",
                x=0.5,
                title_text="Sector",
            ),
        )
    else:
        treemap.update_layout(
            coloraxis_colorbar=dict(
                title=dict(text="PCI", font=dict(color="#0f172a", size=16)),
                orientation="h",
                yanchor="top",
                y=-0.12,
                xanchor="center",
                x=0.5,
                len=0.7,
                bgcolor="rgba(255,255,255,0.96)",
                borderwidth=0,
                tickfont=dict(color="#0f172a", size=14),
                tickcolor="#0f172a",
                ticklen=6,
                tickwidth=1.2,
            ),
        )
    st.plotly_chart(treemap, use_container_width=True)
