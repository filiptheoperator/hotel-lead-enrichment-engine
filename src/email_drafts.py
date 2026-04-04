"""Draft modul pre neskoršiu Fázu 5.

Tento súbor je zámerne mimo aktívny flow.
Aktívny hlavný entrypoint projektu momentálne nekonzumuje tento modul.
"""

from pathlib import Path

import pandas as pd


ENRICHMENT_OUTPUT_DIR = Path("outputs/enrichment")
EMAIL_OUTPUT_DIR = Path("outputs/email_drafts")


def list_enriched_files(enrichment_dir: Path = ENRICHMENT_OUTPUT_DIR) -> list[Path]:
    if not enrichment_dir.exists():
        return []
    return sorted(enrichment_dir.glob("*_enriched.csv"))


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def build_subject_line(row: pd.Series) -> str:
    city = row["city"] or "váš hotel"
    return f"Nápad pre {city}: jednoduchšie priame dopyty"


def build_hook(row: pd.Series) -> str:
    if row["hotel_name"] and row["priority_band"] == "High":
        return f"Zaujal ma hotel {row['hotel_name']} a jeho silný verejný profil."
    if row["hotel_name"]:
        return f"Zaujal ma hotel {row['hotel_name']} pri rýchlom prehľade."
    return "Zaujal ma váš hotel pri rýchlom prehľade."


def build_cold_email(row: pd.Series) -> str:
    hotel_name = row["hotel_name"] or "váš hotel"
    hook = build_hook(row)
    angle = row["personalization_angle"] or "Vidím priestor na zlepšenie relevantnosti oslovenia."

    return (
        f"Dobrý deň,\n\n"
        f"{hook}\n"
        f"{angle}\n\n"
        f"Pomáhame hotelom ako {hotel_name} pripraviť prehľad leadov, enrichment a ďalšie kroky tak, "
        f"aby bol obchodný kontakt jednoduchší a relevantnejší.\n\n"
        f"Ak dáva zmysel, rád pošlem krátky príklad, ako by to vedelo vyzerať aj pre vás.\n\n"
        f"S pozdravom"
    )


def build_followup_email(row: pd.Series) -> str:
    hotel_name = row["hotel_name"] or "váš hotel"
    return (
        f"Dobrý deň,\n\n"
        f"len sa jemne pripomínam k predošlej správe pre {hotel_name}.\n"
        f"Ak by to bolo užitočné, pošlem stručný návrh ďalšieho postupu bez zbytočnej teórie.\n\n"
        f"S pozdravom"
    )


def build_email_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    emails = df.copy()

    for column in emails.columns:
        if emails[column].dtype == object:
            emails[column] = emails[column].apply(normalize_text)

    emails["subject_line"] = emails.apply(build_subject_line, axis=1)
    emails["hook"] = emails.apply(build_hook, axis=1)
    emails["cold_email"] = emails.apply(build_cold_email, axis=1)
    emails["followup_email"] = emails.apply(build_followup_email, axis=1)

    return emails[
        [
            "hotel_name",
            "city",
            "priority_band",
            "priority_score",
            "website",
            "phone",
            "contact_status",
            "personalization_angle",
            "subject_line",
            "hook",
            "cold_email",
            "followup_email",
            "source_file",
        ]
    ].copy()


def save_email_file(df: pd.DataFrame, source_file: str) -> Path:
    EMAIL_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = EMAIL_OUTPUT_DIR / f"{Path(source_file).stem}_email_drafts.csv"
    df.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    enriched_files = list_enriched_files()

    if not enriched_files:
        print("V priečinku outputs/enrichment nie je žiadny enriched CSV súbor.")
        return

    first_file = enriched_files[0]

    try:
        enriched_df = pd.read_csv(first_file)
    except Exception as error:
        print(f"Nepodarilo sa načítať enrichment CSV súbor: {first_file.name}")
        print(f"Dôvod: {error}")
        return

    email_df = build_email_dataframe(enriched_df)
    output_path = save_email_file(email_df, first_file.name)

    print(f"Načítaný enrichment súbor: {first_file.name}")
    print(f"Počet riadkov: {len(email_df)}")
    print(f"Výstup uložený do: {output_path}")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(
        email_df[
            [
                "hotel_name",
                "subject_line",
                "hook",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
