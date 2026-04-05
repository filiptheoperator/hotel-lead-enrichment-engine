from pathlib import Path
from typing import Optional

import pandas as pd
from pandas.errors import EmptyDataError


PROCESSED_DIR = Path("data/processed")
ENRICHMENT_DIR = Path("outputs/enrichment")
EMAIL_DIR = Path("outputs/email_drafts")
CLICKUP_DIR = Path("outputs/clickup")
QA_DIR = Path("data/qa")
RUN_REPORT_PATH = QA_DIR / "run_summary.txt"
RUN_DELTA_REPORT_PATH = QA_DIR / "run_delta_report.txt"
MANUAL_REVIEW_SHORTLIST_PATH = QA_DIR / "manual_review_shortlist.csv"
RUN_MANIFEST_PATH = QA_DIR / "run_manifest.json"
CLICKUP_GATE_TXT_PATH = QA_DIR / "clickup_import_gate.txt"
CLICKUP_GATE_JSON_PATH = QA_DIR / "clickup_import_gate.json"


def get_first_file(folder: Path, pattern: str) -> Optional[Path]:
    files = sorted(folder.glob(pattern), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def get_expected_artifact_path(base_file: Optional[Path], folder: Path, suffix: str) -> Optional[Path]:
    if base_file is None:
        return None
    expected = folder / f"{base_file.stem}{suffix}"
    return expected if expected.exists() else None


def get_current_batch_artifacts() -> dict[str, Optional[Path]]:
    processed_path = get_first_file(PROCESSED_DIR, "*_normalized_scored.csv")
    enrichment_path = get_expected_artifact_path(processed_path, ENRICHMENT_DIR, "_enriched.csv")
    if enrichment_path is None:
        enrichment_path = get_first_file(ENRICHMENT_DIR, "*_enriched.csv")

    email_path = get_expected_artifact_path(enrichment_path, EMAIL_DIR, "_email_drafts.csv")
    if email_path is None:
        email_path = get_first_file(EMAIL_DIR, "*_email_drafts.csv")

    clickup_path = get_expected_artifact_path(email_path, CLICKUP_DIR, "_clickup_import.csv")
    if clickup_path is None:
        clickup_path = get_first_file(CLICKUP_DIR, "*_clickup_import.csv")

    return {
        "processed": processed_path,
        "enrichment": enrichment_path,
        "email": email_path,
        "clickup": clickup_path,
    }


def load_csv(file_path: Optional[Path]) -> pd.DataFrame:
    if file_path is None:
        return pd.DataFrame()
    try:
        return pd.read_csv(file_path)
    except EmptyDataError:
        return pd.DataFrame()


def safe_count(series: pd.Series, expected_value: str) -> int:
    return int(series.fillna("").astype(str).str.strip().eq(expected_value).sum())


def normalize_series(df: pd.DataFrame, column: str) -> pd.Series:
    if column not in df.columns:
        return pd.Series("", index=df.index, dtype="object")
    return df[column].fillna("").astype(str).str.strip()


def build_run_summary() -> str:
    artifacts = get_current_batch_artifacts()
    processed_df = load_csv(artifacts["processed"])
    enrichment_df = load_csv(artifacts["enrichment"])
    email_df = load_csv(artifacts["email"])
    clickup_df = load_csv(artifacts["clickup"])
    qa_df = load_csv(QA_DIR / "qa_issues.csv")
    batch_readiness_score = "Neoverené"
    if CLICKUP_GATE_JSON_PATH.exists():
        try:
            import json
            gate_payload = json.loads(CLICKUP_GATE_JSON_PATH.read_text(encoding="utf-8"))
            batch_readiness_score = gate_payload.get("batch_readiness_score", "Neoverené")
        except Exception:
            batch_readiness_score = "Neoverené"

    verified_public_label = "Overené vo verejnom zdroji"
    unknown_value_label = "Verejne nepotvrdené"

    processed_rows = len(processed_df)
    enrichment_rows = len(enrichment_df)
    email_rows = len(email_df)
    clickup_rows = len(clickup_df)

    verified_opening_hours = 0
    unverified_opening_hours = 0
    verified_checkin_checkout = 0
    unverified_checkin_checkout = 0
    single_side_checkin_checkout_verified = 0
    paired_checkin_checkout_verified = 0
    checkin_checkout_source_origin_jsonld = 0
    checkin_checkout_source_origin_text = 0
    checkin_checkout_source_origin_text_homepage = 0
    checkin_checkout_source_origin_text_subpage_general = 0
    source_coverage_with_website = 0
    source_coverage_reachable = 0
    source_coverage_with_usable_public_source = 0
    reachable_but_missing_opening_hours = 0
    reachable_but_missing_checkin_checkout = 0
    fetch_dns_resolution_failed = 0
    fetch_dns_resolution_failed_fallback_previous = 0
    fetch_request_timeout = 0
    fetch_missing_website = 0
    fetch_live_success = 0
    fetch_blocked_total = 0
    fetch_blocked_without_fallback = 0
    fetch_effective_reachable_after_fallback = 0
    fetch_incident_flag = "no"
    needs_manual_review = 0
    if not enrichment_df.empty:
        opening_status = normalize_series(enrichment_df, "hotel_opening_hours_status")
        checkio_status = normalize_series(enrichment_df, "checkin_checkout_status")
        fetch_status = normalize_series(enrichment_df, "public_source_fetch_status")
        reachable_status = normalize_series(enrichment_df, "public_source_reachable")

        verified_opening_hours = safe_count(
            enrichment_df["hotel_opening_hours_status"], verified_public_label
        )
        unverified_opening_hours = safe_count(
            enrichment_df["hotel_opening_hours_status"], unknown_value_label
        )
        verified_checkin_checkout = safe_count(
            enrichment_df["checkin_checkout_status"], verified_public_label
        )
        unverified_checkin_checkout = safe_count(
            enrichment_df["checkin_checkout_status"], unknown_value_label
        )
        if "checkin_checkout_completeness" in enrichment_df.columns:
            single_side_checkin_checkout_verified = int(
                (
                    checkio_status.eq(verified_public_label)
                    & normalize_series(enrichment_df, "checkin_checkout_completeness").eq("single_side")
                ).sum()
            )
            paired_checkin_checkout_verified = int(
                (
                    checkio_status.eq(verified_public_label)
                    & normalize_series(enrichment_df, "checkin_checkout_completeness").eq("paired")
                ).sum()
            )
        if "checkin_checkout_source_origin" in enrichment_df.columns:
            checkin_checkout_source_origin_jsonld = int(
                normalize_series(enrichment_df, "checkin_checkout_source_origin").eq("jsonld").sum()
            )
            checkin_checkout_source_origin_text = int(
                normalize_series(enrichment_df, "checkin_checkout_source_origin").eq("text").sum()
            )
            if "checkin_checkout_source_type" in enrichment_df.columns:
                text_origin_mask = normalize_series(enrichment_df, "checkin_checkout_source_origin").eq("text")
                checkin_checkout_source_origin_text_homepage = int(
                    (
                        text_origin_mask
                        & normalize_series(enrichment_df, "checkin_checkout_source_type").eq("homepage")
                    ).sum()
                )
                checkin_checkout_source_origin_text_subpage_general = int(
                    (
                        text_origin_mask
                        & normalize_series(enrichment_df, "checkin_checkout_source_type").eq("subpage_general")
                    ).sum()
                )
        source_coverage_with_website = int(
            enrichment_df["website"].fillna("").astype(str).str.strip().ne("").sum()
        )
        if "public_source_reachable" in enrichment_df.columns:
            source_coverage_reachable = int(
                reachable_status.eq("yes").sum()
            )
            reachable_mask = reachable_status.eq("yes")
            reachable_but_missing_opening_hours = int(
                (
                    reachable_mask
                    & opening_status.eq(unknown_value_label)
                ).sum()
            )
            reachable_but_missing_checkin_checkout = int(
                (
                    reachable_mask
                    & checkio_status.eq(unknown_value_label)
                ).sum()
            )
        if "public_source_fetch_status" in enrichment_df.columns:
            fetch_dns_resolution_failed = int(
                fetch_status.eq("dns_resolution_failed").sum()
            )
            fetch_dns_resolution_failed_fallback_previous = int(
                fetch_status.eq("dns_resolution_failed_fallback_previous").sum()
            )
            fetch_request_timeout = int(
                fetch_status.eq("request_timeout").sum()
            )
            fetch_missing_website = int(
                fetch_status.eq("missing_website").sum()
            )
            fetch_live_success = int(fetch_status.eq("ok").sum())
            fetch_blocked_total = int(
                fetch_status.isin(["dns_resolution_failed", "dns_resolution_failed_fallback_previous"]).sum()
            )
            fetch_blocked_without_fallback = int(fetch_status.eq("dns_resolution_failed").sum())
            fetch_effective_reachable_after_fallback = int(
                (
                    reachable_status.eq("yes")
                    & fetch_status.eq("dns_resolution_failed_fallback_previous")
                ).sum()
            )
            website_leads = max(source_coverage_with_website, 0)
            if website_leads and (fetch_blocked_total / website_leads) >= 0.5:
                fetch_incident_flag = "yes"
        source_coverage_with_usable_public_source = int(
            (
                opening_status.eq(verified_public_label)
                | checkio_status.eq(verified_public_label)
            ).sum()
        )

    import_ready_rows = 0
    if not clickup_df.empty:
        required_columns = {"Task name", "Description content", "Status", "Priority"}
        if required_columns.issubset(set(clickup_df.columns)):
            task_name_ok = ~clickup_df["Task name"].fillna("").astype(str).str.strip().eq("")
            status_ok = ~clickup_df["Status"].fillna("").astype(str).str.strip().eq("")
            normalized_priority = (
                clickup_df["Priority"]
                .fillna("")
                .astype(str)
                .str.strip()
                .map(lambda value: str(int(float(value))) if value not in {"", "nan"} else "")
            )
            priority_ok = normalized_priority.isin(["", "1", "2", "3", "4"])
            import_ready_rows = int((task_name_ok & status_ok & priority_ok).sum())

    qa_blocking = 0
    qa_medium = 0
    qa_low = 0
    if not qa_df.empty:
        if "blocking" in qa_df.columns:
            qa_blocking = int(
                qa_df["blocking"].fillna("").astype(str).str.strip().eq("yes").sum()
            )
        qa_medium = int(
            qa_df["severity"].fillna("").astype(str).str.strip().eq("Medium").sum()
        )
        qa_low = int(
            qa_df["severity"].fillna("").astype(str).str.strip().eq("Low").sum()
        )
        needs_manual_review = int(
            qa_df["issue_type"]
            .fillna("")
            .astype(str)
            .str.strip()
            .isin(
                [
                    "missing_contact_data",
                    "unverified_opening_hours",
                    "unverified_checkin_checkout",
                    "missing_clickup_description",
                    "missing_clickup_status",
                ]
            )
            .sum()
        )

    lines = [
        "Hotel Lead Enrichment Engine OS - Run Summary",
        "",
        "Operator Start",
        f"- primary_operator_artifact: {RUN_MANIFEST_PATH}",
        f"- clickup_import_gate_artifact: {CLICKUP_GATE_TXT_PATH}",
        f"- batch_readiness_score: {batch_readiness_score}",
        "",
        "Processed",
        f"- processed_rows: {processed_rows}",
        f"- enrichment_rows: {enrichment_rows}",
        f"- email_rows: {email_rows}",
        f"- clickup_rows: {clickup_rows}",
        "",
        "Verified",
        f"- verified_opening_hours: {verified_opening_hours}",
        f"- verified_checkin_checkout: {verified_checkin_checkout}",
        f"- paired_checkin_checkout_verified: {paired_checkin_checkout_verified}",
        f"- single_side_checkin_checkout_verified: {single_side_checkin_checkout_verified}",
        "",
        "Unverified",
        f"- unverified_opening_hours: {unverified_opening_hours}",
        f"- unverified_checkin_checkout: {unverified_checkin_checkout}",
        "",
        "Source Coverage",
        f"- leads_with_website: {source_coverage_with_website}",
        f"- public_source_reachable: {source_coverage_reachable}",
        f"- usable_public_source: {source_coverage_with_usable_public_source}",
        f"- reachable_but_missing_opening_hours: {reachable_but_missing_opening_hours}",
        f"- reachable_but_missing_checkin_checkout: {reachable_but_missing_checkin_checkout}",
        f"- checkin_checkout_source_origin_jsonld: {checkin_checkout_source_origin_jsonld}",
        f"- checkin_checkout_source_origin_text: {checkin_checkout_source_origin_text}",
        f"- checkin_checkout_source_origin_text_homepage: {checkin_checkout_source_origin_text_homepage}",
        f"- checkin_checkout_source_origin_text_subpage_general: {checkin_checkout_source_origin_text_subpage_general}",
        "",
        "Fetch Health",
        f"- fetch_incident_flag: {fetch_incident_flag}",
        f"- fetch_live_success: {fetch_live_success}",
        f"- fetch_blocked_total: {fetch_blocked_total}",
        f"- fetch_dns_resolution_failed: {fetch_dns_resolution_failed}",
        f"- fetch_dns_resolution_failed_fallback_previous: {fetch_dns_resolution_failed_fallback_previous}",
        f"- fetch_blocked_without_fallback: {fetch_blocked_without_fallback}",
        f"- fetch_effective_reachable_after_fallback: {fetch_effective_reachable_after_fallback}",
        f"- fetch_request_timeout: {fetch_request_timeout}",
        f"- fetch_missing_website: {fetch_missing_website}",
        "",
        "Import Ready",
        f"- clickup_import_ready_rows: {import_ready_rows}",
        f"- clickup_not_ready_rows: {max(clickup_rows - import_ready_rows, 0)}",
        "",
        "Needs Manual Review",
        f"- qa_needs_manual_review_rows: {needs_manual_review}",
        f"- qa_blocking_rows: {qa_blocking}",
        f"- qa_medium_rows: {qa_medium}",
        f"- qa_low_rows: {qa_low}",
    ]
    return "\n".join(lines)


def build_run_delta_report() -> str:
    before_enriched_path = QA_DIR / "before_enriched.csv"
    before_shortlist_path = QA_DIR / "before_manual_review_shortlist.csv"
    current_enriched = load_csv(get_current_batch_artifacts()["enrichment"])
    current_shortlist = load_csv(MANUAL_REVIEW_SHORTLIST_PATH)
    before_enriched = load_csv(before_enriched_path)
    before_shortlist = load_csv(before_shortlist_path)

    lines = ["Hotel Lead Enrichment Engine OS - Run Delta Report", ""]

    if before_enriched.empty or current_enriched.empty:
        lines.append("Enrichment delta: neoverené, chýba before/current artifact.")
    else:
        before_checkio = normalize_series(before_enriched, "checkin_checkout_status")
        current_checkio = normalize_series(current_enriched, "checkin_checkout_status")
        before_fetch = normalize_series(before_enriched, "public_source_fetch_status")
        current_fetch = normalize_series(current_enriched, "public_source_fetch_status")
        before_verified = int(before_checkio.eq("Overené vo verejnom zdroji").sum())
        current_verified = int(current_checkio.eq("Overené vo verejnom zdroji").sum())
        before_unverified = int(before_checkio.eq("Verejne nepotvrdené").sum())
        current_unverified = int(current_checkio.eq("Verejne nepotvrdené").sum())
        before_fallback = int(before_fetch.eq("dns_resolution_failed_fallback_previous").sum())
        current_fallback = int(current_fetch.eq("dns_resolution_failed_fallback_previous").sum())
        before_dns_fail = int(before_fetch.eq("dns_resolution_failed").sum())
        current_dns_fail = int(current_fetch.eq("dns_resolution_failed").sum())
        lines.extend(
            [
                "Check-in / Check-out Delta",
                f"- verified_before: {before_verified}",
                f"- verified_after: {current_verified}",
                f"- verified_delta: {current_verified - before_verified}",
                f"- unverified_before: {before_unverified}",
                f"- unverified_after: {current_unverified}",
                f"- unverified_delta: {current_unverified - before_unverified}",
                "",
                "Fetch Delta",
                f"- dns_fallback_previous_before: {before_fallback}",
                f"- dns_fallback_previous_after: {current_fallback}",
                f"- dns_fallback_previous_delta: {current_fallback - before_fallback}",
                f"- dns_resolution_failed_before: {before_dns_fail}",
                f"- dns_resolution_failed_after: {current_dns_fail}",
                f"- dns_resolution_failed_delta: {current_dns_fail - before_dns_fail}",
                "",
            ]
        )
        if current_fallback or current_dns_fail:
            lines.extend(
                [
                    "Current Run Interpretation",
                    (
                        "- current_run_note: DNS/fallback incident ovplyvnil verejný web fetch; "
                        "quality delta treba čítať spolu s fetch metrikami."
                    ),
                    "",
                ]
            )

    if before_shortlist.empty or current_shortlist.empty:
        lines.append("Shortlist delta: neoverené, chýba before/current shortlist artifact.")
    else:
        before_counts = before_shortlist["review_bucket"].fillna("").astype(str).str.strip().value_counts()
        current_counts = current_shortlist["review_bucket"].fillna("").astype(str).str.strip().value_counts()
        lines.append("Shortlist Bucket Delta")
        for bucket in sorted(set(before_counts.index) | set(current_counts.index)):
            lines.append(
                f"- {bucket or '<empty>'}: before={int(before_counts.get(bucket, 0))}, after={int(current_counts.get(bucket, 0))}, delta={int(current_counts.get(bucket, 0) - before_counts.get(bucket, 0))}"
            )

    return "\n".join(lines)


def save_run_summary(summary_text: str) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    RUN_REPORT_PATH.write_text(summary_text, encoding="utf-8")
    return RUN_REPORT_PATH


def save_run_delta_report(delta_text: str) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    RUN_DELTA_REPORT_PATH.write_text(delta_text, encoding="utf-8")
    return RUN_DELTA_REPORT_PATH


def main() -> None:
    summary_text = build_run_summary()
    output_path = save_run_summary(summary_text)
    delta_text = build_run_delta_report()
    delta_output_path = save_run_delta_report(delta_text)

    print(f"Run summary uložený do: {output_path}")
    print(f"Run delta report uložený do: {delta_output_path}")
    print("\nNáhľad:\n")
    print(summary_text)


if __name__ == "__main__":
    main()
