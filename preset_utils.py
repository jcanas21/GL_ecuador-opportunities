import numpy as np
import pandas as pd

from data_utils import (
    load_anchor_proximity_dataset,
    load_natural_resource_exclusion_labels,
    load_opportunity_dataset,
    normalize_0_1,
)


FEAS_COLS = ["rca_transformed_z", "density_z", "eff_num_exp_z", "dai_percentile_z"]
ATTR_COLS = ["pci_z", "cog_z", "accessible_market_growth_5y_z", "accessible_market_size_mm"]

MANUAL_PRESET_EXCLUDED_HS4 = {"2711", "2710", "7108", "2709", "2713", "2701", "2603", "2616", "8803", "7602", "7404"}

PAGE2_PRESETS = {
    "Margen Intensivo": {
        "trade_min": 0.5,
        "growth_gt": 0.0,
        "rca_min": 0.50,
        "rca_max": 5.00,
        "density_range": None,
        "strategic_balance": 0.50,
        "feas_weights": [0.00, 0.50, 0.00, 0.50],
        "attr_weights": [0.50, 0.00, 0.25, 0.25],
        "top_n": 20,
        "exclude_mode": "natural_resources_plus_manual",
    },
}

PAGE3_PRESETS = {
    "Candidatos seleccionados": {
        "trade_min": 0.5,
        "growth_gt": 0.0,
        "candidate_rca_max": 0.5,
        "anchor_density_max": 50.0,
        "proximity_rank_range": (1, 10),
        "exclude_anchor_sections_prefixes": ("1.", "2.", "3."),
        "exclude_candidate_sections_prefixes": ("1.", "2.", "3."),
        "above_median_proximity_only": True,
        "strategic_balance": 0.50,
        "w_dai": 0.5,
        "w_anchor_count": 0.5,
        "attr_weights": [0.50, 0.00, 0.25, 0.25],
        "top_n": 30,
        "exclude_mode": "natural_resources",
    }
}


def _extract_hs4_codes_from_labels(labels: list[str]) -> set[str]:
    codes: set[str] = set()
    for label in labels:
        code = str(label).split(" - ", 1)[0].strip()
        if code.isdigit():
            codes.add(code.zfill(4)[:4])
    return codes


def natural_resource_hs4_codes() -> set[str]:
    return _extract_hs4_codes_from_labels(load_natural_resource_exclusion_labels())


def exclusion_codes(mode: str) -> set[str]:
    if mode == "natural_resources":
        return natural_resource_hs4_codes()
    if mode == "natural_resources_plus_manual":
        return natural_resource_hs4_codes().union(MANUAL_PRESET_EXCLUDED_HS4)
    if mode == "manual_only":
        return set(MANUAL_PRESET_EXCLUDED_HS4)
    return set()


def weighted_index(frame: pd.DataFrame, cols: list[str], weights: list[float]) -> pd.Series:
    weight_sum = float(sum(weights))
    if weight_sum <= 0:
        return frame[cols].mean(axis=1)
    arr = np.column_stack([frame[c].to_numpy() for c in cols])
    w = np.array(weights, dtype=float)
    return pd.Series((arr * w).sum(axis=1) / weight_sum, index=frame.index)


def build_page2_recommendations(profile_name: str) -> pd.DataFrame:
    profile = PAGE2_PRESETS[profile_name]
    df = load_opportunity_dataset().copy()
    if df.empty:
        return df

    df["hs4"] = df["hs4"].astype(str).str.zfill(4)
    df["accessible_market_size_mm"] = normalize_0_1(pd.to_numeric(df["accessible_market_size"], errors="coerce").fillna(0.0))

    df["feasibility_raw"] = weighted_index(df, FEAS_COLS, profile["feas_weights"])
    df["attractiveness_raw"] = weighted_index(df, ATTR_COLS, profile["attr_weights"])
    df["feasibility_index"] = normalize_0_1(df["feasibility_raw"])
    df["attractiveness_index"] = normalize_0_1(df["attractiveness_raw"])
    df["combined_raw"] = (
        (1 - profile["strategic_balance"]) * df["feasibility_index"]
        + profile["strategic_balance"] * df["attractiveness_index"]
    )
    df["combined_score"] = normalize_0_1(df["combined_raw"])

    density_pct_2d = pd.to_numeric(df["density_percentile"], errors="coerce").fillna(0.0).round(2)
    raw_rca = pd.to_numeric(df["raw_rca"], errors="coerce").fillna(0.0)
    rca_max_data = float(raw_rca.max()) if not raw_rca.empty else 0.0
    rca_step = 0.001
    excluded_codes = exclusion_codes(profile.get("exclude_mode", ""))

    flt = df[
        (pd.to_numeric(df["accessible_market_size_b"], errors="coerce") >= profile["trade_min"])
        & (pd.to_numeric(df["accessible_market_growth_5y"], errors="coerce") > profile["growth_gt"])
        & (raw_rca >= profile["rca_min"])
        & (~df["hs4"].isin(excluded_codes))
    ].copy()

    if profile["rca_max"] is not None:
        effective_rca_upper = float(profile["rca_max"])
        if effective_rca_upper >= float(rca_max_data):
            effective_rca_upper = float(rca_max_data + rca_step)
        flt = flt[raw_rca.loc[flt.index] < effective_rca_upper]

    if profile["density_range"] is not None:
        lo, hi = profile["density_range"]
        flt = flt[(density_pct_2d.loc[flt.index] >= round(lo, 2)) & (density_pct_2d.loc[flt.index] < round(hi, 2))]

    flt = flt.sort_values(["combined_score", "accessible_market_size_b"], ascending=[False, False]).reset_index(drop=True)
    flt["page2_rank"] = np.arange(1, len(flt) + 1)
    return flt.head(profile["top_n"])[
        [
            "hs4",
            "product_name_short",
            "sector",
            "combined_score",
            "page2_rank",
            "raw_rca",
            "density_percentile",
            "dai_percentile",
            "dai_index",
            "accessible_market_size_b",
            "accessible_market_growth_5y",
            "pci",
            "cog",
        ]
    ].rename(
        columns={
            "combined_score": "page2_score",
            "sector": "page2_sector",
            "dai_percentile": "page2_dai_pct",
            "dai_index": "page2_dai_raw",
        }
    )


def build_page3_recommendations(profile_name: str) -> pd.DataFrame:
    profile = PAGE3_PRESETS[profile_name]
    df = load_anchor_proximity_dataset().copy()
    if df.empty:
        return df

    df["candidate_hs4"] = df["candidate_hs4"].astype(str).str.zfill(4)
    anchor_sections_ok = ~df["anchor_hs_section_name"].astype(str).str.startswith(profile["exclude_anchor_sections_prefixes"])
    candidate_sections_ok = ~df["candidate_hs_section_name"].astype(str).str.startswith(profile["exclude_candidate_sections_prefixes"])
    excluded_codes = exclusion_codes(profile.get("exclude_mode", ""))

    flt = df[
        (pd.to_numeric(df["accessible_market_size_b"], errors="coerce") >= profile["trade_min"])
        & (pd.to_numeric(df["accessible_market_growth_5y"], errors="coerce") > profile["growth_gt"])
        & (pd.to_numeric(df["anchor_density_percentile"], errors="coerce") <= profile["anchor_density_max"])
        & (pd.to_numeric(df["candidate_raw_rca"], errors="coerce").fillna(0.0) <= profile["candidate_rca_max"])
        & (pd.to_numeric(df["proximity_rank"], errors="coerce") >= profile["proximity_rank_range"][0])
        & (pd.to_numeric(df["proximity_rank"], errors="coerce") <= profile["proximity_rank_range"][1])
        & anchor_sections_ok
        & candidate_sections_ok
        & (~df["candidate_hs4"].isin(excluded_codes))
    ].copy()

    if profile.get("above_median_proximity_only", False):
        flt = flt[pd.to_numeric(flt["proximity_above_country_median"], errors="coerce").fillna(0).astype(int).eq(1)]

    candidate_scores = (
        flt.groupby(
            [
                "candidate_hs4",
                "candidate_product_name_short",
                "candidate_sector",
                "candidate_hs_section_name",
            ],
            as_index=False,
        )
        .agg(
            accessible_market_size=("accessible_market_size", "first"),
            accessible_market_size_b=("accessible_market_size_b", "first"),
            accessible_market_growth_5y=("accessible_market_growth_5y", "first"),
            dai_index=("dai_index", "first"),
            dai_percentile=("dai_percentile", "first"),
            candidate_raw_rca=("candidate_raw_rca", "first"),
            pci=("pci", "first"),
            cog=("cog", "first"),
            avg_proximity=("proximity", "mean"),
            anchor_count=("anchor_hs4", "nunique"),
        )
    )

    candidate_scores["dai_mm"] = normalize_0_1(candidate_scores["dai_percentile"])
    candidate_scores["anchor_count_mm"] = normalize_0_1(candidate_scores["anchor_count"])
    candidate_scores["pci_mm"] = normalize_0_1(candidate_scores["pci"])
    candidate_scores["cog_mm"] = normalize_0_1(candidate_scores["cog"])
    candidate_scores["accessible_market_growth_mm"] = normalize_0_1(candidate_scores["accessible_market_growth_5y"])
    candidate_scores["accessible_market_size_mm"] = normalize_0_1(candidate_scores["accessible_market_size"])

    w_dai = float(profile.get("w_dai", 0.0))
    w_anchor_count = float(profile.get("w_anchor_count", 0.0))
    denom = w_dai + w_anchor_count
    if denom > 0:
        candidate_scores["feasibility_raw"] = (
            candidate_scores["dai_mm"] * w_dai
            + candidate_scores["anchor_count_mm"] * w_anchor_count
        ) / denom
    else:
        candidate_scores["feasibility_raw"] = 0.0
    candidate_scores["feasibility_index"] = normalize_0_1(candidate_scores["feasibility_raw"])
    attr = candidate_scores[["pci_mm", "cog_mm", "accessible_market_growth_mm", "accessible_market_size_mm"]]
    attr_weights = np.array(profile["attr_weights"], dtype=float)
    candidate_scores["attractiveness_raw"] = (attr.to_numpy() * attr_weights).sum(axis=1) / float(attr_weights.sum())
    candidate_scores["attractiveness_index"] = normalize_0_1(candidate_scores["attractiveness_raw"])
    candidate_scores["combined_raw"] = (
        (1 - profile["strategic_balance"]) * candidate_scores["feasibility_index"]
        + profile["strategic_balance"] * candidate_scores["attractiveness_index"]
    )
    candidate_scores["combined_score"] = normalize_0_1(candidate_scores["combined_raw"])
    candidate_scores = candidate_scores.sort_values(
        ["combined_score", "accessible_market_size_b"], ascending=[False, False]
    ).reset_index(drop=True)
    candidate_scores["page3_rank"] = np.arange(1, len(candidate_scores) + 1)

    return candidate_scores.head(profile["top_n"])[
        [
            "candidate_hs4",
            "candidate_product_name_short",
            "candidate_sector",
            "candidate_hs_section_name",
            "combined_score",
            "page3_rank",
            "dai_percentile",
            "dai_index",
            "candidate_raw_rca",
            "accessible_market_size_b",
            "accessible_market_growth_5y",
            "pci",
            "cog",
            "avg_proximity",
            "anchor_count",
        ]
    ].rename(
        columns={
            "candidate_hs4": "hs4",
            "candidate_product_name_short": "product_name_short",
            "candidate_sector": "page3_sector",
            "dai_percentile": "page3_dai_pct",
            "dai_index": "page3_dai_raw",
            "combined_score": "page3_score",
        }
    )
