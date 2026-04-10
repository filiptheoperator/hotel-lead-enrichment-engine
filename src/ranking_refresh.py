import json
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


ENRICHMENT_DIR = Path("outputs/enrichment")
FACTUAL_ENRICHMENT_DIR = Path("outputs/factual_enrichment")
COMMERCIAL_SYNTHESIS_DIR = Path("outputs/commercial_synthesis")
RANKED_DIR = Path("outputs/ranked")
RANKING_CONFIG_PATH = Path("configs/ranking_tuning.yaml")
UNKNOWN_VALUE_LABEL = "Verejne nepotvrdené"
CANONICAL_COMMERCIAL_SCHEMA_VERSION = "commercial_synthesis/v3-lite"


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_config(config_path: Path = RANKING_CONFIG_PATH) -> dict:
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def get_ranking_config() -> dict:
    config = load_config().get("ranking_tuning", {})
    return {
        "weights": config.get(
            "weights",
            {
                "commercial_verdict": {
                    "silný prospect": 6.0,
                    "zaujímavý prospect": 3.0,
                    "opatrný prospect": -2.0,
                },
                "ownership_confidence": {
                    "public_confirmed": 1.5,
                    "raw_confirmed": 0.5,
                    UNKNOWN_VALUE_LABEL: -0.5,
                },
                "factual_completeness": {
                    "0": -1.0,
                    "1": 0.5,
                    "2": 1.5,
                    "3": 2.0,
                },
                "review_strength": {
                    "strong": 1.0,
                    "weak": -1.0,
                },
                "commercial_read": {
                    "best_entry_angle_present": 1.0,
                    "service_complexity_present": 0.8,
                    "why_commercially_interesting_present": 1.2,
                },
                "missingness_penalties": {
                    "opening_hours_missing": -0.5,
                    "checkin_missing": -0.5,
                    "room_count_missing": -0.5,
                },
                "uncertainty_penalties": {
                    "per_note": -0.2,
                    "max_penalty": -1.0,
                    "ambiguous_hook": -0.5,
                },
            },
        ),
        "thresholds": config.get(
            "thresholds",
            {
                "priority_levels": {
                    "High": 85,
                    "Medium-High": 75,
                    "Medium": 65,
                },
                "rank_buckets": {
                    "A": 85,
                    "B": 75,
                    "C": 65,
                },
                "review_score_strong_min": 4.5,
                "review_score_weak_max": 4.0,
            },
        ),
        "shortlist": config.get(
            "shortlist",
            {
                "operator_shortlist_limit": 100,
                "operator_shortlist_priority_levels": ["High", "Medium-High"],
                "top_export_limit": 20,
            },
        ),
        "review_queue": config.get(
            "review_queue",
            {
                "enabled": True,
                "low_factual_completeness_max": 1,
                "weak_ownership_statuses": [UNKNOWN_VALUE_LABEL, "", "unknown"],
                "review_queue_limit": 100,
            },
        ),
    }


def get_latest_enrichment_file() -> Optional[Path]:
    files = sorted(ENRICHMENT_DIR.glob("*_enriched*.csv"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def build_source_batch_stem(value: str) -> str:
    stem = Path(normalize_text(value)).stem
    for marker in [
        "_normalized_scored_enriched",
        "_normalized_scored",
        "_enriched",
    ]:
        if marker in stem:
            return stem.split(marker, 1)[0]
    return stem


def build_final_priority_band(final_score: float, thresholds: dict) -> str:
    priority_thresholds = thresholds.get("priority_levels", {})
    if final_score >= float(priority_thresholds.get("High", 85)):
        return "High"
    if final_score >= float(priority_thresholds.get("Medium-High", 75)):
        return "Medium-High"
    if final_score >= float(priority_thresholds.get("Medium", 65)):
        return "Medium"
    return "Low"


def build_final_rank_bucket(final_score: float, thresholds: dict) -> str:
    bucket_thresholds = thresholds.get("rank_buckets", {})
    if final_score >= float(bucket_thresholds.get("A", 85)):
        return "A"
    if final_score >= float(bucket_thresholds.get("B", 75)):
        return "B"
    if final_score >= float(bucket_thresholds.get("C", 65)):
        return "C"
    return "D"


def build_structured_row_context(row: pd.Series, source_batch_stem: str) -> dict[str, object]:
    account_id = normalize_text(row.get("account_id"))
    factual = load_json(FACTUAL_ENRICHMENT_DIR / source_batch_stem / f"{account_id}.json") if account_id else {}
    commercial = load_json(COMMERCIAL_SYNTHESIS_DIR / source_batch_stem / f"{account_id}.json") if account_id else {}
    commercial_schema_version = normalize_text(commercial.get("schema_version"))
    commercial_is_canonical = commercial_schema_version == CANONICAL_COMMERCIAL_SCHEMA_VERSION
    canonical_commercial = commercial if commercial_is_canonical else {}

    operating_hours = factual.get("operating_hours", {})
    checkin_checkout = factual.get("checkin_checkout", {})
    room_count_signal = factual.get("room_count_signal", {})
    ownership_signal = factual.get("ownership_company_signal", {})
    row_has_legacy_commercial_fallback = bool(normalize_text(row.get("commercial_verdict")))

    return {
        "commercial_schema_version": commercial_schema_version if commercial_is_canonical else "",
        "commercial_source_mode": "canonical_v3_lite" if commercial_is_canonical else "legacy_fallback_or_missing",
        "commercial_fallback_used": (
            "yes"
            if not commercial_is_canonical and row_has_legacy_commercial_fallback
            else "no"
        ),
        "commercial_verdict": normalize_text(canonical_commercial.get("verdict")),
        "business_interest_summary": normalize_text(canonical_commercial.get("business_interest_summary")),
        "main_bottleneck_hypothesis": normalize_text(canonical_commercial.get("main_bottleneck_hypothesis")),
        "pain_point_hypothesis": normalize_text(canonical_commercial.get("pain_point_hypothesis")),
        "why_commercially_interesting": normalize_text(canonical_commercial.get("why_commercially_interesting")),
        "property_positioning_summary": normalize_text(canonical_commercial.get("property_positioning_summary")),
        "best_entry_angle": normalize_text(canonical_commercial.get("best_entry_angle")),
        "recommended_hook": normalize_text(canonical_commercial.get("recommended_hook")),
        "recommended_first_contact_route": normalize_text(canonical_commercial.get("recommended_first_contact_route")),
        "likely_decision_maker_hypothesis": normalize_text(canonical_commercial.get("likely_decision_maker_hypothesis")),
        "service_complexity_read": normalize_text(canonical_commercial.get("service_complexity_read")),
        "commercial_complexity_read": normalize_text(canonical_commercial.get("commercial_complexity_read")),
        "direct_booking_friction_hypothesis": normalize_text(canonical_commercial.get("direct_booking_friction_hypothesis")),
        "contact_route_friction_hypothesis": normalize_text(canonical_commercial.get("contact_route_friction_hypothesis")),
        "call_hypothesis": normalize_text(canonical_commercial.get("call_hypothesis")),
        "uncertainty_notes_count": len(canonical_commercial.get("uncertainty_notes", []) or []),
        "hotel_opening_hours_status": normalize_text(operating_hours.get("status")),
        "checkin_checkout_status": normalize_text(checkin_checkout.get("status")),
        "room_count_status": normalize_text(room_count_signal.get("status")),
        "ownership_status": normalize_text(ownership_signal.get("status")),
    }


def build_factual_completeness_score(row: pd.Series) -> int:
    score = 0
    if normalize_text(row.get("hotel_opening_hours_status")) == "Overené vo verejnom zdroji":
        score += 1
    if normalize_text(row.get("checkin_checkout_status")) == "Overené vo verejnom zdroji":
        score += 1
    if normalize_text(row.get("room_count_status")) == "public_confirmed":
        score += 1
    return score


def is_ambiguous_hook(value: str) -> bool:
    lowered = normalize_text(value).lower()
    if not lowered:
        return True
    generic_markers = [
        "zlepšiť spoluprácu",
        "pomôcť",
        "možnosti spolupráce",
        "naším riešením",
    ]
    return any(marker in lowered for marker in generic_markers)


def add_reason(target: list[str], reason: str) -> None:
    if reason and reason not in target:
        target.append(reason)


def build_scoring_breakdown(row: pd.Series, config: dict) -> dict[str, object]:
    weights = config.get("weights", {})
    thresholds = config.get("thresholds", {})

    upside_reasons: list[str] = []
    downside_reasons: list[str] = []
    missingness_notes: list[str] = []

    commercial_verdict = normalize_text(row.get("commercial_verdict")).lower()
    ownership_status = normalize_text(row.get("ownership_status"))
    review_score = to_float(row.get("review_score"))
    factual_completeness = build_factual_completeness_score(row)
    uncertainty_notes_count = int(to_float(row.get("uncertainty_notes_count")))
    recommended_hook = normalize_text(row.get("recommended_hook"))
    best_entry_angle = normalize_text(row.get("best_entry_angle"))
    why_commercially_interesting = normalize_text(row.get("why_commercially_interesting"))
    service_complexity_read = normalize_text(row.get("service_complexity_read"))

    commercial_bonus = float(weights.get("commercial_verdict", {}).get(commercial_verdict, 0.0))
    if commercial_bonus > 0:
        add_reason(upside_reasons, f"commercial_verdict:{commercial_verdict}")
    elif commercial_bonus < 0:
        add_reason(downside_reasons, f"commercial_verdict:{commercial_verdict}")

    ownership_bonus = float(weights.get("ownership_confidence", {}).get(ownership_status, 0.0))
    if ownership_bonus > 0:
        add_reason(upside_reasons, f"ownership:{ownership_status}")
    elif ownership_bonus < 0:
        add_reason(downside_reasons, f"ownership:{ownership_status or 'unknown'}")

    factual_bonus = float(weights.get("factual_completeness", {}).get(str(factual_completeness), 0.0))
    if factual_bonus > 0:
        add_reason(upside_reasons, f"factual_completeness:{factual_completeness}")
    elif factual_bonus < 0:
        add_reason(downside_reasons, f"factual_completeness:{factual_completeness}")

    review_bonus = 0.0
    strong_min = float(thresholds.get("review_score_strong_min", 4.5))
    weak_max = float(thresholds.get("review_score_weak_max", 4.0))
    review_weights = weights.get("review_strength", {})
    if review_score >= strong_min:
        review_bonus = float(review_weights.get("strong", 0.0))
        add_reason(upside_reasons, "review_signal:strong")
    elif 0 < review_score < weak_max:
        review_bonus = float(review_weights.get("weak", 0.0))
        if review_bonus < 0:
            add_reason(downside_reasons, "review_signal:weak")

    commercial_read_weights = weights.get("commercial_read", {})
    commercial_read_bonus = 0.0
    if best_entry_angle:
        commercial_read_bonus += float(commercial_read_weights.get("best_entry_angle_present", 0.0))
        add_reason(upside_reasons, "entry_angle:present")
    if why_commercially_interesting:
        commercial_read_bonus += float(commercial_read_weights.get("why_commercially_interesting_present", 0.0))
        add_reason(upside_reasons, "commercial_read:present")
    if service_complexity_read:
        commercial_read_bonus += float(commercial_read_weights.get("service_complexity_present", 0.0))
        add_reason(upside_reasons, "service_complexity:present")

    missingness_penalty = 0.0
    missingness_weights = weights.get("missingness_penalties", {})
    for key, status_column in [
        ("opening_hours_missing", "hotel_opening_hours_status"),
        ("checkin_missing", "checkin_checkout_status"),
        ("room_count_missing", "room_count_status"),
    ]:
        status = normalize_text(row.get(status_column))
        is_missing = status in {"", UNKNOWN_VALUE_LABEL}
        if is_missing:
            penalty = float(missingness_weights.get(key, 0.0))
            missingness_penalty += penalty
            add_reason(downside_reasons, key)
            add_reason(missingness_notes, key)

    uncertainty_penalty = 0.0
    uncertainty_weights = weights.get("uncertainty_penalties", {})
    per_note = float(uncertainty_weights.get("per_note", 0.0))
    max_penalty = float(uncertainty_weights.get("max_penalty", 0.0))
    if uncertainty_notes_count > 0 and per_note != 0:
        uncertainty_penalty = max(uncertainty_notes_count * per_note, max_penalty)
        add_reason(downside_reasons, f"uncertainty_notes:{uncertainty_notes_count}")
        add_reason(missingness_notes, f"uncertainty_notes:{uncertainty_notes_count}")

    ambiguous_hook_penalty = 0.0
    if is_ambiguous_hook(recommended_hook):
        ambiguous_hook_penalty = float(uncertainty_weights.get("ambiguous_hook", 0.0))
        if ambiguous_hook_penalty < 0:
            add_reason(downside_reasons, "ambiguous_hook")
            add_reason(missingness_notes, "ambiguous_hook")

    total_bonus = (
        commercial_bonus
        + ownership_bonus
        + factual_bonus
        + review_bonus
        + commercial_read_bonus
        + missingness_penalty
        + uncertainty_penalty
        + ambiguous_hook_penalty
    )
    ranking_refresh_reason = " | ".join(upside_reasons + downside_reasons)

    return {
        "commercial_bonus": round(total_bonus, 2),
        "factual_completeness_score": factual_completeness,
        "ranking_refresh_reason": ranking_refresh_reason,
        "ranking_upside_reasons": " | ".join(upside_reasons),
        "ranking_downside_reasons": " | ".join(downside_reasons),
        "ranking_missingness_notes": " | ".join(missingness_notes),
        "review_strength_bonus": round(review_bonus, 2),
        "uncertainty_penalty": round(uncertainty_penalty + ambiguous_hook_penalty, 2),
    }


def build_review_queue_reason_codes(row: pd.Series, config: dict) -> str:
    review_config = config.get("review_queue", {})
    reason_codes: list[str] = []
    factual_max = int(review_config.get("low_factual_completeness_max", 1))
    high_uncertainty_notes_min = int(review_config.get("high_uncertainty_notes_min", 4))
    ambiguous_hook_factual_max = int(review_config.get("ambiguous_hook_factual_max", 0))
    force_manual_review_verdicts = {
        normalize_text(item).lower()
        for item in review_config.get("force_manual_review_verdicts", ["opatrný prospect"])
    }
    weak_ownership_statuses = {
        normalize_text(item)
        for item in review_config.get("weak_ownership_statuses", [UNKNOWN_VALUE_LABEL, "", "unknown"])
    }
    factual_score = int(to_float(row.get("factual_completeness_score")))
    ownership_status = normalize_text(row.get("ownership_status"))
    verdict = normalize_text(row.get("commercial_verdict")).lower()
    uncertainty_notes_count = int(to_float(row.get("uncertainty_notes_count")))

    if factual_score <= factual_max:
        add_reason(reason_codes, "low_factual_completeness")
    if ownership_status in weak_ownership_statuses:
        add_reason(reason_codes, "weak_ownership_confidence")
    if is_ambiguous_hook(normalize_text(row.get("recommended_hook"))) and factual_score <= ambiguous_hook_factual_max:
        add_reason(reason_codes, "ambiguous_commercial_hook")
    review_reason = normalize_text(row.get("review_reason"))
    if normalize_text(row.get("review_flag")).lower() == "yes" and review_reason != "out_of_profile_geography":
        add_reason(reason_codes, "legacy_review_flag")
    if uncertainty_notes_count >= high_uncertainty_notes_min:
        add_reason(reason_codes, "high_uncertainty")
    if verdict in force_manual_review_verdicts:
        add_reason(reason_codes, "cautious_verdict")

    return " | ".join(reason_codes)


def build_decision_status(row: pd.Series, config: dict) -> str:
    shortlist_config = config.get("shortlist", {})
    priority_levels = {
        normalize_text(item)
        for item in shortlist_config.get("operator_shortlist_priority_levels", ["High", "Medium-High"])
    }
    reason_codes = normalize_text(row.get("review_queue_reason_codes"))
    review_config = config.get("review_queue", {})
    override_config = review_config.get("outreach_override", {})
    override_allowed = bool(override_config.get("enabled", True))
    override_priority_levels = {
        normalize_text(item)
        for item in override_config.get("allowed_priority_levels", ["High", "Medium-High"])
    }
    override_verdicts = {
        normalize_text(item).lower()
        for item in override_config.get("allowed_verdicts", ["zaujímavý prospect", "silný prospect"])
    }
    override_reason_codes = {
        normalize_text(item)
        for item in override_config.get("allow_only_reason_codes", ["low_factual_completeness"])
    }
    raw_reason_codes = [
        part.strip()
        for part in reason_codes.split("|")
        if part.strip()
    ]
    can_override_to_outreach = (
        override_allowed
        and raw_reason_codes
        and set(raw_reason_codes).issubset(override_reason_codes)
        and normalize_text(row.get("priority_level_final")) in override_priority_levels
        and normalize_text(row.get("commercial_verdict")).lower() in override_verdicts
        and int(to_float(row.get("uncertainty_notes_count"))) <= int(override_config.get("max_uncertainty_notes", 0))
    )
    if can_override_to_outreach:
        return "outreach_now"
    if reason_codes:
        return "manual_review"
    if normalize_text(row.get("priority_level_final")) in priority_levels:
        return "outreach_now"
    return "hold_later"


def build_ranked_dataframe(enrichment_df: pd.DataFrame, source_batch_stem: str, config: dict) -> pd.DataFrame:
    ranked = enrichment_df.copy()
    for column in ranked.columns:
        if ranked[column].dtype == object:
            ranked[column] = ranked[column].apply(normalize_text)

    for column in [
        "commercial_schema_version",
        "commercial_source_mode",
        "commercial_fallback_used",
        "commercial_verdict",
        "business_interest_summary",
        "why_commercially_interesting",
        "property_positioning_summary",
        "main_bottleneck_hypothesis",
        "pain_point_hypothesis",
        "best_entry_angle",
        "recommended_hook",
        "recommended_first_contact_route",
        "likely_decision_maker_hypothesis",
        "service_complexity_read",
        "commercial_complexity_read",
        "direct_booking_friction_hypothesis",
        "contact_route_friction_hypothesis",
        "call_hypothesis",
        "uncertainty_notes_count",
        "room_count_status",
        "hotel_opening_hours_status",
        "checkin_checkout_status",
        "ownership_status",
    ]:
        if column not in ranked.columns:
            ranked[column] = ""

    structured_context = ranked.apply(
        lambda row: pd.Series(build_structured_row_context(row, source_batch_stem)),
        axis=1,
    )
    metadata_columns = {
        "commercial_schema_version",
        "commercial_source_mode",
        "commercial_fallback_used",
    }
    for column in structured_context.columns:
        if column in metadata_columns:
            ranked[column] = structured_context[column].fillna("").astype(str)
        else:
            ranked[column] = structured_context[column].where(
                structured_context[column].fillna("").astype(str).str.strip().ne(""),
                ranked[column],
            )

    scoring_breakdown = ranked.apply(
        lambda row: pd.Series(build_scoring_breakdown(row, config)),
        axis=1,
    )
    for column in scoring_breakdown.columns:
        ranked[column] = scoring_breakdown[column]

    ranked["ranking_score_final"] = (
        ranked["ranking_score"].apply(to_float) + ranked["commercial_bonus"].apply(to_float)
    ).round(2)
    ranked["priority_level_final"] = ranked["ranking_score_final"].apply(
        lambda value: build_final_priority_band(value, config.get("thresholds", {}))
    )
    ranked["rank_bucket_final"] = ranked["ranking_score_final"].apply(
        lambda value: build_final_rank_bucket(value, config.get("thresholds", {}))
    )
    ranked["review_queue_reason_codes"] = ranked.apply(
        lambda row: build_review_queue_reason_codes(row, config),
        axis=1,
    )
    ranked["manual_review_needed"] = ranked["review_queue_reason_codes"].apply(
        lambda value: "yes" if normalize_text(value) else "no"
    )
    ranked["decision_status"] = ranked.apply(lambda row: build_decision_status(row, config), axis=1)
    ranked["outreach_ready"] = ranked["decision_status"].apply(
        lambda value: "yes" if normalize_text(value) == "outreach_now" else "no"
    )
    ranked["shortlist_candidate"] = ranked["priority_level_final"].apply(
        lambda value: "yes"
        if normalize_text(value) in {
            normalize_text(item)
            for item in config.get("shortlist", {}).get("operator_shortlist_priority_levels", ["High", "Medium-High"])
        }
        else "no"
    )
    ranked = ranked.sort_values(
        ["ranking_score_final", "priority_score", "hotel_name"],
        ascending=[False, False, True],
    ).reset_index(drop=True)
    return ranked


def save_ranked_dataframe(df: pd.DataFrame, source_file: str, output_suffix: str = "") -> Path:
    RANKED_DIR.mkdir(parents=True, exist_ok=True)
    suffix = f"_{output_suffix}" if output_suffix else ""
    output_path = RANKED_DIR / f"{Path(source_file).stem}_ranking_refreshed{suffix}.csv"
    df.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    preferred_enrichment_file = normalize_text(os.getenv("RANKING_ENRICHMENT_SOURCE_FILE"))
    enrichment_path = (ENRICHMENT_DIR / preferred_enrichment_file) if preferred_enrichment_file else get_latest_enrichment_file()
    if enrichment_path is None or not enrichment_path.exists():
        print("Chýba enrichment CSV pre ranking refresh.")
        return

    enrichment_df = pd.read_csv(enrichment_path)
    source_batch_stem = build_source_batch_stem(enrichment_path.name)
    config = get_ranking_config()
    ranked_df = build_ranked_dataframe(enrichment_df, source_batch_stem, config)
    output_suffix = normalize_text(os.getenv("RANKING_OUTPUT_SUFFIX"))
    output_path = save_ranked_dataframe(ranked_df, enrichment_path.name, output_suffix=output_suffix)

    print(f"Načítaný enrichment súbor: {enrichment_path.name}")
    print(f"Počet riadkov: {len(ranked_df)}")
    print(f"Výstup uložený do: {output_path}")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(
        ranked_df[
            [
                "hotel_name",
                "commercial_verdict",
                "commercial_bonus",
                "factual_completeness_score",
                "ranking_score",
                "ranking_score_final",
                "priority_level_final",
                "decision_status",
                "review_queue_reason_codes",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
