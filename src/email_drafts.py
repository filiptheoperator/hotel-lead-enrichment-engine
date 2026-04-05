from pathlib import Path

import pandas as pd
import yaml


ENRICHMENT_OUTPUT_DIR = Path("outputs/enrichment")
EMAIL_OUTPUT_DIR = Path("outputs/email_drafts")
EMAIL_CONFIG_PATH = Path("configs/email.yaml")


def list_enriched_files(enrichment_dir: Path = ENRICHMENT_OUTPUT_DIR) -> list[Path]:
    if not enrichment_dir.exists():
        return []
    return sorted(enrichment_dir.glob("*_enriched.csv"), key=lambda path: path.stat().st_mtime)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_email_config() -> dict:
    if not EMAIL_CONFIG_PATH.exists():
        return {}
    with EMAIL_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


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
    email_angle = normalize_text(row.get("email_angle"))
    if email_angle == "opening_hours_clarity":
        return f"{hotel_name}: krátky postreh"
    if email_angle == "checkin_checkout_clarity":
        return f"{hotel_name}: krátky postreh"
    return f"{hotel_name}: krátky nápad"


def build_hook(row: pd.Series) -> str:
    if normalize_text(row.get("email_hook")):
        return normalize_text(row.get("email_hook"))
    if row["hotel_name"] and row["city"]:
        return f"Pozeral som sa na {row['hotel_name']} v lokalite {row['city']}."
    if row["hotel_name"]:
        return f"Pozeral som sa na {row['hotel_name']}."
    return "Pozeral som sa na váš hotel pri rýchlom verejnom prehľade."


def build_cold_email(row: pd.Series) -> str:
    parts = [
        "Dobrý deň,",
        "",
        normalize_text(row.get("personalization_line")),
        normalize_text(row.get("give_first_line")),
        normalize_text(row.get("relevance_line")),
    ]
    proof_line = normalize_text(row.get("proof_line"))
    if proof_line:
        parts.append(proof_line)
    parts.extend(
        [
            "",
            normalize_text(row.get("low_friction_cta")),
            "",
            "S pozdravom",
        ]
    )
    return "\n".join(parts)


def build_followup_email(row: pd.Series) -> str:
    hotel_name = row["hotel_name"] or "váš hotel"
    low_friction_cta = normalize_text(row.get("low_friction_cta")) or "Ak chcete, pošlem to stručne v pár bodoch."
    return (
        f"Dobrý deň,\n\n"
        f"jemne sa pripomínam k predošlej správe pre {hotel_name}.\n"
        f"{low_friction_cta}\n\n"
        f"S pozdravom"
    )


def ensure_column(df: pd.DataFrame, column: str, default_value: str = "") -> None:
    if column not in df.columns:
        df[column] = default_value


def build_personalization_line(row: pd.Series) -> str:
    return build_hook(row)


def build_give_first_line(row: pd.Series) -> str:
    insight = normalize_text(row.get("give_first_insight"))
    if insight:
        return insight
    return "Pri rýchlom pozretí verejných údajov som si všimol jeden stručný praktický detail."


def build_relevance_line(row: pd.Series) -> str:
    factual_line = build_short_factual_line(row)
    main_issue = normalize_text(row.get("main_observed_issue"))
    if main_issue:
        return f"{main_issue} {factual_line}"
    return factual_line


def build_low_friction_cta(row: pd.Series) -> str:
    micro_cta = normalize_text(row.get("micro_cta"))
    if micro_cta:
        return micro_cta
    return "Ak chcete, pošlem 3 stručné postrehy v krátkej forme."


def build_proof_line(row: pd.Series) -> str:
    return normalize_text(row.get("proof_snippet"))


def build_email_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    emails = df.copy()
    email_config = load_email_config().get("email", {})

    for column in emails.columns:
        if emails[column].dtype == object:
            emails[column] = emails[column].apply(normalize_text)

    for column in [
        "hotel_name_normalized",
        "country_code",
        "account_id",
        "ranking_score",
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
        "why_not_top_tier",
        "rank_bucket",
        "ranking_reason",
        "review_flag",
        "review_reason",
        "website_domain",
        "hotel_type_class",
        "geography_fit",
        "independent_chain_class",
        "ownership_type",
        "direct_booking_weakness",
        "ota_dependency_signal_label",
        "dedupe_status",
        "duplicate_group_id",
        "contact_duplicate_flag",
        "manual_merge_candidate",
        "active_icp_profile",
        "give_first_insight",
        "main_observed_issue",
        "email_hook",
        "micro_cta",
        "primary_email_goal",
        "proof_snippet",
        "email_angle",
        "cta_type",
        "variant_id",
        "test_batch",
        "reply_outcome",
    ]:
        ensure_column(emails, column, "")

    emails["subject_line"] = emails.apply(build_subject_line, axis=1)
    emails["hook"] = emails.apply(build_hook, axis=1)
    emails["personalization_line"] = emails.apply(build_personalization_line, axis=1)
    emails["give_first_line"] = emails.apply(build_give_first_line, axis=1)
    emails["relevance_line"] = emails.apply(build_relevance_line, axis=1)
    emails["low_friction_cta"] = emails.apply(build_low_friction_cta, axis=1)
    emails["proof_line"] = emails.apply(build_proof_line, axis=1)
    if email_config.get("one_email_one_goal", True):
        emails["primary_email_goal"] = emails["primary_email_goal"].replace("", email_config.get("primary_email_goal", "reply_with_permission"))
    emails["cta_type"] = emails["cta_type"].replace("", email_config.get("default_cta_type", "low_friction_permission"))
    emails["cold_email"] = emails.apply(build_cold_email, axis=1)
    emails["followup_email"] = emails.apply(build_followup_email, axis=1)

    return emails[
        [
            "account_id",
            "hotel_name",
            "hotel_name_normalized",
            "city",
            "country_code",
            "priority_band",
            "priority_score",
            "ranking_score",
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
            "why_not_top_tier",
            "rank_bucket",
            "ranking_reason",
            "review_flag",
            "review_reason",
            "website",
            "website_domain",
            "phone",
            "contact_status",
            "hotel_type_class",
            "geography_fit",
            "independent_chain_class",
            "ownership_type",
            "direct_booking_weakness",
            "ota_dependency_signal_label",
            "dedupe_status",
            "duplicate_group_id",
            "contact_duplicate_flag",
            "manual_merge_candidate",
            "active_icp_profile",
            "factual_summary",
            "subject_line",
            "hook",
            "give_first_insight",
            "main_observed_issue",
            "email_hook",
            "micro_cta",
            "primary_email_goal",
            "proof_snippet",
            "email_angle",
            "cta_type",
            "variant_id",
            "test_batch",
            "reply_outcome",
            "personalization_line",
            "give_first_line",
            "relevance_line",
            "low_friction_cta",
            "proof_line",
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

    first_file = enriched_files[-1]

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
                "give_first_insight",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
