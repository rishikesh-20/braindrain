from __future__ import annotations

import pandas as pd


METHODOLOGY_NOTES = [
    "B07409 is a proxy for educated out-migration, so net migration figures are directional estimates.",
    "Young mobility metrics cover ages 25 to 34 and do not isolate degree status in that view.",
    "B25070 measures renter cost burden only and does not represent full cost of living.",
    "ACS 5-year estimates are period estimates for structural comparison, not single-year snapshots.",
]

CHART_IDS = {
    "quadrant": "National Talent Positioning Map",
    "choropleth": "Geographic Brain Drain Signal",
    "peer_gaps": "Peer Gaps vs U.S. Median",
    "housing_young": "Housing Pressure vs. Young Net Migration",
    "earnings_net": "Bachelor's Earnings vs. Net Migration",
}

CHART_DESIGN = {
    "quadrant": {
        "mark": "scatter plot with sized points and a highlighted focal-state marker",
        "channels": {
            "x": "educated net migration rate per 1k",
            "y": "talent concentration percent",
            "size": "educated stock",
            "color": "policy segment",
            "text": "focal state label",
        },
        "description": "Shows how each state sits on talent attraction and talent concentration at the same time.",
        "why_this_chart": "A scatter plot is useful here because it compares two continuous measures at once and makes quadrant positioning easy to interpret.",
    },
    "choropleth": {
        "mark": "filled U.S. state geoshapes with a highlighted focal-state outline",
        "channels": {
            "color": "educated net migration rate per 1k on a diverging scale",
            "shape": "state geography",
            "stroke": "focal state emphasis",
        },
        "description": "Maps where states are above or below zero on educated net migration rate.",
        "why_this_chart": "A choropleth works best here because the goal is geographic pattern recognition across states rather than precise pairwise comparison.",
    },
    "peer_gaps": {
        "mark": "grouped vertical bars",
        "channels": {
            "x": "selected peer states",
            "y": "gap versus U.S. median",
            "color": "metric type",
        },
        "description": "Compares each selected peer state's gap to the U.S. median across net migration, young migration, and rent burden.",
        "why_this_chart": "Grouped bars make side-by-side peer comparison easy because each state can be read across the same three gap measures around the zero baseline.",
    },
    "housing_young": {
        "mark": "scatter plot with sized points and focal-state annotation",
        "channels": {
            "x": "rent burden rate",
            "y": "young net migration rate",
            "size": "young adult population",
            "color": "positive or negative young migration sign",
        },
        "description": "Shows how housing pressure lines up with young adult migration performance.",
        "why_this_chart": "A scatter plot is appropriate because it reveals how two continuous variables move together while also preserving state-level differences.",
    },
    "earnings_net": {
        "mark": "scatter plot with sized points and focal-state annotation",
        "channels": {
            "x": "median earnings for bachelor's degree holders",
            "y": "educated net migration rate",
            "size": "educated stock",
            "color": "positive or negative net migration sign",
        },
        "description": "Shows how bachelor's-level earnings compare with overall educated migration performance.",
        "why_this_chart": "A scatter plot is useful here because it helps show whether states with stronger wage signals also sit higher on net migration.",
    },
}

RELATIONSHIP_METRIC_MAP = {
    "housing pressure": "rent_burden_30plus_rate",
    "rent burden": "rent_burden_30plus_rate",
    "rent": "rent_burden_30plus_rate",
    "bachelor earnings": "median_earnings_bachelors",
    "bachelor's earnings": "median_earnings_bachelors",
    "ba earnings premium": "bachelors_earnings_premium",
    "earnings premium": "bachelors_earnings_premium",
    "earnings": "median_earnings_bachelors",
    "wages": "median_earnings_bachelors",
    "young migration": "young_net_migration_rate",
    "young talent": "young_net_migration_rate",
    "net migration": "net_migration_rate",
    "talent concentration": "talent_concentration",
}

DISPLAY_LABELS = {
    "net_migration_rate": "Educated Net Migration Rate (per 1k)",
    "young_net_migration_rate": "Young Net Migration Rate (per 1k)",
    "talent_concentration": "Talent Concentration (%)",
    "rent_burden_30plus_rate": "Rent Burden (30%+)",
    "bachelors_earnings_premium": "BA Earnings Premium ($)",
    "median_earnings_bachelors": "Median Earnings: Bachelor's ($)",
}


def _first_available_column(df: pd.DataFrame, candidates: list[str]) -> str:
    for column in candidates:
        if column in df.columns:
            return column
    raise KeyError(f"None of the expected columns are available: {', '.join(candidates)}")


def _migration_metric_column(df: pd.DataFrame) -> str:
    return _first_available_column(df, ["net_migration_rate", "young_net_migration_rate"])


def _migration_metric_label(metric_col: str) -> str:
    return DISPLAY_LABELS.get(metric_col, metric_col)


def _state_row(df: pd.DataFrame, state: str) -> pd.Series:
    return df[df["state"] == state].iloc[0]


def _optional_state_row(df: pd.DataFrame, state: str | None) -> pd.Series | None:
    if not state:
        return None
    matches = df[df["state"] == state]
    if matches.empty:
        return None
    return matches.iloc[0]


def build_briefing_context(df: pd.DataFrame, focal_state: str) -> dict:
    focal = _state_row(df, focal_state)
    ranked_net = df["net_migration_rate"].rank(ascending=False, method="min")
    ranked_young = df["young_net_migration_rate"].rank(ascending=False, method="min")
    ranked_rent = df["rent_burden_30plus_rate"].rank(ascending=True, method="min")

    return {
        "state": focal_state,
        "metrics": {
            "educated_in_migrants": int(focal["interstate_in_educated"]),
            "educated_out_migrants_est": int(focal["interstate_out_educated"]),
            "net_educated_migrants": int(focal["net_educated_migrants"]),
            "net_migration_rate_per_1k": round(float(focal["net_migration_rate"]), 2),
            "young_net_migration_rate_per_1k": round(float(focal["young_net_migration_rate"]), 2),
            "talent_concentration_pct": round(float(focal["talent_concentration"]), 1),
            "rent_burden_30plus_pct": round(float(focal["rent_burden_30plus_rate"]), 1),
            "bachelors_earnings_premium_usd": round(float(focal["bachelors_earnings_premium"]), 0),
            "policy_segment": focal["segment"],
        },
        "national_medians": {
            "net_migration_rate_per_1k": round(float(df["net_migration_rate"].median()), 2),
            "young_net_migration_rate_per_1k": round(float(df["young_net_migration_rate"].median()), 2),
            "talent_concentration_pct": round(float(df["talent_concentration"].median()), 1),
            "rent_burden_30plus_pct": round(float(df["rent_burden_30plus_rate"].median()), 1),
            "bachelors_earnings_premium_usd": round(float(df["bachelors_earnings_premium"].median()), 0),
        },
        "ranks": {
            "net_migration_rate_rank": int(ranked_net.loc[focal.name]),
            "young_net_migration_rate_rank": int(ranked_young.loc[focal.name]),
            "rent_burden_rank_lower_is_better": int(ranked_rent.loc[focal.name]),
        },
        "methodology_cautions": METHODOLOGY_NOTES,
    }


def build_chart_context(
    df: pd.DataFrame,
    chart_id: str,
    focal_state: str | None,
    peer_states: list[str] | None = None,
    applied_filters: dict | None = None,
    benchmark_df: pd.DataFrame | None = None,
    visual_encoding: dict | None = None,
) -> dict:
    focal = _optional_state_row(df, focal_state)
    peer_states = peer_states or []
    applied_filters = applied_filters or {}
    benchmark_df = benchmark_df if benchmark_df is not None else df
    base_context = {
        "chart_id": chart_id,
        "chart_title": CHART_IDS[chart_id],
        "chart_design": CHART_DESIGN[chart_id],
        "focal_state": focal_state if focal is not None else None,
        "displayed_state_count": int(df["state"].nunique()) if "state" in df.columns else 0,
        "applied_filters": applied_filters,
        "visual_encoding": visual_encoding or {},
        "cautions": METHODOLOGY_NOTES,
    }

    if chart_id == "quadrant":
        metric_col = _migration_metric_column(df)
        top_positive = df.nlargest(3, metric_col)[["state", metric_col]].round(2).to_dict("records")
        top_negative = df.nsmallest(3, metric_col)[["state", metric_col]].round(2).to_dict("records")
        context = {
            **base_context,
            "axes": {
                "x": _migration_metric_label(metric_col),
                "y": "Talent Concentration (%)",
            },
            "benchmark_lines": {
                "national_median_net_migration_rate_per_1k": round(float(df[metric_col].median()), 2),
                "national_median_talent_concentration_pct": round(float(df["talent_concentration"].median()), 1),
            },
            "top_positive_outliers": top_positive,
            "top_negative_outliers": top_negative,
        }
        if focal is not None:
            context["focal_point"] = {
                "net_migration_rate_per_1k": round(float(focal[metric_col]), 2),
                "talent_concentration_pct": round(float(focal["talent_concentration"]), 1),
                "segment": focal["segment"],
            }
        return context

    if chart_id == "choropleth":
        metric_col = _migration_metric_column(df)
        top_positive = df.nlargest(5, metric_col)[["state", metric_col]].round(2).to_dict("records")
        top_negative = df.nsmallest(5, metric_col)[["state", metric_col]].round(2).to_dict("records")
        context = {
            **base_context,
            "metric": _migration_metric_label(metric_col),
            "top_positive_states": top_positive,
            "top_negative_states": top_negative,
        }
        if focal is not None:
            context["focal_value"] = round(float(focal[metric_col]), 2)
        return context

    if chart_id == "peer_gaps":
        benchmark_states = [focal_state] + peer_states
        bench = df[df["state"].isin(benchmark_states)].copy()
        medians = {
            "net": benchmark_df["net_migration_rate"].median(),
            "young": benchmark_df["young_net_migration_rate"].median(),
            "rent": benchmark_df["rent_burden_30plus_rate"].median(),
        }
        peer_rows = []
        for _, row in bench.iterrows():
            peer_rows.append({
                "state": row["state"],
                "gap_net_rate_per_1k": round(float(row["net_migration_rate"] - medians["net"]), 2),
                "gap_young_rate_per_1k": round(float(row["young_net_migration_rate"] - medians["young"]), 2),
                "gap_rent_burden_pct": round(float(row["rent_burden_30plus_rate"] - medians["rent"]), 2),
            })
        return {
            **base_context,
            "peer_states": benchmark_states,
            "comparison_medians": {
                "net_migration_rate_per_1k": round(float(medians["net"]), 2),
                "young_net_migration_rate_per_1k": round(float(medians["young"]), 2),
                "rent_burden_30plus_pct": round(float(medians["rent"]), 2),
            },
            "peer_gap_rows": peer_rows,
        }

    if chart_id == "housing_young":
        top_positive = df.nlargest(3, "young_net_migration_rate")[["state", "young_net_migration_rate"]].round(2).to_dict("records")
        top_negative = df.nsmallest(3, "young_net_migration_rate")[["state", "young_net_migration_rate"]].round(2).to_dict("records")
        context = {
            **base_context,
            "axes": {
                "x": "Rent Burden (30%+)",
                "y": "Young Net Migration Rate (per 1k)",
            },
            "benchmark_lines": {
                "median_rent_burden_pct": round(float(df["rent_burden_30plus_rate"].median()), 1),
                "zero_young_net_rate": 0.0,
            },
            "top_positive_outliers": top_positive,
            "top_negative_outliers": top_negative,
        }
        if focal is not None:
            context["focal_point"] = {
                "rent_burden_30plus_pct": round(float(focal["rent_burden_30plus_rate"]), 1),
                "young_net_migration_rate_per_1k": round(float(focal["young_net_migration_rate"]), 2),
            }
        return context

    if chart_id == "earnings_net":
        top_positive = df.nlargest(3, "net_migration_rate")[["state", "net_migration_rate"]].round(2).to_dict("records")
        top_negative = df.nsmallest(3, "net_migration_rate")[["state", "net_migration_rate"]].round(2).to_dict("records")
        context = {
            **base_context,
            "axes": {
                "x": "Median Earnings: Bachelor's Degree ($)",
                "y": "Net Educated Migration Rate (per 1k)",
            },
            "benchmark_lines": {
                "median_bachelors_earnings_usd": round(float(df["median_earnings_bachelors"].median()), 0),
                "zero_net_rate": 0.0,
            },
            "top_positive_outliers": top_positive,
            "top_negative_outliers": top_negative,
        }
        if focal is not None:
            context["focal_point"] = {
                "median_earnings_bachelors_usd": round(float(focal["median_earnings_bachelors"]), 0),
                "net_migration_rate_per_1k": round(float(focal["net_migration_rate"]), 2),
            }
        return context

    raise ValueError(f"Unsupported chart_id: {chart_id}")


def get_methodology_notes() -> dict:
    return {"methodology_cautions": METHODOLOGY_NOTES}


def get_national_summary(df: pd.DataFrame) -> dict:
    top_positive = df.nlargest(5, "net_migration_rate")[["state", "net_migration_rate"]].round(2).to_dict("records")
    top_negative = df.nsmallest(5, "net_migration_rate")[["state", "net_migration_rate"]].round(2).to_dict("records")
    top_young_positive = df.nlargest(5, "young_net_migration_rate")[["state", "young_net_migration_rate"]].round(2).to_dict("records")
    bottom_young = df.nsmallest(5, "young_net_migration_rate")[["state", "young_net_migration_rate"]].round(2).to_dict("records")
    top_rent_burden = df.nlargest(5, "rent_burden_30plus_rate")[["state", "rent_burden_30plus_rate"]].round(2).to_dict("records")
    lowest_rent_burden = df.nsmallest(5, "rent_burden_30plus_rate")[["state", "rent_burden_30plus_rate"]].round(2).to_dict("records")
    top_talent = df.nlargest(5, "talent_concentration")[["state", "talent_concentration"]].round(2).to_dict("records")
    bottom_talent = df.nsmallest(5, "talent_concentration")[["state", "talent_concentration"]].round(2).to_dict("records")
    segment_counts = df["segment"].value_counts().to_dict()
    return {
        "scope": "national_dashboard_summary",
        "state_count": int(df["state"].nunique()),
        "medians": {
            "net_migration_rate_per_1k": round(float(df["net_migration_rate"].median()), 2),
            "young_net_migration_rate_per_1k": round(float(df["young_net_migration_rate"].median()), 2),
            "talent_concentration_pct": round(float(df["talent_concentration"].median()), 1),
            "rent_burden_30plus_pct": round(float(df["rent_burden_30plus_rate"].median()), 1),
            "bachelors_earnings_premium_usd": round(float(df["bachelors_earnings_premium"].median()), 0),
        },
        "leaders": {
            "top_net_migration_states": top_positive,
            "bottom_net_migration_states": top_negative,
            "top_young_migration_states": top_young_positive,
            "bottom_young_migration_states": bottom_young,
            "highest_rent_burden_states": top_rent_burden,
            "lowest_rent_burden_states": lowest_rent_burden,
            "highest_talent_concentration_states": top_talent,
            "lowest_talent_concentration_states": bottom_talent,
        },
        "segment_counts": segment_counts,
        "methodology_cautions": METHODOLOGY_NOTES,
    }


def get_full_dashboard_context(df: pd.DataFrame, top_n: int = 10) -> dict:
    leaderboard_metrics = [
        "net_migration_rate",
        "young_net_migration_rate",
        "talent_concentration",
        "rent_burden_30plus_rate",
        "bachelors_earnings_premium",
    ]
    leaderboards = {}
    for metric in leaderboard_metrics:
        leaderboards[metric] = {
            "top": df.nlargest(top_n, metric)[["state", metric]].round(2).to_dict("records"),
            "bottom": df.nsmallest(top_n, metric)[["state", metric]].round(2).to_dict("records"),
        }
    state_metric_rows = df[
        [
            "state",
            "net_migration_rate",
            "young_net_migration_rate",
            "talent_concentration",
            "rent_burden_30plus_rate",
            "bachelors_earnings_premium",
            "median_earnings_bachelors",
            "segment",
        ]
    ].round(2).to_dict("records")
    return {
        "scope": "full_dashboard_context",
        "state_count": int(df["state"].nunique()),
        "metrics_available": list(DISPLAY_LABELS.values()),
        "national_medians": {
            metric: round(float(df[metric].median()), 2)
            for metric in leaderboard_metrics + ["median_earnings_bachelors"]
        },
        "leaderboards": leaderboards,
        "state_metric_rows": state_metric_rows,
        "segment_counts": df["segment"].value_counts().to_dict(),
        "methodology_cautions": METHODOLOGY_NOTES,
    }


def analyze_metric_relationship(df: pd.DataFrame, metric_a: str, metric_b: str, top_n: int = 10) -> dict:
    metric_df = df[["state", metric_a, metric_b]].dropna().copy()
    correlation = metric_df[metric_a].corr(metric_df[metric_b])
    strongest_metric_a = metric_df.nlargest(top_n, metric_a)[["state", metric_a, metric_b]].round(2).to_dict("records")
    strongest_metric_b = metric_df.nlargest(top_n, metric_b)[["state", metric_a, metric_b]].round(2).to_dict("records")
    return {
        "scope": "metric_relationship",
        "metric_a": metric_a,
        "metric_a_label": DISPLAY_LABELS.get(metric_a, metric_a),
        "metric_b": metric_b,
        "metric_b_label": DISPLAY_LABELS.get(metric_b, metric_b),
        "correlation": round(float(correlation), 3) if pd.notna(correlation) else None,
        "rows": metric_df.round(2).to_dict("records"),
        "top_metric_a_rows": strongest_metric_a,
        "top_metric_b_rows": strongest_metric_b,
        "methodology_cautions": METHODOLOGY_NOTES,
    }


def get_state_metrics(df: pd.DataFrame, state: str) -> dict:
    focal = _state_row(df, state)
    return {
        "state": state,
        "metrics": {
            "educated_in_migrants": int(focal["interstate_in_educated"]),
            "educated_out_migrants_est": int(focal["interstate_out_educated"]),
            "net_educated_migrants": int(focal["net_educated_migrants"]),
            "net_migration_rate_per_1k": round(float(focal["net_migration_rate"]), 2),
            "young_net_migration_rate_per_1k": round(float(focal["young_net_migration_rate"]), 2),
            "talent_concentration_pct": round(float(focal["talent_concentration"]), 1),
            "rent_burden_30plus_pct": round(float(focal["rent_burden_30plus_rate"]), 1),
            "bachelors_earnings_premium_usd": round(float(focal["bachelors_earnings_premium"]), 0),
            "policy_segment": focal["segment"],
        },
        "methodology_cautions": METHODOLOGY_NOTES,
    }


def compare_states(df: pd.DataFrame, state_a: str, state_b: str) -> dict:
    metrics = [
        ("net_migration_rate_per_1k", "net_migration_rate"),
        ("young_net_migration_rate_per_1k", "young_net_migration_rate"),
        ("talent_concentration_pct", "talent_concentration"),
        ("rent_burden_30plus_pct", "rent_burden_30plus_rate"),
        ("bachelors_earnings_premium_usd", "bachelors_earnings_premium"),
    ]
    row_a = _state_row(df, state_a)
    row_b = _state_row(df, state_b)
    comparisons = []
    for label, col in metrics:
        a_value = round(float(row_a[col]), 2)
        b_value = round(float(row_b[col]), 2)
        comparisons.append({"metric": label, state_a: a_value, state_b: b_value})
    return {
        "states": [state_a, state_b],
        "comparisons": comparisons,
        "methodology_cautions": METHODOLOGY_NOTES,
    }


def rank_states(df: pd.DataFrame, metric: str, top_n: int = 5, ascending: bool = False) -> dict:
    ranked = df[["state", metric]].dropna().sort_values(metric, ascending=ascending).head(top_n)
    rows = []
    for _, row in ranked.iterrows():
        rows.append({"state": row["state"], metric: round(float(row[metric]), 2)})
    return {
        "metric": metric,
        "top_n": top_n,
        "ascending": ascending,
        "rows": rows,
        "methodology_cautions": METHODOLOGY_NOTES,
    }


def find_peer_states(df: pd.DataFrame, state: str, top_n: int = 5) -> dict:
    focal = _state_row(df, state)
    features = [
        "net_migration_rate",
        "young_net_migration_rate",
        "talent_concentration",
        "rent_burden_30plus_rate",
        "bachelors_earnings_premium",
    ]
    candidates = df[df["state"] != state].copy()
    candidates["distance"] = 0.0
    for feature in features:
        scale = df[feature].std() or 1.0
        candidates["distance"] += ((candidates[feature] - focal[feature]) / scale) ** 2
    nearest = candidates.nsmallest(top_n, "distance")[["state", "distance"]]
    return {
        "state": state,
        "peer_states": [
            {"state": row["state"], "distance": round(float(row["distance"]), 2)}
            for _, row in nearest.iterrows()
        ],
        "methodology_cautions": METHODOLOGY_NOTES,
    }


def identify_states_from_question(question: str, all_states: list[str], focal_state: str) -> list[str]:
    lower_question = question.lower()
    matches = [state for state in all_states if state.lower() in lower_question]
    if not matches:
        return [focal_state]
    seen = []
    for state in matches:
        if state not in seen:
            seen.append(state)
    return seen


def route_chat_question(
    df: pd.DataFrame,
    question: str,
    focal_state: str,
    all_states: list[str],
    peer_states: list[str] | None = None,
) -> dict:
    question_lower = question.lower()
    mentioned_states = identify_states_from_question(question, all_states, focal_state)
    relationship_metrics = []
    for phrase, metric in RELATIONSHIP_METRIC_MAP.items():
        if phrase in question_lower and metric not in relationship_metrics:
            relationship_metrics.append(metric)

    if any(word in question_lower for word in ["methodology", "limit", "proxy", "acs", "caution"]):
        return {"tool_name": "get_methodology_notes", "tool_payload": get_methodology_notes()}

    if any(word in question_lower for word in ["overall", "national", "all states", "entire dataset", "dashboard overall", "whole data", "complete census data", "full dashboard"]):
        return {"tool_name": "get_full_dashboard_context", "tool_payload": get_full_dashboard_context(df)}

    if len(relationship_metrics) >= 2:
        return {
            "tool_name": "analyze_metric_relationship",
            "tool_payload": analyze_metric_relationship(df, relationship_metrics[0], relationship_metrics[1]),
        }

    if any(word in question_lower for word in ["summary", "overview"]) and not mentioned_states:
        return {"tool_name": "get_national_summary", "tool_payload": get_national_summary(df)}

    if any(word in question_lower for word in ["peer", "similar"]):
        target_state = mentioned_states[0] if mentioned_states else focal_state
        return {"tool_name": "find_peer_states", "tool_payload": find_peer_states(df, target_state)}

    if any(word in question_lower for word in ["compare", "versus", "vs"]):
        if len(relationship_metrics) >= 2:
            return {
                "tool_name": "analyze_metric_relationship",
                "tool_payload": analyze_metric_relationship(df, relationship_metrics[0], relationship_metrics[1]),
            }
        if len(mentioned_states) < 2:
            return {"tool_name": "get_full_dashboard_context", "tool_payload": get_full_dashboard_context(df)}
        if len(mentioned_states) == 1:
            state_a, state_b = focal_state, mentioned_states[0]
        else:
            state_a = mentioned_states[0]
            state_b = mentioned_states[1] if len(mentioned_states) > 1 else focal_state
        return {"tool_name": "compare_states", "tool_payload": compare_states(df, state_a, state_b)}

    if any(word in question_lower for word in ["rank", "top", "bottom", "highest", "lowest"]):
        metric_map = {
            "young": "young_net_migration_rate",
            "rent": "rent_burden_30plus_rate",
            "earn": "bachelors_earnings_premium",
            "talent": "talent_concentration",
        }
        metric = "net_migration_rate"
        for key, value in metric_map.items():
            if key in question_lower:
                metric = value
                break
        ascending = any(word in question_lower for word in ["bottom", "lowest"])
        return {"tool_name": "rank_states", "tool_payload": rank_states(df, metric, ascending=ascending)}

    if any(word in question_lower for word in ["chart", "map", "scatter", "quadrant"]):
        chart_id = "quadrant"
        if "housing" in question_lower or "young" in question_lower:
            chart_id = "housing_young"
        elif "earn" in question_lower or "wage" in question_lower:
            chart_id = "earnings_net"
        elif "geo" in question_lower or "choropleth" in question_lower or "map" in question_lower:
            chart_id = "choropleth"
        elif "peer" in question_lower or "gap" in question_lower:
            chart_id = "peer_gaps"
        return {
            "tool_name": "get_chart_summary",
            "tool_payload": build_chart_context(df, chart_id, focal_state, peer_states=peer_states),
        }

    return {"tool_name": "get_state_metrics", "tool_payload": get_state_metrics(df, mentioned_states[0])}
