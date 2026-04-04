from pathlib import Path
import html
import json
import re
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
import yaml


PROCESSED_DIR = Path("data/processed")
ENRICHMENT_OUTPUT_DIR = Path("outputs/enrichment")
ENRICHMENT_CONFIG_PATH = Path("configs/enrichment.yaml")
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; HotelLeadEnrichmentEngine/1.0; "
        "+https://github.com/filiptheoperator/hotel-lead-enrichment-engine)"
    )
}


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


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def html_to_text(value: str) -> str:
    without_scripts = re.sub(
        r"<script[^>]*>.*?</script>",
        " ",
        value,
        flags=re.IGNORECASE | re.DOTALL,
    )
    without_styles = re.sub(
        r"<style[^>]*>.*?</style>",
        " ",
        without_scripts,
        flags=re.IGNORECASE | re.DOTALL,
    )
    without_tags = re.sub(r"<[^>]+>", " ", without_styles)
    return normalize_whitespace(html.unescape(without_tags))


def normalize_time_value(value: str) -> str:
    value = value.replace(".", ":").strip()
    match = re.fullmatch(r"(\d{1,2}):(\d{2})", value)
    if not match:
        return ""

    hours = int(match.group(1))
    minutes = int(match.group(2))
    if hours > 23 or minutes > 59:
        return ""

    return f"{hours:02d}:{minutes:02d}"


def cleanup_opening_hours_value(value: str) -> str:
    value = html_to_text(value)
    value = value.replace("–", "-")
    value = normalize_whitespace(value)
    value = re.sub(
        r"^(otváracie hodiny(?: recepcie)?[:\s-]*){2,}",
        "Otváracie hodiny: ",
        value,
        flags=re.IGNORECASE,
    )
    value = re.sub(
        r"^(opening hours[:\s-]*){2,}",
        "Opening hours: ",
        value,
        flags=re.IGNORECASE,
    )

    cleanup_markers = [
        "check-in",
        "check in",
        "check-out",
        "check out",
        "breakfast",
        "continental breakfast",
        "možnosť parkovania",
        "moznost parkovania",
        "parkovanie",
        "príchod",
        "prichod",
        "odchod",
        "rezervácie",
        "rezervacia",
        "pre rezerváciu",
        "pre rezervaciu",
        "copyright",
        "created by",
        "learn more",
        "meta",
        "galéria",
        "galeria",
        "služby",
        "sluzby",
        "viac informácií",
        "viac informacii",
        "podmienky",
    ]

    lowered = value.lower()
    cut_positions = [lowered.find(marker) for marker in cleanup_markers if lowered.find(marker) != -1]
    if cut_positions:
        value = value[: min(cut_positions)].strip(" ,;:-")

    value = re.sub(r"\s{2,}", " ", value)
    return value[:180].strip(" ,;:-")


def is_likely_accommodation_lead(row: pd.Series) -> bool:
    category_name = normalize_text(row.get("category_name")).lower()
    all_categories = normalize_text(row.get("all_categories")).lower()
    hotel_name = normalize_text(row.get("hotel_name")).lower()
    category_context = " ".join([category_name, all_categories, hotel_name])

    accommodation_markers = [
        "hotel",
        "hostel",
        "penzion",
        "pension",
        "ubyt",
        "apartm",
        "residence",
        "residenc",
        "guesthouse",
        "boutique",
        "garni",
        "botel",
    ]
    return any(marker in category_context for marker in accommodation_markers)


def is_likely_hotel_opening_hours(row: pd.Series, value: str, source_url: str) -> bool:
    cleaned = normalize_text(value)
    if not cleaned:
        return False
    if not is_likely_accommodation_lead(row):
        return False

    lowered = cleaned.lower()
    source_lowered = normalize_text(source_url).lower()

    allowed_markers = [
        "hotel",
        "recepcia",
        "reception",
        "front desk",
        "24/7",
        "nonstop",
    ]
    excluded_markers = [
        "wellness",
        "spa",
        "restaurant",
        "reštaur",
        "restaurac",
        "kaviareň",
        "kaviaren",
        "fitness",
        "squash",
        "sauna",
        "bar",
        "massage",
        "masáž",
        "masaz",
    ]

    has_allowed_marker = any(marker in lowered for marker in allowed_markers)
    has_excluded_marker = any(marker in lowered for marker in excluded_markers)
    source_is_excluded = any(marker in source_lowered for marker in excluded_markers)
    has_time_signal = bool(re.search(r"\b\d{1,2}[:.]\d{2}\b", lowered)) or "24/7" in lowered

    if has_excluded_marker and not has_allowed_marker:
        return False
    if source_is_excluded and not has_allowed_marker:
        return False
    if has_allowed_marker and has_time_signal:
        return True

    parsed_source = urlparse(source_url)
    source_path = parsed_source.path.strip("/")
    source_is_homepage = not source_path

    if source_is_homepage and has_time_signal and not has_excluded_marker:
        return True

    return False


def extract_opening_hours_window(text: str, start_index: int) -> str:
    plain_text = html_to_text(text)
    window = plain_text[start_index : start_index + 320]
    split_markers = [
        " check-in",
        " check in",
        " check-out",
        " check out",
        " breakfast",
        " continental breakfast",
        " možnosť parkovania",
        " moznost parkovania",
        " parkovanie",
        " rezervácie",
        " rezervacia",
        " pre rezerváciu",
        " pre rezervaciu",
        " copyright",
        " created by",
        " learn more",
        " meta",
        " galéria",
        " galeria",
        " služby",
        " sluzby",
        " viac informácií",
        " viac informacii",
        " podmienky",
    ]

    lowered = window.lower()
    cut_positions = [lowered.find(marker) for marker in split_markers if lowered.find(marker) != -1]
    if cut_positions:
        window = window[: min(cut_positions)]

    return cleanup_opening_hours_value(window)


def extract_first_present_value(row: pd.Series, candidate_columns: list[str]) -> str:
    for column in candidate_columns:
        if column in row.index:
            value = normalize_text(row.get(column))
            if value:
                return value
    return ""


def fetch_public_page(url: str, timeout_seconds: int) -> str:
    response = requests.get(
        url,
        timeout=timeout_seconds,
        headers=DEFAULT_HEADERS,
        allow_redirects=True,
    )
    response.raise_for_status()
    return response.text


def extract_same_domain_candidate_urls(
    base_url: str,
    html: str,
    keywords: list[str],
    max_pages: int,
) -> list[str]:
    parsed_base = urlparse(base_url)
    if not parsed_base.netloc:
        return []

    found_urls: list[str] = []
    seen: set[str] = set()

    for href in re.findall(r'href=["\']([^"\']+)["\']', html, flags=re.IGNORECASE):
        candidate_url = urljoin(base_url, href)
        parsed_candidate = urlparse(candidate_url)

        if parsed_candidate.scheme not in {"http", "https"}:
            continue
        if parsed_candidate.netloc != parsed_base.netloc:
            continue

        normalized_candidate = candidate_url.split("#", 1)[0]
        lower_candidate = normalized_candidate.lower()
        if not any(keyword in lower_candidate for keyword in keywords):
            continue
        if normalized_candidate in seen:
            continue

        seen.add(normalized_candidate)
        found_urls.append(normalized_candidate)

        if len(found_urls) >= max_pages:
            break

    return found_urls


def extract_json_ld_blocks(html: str) -> list[dict]:
    blocks: list[dict] = []
    matches = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )

    for match in matches:
        payload = normalize_text(match)
        if not payload:
            continue
        try:
            data = json.loads(payload)
        except json.JSONDecodeError:
            continue

        if isinstance(data, list):
            blocks.extend(item for item in data if isinstance(item, dict))
        elif isinstance(data, dict):
            blocks.append(data)

    return blocks


def iter_json_objects(data: object):
    if isinstance(data, dict):
        yield data
        for value in data.values():
            yield from iter_json_objects(value)
    elif isinstance(data, list):
        for item in data:
            yield from iter_json_objects(item)


def extract_opening_hours_from_json_ld(html: str) -> str:
    values: list[str] = []
    for block in extract_json_ld_blocks(html):
        for obj in iter_json_objects(block):
            opening_hours = obj.get("openingHours")
            if isinstance(opening_hours, list):
                hours = ", ".join(normalize_whitespace(str(item)) for item in opening_hours if normalize_text(item))
                if hours:
                    values.append(hours)
            elif normalize_text(opening_hours):
                values.append(normalize_whitespace(str(opening_hours)))

            specification = obj.get("openingHoursSpecification")
            if isinstance(specification, list):
                spec_parts: list[str] = []
                for item in specification:
                    if not isinstance(item, dict):
                        continue
                    days = item.get("dayOfWeek")
                    opens = normalize_text(item.get("opens"))
                    closes = normalize_text(item.get("closes"))

                    day_text = ""
                    if isinstance(days, list):
                        day_text = ", ".join(
                            normalize_text(str(day)).split("/")[-1] for day in days if normalize_text(day)
                        )
                    elif normalize_text(days):
                        day_text = normalize_text(str(days)).split("/")[-1]

                    time_text = ""
                    if opens and closes:
                        time_text = f"{opens}-{closes}"
                    elif opens:
                        time_text = f"od {opens}"
                    elif closes:
                        time_text = f"do {closes}"

                    if day_text and time_text:
                        spec_parts.append(f"{day_text}: {time_text}")
                    elif time_text:
                        spec_parts.append(time_text)

                if spec_parts:
                    values.append("; ".join(spec_parts))

    return cleanup_opening_hours_value(values[0]) if values else ""


def extract_checkin_checkout_from_json_ld(html: str) -> str:
    for block in extract_json_ld_blocks(html):
        for obj in iter_json_objects(block):
            checkin = normalize_text(obj.get("checkinTime"))
            checkout = normalize_text(obj.get("checkoutTime"))
            if checkin or checkout:
                parts = []
                if checkin:
                    parts.append(f"Check-in od {checkin}")
                if checkout:
                    parts.append(f"Check-out do {checkout}")
                return " / ".join(parts)
    return ""


def extract_checkin_checkout_from_text(text: str) -> str:
    plain_text = html_to_text(text)
    patterns = [
        r"check[\s\-]?in[^0-9]{0,40}(\d{1,2}[:.]\d{2})[^a-z0-9]{0,20}check[\s\-]?out[^0-9]{0,40}(\d{1,2}[:.]\d{2})",
        r"arrival[^0-9]{0,40}(\d{1,2}[:.]\d{2})[^a-z0-9]{0,20}departure[^0-9]{0,40}(\d{1,2}[:.]\d{2})",
    ]

    lowered = plain_text.lower()
    for pattern in patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if match:
            checkin = normalize_time_value(match.group(1))
            checkout = normalize_time_value(match.group(2))
            if checkin and checkout:
                return f"Check-in od {checkin} / Check-out do {checkout}"

    checkin_match = re.search(
        r"check[\s\-]?in(?:\s+from|\s+od|\s*:)?[^0-9]{0,20}(\d{1,2}[:.]\d{2})",
        lowered,
        flags=re.IGNORECASE,
    )
    checkout_match = re.search(
        r"check[\s\-]?out(?:\s+until|\s+do|\s*:)?[^0-9]{0,20}(\d{1,2}[:.]\d{2})",
        lowered,
        flags=re.IGNORECASE,
    )

    if checkin_match or checkout_match:
        parts = []
        if checkin_match:
            checkin = normalize_time_value(checkin_match.group(1))
            if checkin:
                parts.append(f"Check-in od {checkin}")
        if checkout_match:
            checkout = normalize_time_value(checkout_match.group(1))
            if checkout:
                parts.append(f"Check-out do {checkout}")
        return " / ".join(parts)

    return ""


def extract_opening_hours_from_text(text: str) -> str:
    plain_text = html_to_text(text)
    lowered = plain_text.lower()
    keyword_patterns = [
        "opening hours",
        "operating hours",
        "open daily",
        "reception 24/7",
        "recepcia 24/7",
        "otváracie hodiny",
        "prevádzkové hodiny",
    ]

    for keyword in keyword_patterns:
        position = lowered.find(keyword)
        if position == -1:
            continue

        snippet = extract_opening_hours_window(plain_text, position)
        has_time = bool(re.search(r"\b\d{1,2}[:.]\d{2}\b", snippet))
        has_always_open = "24/7" in snippet.lower()
        if has_time or has_always_open:
            return snippet

    weekday_pattern = re.search(
        r"(monday|tuesday|wednesday|thursday|friday|saturday|sunday|pondelok|utorok|streda|štvrtok|stvrtok|piatok|sobota|nedeľa|nedela|mo-su|mo-fr|po-ne|po-pia)[^\.]{0,220}\d{1,2}[:.]\d{2}",
        lowered,
        flags=re.IGNORECASE,
    )
    if weekday_pattern:
        start = max(0, weekday_pattern.start())
        snippet = extract_opening_hours_window(plain_text, start)
        if snippet:
            return snippet

    return ""


def collect_public_pages(
    website_url: str,
    timeout_seconds: int,
    page_keywords: list[str],
    max_pages_per_hotel: int,
) -> list[tuple[str, str]]:
    if not website_url:
        return []

    pages: list[tuple[str, str]] = []
    try:
        homepage_html = fetch_public_page(website_url, timeout_seconds)
    except Exception:
        return []

    pages.append((website_url, homepage_html))

    candidate_urls = extract_same_domain_candidate_urls(
        base_url=website_url,
        html=homepage_html,
        keywords=page_keywords,
        max_pages=max(0, max_pages_per_hotel - 1),
    )

    for candidate_url in candidate_urls:
        try:
            pages.append((candidate_url, fetch_public_page(candidate_url, timeout_seconds)))
        except Exception:
            continue

    return pages


def enrich_public_web_fields(
    row: pd.Series,
    unknown_value_label: str,
    verified_public_label: str,
    timeout_seconds: int,
    page_keywords: list[str],
    max_pages_per_hotel: int,
) -> dict[str, str]:
    fallback_opening_hours = extract_first_present_value(
        row,
        ["hotel_opening_hours", "opening_hours", "operating_hours", "business_hours"],
    )
    fallback_checkin_checkout = extract_first_present_value(
        row,
        ["checkin_checkout_info", "checkin_checkout", "check_in_out", "checkin"],
    )

    result = {
        "hotel_opening_hours": fallback_opening_hours or unknown_value_label,
        "hotel_opening_hours_status": verified_public_label if fallback_opening_hours else unknown_value_label,
        "hotel_opening_hours_source_url": normalize_text(row.get("website")) if fallback_opening_hours else "",
        "checkin_checkout_info": fallback_checkin_checkout or unknown_value_label,
        "checkin_checkout_status": verified_public_label if fallback_checkin_checkout else unknown_value_label,
        "checkin_checkout_source_url": normalize_text(row.get("website")) if fallback_checkin_checkout else "",
    }

    website_url = normalize_text(row.get("website"))
    if not website_url:
        return result

    pages = collect_public_pages(
        website_url=website_url,
        timeout_seconds=timeout_seconds,
        page_keywords=page_keywords,
        max_pages_per_hotel=max_pages_per_hotel,
    )

    for page_url, html in pages:
        if result["hotel_opening_hours"] == unknown_value_label:
            opening_hours = extract_opening_hours_from_json_ld(html) or extract_opening_hours_from_text(html)
            if opening_hours and is_likely_hotel_opening_hours(row, opening_hours, page_url):
                result["hotel_opening_hours"] = opening_hours
                result["hotel_opening_hours_status"] = verified_public_label
                result["hotel_opening_hours_source_url"] = page_url

        if result["checkin_checkout_info"] == unknown_value_label:
            checkin_checkout = extract_checkin_checkout_from_json_ld(html) or extract_checkin_checkout_from_text(html)
            if checkin_checkout:
                result["checkin_checkout_info"] = checkin_checkout
                result["checkin_checkout_status"] = verified_public_label
                result["checkin_checkout_source_url"] = page_url

        if (
            result["hotel_opening_hours"] != unknown_value_label
            and result["checkin_checkout_info"] != unknown_value_label
        ):
            break

    return result


def build_contact_status(
    row: pd.Series,
    unknown_value_label: str,
    verified_raw_label: str,
    partial_raw_label: str,
) -> str:
    if row["website"] and row["phone"]:
        return f"{verified_raw_label}: web aj telefón"
    if row["website"]:
        return f"{partial_raw_label}: len web"
    if row["phone"]:
        return f"{partial_raw_label}: len telefón"
    return f"{unknown_value_label}: chýba web aj telefón"


def build_factual_summary(row: pd.Series, unknown_value_label: str) -> str:
    parts = []

    if row["hotel_name"]:
        parts.append(f"Hotel: {row['hotel_name']}")
    if row["city"]:
        parts.append(f"Mesto: {row['city']}")
    if row["category_name"]:
        parts.append(f"Kategória: {row['category_name']}")
    if row["priority_band"] or row["priority_score"] > 0:
        parts.append(
            f"Priorita: {row['priority_band']} ({row['priority_score']})".strip()
        )
    if row["review_score"] > 0:
        review_part = f"Hodnotenie: {row['review_score']}/5"
        if row["reviews_count"] > 0:
            review_part += f" z {int(row['reviews_count'])} recenzií"
        parts.append(review_part)

    website_status = row["website"] if row["website"] else unknown_value_label
    phone_status = row["phone"] if row["phone"] else unknown_value_label
    parts.append(f"Web: {website_status}")
    parts.append(f"Telefón: {phone_status}")
    parts.append(
        f"Otváracie hodiny: {row['hotel_opening_hours']} ({row['hotel_opening_hours_status']})"
    )
    parts.append(
        f"Check-in / check-out: {row['checkin_checkout_info']} ({row['checkin_checkout_status']})"
    )

    return " | ".join(parts)


def build_enrichment_dataframe(
    df: pd.DataFrame,
    unknown_value_label: str,
    verified_public_label: str,
    verified_raw_label: str,
    partial_raw_label: str,
    timeout_seconds: int,
    page_keywords: list[str],
    max_pages_per_hotel: int,
) -> pd.DataFrame:
    enriched = df.copy()

    public_web_fields = enriched.apply(
        lambda row: enrich_public_web_fields(
            row,
            unknown_value_label=unknown_value_label,
            verified_public_label=verified_public_label,
            timeout_seconds=timeout_seconds,
            page_keywords=page_keywords,
            max_pages_per_hotel=max_pages_per_hotel,
        ),
        axis=1,
    )
    public_web_fields = pd.DataFrame(public_web_fields.tolist(), index=enriched.index)

    enriched = pd.concat(
        [
            enriched,
            public_web_fields,
        ],
        axis=1,
    )

    enriched["contact_status"] = enriched.apply(
        lambda row: build_contact_status(
            row,
            unknown_value_label=unknown_value_label,
            verified_raw_label=verified_raw_label,
            partial_raw_label=partial_raw_label,
        ),
        axis=1,
    )
    enriched["factual_summary"] = enriched.apply(
        lambda row: build_factual_summary(row, unknown_value_label),
        axis=1,
    )

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
            "hotel_opening_hours_source_url",
            "checkin_checkout_info",
            "checkin_checkout_status",
            "checkin_checkout_source_url",
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
    enrichment_config = config.get("enrichment", {})
    unknown_value_label = enrichment_config.get(
        "unknown_value_label", "Verejne nepotvrdené"
    )
    verified_public_label = enrichment_config.get(
        "verified_public_label", "Overené vo verejnom zdroji"
    )
    verified_raw_label = enrichment_config.get(
        "verified_raw_label", "Overené z raw vstupu"
    )
    partial_raw_label = enrichment_config.get(
        "partial_raw_label", "Čiastočne overené z raw vstupu"
    )
    timeout_seconds = int(enrichment_config.get("request_timeout_seconds", 12))
    max_pages_per_hotel = int(enrichment_config.get("max_public_pages_per_hotel", 3))
    page_keywords = [
        normalize_text(item).lower()
        for item in enrichment_config.get("public_page_keywords", [])
        if normalize_text(item)
    ]

    try:
        scored_df = pd.read_csv(first_file)
    except Exception as error:
        print(f"Nepodarilo sa načítať processed CSV súbor: {first_file.name}")
        print(f"Dôvod: {error}")
        return

    for column in scored_df.columns:
        if scored_df[column].dtype == object:
            scored_df[column] = scored_df[column].apply(normalize_text)

    enriched_df = build_enrichment_dataframe(
        scored_df,
        unknown_value_label=unknown_value_label,
        verified_public_label=verified_public_label,
        verified_raw_label=verified_raw_label,
        partial_raw_label=partial_raw_label,
        timeout_seconds=timeout_seconds,
        page_keywords=page_keywords,
        max_pages_per_hotel=max_pages_per_hotel,
    )
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
