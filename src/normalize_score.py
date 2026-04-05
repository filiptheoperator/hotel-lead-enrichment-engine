from pathlib import Path
import hashlib
import re
from urllib.parse import urlparse

import pandas as pd
import yaml

from ingest.raw_loader import list_raw_csv_files, load_raw_csv


PROCESSED_DIR = Path("data/processed")
SCORING_CONFIG_PATH = Path("configs/scoring.yaml")
PROJECT_CONFIG_PATH = Path("configs/project.yaml")
ICP_PROFILES_CONFIG_PATH = Path("configs/icp_profiles.yaml")
RANKING_TUNING_CONFIG_PATH = Path("configs/ranking_tuning.yaml")

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

FINAL_OUTPUT_COLUMNS = [
    "account_id",
    "hotel_name",
    "hotel_name_normalized",
    "review_score",
    "reviews_count",
    "street",
    "city",
    "state",
    "country_code",
    "website",
    "website_domain",
    "phone",
    "category_name",
    "hotel_type_class",
    "geography_fit",
    "independent_chain_class",
    "ownership_type",
    "direct_booking_weakness",
    "ota_dependency_signal_label",
    "source_url",
    "all_categories",
    "source_file",
    "dedupe_status",
    "duplicate_group_id",
    "contact_duplicate_flag",
    "review_flag",
    "review_reason",
    "icp_fit_score",
    "icp_fit_class",
    "non_icp_but_keep",
    "fit_confidence",
    "confidence_reason",
    "review_bucket",
    "owner_gm_decision_cycle_signal",
    "contact_discovery_likelihood",
    "ota_visibility_signal",
    "website_quality",
    "chain_signal_confidence",
    "contact_gap_reason",
    "contact_gap_count",
    "why_not_top_tier",
    "rank_bucket",
    "rank_bucket_reason",
    "ranking_reason",
    "ranking_score",
    "priority_score",
    "priority_band",
    "manual_merge_candidate",
    "active_icp_profile",
]

TEXT_COLUMNS = [
    "hotel_name",
    "street",
    "city",
    "state",
    "category_name",
    "source_url",
    "all_categories",
    "source_file",
]


def load_scoring_config(config_path: Path = SCORING_CONFIG_PATH) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_project_config(config_path: Path = PROJECT_CONFIG_PATH) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_icp_profiles_config(config_path: Path = ICP_PROFILES_CONFIG_PATH) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_ranking_tuning_config(config_path: Path = RANKING_TUNING_CONFIG_PATH) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_country_code(value: object) -> str:
    return normalize_text(value).upper()


def normalize_match_text(value: object) -> str:
    text = normalize_text(value).lower()
    if not text:
        return ""
    text = re.sub(r"[^a-z0-9]+", " ", text)
    return re.sub(r"\s+", " ", text).strip()


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


def normalize_website_domain(value: object) -> str:
    website = normalize_website(value)
    if not website:
        return ""
    parsed = urlparse(website)
    domain = parsed.netloc.lower().strip()
    if domain.startswith("www."):
        domain = domain[4:]
    return domain


def build_account_id(row: pd.Series) -> str:
    raw = "|".join(
        [
            normalize_text(row.get("hotel_name_normalized")).lower(),
            normalize_text(row.get("city_normalized")).lower(),
            normalize_text(row.get("website_domain")).lower(),
            normalize_text(row.get("source_file")).lower(),
        ]
    )
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
    return f"acc_{digest}"


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


def count_categories(value: str) -> int:
    if not value:
        return 0
    return len([item for item in value.split(" | ") if item])


def normalize_dataframe(df: pd.DataFrame, source_file: str) -> pd.DataFrame:
    normalized = df.rename(columns=RAW_TO_NORMALIZED_COLUMNS).copy()
    normalized["all_categories"] = collect_categories(df)
    normalized["source_file"] = source_file

    for column in NORMALIZED_COLUMNS:
        if column not in normalized.columns:
            normalized[column] = ""

    normalized = normalized[NORMALIZED_COLUMNS].copy()

    for column in TEXT_COLUMNS:
        normalized[column] = normalized[column].apply(normalize_text)

    normalized["country_code"] = normalized["country_code"].apply(normalize_country_code)
    normalized["website"] = normalized["website"].apply(normalize_website)
    normalized["phone"] = normalized["phone"].apply(normalize_phone)
    normalized["hotel_name_normalized"] = normalized["hotel_name"].apply(normalize_match_text)
    normalized["city_normalized"] = normalized["city"].apply(normalize_match_text)
    normalized["street_normalized"] = normalized["street"].apply(normalize_match_text)
    normalized["website_domain"] = normalized["website"].apply(normalize_website_domain)
    normalized["account_id"] = normalized.apply(build_account_id, axis=1)

    normalized["review_score"] = pd.to_numeric(
        normalized["review_score"], errors="coerce"
    ).fillna(0.0)
    normalized["reviews_count"] = pd.to_numeric(
        normalized["reviews_count"], errors="coerce"
    ).fillna(0).astype(int)

    normalized["duplicate_group_id"] = normalized.apply(build_duplicate_group_id, axis=1)
    normalized["exact_row_key"] = normalized.apply(build_exact_row_key, axis=1)
    normalized["contact_identity_key"] = normalized.apply(build_contact_identity_key, axis=1)

    duplicate_group_counts = normalized["duplicate_group_id"].value_counts()
    contact_counts = normalized["contact_identity_key"].value_counts()

    normalized["dedupe_status"] = normalized["duplicate_group_id"].apply(
        lambda value: "merged_exact_duplicate" if value and duplicate_group_counts.get(value, 0) > 1 else "unique"
    )
    normalized["contact_duplicate_flag"] = normalized["contact_identity_key"].apply(
        lambda value: "yes" if value and contact_counts.get(value, 0) > 1 else "no"
    )

    normalized = normalized.drop_duplicates(subset=["exact_row_key"], keep="first").reset_index(drop=True)

    return normalized


def maybe_apply_sample_batch(df: pd.DataFrame, project_config: dict) -> tuple[pd.DataFrame, bool, int]:
    sample_mode_enabled = bool(project_config.get("sample_batch_mode", False))
    sample_batch_size = int(project_config.get("sample_batch_size", 10))

    if not sample_mode_enabled:
        return df, False, len(df)

    limited_df = df.head(sample_batch_size).copy()
    return limited_df, True, len(limited_df)


def validate_icp_profile(project_config: dict, scoring_config: dict, icp_profiles_config: dict) -> str:
    active_profile = normalize_text(project_config.get("active_icp_profile"))
    enforce = bool(project_config.get("enforce_single_icp_profile_per_run", True))
    if not enforce:
        return active_profile or "unlocked_profile"
    if not active_profile:
        raise ValueError("Chýba active_icp_profile v configs/project.yaml.")
    known_profiles = icp_profiles_config.get("icp_profiles", {})
    if active_profile not in known_profiles:
        raise ValueError(f"Neznámy ICP profil: {active_profile}")
    profile = known_profiles.get(active_profile, {})
    heuristics = scoring_config.get("scoring", {}).get("heuristics", {})
    profile_country_codes = [normalize_text(value).upper() for value in profile.get("target_country_codes", [])]
    scoring_country_codes = [normalize_text(value).upper() for value in heuristics.get("target_country_codes", [])]
    if profile_country_codes != scoring_country_codes:
        raise ValueError("ICP profile guard zlyhal: target_country_codes v scoring.yaml nesedia s active_icp_profile.")
    return active_profile


def clamp_score(value: float) -> float:
    return max(0.0, min(10.0, value))


def contains_any_keyword(text: str, keywords: list[str]) -> bool:
    normalized_text = normalize_match_text(text)
    if not normalized_text:
        return False
    return any(normalize_match_text(keyword) in normalized_text for keyword in keywords if normalize_match_text(keyword))


def classify_hotel_type(category_name: str, all_categories: str, scoring_config: dict) -> tuple[str, float]:
    heuristics = scoring_config.get("scoring", {}).get("heuristics", {})
    combined = " | ".join([normalize_text(category_name), normalize_text(all_categories)])
    if contains_any_keyword(combined, heuristics.get("preferred_hotel_type_keywords", [])):
        return "Preferred hotel", 10.0
    if contains_any_keyword(combined, heuristics.get("review_hotel_type_keywords", [])):
        return "Review type", 5.0
    if "hotel" in normalize_match_text(combined):
        return "Hotel", 8.0
    return "Other lodging", 3.0


def classify_geography(city: str, country_code: str, scoring_config: dict) -> tuple[str, float]:
    heuristics = scoring_config.get("scoring", {}).get("heuristics", {})
    target_country_codes = [normalize_text(item).upper() for item in heuristics.get("target_country_codes", [])]
    target_city_keywords = heuristics.get("target_city_keywords", [])
    city_normalized = normalize_match_text(city)
    country_match = normalize_text(country_code).upper() in target_country_codes
    city_match = any(normalize_match_text(keyword) == city_normalized for keyword in target_city_keywords if normalize_match_text(keyword))
    if city_match and country_match:
        return "Core geography", 10.0
    if country_match:
        return "In-country expansion", 7.0
    return "Out-of-profile geography", 3.0


def classify_independence(hotel_name: str, website_domain: str, all_categories: str, scoring_config: dict) -> tuple[str, str, float]:
    heuristics = scoring_config.get("scoring", {}).get("heuristics", {})
    chain_keywords = heuristics.get("chain_keywords", [])
    combined = " | ".join([normalize_text(hotel_name), normalize_text(website_domain), normalize_text(all_categories)])
    if contains_any_keyword(combined, chain_keywords):
        return "Chain candidate", "Chain-owned or branded candidate", 3.0
    return "Independent candidate", "Independent operator candidate", 9.0


def build_duplicate_group_id(row: pd.Series) -> str:
    hotel = normalize_text(row.get("hotel_name_normalized"))
    city = normalize_text(row.get("city_normalized"))
    street = normalize_text(row.get("street_normalized"))
    website_domain = normalize_text(row.get("website_domain"))
    if hotel and city and street:
        return f"{hotel}|{city}|{street}"
    if hotel and city and website_domain:
        return f"{hotel}|{city}|{website_domain}"
    return f"{hotel}|{city}"


def build_exact_row_key(row: pd.Series) -> str:
    return "|".join(
        [
            normalize_text(row.get("duplicate_group_id")),
            normalize_text(row.get("website_domain")),
            normalize_text(row.get("phone")),
        ]
    )


def build_contact_identity_key(row: pd.Series) -> str:
    phone = normalize_text(row.get("phone"))
    duplicate_group_id = normalize_text(row.get("duplicate_group_id"))
    if not duplicate_group_id or not phone:
        return ""
    return "|".join([duplicate_group_id, phone])


def build_fit_confidence(row: pd.Series) -> float:
    score = 0.0
    if normalize_text(row.get("website")):
        score += 3.0
    if normalize_text(row.get("phone")):
        score += 2.0
    if normalize_text(row.get("city")) and normalize_text(row.get("country_code")):
        score += 2.0
    if normalize_text(row.get("category_name")):
        score += 1.5
    if int(row.get("reviews_count", 0) or 0) > 0:
        score += 1.5
    return clamp_score(score)


def build_confidence_reason(row: pd.Series) -> str:
    reasons: list[str] = []
    if normalize_text(row.get("website")):
        reasons.append("website_present")
    else:
        reasons.append("website_missing")
    if normalize_text(row.get("phone")):
        reasons.append("phone_present")
    else:
        reasons.append("phone_missing")
    if normalize_text(row.get("category_name")):
        reasons.append("category_present")
    if int(row.get("reviews_count", 0) or 0) > 0:
        reasons.append("reviews_present")
    return " | ".join(reasons[:4])


def build_icp_fit_class(score_100: float) -> str:
    if score_100 >= 75:
        return "Keep"
    if score_100 >= 45:
        return "Review"
    return "Low-fit"


def build_review_reason(row: pd.Series) -> str:
    reasons: list[str] = []
    if normalize_text(row.get("independent_chain_class")) == "Chain candidate":
        reasons.append("possible_chain")
    if normalize_text(row.get("hotel_type_class")) == "Review type":
        reasons.append("review_type")
    if normalize_text(row.get("geography_fit")) == "Out-of-profile geography":
        reasons.append("out_of_profile_geography")
    if not normalize_text(row.get("website")) and not normalize_text(row.get("phone")):
        reasons.append("missing_contact_data")
    if float(row.get("fit_confidence", 0) or 0) < 5.0:
        reasons.append("low_fit_confidence")
    duplicate_group_id = normalize_text(row.get("duplicate_group_id"))
    exact_row_key = normalize_text(row.get("exact_row_key"))
    if duplicate_group_id and duplicate_group_id != exact_row_key and normalize_text(row.get("dedupe_status")) == "merged_exact_duplicate":
        reasons.append("exact_duplicate_merged")
    return " | ".join(reasons)


def build_ranking_reason(row: pd.Series) -> str:
    reasons: list[str] = []
    icp_fit_class = normalize_text(row.get("icp_fit_class"))
    if icp_fit_class == "Keep":
        reasons.append("strong_icp_fit")
    elif icp_fit_class == "Review":
        reasons.append("review_fit")
    else:
        reasons.append("low_fit")
    if normalize_text(row.get("independent_chain_class")) == "Independent candidate":
        reasons.append("independent_signal")
    if normalize_text(row.get("hotel_type_class")) == "Preferred hotel":
        reasons.append("preferred_hotel_type")
    if normalize_text(row.get("geography_fit")) == "Core geography":
        reasons.append("core_geography")
    elif normalize_text(row.get("geography_fit")) == "Out-of-profile geography":
        reasons.append("out_of_profile_geography")
    if normalize_text(row.get("website")):
        reasons.append("has_website")
    if normalize_text(row.get("phone")):
        reasons.append("has_phone")
    return " | ".join(reasons[:4])


def build_review_bucket(row: pd.Series) -> str:
    if normalize_text(row.get("dedupe_status")) != "unique" or normalize_text(row.get("contact_duplicate_flag")) == "yes":
        return "dedupe_review"
    if normalize_text(row.get("review_flag")) == "yes":
        return "manual_review"
    if normalize_text(row.get("icp_fit_class")) == "Low-fit":
        return "kept_low_fit"
    return "ready_ranked"


def build_owner_gm_decision_cycle_signal(row: pd.Series) -> str:
    if normalize_text(row.get("independent_chain_class")) == "Independent candidate":
        return "Likely shorter owner_gm_cycle"
    return "Likely layered decision_cycle"


def build_contact_discovery_likelihood(row: pd.Series) -> str:
    has_website = bool(normalize_text(row.get("website")))
    has_phone = bool(normalize_text(row.get("phone")))
    if has_website and has_phone:
        return "High"
    if has_website or has_phone:
        return "Medium"
    return "Low"


def build_contact_gap_reason(row: pd.Series) -> str:
    has_website = bool(normalize_text(row.get("website")))
    has_phone = bool(normalize_text(row.get("phone")))
    if has_website and has_phone:
        return "no_major_gap"
    if has_website and not has_phone:
        return "phone_missing"
    if has_phone and not has_website:
        return "website_missing"
    return "website_and_phone_missing"


def build_contact_gap_count(row: pd.Series) -> int:
    missing = 0
    if not normalize_text(row.get("website")):
        missing += 1
    if not normalize_text(row.get("phone")):
        missing += 1
    return missing


def build_chain_signal_confidence(row: pd.Series) -> str:
    chain_class = normalize_text(row.get("independent_chain_class"))
    website_domain = normalize_text(row.get("website_domain"))
    hotel_name = normalize_text(row.get("hotel_name"))
    if chain_class == "Chain candidate" and website_domain and hotel_name:
        return "High"
    if chain_class == "Chain candidate":
        return "Medium"
    return "Low"


def build_website_quality(row: pd.Series) -> str:
    website = normalize_text(row.get("website"))
    website_domain = normalize_text(row.get("website_domain"))
    parsed = urlparse(website) if website else None
    path = normalize_text(parsed.path if parsed else "")
    query = normalize_text(parsed.query if parsed else "")
    reviews_count = int(row.get("reviews_count", 0) or 0)
    if not website:
        return "Missing"
    if website_domain and (path in {"", "/"} and not query) and reviews_count >= 20:
        return "Strong"
    if website_domain and path in {"", "/"}:
        return "Basic"
    return "Weak"


def build_why_not_top_tier(row: pd.Series) -> str:
    reasons: list[str] = []
    if normalize_text(row.get("independent_chain_class")) == "Chain candidate":
        reasons.append("chain_signal")
    if normalize_text(row.get("geography_fit")) == "Out-of-profile geography":
        reasons.append("geo_mismatch")
    if normalize_text(row.get("contact_gap_reason")) != "no_major_gap":
        reasons.append(normalize_text(row.get("contact_gap_reason")))
    if normalize_text(row.get("website_quality")) == "Missing":
        reasons.append("website_missing")
    if normalize_text(row.get("hotel_type_class")) == "Review type":
        reasons.append("review_type")
    return " | ".join(reasons[:3]) or "top_tier_candidate"


def build_rank_bucket(ranking_score: float) -> str:
    if ranking_score >= 80:
        return "A"
    if ranking_score >= 65:
        return "B"
    if ranking_score >= 50:
        return "C"
    return "D"


def build_rank_bucket_reason(row: pd.Series) -> str:
    bucket = normalize_text(row.get("rank_bucket"))
    why_not = normalize_text(row.get("why_not_top_tier"))
    ranking_reason = normalize_text(row.get("ranking_reason"))
    if bucket == "A":
        return ranking_reason or "top_ranked"
    return why_not or ranking_reason or "lower_rank_bucket"


def compute_score_components(df: pd.DataFrame) -> pd.DataFrame:
    scoring_config = load_scoring_config()
    has_website = df["website"].apply(bool)
    has_phone = df["phone"].apply(bool)

    review_score_component = (df["review_score"] / 5.0) * 10.0
    review_count_component = (df["reviews_count"].clip(upper=500) / 500.0) * 10.0

    direct_booking_strength = has_website.apply(lambda value: 10.0 if value else 0.0)
    ota_dependency_signal = has_website.apply(lambda value: 6.0 if value else 4.0)
    operational_complexity = df["all_categories"].apply(
        lambda value: clamp_score(float(min(count_categories(value), 5) * 2))
    )
    review_signal = ((review_score_component + review_count_component) / 2.0).apply(clamp_score)
    contact_quality = (has_website.astype(int) + has_phone.astype(int)) * 5.0
    fit_confidence = df.apply(build_fit_confidence, axis=1)
    website_quality_component = df.apply(
        lambda row: 10.0 if normalize_text(row.get("website")) and int(row.get("reviews_count", 0) or 0) >= 20
        else 6.0 if normalize_text(row.get("website"))
        else 0.0,
        axis=1,
    )

    hotel_type = df.apply(
        lambda row: classify_hotel_type(
            normalize_text(row.get("category_name")),
            normalize_text(row.get("all_categories")),
            scoring_config,
        ),
        axis=1,
    )
    geography = df.apply(
        lambda row: classify_geography(
            normalize_text(row.get("city")),
            normalize_text(row.get("country_code")),
            scoring_config,
        ),
        axis=1,
    )
    independence = df.apply(
        lambda row: classify_independence(
            normalize_text(row.get("hotel_name")),
            normalize_text(row.get("website_domain")),
            normalize_text(row.get("all_categories")),
            scoring_config,
        ),
        axis=1,
    )

    hotel_type_relevance = pd.to_numeric(hotel_type.apply(lambda item: item[1]), errors="coerce").fillna(0.0)
    geography_fit = pd.to_numeric(geography.apply(lambda item: item[1]), errors="coerce").fillna(0.0)
    independence_signal = pd.to_numeric(independence.apply(lambda item: item[2]), errors="coerce").fillna(0.0)
    direct_booking_strength = pd.to_numeric(direct_booking_strength, errors="coerce").fillna(0.0)
    ota_dependency_signal = pd.to_numeric(ota_dependency_signal, errors="coerce").fillna(0.0)
    operational_complexity = pd.to_numeric(operational_complexity, errors="coerce").fillna(0.0)
    review_signal = pd.to_numeric(review_signal, errors="coerce").fillna(0.0)
    contact_quality = pd.to_numeric(contact_quality, errors="coerce").fillna(0.0)
    fit_confidence = pd.to_numeric(fit_confidence, errors="coerce").fillna(0.0)
    icp_fit = (
        hotel_type_relevance * 0.4
        + geography_fit * 0.3
        + independence_signal * 0.3
    ).apply(clamp_score)

    return pd.DataFrame(
        {
            "icp_fit": icp_fit,
            "independence_signal": independence_signal,
            "geography_fit": geography_fit,
            "hotel_type_relevance": hotel_type_relevance,
            "direct_booking_strength": direct_booking_strength,
            "ota_dependency_signal": ota_dependency_signal,
            "operational_complexity": operational_complexity,
            "review_signal": review_signal,
            "contact_quality": contact_quality,
            "fit_confidence": fit_confidence,
            "website_quality_component": website_quality_component,
        }
    )


def apply_weighted_score(df: pd.DataFrame, scoring_config: dict, ranking_tuning_config: dict) -> pd.DataFrame:
    scored = df.copy()
    components = compute_score_components(scored)
    weights = scoring_config.get("scoring", {}).get("weights", {})

    scored = pd.concat([scored, components], axis=1)
    hotel_type = scored.apply(
        lambda row: classify_hotel_type(
            normalize_text(row.get("category_name")),
            normalize_text(row.get("all_categories")),
            scoring_config,
        ),
        axis=1,
    )
    geography = scored.apply(
        lambda row: classify_geography(
            normalize_text(row.get("city")),
            normalize_text(row.get("country_code")),
            scoring_config,
        ),
        axis=1,
    )
    independence = scored.apply(
        lambda row: classify_independence(
            normalize_text(row.get("hotel_name")),
            normalize_text(row.get("website_domain")),
            normalize_text(row.get("all_categories")),
            scoring_config,
        ),
        axis=1,
    )

    scored["ranking_score"] = 0.0

    for column in components.columns:
        weight = float(weights.get(column, 0.0))
        scored["ranking_score"] += scored[column] * weight

    scored["ranking_score"] = (scored["ranking_score"] * 10.0).round(2)
    scored["icp_fit_score"] = (scored["icp_fit"] * 10.0).round(2)
    scored["fit_confidence"] = scored["fit_confidence"].round(2)
    scored["icp_fit_class"] = scored["icp_fit_score"].apply(build_icp_fit_class)
    low_fit_threshold = float(ranking_tuning_config.get("ranking_tuning", {}).get("non_icp_keep_threshold", 45))
    scored["non_icp_but_keep"] = scored["icp_fit_score"].apply(
        lambda value: "yes" if float(value or 0) < low_fit_threshold else "no"
    )
    scored["hotel_type_class"] = hotel_type.apply(lambda item: item[0])
    scored["geography_fit"] = geography.apply(lambda item: item[0])
    scored["independent_chain_class"] = independence.apply(lambda item: item[0])
    scored["ownership_type"] = independence.apply(lambda item: item[1])
    scored["direct_booking_weakness"] = scored["website"].apply(
        lambda value: "Needs direct booking clarity" if normalize_text(value) else "Website missing"
    )
    scored["ota_visibility_signal"] = scored["website"].apply(
        lambda value: 3.0 if normalize_text(value) else 7.0
    )
    scored["ota_dependency_signal_label"] = scored["website"].apply(
        lambda value: "Low visible" if normalize_text(value) else "Unknown / likely higher OTA reliance"
    )
    scored["website_quality"] = scored.apply(build_website_quality, axis=1)
    scored["chain_signal_confidence"] = scored.apply(build_chain_signal_confidence, axis=1)
    scored["contact_gap_reason"] = scored.apply(build_contact_gap_reason, axis=1)
    scored["contact_gap_count"] = scored.apply(build_contact_gap_count, axis=1)
    scored["priority_score"] = (scored["ranking_score"] / 10.0).round(2)
    scored["priority_band"] = scored["priority_score"].apply(
        lambda value: score_to_priority_band(value, scoring_config)
    )
    scored["review_reason"] = scored.apply(build_review_reason, axis=1)
    scored["review_flag"] = scored["review_reason"].apply(lambda value: "yes" if normalize_text(value) else "no")
    duplicate_group_counts = scored["duplicate_group_id"].value_counts()
    scored["manual_merge_candidate"] = scored["duplicate_group_id"].apply(
        lambda value: "yes" if value and duplicate_group_counts.get(value, 0) > 1 else "no"
    )
    scored["confidence_reason"] = scored.apply(build_confidence_reason, axis=1)
    scored["review_bucket"] = scored.apply(build_review_bucket, axis=1)
    scored["owner_gm_decision_cycle_signal"] = scored.apply(build_owner_gm_decision_cycle_signal, axis=1)
    scored["contact_discovery_likelihood"] = scored.apply(build_contact_discovery_likelihood, axis=1)
    scored["why_not_top_tier"] = scored.apply(build_why_not_top_tier, axis=1)
    scored["rank_bucket"] = scored["ranking_score"].apply(build_rank_bucket)
    scored["rank_bucket_reason"] = scored.apply(build_rank_bucket_reason, axis=1)
    scored["ranking_reason"] = scored.apply(build_ranking_reason, axis=1)
    if "active_icp_profile" not in scored.columns:
        scored["active_icp_profile"] = ""
    scored = scored.sort_values(
        by=["ranking_score", "review_score", "reviews_count"],
        ascending=[False, False, False],
    ).reset_index(drop=True)
    return scored[FINAL_OUTPUT_COLUMNS].copy()


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

    first_file = csv_files[-1]

    try:
        raw_df = load_raw_csv(first_file)
    except Exception as error:
        print(f"Nepodarilo sa načítať CSV súbor: {first_file.name}")
        print(f"Dôvod: {error}")
        return

    normalized_df = normalize_dataframe(raw_df, first_file.name)
    project_config = load_project_config()
    normalized_df, sample_mode_enabled, sample_row_count = maybe_apply_sample_batch(
        normalized_df,
        project_config,
    )
    scoring_config = load_scoring_config()
    ranking_tuning_config = load_ranking_tuning_config()
    icp_profiles_config = load_icp_profiles_config()
    active_icp_profile = validate_icp_profile(project_config, scoring_config, icp_profiles_config)
    scored_df = apply_weighted_score(normalized_df, scoring_config, ranking_tuning_config)
    scored_df["active_icp_profile"] = active_icp_profile
    output_path = save_processed_file(scored_df, first_file.name)

    print(f"Načítaný súbor: {first_file.name}")
    print(f"Počet raw riadkov: {len(raw_df)}")
    if sample_mode_enabled:
        print(f"Sample batch mode: zapnutý ({sample_row_count} riadkov)")
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
