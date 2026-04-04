from pathlib import Path
import re
from urllib.parse import urlparse

import pandas as pd
import yaml

from ingest.raw_loader import build_raw_preview, list_raw_csv_files, load_raw_csv


PROCESSED_DIR = Path("data/processed")
SCORING_CONFIG_PATH = Path("configs/scoring.yaml")

RAW_TO_NORMALIZED_COLUMNS = {
    "title": "hotel_name",
    "totalScore": "review_score",
    "reviewsCount": "reviews_count",
    "street": "street",
    "city": "city",
    "state": "state",
    "countryCode": "country_code",
    "website": "website",
    "phone": "phone",
    "url": "source_url",
    "categoryName": "category_name",
}

NORMALIZED_COLUMNS = [
    "hotel_name",
    "review_score",
    "reviews_count",
    "street",
    "city",
    "state",
    "country_code",
    "website",
    "phone",
    "category_name",
    "source_url",
    "all_categories",
    "source_file",
]


def load_scoring_config(config_path: Path = SCORING_CONFIG_PATH) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_country_code(value: object) -> str:
    return normalize_text(value).upper()


def normalize_phone(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""
    return re.sub(r"\s+", " ", text)


def normalize_website(value: object) -> str:
    text = normalize_text(value)
    if not text:
        return ""

    if not text.startswith(("http://", "https://")):
        text = f"https://{text}"

    parsed = urlparse(text)
    if not parsed.netloc:
        return ""

    return text


def collect_categories(df: pd.DataFrame) -> pd.Series:
    category_columns = sorted(
        [column for column in df.columns if column.startswith("categories/")]
    )

    if not category_columns:
        return pd.Series([""] * len(df), index=df.index)

    return df[category_columns].apply(
        lambda row: " | ".join(
            normalize_text(value) for value in row if normalize_text(value)
        ),
        axis=1,
    )


def normalize_dataframe(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    normalized = df.rename(columns=RAW_TO_NORMALIZED_COLUMNS).copy()
    normalized["all_categories"] = collect_categories(df)
    normalized["source_file"] = source_file

    for column in NORMALIZED_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""

    normalized = normalized[NORMALIZED_COLUMNS].copy()
    normalized["hotel_name"] = normalized["hotel_name"].apply(normalize_text)
    normalized["street"] = normalized["street"].apply(normalize_text)
    normalized["city"] = normalized["city"].apply(normalize_text)
    normalized["state"] = normalized["state"].apply(normalize_text)
    normalized["country_code"] = normalized["country_code"].apply(normalize_country_code)
    normalized["website"] = normalized["website"].apply(normalize_website)
    normalized["phone"] = normalized["phone"].apply(normalize_phone)
    normalized["category_name"] = normalized["category_name"].apply(normalize_text)
    normalized["source_url"] = normalized["source_url"].apply(normalize_text)
    normalized["all_categories"] = normalized["all_categories"].apply(normalize_text)
    normalized["source_file"] = normalized["source_file"].apply(normalize_text)

    normalized["review_score"] = pd.to_numeric(
        normalized["review_score"], errors="coerce"
    ).fillna(0.0)
    normalized["reviews_count"] = pd.to_numeric(
        normalized["reviews_count"], errors="coerce"
    ).fillna(0).astype(int)

    return normalized.drop_duplicates(
        subset=["hotel_name", "city", "street"], keep="first"
    ).reset_index(drop=True)


def clamp_score(value: float) -> float:
    return max(0.0, min(10.0, value))


def compute_score_components(df: pd.DataFrame) -> pd.DataFrame:
    review_score_component = (df["review_score"] / 5.0) * 10.0
    review_count_component = (df["reviews_count"].clip(upper=500) / 500.0) * 10.0

    direct_booking_strength = df["website"].apply(lambda value: 10.0 if value else 0.0)
    ota_dependency_signal = df["website"].apply(lambda value: 8.0 if value else 2.0)
    digital_maturity = (
        df["website"].apply(lambda value: 5.0 if value else 0.0)
        + df["phone"].apply(lambda value: 5.0 if value else 0.0)
    )
    operational_complexity = df["all_categories"].apply(
        lambda value: clamp_score(float(min(len([item for item in value.split(" | ") if item]), 5) * 2))
    )
    review_signal = ((review_score_component + review_count_component) / 2.0).apply(
        clamp_score
    )
    contact_quality = (
        df["website"].apply(lambda value: 5.0 if value else 0.0)
        + df["phone"].apply(lambda value: 5.0 if value else 0.0)
    )
    fit_to_icp = df["category_name"].apply(
        lambda value: 8.0 if "hotel" in value.lower() else 5.0 if value else 0.0
    )

    return pd.DataFrame(
        {
            "direct_booking_strength": direct_booking_strength,
            "ota_dependency_signal": ota_dependency_signal,
            "digital_maturity": digital_maturity,
            "operational_complexity": operational_complexity,
            "review_signal": review_signal,
            "contact_quality": contact_quality,
            "fit_to_icp": fit_to_icp,
        }
    )


def apply_weighted_score(df: pd.DataFrame, scoring_config: dict) -> pd.DataFrame:
    scored = df.copy()
    components = compute_score_components(scored)
    weights = scoring_config.get("scoring", {}).get("weights", {})

    scored = pd.concat([scored, components], axis=1)
    scored["priority_score"] = 0.0

    for column in components.columns:
        weight = float(weights.get(column, 0.0))
        scored["priority_score"] += scored[column] * weight

    scored["priority_score"] = scored["priority_score"].round(2)
    scored["priority_band"] = scored["priority_score"].apply(
        lambda value: score_to_priority_band(value, scoring_config)
    )
    return scored.sort_values(by="priority_score", ascending=False).reset_index(drop=True)


def score_to_priority_band(score: float, scoring_config: dict) -> str:
    priority_bands = scoring_config.get("priority_bands", {})
    if score >= float(priority_bands.get("high_min", 8.5)):
        return "High"
    if score >= float(priority_bands.get("medium_high_min", 7.5)):
        return "Medium-High"
    if score >= float(priority_bands.get("medium_min", 6.5)):
        return "Medium"
    return "Low"


def save_processed_file(df: pd.DataFrame, source_file: str) -> Path:
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
    output_path = PROCESSED_DIR / f"{Path(source_file).stem}_normalized_scored.csv"
    df.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    csv_files = list_raw_csv_files()

    if not csv_files:
        print("V priečinku data/raw nie je žiadny CSV súbor.")
        return

    first_file = csv_files[0]

    try:
        raw_df = load_raw_csv(first_file)
    except Exception as error:
        print(f"Nepodarilo sa načítať CSV súbor: {first_file.name}")
        print(f"Dôvod: {error}")
        return

    raw_preview = build_raw_preview(raw_df, first_file.name)
    normalized_df = normalize_dataframe(raw_df, first_file.name)
    scoring_config = load_scoring_config()
    scored_df = apply_weighted_score(normalized_df, scoring_config)
    output_path = save_processed_file(scored_df, first_file.name)

    print(f"Načítaný súbor: {first_file.name}")
    print(f"Počet raw riadkov: {len(raw_preview)}")
    print(f"Počet normalizovaných riadkov: {len(scored_df)}")
    print(f"Výstup uložený do: {output_path}")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(
        scored_df[
            [
                "hotel_name",
                "city",
                "review_score",
                "reviews_count",
                "priority_score",
                "priority_band",
                "source_file",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
