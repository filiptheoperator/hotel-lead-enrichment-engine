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


def is_verified_public(value: str) -> bool:
    return normalize_text(value) == "Overené vo verejnom zdroji"


def format_score(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return f"{number:.2f}".rstrip("0").rstrip(".")


def build_short_factual_line(row: pd.Series) -> str:
    facts: list[str] = []

    if row["city"]:
        facts.append(f"v lokalite {row['city']}")
    if row["priority_band"]:
        score = format_score(row.get("priority_score"))
        if score:
            facts.append(f"s prioritou {row['priority_band']} ({score})")
        else:
            facts.append(f"s prioritou {row['priority_band']}")

    try:
        review_score = float(row.get("review_score", 0) or 0)
    except (TypeError, ValueError):
        review_score = 0
    try:
        reviews_count = int(float(row.get("reviews_count", 0) or 0))
    except (TypeError, ValueError):
        reviews_count = 0

    if review_score > 0 and reviews_count > 0:
        facts.append(f"s hodnotením {review_score:.1f}/5 z {reviews_count} recenzií")

    if not facts:
        return "Pozrel som si váš verejný profil a základné údaje."

    return "Pozrel som si váš verejný profil " + ", ".join(facts) + "."


def build_subject_line(row: pd.Series) -> str:
    hotel_name = row["hotel_name"] or "váš hotel"
    return f"{hotel_name}: krátky nápad"


def build_hook(row: pd.Series) -> str:
    if row["hotel_name"] and row["city"]:
        return f"Pozeral som sa na {row['hotel_name']} v lokalite {row['city']}."
    if row["hotel_name"]:
        return f"Pozeral som sa na {row['hotel_name']}."
    return "Pozeral som sa na váš hotel pri rýchlom verejnom prehľade."


def build_cold_email(row: pd.Series) -> str:
    hook = build_hook(row)
    factual_line = build_short_factual_line(row)
    hotel_name = row["hotel_name"] or "váš hotel"

    return (
        f"Dobrý deň,\n\n"
        f"{hook}\n"
        f"{factual_line}\n\n"
        f"Mám jeden stručný nápad, ako zlepšiť prvý dojem a dopyty pre {hotel_name}.\n"
        f"Ak bude dávať zmysel, pošlem ho v 3 bodoch.\n\n"
        f"S pozdravom"
    )


def build_followup_email(row: pd.Series) -> str:
    hotel_name = row["hotel_name"] or "váš hotel"
    return (
        f"Dobrý deň,\n\n"
        f"jemne sa pripomínam k predošlej správe pre {hotel_name}.\n"
        f"Ak je to pre vás relevantné, pošlem krátky návrh v 3 bodoch.\n\n"
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
            "factual_summary",
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
