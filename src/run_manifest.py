import json
from datetime import datetime
from pathlib import Path
from typing import Optional

import pandas as pd


PROCESSED_DIR = Path("data/processed")
ENRICHMENT_DIR = Path("outputs/enrichment")
EMAIL_DIR = Path("outputs/email_drafts")
CLICKUP_DIR = Path("outputs/clickup")
MASTER_DIR = Path("outputs/master")
QA_DIR = Path("data/qa")
RUN_MANIFEST_PATH = QA_DIR / "run_manifest.json"
CLICKUP_GATE_JSON_PATH = QA_DIR / "clickup_import_gate.json"
CLICKUP_GATE_TXT_PATH = QA_DIR / "clickup_import_gate.txt"
CLICKUP_GATE_HIGH_ONLY_JSON_PATH = QA_DIR / "clickup_import_gate_high_only.json"
CLICKUP_GATE_HIGH_ONLY_TXT_PATH = QA_DIR / "clickup_import_gate_high_only.txt"
READINESS_EXPLANATION_JSON_PATH = QA_DIR / "batch_readiness_explanation.json"
READINESS_EXPLANATION_TXT_PATH = QA_DIR / "batch_readiness_explanation.txt"
CLICKUP_DRY_RUN_SAMPLE_PATH = QA_DIR / "clickup_import_dry_run_sample.csv"
CLICKUP_DRY_RUN_NOTES_PATH = QA_DIR / "clickup_import_dry_run_notes.txt"
CLICKUP_DRY_RUN_HIGH_ONLY_SAMPLE_PATH = QA_DIR / "clickup_import_dry_run_sample_high_only.csv"
CLICKUP_DRY_RUN_HIGH_ONLY_NOTES_PATH = QA_DIR / "clickup_import_dry_run_notes_high_only.txt"
HIGH_LEADS_PREIMPORT_CHECKLIST_PATH = QA_DIR / "high_leads_preimport_checklist.csv"
HIGH_LEADS_PREIMPORT_NOTES_PATH = QA_DIR / "high_leads_preimport_checklist.txt"
OPERATOR_DECISION_SUMMARY_PATH = QA_DIR / "operator_decision_summary.txt"
OPERATOR_DECISION_SUMMARY_CSV_PATH = QA_DIR / "operator_decision_summary.csv"
OPERATOR_DECISION_SUMMARY_HIGH_PATH = QA_DIR / "operator_decision_summary_high.txt"
OPERATOR_DECISION_SUMMARY_HIGH_CSV_PATH = QA_DIR / "operator_decision_summary_high.csv"
ARCHIVE_CLEANUP_REPORT_PATH = QA_DIR / "archive_cleanup_report.txt"
CLICKUP_API_MAPPING_PREVIEW_PATH = QA_DIR / "clickup_api_mapping_preview.json"
CLICKUP_API_MAPPING_VALIDATION_PATH = QA_DIR / "clickup_api_mapping_validation.json"
CLICKUP_API_PAYLOAD_DIFF_PATH = QA_DIR / "clickup_api_payload_diff.json"


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

    clickup_path = get_expected_artifact_path(email_path, CLICKUP_DIR, "_clickup_import.csv")
    if clickup_path is None:
        clickup_path = get_latest_file(CLICKUP_DIR, "*_clickup_import.csv")

    clickup_high_only_path = get_expected_artifact_path(email_path, CLICKUP_DIR, "_clickup_import_high_only.csv")
    if clickup_high_only_path is None:
        clickup_high_only_path = get_latest_file(CLICKUP_DIR, "*_clickup_import_high_only.csv")
    clickup_phase1_minimal_path = get_expected_artifact_path(email_path, CLICKUP_DIR, "_clickup_phase1_minimal.csv")
    clickup_full_ranked_path = get_expected_artifact_path(email_path, CLICKUP_DIR, "_clickup_full_ranked.csv")

    batch_stem = processed_path.stem.replace("_normalized_scored", "") if processed_path else ""
    accounts_master_path = (MASTER_DIR / f"{batch_stem}_accounts_master.csv") if batch_stem else None
    enrichment_master_path = (MASTER_DIR / f"{batch_stem}_enrichment_master.csv") if batch_stem else None
    outreach_drafts_path = (MASTER_DIR / f"{batch_stem}_outreach_drafts.csv") if batch_stem else None
    dedupe_review_path = (MASTER_DIR / f"{batch_stem}_dedupe_review.csv") if batch_stem else None

    return {
        "processed": processed_path,
        "enrichment": enrichment_path,
        "email": email_path,
        "clickup": clickup_path,
        "clickup_high_only": clickup_high_only_path,
        "clickup_phase1_minimal": clickup_phase1_minimal_path if clickup_phase1_minimal_path and clickup_phase1_minimal_path.exists() else None,
        "clickup_full_ranked": clickup_full_ranked_path if clickup_full_ranked_path and clickup_full_ranked_path.exists() else None,
        "accounts_master": accounts_master_path if accounts_master_path and accounts_master_path.exists() else None,
        "enrichment_master": enrichment_master_path if enrichment_master_path and enrichment_master_path.exists() else None,
        "outreach_drafts": outreach_drafts_path if outreach_drafts_path and outreach_drafts_path.exists() else None,
        "dedupe_review": dedupe_review_path if dedupe_review_path and dedupe_review_path.exists() else None,
    }


def load_csv(file_path: Optional[Path]) -> pd.DataFrame:
    if file_path is None or not file_path.exists():
        return pd.DataFrame()
    return pd.read_csv(file_path)


def normalize_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series("", index=df.index, dtype="object")
    return df[column].fillna("").astype(str).str.strip()


def count_value(df: pd.DataFrame, column: str, value: str) -> int:
    return int(normalize_series(df, column).eq(value).sum())


def normalize_clickup_priority(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        return str(int(float(text)))
    except ValueError:
        return text


def build_run_manifest() -> dict:
    artifacts = get_current_batch_artifacts()
    processed_path = artifacts["processed"]
    enrichment_path = artifacts["enrichment"]
    email_path = artifacts["email"]
    clickup_path = artifacts["clickup"]
    clickup_high_only_path = artifacts["clickup_high_only"]
    clickup_phase1_minimal_path = artifacts["clickup_phase1_minimal"]
    clickup_full_ranked_path = artifacts["clickup_full_ranked"]
    accounts_master_path = artifacts["accounts_master"]
    enrichment_master_path = artifacts["enrichment_master"]
    outreach_drafts_path = artifacts["outreach_drafts"]
    dedupe_review_path = artifacts["dedupe_review"]
    qa_issues_path = QA_DIR / "qa_issues.csv"
    shortlist_path = QA_DIR / "manual_review_shortlist.csv"
    run_summary_path = QA_DIR / "run_summary.txt"
    run_delta_path = QA_DIR / "run_delta_report.txt"

    processed_df = load_csv(processed_path)
    enrichment_df = load_csv(enrichment_path)
    email_df = load_csv(email_path)
    clickup_df = load_csv(clickup_path)
    qa_issues_df = load_csv(qa_issues_path)
    shortlist_df = load_csv(shortlist_path)

    fetch_status = normalize_series(enrichment_df, "public_source_fetch_status")
    website_status = normalize_series(enrichment_df, "website")
    review_bucket = normalize_series(shortlist_df, "review_bucket")
    triage_action = normalize_series(shortlist_df, "operator_triage_action")
    normalized_clickup_priority = (
        clickup_df["Priority"].apply(normalize_clickup_priority)
        if "Priority" in clickup_df.columns
        else pd.Series("", index=clickup_df.index, dtype="object")
    )

    leads_with_website = int(website_status.ne("").sum())
    fetch_blocked_total = int(
        fetch_status.isin(["dns_resolution_failed", "dns_resolution_failed_fallback_previous"]).sum()
    )
    fetch_incident_flag = (
        "yes" if leads_with_website and (fetch_blocked_total / leads_with_website) >= 0.5 else "no"
    )

    source_files = sorted(
        {
            value
            for value in normalize_series(processed_df, "source_file").tolist()
            if value
        }
    )

    manifest = {
        "project": "Hotel Lead Enrichment Engine OS",
        "manifest_version": 1,
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "batch": {
            "source_files": source_files,
            "source_file_count": len(source_files),
        },
        "artifacts": {
            "processed_csv": str(processed_path) if processed_path else "",
            "enrichment_csv": str(enrichment_path) if enrichment_path else "",
            "email_drafts_csv": str(email_path) if email_path else "",
            "clickup_import_csv": str(clickup_path) if clickup_path else "",
            "clickup_import_high_only_csv": str(clickup_high_only_path) if clickup_high_only_path else "",
            "clickup_phase1_minimal_csv": str(clickup_phase1_minimal_path) if clickup_phase1_minimal_path else "",
            "clickup_full_ranked_csv": str(clickup_full_ranked_path) if clickup_full_ranked_path else "",
            "accounts_master_csv": str(accounts_master_path) if accounts_master_path else "",
            "enrichment_master_csv": str(enrichment_master_path) if enrichment_master_path else "",
            "outreach_drafts_csv": str(outreach_drafts_path) if outreach_drafts_path else "",
            "dedupe_review_csv": str(dedupe_review_path) if dedupe_review_path else "",
            "qa_issues_csv": str(qa_issues_path) if qa_issues_path.exists() else "",
            "manual_review_shortlist_csv": str(shortlist_path) if shortlist_path.exists() else "",
            "run_summary_txt": str(run_summary_path) if run_summary_path.exists() else "",
            "run_delta_report_txt": str(run_delta_path) if run_delta_path.exists() else "",
            "clickup_import_gate_json": str(CLICKUP_GATE_JSON_PATH) if CLICKUP_GATE_JSON_PATH.exists() else "",
            "clickup_import_gate_txt": str(CLICKUP_GATE_TXT_PATH) if CLICKUP_GATE_TXT_PATH.exists() else "",
            "clickup_import_gate_high_only_json": str(CLICKUP_GATE_HIGH_ONLY_JSON_PATH) if CLICKUP_GATE_HIGH_ONLY_JSON_PATH.exists() else "",
            "clickup_import_gate_high_only_txt": str(CLICKUP_GATE_HIGH_ONLY_TXT_PATH) if CLICKUP_GATE_HIGH_ONLY_TXT_PATH.exists() else "",
            "batch_readiness_explanation_json": str(READINESS_EXPLANATION_JSON_PATH) if READINESS_EXPLANATION_JSON_PATH.exists() else "",
            "batch_readiness_explanation_txt": str(READINESS_EXPLANATION_TXT_PATH) if READINESS_EXPLANATION_TXT_PATH.exists() else "",
            "clickup_import_dry_run_sample_csv": str(CLICKUP_DRY_RUN_SAMPLE_PATH) if CLICKUP_DRY_RUN_SAMPLE_PATH.exists() else "",
            "clickup_import_dry_run_notes_txt": str(CLICKUP_DRY_RUN_NOTES_PATH) if CLICKUP_DRY_RUN_NOTES_PATH.exists() else "",
            "clickup_import_dry_run_sample_high_only_csv": str(CLICKUP_DRY_RUN_HIGH_ONLY_SAMPLE_PATH) if CLICKUP_DRY_RUN_HIGH_ONLY_SAMPLE_PATH.exists() else "",
            "clickup_import_dry_run_notes_high_only_txt": str(CLICKUP_DRY_RUN_HIGH_ONLY_NOTES_PATH) if CLICKUP_DRY_RUN_HIGH_ONLY_NOTES_PATH.exists() else "",
            "high_leads_preimport_checklist_csv": str(HIGH_LEADS_PREIMPORT_CHECKLIST_PATH) if HIGH_LEADS_PREIMPORT_CHECKLIST_PATH.exists() else "",
            "high_leads_preimport_checklist_txt": str(HIGH_LEADS_PREIMPORT_NOTES_PATH) if HIGH_LEADS_PREIMPORT_NOTES_PATH.exists() else "",
            "operator_decision_summary_txt": str(OPERATOR_DECISION_SUMMARY_PATH) if OPERATOR_DECISION_SUMMARY_PATH.exists() else "",
            "operator_decision_summary_csv": str(OPERATOR_DECISION_SUMMARY_CSV_PATH) if OPERATOR_DECISION_SUMMARY_CSV_PATH.exists() else "",
            "operator_decision_summary_high_txt": str(OPERATOR_DECISION_SUMMARY_HIGH_PATH) if OPERATOR_DECISION_SUMMARY_HIGH_PATH.exists() else "",
            "operator_decision_summary_high_csv": str(OPERATOR_DECISION_SUMMARY_HIGH_CSV_PATH) if OPERATOR_DECISION_SUMMARY_HIGH_CSV_PATH.exists() else "",
            "archive_cleanup_report_txt": str(ARCHIVE_CLEANUP_REPORT_PATH) if ARCHIVE_CLEANUP_REPORT_PATH.exists() else "",
            "clickup_api_mapping_preview_json": str(CLICKUP_API_MAPPING_PREVIEW_PATH) if CLICKUP_API_MAPPING_PREVIEW_PATH.exists() else "",
            "clickup_api_mapping_validation_json": str(CLICKUP_API_MAPPING_VALIDATION_PATH) if CLICKUP_API_MAPPING_VALIDATION_PATH.exists() else "",
            "clickup_api_payload_diff_json": str(CLICKUP_API_PAYLOAD_DIFF_PATH) if CLICKUP_API_PAYLOAD_DIFF_PATH.exists() else "",
        },
        "row_counts": {
            "processed_rows": len(processed_df),
            "enrichment_rows": len(enrichment_df),
            "email_rows": len(email_df),
            "clickup_rows": len(clickup_df),
            "qa_issue_rows": len(qa_issues_df),
            "manual_review_shortlist_rows": len(shortlist_df),
        },
        "quality_snapshot": {
            "verified_opening_hours": count_value(
                enrichment_df, "hotel_opening_hours_status", "Overené vo verejnom zdroji"
            ),
            "verified_checkin_checkout": count_value(
                enrichment_df, "checkin_checkout_status", "Overené vo verejnom zdroji"
            ),
            "paired_checkin_checkout_verified": int(
                (
                    normalize_series(enrichment_df, "checkin_checkout_status").eq("Overené vo verejnom zdroji")
                    & normalize_series(enrichment_df, "checkin_checkout_completeness").eq("paired")
                ).sum()
            ),
            "single_side_checkin_checkout_verified": int(
                (
                    normalize_series(enrichment_df, "checkin_checkout_status").eq("Overené vo verejnom zdroji")
                    & normalize_series(enrichment_df, "checkin_checkout_completeness").eq("single_side")
                ).sum()
            ),
        },
        "fetch_health": {
            "fetch_incident_flag": fetch_incident_flag,
            "fetch_live_success": int(fetch_status.eq("ok").sum()),
            "fetch_dns_resolution_failed": int(fetch_status.eq("dns_resolution_failed").sum()),
            "fetch_dns_resolution_failed_fallback_previous": int(
                fetch_status.eq("dns_resolution_failed_fallback_previous").sum()
            ),
            "fetch_missing_website": int(fetch_status.eq("missing_website").sum()),
        },
        "shortlist_snapshot": {
            "review_bucket_counts": {
                bucket: int(count)
                for bucket, count in review_bucket.value_counts().to_dict().items()
            },
            "operator_triage_action_counts": {
                action: int(count)
                for action, count in triage_action.value_counts().to_dict().items()
            },
        },
        "import_snapshot": {
            "clickup_import_ready_rows": int(
                (
                    normalize_series(clickup_df, "Task name").ne("")
                    & normalize_series(clickup_df, "Status").ne("")
                    & normalized_clickup_priority.isin(["", "1", "2", "3", "4"])
                ).sum()
            ),
            "qa_blocking_rows": count_value(qa_issues_df, "blocking", "yes"),
        },
    }
    return manifest


def save_run_manifest(manifest: dict) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    RUN_MANIFEST_PATH.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return RUN_MANIFEST_PATH


def main() -> None:
    manifest = build_run_manifest()
    output_path = save_run_manifest(manifest)
    print(f"Run manifest uložený do: {output_path}")
    print("\nNáhľad:\n")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
