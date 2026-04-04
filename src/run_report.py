from pathlib import Path
from typing import Optional

import pandas as pd


PROCESSED_DIR = Path("data/processed")
ENRICHMENT_DIR = Path("outputs/enrichment")
EMAIL_DIR = Path("outputs/email_drafts")
CLICKUP_DIR = Path("outputs/clickup")
QA_DIR = Path("data/qa")
RUN_REPORT_PATH = QA_DIR / "run_summary.txt"


def get_first_file(folder: Path, pattern: str) -> Optional[Path]:
    files = sorted(folder.glob(pattern))
    return files[0] if files else None


def load_csv(file_path: Optional[Path]) -> pd.DataFrame:
    if file_path is None:
        return pd.DataFrame()
    return pd.read_csv(file_path)


def safe_count(series: pd.Series, expected_value: str) -> int:
    return int(series.fillna("").astype(str).str.strip().eq(expected_value).sum())


def build_run_summary() -> str:
    processed_df = load_csv(get_first_file(PROCESSED_DIR, "*_normalized_scored.csv"))
    enrichment_df = load_csv(get_first_file(ENRICHMENT_DIR, "*_enriched.csv"))
    email_df = load_csv(get_first_file(EMAIL_DIR, "*_email_drafts.csv"))
    clickup_df = load_csv(get_first_file(CLICKUP_DIR, "*_clickup_import.csv"))
    qa_df = load_csv(QA_DIR / "qa_issues.csv")

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
    needs_manual_review = 0
    if not enrichment_df.empty:
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
        "Processed",
        f"- processed_rows: {processed_rows}",
        f"- enrichment_rows: {enrichment_rows}",
        f"- email_rows: {email_rows}",
        f"- clickup_rows: {clickup_rows}",
        "",
        "Verified",
        f"- verified_opening_hours: {verified_opening_hours}",
        f"- verified_checkin_checkout: {verified_checkin_checkout}",
        "",
        "Unverified",
        f"- unverified_opening_hours: {unverified_opening_hours}",
        f"- unverified_checkin_checkout: {unverified_checkin_checkout}",
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


def save_run_summary(summary_text: str) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    RUN_REPORT_PATH.write_text(summary_text, encoding="utf-8")
    return RUN_REPORT_PATH


def main() -> None:
    summary_text = build_run_summary()
    output_path = save_run_summary(summary_text)

    print(f"Run summary uložený do: {output_path}")
    print("\nNáhľad:\n")
    print(summary_text)


if __name__ == "__main__":
    main()
