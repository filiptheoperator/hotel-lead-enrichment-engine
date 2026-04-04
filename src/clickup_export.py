from pathlib import Path

import pandas as pd


EMAIL_OUTPUT_DIR = Path("outputs/email_drafts")
CLICKUP_OUTPUT_DIR = Path("outputs/clickup")
CLICKUP_REQUIRED_COLUMNS = ["Task name"]
CLICKUP_SUPPORTED_CORE_COLUMNS = [
    "Task name",
    "Description content",
    "Status",
    "Priority",
]
CLICKUP_ALLOWED_PRIORITY_VALUES = {"", "1", "2", "3", "4"}


def list_email_draft_files(email_dir: Path = EMAIL_OUTPUT_DIR) -> list[Path]:
    if not email_dir.exists():
        return []
    return sorted(email_dir.glob("*_email_drafts.csv"))


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def build_clickup_task_name(row: pd.Series) -> str:
    hotel_name = row["hotel_name"] or "Hotel lead"
    return f"Lead outreach - {hotel_name}"


def map_clickup_priority(priority_band: str) -> str:
    normalized = normalize_text(priority_band).lower()
    if normalized == "high":
        return "2"
    if normalized == "medium":
        return "3"
    if normalized == "low":
        return "4"
    return ""


def build_clickup_status(row: pd.Series) -> str:
    return "to do"


def build_clickup_notes(row: pd.Series) -> str:
    parts = [
        f"Hotel: {normalize_text(row.get('hotel_name', ''))}",
        f"Mesto: {normalize_text(row.get('city', ''))}",
        f"Priorita band: {normalize_text(row.get('priority_band', ''))}",
        f"Skóre: {normalize_text(row.get('priority_score', ''))}",
        f"Web: {normalize_text(row.get('website', '')) or 'Verejne nepotvrdené'}",
        f"Telefón: {normalize_text(row.get('phone', '')) or 'Verejne nepotvrdené'}",
        f"Email angle: {normalize_text(row.get('email_angle', ''))}",
        f"CTA type: {normalize_text(row.get('cta_type', ''))}",
        f"Variant ID: {normalize_text(row.get('variant_id', ''))}",
        f"Test batch: {normalize_text(row.get('test_batch', ''))}",
        f"Reply outcome: {normalize_text(row.get('reply_outcome', ''))}",
        "",
        f"Email hook: {normalize_text(row.get('email_hook', row.get('hook', '')))}",
        f"Give-first insight: {normalize_text(row.get('give_first_insight', ''))}",
        f"Main observed issue: {normalize_text(row.get('main_observed_issue', ''))}",
        f"Proof snippet: {normalize_text(row.get('proof_snippet', ''))}",
        f"Micro CTA: {normalize_text(row.get('micro_cta', ''))}",
        f"Primary email goal: {normalize_text(row.get('primary_email_goal', ''))}",
        "",
        "Cold email:",
        normalize_text(row.get("cold_email", "")),
        "",
        "Follow-up email:",
        normalize_text(row.get("followup_email", "")),
    ]
    return "\n".join(parts)


def build_clickup_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    export_df = df.copy()

    for column in export_df.columns:
        if export_df[column].dtype == object:
            export_df[column] = export_df[column].apply(normalize_text)

    for column in [
        "email_angle",
        "cta_type",
        "variant_id",
        "test_batch",
        "reply_outcome",
        "give_first_insight",
        "main_observed_issue",
        "email_hook",
        "micro_cta",
        "proof_snippet",
        "primary_email_goal",
    ]:
        if column in export_df.columns:
            export_df[column] = export_df[column].apply(normalize_text)

    export_df["task_name"] = export_df.apply(build_clickup_task_name, axis=1)
    export_df["clickup_priority"] = export_df["priority_band"].apply(map_clickup_priority)
    export_df["clickup_status"] = export_df.apply(build_clickup_status, axis=1)
    export_df["contact_phone"] = export_df["phone"]
    export_df["contact_website"] = export_df["website"]
    export_df["task_notes"] = export_df.apply(build_clickup_notes, axis=1)

    return export_df[
        [
            "task_name",
            "task_notes",
            "clickup_status",
            "clickup_priority",
            "hotel_name",
            "city",
            "priority_score",
            "contact_phone",
            "contact_website",
            "subject_line",
            "source_file",
            "email_angle",
            "cta_type",
            "variant_id",
            "test_batch",
            "reply_outcome",
            "give_first_insight",
            "main_observed_issue",
            "email_hook",
            "micro_cta",
            "proof_snippet",
            "primary_email_goal",
        ]
    ].rename(
        columns={
            "task_name": "Task name",
            "task_notes": "Description content",
            "clickup_status": "Status",
            "clickup_priority": "Priority",
            "hotel_name": "Hotel name",
            "city": "City",
            "priority_score": "Priority score",
            "contact_phone": "Contact phone",
            "contact_website": "Contact website",
            "subject_line": "Subject line",
            "source_file": "Source file",
            "email_angle": "Email angle",
            "cta_type": "CTA type",
            "variant_id": "Variant ID",
            "test_batch": "Test batch",
            "reply_outcome": "Reply outcome",
            "give_first_insight": "Give-first insight",
            "main_observed_issue": "Main observed issue",
            "email_hook": "Email hook",
            "micro_cta": "Micro CTA",
            "proof_snippet": "Proof snippet",
            "primary_email_goal": "Primary email goal",
        }
    ).copy()


def validate_clickup_import_readiness(df: pd.DataFrame) -> list[str]:
    issues: list[str] = []

    missing_required_columns = [
        column for column in CLICKUP_REQUIRED_COLUMNS if column not in df.columns
    ]
    if missing_required_columns:
        issues.append(
            "Chýbajú povinné ClickUp stĺpce: " + ", ".join(missing_required_columns)
        )
        return issues

    missing_supported_core_columns = [
        column for column in CLICKUP_SUPPORTED_CORE_COLUMNS if column not in df.columns
    ]
    if missing_supported_core_columns:
        issues.append(
            "Chýbajú odporúčané ClickUp core stĺpce: "
            + ", ".join(missing_supported_core_columns)
        )

    if len(df) > 10000:
        issues.append("CSV prekračuje ClickUp import limit 10 000 riadkov.")

    empty_task_name_count = (
        df["Task name"].fillna("").astype(str).str.strip().eq("").sum()
    )
    if empty_task_name_count:
        issues.append(f"Task name chýba v {int(empty_task_name_count)} riadkoch.")

    if "Priority" in df.columns:
        normalized_priorities = (
            df["Priority"]
            .fillna("")
            .astype(str)
            .str.strip()
            .map(lambda value: str(int(float(value))) if value not in {"", "nan"} else "")
        )
        invalid_priority_count = (~normalized_priorities.isin(CLICKUP_ALLOWED_PRIORITY_VALUES)).sum()
        if invalid_priority_count:
            issues.append(
                f"Priority má neplatnú ClickUp hodnotu v {int(invalid_priority_count)} riadkoch."
            )

    if "Status" in df.columns:
        empty_status_count = df["Status"].fillna("").astype(str).str.strip().eq("").sum()
        if empty_status_count:
            issues.append(f"Status chýba v {int(empty_status_count)} riadkoch.")

    return issues


def save_clickup_file(df: pd.DataFrame, source_file: str) -> Path:
    CLICKUP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLICKUP_OUTPUT_DIR / f"{Path(source_file).stem}_clickup_import.csv"
    df.to_csv(output_path, index=False)
    return output_path


def save_high_leads_clickup_file(df: pd.DataFrame, source_file: str) -> Path:
    CLICKUP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLICKUP_OUTPUT_DIR / f"{Path(source_file).stem}_clickup_import_high_only.csv"
    df.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    email_files = list_email_draft_files()

    if not email_files:
        print("V priečinku outputs/email_drafts nie je žiadny email draft CSV súbor.")
        return

    first_file = email_files[0]

    try:
        email_df = pd.read_csv(first_file)
    except Exception as error:
        print(f"Nepodarilo sa načítať email draft CSV súbor: {first_file.name}")
        print(f"Dôvod: {error}")
        return

    clickup_df = build_clickup_dataframe(email_df)
    high_clickup_df = build_clickup_dataframe(
        email_df[email_df["priority_band"].fillna("").astype(str).str.strip().eq("High")].copy()
    )
    readiness_issues = validate_clickup_import_readiness(clickup_df)
    output_path = save_clickup_file(clickup_df, first_file.name)
    high_output_path = save_high_leads_clickup_file(high_clickup_df, first_file.name)

    print(f"Načítaný email draft súbor: {first_file.name}")
    print(f"Počet riadkov: {len(clickup_df)}")
    print(f"Výstup uložený do: {output_path}")
    print(f"High-only výstup uložený do: {high_output_path}")
    if readiness_issues:
        print("\nClickUp import readiness:\n")
        for issue in readiness_issues:
            print(f"- {issue}")
    else:
        print("\nClickUp import readiness:\n")
        print("- OK: export vyzerá pripravený pre Spreadsheet importer.")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(
        clickup_df[
            [
                "Task name",
                "Priority",
                "Subject line",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
