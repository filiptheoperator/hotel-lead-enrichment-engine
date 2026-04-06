from pathlib import Path
import html
import json
import os
import re
from datetime import datetime, timezone
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
import yaml
from dotenv import load_dotenv


PROCESSED_DIR = Path("data/processed")
QA_DIR = Path("data/qa")
ENRICHMENT_OUTPUT_DIR = Path("outputs/enrichment")
SOURCE_BUNDLE_DIR = Path("outputs/source_bundles")
FACTUAL_ENRICHMENT_DIR = Path("outputs/factual_enrichment")
COMMERCIAL_SYNTHESIS_DIR = Path("outputs/commercial_synthesis")
ENRICHMENT_CONFIG_PATH = Path("configs/enrichment.yaml")
DEFAULT_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (compatible; HotelLeadEnrichmentEngine/1.0; "
        "+https://github.com/filiptheoperator/hotel-lead-enrichment-engine)"
    )
}
NON_HTML_FILE_EXTENSIONS = {
    ".json",
    ".xml",
    ".txt",
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".gif",
    ".svg",
    ".ico",
    ".pdf",
    ".zip",
    ".css",
    ".js",
    ".map",
    ".woff",
    ".woff2",
    ".ttf",
    ".eot",
}
PUBLIC_WEB_COLUMNS = [
    "hotel_opening_hours",
    "hotel_opening_hours_status",
    "hotel_opening_hours_source_url",
    "hotel_opening_hours_source_type",
    "checkin_checkout_info",
    "checkin_checkout_status",
    "checkin_checkout_source_url",
    "checkin_checkout_source_type",
    "checkin_checkout_source_origin",
    "checkin_checkout_completeness",
    "public_source_reachable",
]
PREVIOUS_ARTIFACT_KEY_COLUMNS = ["hotel_name", "city", "source_file"]
SOURCE_BUNDLE_SCHEMA_VERSION = "source_bundle/v1"
FACTUAL_ENRICHMENT_SCHEMA_VERSION = "factual_enrichment/v1"
COMMERCIAL_SYNTHESIS_SCHEMA_VERSION = "commercial_synthesis/v1"
GOOGLE_PLACE_DETAILS_API_URL = "https://places.googleapis.com/v1/places"


def load_enrichment_config(config_path: Path = ENRICHMENT_CONFIG_PATH) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_environment(env_path: Path = Path(".env")) -> None:
    load_dotenv(dotenv_path=env_path, override=False)


def list_processed_files(processed_dir: Path = PROCESSED_DIR) -> list[Path]:
    if not processed_dir.exists():
        return []
    return sorted(processed_dir.glob("*_normalized_scored.csv"), key=lambda path: path.stat().st_mtime)


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def normalize_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def build_bundle_file_stem(row: pd.Series) -> str:
    account_id = normalize_text(row.get("account_id"))
    if account_id:
        return account_id

    hotel_name = normalize_text(row.get("hotel_name")).lower()
    slug = re.sub(r"[^a-z0-9]+", "-", hotel_name).strip("-")
    return slug or "unknown_hotel"


def normalize_numeric_text(value: object) -> str:
    normalized = normalize_text(value)
    if not normalized:
        return ""
    try:
        numeric = float(normalized)
    except ValueError:
        return normalized
    if numeric.is_integer():
        return str(int(numeric))
    return str(numeric)


def extract_google_place_id(source_url: str) -> str:
    match = re.search(r"query_place_id=([^&]+)", normalize_text(source_url))
    if not match:
        return ""
    return match.group(1).strip()


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
    match = re.fullmatch(r"(\d{1,2}):(\d{2})(?::(\d{2}))?", value)
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
        "cookies",
        "zobraziť viac",
        "zobrazit viac",
        "tešíme sa na vás",
        "tesime sa na vas",
        "spravovať súhlas",
        "spravovat suhlas",
        "používame technológie",
        "pouzivame technologie",
    ]

    lowered = value.lower()
    cut_positions = [lowered.find(marker) for marker in cleanup_markers if lowered.find(marker) != -1]
    if cut_positions:
        value = value[: min(cut_positions)].strip(" ,;:-")

    value = re.sub(r"\s{2,}", " ", value)
    return value[:180].strip(" ,;:-")


def extract_relevant_opening_hours_segment(value: str) -> str:
    cleaned = cleanup_opening_hours_value(value)
    lowered = cleaned.lower()

    preferred_markers = [
        "otváracie hodiny recepcie",
        "reception",
        "recepcia",
        "front desk",
        "hotel",
        "nonstop",
        "24/7",
        "otváracie hodiny",
        "opening hours",
    ]

    for marker in preferred_markers:
        index = lowered.find(marker)
        if index != -1:
            cleaned = cleaned[index:]
            break

    cleaned = re.sub(r"^(otváracie hodiny[:\s-]*)+", "Otváracie hodiny: ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"^(opening hours[:\s-]*)+", "Opening hours: ", cleaned, flags=re.IGNORECASE)
    cleaned = re.sub(r"(?i)otváracie hodiny:\s*recepcie:\s*", "Otváracie hodiny recepcie: ", cleaned)
    cleaned = re.sub(r"(?i)opening hours:\s*reception:\s*", "Reception: ", cleaned)

    sentence_breaks = [
        " reštaurácia ",
        " wellness ",
        " spa ",
        " sauna ",
        " bar ",
        " fitness ",
        " squash ",
        " kaviareň ",
        " kaviaren ",
    ]
    lowered = cleaned.lower()
    cut_positions = [lowered.find(marker) for marker in sentence_breaks if lowered.find(marker) > 0]
    if cut_positions:
        cleaned = cleaned[: min(cut_positions)].strip(" ,;:-")

    cleaned = re.sub(r"\(\s*$", "", cleaned).strip(" ,;:-")
    cleaned = cleaned.replace(" h.", "")
    cleaned = cleaned.replace(" hod.", "")
    cleaned = normalize_whitespace(cleaned)
    return cleaned[:140].strip(" ,;:-")


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
        "otváracie hodiny recepcie",
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
        "kuchyňa",
        "kuchyna",
        "raňajky",
        "ranajky",
    ]

    has_allowed_marker = any(marker in lowered for marker in allowed_markers)
    has_excluded_marker = any(marker in lowered for marker in excluded_markers)
    source_is_excluded = any(marker in source_lowered for marker in excluded_markers)
    has_time_signal = bool(re.search(r"\b\d{1,2}[:.]\d{2}\b", lowered)) or "24/7" in lowered

    if has_excluded_marker:
        return False
    if source_is_excluded:
        return False
    if has_allowed_marker and has_time_signal:
        return True

    parsed_source = urlparse(source_url)
    source_path = parsed_source.path.strip("/")
    source_is_homepage = not source_path

    if source_is_homepage and has_time_signal and any(
        marker in normalize_text(row.get("category_name")).lower()
        or marker in normalize_text(row.get("all_categories")).lower()
        for marker in ["hotel", "hostel", "penzion", "residence", "garni", "botel"]
    ):
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
        " cookies",
        " zobraziť viac",
        " zobrazit viac",
    ]

    lowered = window.lower()
    cut_positions = [lowered.find(marker) for marker in split_markers if lowered.find(marker) != -1]
    if cut_positions:
        window = window[: min(cut_positions)]

    return extract_relevant_opening_hours_segment(window)


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
    content_type = normalize_text(response.headers.get("Content-Type")).lower()
    if content_type and "text/html" not in content_type and "application/xhtml+xml" not in content_type:
        return ""
    return response.text


def fetch_google_place_details(
    place_id: str,
    api_key: str,
    timeout_seconds: int,
    fields: list[str],
) -> dict:
    response = requests.get(
        f"{GOOGLE_PLACE_DETAILS_API_URL}/{place_id}",
        timeout=timeout_seconds,
        headers={
            **DEFAULT_HEADERS,
            "Content-Type": "application/json",
            "X-Goog-Api-Key": api_key,
            "X-Goog-FieldMask": ",".join(fields),
        },
    )
    response.raise_for_status()
    return response.json()


def classify_fetch_error(error: Exception) -> str:
    error_text = normalize_text(str(error)).lower()
    error_name = error.__class__.__name__.lower()

    if "nameresolutionerror" in error_text or "failed to resolve" in error_text:
        return "dns_resolution_failed"
    if "connecttimeout" in error_name or "readtimeout" in error_name or "timed out" in error_text:
        return "request_timeout"
    if "ssl" in error_name or "ssl" in error_text:
        return "ssl_error"
    if "connectionerror" in error_name:
        return "connection_error"
    if "http" in error_name:
        return "http_error"
    return "request_failed"


def classify_public_source_type(source_url: str) -> str:
    parsed = urlparse(normalize_text(source_url))
    path = parsed.path.lower().strip("/")

    if not path:
        return "homepage"
    if any(path.endswith(extension) for extension in NON_HTML_FILE_EXTENSIONS):
        return "asset_file"
    if any(marker in path for marker in ["faq", "frequently-asked"]):
        return "faq_page"
    if any(marker in path for marker in ["contact", "kontakt"]):
        return "contact_page"
    if any(marker in path for marker in ["wellness", "spa", "restaurant", "restauracia", "restauracia", "bar"]):
        return "subpage_non_hotel"
    return "subpage_general"


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
        if any(parsed_candidate.path.lower().endswith(extension) for extension in NON_HTML_FILE_EXTENSIONS):
            continue

        normalized_candidate = candidate_url.split("#", 1)[0]
        lower_candidate = normalized_candidate.lower()
        if any(marker in lower_candidate for marker in ["manifest", "favicon", "apple-touch-icon", "android-icon"]):
            continue
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

    return extract_relevant_opening_hours_segment(values[0]) if values else ""


def extract_checkin_checkout_from_json_ld(html: str) -> str:
    for block in extract_json_ld_blocks(html):
        for obj in iter_json_objects(block):
            checkin = normalize_time_value(normalize_text(obj.get("checkinTime")))
            checkout = normalize_time_value(normalize_text(obj.get("checkoutTime")))
            if checkin or checkout:
                parts = []
                if checkin:
                    parts.append(f"Check-in od {checkin}")
                if checkout:
                    parts.append(f"Check-out do {checkout}")
                return " / ".join(parts)
    return ""


def classify_checkin_checkout_completeness(value: str) -> str:
    normalized = normalize_text(value)
    if not normalized or normalized == "Verejne nepotvrdené":
        return "none"

    has_checkin = "Check-in od" in normalized
    has_checkout = "Check-out do" in normalized
    if has_checkin and has_checkout:
        return "paired"
    if has_checkin or has_checkout:
        return "single_side"
    return "none"


def extract_checkin_checkout_window(text: str, start_index: int) -> str:
    plain_text = html_to_text(text)
    window_start = max(0, start_index - 80)
    window = plain_text[window_start : window_start + 260]
    split_markers = [
        " breakfast",
        " continental breakfast",
        " opening hours",
        " operating hours",
        " otváracie hodiny",
        " prevádzkové hodiny",
        " wellness",
        " spa",
        " sauna",
        " restaurant",
        " reštaur",
        " restaurac",
        " parking",
        " parkovanie",
        " cookies",
        " privacy",
        " gdpr",
        " terms",
        " conditions",
        " storno",
        " cancellation",
        " copyright",
    ]

    lowered = window.lower()
    cut_positions = [lowered.find(marker) for marker in split_markers if lowered.find(marker) > 0]
    if cut_positions:
        window = window[: min(cut_positions)]

    return normalize_whitespace(window)[:200].strip(" ,;:-")


def parse_checkin_checkout_candidate(text: str) -> str:
    lowered = normalize_whitespace(text).lower()
    if not lowered:
        return ""

    patterns = [
        r"check[\s\-]?in[^0-9]{0,30}(\d{1,2}[:.]\d{2})[^a-z0-9]{0,16}check[\s\-]?out[^0-9]{0,30}(\d{1,2}[:.]\d{2})",
        r"check[\s\-]?out[^0-9]{0,30}(\d{1,2}[:.]\d{2})[^a-z0-9]{0,16}check[\s\-]?in[^0-9]{0,30}(\d{1,2}[:.]\d{2})",
        r"arrival[^0-9]{0,30}(\d{1,2}[:.]\d{2})[^a-z0-9]{0,16}departure[^0-9]{0,30}(\d{1,2}[:.]\d{2})",
    ]

    for pattern in patterns:
        match = re.search(pattern, lowered, flags=re.IGNORECASE)
        if not match:
            continue
        if "check out" in pattern or "check[\s\-]?out" in pattern[:20]:
            checkout = normalize_time_value(match.group(1))
            checkin = normalize_time_value(match.group(2))
        else:
            checkin = normalize_time_value(match.group(1))
            checkout = normalize_time_value(match.group(2))
        if checkin and checkout:
            return f"Check-in od {checkin} / Check-out do {checkout}"

    checkin_match = re.search(
        r"(check[\s\-]?in)(?:\s+from|\s+od|\s*:)?[^0-9]{0,20}(\d{1,2}[:.]\d{2})",
        lowered,
        flags=re.IGNORECASE,
    )
    checkout_match = re.search(
        r"(check[\s\-]?out)(?:\s+until|\s+do|\s*:)?[^0-9]{0,20}(\d{1,2}[:.]\d{2})",
        lowered,
        flags=re.IGNORECASE,
    )

    parts = []
    if checkin_match:
        checkin = normalize_time_value(checkin_match.group(2))
        if checkin:
            parts.append(f"Check-in od {checkin}")
    if checkout_match:
        checkout = normalize_time_value(checkout_match.group(2))
        if checkout:
            parts.append(f"Check-out do {checkout}")

    if len(parts) == 1:
        time_matches = re.findall(r"\b\d{1,2}[:.]\d{2}(?::\d{2})?\b", lowered)
        if len(time_matches) > 1:
            return ""

    return " / ".join(parts)


def is_likely_checkin_checkout(row: pd.Series, value: str, source_url: str) -> bool:
    cleaned = normalize_text(value)
    if not cleaned:
        return False
    if not is_likely_accommodation_lead(row):
        return False

    lowered = cleaned.lower()
    source_lowered = normalize_text(source_url).lower()
    source_type = classify_public_source_type(source_url)
    hotel_name_lowered = normalize_text(row.get("hotel_name")).lower()
    path_tokens = [token for token in re.split(r"[^a-z0-9]+", urlparse(source_url).path.lower()) if token]

    excluded_markers = [
        "wellness",
        "spa",
        "restaurant",
        "reštaur",
        "restaurac",
        "sauna",
        "massage",
        "masáž",
        "masaz",
        "breakfast",
        "raňajky",
        "ranajky",
        "parking",
        "parkovanie",
        "storno",
        "cancellation",
        "privacy",
        "cookies",
    ]
    strong_source_markers = [
        "hotel",
        "room",
        "rooms",
        "stay",
        "accommodation",
        "ubyt",
        "apartment",
        "apartments",
        "faq",
        "contact",
        "kontakt",
    ]
    has_excluded_marker = any(marker in lowered for marker in excluded_markers)
    source_is_excluded = any(marker in source_lowered for marker in excluded_markers)
    has_explicit_checkin_marker = "check-in" in lowered or "check in" in lowered
    has_explicit_checkout_marker = "check-out" in lowered or "check out" in lowered
    has_arrival_marker = "arrival" in lowered
    has_departure_marker = "departure" in lowered
    has_checkin_marker = has_explicit_checkin_marker or has_arrival_marker
    has_checkout_marker = has_explicit_checkout_marker or has_departure_marker
    time_matches = re.findall(r"\b\d{1,2}:\d{2}\b", lowered)
    strong_source_context = (
        any(marker in source_lowered for marker in strong_source_markers)
        or any(marker in hotel_name_lowered for marker in ["hotel", "hostel", "penzion", "apartm", "residence"])
        or source_type in {"faq_page", "contact_page"}
    )
    single_side_path_ok = bool(
        set(path_tokens).intersection({"hotel", "hostel", "room", "rooms", "stay", "accommodation", "contact", "faq"})
    )

    if has_excluded_marker or source_is_excluded:
        return False
    if source_type not in {"homepage", "subpage_general", "faq_page", "contact_page"}:
        return False
    if not time_matches:
        return False
    if (has_arrival_marker or has_departure_marker) and not (has_explicit_checkin_marker or has_explicit_checkout_marker):
        return has_arrival_marker and has_departure_marker and len(time_matches) >= 2 and strong_source_context
    if has_checkin_marker and has_checkout_marker:
        return True
    if len(time_matches) > 1 and (has_checkin_marker ^ has_checkout_marker):
        return False
    if len(time_matches) >= 2 and (has_checkin_marker or has_checkout_marker) and strong_source_context:
        return True
    if (
        (has_checkin_marker or has_checkout_marker)
        and strong_source_context
        and (
            source_type in {"homepage", "contact_page", "faq_page"}
            or single_side_path_ok
        )
    ):
        return True
    return False


def extract_checkin_checkout_from_text(text: str) -> str:
    plain_text = html_to_text(text)
    anchor_pattern = re.compile(
        r"check[\s\-]?in|check[\s\-]?out",
        flags=re.IGNORECASE,
    )
    candidates: list[str] = []
    seen: set[str] = set()

    for match in anchor_pattern.finditer(plain_text):
        snippet = extract_checkin_checkout_window(plain_text, match.start())
        if not snippet:
            continue
        candidate = parse_checkin_checkout_candidate(snippet)
        if candidate and candidate not in seen:
            seen.add(candidate)
            candidates.append(candidate)

    if candidates:
        paired_candidates = [
            candidate
            for candidate in candidates
            if "Check-in od" in candidate and "Check-out do" in candidate
        ]
        if paired_candidates:
            return paired_candidates[0]
        return candidates[0]

    fallback_patterns = [
        r"check[\s\-]?in[^0-9]{0,40}(\d{1,2}[:.]\d{2})[^a-z0-9]{0,20}check[\s\-]?out[^0-9]{0,40}(\d{1,2}[:.]\d{2})",
        r"arrival[^0-9]{0,40}(\d{1,2}[:.]\d{2})[^a-z0-9]{0,20}departure[^0-9]{0,40}(\d{1,2}[:.]\d{2})",
    ]

    lowered = plain_text.lower()
    for pattern in fallback_patterns:
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
        all_time_matches = re.findall(r"\b\d{1,2}[:.]\d{2}(?::\d{2})?\b", lowered)
        if len(all_time_matches) > 1 and not (checkin_match and checkout_match):
            return ""
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
        "otváracie hodiny recepcie",
        "opening hours reception",
        "reception",
        "recepcia",
        "opening hours",
        "operating hours",
        "otváracie hodiny",
        "prevádzkové hodiny",
        "front desk",
        "hotel",
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
) -> tuple[list[tuple[str, str]], str]:
    if not website_url:
        return [], "missing_website"

    pages: list[tuple[str, str]] = []
    try:
        homepage_html = fetch_public_page(website_url, timeout_seconds)
    except Exception as error:
        return [], classify_fetch_error(error)

    pages.append((website_url, homepage_html))
    fetch_status = "ok"

    candidate_urls = extract_same_domain_candidate_urls(
        base_url=website_url,
        html=homepage_html,
        keywords=page_keywords,
        max_pages=max(0, max_pages_per_hotel - 1),
    )

    for candidate_url in candidate_urls:
        try:
            candidate_html = fetch_public_page(candidate_url, timeout_seconds)
            if not candidate_html:
                continue
            pages.append((candidate_url, candidate_html))
        except Exception:
            continue

    return pages, fetch_status


def collect_google_places_source(
    row: pd.Series,
    timeout_seconds: int,
    google_places_enabled: bool,
    google_places_api_key: str,
    google_places_fields: list[str],
) -> dict:
    source_url = normalize_text(row.get("source_url"))
    place_id = extract_google_place_id(source_url)
    google_maps_url = source_url

    source = {
        "status": "not_enabled" if not google_places_enabled else "not_attempted",
        "place_id": place_id,
        "google_maps_url": google_maps_url,
        "fields_requested": google_places_fields,
        "result": {},
    }

    if not google_places_enabled:
        return source
    if not google_places_api_key:
        source["status"] = "not_configured"
        return source
    if not place_id:
        source["status"] = "missing_place_id"
        return source

    try:
        payload = fetch_google_place_details(
            place_id=place_id,
            api_key=google_places_api_key,
            timeout_seconds=timeout_seconds,
            fields=google_places_fields,
        )
    except Exception as error:
        source["status"] = classify_fetch_error(error)
        source["error_type"] = error.__class__.__name__
        return source

    if isinstance(payload, dict) and isinstance(payload.get("error"), dict):
        error_obj = payload.get("error", {})
        source["status"] = normalize_text(error_obj.get("status")).lower() or "api_error"
        source["error_message"] = normalize_text(error_obj.get("message"))
        return source

    if isinstance(payload, dict):
        api_status = normalize_text(payload.get("status"))
        if api_status:
            source["status"] = api_status.lower()
            source["result"] = payload.get("result", {}) if isinstance(payload.get("result"), dict) else {}
            if api_status != "OK":
                source["error_message"] = normalize_text(payload.get("error_message"))
            return source

        source["status"] = "ok"
        source["result"] = payload
        return source

    source["status"] = "unexpected_payload"

    return source


def extract_company_candidate_from_json_ld(html: str) -> dict[str, str]:
    preferred_types = {
        "organization",
        "corporation",
        "hotel",
        "lodgingbusiness",
        "localbusiness",
        "travelagency",
    }

    for block in extract_json_ld_blocks(html):
        for obj in iter_json_objects(block):
            raw_type = obj.get("@type")
            type_values = raw_type if isinstance(raw_type, list) else [raw_type]
            normalized_types = {
                normalize_text(type_value).lower()
                for type_value in type_values
                if normalize_text(type_value)
            }
            if not normalized_types.intersection(preferred_types):
                continue

            company_name = normalize_text(obj.get("name"))
            if not company_name:
                continue

            return {
                "name": company_name,
                "raw_type": ", ".join(sorted(normalized_types)),
            }

    return {}


def extract_room_count_from_json_ld(html: str) -> str:
    for block in extract_json_ld_blocks(html):
        for obj in iter_json_objects(block):
            for key in ["numberOfRooms", "numberOfAccommodationUnits", "numberOfRoomsTotal"]:
                value = normalize_numeric_text(obj.get(key))
                if value and value.isdigit():
                    numeric_value = int(value)
                    if 3 <= numeric_value <= 500:
                        return value
    return ""


def extract_room_count_from_text(text: str) -> str:
    plain_text = html_to_text(text).lower()
    patterns = [
        r"\b(\d{1,3})\s+(?:rooms|room|guest rooms|guestroom|guestrooms)\b",
        r"\bwith\s+(\d{1,3})\s+(?:rooms|room|guest rooms)\b",
        r"\bponúka\s+(\d{1,3})\s+(?:izieb|izby|izba)\b",
        r"\b(\d{1,3})\s+(?:izieb|izby|izba)\b",
    ]
    for pattern in patterns:
        match = re.search(pattern, plain_text, flags=re.IGNORECASE)
        if not match:
            continue
        value = normalize_numeric_text(match.group(1))
        if value and value.isdigit():
            numeric_value = int(value)
            if 3 <= numeric_value <= 500:
                return value
    return ""


def classify_rooms_range(room_count_value: str) -> str:
    if not room_count_value or not room_count_value.isdigit():
        return ""
    room_count = int(room_count_value)
    if room_count <= 15:
        return "1-15"
    if room_count <= 30:
        return "16-30"
    if room_count <= 50:
        return "31-50"
    if room_count <= 80:
        return "51-80"
    if room_count <= 120:
        return "81-120"
    return "120+"


def extract_star_signal_from_json_ld(html: str) -> str:
    for block in extract_json_ld_blocks(html):
        for obj in iter_json_objects(block):
            star_value = normalize_numeric_text(obj.get("starRating"))
            if star_value and star_value.isdigit() and 1 <= int(star_value) <= 5:
                return star_value

            aggregate_rating = obj.get("starRating")
            if isinstance(aggregate_rating, dict):
                rating_value = normalize_numeric_text(aggregate_rating.get("ratingValue"))
                if rating_value and rating_value.isdigit() and 1 <= int(rating_value) <= 5:
                    return rating_value
    return ""


def extract_star_signal_from_text(text: str) -> str:
    plain_text = html_to_text(text).lower()
    patterns = [
        r"\b([3-5])\s*(?:star|stars)\b",
        r"\b([3-5])\s*[★*]\b",
        r"\b([3-5])\s*hviezd",
    ]
    for pattern in patterns:
        match = re.search(pattern, plain_text, flags=re.IGNORECASE)
        if match:
            return normalize_text(match.group(1))
    return ""


def score_checkin_checkout_candidate(value: str, origin: str, source_type: str) -> int:
    score = 0
    completeness = classify_checkin_checkout_completeness(value)
    if completeness == "paired":
        score += 6
    elif completeness == "single_side":
        score += 2
    if origin == "jsonld":
        score += 4
    elif origin == "text":
        score += 1
    if source_type in {"faq_page", "contact_page"}:
        score += 2
    elif source_type == "homepage":
        score += 1
    return score


def build_source_bundle(
    row: pd.Series,
    timeout_seconds: int,
    page_keywords: list[str],
    max_pages_per_hotel: int,
    google_places_enabled: bool,
    google_places_api_key: str,
    google_places_fields: list[str],
) -> dict:
    website_url = normalize_text(row.get("website"))
    raw_opening_hours = extract_first_present_value(
        row,
        ["hotel_opening_hours", "opening_hours", "operating_hours", "business_hours"],
    )
    raw_checkin_checkout = extract_first_present_value(
        row,
        ["checkin_checkout_info", "checkin_checkout", "check_in_out", "checkin"],
    )

    bundle = {
        "schema_version": SOURCE_BUNDLE_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "account_id": normalize_text(row.get("account_id")),
        "source_file": normalize_text(row.get("source_file")),
        "hotel_identity": {
            "hotel_name": normalize_text(row.get("hotel_name")),
            "city": normalize_text(row.get("city")),
            "country_code": normalize_text(row.get("country_code")),
            "website": website_url,
            "website_domain": normalize_text(row.get("website_domain")),
        },
        "raw_contact_hints": {
            "phone": normalize_text(row.get("phone")),
            "source_url": normalize_text(row.get("source_url")),
            "fallback_opening_hours": raw_opening_hours,
            "fallback_checkin_checkout": raw_checkin_checkout,
        },
        "sources": {
            "google_places": collect_google_places_source(
                row,
                timeout_seconds=timeout_seconds,
                google_places_enabled=google_places_enabled,
                google_places_api_key=google_places_api_key,
                google_places_fields=google_places_fields,
            ),
            "official_website": {
                "base_url": website_url,
                "fetch_status": "not_attempted",
                "reachable": False,
                "pages": [],
            },
        },
        "extracted_candidates": {
            "hotel_opening_hours": {
                "value": "",
                "origin": "",
                "source_url": "",
                "source_type": "",
            },
            "checkin_checkout": {
                "value": "",
                "origin": "",
                "source_url": "",
                "source_type": "",
            },
            "ownership_company": {
                "value": "",
                "origin": "",
                "source_url": "",
                "source_type": "",
                "raw_type": "",
            },
            "room_count": {
                "value": "",
                "origin": "",
                "source_url": "",
                "source_type": "",
            },
            "star_signal": {
                "value": "",
                "origin": "",
                "source_url": "",
                "source_type": "",
            },
        },
    }

    if not website_url:
        bundle["sources"]["official_website"]["fetch_status"] = "missing_website"
        return bundle

    pages, fetch_status = collect_public_pages(
        website_url=website_url,
        timeout_seconds=timeout_seconds,
        page_keywords=page_keywords,
        max_pages_per_hotel=max_pages_per_hotel,
    )
    website_source = bundle["sources"]["official_website"]
    website_source["fetch_status"] = fetch_status
    website_source["reachable"] = bool(pages)

    for page_url, html in pages:
        source_type = classify_public_source_type(page_url)
        opening_hours_jsonld = extract_opening_hours_from_json_ld(html)
        opening_hours_text = extract_opening_hours_from_text(html)
        checkin_checkout_jsonld = extract_checkin_checkout_from_json_ld(html)
        checkin_checkout_text = extract_checkin_checkout_from_text(html)
        star_signal_jsonld = extract_star_signal_from_json_ld(html)
        star_signal_text = extract_star_signal_from_text(html)

        opening_hours_value = opening_hours_jsonld or opening_hours_text
        opening_hours_origin = "jsonld" if opening_hours_jsonld else "text" if opening_hours_text else ""
        checkin_checkout_value = checkin_checkout_jsonld or checkin_checkout_text
        checkin_checkout_origin = "jsonld" if checkin_checkout_jsonld else "text" if checkin_checkout_text else ""

        opening_hours_valid = bool(
            opening_hours_value and is_likely_hotel_opening_hours(row, opening_hours_value, page_url)
        )
        checkin_checkout_valid = bool(
            checkin_checkout_value and is_likely_checkin_checkout(row, checkin_checkout_value, page_url)
        )

        website_source["pages"].append(
            {
                "url": page_url,
                "source_type": source_type,
                "jsonld_detected": bool(extract_json_ld_blocks(html)),
                "text_length": len(html_to_text(html)),
                "opening_hours_candidate": opening_hours_value,
                "opening_hours_origin": opening_hours_origin,
                "opening_hours_valid": opening_hours_valid,
                "checkin_checkout_candidate": checkin_checkout_value,
                "checkin_checkout_origin": checkin_checkout_origin,
                "checkin_checkout_valid": checkin_checkout_valid,
            }
        )

        jsonld_company_candidate = extract_company_candidate_from_json_ld(html)
        if jsonld_company_candidate and not bundle["extracted_candidates"]["ownership_company"]["value"]:
            bundle["extracted_candidates"]["ownership_company"] = {
                "value": normalize_text(jsonld_company_candidate.get("name")),
                "origin": "jsonld",
                "source_url": page_url,
                "source_type": source_type,
                "raw_type": normalize_text(jsonld_company_candidate.get("raw_type")),
            }

        room_count_value = extract_room_count_from_json_ld(html)
        room_count_origin = "jsonld"
        if not room_count_value:
            room_count_value = extract_room_count_from_text(html)
            room_count_origin = "text" if room_count_value else ""
        if room_count_value and not bundle["extracted_candidates"]["room_count"]["value"]:
            bundle["extracted_candidates"]["room_count"] = {
                "value": room_count_value,
                "origin": room_count_origin,
                "source_url": page_url,
                "source_type": source_type,
            }

        if opening_hours_valid and not bundle["extracted_candidates"]["hotel_opening_hours"]["value"]:
            bundle["extracted_candidates"]["hotel_opening_hours"] = {
                "value": opening_hours_value,
                "origin": opening_hours_origin,
                "source_url": page_url,
                "source_type": source_type,
            }

        if checkin_checkout_valid and not bundle["extracted_candidates"]["checkin_checkout"]["value"]:
            bundle["extracted_candidates"]["checkin_checkout"] = {
                "value": checkin_checkout_value,
                "origin": checkin_checkout_origin,
                "source_url": page_url,
                "source_type": source_type,
            }
        elif checkin_checkout_valid:
            existing_candidate = bundle["extracted_candidates"]["checkin_checkout"]
            existing_score = score_checkin_checkout_candidate(
                normalize_text(existing_candidate.get("value")),
                normalize_text(existing_candidate.get("origin")),
                normalize_text(existing_candidate.get("source_type")),
            )
            current_score = score_checkin_checkout_candidate(
                checkin_checkout_value,
                checkin_checkout_origin,
                source_type,
            )
            if current_score > existing_score:
                bundle["extracted_candidates"]["checkin_checkout"] = {
                    "value": checkin_checkout_value,
                    "origin": checkin_checkout_origin,
                    "source_url": page_url,
                    "source_type": source_type,
                }

        star_signal_value = star_signal_jsonld or star_signal_text
        star_signal_origin = "jsonld" if star_signal_jsonld else "text" if star_signal_text else ""
        if star_signal_value and not bundle["extracted_candidates"]["star_signal"]["value"]:
            bundle["extracted_candidates"]["star_signal"] = {
                "value": star_signal_value,
                "origin": star_signal_origin,
                "source_url": page_url,
                "source_type": source_type,
            }

    return bundle


def save_source_bundle(bundle: dict, row: pd.Series) -> Path:
    source_file_stem = Path(normalize_text(row.get("source_file")) or "unknown_source").stem
    bundle_dir = SOURCE_BUNDLE_DIR / source_file_stem
    bundle_dir.mkdir(parents=True, exist_ok=True)
    bundle_path = bundle_dir / f"{build_bundle_file_stem(row)}.json"
    with bundle_path.open("w", encoding="utf-8") as file:
        json.dump(bundle, file, ensure_ascii=False, indent=2)
    return bundle_path


def build_service_mix(row: pd.Series, source_bundle: dict, unknown_value_label: str) -> dict:
    google_places_result = get_google_places_result(source_bundle)
    google_types = {
        normalize_text(item).lower()
        for item in google_places_result.get("types", [])
        if normalize_text(item)
    }
    google_primary_type = normalize_text(google_places_result.get("primaryType")).lower()
    category_context = " ".join(
        [
            normalize_text(row.get("category_name")).lower(),
            normalize_text(row.get("all_categories")).lower(),
            normalize_text(row.get("hotel_name")).lower(),
        ]
    )
    page_context = " ".join(
        normalize_text(page.get("url")).lower()
        for page in source_bundle.get("sources", {}).get("official_website", {}).get("pages", [])
    )

    service_rules = {
        "wellness": {
            "text_markers": ["wellness"],
            "google_types": {"spa", "health_spa"},
        },
        "restaurant": {
            "text_markers": ["restaurant", "reštaur", "restaurac", "gastro", "dining"],
            "google_types": {"restaurant", "meal_takeaway", "meal_delivery", "bar"},
        },
        "event_congress": {
            "text_markers": ["event", "kongres", "congress", "conference", "meeting", "wedding", "function room"],
            "google_types": {"event_venue", "wedding_venue", "conference_center", "banquet_hall"},
        },
        "spa": {
            "text_markers": ["spa"],
            "google_types": {"spa"},
        },
        "parking": {
            "text_markers": ["parking", "parkovanie"],
            "google_types": {"parking"},
        },
        "bowling": {
            "text_markers": ["bowling"],
            "google_types": {"bowling_alley"},
        },
    }

    result: dict[str, dict[str, str]] = {}
    for service_name, rule in service_rules.items():
        text_markers = rule["text_markers"]
        type_markers = rule["google_types"]
        in_categories = any(marker in category_context for marker in text_markers)
        in_pages = any(marker in page_context for marker in text_markers)
        in_google_types = bool(type_markers.intersection(google_types)) or google_primary_type in type_markers
        detected = in_categories or in_pages or in_google_types

        if in_categories:
            source_origin = "raw_categories"
            evidence = ", ".join(text_markers)
        elif in_google_types:
            source_origin = "google_places_types"
            evidence = ", ".join(sorted(type_markers.intersection(google_types) or ({google_primary_type} if google_primary_type in type_markers else set())))
        elif in_pages:
            source_origin = "official_web_url"
            evidence = ", ".join(text_markers)
        else:
            source_origin = ""
            evidence = unknown_value_label

        result[service_name] = {
            "available": "yes" if detected else "unknown",
            "source_origin": source_origin,
            "evidence": evidence,
        }

    return result


def build_review_signal(row: pd.Series, unknown_value_label: str) -> dict[str, str]:
    review_score = normalize_numeric_text(row.get("review_score"))
    reviews_count = normalize_numeric_text(row.get("reviews_count"))
    if review_score and review_score not in {"0", "0.0"}:
        summary = f"{review_score}/5"
        if reviews_count and reviews_count not in {"0", "0.0"}:
            summary += f" z {reviews_count} recenzií"
        return {
            "summary": summary,
            "score": review_score,
            "reviews_count": reviews_count,
            "status": "raw_confirmed",
            "source_origin": "processed_row",
        }

    return {
        "summary": unknown_value_label,
        "score": "",
        "reviews_count": reviews_count,
        "status": unknown_value_label,
        "source_origin": "",
    }


def build_room_count_signal(row: pd.Series, source_bundle: dict, unknown_value_label: str) -> dict[str, str]:
    extracted_room_count = source_bundle.get("extracted_candidates", {}).get("room_count", {})
    extracted_value = normalize_numeric_text(extracted_room_count.get("value"))
    if extracted_value and extracted_value.isdigit():
        return {
            "value": extracted_value,
            "rooms_range": classify_rooms_range(extracted_value),
            "status": "public_confirmed",
            "source_origin": normalize_text(extracted_room_count.get("origin")) or "official_web",
            "note": (
                f"Room count candidate z official webu: {extracted_value}"
                f" | source_type: {normalize_text(extracted_room_count.get('source_type'))}"
            ),
        }

    room_count = normalize_numeric_text(row.get("room_count"))
    if room_count and room_count not in {"0", "0.0"}:
        return {
            "value": room_count,
            "rooms_range": classify_rooms_range(room_count),
            "status": "raw_confirmed",
            "source_origin": "processed_row",
            "note": f"V raw/processed vstupe je uvedený room_count = {room_count}.",
        }

    return {
        "value": "",
        "rooms_range": "",
        "status": unknown_value_label,
        "source_origin": "",
        "note": "Presný počet izieb je verejne nepotvrdený v aktuálnom source bundle.",
    }


def build_ownership_company_signal(row: pd.Series, source_bundle: dict, unknown_value_label: str) -> dict[str, str]:
    google_places_result = get_google_places_result(source_bundle)
    extracted_ownership = source_bundle.get("extracted_candidates", {}).get("ownership_company", {})
    jsonld_company_name = normalize_text(extracted_ownership.get("value"))
    jsonld_company_type = normalize_text(extracted_ownership.get("raw_type"))
    business_status = normalize_text(google_places_result.get("businessStatus"))
    display_name = normalize_text(google_places_result.get("displayName", {}).get("text"))
    raw_ownership_type = normalize_text(row.get("ownership_type"))

    if jsonld_company_name:
        note_parts = [f"JSON-LD názov: {jsonld_company_name}"]
        if jsonld_company_type:
            note_parts.append(f"typ: {jsonld_company_type}")
        if business_status:
            note_parts.append(f"businessStatus: {business_status}")
        return {
            "value": jsonld_company_name,
            "status": "public_confirmed",
            "source_origin": "official_web_jsonld",
            "note": " | ".join(note_parts),
        }

    if raw_ownership_type:
        note = f"Processed ownership_type: {raw_ownership_type}"
        if display_name:
            note += f" | Google displayName: {display_name}"
        if business_status:
            note += f" | businessStatus: {business_status}"
        return {
            "value": raw_ownership_type,
            "status": "raw_confirmed",
            "source_origin": "processed_row",
            "note": note,
        }

    note = f"Google displayName: {display_name}" if display_name else "Ownership/company signal je verejne nepotvrdený."
    if business_status:
        note += f" | businessStatus: {business_status}"
    return {
        "value": unknown_value_label,
        "status": unknown_value_label,
        "source_origin": "",
        "note": note,
    }


def build_factual_enrichment_artifact(
    row: pd.Series,
    source_bundle: dict,
    unknown_value_label: str,
    verified_public_label: str,
) -> dict:
    google_places_result = get_google_places_result(source_bundle)
    public_web_fields = enrich_public_web_fields_from_bundle(
        row,
        source_bundle=source_bundle,
        unknown_value_label=unknown_value_label,
        verified_public_label=verified_public_label,
    )
    address_parts = [
        normalize_text(google_places_result.get("formatted_address")) or normalize_text(row.get("street")),
        normalize_text(row.get("city")),
        normalize_text(row.get("state")),
        normalize_text(row.get("country_code")),
    ]
    address_summary = ", ".join(part for part in address_parts if part)
    google_phone = normalize_text(google_places_result.get("internationalPhoneNumber"))
    google_rating = normalize_numeric_text(google_places_result.get("rating"))
    google_user_rating_count = normalize_numeric_text(google_places_result.get("userRatingCount"))
    google_name = normalize_text(google_places_result.get("displayName", {}).get("text"))
    google_formatted_address = normalize_text(google_places_result.get("formattedAddress"))
    google_website = normalize_text(google_places_result.get("websiteUri"))
    google_primary_type = normalize_text(google_places_result.get("primaryType"))
    google_primary_type_display_name = normalize_text(
        google_places_result.get("primaryTypeDisplayName", {}).get("text")
    )
    google_types = [
        normalize_text(item)
        for item in google_places_result.get("types", [])
        if normalize_text(item)
    ]
    ownership_company_signal = build_ownership_company_signal(row, source_bundle, unknown_value_label)
    room_count_signal = build_room_count_signal(row, source_bundle, unknown_value_label)
    star_signal = source_bundle.get("extracted_candidates", {}).get("star_signal", {})
    google_opening_hours = google_places_result.get("regularOpeningHours", {})
    google_opening_hours_text = ""
    if isinstance(google_opening_hours, dict):
        weekday_text = google_opening_hours.get("weekdayDescriptions")
        if isinstance(weekday_text, list):
            google_opening_hours_text = "; ".join(normalize_text(item) for item in weekday_text if normalize_text(item))

    return {
        "schema_version": FACTUAL_ENRICHMENT_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "account_id": normalize_text(row.get("account_id")),
        "source_file": normalize_text(row.get("source_file")),
        "source_bundle_ref": str(
            SOURCE_BUNDLE_DIR
            / Path(normalize_text(row.get("source_file")) or "unknown_source").stem
            / f"{build_bundle_file_stem(row)}.json"
        ),
        "identity": {
            "hotel_name": google_name or normalize_text(row.get("hotel_name")),
            "city": normalize_text(row.get("city")),
            "state": normalize_text(row.get("state")),
            "country_code": normalize_text(row.get("country_code")),
            "hotel_type_class": normalize_text(row.get("hotel_type_class")),
            "category_name": normalize_text(row.get("category_name")),
            "ownership_type": normalize_text(row.get("ownership_type")) or unknown_value_label,
            "google_place_name": google_name,
            "google_primary_type": google_primary_type,
            "google_primary_type_display_name": google_primary_type_display_name,
            "google_types": google_types,
        },
        "contacts": {
            "website": google_website or normalize_text(row.get("website")) or unknown_value_label,
            "website_domain": normalize_text(row.get("website_domain")),
            "phone": google_phone or normalize_text(row.get("phone")) or unknown_value_label,
            "source_origin": "google_places" if google_phone or google_website else "processed_row",
        },
        "address": {
            "street": normalize_text(row.get("street")) or unknown_value_label,
            "city": normalize_text(row.get("city")) or unknown_value_label,
            "state": normalize_text(row.get("state")) or unknown_value_label,
            "country_code": normalize_text(row.get("country_code")) or unknown_value_label,
            "formatted": google_formatted_address or address_summary or unknown_value_label,
            "source_origin": "google_places" if google_formatted_address else "processed_row",
        },
        "operating_hours": {
            "hotel_opening_hours": public_web_fields["hotel_opening_hours"],
            "status": public_web_fields["hotel_opening_hours_status"],
            "source_url": public_web_fields["hotel_opening_hours_source_url"],
            "source_type": public_web_fields["hotel_opening_hours_source_type"],
            "google_places_weekday_text": google_opening_hours_text,
        },
        "checkin_checkout": {
            "value": public_web_fields["checkin_checkout_info"],
            "status": public_web_fields["checkin_checkout_status"],
            "source_url": public_web_fields["checkin_checkout_source_url"],
            "source_type": public_web_fields["checkin_checkout_source_type"],
            "source_origin": public_web_fields["checkin_checkout_source_origin"],
            "completeness": public_web_fields["checkin_checkout_completeness"],
        },
        "star_signal": {
            "value": normalize_text(star_signal.get("value")) or unknown_value_label,
            "status": "public_confirmed" if normalize_text(star_signal.get("value")) else unknown_value_label,
            "source_url": normalize_text(star_signal.get("source_url")),
            "source_type": normalize_text(star_signal.get("source_type")),
            "source_origin": normalize_text(star_signal.get("origin")),
        },
        "room_count_signal": room_count_signal,
        "service_mix": build_service_mix(row, source_bundle, unknown_value_label),
        "review_trust_signal": build_review_signal(row, unknown_value_label),
        "google_review_signal": {
            "rating": google_rating,
            "user_ratings_total": google_user_rating_count,
            "status": "google_places_confirmed" if google_rating else unknown_value_label,
            "source_origin": "google_places" if google_rating else "",
        },
        "ownership_company_signal": {
            "value": ownership_company_signal["value"],
            "status": ownership_company_signal["status"],
            "source_origin": ownership_company_signal["source_origin"],
            "note": ownership_company_signal["note"],
        },
        "source_reachability": {
            "public_source_reachable": public_web_fields["public_source_reachable"],
            "public_source_fetch_status": public_web_fields["public_source_fetch_status"],
            "google_places_status": normalize_text(source_bundle.get("sources", {}).get("google_places", {}).get("status")),
        },
    }


def save_factual_enrichment_artifact(factual_enrichment: dict, row: pd.Series) -> Path:
    source_file_stem = Path(normalize_text(row.get("source_file")) or "unknown_source").stem
    factual_dir = FACTUAL_ENRICHMENT_DIR / source_file_stem
    factual_dir.mkdir(parents=True, exist_ok=True)
    factual_path = factual_dir / f"{build_bundle_file_stem(row)}.json"
    with factual_path.open("w", encoding="utf-8") as file:
        json.dump(factual_enrichment, file, ensure_ascii=False, indent=2)
    return factual_path


def build_service_summary(service_mix: dict) -> tuple[list[str], int]:
    active_services = [
        service_name
        for service_name, payload in service_mix.items()
        if normalize_text(payload.get("available")) == "yes"
    ]
    return active_services, len(active_services)


def build_verdict_label(
    priority_band: str,
    service_count: int,
    review_score: str,
    ownership_status: str,
    ranking_score: float,
    room_count_missing: bool,
    opening_hours_missing: bool,
    checkin_missing: bool,
) -> str:
    review_value = float(review_score) if review_score else 0.0
    practical_clarity_score = int(not opening_hours_missing) + int(not checkin_missing) + int(not room_count_missing)

    if (
        priority_band in {"High", "Medium-High"}
        and ranking_score >= 80
        and review_value >= 4.4
        and service_count >= 2
        and (ownership_status == "public_confirmed" or practical_clarity_score >= 2)
    ):
        return "silný prospect"
    if ownership_status == "public_confirmed" or service_count >= 2 or review_value >= 4.4:
        return "zaujímavý prospect"
    return "opatrný prospect"


def build_commercial_synthesis_artifact(
    row: pd.Series,
    source_bundle: dict,
    factual_enrichment: dict,
    unknown_value_label: str,
) -> dict:
    service_mix = factual_enrichment.get("service_mix", {})
    active_services, service_count = build_service_summary(service_mix)
    service_labels = {
        "wellness": "wellness",
        "restaurant": "reštaurácia / gastro",
        "event_congress": "event / kongres",
        "spa": "spa",
        "parking": "parkovanie",
        "bowling": "bowling",
    }
    service_list_text = ", ".join(service_labels.get(service, service) for service in active_services)
    opening_hours_missing = normalize_text(factual_enrichment.get("operating_hours", {}).get("status")) == unknown_value_label
    checkin_missing = normalize_text(factual_enrichment.get("checkin_checkout", {}).get("status")) == unknown_value_label
    room_count_signal = factual_enrichment.get("room_count_signal", {})
    room_count_missing = normalize_text(room_count_signal.get("status")) == unknown_value_label
    review_signal = factual_enrichment.get("review_trust_signal", {})
    review_score = normalize_numeric_text(review_signal.get("score"))
    review_count = normalize_numeric_text(review_signal.get("reviews_count"))
    ownership_signal = factual_enrichment.get("ownership_company_signal", {})
    ownership_status = normalize_text(ownership_signal.get("status"))
    priority_band = normalize_text(row.get("priority_band"))
    ranking_score = float(row.get("ranking_score") or 0)
    hotel_name = normalize_text(row.get("hotel_name"))
    city = normalize_text(row.get("city"))

    strengths: list[str] = []
    if service_count >= 2:
        strengths.append(f"Hotel má širší service mix: {service_list_text}.")
    if review_score and float(review_score) >= 4.4:
        review_text = f"{review_score}/5"
        if review_count:
            review_text += f" z {review_count} recenzií"
        strengths.append(f"Silný review trust signal: {review_text}.")
    if ownership_status == "public_confirmed":
        strengths.append("Ownership/company signal je verejne potvrdený z official webu.")
    if normalize_text(factual_enrichment.get("operating_hours", {}).get("status")) != unknown_value_label:
        strengths.append("Hotel má verejne dohľadateľné operating hours.")

    opportunity_gaps: list[str] = []
    if opening_hours_missing:
        opportunity_gaps.append("Chýbajú jasné hotelové operating hours na prvý pohľad.")
    if checkin_missing:
        opportunity_gaps.append("Chýba jasný check-in / check-out signal vo verejných zdrojoch.")
    if room_count_missing:
        opportunity_gaps.append("Presný room count alebo rooms range ostáva verejne nepotvrdený.")
    if service_count >= 3:
        opportunity_gaps.append("Širší service mix môže zvyšovať komunikačnú a rozhodovaciu zložitosť.")

    if service_count >= 3:
        main_bottleneck = "Pri širšom service mixe sa môže časť dopytu strácať medzi typom záujmu a správnym ďalším krokom."
    elif opening_hours_missing or checkin_missing:
        main_bottleneck = "Praktické informácie nie sú všade rovnako jasné, čo môže brzdiť prvý kontakt alebo rozhodnutie."
    else:
        main_bottleneck = "Hlavný bottleneck zatiaľ verejne nevyzerá kriticky, ale oplatí sa preveriť jasnosť prvého kroku pre hosťa."

    if checkin_missing:
        pain_point = "Hosť nemusí mať rýchlo jasno v praktických pobytových pravidlách pred rezerváciou."
    elif opening_hours_missing:
        pain_point = "Hosť nemusí mať na prvý pohľad jasné, kedy a ako sa vie spojiť s hotelom alebo prevádzkou."
    elif service_count >= 3:
        pain_point = "Pri viacerých službách naraz môže byť pre hosťa menej jasné, kam presne smerovať svoj záujem."
    else:
        pain_point = "Najpravdepodobnejší pain point je skôr v jemnej optimalizácii cesty k dopytu než v zásadnej informačnej diere."

    personalization_angles: list[str] = []
    if service_count >= 2:
        personalization_angles.append(
            f"Hotel spája viac línií dopytu naraz: {service_list_text}."
        )
    if review_score and float(review_score) >= 4.4:
        personalization_angles.append(
            f"Silný reputačný základ ({review_score}/5) dáva priestor riešiť skôr konverznú jasnosť než reputačný problém."
        )
    if opening_hours_missing or checkin_missing:
        personalization_angles.append(
            "Vo verejných zdrojoch chýbajú niektoré praktické pobytové informácie, čo vie byť prirodzený vstup do konverzácie."
        )

    if service_count >= 3:
        business_interest_summary = (
            f"{hotel_name} v {city} pôsobí obchodne zaujímavo najmä pre širší service mix a viac typov dopytu."
        )
        recommended_hook = (
            "Krátky pohľad na to, či má každý typ hosťa okamžite jasné, čo má spraviť ako prvé."
        )
    elif ownership_status == "public_confirmed" and review_score and float(review_score) >= 4.4:
        business_interest_summary = (
            f"{hotel_name} v {city} pôsobí ako stabilný account s verejne čitateľným profilom a slušným review základom."
        )
        recommended_hook = (
            "Krátky pohľad na to, kde sa dá ešte zjednodušiť cesta od prvého záujmu k priamemu dopytu."
        )
    elif opening_hours_missing or checkin_missing:
        business_interest_summary = (
            f"{hotel_name} v {city} je zaujímavý skôr cez praktickú informačnú vrstvu a jasnosť prvého kontaktu."
        )
        recommended_hook = (
            "Krátky postreh k tomu, ktoré praktické informácie hosť nemusí nájsť hneď na prvý pohľad."
        )
    else:
        business_interest_summary = (
            f"{hotel_name} v {city} má základné signály v poriadku a vyzerá skôr na jemnú optimalizáciu než veľký verejný problém."
        )
        recommended_hook = (
            "Krátky audit toho, či silný verejný profil rovnako dobre podporuje aj priamy dopyt."
        )

    call_hypothesis = (
        "Na krátkom hovore sa oplatí overiť, ktoré typy dopytu dnes dominujú a kde vzniká najväčšie váhanie pred kontaktom alebo rezerváciou."
    )
    verdict = build_verdict_label(
        priority_band=priority_band,
        service_count=service_count,
        review_score=review_score,
        ownership_status=ownership_status,
        ranking_score=ranking_score,
        room_count_missing=room_count_missing,
        opening_hours_missing=opening_hours_missing,
        checkin_missing=checkin_missing,
    )

    return {
        "schema_version": COMMERCIAL_SYNTHESIS_SCHEMA_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "account_id": normalize_text(row.get("account_id")),
        "source_file": normalize_text(row.get("source_file")),
        "source_bundle_ref": str(
            SOURCE_BUNDLE_DIR
            / Path(normalize_text(row.get("source_file")) or "unknown_source").stem
            / f"{build_bundle_file_stem(row)}.json"
        ),
        "factual_enrichment_ref": str(
            FACTUAL_ENRICHMENT_DIR
            / Path(normalize_text(row.get("source_file")) or "unknown_source").stem
            / f"{build_bundle_file_stem(row)}.json"
        ),
        "business_interest_summary": business_interest_summary,
        "strengths": strengths,
        "opportunity_gaps": opportunity_gaps,
        "main_bottleneck_hypothesis": main_bottleneck,
        "pain_point_hypothesis": pain_point,
        "personalization_angles": personalization_angles,
        "recommended_hook": recommended_hook,
        "call_hypothesis": call_hypothesis,
        "verdict": verdict,
        "grounding": {
            "active_services": active_services,
            "service_count": service_count,
            "opening_hours_missing": opening_hours_missing,
            "checkin_checkout_missing": checkin_missing,
            "room_count_missing": room_count_missing,
            "review_score": review_score,
            "review_count": review_count,
            "ownership_status": ownership_status,
            "priority_band": priority_band,
        },
    }


def save_commercial_synthesis_artifact(commercial_synthesis: dict, row: pd.Series) -> Path:
    source_file_stem = Path(normalize_text(row.get("source_file")) or "unknown_source").stem
    commercial_dir = COMMERCIAL_SYNTHESIS_DIR / source_file_stem
    commercial_dir.mkdir(parents=True, exist_ok=True)
    commercial_path = commercial_dir / f"{build_bundle_file_stem(row)}.json"
    with commercial_path.open("w", encoding="utf-8") as file:
        json.dump(commercial_synthesis, file, ensure_ascii=False, indent=2)
    return commercial_path


def build_row_artifact_path(base_dir: Path, row: pd.Series) -> Path:
    source_file_stem = Path(normalize_text(row.get("source_file")) or "unknown_source").stem
    return base_dir / source_file_stem / f"{build_bundle_file_stem(row)}.json"


def load_json_artifact(artifact_path: Path) -> dict:
    if not artifact_path.exists():
        return {}
    try:
        with artifact_path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def build_selected_commercial_csv_fields(row: pd.Series, unknown_value_label: str) -> dict[str, str]:
    factual_artifact = load_json_artifact(build_row_artifact_path(FACTUAL_ENRICHMENT_DIR, row))
    commercial_artifact = load_json_artifact(build_row_artifact_path(COMMERCIAL_SYNTHESIS_DIR, row))

    room_count_signal = factual_artifact.get("room_count_signal", {})
    return {
        "rooms_range": normalize_text(room_count_signal.get("rooms_range")),
        "room_count_value": normalize_text(room_count_signal.get("value")),
        "room_count_status": normalize_text(room_count_signal.get("status")) or unknown_value_label,
        "business_interest_summary": normalize_text(commercial_artifact.get("business_interest_summary")),
        "main_bottleneck_hypothesis": normalize_text(commercial_artifact.get("main_bottleneck_hypothesis")),
        "pain_point_hypothesis": normalize_text(commercial_artifact.get("pain_point_hypothesis")),
        "recommended_hook": normalize_text(commercial_artifact.get("recommended_hook")),
        "call_hypothesis": normalize_text(commercial_artifact.get("call_hypothesis")),
        "commercial_verdict": normalize_text(commercial_artifact.get("verdict")),
    }


def get_google_places_result(source_bundle: dict) -> dict:
    google_places = source_bundle.get("sources", {}).get("google_places", {})
    if normalize_text(google_places.get("status")).lower() != "ok":
        return {}
    result = google_places.get("result", {})
    return result if isinstance(result, dict) else {}


def enrich_public_web_fields_from_bundle(
    row: pd.Series,
    source_bundle: dict,
    unknown_value_label: str,
    verified_public_label: str,
) -> dict[str, str]:
    fallback_opening_hours = source_bundle.get("raw_contact_hints", {}).get("fallback_opening_hours", "")
    fallback_checkin_checkout = source_bundle.get("raw_contact_hints", {}).get("fallback_checkin_checkout", "")
    extracted_opening_hours = source_bundle.get("extracted_candidates", {}).get("hotel_opening_hours", {})
    extracted_checkin_checkout = source_bundle.get("extracted_candidates", {}).get("checkin_checkout", {})
    website_source = source_bundle.get("sources", {}).get("official_website", {})
    google_places_result = get_google_places_result(source_bundle)
    google_maps_url = normalize_text(source_bundle.get("sources", {}).get("google_places", {}).get("google_maps_url"))
    google_opening_hours = google_places_result.get("regularOpeningHours", {})
    google_weekday_descriptions = []
    if isinstance(google_opening_hours, dict):
        weekday_descriptions = google_opening_hours.get("weekdayDescriptions")
        if isinstance(weekday_descriptions, list):
            google_weekday_descriptions = [normalize_text(item) for item in weekday_descriptions if normalize_text(item)]
    google_opening_hours_text = "; ".join(google_weekday_descriptions)

    result = {
        "hotel_opening_hours": fallback_opening_hours or unknown_value_label,
        "hotel_opening_hours_status": verified_public_label if fallback_opening_hours else unknown_value_label,
        "hotel_opening_hours_source_url": normalize_text(row.get("website")) if fallback_opening_hours else "",
        "hotel_opening_hours_source_type": classify_public_source_type(normalize_text(row.get("website"))) if fallback_opening_hours else "",
        "checkin_checkout_info": fallback_checkin_checkout or unknown_value_label,
        "checkin_checkout_status": verified_public_label if fallback_checkin_checkout else unknown_value_label,
        "checkin_checkout_source_url": normalize_text(row.get("website")) if fallback_checkin_checkout else "",
        "checkin_checkout_source_type": classify_public_source_type(normalize_text(row.get("website"))) if fallback_checkin_checkout else "",
        "checkin_checkout_source_origin": "raw_input" if fallback_checkin_checkout else "",
        "checkin_checkout_completeness": classify_checkin_checkout_completeness(fallback_checkin_checkout),
        "public_source_reachable": "yes" if website_source.get("reachable") else "no",
        "public_source_fetch_status": normalize_text(website_source.get("fetch_status")) or "not_attempted",
    }

    if extracted_opening_hours.get("value"):
        result["hotel_opening_hours"] = normalize_text(extracted_opening_hours.get("value"))
        result["hotel_opening_hours_status"] = verified_public_label
        result["hotel_opening_hours_source_url"] = normalize_text(extracted_opening_hours.get("source_url"))
        result["hotel_opening_hours_source_type"] = normalize_text(extracted_opening_hours.get("source_type"))
    elif google_opening_hours_text:
        result["hotel_opening_hours"] = google_opening_hours_text
        result["hotel_opening_hours_status"] = verified_public_label
        result["hotel_opening_hours_source_url"] = google_maps_url
        result["hotel_opening_hours_source_type"] = "google_places"

    if extracted_checkin_checkout.get("value"):
        value = normalize_text(extracted_checkin_checkout.get("value"))
        result["checkin_checkout_info"] = value
        result["checkin_checkout_status"] = verified_public_label
        result["checkin_checkout_source_url"] = normalize_text(extracted_checkin_checkout.get("source_url"))
        result["checkin_checkout_source_type"] = normalize_text(extracted_checkin_checkout.get("source_type"))
        result["checkin_checkout_source_origin"] = normalize_text(extracted_checkin_checkout.get("origin"))
        result["checkin_checkout_completeness"] = classify_checkin_checkout_completeness(value)

    return result


def enrich_public_web_fields(
    row: pd.Series,
    unknown_value_label: str,
    verified_public_label: str,
    timeout_seconds: int,
    page_keywords: list[str],
    max_pages_per_hotel: int,
    google_places_enabled: bool,
    google_places_api_key: str,
    google_places_fields: list[str],
) -> dict[str, str]:
    source_bundle = build_source_bundle(
        row,
        timeout_seconds=timeout_seconds,
        page_keywords=page_keywords,
        max_pages_per_hotel=max_pages_per_hotel,
        google_places_enabled=google_places_enabled,
        google_places_api_key=google_places_api_key,
        google_places_fields=google_places_fields,
    )
    save_source_bundle(source_bundle, row)
    factual_enrichment = build_factual_enrichment_artifact(
        row,
        source_bundle=source_bundle,
        unknown_value_label=unknown_value_label,
        verified_public_label=verified_public_label,
    )
    save_factual_enrichment_artifact(factual_enrichment, row)
    commercial_synthesis = build_commercial_synthesis_artifact(
        row,
        source_bundle=source_bundle,
        factual_enrichment=factual_enrichment,
        unknown_value_label=unknown_value_label,
    )
    save_commercial_synthesis_artifact(commercial_synthesis, row)
    return enrich_public_web_fields_from_bundle(
        row,
        source_bundle=source_bundle,
        unknown_value_label=unknown_value_label,
        verified_public_label=verified_public_label,
    )


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


def is_unknown_value(value: object, unknown_value_label: str) -> bool:
    normalized = normalize_text(value)
    return normalized == "" or normalized == unknown_value_label


def build_main_observed_issue(row: pd.Series, unknown_value_label: str) -> str:
    if is_unknown_value(row.get("hotel_opening_hours"), unknown_value_label):
        return "Na webe som nenašiel jasne uvedené otváracie hodiny alebo recepčné časy."
    if is_unknown_value(row.get("checkin_checkout_info"), unknown_value_label):
        return "Na webe som nenašiel jasne uvedený check-in a check-out na prvý pohľad."
    if not normalize_text(row.get("website")):
        return "Vo verejnom profile chýba jasný webový kontakt."
    if not normalize_text(row.get("phone")):
        return "Vo verejnom profile chýba jasne uvedený telefónny kontakt."
    return "Základné informácie sú dostupné, ale prvý kontakt môže ísť ešte stručnejšie a vecnejšie."


def build_give_first_insight(row: pd.Series, unknown_value_label: str) -> str:
    if is_unknown_value(row.get("hotel_opening_hours"), unknown_value_label):
        return "Pri rýchlom pozretí webu som nenašiel jasne uvedené otváracie hodiny alebo časy recepcie."
    if is_unknown_value(row.get("checkin_checkout_info"), unknown_value_label):
        return "Pri rýchlom pozretí webu som nenašiel jasne uvedený check-in a check-out."
    if not normalize_text(row.get("website")):
        return "Vo verejnom profile som nenašiel priamo uvedený web, čo vie brzdiť prvý kontakt."
    if not normalize_text(row.get("phone")):
        return "Vo verejnom profile som nenašiel priamo uvedený telefón, čo vie brzdiť rýchly kontakt."
    return "Na webe som našiel základné praktické údaje, takže prvý email môže ísť rovno cez krátky konkrétny postreh."


def build_email_hook(row: pd.Series) -> str:
    hotel_name = normalize_text(row.get("hotel_name"))
    city = normalize_text(row.get("city"))
    if hotel_name and city:
        return f"Pozeral som sa na {hotel_name} v lokalite {city}."
    if hotel_name:
        return f"Pozeral som sa na {hotel_name}."
    return "Pozeral som sa na váš hotel cez verejne dostupné údaje."


def build_micro_cta(row: pd.Series, primary_email_goal: str) -> str:
    if primary_email_goal == "reply_with_permission":
        return "Ak chcete, pošlem 3 stručné postrehy v krátkej forme."
    if primary_email_goal == "reply_with_interest":
        return "Ak to je pre vás zaujímavé, môžem poslať krátke zhrnutie."
    return "Ak chcete, môžem to poslať stručne v pár bodoch."


def build_proof_snippet(row: pd.Series, unknown_value_label: str) -> str:
    if normalize_text(row.get("hotel_opening_hours_status")) == "Overené vo verejnom zdroji":
        return f"Vychádzal som z verejne uvedených hodín: {normalize_text(row.get('hotel_opening_hours'))}."
    if normalize_text(row.get("checkin_checkout_status")) == "Overené vo verejnom zdroji":
        return f"Vychádzal som z verejne uvedeného check-in/check-out: {normalize_text(row.get('checkin_checkout_info'))}."
    if normalize_text(row.get("website")) or normalize_text(row.get("phone")):
        return "Pozeral som len verejne dostupný profil a základné kontaktné údaje."
    return f"Nemal som viac než verejne dostupné údaje, preto držím len opatrný a krátky postreh."


def classify_email_angle(row: pd.Series, unknown_value_label: str) -> str:
    if is_unknown_value(row.get("hotel_opening_hours"), unknown_value_label):
        return "opening_hours_clarity"
    if is_unknown_value(row.get("checkin_checkout_info"), unknown_value_label):
        return "checkin_checkout_clarity"
    if not normalize_text(row.get("website")) or not normalize_text(row.get("phone")):
        return "contact_clarity"
    return "first_contact_clarity"


def build_variant_id(email_angle: str, variant_prefix: str) -> str:
    suffix_map = {
        "opening_hours_clarity": "1",
        "checkin_checkout_clarity": "2",
        "contact_clarity": "3",
        "first_contact_clarity": "4",
    }
    return f"{variant_prefix}{suffix_map.get(email_angle, '0')}"


def build_test_batch(row: pd.Series) -> str:
    source_file = normalize_text(row.get("source_file"))
    if not source_file:
        return ""
    return Path(source_file).stem


def build_enrichment_dataframe(
    df: pd.DataFrame,
    unknown_value_label: str,
    verified_public_label: str,
    verified_raw_label: str,
    partial_raw_label: str,
    timeout_seconds: int,
    page_keywords: list[str],
    max_pages_per_hotel: int,
    primary_email_goal_default: str,
    default_cta_type: str,
    default_reply_outcome: str,
    default_variant_prefix: str,
    google_places_enabled: bool,
    google_places_api_key: str,
    google_places_fields: list[str],
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
            google_places_enabled=google_places_enabled,
            google_places_api_key=google_places_api_key,
            google_places_fields=google_places_fields,
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
    enriched["email_hook"] = enriched.apply(build_email_hook, axis=1)
    enriched["main_observed_issue"] = enriched.apply(
        lambda row: build_main_observed_issue(row, unknown_value_label),
        axis=1,
    )
    enriched["give_first_insight"] = enriched.apply(
        lambda row: build_give_first_insight(row, unknown_value_label),
        axis=1,
    )
    enriched["primary_email_goal"] = primary_email_goal_default
    enriched["micro_cta"] = enriched.apply(
        lambda row: build_micro_cta(row, primary_email_goal_default),
        axis=1,
    )
    enriched["proof_snippet"] = enriched.apply(
        lambda row: build_proof_snippet(row, unknown_value_label),
        axis=1,
    )
    enriched["email_angle"] = enriched.apply(
        lambda row: classify_email_angle(row, unknown_value_label),
        axis=1,
    )
    enriched["cta_type"] = default_cta_type
    enriched["variant_id"] = enriched["email_angle"].apply(
        lambda value: build_variant_id(normalize_text(value), default_variant_prefix)
    )
    enriched["test_batch"] = enriched.apply(build_test_batch, axis=1)
    enriched["reply_outcome"] = default_reply_outcome

    commercial_csv_fields = enriched.apply(
        lambda row: build_selected_commercial_csv_fields(row, unknown_value_label),
        axis=1,
    )
    commercial_csv_fields = pd.DataFrame(commercial_csv_fields.tolist(), index=enriched.index)
    enriched = pd.concat([enriched, commercial_csv_fields], axis=1)

    return enriched[
        [
            "account_id",
            "hotel_name",
            "hotel_name_normalized",
            "city",
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
            "all_categories",
            "review_score",
            "reviews_count",
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
            "rooms_range",
            "room_count_value",
            "room_count_status",
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
            "hotel_opening_hours",
            "hotel_opening_hours_status",
            "hotel_opening_hours_source_url",
            "hotel_opening_hours_source_type",
            "checkin_checkout_info",
            "checkin_checkout_status",
            "checkin_checkout_source_url",
            "checkin_checkout_source_type",
            "checkin_checkout_source_origin",
            "checkin_checkout_completeness",
            "public_source_reachable",
            "public_source_fetch_status",
            "contact_status",
            "factual_summary",
            "business_interest_summary",
            "main_bottleneck_hypothesis",
            "pain_point_hypothesis",
            "recommended_hook",
            "call_hypothesis",
            "commercial_verdict",
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
            "source_url",
            "source_file",
        ]
    ].copy()


def load_previous_enrichment_artifact(source_file: str) -> pd.DataFrame:
    candidate_paths = [
        ENRICHMENT_OUTPUT_DIR / f"{Path(source_file).stem}_enriched.csv",
        QA_DIR / "before_enriched.csv",
    ]

    best_df = pd.DataFrame()
    best_score = -1
    for candidate_path in candidate_paths:
        if not candidate_path.exists():
            continue
        try:
            candidate_df = pd.read_csv(candidate_path)
        except Exception:
            continue
        if "checkin_checkout_source_origin" not in candidate_df.columns:
            candidate_df["checkin_checkout_source_origin"] = ""
            verified_mask = candidate_df["checkin_checkout_status"].fillna("").astype(str).str.strip().eq(
                "Overené vo verejnom zdroji"
            )
            candidate_df.loc[verified_mask, "checkin_checkout_source_origin"] = "text"
        if "checkin_checkout_completeness" not in candidate_df.columns:
            candidate_df["checkin_checkout_completeness"] = candidate_df["checkin_checkout_info"].apply(
                classify_checkin_checkout_completeness
            )
        if not set(PREVIOUS_ARTIFACT_KEY_COLUMNS + PUBLIC_WEB_COLUMNS).issubset(candidate_df.columns):
            continue

        candidate_score = int(
            candidate_df["public_source_reachable"].fillna("").astype(str).str.strip().eq("yes").sum()
        )
        if candidate_score > best_score:
            best_df = candidate_df
            best_score = candidate_score

    return best_df


def reuse_previous_public_web_fields(
    enriched_df: pd.DataFrame,
    previous_df: pd.DataFrame,
) -> tuple[pd.DataFrame, int]:
    if enriched_df.empty or previous_df.empty:
        return enriched_df, 0

    required_columns = set(PREVIOUS_ARTIFACT_KEY_COLUMNS + PUBLIC_WEB_COLUMNS)
    if not required_columns.issubset(previous_df.columns):
        return enriched_df, 0

    fallback_source = previous_df[PREVIOUS_ARTIFACT_KEY_COLUMNS + PUBLIC_WEB_COLUMNS].copy()
    fallback_source = fallback_source.rename(
        columns={column: f"{column}_previous" for column in PUBLIC_WEB_COLUMNS}
    )

    merged = enriched_df.merge(
        fallback_source,
        on=PREVIOUS_ARTIFACT_KEY_COLUMNS,
        how="left",
    )

    fallback_mask = (
        merged["public_source_fetch_status"].fillna("").astype(str).str.strip().eq("dns_resolution_failed")
        & merged["public_source_reachable_previous"].fillna("").astype(str).str.strip().eq("yes")
    )

    reused_rows = int(fallback_mask.sum())
    if reused_rows == 0:
        return enriched_df, 0

    for column in PUBLIC_WEB_COLUMNS:
        previous_column = f"{column}_previous"
        merged.loc[fallback_mask, column] = merged.loc[fallback_mask, previous_column]

    merged.loc[fallback_mask, "public_source_fetch_status"] = "dns_resolution_failed_fallback_previous"

    cleanup_columns = [f"{column}_previous" for column in PUBLIC_WEB_COLUMNS]
    merged = merged.drop(columns=cleanup_columns)
    return merged, reused_rows


def save_enriched_file(df: pd.DataFrame, source_file: str, output_suffix: str = "") -> Path:
    ENRICHMENT_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    suffix = f"_{output_suffix}" if output_suffix else ""
    output_path = ENRICHMENT_OUTPUT_DIR / f"{Path(source_file).stem}_enriched{suffix}.csv"
    df.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    load_environment()
    processed_files = list_processed_files()

    if not processed_files:
        print("V priečinku data/processed nie je žiadny normalized_scored CSV súbor.")
        return

    preferred_source_file = normalize_text(os.getenv("ENRICHMENT_SOURCE_FILE"))
    first_file = processed_files[-1]
    if preferred_source_file:
        for candidate in processed_files:
            if candidate.name == preferred_source_file:
                first_file = candidate
                break
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
    primary_email_goal_default = str(
        enrichment_config.get("primary_email_goal_default", "reply_with_permission")
    ).strip()
    default_cta_type = str(
        enrichment_config.get("default_cta_type", "low_friction_permission")
    ).strip()
    default_reply_outcome = str(
        enrichment_config.get("default_reply_outcome", "")
    ).strip()
    default_variant_prefix = str(
        enrichment_config.get("default_variant_prefix", "A")
    ).strip() or "A"
    timeout_seconds = int(enrichment_config.get("request_timeout_seconds", 12))
    max_pages_per_hotel = int(enrichment_config.get("max_public_pages_per_hotel", 3))
    google_places_enabled = str(
        enrichment_config.get("google_places_enabled", "false")
    ).strip().lower() in {"1", "true", "yes", "on"}
    google_places_api_key = normalize_text(
        os.getenv("GOOGLE_PLACES_API_KEY") or os.getenv("GOOGLE_MAPS_API_KEY")
    )
    google_places_fields = [
        normalize_text(item)
        for item in enrichment_config.get(
            "google_places_fields",
            [
                "displayName",
                "formattedAddress",
                "websiteUri",
                "internationalPhoneNumber",
                "rating",
                "userRatingCount",
                "regularOpeningHours",
                "googleMapsUri",
            ],
        )
        if normalize_text(item)
    ]
    page_keywords = [
        normalize_text(item).lower()
        for item in enrichment_config.get("public_page_keywords", [])
        if normalize_text(item)
    ]
    batch_limit_raw = normalize_text(os.getenv("ENRICHMENT_BATCH_LIMIT"))
    output_suffix = normalize_text(os.getenv("ENRICHMENT_OUTPUT_SUFFIX"))

    try:
        scored_df = pd.read_csv(first_file)
    except Exception as error:
        print(f"Nepodarilo sa načítať processed CSV súbor: {first_file.name}")
        print(f"Dôvod: {error}")
        return

    for column in scored_df.columns:
        if scored_df[column].dtype == object:
            scored_df[column] = scored_df[column].apply(normalize_text)

    if batch_limit_raw:
        try:
            batch_limit = int(batch_limit_raw)
        except ValueError:
            batch_limit = 0
        if batch_limit > 0:
            scored_df = scored_df.head(batch_limit).copy()

    previous_enriched_df = load_previous_enrichment_artifact(first_file.name)
    enriched_df = build_enrichment_dataframe(
        scored_df,
        unknown_value_label=unknown_value_label,
        verified_public_label=verified_public_label,
        verified_raw_label=verified_raw_label,
        partial_raw_label=partial_raw_label,
        timeout_seconds=timeout_seconds,
        page_keywords=page_keywords,
        max_pages_per_hotel=max_pages_per_hotel,
        primary_email_goal_default=primary_email_goal_default,
        default_cta_type=default_cta_type,
        default_reply_outcome=default_reply_outcome,
        default_variant_prefix=default_variant_prefix,
        google_places_enabled=google_places_enabled,
        google_places_api_key=google_places_api_key,
        google_places_fields=google_places_fields,
    )
    enriched_df, reused_previous_rows = reuse_previous_public_web_fields(
        enriched_df=enriched_df,
        previous_df=previous_enriched_df,
    )
    enriched_df["factual_summary"] = enriched_df.apply(
        lambda row: build_factual_summary(row, unknown_value_label),
        axis=1,
    )
    output_path = save_enriched_file(enriched_df, first_file.name, output_suffix=output_suffix)

    print(f"Načítaný processed súbor: {first_file.name}")
    print(f"Počet riadkov: {len(enriched_df)}")
    print(f"Výstup uložený do: {output_path}")
    if reused_previous_rows:
        print(
            f"Použitý fallback z predchádzajúceho enrichment artifactu pre {reused_previous_rows} riadkov."
        )
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
