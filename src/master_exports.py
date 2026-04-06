import hashlib
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


PROCESSED_DIR = Path("data/processed")
ENRICHMENT_DIR = Path("outputs/enrichment")
EMAIL_DIR = Path("outputs/email_drafts")
RANKED_DIR = Path("outputs/ranked")
MASTER_DIR = Path("outputs/master")
RANKING_TUNING_CONFIG_PATH = Path("configs/ranking_tuning.yaml")


def get_latest_file(folder: Path, pattern: str) -> Optional[Path]:
    files = sorted(folder.glob(pattern), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def get_expected_artifact_path(base_file: Optional[Path], folder: Path, suffix: str) -> Optional[Path]:
    if base_file is None:
        return None
    expected = folder / f"{base_file.stem}{suffix}"
    return expected if expected.exists() else None


def get_current_batch_artifacts() -> dict[str, Optional[Path]]:
    preferred_processed = normalize_text(os.getenv("MASTER_PROCESSED_SOURCE_FILE"))
    preferred_enrichment = normalize_text(os.getenv("MASTER_ENRICHMENT_SOURCE_FILE"))
    preferred_email = normalize_text(os.getenv("MASTER_EMAIL_SOURCE_FILE"))
    preferred_ranked = normalize_text(os.getenv("MASTER_RANKED_SOURCE_FILE"))

    processed_path = (PROCESSED_DIR / preferred_processed) if preferred_processed else get_latest_file(PROCESSED_DIR, "*_normalized_scored.csv")
    if processed_path is not None and not processed_path.exists():
        processed_path = get_latest_file(PROCESSED_DIR, "*_normalized_scored.csv")

    enrichment_path = (ENRICHMENT_DIR / preferred_enrichment) if preferred_enrichment else get_expected_artifact_path(processed_path, ENRICHMENT_DIR, "_enriched.csv")
    if enrichment_path is not None and not enrichment_path.exists():
        enrichment_path = None
    if enrichment_path is None:
        enrichment_path = get_latest_file(ENRICHMENT_DIR, "*_enriched*.csv")

    email_path = (EMAIL_DIR / preferred_email) if preferred_email else get_expected_artifact_path(enrichment_path, EMAIL_DIR, "_email_drafts.csv")
    if email_path is not None and not email_path.exists():
        email_path = None
    if email_path is None:
        email_path = get_latest_file(EMAIL_DIR, "*_email_drafts*.csv")

    ranked_path = (RANKED_DIR / preferred_ranked) if preferred_ranked else get_expected_artifact_path(enrichment_path, RANKED_DIR, "_ranking_refreshed.csv")
    if ranked_path is not None and not ranked_path.exists():
        ranked_path = None
    if ranked_path is None and enrichment_path is not None:
        ranked_matches = sorted(
            RANKED_DIR.glob(f"{enrichment_path.stem}_ranking_refreshed*.csv"),
            key=lambda path: path.stat().st_mtime,
        )
        if ranked_matches:
            ranked_path = ranked_matches[-1]
    if ranked_path is None:
        ranked_path = get_latest_file(RANKED_DIR, "*_ranking_refreshed*.csv")

    return {
        "processed": processed_path,
        "enrichment": enrichment_path,
        "email": email_path,
        "ranked": ranked_path,
    }


def load_csv(path: Optional[Path]) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def build_join_key(df: pd.DataFrame) -> pd.Series:
    parts = [
        df.get("hotel_name_normalized", pd.Series("", index=df.index)).fillna("").astype(str).str.strip().str.lower(),
        df.get("city", pd.Series("", index=df.index)).fillna("").astype(str).str.strip().str.lower(),
        df.get("website_domain", pd.Series("", index=df.index)).fillna("").astype(str).str.strip().str.lower(),
        df.get("source_file", pd.Series("", index=df.index)).fillna("").astype(str).str.strip().str.lower(),
    ]
    return parts[0] + "|" + parts[1] + "|" + parts[2] + "|" + parts[3]


def build_account_id(row: pd.Series) -> str:
    raw = "|".join(
        [
            normalize_text(row.get("hotel_name_normalized")).lower(),
            normalize_text(row.get("city")).lower(),
            normalize_text(row.get("website_domain")).lower(),
            normalize_text(row.get("source_file")).lower(),
        ]
    )
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
    return f"acc_{digest}"


def ensure_column(df: pd.DataFrame, column: str, default: object = "") -> None:
    if column not in df.columns:
        df[column] = default


def load_ranking_tuning_config(config_path: Path = RANKING_TUNING_CONFIG_PATH) -> dict:
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def to_float(value: object) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return 0.0


def normalize_priority_level(value: str) -> str:
    normalized = normalize_text(value)
    if normalized:
        return normalized
    return "Low"


def build_master_exports(
    processed_df: pd.DataFrame,
    enrichment_df: pd.DataFrame,
    email_df: pd.DataFrame,
    ranked_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    processed = processed_df.copy()
    enrichment = enrichment_df.copy()
    email = email_df.copy()
    ranked = ranked_df.copy()

    for frame in [processed, enrichment, email, ranked]:
        for column in ["hotel_name_normalized", "city", "website_domain", "source_file"]:
            ensure_column(frame, column)
        frame["account_join_key"] = build_join_key(frame)
        ensure_column(frame, "account_id")

    if processed["account_id"].fillna("").astype(str).str.strip().eq("").all():
        processed["account_id"] = processed.apply(build_account_id, axis=1)
    if enrichment["account_id"].fillna("").astype(str).str.strip().eq("").all():
        enrichment["account_id"] = enrichment.apply(build_account_id, axis=1)
    if email["account_id"].fillna("").astype(str).str.strip().eq("").all():
        email["account_id"] = email.apply(build_account_id, axis=1)
    if not ranked.empty and ranked["account_id"].fillna("").astype(str).str.strip().eq("").all():
        ranked["account_id"] = ranked.apply(build_account_id, axis=1)

    for column in [
        "rooms_range",
        "room_count_value",
        "room_count_status",
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
        "commercial_verdict",
        "hotel_opening_hours_status",
        "checkin_checkout_status",
        "checkin_checkout_completeness",
        "hotel_opening_hours_source_type",
        "ownership_company_signal",
    ]:
        ensure_column(enrichment, column, "")

    accounts = processed.copy()
    accounts["account_id"] = accounts.apply(build_account_id, axis=1)
    relevant_account_ids = set()
    if not enrichment.empty:
        relevant_account_ids.update(
            enrichment["account_id"].fillna("").astype(str).str.strip().tolist()
        )
    if not email.empty:
        relevant_account_ids.update(
            email["account_id"].fillna("").astype(str).str.strip().tolist()
        )
    relevant_account_ids.discard("")
    if relevant_account_ids and len(relevant_account_ids) < len(accounts):
        accounts = accounts[accounts["account_id"].isin(relevant_account_ids)].copy()
    accounts["record_rank"] = range(1, len(accounts) + 1)
    accounts_master = accounts[
        [
            "account_id",
            "record_rank",
            "source_file",
            "hotel_name",
            "hotel_name_normalized",
            "country_code",
            "city",
            "state",
            "street",
            "website",
            "website_domain",
            "phone",
            "category_name",
            "hotel_type_class",
            "geography_fit",
            "independent_chain_class",
            "ownership_type",
            "review_score",
            "reviews_count",
            "icp_fit_score",
            "icp_fit_class",
            "non_icp_but_keep",
            "fit_confidence",
            "confidence_reason",
            "review_bucket",
            "owner_gm_decision_cycle_signal",
            "contact_discovery_likelihood",
            "ota_visibility_signal",
            "website_quality",
            "chain_signal_confidence",
            "contact_gap_reason",
            "contact_gap_count",
            "why_not_top_tier",
            "rank_bucket",
            "rank_bucket_reason",
            "ranking_reason",
            "ranking_score",
            "priority_score",
            "priority_band",
            "dedupe_status",
            "duplicate_group_id",
            "contact_duplicate_flag",
            "review_flag",
            "review_reason",
            "manual_merge_candidate",
            "source_url",
        ]
    ].copy()

    commercial_fields = enrichment[
        [
            "account_id",
            "rooms_range",
            "room_count_value",
            "room_count_status",
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
            "commercial_verdict",
            "hotel_opening_hours_status",
            "checkin_checkout_status",
            "checkin_checkout_completeness",
            "hotel_opening_hours_source_type",
            "ownership_company_signal",
        ]
    ].copy()
    commercial_fields = commercial_fields.rename(columns={"ownership_company_signal": "ownership_status"})
    accounts_master = accounts_master.merge(commercial_fields, on="account_id", how="left")

    ranking_fields = pd.DataFrame(columns=["account_id"])
    if not ranked.empty:
        for column in [
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
            "room_count_status",
            "hotel_opening_hours_status",
            "checkin_checkout_status",
            "ownership_status",
            "commercial_bonus",
            "factual_completeness_score",
            "ranking_score_final",
            "priority_level_final",
            "rank_bucket_final",
            "ranking_refresh_reason",
            "ranking_upside_reasons",
            "ranking_downside_reasons",
            "ranking_missingness_notes",
            "uncertainty_penalty",
            "decision_status",
            "manual_review_needed",
            "review_queue_reason_codes",
            "outreach_ready",
            "shortlist_candidate",
        ]:
            ensure_column(ranked, column, "")
        ranking_fields = ranked[
            [
                "account_id",
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
                "room_count_status",
                "hotel_opening_hours_status",
                "checkin_checkout_status",
                "ownership_status",
                "commercial_bonus",
                "factual_completeness_score",
                "ranking_score_final",
                "priority_level_final",
                "rank_bucket_final",
                "ranking_refresh_reason",
                "ranking_upside_reasons",
                "ranking_downside_reasons",
                "ranking_missingness_notes",
                "uncertainty_penalty",
                "decision_status",
                "manual_review_needed",
                "review_queue_reason_codes",
                "outreach_ready",
                "shortlist_candidate",
            ]
        ].copy()
        ranking_fields = ranking_fields.rename(
            columns={
                "commercial_verdict": "ranked_commercial_verdict",
                "business_interest_summary": "ranked_business_interest_summary",
                "why_commercially_interesting": "ranked_why_commercially_interesting",
                "property_positioning_summary": "ranked_property_positioning_summary",
                "main_bottleneck_hypothesis": "ranked_main_bottleneck_hypothesis",
                "pain_point_hypothesis": "ranked_pain_point_hypothesis",
                "best_entry_angle": "ranked_best_entry_angle",
                "recommended_hook": "ranked_recommended_hook",
                "recommended_first_contact_route": "ranked_recommended_first_contact_route",
                "likely_decision_maker_hypothesis": "ranked_likely_decision_maker_hypothesis",
                "service_complexity_read": "ranked_service_complexity_read",
                "commercial_complexity_read": "ranked_commercial_complexity_read",
                "direct_booking_friction_hypothesis": "ranked_direct_booking_friction_hypothesis",
                "contact_route_friction_hypothesis": "ranked_contact_route_friction_hypothesis",
                "call_hypothesis": "ranked_call_hypothesis",
                "room_count_status": "ranked_room_count_status",
                "hotel_opening_hours_status": "ranked_hotel_opening_hours_status",
                "checkin_checkout_status": "ranked_checkin_checkout_status",
                "ownership_status": "ranked_ownership_status",
            }
        )
        accounts_master = accounts_master.merge(ranking_fields, on="account_id", how="left")

        for target, ranked_column in [
            ("commercial_verdict", "ranked_commercial_verdict"),
            ("business_interest_summary", "ranked_business_interest_summary"),
            ("why_commercially_interesting", "ranked_why_commercially_interesting"),
            ("property_positioning_summary", "ranked_property_positioning_summary"),
            ("main_bottleneck_hypothesis", "ranked_main_bottleneck_hypothesis"),
            ("pain_point_hypothesis", "ranked_pain_point_hypothesis"),
            ("best_entry_angle", "ranked_best_entry_angle"),
            ("recommended_hook", "ranked_recommended_hook"),
            ("recommended_first_contact_route", "ranked_recommended_first_contact_route"),
            ("likely_decision_maker_hypothesis", "ranked_likely_decision_maker_hypothesis"),
            ("service_complexity_read", "ranked_service_complexity_read"),
            ("commercial_complexity_read", "ranked_commercial_complexity_read"),
            ("direct_booking_friction_hypothesis", "ranked_direct_booking_friction_hypothesis"),
            ("contact_route_friction_hypothesis", "ranked_contact_route_friction_hypothesis"),
            ("room_count_status", "ranked_room_count_status"),
            ("hotel_opening_hours_status", "ranked_hotel_opening_hours_status"),
            ("checkin_checkout_status", "ranked_checkin_checkout_status"),
            ("ownership_status", "ranked_ownership_status"),
        ]:
            accounts_master[target] = accounts_master[ranked_column].where(
                accounts_master[ranked_column].fillna("").astype(str).str.strip().ne(""),
                accounts_master[target],
            )
        accounts_master["commercial_bonus"] = accounts_master["commercial_bonus"].where(
            accounts_master["commercial_bonus"].fillna("").astype(str).str.strip().ne(""),
            accounts_master.get("commercial_bonus", 0),
        )
        accounts_master["factual_completeness_score"] = accounts_master["factual_completeness_score"].where(
            accounts_master["factual_completeness_score"].fillna("").astype(str).str.strip().ne(""),
            "",
        )
        accounts_master["ranking_score_final"] = accounts_master["ranking_score_final"].where(
            accounts_master["ranking_score_final"].fillna("").astype(str).str.strip().ne(""),
            "",
        )
        accounts_master["priority_level_final"] = accounts_master["priority_level_final"].where(
            accounts_master["priority_level_final"].fillna("").astype(str).str.strip().ne(""),
            "",
        )
        accounts_master["rank_bucket_final"] = accounts_master["rank_bucket_final"].where(
            accounts_master["rank_bucket_final"].fillna("").astype(str).str.strip().ne(""),
            "",
        )
        accounts_master["ranking_refresh_reason"] = accounts_master["ranking_refresh_reason"].where(
            accounts_master["ranking_refresh_reason"].fillna("").astype(str).str.strip().ne(""),
            "",
        )

    enrichment_merge = enrichment.copy()
    enrichment_merge["account_id"] = enrichment_merge["account_id"].where(
        enrichment_merge["account_id"].fillna("").astype(str).str.strip().ne(""),
        enrichment_merge.apply(build_account_id, axis=1),
    )
    enrichment_master = enrichment_merge[
        [
            "account_id",
            "hotel_name",
            "country_code",
            "city",
            "website",
            "phone",
            "hotel_type_class",
            "independent_chain_class",
            "direct_booking_weakness",
            "ota_dependency_signal_label",
            "hotel_opening_hours",
            "hotel_opening_hours_status",
            "hotel_opening_hours_source_url",
            "checkin_checkout_info",
            "checkin_checkout_status",
            "checkin_checkout_source_url",
            "checkin_checkout_completeness",
            "public_source_reachable",
            "public_source_fetch_status",
            "contact_status",
            "factual_summary",
            "rooms_range",
            "room_count_value",
            "room_count_status",
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
            "commercial_verdict",
            "give_first_insight",
            "main_observed_issue",
            "proof_snippet",
            "primary_email_goal",
            "confidence_reason",
            "review_bucket",
            "owner_gm_decision_cycle_signal",
            "contact_discovery_likelihood",
            "ota_visibility_signal",
            "website_quality",
            "chain_signal_confidence",
            "contact_gap_reason",
            "contact_gap_count",
            "why_not_top_tier",
            "rank_bucket",
            "rank_bucket_reason",
            "email_angle",
            "cta_type",
            "variant_id",
            "test_batch",
            "reply_outcome",
            "review_flag",
            "review_reason",
            "active_icp_profile",
            "source_file",
        ]
    ].copy()
    enrichment_master = enrichment_master.merge(
        accounts_master[
            [
                "account_id",
                "ranking_score_final",
                "priority_level_final",
                "rank_bucket_final",
                "ranking_refresh_reason",
                "ranking_upside_reasons",
                "ranking_downside_reasons",
                "ranking_missingness_notes",
                "decision_status",
                "manual_review_needed",
                "review_queue_reason_codes",
            ]
        ],
        on="account_id",
        how="left",
    )

    outreach_merge = email.copy()
    outreach_merge["account_id"] = outreach_merge["account_id"].where(
        outreach_merge["account_id"].fillna("").astype(str).str.strip().ne(""),
        outreach_merge.apply(build_account_id, axis=1),
    )
    outreach_drafts = outreach_merge[
        [
            "account_id",
            "hotel_name",
            "city",
            "subject_line",
            "hook",
            "personalization_line",
            "give_first_line",
            "relevance_line",
            "proof_line",
            "low_friction_cta",
            "cold_email",
            "followup_email",
            "primary_email_goal",
            "business_interest_summary",
            "why_commercially_interesting",
            "main_bottleneck_hypothesis",
            "best_entry_angle",
            "recommended_hook",
            "recommended_first_contact_route",
            "call_hypothesis",
            "commercial_verdict",
            "email_angle",
            "cta_type",
            "variant_id",
            "test_batch",
            "reply_outcome",
            "ranking_score",
            "priority_band",
            "why_not_top_tier",
            "rank_bucket",
            "rank_bucket_reason",
            "ranking_reason",
            "review_bucket",
            "review_flag",
            "review_reason",
            "active_icp_profile",
            "source_file",
        ]
    ].copy()
    outreach_drafts = outreach_drafts.merge(
        accounts_master[
            [
                "account_id",
                "ranking_score_final",
                "priority_level_final",
                "rank_bucket_final",
                "decision_status",
                "manual_review_needed",
                "review_queue_reason_codes",
            ]
        ],
        on="account_id",
        how="left",
    )

    dedupe_source = accounts.copy()
    dedupe_review = dedupe_source[
        (
            dedupe_source["dedupe_status"].fillna("").astype(str).str.strip().ne("unique")
            | dedupe_source["contact_duplicate_flag"].fillna("").astype(str).str.strip().eq("yes")
        )
    ].copy()
    if dedupe_review.empty:
        dedupe_review = pd.DataFrame(
            columns=[
                "account_id",
                "hotel_name",
                "city",
                "website_domain",
                "source_file",
                "dedupe_status",
                "duplicate_group_id",
                "contact_duplicate_flag",
                "dedupe_type",
                "match_basis",
                "merge_recommended",
                "manual_merge_candidate",
                "account_merge_notes",
                "manual_review_needed",
                "manual_review_reason",
            ]
        )
    else:
        dedupe_review["dedupe_type"] = dedupe_review["contact_duplicate_flag"].apply(
            lambda value: "contact_duplicate" if normalize_text(value) == "yes" else "account_duplicate"
        )
        dedupe_review["match_basis"] = dedupe_review["dedupe_type"].apply(
            lambda value: "account_identity_plus_contact" if value == "contact_duplicate" else "hotel_name_city_street_or_domain"
        )
        dedupe_review["merge_recommended"] = "yes"
        dedupe_review["manual_merge_candidate"] = dedupe_review["manual_merge_candidate"]
        dedupe_review["account_merge_notes"] = dedupe_review.apply(
            lambda row: (
                "Skontrolovať merge účtu a kontaktov."
                if normalize_text(row.get("manual_merge_candidate")) == "yes"
                else "Skontrolovať iba kontakt duplicitneho záznamu."
            ),
            axis=1,
        )
        dedupe_review["manual_review_needed"] = dedupe_review["review_flag"].apply(
            lambda value: "yes" if normalize_text(value) == "yes" else "no"
        )
        dedupe_review["manual_review_reason"] = dedupe_review["review_reason"]
        dedupe_review = dedupe_review[
            [
                "account_id",
                "hotel_name",
                "city",
                "website_domain",
                "source_file",
                "dedupe_status",
                "duplicate_group_id",
                "contact_duplicate_flag",
                "dedupe_type",
                "match_basis",
                "merge_recommended",
                "manual_merge_candidate",
                "account_merge_notes",
                "manual_review_needed",
                "manual_review_reason",
            ]
        ].copy()

    ranking_tuning = load_ranking_tuning_config().get("ranking_tuning", {})
    shortlist_config = ranking_tuning.get("shortlist", {})
    shortlist_levels = {
        normalize_text(value)
        for value in shortlist_config.get("operator_shortlist_priority_levels", ["High", "Medium-High"])
    }
    shortlist_limit = int(shortlist_config.get("operator_shortlist_limit", 100) or 100)
    operator_shortlist = accounts_master[
        accounts_master["decision_status"].fillna("").astype(str).str.strip().eq("outreach_now")
        | accounts_master["priority_level_final"].fillna("").astype(str).str.strip().isin(shortlist_levels)
    ].copy()
    operator_shortlist["shortlist_reason"] = operator_shortlist.apply(
        lambda row: " | ".join(
            [
                normalize_text(row.get("decision_status")),
                normalize_text(row.get("priority_level_final")),
                normalize_text(row.get("rank_bucket_final")),
                normalize_text(row.get("commercial_verdict")),
                normalize_text(row.get("ranking_upside_reasons")),
            ]
        ).strip(" |"),
        axis=1,
    )
    operator_shortlist = operator_shortlist.sort_values(
        ["ranking_score_final", "priority_score"], ascending=[False, False]
    ).head(shortlist_limit).reset_index(drop=True)
    operator_shortlist["artifact_scope"] = "shortlist_canonical"
    top_export_limit = int(shortlist_config.get("top_export_limit", 20) or 20)
    top_20_export = accounts_master.sort_values("ranking_score_final", ascending=False).head(top_export_limit).reset_index(drop=True)
    top_20_export["artifact_scope"] = "top_export_canonical"

    review_queue_limit = int(ranking_tuning.get("review_queue", {}).get("review_queue_limit", 100) or 100)
    review_queue = accounts_master[
        accounts_master["manual_review_needed"].fillna("").astype(str).str.strip().eq("yes")
    ].copy()
    review_queue["review_queue_summary"] = review_queue.apply(
        lambda row: " | ".join(
            [
                normalize_text(row.get("review_queue_reason_codes")),
                normalize_text(row.get("ranking_downside_reasons")),
                normalize_text(row.get("ranking_missingness_notes")),
            ]
        ).strip(" |"),
        axis=1,
    )
    review_queue = review_queue.sort_values(
        ["ranking_score_final", "priority_score"], ascending=[False, False]
    ).head(review_queue_limit).reset_index(drop=True)
    review_queue["artifact_scope"] = "review_queue_canonical"

    accounts_master["artifact_scope"] = "full_batch_canonical"
    enrichment_master["artifact_scope"] = "full_batch_canonical"
    outreach_drafts["artifact_scope"] = "full_batch_canonical"
    dedupe_review["artifact_scope"] = "dedupe_review_canonical"

    return {
        "accounts_master": accounts_master.sort_values("ranking_score_final", ascending=False).reset_index(drop=True),
        "enrichment_master": enrichment_master.sort_values("account_id").reset_index(drop=True),
        "outreach_drafts": outreach_drafts.sort_values("ranking_score_final", ascending=False).reset_index(drop=True),
        "dedupe_review": dedupe_review.reset_index(drop=True),
        "operator_shortlist": operator_shortlist,
        "review_queue": review_queue,
        "top_20_export": top_20_export,
    }


def save_master_exports(exports: dict[str, pd.DataFrame], processed_path: Path, output_suffix: str = "") -> dict[str, Path]:
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    batch_stem = processed_path.stem.replace("_normalized_scored", "")
    suffix = f"_{output_suffix}" if output_suffix else ""
    output_paths: dict[str, Path] = {}

    for name, df in exports.items():
        export_df = df.copy()
        for column in export_df.columns:
            if export_df[column].dtype == object:
                export_df[column] = export_df[column].fillna("").astype(str)
        output_path = MASTER_DIR / f"{batch_stem}_{name}{suffix}.csv"
        export_df.to_csv(output_path, index=False)
        output_paths[name] = output_path

    return output_paths


def main() -> None:
    artifacts = get_current_batch_artifacts()
    processed_path = artifacts["processed"]
    if processed_path is None:
        print("Chýba processed batch pre master exporty.")
        return

    processed_df = load_csv(artifacts["processed"])
    enrichment_df = load_csv(artifacts["enrichment"])
    email_df = load_csv(artifacts["email"])
    ranked_df = load_csv(artifacts["ranked"])

    if processed_df.empty or enrichment_df.empty or email_df.empty:
        print("Chýba jeden z required artifactov pre master exporty.")
        return

    exports = build_master_exports(processed_df, enrichment_df, email_df, ranked_df)
    output_suffix = normalize_text(os.getenv("MASTER_OUTPUT_SUFFIX"))
    output_paths = save_master_exports(exports, processed_path, output_suffix=output_suffix)

    print(f"Načítaný batch: {processed_path.name}")
    for name, output_path in output_paths.items():
        print(f"{name} uložený do: {output_path}")


if __name__ == "__main__":
    main()
