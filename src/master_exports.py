import hashlib
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


PROCESSED_DIR = Path("data/processed")
ENRICHMENT_DIR = Path("outputs/enrichment")
EMAIL_DIR = Path("outputs/email_drafts")
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
    processed_path = get_latest_file(PROCESSED_DIR, "*_normalized_scored.csv")
    enrichment_path = get_expected_artifact_path(processed_path, ENRICHMENT_DIR, "_enriched.csv")
    if enrichment_path is None:
        enrichment_path = get_latest_file(ENRICHMENT_DIR, "*_enriched.csv")

    email_path = get_expected_artifact_path(enrichment_path, EMAIL_DIR, "_email_drafts.csv")
    if email_path is None:
        email_path = get_latest_file(EMAIL_DIR, "*_email_drafts.csv")

    return {
        "processed": processed_path,
        "enrichment": enrichment_path,
        "email": email_path,
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


def build_master_exports(
    processed_df: pd.DataFrame,
    enrichment_df: pd.DataFrame,
    email_df: pd.DataFrame,
) -> dict[str, pd.DataFrame]:
    processed = processed_df.copy()
    enrichment = enrichment_df.copy()
    email = email_df.copy()

    for frame in [processed, enrichment, email]:
        for column in ["hotel_name_normalized", "city", "website_domain", "source_file"]:
            ensure_column(frame, column)
        frame["account_join_key"] = build_join_key(frame)

    accounts = processed.copy()
    accounts["account_id"] = accounts.apply(build_account_id, axis=1)
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

    enrichment_merge = enrichment.copy()
    enrichment_merge["account_id"] = enrichment_merge.apply(build_account_id, axis=1)
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
            "give_first_insight",
            "main_observed_issue",
            "proof_snippet",
            "primary_email_goal",
            "confidence_reason",
            "review_bucket",
            "owner_gm_decision_cycle_signal",
            "contact_discovery_likelihood",
            "ota_visibility_signal",
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

    outreach_merge = email.copy()
    outreach_merge["account_id"] = outreach_merge.apply(build_account_id, axis=1)
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
            "email_angle",
            "cta_type",
            "variant_id",
            "test_batch",
            "reply_outcome",
            "ranking_score",
            "priority_band",
            "ranking_reason",
            "review_bucket",
            "review_flag",
            "review_reason",
            "active_icp_profile",
            "source_file",
        ]
    ].copy()

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
                "manual_review_needed",
                "manual_review_reason",
            ]
        ].copy()

    ranking_tuning = load_ranking_tuning_config().get("ranking_tuning", {})
    shortlist_bands = {
        normalize_text(value) for value in ranking_tuning.get("operator_shortlist_priority_bands", ["High", "Medium-High"])
    }
    include_review_flag = bool(ranking_tuning.get("operator_shortlist_include_review_flag", True))
    shortlist_mask = accounts_master["priority_band"].fillna("").astype(str).str.strip().isin(shortlist_bands)
    if include_review_flag:
        shortlist_mask = shortlist_mask | accounts_master["review_flag"].fillna("").astype(str).str.strip().eq("yes")
    operator_shortlist = accounts_master[shortlist_mask].copy()

    return {
        "accounts_master": accounts_master.sort_values("ranking_score", ascending=False).reset_index(drop=True),
        "enrichment_master": enrichment_master.sort_values("account_id").reset_index(drop=True),
        "outreach_drafts": outreach_drafts.sort_values("ranking_score", ascending=False).reset_index(drop=True),
        "dedupe_review": dedupe_review.reset_index(drop=True),
        "operator_shortlist": operator_shortlist.sort_values(["priority_score", "ranking_score"], ascending=[False, False]).reset_index(drop=True),
    }


def save_master_exports(exports: dict[str, pd.DataFrame], processed_path: Path) -> dict[str, Path]:
    MASTER_DIR.mkdir(parents=True, exist_ok=True)
    batch_stem = processed_path.stem.replace("_normalized_scored", "")
    output_paths: dict[str, Path] = {}

    for name, df in exports.items():
        output_path = MASTER_DIR / f"{batch_stem}_{name}.csv"
        df.to_csv(output_path, index=False)
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

    if processed_df.empty or enrichment_df.empty or email_df.empty:
        print("Chýba jeden z required artifactov pre master exporty.")
        return

    exports = build_master_exports(processed_df, enrichment_df, email_df)
    output_paths = save_master_exports(exports, processed_path)

    print(f"Načítaný batch: {processed_path.name}")
    for name, output_path in output_paths.items():
        print(f"{name} uložený do: {output_path}")


if __name__ == "__main__":
    main()
