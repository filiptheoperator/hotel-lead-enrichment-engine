import hashlib
import json
import os
from pathlib import Path
from typing import Optional

import pandas as pd


PROCESSED_DIR = Path("data/processed")
MASTER_DIR = Path("outputs/master")
EMAIL_DIR = Path("outputs/email_drafts")
SOURCE_BUNDLE_DIR = Path("outputs/source_bundles")
FACTUAL_ENRICHMENT_DIR = Path("outputs/factual_enrichment")
COMMERCIAL_SYNTHESIS_DIR = Path("outputs/commercial_synthesis")
RANKED_DIR = Path("outputs/ranked")
MARKDOWN_DIR = Path("outputs/hotel_markdown")
UNKNOWN_VALUE_LABEL = "Verejne nepotvrdené"
DEFAULT_MODE = "batch"
SUPPORTED_MODES = {"single", "batch", "shortlist", "review_queue", "top_export", "all"}
SUPPORTED_TEMPLATES = {"operator_brief", "old_template_full"}


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def collapse_whitespace(value: object) -> str:
    return " ".join(normalize_text(value).split())


def truncate_text(value: object, max_len: int = 160) -> str:
    text = collapse_whitespace(value)
    if len(text) <= max_len:
        return text
    return text[: max_len - 1].rstrip(" ,;:-") + "…"


def list_processed_files() -> list[Path]:
    return sorted(PROCESSED_DIR.glob("*_normalized_scored.csv"), key=lambda path: path.stat().st_mtime)


def build_source_batch_stem(value: str) -> str:
    stem = Path(normalize_text(value)).stem
    for marker in [
        "_normalized_scored_enriched",
        "_normalized_scored",
        "_enriched",
        "_ranking_refreshed",
        "_email_drafts",
    ]:
        if marker in stem:
            return stem.split(marker, 1)[0]
    return stem


def build_account_id(row: pd.Series) -> str:
    account_id = normalize_text(row.get("account_id"))
    if account_id:
        return account_id
    raw = "|".join(
        [
            normalize_text(row.get("hotel_name_normalized")).lower(),
            normalize_text(row.get("city")).lower(),
            normalize_text(row.get("website_domain")).lower(),
            normalize_text(row.get("source_file")).lower(),
        ]
    )
    digest = hashlib.md5(raw.encode("utf-8")).hexdigest()[:12]
    return f"acc_{digest}"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def load_csv(path: Optional[Path]) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    for column in df.columns:
        if df[column].dtype == object:
            df[column] = df[column].apply(normalize_text)
    return df


def get_latest_file(folder: Path, pattern: str) -> Optional[Path]:
    files = sorted(folder.glob(pattern), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def get_ranked_file_for_processed(processed_file_name: str) -> Optional[Path]:
    preferred_ranked_file = normalize_text(os.getenv("MARKDOWN_RANKED_SOURCE_FILE"))
    if preferred_ranked_file:
        ranked_path = RANKED_DIR / preferred_ranked_file
        if ranked_path.exists():
            return ranked_path

    processed_stem = Path(processed_file_name).stem
    matches = sorted(
        RANKED_DIR.glob(f"{processed_stem}_enriched*_ranking_refreshed*.csv"),
        key=lambda path: path.stat().st_mtime,
    )
    if matches:
        return matches[-1]
    return get_latest_file(RANKED_DIR, "*_ranking_refreshed*.csv")


def get_email_file_for_ranked(ranked_path: Optional[Path]) -> Optional[Path]:
    preferred = normalize_text(os.getenv("MARKDOWN_EMAIL_SOURCE_FILE"))
    if preferred:
        candidate = EMAIL_DIR / preferred
        if candidate.exists():
            return candidate
    if ranked_path is not None:
        batch_stem = build_source_batch_stem(ranked_path.name)
        matches = sorted(
            EMAIL_DIR.glob(f"{batch_stem}_normalized_scored_enriched*_email_drafts.csv"),
            key=lambda path: path.stat().st_mtime,
        )
        if matches:
            return matches[-1]
        direct = EMAIL_DIR / f"{Path(ranked_path.name).stem.replace('_ranking_refreshed', '')}_email_drafts.csv"
        if direct.exists():
            return direct
    return get_latest_file(EMAIL_DIR, "*_email_drafts.csv")


def get_master_file(kind: str) -> Optional[Path]:
    env_key = {
        "shortlist": "MARKDOWN_OPERATOR_SHORTLIST_FILE",
        "review_queue": "MARKDOWN_REVIEW_QUEUE_FILE",
        "top_export": "MARKDOWN_TOP_EXPORT_FILE",
    }.get(kind, "")
    preferred = normalize_text(os.getenv(env_key)) if env_key else ""
    if preferred:
        candidate = MASTER_DIR / preferred
        if candidate.exists():
            return candidate
    patterns = {
        "shortlist": "*_operator_shortlist*.csv",
        "review_queue": "*_review_queue*.csv",
        "top_export": "*_top_20_export*.csv",
    }
    return get_latest_file(MASTER_DIR, patterns[kind])


def build_status_suffix(status: str) -> str:
    normalized = normalize_text(status)
    return f" [{normalized}]" if normalized else ""


def filter_rows_by_decision(rows: pd.DataFrame, decision_status: str) -> pd.DataFrame:
    if rows.empty or "decision_status" not in rows.columns:
        return rows.copy()
    mask = rows["decision_status"].fillna("").astype(str).str.strip().eq(decision_status)
    return rows[mask].copy()


def build_summary_frames(
    ranked_df: pd.DataFrame,
    shortlist_df: pd.DataFrame,
    review_queue_df: pd.DataFrame,
    top_export_df: pd.DataFrame,
) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    shortlist_rows = filter_rows_by_decision(shortlist_df, "outreach_now")
    if shortlist_rows.empty:
        shortlist_rows = filter_rows_by_decision(ranked_df, "outreach_now")

    review_rows = filter_rows_by_decision(review_queue_df, "manual_review")
    if review_rows.empty:
        review_rows = filter_rows_by_decision(ranked_df, "manual_review")

    if top_export_df.empty:
        top_rows = shortlist_rows.head(20).copy()
    else:
        top_rows = top_export_df.copy()

    return shortlist_rows, review_rows, top_rows


def format_fact_line(label: str, value: object, status: str = "", max_len: int = 180) -> str:
    text = collapse_whitespace(value) or UNKNOWN_VALUE_LABEL
    return f"- {label}: {truncate_text(text, max_len=max_len)}{build_status_suffix(status)}"


def format_list_block(items: list[str], fallback: str = UNKNOWN_VALUE_LABEL, max_len: int = 140) -> list[str]:
    values = [truncate_text(item, max_len=max_len) for item in items if collapse_whitespace(item)]
    if not values:
        return [f"- {fallback}"]
    return [f"- {value}" for value in values]


def collect_service_mix_lines(service_mix: dict) -> list[str]:
    lines: list[str] = []
    for key, payload in service_mix.items():
        availability = normalize_text(payload.get("available"))
        if availability in {"yes", "unknown"}:
            evidence = truncate_text(payload.get("evidence"), max_len=120) or UNKNOWN_VALUE_LABEL
            origin = normalize_text(payload.get("source_origin"))
            label = key.replace("_", " ")
            suffix = f" ({origin})" if origin else ""
            lines.append(f"{label}: {availability}{suffix} | {evidence}")
    return lines


def collect_source_urls(source_bundle: dict) -> list[str]:
    urls: list[str] = []
    google_maps_url = normalize_text(source_bundle.get("sources", {}).get("google_places", {}).get("google_maps_url"))
    if google_maps_url:
        urls.append(f"Google Maps: {google_maps_url}")
    official = source_bundle.get("sources", {}).get("official_website", {})
    base_url = normalize_text(official.get("base_url"))
    if base_url:
        urls.append(f"Official website: {base_url}")
    for page in official.get("pages", []):
        url = normalize_text(page.get("url"))
        source_type = normalize_text(page.get("source_type"))
        if url:
            urls.append(f"{source_type or 'page'}: {url}")
    unique_urls: list[str] = []
    for item in urls:
        if item not in unique_urls:
            unique_urls.append(item)
    return unique_urls


def collect_verified_lines(factual: dict) -> list[str]:
    lines: list[str] = []
    operating = factual.get("operating_hours", {})
    checkin = factual.get("checkin_checkout", {})
    room_signal = factual.get("room_count_signal", {})
    ownership = factual.get("ownership_company_signal", {})
    if normalize_text(operating.get("status")) == "Overené vo verejnom zdroji":
        lines.append(f"Operating hours: {normalize_text(operating.get('hotel_opening_hours'))}")
    if normalize_text(checkin.get("status")) == "Overené vo verejnom zdroji":
        lines.append(f"Check-in / check-out: {normalize_text(checkin.get('value'))}")
    if normalize_text(room_signal.get("status")) == "public_confirmed":
        lines.append(f"Room signal: {normalize_text(room_signal.get('value'))} / {normalize_text(room_signal.get('rooms_range'))}")
    if normalize_text(ownership.get("status")) == "public_confirmed":
        lines.append(f"Ownership: {normalize_text(ownership.get('value'))}")
    return lines


def collect_raw_lines(factual: dict) -> list[str]:
    lines: list[str] = []
    review_signal = factual.get("review_trust_signal", {})
    ownership = factual.get("ownership_company_signal", {})
    if normalize_text(review_signal.get("status")) == "raw_confirmed":
        lines.append(f"Review signal: {normalize_text(review_signal.get('summary'))}")
    if normalize_text(ownership.get("status")) == "raw_confirmed":
        lines.append(f"Ownership: {normalize_text(ownership.get('value'))}")
    return lines


def build_operator_action(row: dict) -> tuple[str, list[str], list[str]]:
    decision_status = normalize_text(row.get("decision_status"))
    review_reason_codes = [
        part.strip()
        for part in normalize_text(row.get("review_queue_reason_codes")).split("|")
        if part.strip()
    ]
    if decision_status == "outreach_now":
        return (
            "Poslať first outreach.",
            [],
            [
                "Neeskalovať manuálne, ak sa neobjaví nový konflikt v dátach.",
                "Neriešiť teraz polia označené ako Verejne nepotvrdené, ak neblokujú prvý kontakt.",
            ],
        )
    if decision_status == "manual_review":
        verify = []
        if "low_factual_completeness" in review_reason_codes:
            verify.append("Doplniť chýbajúce praktické údaje z verejných zdrojov.")
        if "ambiguous_commercial_hook" in review_reason_codes:
            verify.append("Sprísniť alebo prepísať hook na konkrétny factual angle.")
        if "high_uncertainty" in review_reason_codes:
            verify.append("Skontrolovať uncertainty notes a oddeliť neisté tvrdenia od faktov.")
        if "cautious_verdict" in review_reason_codes:
            verify.append("Overiť, či je opatrný verdict stále opodstatnený pred outreachom.")
        return (
            "Urobiť krátky manuálny review pred outreachom.",
            verify or ["Skontrolovať ranked reasons a factual missingness."],
            ["Neposielať outreach automaticky bez krátkeho review."],
        )
    return (
        "Držať lead v hold_later.",
        ["Skontrolovať neskôr po doplnení faktov alebo po zmene scoring policy."],
        ["Neriešiť teraz outreach ani manuálny deep review."],
    )


def build_header_section(row: dict) -> list[str]:
    return [
        f"# {normalize_text(row.get('hotel_name')) or 'Hotel'}",
        "",
        format_fact_line("Account ID", row.get("account_id")),
        format_fact_line("Mesto / krajina", f"{normalize_text(row.get('city'))} / {normalize_text(row.get('country_code'))}".strip(" /")),
        format_fact_line("Final priority", row.get("priority_level_final")),
        format_fact_line("Decision status", row.get("decision_status")),
    ]


def build_natural_hotel_label(identity: dict, commercial: dict) -> str:
    return (
        normalize_text(commercial.get("property_positioning_summary"))
        or normalize_text(identity.get("category_name"))
        or normalize_text(identity.get("hotel_type_class"))
        or UNKNOWN_VALUE_LABEL
    )


def build_old_template_markdown(row: dict, source_bundle: dict, factual: dict, commercial: dict, email_row: dict) -> str:
    identity = factual.get("identity", {})
    contacts = factual.get("contacts", {})
    address = factual.get("address", {})
    operating = factual.get("operating_hours", {})
    checkin = factual.get("checkin_checkout", {})
    room_signal = factual.get("room_count_signal", {})
    star_signal = factual.get("star_signal", {})
    service_mix = factual.get("service_mix", {})
    review_signal = factual.get("review_trust_signal", {})
    ownership = factual.get("ownership_company_signal", {})
    uncertainty_notes = commercial.get("uncertainty_notes", []) or []
    missingness_notes = [part.strip() for part in normalize_text(row.get("ranking_missingness_notes")).split("|") if part.strip()]
    review_queue_reasons = [part.strip() for part in normalize_text(row.get("review_queue_reason_codes")).split("|") if part.strip()]
    operator_action, verify_list, _ = build_operator_action(row)

    lines: list[str] = []
    lines.extend(build_header_section(row))
    lines.extend(
        [
            "",
            "## Základný profil hotela",
            format_fact_line("Property positioning", build_natural_hotel_label(identity, commercial), max_len=220),
            format_fact_line("Typ hotela", identity.get("category_name")),
            format_fact_line("Hviezdy", star_signal.get("value"), star_signal.get("status")),
            format_fact_line("Room signal", f"{normalize_text(room_signal.get('value'))} / {normalize_text(room_signal.get('rooms_range'))}".strip(" /"), room_signal.get("status")),
            format_fact_line("Owner / company", ownership.get("value"), ownership.get("status")),
            "",
            "## Kontaktné údaje",
            format_fact_line("Web", contacts.get("website")),
            format_fact_line("Phone", contacts.get("phone")),
            format_fact_line("Adresa", address.get("formatted")),
            format_fact_line("Odporúčaný prvý kontakt", commercial.get("recommended_first_contact_route")),
            format_fact_line("Likely decision maker", commercial.get("likely_decision_maker_hypothesis")),
            "",
            "## Prevádzkové hodiny a dôležité časy",
            format_fact_line("Opening hours", operating.get("hotel_opening_hours"), operating.get("status"), max_len=220),
            format_fact_line("Check-in / check-out", checkin.get("value"), checkin.get("status")),
            "",
            "## Čo je na hoteli obchodne zaujímavé",
            format_fact_line("Commercial summary", commercial.get("business_interest_summary"), max_len=220),
            format_fact_line("Why commercially interesting", commercial.get("why_commercially_interesting"), max_len=240),
            format_fact_line("Service complexity", commercial.get("service_complexity_read"), max_len=220),
            format_fact_line("Commercial complexity", commercial.get("commercial_complexity_read"), max_len=220),
            "",
            "- Demand mix hypothesis:",
        ]
    )
    lines.extend(format_list_block(commercial.get("demand_mix_hypothesis", []) or [], max_len=180))
    lines.extend(
        [
            "",
            "## Dôvera a recenzie",
            format_fact_line("Review signal", review_signal.get("summary"), review_signal.get("status")),
            "",
            "## Rýchle zhodnotenie",
            "- Silné stránky:",
        ]
    )
    lines.extend(format_list_block(commercial.get("strengths", []) or [], max_len=180))
    lines.extend(["", "- Priestor / gaps:"])
    lines.extend(format_list_block(commercial.get("opportunity_gaps", []) or [], max_len=180))
    lines.extend(
        [
            "",
            format_fact_line("Main bottleneck", commercial.get("main_bottleneck_hypothesis"), max_len=220),
            format_fact_line("Pain point", commercial.get("pain_point_hypothesis"), max_len=220),
            format_fact_line("Direct booking friction", commercial.get("direct_booking_friction_hypothesis"), max_len=220),
            format_fact_line("Contact route friction", commercial.get("contact_route_friction_hypothesis"), max_len=220),
            "",
            "## Personalizačné uhly",
        ]
    )
    lines.extend(format_list_block(commercial.get("personalization_angles", []) or [], max_len=180))
    lines.extend(
        [
            "",
            "## Odporúčaný háčik",
            format_fact_line("Best entry angle", commercial.get("best_entry_angle"), max_len=220),
            format_fact_line("Recommended hook", commercial.get("recommended_hook"), max_len=220),
            "",
            "## Návrh prvého e-mailu",
            format_fact_line("Subject", email_row.get("subject_line")),
            format_fact_line("Give first line", email_row.get("give_first_line"), max_len=220),
            format_fact_line("Relevance line", email_row.get("relevance_line"), max_len=220),
            format_fact_line("CTA", email_row.get("low_friction_cta"), max_len=200),
            "",
            "## Návrh následného e-mailu",
            format_fact_line("Follow-up", email_row.get("followup_email"), max_len=260),
            "",
            "## Hypotéza na krátky úvodný rozhovor",
            format_fact_line("Call hypothesis", commercial.get("call_hypothesis"), max_len=220),
            "",
            "## Verdikt",
            format_fact_line("Verdict", commercial.get("verdict")),
            format_fact_line("Decision status", row.get("decision_status")),
            format_fact_line("Ranking reason", row.get("ranking_refresh_reason"), max_len=220),
            format_fact_line("Recommended operator action", operator_action),
            "",
            "## Neistoty a čo treba overiť",
            "- Uncertainty notes:",
        ]
    )
    lines.extend(format_list_block(uncertainty_notes, max_len=180))
    lines.extend(["", "- Missingness notes:"])
    lines.extend(format_list_block(missingness_notes))
    lines.extend(["", "- Review queue reasons:"])
    lines.extend(format_list_block(review_queue_reasons))
    lines.extend(["", "- Manuálne overiť:"])
    lines.extend(format_list_block(verify_list, fallback="Nič kritické navyše."))
    lines.extend(["", "- Source URLs:"])
    lines.extend(format_list_block(collect_source_urls(source_bundle), max_len=220))
    return "\n".join(lines).strip() + "\n"


def build_operator_brief_markdown(row: dict, source_bundle: dict, factual: dict, commercial: dict, email_row: dict) -> str:
    identity = factual.get("identity", {})
    contacts = factual.get("contacts", {})
    address = factual.get("address", {})
    operating = factual.get("operating_hours", {})
    checkin = factual.get("checkin_checkout", {})
    room_signal = factual.get("room_count_signal", {})
    star_signal = factual.get("star_signal", {})
    service_mix = factual.get("service_mix", {})
    review_signal = factual.get("review_trust_signal", {})
    ownership = factual.get("ownership_company_signal", {})

    verified_lines = collect_verified_lines(factual)
    raw_lines = collect_raw_lines(factual)
    source_urls = collect_source_urls(source_bundle)
    uncertainty_notes = commercial.get("uncertainty_notes", []) or []
    missingness_notes = [
        part.strip()
        for part in normalize_text(row.get("ranking_missingness_notes")).split("|")
        if part.strip()
    ]
    review_queue_reasons = [
        part.strip()
        for part in normalize_text(row.get("review_queue_reason_codes")).split("|")
        if part.strip()
    ]
    operator_action, verify_list, ignore_list = build_operator_action(row)

    lines: list[str] = []
    lines.extend(build_header_section(row))
    lines.extend(
        [
            "",
            "## Executive Summary",
            format_fact_line("Commercial summary", commercial.get("business_interest_summary")),
            format_fact_line("Verdict", commercial.get("verdict")),
            format_fact_line("Main bottleneck", commercial.get("main_bottleneck_hypothesis")),
            "",
            "## Decision Block",
            format_fact_line("Decision", row.get("decision_status")),
            format_fact_line("Why", row.get("ranking_refresh_reason")),
            format_fact_line("Score up", row.get("ranking_upside_reasons")),
            format_fact_line("Score down", row.get("ranking_downside_reasons")),
            format_fact_line("Ranking score final", row.get("ranking_score_final")),
            format_fact_line("Rank bucket final", row.get("rank_bucket_final")),
            "",
            "## Factual Block",
            format_fact_line("Hotel", identity.get("hotel_name")),
            format_fact_line("Hotel type", identity.get("hotel_type_class")),
            format_fact_line("Category", identity.get("category_name")),
            format_fact_line("Website", contacts.get("website")),
            format_fact_line("Phone", contacts.get("phone")),
            format_fact_line("Address", address.get("formatted")),
            format_fact_line("Opening hours", operating.get("hotel_opening_hours"), operating.get("status")),
            format_fact_line("Check-in / check-out", checkin.get("value"), checkin.get("status")),
            format_fact_line("Room signal", f"{normalize_text(room_signal.get('value'))} / {normalize_text(room_signal.get('rooms_range'))}".strip(" /"), room_signal.get("status")),
            format_fact_line("Star signal", star_signal.get("value"), star_signal.get("status")),
            format_fact_line("Review signal", review_signal.get("summary"), review_signal.get("status")),
            format_fact_line("Ownership signal", ownership.get("value"), ownership.get("status")),
            "",
            "- Service mix:",
        ]
    )
    lines.extend(format_list_block(collect_service_mix_lines(service_mix), max_len=140))
    lines.extend(
        [
            "",
            "## Evidence Block",
            "- Source URLs:",
        ]
    )
    lines.extend(format_list_block(source_urls, max_len=220))
    lines.extend(["", "- Verified facts:"])
    lines.extend(format_list_block(verified_lines))
    lines.extend(["", "- Raw confirmed facts:"])
    lines.extend(format_list_block(raw_lines))
    lines.extend(
        [
            "",
            "## Uncertainty Block",
            "- Uncertainty notes:",
        ]
    )
    lines.extend(format_list_block([truncate_text(item, 140) for item in uncertainty_notes]))
    lines.extend(["", "- Missingness notes:"])
    lines.extend(format_list_block(missingness_notes))
    lines.extend(["", "- Review queue reasons:"])
    lines.extend(format_list_block(review_queue_reasons))
    lines.extend(
        [
            "",
            "## Outreach Block",
            format_fact_line("Subject", email_row.get("subject_line")),
            format_fact_line("Give first line", email_row.get("give_first_line"), max_len=180),
            format_fact_line("Relevance line", email_row.get("relevance_line"), max_len=180),
            format_fact_line("CTA", email_row.get("low_friction_cta"), max_len=160),
            "",
            "## Operator Action Block",
            format_fact_line("Recommended action", operator_action),
            "- Čo treba manuálne overiť:",
        ]
    )
    lines.extend(format_list_block(verify_list, fallback="Nič kritické navyše."))
    lines.extend(["", "- Čo netreba riešiť teraz:"])
    lines.extend(format_list_block(ignore_list, fallback="Bez ďalších výnimiek."))
    return "\n".join(lines).strip() + "\n"


def build_markdown(row: dict, source_bundle: dict, factual: dict, commercial: dict, email_row: dict, template_mode: str) -> str:
    if template_mode == "old_template_full":
        return build_old_template_markdown(row, source_bundle, factual, commercial, email_row)
    return build_operator_brief_markdown(row, source_bundle, factual, commercial, email_row)


def build_summary_markdown(title: str, rows: pd.DataFrame) -> str:
    lines = [f"# {title}", ""]
    if rows.empty:
        lines.append("- Bez riadkov.")
        return "\n".join(lines) + "\n"
    for _, row in rows.iterrows():
        top_reason = (
            normalize_text(row.get("best_entry_angle"))
            or normalize_text(row.get("why_commercially_interesting"))
            or normalize_text(row.get("ranking_upside_reasons"))
            or normalize_text(row.get("review_queue_reason_codes"))
            or normalize_text(row.get("ranking_refresh_reason"))
        )
        operator_action, _, _ = build_operator_action(row.to_dict())
        lines.extend(
            [
                f"## {normalize_text(row.get('hotel_name'))}",
                format_fact_line("Final score", row.get("ranking_score_final")),
                format_fact_line("Decision status", row.get("decision_status")),
                format_fact_line("Commercial verdict", row.get("commercial_verdict")),
                format_fact_line("Top reason", top_reason, max_len=180),
                format_fact_line("Operator next step", operator_action, max_len=180),
                "",
            ]
        )
    return "\n".join(lines).strip() + "\n"


def build_qa_report(rows: list[dict]) -> pd.DataFrame:
    records: list[dict] = []
    for item in rows:
        row = item["ranked_row"]
        commercial = item["commercial"]
        markdown = item["markdown"]
        records.append(
            {
                "account_id": normalize_text(row.get("account_id")),
                "hotel_name": normalize_text(row.get("hotel_name")),
                "decision_status": normalize_text(row.get("decision_status")),
                "groundedness_check": "pass"
                if commercial.get("source_bundle_ref") and commercial.get("factual_enrichment_ref")
                else "fail",
                "decision_alignment_check": "pass"
                if normalize_text(row.get("decision_status")) in markdown
                else "fail",
                "uncertainty_check": "pass"
                if "## Uncertainty Block" in markdown or "## Neistoty a čo treba overiť" in markdown
                else "fail",
                "section_order_check": "pass"
                if (
                    ("## Executive Summary" in markdown and markdown.find("## Executive Summary") < markdown.find("## Decision Block") < markdown.find("## Factual Block") < markdown.find("## Outreach Block"))
                    or ("## Základný profil hotela" in markdown and markdown.find("## Základný profil hotela") < markdown.find("## Čo je na hoteli obchodne zaujímavé") < markdown.find("## Odporúčaný háčik") < markdown.find("## Verdikt"))
                )
                else "fail",
                "readability_check": "pass"
                if len(markdown.splitlines()) <= 120
                else "review",
            }
        )
    return pd.DataFrame(records)


def select_rows(
    mode: str,
    ranked_df: pd.DataFrame,
    shortlist_df: pd.DataFrame,
    review_queue_df: pd.DataFrame,
    top_export_df: pd.DataFrame,
) -> pd.DataFrame:
    account_id = normalize_text(os.getenv("MARKDOWN_ACCOUNT_ID"))
    batch_limit_raw = normalize_text(os.getenv("MARKDOWN_BATCH_LIMIT"))
    try:
        batch_limit = int(batch_limit_raw) if batch_limit_raw else 0
    except ValueError:
        batch_limit = 0

    selected = ranked_df.copy()
    if mode == "single" and account_id:
        selected = ranked_df[ranked_df["account_id"].fillna("").astype(str).str.strip().eq(account_id)].copy()
    elif mode == "shortlist":
        selected = shortlist_df.copy()
    elif mode == "review_queue":
        selected = review_queue_df.copy()
    elif mode == "top_export":
        selected = top_export_df.copy()
    elif mode in {"batch", "all"}:
        selected = ranked_df.copy()

    if batch_limit > 0 and mode in {"batch", "all", "shortlist", "review_queue", "top_export"}:
        selected = selected.head(batch_limit).copy()
    return selected


def main() -> None:
    processed_files = list_processed_files()
    if not processed_files:
        print("Chýba processed CSV pre markdown renderer.")
        return

    preferred_source_file = normalize_text(os.getenv("MARKDOWN_SOURCE_FILE"))
    processed_path = processed_files[-1]
    if preferred_source_file:
        for candidate in processed_files:
            if candidate.name == preferred_source_file:
                processed_path = candidate
                break

    mode = normalize_text(os.getenv("MARKDOWN_MODE")).lower() or DEFAULT_MODE
    if mode not in SUPPORTED_MODES:
        mode = DEFAULT_MODE
    template_mode = normalize_text(os.getenv("MARKDOWN_TEMPLATE")).lower() or "operator_brief"
    if template_mode not in SUPPORTED_TEMPLATES:
        template_mode = "operator_brief"

    ranked_path = get_ranked_file_for_processed(processed_path.name)
    ranked_df = load_csv(ranked_path)
    if ranked_df.empty:
        print("Chýba ranked CSV pre renderer.")
        return

    email_df = load_csv(get_email_file_for_ranked(ranked_path))
    email_lookup = {
        normalize_text(row["account_id"]): row.to_dict()
        for _, row in email_df.iterrows()
        if normalize_text(row.get("account_id"))
    }

    shortlist_df = load_csv(get_master_file("shortlist"))
    review_queue_df = load_csv(get_master_file("review_queue"))
    top_export_df = load_csv(get_master_file("top_export"))
    shortlist_summary_df, review_summary_df, top_summary_df = build_summary_frames(
        ranked_df=ranked_df,
        shortlist_df=shortlist_df,
        review_queue_df=review_queue_df,
        top_export_df=top_export_df,
    )

    selected_df = select_rows(mode, ranked_df, shortlist_summary_df, review_summary_df, top_summary_df)
    if selected_df.empty:
        print("Renderer nenašiel žiadne riadky pre zvolený mód.")
        return

    source_file_stem = build_source_batch_stem(processed_path.name)
    output_dir = MARKDOWN_DIR / source_file_stem
    output_dir.mkdir(parents=True, exist_ok=True)

    rendered_rows: list[dict] = []
    for _, row in selected_df.iterrows():
        row_dict = row.to_dict()
        account_id = normalize_text(row_dict.get("account_id")) or build_account_id(pd.Series(row_dict))
        source_bundle = load_json(SOURCE_BUNDLE_DIR / source_file_stem / f"{account_id}.json")
        factual = load_json(FACTUAL_ENRICHMENT_DIR / source_file_stem / f"{account_id}.json")
        commercial = load_json(COMMERCIAL_SYNTHESIS_DIR / source_file_stem / f"{account_id}.json")
        if not source_bundle or not factual or not commercial:
            continue
        email_row = email_lookup.get(account_id, {})
        markdown = build_markdown(row_dict, source_bundle, factual, commercial, email_row, template_mode=template_mode)
        output_path = output_dir / f"{account_id}.md"
        output_path.write_text(markdown, encoding="utf-8")
        rendered_rows.append(
            {
                "ranked_row": row_dict,
                "source_bundle": source_bundle,
                "factual": factual,
                "commercial": commercial,
                "email_row": email_row,
                "markdown": markdown,
                "output_path": output_path,
            }
        )

    shortlist_summary = build_summary_markdown("Operator Shortlist Summary", shortlist_summary_df)
    (output_dir / "operator_shortlist_summary.md").write_text(shortlist_summary, encoding="utf-8")
    review_summary = build_summary_markdown("Review Queue Summary", review_summary_df)
    (output_dir / "review_queue_summary.md").write_text(review_summary, encoding="utf-8")
    executive_summary = build_summary_markdown("Top Export Summary", top_summary_df)
    (output_dir / "top_export_summary.md").write_text(executive_summary, encoding="utf-8")

    qa_df = build_qa_report(rendered_rows)
    qa_path = output_dir / "wave5_render_qa_report.csv"
    qa_df.to_csv(qa_path, index=False)

    print(f"Processed source: {processed_path.name}")
    print(f"Mode: {mode}")
    print(f"Template: {template_mode}")
    print(f"Rendered markdown count: {len(rendered_rows)}")
    print(f"Output dir: {output_dir}")
    print(f"QA report: {qa_path}")
    print(f"Shortlist summary: {output_dir / 'operator_shortlist_summary.md'}")
    print(f"Review summary: {output_dir / 'review_queue_summary.md'}")


if __name__ == "__main__":
    main()
