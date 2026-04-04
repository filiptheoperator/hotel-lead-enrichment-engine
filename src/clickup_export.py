from pathlib import Path

import pandas as pd


EMAIL_OUTPUT_DIR = Path("outputs/email_drafts")
CLICKUP_OUTPUT_DIR = Path("outputs/clickup")


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


def build_clickup_notes(row: pd.Series) -> str:
    parts = [
        f"Hotel: {row['hotel_name']}",
        f"Mesto: {row['city']}",
        f"Priorita: {row['priority_band']}",
        f"Skóre: {row['priority_score']}",
        f"Web: {row['website'] or 'Verejne nepotvrdené'}",
        f"Telefón: {row['phone'] or 'Verejne nepotvrdené'}",
        "",
        f"Hook: {row['hook']}",
        "",
        "Cold email:",
        row["cold_email"],
        "",
        "Follow-up email:",
        row["followup_email"],
    ]
    return "\n".join(parts)


def build_clickup_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    export_df = df.copy()

    for column in export_df.columns:
        if export_df[column].dtype == object:
            export_df[column] = export_df[column].apply(normalize_text)

    export_df["task_name"] = export_df.apply(build_clickup_task_name, axis=1)
    export_df["task_priority"] = export_df["priority_band"]
    export_df["task_status"] = "to do"
    export_df["contact_phone"] = export_df["phone"]
    export_df["contact_website"] = export_df["website"]
    export_df["task_notes"] = export_df.apply(build_clickup_notes, axis=1)

    return export_df[
        [
            "task_name",
            "task_priority",
            "task_status",
            "hotel_name",
            "city",
            "priority_score",
            "contact_phone",
            "contact_website",
            "subject_line",
            "hook",
            "cold_email",
            "followup_email",
            "task_notes",
            "source_file",
        ]
    ].copy()


def save_clickup_file(df: pd.DataFrame, source_file: str) -> Path:
    CLICKUP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLICKUP_OUTPUT_DIR / f"{Path(source_file).stem}_clickup_import.csv"
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
    output_path = save_clickup_file(clickup_df, first_file.name)

    print(f"Načítaný email draft súbor: {first_file.name}")
    print(f"Počet riadkov: {len(clickup_df)}")
    print(f"Výstup uložený do: {output_path}")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(
        clickup_df[
            [
                "task_name",
                "task_priority",
                "subject_line",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
