"""Draft modul pre neskoršiu Fázu 7.

Tento súbor je zámerne mimo aktívny flow.
Aktívny hlavný entrypoint projektu momentálne nekonzumuje tento modul.
"""

from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


PROCESSED_DIR = Path("data/processed")
ENRICHMENT_DIR = Path("outputs/enrichment")
EMAIL_DRAFTS_DIR = Path("outputs/email_drafts")
CLICKUP_DIR = Path("outputs/clickup")
QA_DIR = Path("data/qa")
PROJECT_CONFIG_PATH = Path("configs/project.yaml")


def load_project_config(config_path: Path = PROJECT_CONFIG_PATH) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def get_first_file(folder: Path, pattern: str) -> Optional[Path]:
    files = sorted(folder.glob(pattern))
    return files[0] if files else None


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_csv(file_path: Optional[Path]) -> pd.DataFrame:
    if file_path is None:
        return pd.DataFrame()
    return pd.read_csv(file_path)


def build_issue_rows(
    processed_df: pd.DataFrame,
    enrichment_df: pd.DataFrame,
    email_df: pd.DataFrame,
    clickup_df: pd.DataFrame,
    review_priorities: list[str],
) -> pd.DataFrame:
    issues: list[dict[str, object]] = []

    if not processed_df.empty:
        duplicate_mask = processed_df.duplicated(
            subset=["hotel_name", "city", "street"], keep=False
        )
        for _, row in processed_df[duplicate_mask].iterrows():
            issues.append(
                {
                    "issue_type": "duplicate_lead",
                    "severity": "High",
                    "hotel_name": normalize_text(row.get("hotel_name")),
                    "city": normalize_text(row.get("city")),
                    "priority_band": normalize_text(row.get("priority_band")),
                    "details": "Duplicitný lead podľa hotel_name + city + street.",
                    "source_file": normalize_text(row.get("source_file")),
                }
            )

        missing_contact_mask = (
            processed_df["website"].fillna("").astype(str).str.strip().eq("")
            & processed_df["phone"].fillna("").astype(str).str.strip().eq("")
        )
        for _, row in processed_df[missing_contact_mask].iterrows():
            severity = (
                "High"
                if normalize_text(row.get("priority_band")) in review_priorities
                else "Medium"
            )
            issues.append(
                {
                    "issue_type": "missing_contact_data",
                    "severity": severity,
                    "hotel_name": normalize_text(row.get("hotel_name")),
                    "city": normalize_text(row.get("city")),
                    "priority_band": normalize_text(row.get("priority_band")),
                    "details": "Chýba web aj telefón.",
                    "source_file": normalize_text(row.get("source_file")),
                }
            )

    if not enrichment_df.empty:
        unverified_mask = enrichment_df["hotel_opening_hours_status"].fillna("").astype(str).str.strip().eq(
            "Verejne nepotvrdené"
        )
        for _, row in enrichment_df[unverified_mask].iterrows():
            severity = (
                "High"
                if normalize_text(row.get("priority_band")) in review_priorities
                else "Medium"
            )
            issues.append(
                {
                    "issue_type": "unverified_opening_hours",
                    "severity": severity,
                    "hotel_name": normalize_text(row.get("hotel_name")),
                    "city": normalize_text(row.get("city")),
                    "priority_band": normalize_text(row.get("priority_band")),
                    "details": "Otváracie hodiny sú verejne nepotvrdené.",
                    "source_file": normalize_text(row.get("source_file")),
                }
            )

    if not email_df.empty:
        empty_email_mask = (
            email_df["subject_line"].fillna("").astype(str).str.strip().eq("")
            | email_df["cold_email"].fillna("").astype(str).str.strip().eq("")
        )
        for _, row in email_df[empty_email_mask].iterrows():
            issues.append(
                {
                    "issue_type": "missing_email_draft",
                    "severity": "High",
                    "hotel_name": normalize_text(row.get("hotel_name")),
                    "city": normalize_text(row.get("city")),
                    "priority_band": normalize_text(row.get("priority_band")),
                    "details": "Chýba subject_line alebo cold_email.",
                    "source_file": normalize_text(row.get("source_file")),
                }
            )

    if not clickup_df.empty:
        duplicate_task_mask = clickup_df.duplicated(subset=["task_name"], keep=False)
        for _, row in clickup_df[duplicate_task_mask].iterrows():
            issues.append(
                {
                    "issue_type": "duplicate_clickup_task",
                    "severity": "Medium",
                    "hotel_name": normalize_text(row.get("hotel_name")),
                    "city": normalize_text(row.get("city")),
                    "priority_band": normalize_text(row.get("task_priority")),
                    "details": "Duplicitný ClickUp task_name.",
                    "source_file": normalize_text(row.get("source_file")),
                }
            )

    if not issues:
        return pd.DataFrame(
            [
                {
                    "issue_type": "no_issues_found",
                    "severity": "OK",
                    "hotel_name": "",
                    "city": "",
                    "priority_band": "",
                    "details": "QA nenašlo žiadne problémy podľa aktuálnych pravidiel.",
                    "source_file": "",
                }
            ]
        )

    return pd.DataFrame(issues)


def save_qa_outputs(issues_df: pd.DataFrame) -> tuple[Path, Path]:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    issues_path = QA_DIR / "qa_issues.csv"
    summary_path = QA_DIR / "qa_summary.txt"

    issues_df.to_csv(issues_path, index=False)

    summary_lines = [
        f"Počet QA issue riadkov: {len(issues_df)}",
        f"High: {len(issues_df[issues_df['severity'] == 'High'])}",
        f"Medium: {len(issues_df[issues_df['severity'] == 'Medium'])}",
        f"OK: {len(issues_df[issues_df['severity'] == 'OK'])}",
    ]
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    return issues_path, summary_path


def main() -> None:
    project_config = load_project_config()
    review_priorities = project_config.get("review_required_priorities", [])

    processed_df = load_csv(get_first_file(PROCESSED_DIR, "*_normalized_scored.csv"))
    enrichment_df = load_csv(get_first_file(ENRICHMENT_DIR, "*_enriched.csv"))
    email_df = load_csv(get_first_file(EMAIL_DRAFTS_DIR, "*_email_drafts.csv"))
    clickup_df = load_csv(get_first_file(CLICKUP_DIR, "*_clickup_import.csv"))

    issues_df = build_issue_rows(
        processed_df=processed_df,
        enrichment_df=enrichment_df,
        email_df=email_df,
        clickup_df=clickup_df,
        review_priorities=review_priorities,
    )
    issues_path, summary_path = save_qa_outputs(issues_df)

    print(f"QA issues uložené do: {issues_path}")
    print(f"QA summary uložené do: {summary_path}")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(issues_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
