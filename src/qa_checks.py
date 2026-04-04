from pathlib import Path
from typing import Optional

import pandas as pd


PROCESSED_DIR = Path("data/processed")
ENRICHMENT_DIR = Path("outputs/enrichment")
CLICKUP_DIR = Path("outputs/clickup")
QA_DIR = Path("data/qa")


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


def normalize_severity(value: str) -> str:
    normalized = normalize_text(value)
    return normalized if normalized else "Info"


def build_issue(
    issue_type: str,
    severity: str,
    hotel_name: object,
    city: object,
    priority_band: object,
    details: str,
    source_file: object,
) -> dict[str, object]:
    return {
        "issue_type": issue_type,
        "severity": normalize_severity(severity),
        "blocking": "yes" if normalize_severity(severity) == "High" else "no",
        "hotel_name": normalize_text(hotel_name),
        "city": normalize_text(city),
        "priority_band": normalize_text(priority_band),
        "details": details,
        "source_file": normalize_text(source_file),
    }


def normalize_clickup_priority_value(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    try:
        number = int(float(text))
    except ValueError:
        return text
    return str(number)


def build_issue_rows(
    processed_df: pd.DataFrame,
    enrichment_df: pd.DataFrame,
    clickup_df: pd.DataFrame,
) -> pd.DataFrame:
    issues: list[dict[str, object]] = []

    if not processed_df.empty:
        duplicate_mask = processed_df.duplicated(
            subset=["hotel_name", "city", "street"], keep=False
        )
        for _, row in processed_df[duplicate_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="duplicate_lead",
                    severity="High",
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Duplicitný lead podľa hotel_name + city + street.",
                    source_file=row.get("source_file"),
                )
            )

        missing_contact_mask = (
            processed_df["website"].fillna("").astype(str).str.strip().eq("")
            & processed_df["phone"].fillna("").astype(str).str.strip().eq("")
        )
        for _, row in processed_df[missing_contact_mask].iterrows():
            severity = "High" if normalize_text(row.get("priority_band")) == "High" else "Medium"
            issues.append(
                build_issue(
                    issue_type="missing_contact_data",
                    severity=severity,
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Chýba web aj telefón.",
                    source_file=row.get("source_file"),
                )
            )

    if not enrichment_df.empty:
        missing_summary_mask = enrichment_df["factual_summary"].fillna("").astype(str).str.strip().eq("")
        for _, row in enrichment_df[missing_summary_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="missing_factual_summary",
                    severity="High",
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Chýba factual_summary v enrichment výstupe.",
                    source_file=row.get("source_file"),
                )
            )

        missing_contact_status_mask = enrichment_df["contact_status"].fillna("").astype(str).str.strip().eq("")
        for _, row in enrichment_df[missing_contact_status_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="missing_contact_status",
                    severity="High",
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Chýba contact_status v enrichment výstupe.",
                    source_file=row.get("source_file"),
                )
            )

        unverified_hours_mask = enrichment_df["hotel_opening_hours_status"].fillna("").astype(str).str.strip().eq(
            "Verejne nepotvrdené"
        )
        for _, row in enrichment_df[unverified_hours_mask].iterrows():
            severity = "Medium" if normalize_text(row.get("priority_band")) == "High" else "Low"
            issues.append(
                build_issue(
                    issue_type="unverified_opening_hours",
                    severity=severity,
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Otváracie hodiny sú verejne nepotvrdené.",
                    source_file=row.get("source_file"),
                )
            )

        unverified_checkio_mask = enrichment_df["checkin_checkout_status"].fillna("").astype(str).str.strip().eq(
            "Verejne nepotvrdené"
        ) & enrichment_df["priority_band"].fillna("").astype(str).str.strip().eq("High")
        for _, row in enrichment_df[unverified_checkio_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="unverified_checkin_checkout",
                    severity="Low",
                    hotel_name=row.get("hotel_name"),
                    city=row.get("city"),
                    priority_band=row.get("priority_band"),
                    details="Check-in / check-out je verejne nepotvrdený pre high-priority lead.",
                    source_file=row.get("source_file"),
                )
            )

    if not clickup_df.empty:
        duplicate_task_mask = clickup_df.duplicated(subset=["Task name"], keep=False)
        for _, row in clickup_df[duplicate_task_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="duplicate_clickup_task",
                    severity="High",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Duplicitný ClickUp Task name.",
                    source_file=row.get("Source file"),
                )
            )

        empty_task_name_mask = clickup_df["Task name"].fillna("").astype(str).str.strip().eq("")
        for _, row in clickup_df[empty_task_name_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="missing_clickup_task_name",
                    severity="High",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Chýba Task name pre ClickUp export.",
                    source_file=row.get("Source file"),
                )
            )

        empty_description_mask = clickup_df["Description content"].fillna("").astype(str).str.strip().eq("")
        for _, row in clickup_df[empty_description_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="missing_clickup_description",
                    severity="Medium",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Chýba Description content pre ClickUp export.",
                    source_file=row.get("Source file"),
                )
            )

        invalid_status_mask = ~clickup_df["Status"].fillna("").astype(str).str.strip().str.lower().isin(
            ["to do", "todo", "open", "backlog", "in progress", "complete", "done"]
        )
        for _, row in clickup_df[invalid_status_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="invalid_clickup_status",
                    severity="Medium",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Status nie je v bezpečnom importnom sete.",
                    source_file=row.get("Source file"),
                )
            )

        normalized_priorities = clickup_df["Priority"].apply(normalize_clickup_priority_value)
        invalid_priority_mask = ~normalized_priorities.isin(["", "1", "2", "3", "4"])
        for _, row in clickup_df[invalid_priority_mask].iterrows():
            issues.append(
                build_issue(
                    issue_type="invalid_clickup_priority",
                    severity="Medium",
                    hotel_name=row.get("Hotel name"),
                    city=row.get("City"),
                    priority_band=row.get("Priority"),
                    details="Priority nie je v očakávanom ClickUp numeric sete 1-4.",
                    source_file=row.get("Source file"),
                )
            )

    if not issues:
        return pd.DataFrame(
            [
                build_issue(
                    issue_type="no_issues_found",
                    severity="OK",
                    hotel_name="",
                    city="",
                    priority_band="",
                    details="QA nenašlo žiadne problémy podľa aktuálnych pravidiel.",
                    source_file="",
                )
            ]
        )

    return pd.DataFrame(issues)


def save_qa_outputs(issues_df: pd.DataFrame) -> tuple[Path, Path]:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    issues_path = QA_DIR / "qa_issues.csv"
    summary_path = QA_DIR / "qa_summary.txt"

    issues_df.to_csv(issues_path, index=False)

    blocking_count = len(issues_df[issues_df["blocking"] == "yes"])
    high_count = len(issues_df[issues_df["severity"] == "High"])
    medium_count = len(issues_df[issues_df["severity"] == "Medium"])
    low_count = len(issues_df[issues_df["severity"] == "Low"])
    ok_count = len(issues_df[issues_df["severity"] == "OK"])

    summary_lines = [
        f"Počet QA issue riadkov: {len(issues_df)}",
        f"Blocking: {blocking_count}",
        f"High: {high_count}",
        f"Medium: {medium_count}",
        f"Low: {low_count}",
        f"OK: {ok_count}",
    ]
    summary_path.write_text("\n".join(summary_lines), encoding="utf-8")

    return issues_path, summary_path


def main() -> None:
    processed_df = load_csv(get_first_file(PROCESSED_DIR, "*_normalized_scored.csv"))
    enrichment_df = load_csv(get_first_file(ENRICHMENT_DIR, "*_enriched.csv"))
    clickup_df = load_csv(get_first_file(CLICKUP_DIR, "*_clickup_import.csv"))

    issues_df = build_issue_rows(
        processed_df=processed_df,
        enrichment_df=enrichment_df,
        clickup_df=clickup_df,
    )
    issues_path, summary_path = save_qa_outputs(issues_df)

    print(f"QA issues uložené do: {issues_path}")
    print(f"QA summary uložené do: {summary_path}")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(issues_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
