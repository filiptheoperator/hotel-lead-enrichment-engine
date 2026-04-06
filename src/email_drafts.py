import json
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


ENRICHMENT_OUTPUT_DIR = Path("outputs/enrichment")
EMAIL_OUTPUT_DIR = Path("outputs/email_drafts")
FACTUAL_ENRICHMENT_DIR = Path("outputs/factual_enrichment")
COMMERCIAL_SYNTHESIS_DIR = Path("outputs/commercial_synthesis")
RANKED_DIR = Path("outputs/ranked")
EMAIL_CONFIG_PATH = Path("configs/email.yaml")
UNKNOWN_VALUE_LABEL = "Verejne nepotvrdené"


def list_enriched_files(enrichment_dir: Path = ENRICHMENT_OUTPUT_DIR) -> list[Path]:
    if not enrichment_dir.exists():
        return []
    return sorted(enrichment_dir.glob("*_enriched*.csv"), key=lambda path: path.stat().st_mtime)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_email_config() -> dict:
    if not EMAIL_CONFIG_PATH.exists():
        return {}
    with EMAIL_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def ensure_column(df: pd.DataFrame, column: str, default_value: str = "") -> None:
    if column not in df.columns:
        df[column] = default_value


def collapse_whitespace(value: object) -> str:
    return " ".join(normalize_text(value).split())


def truncate_text(value: object, max_len: int = 180) -> str:
    text = collapse_whitespace(value)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip(" ,;:-") + "…"


def humanize_outreach_text(value: object, max_len: int = 220) -> str:
    text = collapse_whitespace(value)
    if not text:
        return ""
    replacements = {
        "ICP": "",
        "silnú zhodu": "dobrú zhodu",
        "atraktívny cieľ pre spoluprácu": "prevádzku, kde sa oplatí preveriť konkrétne miesto trenia",
        "atraktívny cieľ": "prevádzku, kde sa oplatí preveriť konkrétne miesto trenia",
        "s našimi riešeniami": "",
        "našimi riešeniami": "",
        "čo by sme mohli pomôcť preveriť": "čo sa oplatí preveriť",
        "čo by sme mohli pomôcť": "čo sa oplatí preveriť",
        "Zaujímalo by nás": "Pri rýchlom pozretí nás zaujalo",
        "Váš vysoký rating a nezávislý status sú ideálnym základom": "Vidno tu dobrú verejnú spätnú väzbu a nezávislý model prevádzky",
        "Vaša silná pozícia": "Vidno silnú pozíciu",
        "obchodné možnosti": "miesta, kde sa môže strácať časť záujmu pred dopytom",
        "rozšírenie eventových a reštauračných služieb": "koordináciu eventového, gastro a pobytového dopytu",
        "príležitosti na zlepšenie": "miesta, kde sa môže strácať časť záujmu pred dopytom",
        "môžeme pomôcť lepšie zvládnuť": "sa oplatí presnejšie preveriť",
        "môžeme pomôcť": "sa oplatí preveriť",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = " ".join(text.split())
    return truncate_text(text, max_len=max_len)


def starts_with_observation(value: str) -> bool:
    lowered = collapse_whitespace(value).lower()
    return lowered.startswith(("všimli sme si", "pri takomto type hotela", "často sa tu", "oplatí sa preveriť", "vidno"))


def build_source_batch_stem(value: str) -> str:
    stem = Path(normalize_text(value)).stem
    for marker in [
        "_normalized_scored_enriched",
        "_normalized_scored",
        "_enriched",
    ]:
        if marker in stem:
            return stem.split(marker, 1)[0]
    return stem


def get_latest_ranked_file() -> Optional[Path]:
    files = sorted(RANKED_DIR.glob("*_ranking_refreshed*.csv"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def get_ranked_file_for_enrichment(enrichment_file_name: str) -> Optional[Path]:
    preferred_ranked_file = normalize_text(os.getenv("EMAIL_RANKED_SOURCE_FILE"))
    if preferred_ranked_file:
        ranked_path = RANKED_DIR / preferred_ranked_file
        if ranked_path.exists():
            return ranked_path

    enrichment_stem = Path(enrichment_file_name).stem
    matching = sorted(
        RANKED_DIR.glob(f"{enrichment_stem}_ranking_refreshed*.csv"),
        key=lambda path: path.stat().st_mtime,
    )
    if matching:
        return matching[-1]
    return get_latest_ranked_file()


def build_short_factual_line(row: pd.Series) -> str:
    facts: list[str] = []

    if row["city"]:
        facts.append(f"v lokalite {row['city']}")

    priority_level_final = normalize_text(row.get("priority_level_final"))
    ranking_score_final = format_score(row.get("ranking_score_final"))
    priority_band = normalize_text(row.get("priority_band"))
    priority_score = format_score(row.get("priority_score"))
    if priority_level_final and ranking_score_final:
        facts.append(f"s finálnou prioritou {priority_level_final} ({ranking_score_final})")
    elif priority_band:
        if priority_score:
            facts.append(f"s prioritou {priority_band} ({priority_score})")
        else:
            facts.append(f"s prioritou {priority_band}")

    review_signal = normalize_text(row.get("review_signal_summary"))
    if review_signal:
        facts.append(f"so signalom hodnotení {review_signal}")
    else:
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
    best_entry_angle = normalize_text(row.get("best_entry_angle")).lower()
    why_commercially_interesting = normalize_text(row.get("why_commercially_interesting")).lower()
    contact_route = normalize_text(row.get("recommended_first_contact_route")).lower()
    recommended_hook = normalize_text(row.get("recommended_hook")).lower()
    main_bottleneck = normalize_text(row.get("main_bottleneck_hypothesis")).lower()

    if "event" in best_entry_angle or "kongres" in best_entry_angle or "event" in why_commercially_interesting:
        return f"{hotel_name}: krátky postreh k event dopytu"
    if "recepci" in contact_route or "kontakt" in contact_route:
        return f"{hotel_name}: krátky postreh k prvému kontaktu"
    if "prevádz" in recommended_hook or "kapacit" in recommended_hook or "prevádz" in main_bottleneck:
        return f"{hotel_name}: krátky postreh k prevádzkovým info"
    if "praktick" in recommended_hook or "inform" in recommended_hook:
        return f"{hotel_name}: krátky postreh k praktickým info"
    if "event" in recommended_hook or "kongres" in recommended_hook:
        return f"{hotel_name}: krátky postreh k event dopytu"
    if "check-in" in recommended_hook or "check in" in recommended_hook:
        return f"{hotel_name}: krátky postreh k check-in info"
    if normalize_text(row.get("email_angle")) == "checkin_checkout_clarity":
        return f"{hotel_name}: krátky postreh k pobytovým info"
    return f"{hotel_name}: krátky nápad"


def build_hook(row: pd.Series) -> str:
    recommended_hook = humanize_outreach_text(row.get("recommended_hook"), max_len=170)
    if recommended_hook:
        return recommended_hook
    if normalize_text(row.get("email_hook")):
        return normalize_text(row.get("email_hook"))
    if row["hotel_name"] and row["city"]:
        return f"Pozeral som sa na {row['hotel_name']} v lokalite {row['city']}."
    if row["hotel_name"]:
        return f"Pozeral som sa na {row['hotel_name']}."
    return "Pozeral som sa na váš hotel pri rýchlom verejnom prehľade."


def build_personalization_line(row: pd.Series) -> str:
    angle = humanize_outreach_text(row.get("personalization_angle_1"), max_len=300)
    if angle:
        return angle
    return build_hook(row)


def build_give_first_line(row: pd.Series) -> str:
    insight = humanize_outreach_text(row.get("best_entry_angle"), max_len=180)
    if not insight:
        insight = humanize_outreach_text(row.get("recommended_hook"), max_len=180)
    if not insight:
        insight = humanize_outreach_text(row.get("business_interest_summary"), max_len=180)
    if not insight:
        insight = humanize_outreach_text(row.get("give_first_insight"), max_len=180)
    if insight:
        if not starts_with_observation(insight):
            insight = f"Všimli sme si, že {insight[:1].lower() + insight[1:]}"
        return insight
    return "Pri rýchlom pozretí verejných údajov som si všimol jeden stručný praktický detail."


def build_relevance_line(row: pd.Series) -> str:
    why_interesting = humanize_outreach_text(row.get("why_commercially_interesting"), max_len=220)
    if why_interesting:
        return why_interesting
    main_issue = humanize_outreach_text(row.get("main_bottleneck_hypothesis"), max_len=220) or humanize_outreach_text(row.get("main_observed_issue"), max_len=220)
    if main_issue:
        return main_issue
    factual_line = build_short_factual_line(row)
    if normalize_text(row.get("business_interest_summary")):
        return humanize_outreach_text(row.get("business_interest_summary"), max_len=220)
    return factual_line


def build_low_friction_cta(row: pd.Series) -> str:
    micro_cta = normalize_text(row.get("micro_cta"))
    if micro_cta:
        return micro_cta
    first_contact_route = normalize_text(row.get("recommended_first_contact_route"))
    if first_contact_route:
        return "Ak chcete, pošlem 3 stručné postrehy priamo k tejto kontaktnej a dopytovej ceste."
    call_hypothesis = normalize_text(row.get("call_hypothesis"))
    if call_hypothesis:
        return "Ak chcete, pošlem to stručne v 3 bodoch alebo to prejdeme v krátkom 10-min hovore."
    return "Ak chcete, pošlem 3 stručné postrehy v krátkej forme."


def build_proof_line(row: pd.Series) -> str:
    proof_snippet = normalize_text(row.get("proof_snippet"))
    if proof_snippet:
        return proof_snippet

    review_signal = normalize_text(row.get("review_signal_summary"))
    if review_signal:
        return f"Vychádzal som z verejných signálov ako {review_signal}."

    if normalize_text(row.get("hotel_opening_hours_status")) == "Overené vo verejnom zdroji":
        return f"Verejne sa mi podarilo potvrdiť operating hours: {normalize_text(row.get('hotel_opening_hours'))}."

    if normalize_text(row.get("checkin_checkout_status")) == "Overené vo verejnom zdroji":
        return f"Verejne sa mi podarilo potvrdiť check-in/check-out: {normalize_text(row.get('checkin_checkout_info'))}."

    if normalize_text(row.get("business_interest_summary")):
        return build_short_factual_line(row)

    return ""


def build_cold_email(row: pd.Series) -> str:
    personalization = normalize_text(row.get("personalization_line"))
    give_first_line = normalize_text(row.get("give_first_line"))
    relevance_line = normalize_text(row.get("relevance_line"))
    if personalization and give_first_line and personalization == give_first_line:
        personalization = ""
    parts = [
        "Dobrý deň,",
        "",
        personalization,
        give_first_line,
        relevance_line,
    ]
    proof_line = humanize_outreach_text(row.get("proof_line"), max_len=220)
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


def fallback_contact_gap_count(row: pd.Series) -> int:
    try:
        return int(float(row.get("contact_gap_count", 0)))
    except (TypeError, ValueError):
        pass
    gap_reason = normalize_text(row.get("contact_gap_reason"))
    if gap_reason == "website_and_phone_missing":
        return 2
    if gap_reason in {"phone_missing", "website_missing"}:
        return 1
    return 0


def fallback_rank_bucket_reason(row: pd.Series) -> str:
    current = normalize_text(row.get("rank_bucket_reason"))
    if current:
        return current
    if normalize_text(row.get("rank_bucket")) == "A":
        return normalize_text(row.get("ranking_reason")) or "top_ranked"
    return normalize_text(row.get("why_not_top_tier")) or normalize_text(row.get("ranking_reason")) or "lower_rank_bucket"


def format_score(value: object) -> str:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return ""
    return f"{number:.2f}".rstrip("0").rstrip(".")


def build_factual_summary_from_artifact(factual: dict) -> str:
    parts: list[str] = []
    review_summary = normalize_text(factual.get("review_trust_signal", {}).get("summary"))
    if review_summary:
        parts.append(f"review signal {review_summary}")

    room_range = normalize_text(factual.get("room_count_signal", {}).get("rooms_range"))
    if room_range:
        parts.append(f"rooms range {room_range}")

    services = factual.get("service_mix", {})
    active_services = [
        name.replace("_", " ")
        for name, payload in services.items()
        if normalize_text(payload.get("available")) == "yes"
    ]
    if active_services:
        parts.append("service mix " + ", ".join(active_services[:3]))

    if not parts:
        return ""
    return "; ".join(parts)


def first_personalization_angle(commercial: dict) -> str:
    angles = commercial.get("personalization_angles", []) or []
    if isinstance(angles, list):
        for item in angles:
            text = truncate_text(item, max_len=280)
            if text:
                return text
    return ""


def build_row_artifact_context(
    row: pd.Series,
    source_batch_stem: str,
    ranked_lookup: dict[str, dict],
) -> dict[str, str]:
    account_id = normalize_text(row.get("account_id"))
    factual = load_json(FACTUAL_ENRICHMENT_DIR / source_batch_stem / f"{account_id}.json") if account_id else {}
    commercial = load_json(COMMERCIAL_SYNTHESIS_DIR / source_batch_stem / f"{account_id}.json") if account_id else {}
    ranked_row = ranked_lookup.get(account_id, {})

    operating_hours = factual.get("operating_hours", {})
    checkin_checkout = factual.get("checkin_checkout", {})
    room_count_signal = factual.get("room_count_signal", {})
    review_trust_signal = factual.get("review_trust_signal", {})
    ownership_signal = factual.get("ownership_company_signal", {})

    return {
        "factual_summary": build_factual_summary_from_artifact(factual),
        "hotel_opening_hours": normalize_text(operating_hours.get("hotel_opening_hours")),
        "hotel_opening_hours_status": normalize_text(operating_hours.get("status")),
        "checkin_checkout_info": normalize_text(checkin_checkout.get("value")),
        "checkin_checkout_status": normalize_text(checkin_checkout.get("status")),
        "rooms_range": normalize_text(room_count_signal.get("rooms_range")),
        "room_count_value": normalize_text(room_count_signal.get("value")),
        "room_count_status": normalize_text(room_count_signal.get("status")),
        "review_signal_summary": normalize_text(review_trust_signal.get("summary")),
        "ownership_status": normalize_text(ownership_signal.get("status")),
        "business_interest_summary": normalize_text(commercial.get("business_interest_summary")),
        "why_commercially_interesting": normalize_text(commercial.get("why_commercially_interesting")),
        "property_positioning_summary": normalize_text(commercial.get("property_positioning_summary")),
        "main_bottleneck_hypothesis": normalize_text(commercial.get("main_bottleneck_hypothesis")),
        "pain_point_hypothesis": normalize_text(commercial.get("pain_point_hypothesis")),
        "best_entry_angle": normalize_text(commercial.get("best_entry_angle")),
        "personalization_angle_1": first_personalization_angle(commercial),
        "recommended_hook": normalize_text(commercial.get("recommended_hook")),
        "recommended_first_contact_route": normalize_text(commercial.get("recommended_first_contact_route")),
        "likely_decision_maker_hypothesis": normalize_text(commercial.get("likely_decision_maker_hypothesis")),
        "service_complexity_read": normalize_text(commercial.get("service_complexity_read")),
        "commercial_complexity_read": normalize_text(commercial.get("commercial_complexity_read")),
        "direct_booking_friction_hypothesis": normalize_text(commercial.get("direct_booking_friction_hypothesis")),
        "contact_route_friction_hypothesis": normalize_text(commercial.get("contact_route_friction_hypothesis")),
        "call_hypothesis": normalize_text(commercial.get("call_hypothesis")),
        "commercial_verdict": normalize_text(commercial.get("verdict")),
        "ranking_score_final": normalize_text(ranked_row.get("ranking_score_final")),
        "priority_level_final": normalize_text(ranked_row.get("priority_level_final")),
        "rank_bucket_final": normalize_text(ranked_row.get("rank_bucket_final")),
        "ranking_refresh_reason": normalize_text(ranked_row.get("ranking_refresh_reason")),
        "ranking_upside_reasons": normalize_text(ranked_row.get("ranking_upside_reasons")),
        "ranking_downside_reasons": normalize_text(ranked_row.get("ranking_downside_reasons")),
        "ranking_missingness_notes": normalize_text(ranked_row.get("ranking_missingness_notes")),
        "decision_status": normalize_text(ranked_row.get("decision_status")),
        "manual_review_needed": normalize_text(ranked_row.get("manual_review_needed")),
        "review_queue_reason_codes": normalize_text(ranked_row.get("review_queue_reason_codes")),
    }


def load_ranked_lookup(enrichment_source_file: str) -> dict[str, dict]:
    ranked_path = get_ranked_file_for_enrichment(enrichment_source_file)
    if ranked_path is None or not ranked_path.exists():
        return {}
    ranked_df = pd.read_csv(ranked_path)
    for column in ranked_df.columns:
        if ranked_df[column].dtype == object:
            ranked_df[column] = ranked_df[column].apply(normalize_text)
    if "account_id" not in ranked_df.columns:
        return {}
    return {
        normalize_text(row["account_id"]): row.to_dict()
        for _, row in ranked_df.iterrows()
        if normalize_text(row.get("account_id"))
    }


def build_email_dataframe(df: pd.DataFrame, enrichment_source_file: str) -> pd.DataFrame:
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
        "contact_gap_count",
        "why_not_top_tier",
        "rank_bucket",
        "rank_bucket_reason",
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
        "factual_summary",
        "hotel_opening_hours",
        "hotel_opening_hours_status",
        "checkin_checkout_info",
        "checkin_checkout_status",
        "rooms_range",
        "room_count_value",
        "room_count_status",
        "review_signal_summary",
        "ownership_status",
        "business_interest_summary",
        "why_commercially_interesting",
        "property_positioning_summary",
        "main_bottleneck_hypothesis",
        "pain_point_hypothesis",
        "best_entry_angle",
        "personalization_angle_1",
        "recommended_hook",
        "recommended_first_contact_route",
        "likely_decision_maker_hypothesis",
        "service_complexity_read",
        "commercial_complexity_read",
        "direct_booking_friction_hypothesis",
        "contact_route_friction_hypothesis",
        "call_hypothesis",
        "commercial_verdict",
        "ranking_score_final",
        "priority_level_final",
        "rank_bucket_final",
        "ranking_refresh_reason",
        "ranking_upside_reasons",
        "ranking_downside_reasons",
        "ranking_missingness_notes",
        "decision_status",
        "manual_review_needed",
        "review_queue_reason_codes",
    ]:
        ensure_column(emails, column, "")

    source_batch_stem = build_source_batch_stem(enrichment_source_file)
    ranked_lookup = load_ranked_lookup(enrichment_source_file)
    structured_context = emails.apply(
        lambda row: pd.Series(build_row_artifact_context(row, source_batch_stem, ranked_lookup)),
        axis=1,
    )
    for column in structured_context.columns:
        if column not in emails.columns:
            emails[column] = ""
        emails[column] = structured_context[column].where(
            structured_context[column].fillna("").astype(str).str.strip().ne(""),
            emails[column],
        )

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
    emails["contact_gap_count"] = emails.apply(fallback_contact_gap_count, axis=1)
    emails["rank_bucket_reason"] = emails.apply(fallback_rank_bucket_reason, axis=1)
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
            "ranking_score_final",
            "priority_level_final",
            "rank_bucket_final",
            "ranking_refresh_reason",
            "ranking_upside_reasons",
            "ranking_downside_reasons",
            "ranking_missingness_notes",
            "decision_status",
            "manual_review_needed",
            "review_queue_reason_codes",
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
            "ownership_status",
            "direct_booking_weakness",
            "ota_dependency_signal_label",
            "dedupe_status",
            "duplicate_group_id",
            "contact_duplicate_flag",
            "manual_merge_candidate",
            "active_icp_profile",
            "factual_summary",
            "hotel_opening_hours",
            "hotel_opening_hours_status",
            "checkin_checkout_info",
            "checkin_checkout_status",
            "review_signal_summary",
            "rooms_range",
            "room_count_value",
            "room_count_status",
            "business_interest_summary",
            "why_commercially_interesting",
            "property_positioning_summary",
            "main_bottleneck_hypothesis",
            "pain_point_hypothesis",
            "best_entry_angle",
            "recommended_hook",
            "recommended_first_contact_route",
            "likely_decision_maker_hypothesis",
            "service_complexity_read",
            "commercial_complexity_read",
            "direct_booking_friction_hypothesis",
            "contact_route_friction_hypothesis",
            "call_hypothesis",
            "commercial_verdict",
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

    preferred_enrichment_file = normalize_text(os.getenv("EMAIL_ENRICHMENT_SOURCE_FILE"))
    first_file = enriched_files[-1]
    if preferred_enrichment_file:
        for candidate in enriched_files:
            if candidate.name == preferred_enrichment_file:
                first_file = candidate
                break

    try:
        enriched_df = pd.read_csv(first_file)
    except Exception as error:
        print(f"Nepodarilo sa načítať enrichment CSV súbor: {first_file.name}")
        print(f"Dôvod: {error}")
        return

    email_df = build_email_dataframe(enriched_df, first_file.name)
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
                "business_interest_summary",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
