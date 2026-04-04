from pathlib import Path

import pandas as pd
import yaml


PROCESSED_DIR = Path("data/processed")
ENRICHMENT_OUTPUT_DIR = Path("outputs/enrichment")
ENRICHMENT_CONFIG_PATH = Path("configs/enrichment.yaml")


def load_enrichment_config(config_path: Path = ENRICHMENT_CONFIG_PATH) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def list_processed_files(processed_dir: Path = PROCESSED_DIR) -> list[Path]:
    if not processed_dir.exists():
        return []
    return sorted(processed_dir.glob("*_normalized_scored.csv"))


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def build_factual_summary(row: pd.Series) -> str:
    parts = []

    if row["hotel_name"]:
        parts.append(f"Hotel {row['hotel_name']}")
    if row["city"]:
        parts.append(f"sa nachádza v lokalite {row['city']}")
    if row["category_name"]:
        parts.append(f"kategória: {row['category_name']}")
    if row["priority_band"]:
        parts.append(f"priorita: {row['priority_band']}")
    if row["review_score"] > 0:
        parts.append(f"hodnotenie: {row['review_score']}/5")
    if row["reviews_count"] > 0:
        parts.append(f"počet recenzií: {row['reviews_count']}")

    return ", ".join(parts)


def build_contact_status(row: pd.Series, unknown_value_label: str) -> str:
    if row["website"] and row["phone"]:
        return "Overené z raw vstupu: web aj telefón"
    if row["website"]:
        return "Overené z raw vstupu: len web"
    if row["phone"]:
        return "Overené z raw vstupu: len telefón"
    return unknown_value_label


def build_enrichment_dataframe(df: pd.DataFrame, unknown_value_label: str) -> pd.DataFrame:
    enriched = df.copy()

    enriched["hotel_opening_hours"] = unknown_value_label
    enriched["hotel_opening_hours_status"] = "Verejne nepotvrdené"
    enriched["checkin_checkout_info"] = unknown_value_label
    enriched["checkin_checkout_status"] = "Verejne nepotvrdené"
    enriched["contact_status"] = enriched.apply(
        lambda row: build_contact_status(row, unknown_value_label),
        axis=1,
    )
    enriched["factual_summary"] = enriched.apply(build_factual_summary, axis=1)

    return enriched[
        [
            "hotel_name",
            "city",
            "country_code",
            "website",
            "phone",
            "category_name",
            "all_categories",
            "review_score",
            "reviews_count",
            "priority_score",
            "priority_band",
            "hotel_opening_hours",
            "hotel_opening_hours_status",
            "checkin_checkout_info",
            "checkin_checkout_status",
            "contact_status",
            "factual_summary",
            "source_url",
            "source_file",
        ]
    ].copy()


def save_enriched_file(df: pd.DataFrame, source_file: str) -> Path:
    ENRICHMENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = ENRICHMENT_OUTPUT_DIR / f"{Path(source_file).stem}_enriched.csv"
    df.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    processed_files = list_processed_files()

    if not processed_files:
        print("V priečinku data/processed nie je žiadny normalized_scored CSV súbor.")
        return

    first_file = processed_files[0]
    config = load_enrichment_config()
    unknown_value_label = config.get("enrichment", {}).get(
        "unknown_value_label", "Verejne nepotvrdené"
    )

    try:
        scored_df = pd.read_csv(first_file)
    except Exception as error:
        print(f"Nepodarilo sa načítať processed CSV súbor: {first_file.name}")
        print(f"Dôvod: {error}")
        return

    for column in scored_df.columns:
        if scored_df[column].dtype == object:
            scored_df[column] = scored_df[column].apply(normalize_text)

    enriched_df = build_enrichment_dataframe(scored_df, unknown_value_label)
    output_path = save_enriched_file(enriched_df, first_file.name)

    print(f"Načítaný processed súbor: {first_file.name}")
    print(f"Počet riadkov: {len(enriched_df)}")
    print(f"Výstup uložený do: {output_path}")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(
        enriched_df[
            [
                "hotel_name",
                "priority_band",
                "hotel_opening_hours",
                "contact_status",
                "factual_summary",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
