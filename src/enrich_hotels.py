from pathlib import Path
import html
import json
import re
from urllib.parse import urljoin, urlparse

import pandas as pd
import requests
import yaml


PROCESSED_DIR = Path("data/processed")
QA_DIR = Path("data/qa")
ENRICHMENT_OUTPUT_DIR = Path("outputs/enrichment")
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


def load_enrichment_config(config_path: Path = ENRICHMENT_CONFIG_PATH) -> dict:
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


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
        r"(check[\s\-]?in|arrival)(?:\s+from|\s+od|\s*:)?[^0-9]{0,20}(\d{1,2}[:.]\d{2})",
        lowered,
        flags=re.IGNORECASE,
    )
    checkout_match = re.search(
        r"(check[\s\-]?out|departure)(?:\s+until|\s+do|\s*:)?[^0-9]{0,20}(\d{1,2}[:.]\d{2})",
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
    has_checkin_marker = "check-in" in lowered or "check in" in lowered or "arrival" in lowered
    has_checkout_marker = "check-out" in lowered or "check out" in lowered or "departure" in lowered
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
        r"check[\s\-]?in|check[\s\-]?out|arrival|departure",
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
        "hotel_opening_hours_source_type": classify_public_source_type(normalize_text(row.get("website"))) if fallback_opening_hours else "",
        "checkin_checkout_info": fallback_checkin_checkout or unknown_value_label,
        "checkin_checkout_status": verified_public_label if fallback_checkin_checkout else unknown_value_label,
        "checkin_checkout_source_url": normalize_text(row.get("website")) if fallback_checkin_checkout else "",
        "checkin_checkout_source_type": classify_public_source_type(normalize_text(row.get("website"))) if fallback_checkin_checkout else "",
        "checkin_checkout_source_origin": "raw_input" if fallback_checkin_checkout else "",
        "checkin_checkout_completeness": classify_checkin_checkout_completeness(fallback_checkin_checkout),
        "public_source_reachable": "no",
        "public_source_fetch_status": "not_attempted",
    }

    website_url = normalize_text(row.get("website"))
    if not website_url:
        result["public_source_fetch_status"] = "missing_website"
        return result

    pages, fetch_status = collect_public_pages(
        website_url=website_url,
        timeout_seconds=timeout_seconds,
        page_keywords=page_keywords,
        max_pages_per_hotel=max_pages_per_hotel,
    )
    result["public_source_fetch_status"] = fetch_status
    if pages:
        result["public_source_reachable"] = "yes"

    for page_url, html in pages:
        if result["hotel_opening_hours"] == unknown_value_label:
            opening_hours = extract_opening_hours_from_json_ld(html) or extract_opening_hours_from_text(html)
            if opening_hours and is_likely_hotel_opening_hours(row, opening_hours, page_url):
                result["hotel_opening_hours"] = opening_hours
                result["hotel_opening_hours_status"] = verified_public_label
                result["hotel_opening_hours_source_url"] = page_url
                result["hotel_opening_hours_source_type"] = classify_public_source_type(page_url)

        if result["checkin_checkout_info"] == unknown_value_label:
            checkin_checkout = ""
            checkin_checkout_origin = ""
            jsonld_checkin_checkout = extract_checkin_checkout_from_json_ld(html)
            if jsonld_checkin_checkout:
                checkin_checkout = jsonld_checkin_checkout
                checkin_checkout_origin = "jsonld"
            else:
                text_checkin_checkout = extract_checkin_checkout_from_text(html)
                if text_checkin_checkout:
                    checkin_checkout = text_checkin_checkout
                    checkin_checkout_origin = "text"
            if checkin_checkout and is_likely_checkin_checkout(row, checkin_checkout, page_url):
                result["checkin_checkout_info"] = checkin_checkout
                result["checkin_checkout_status"] = verified_public_label
                result["checkin_checkout_source_url"] = page_url
                result["checkin_checkout_source_type"] = classify_public_source_type(page_url)
                result["checkin_checkout_source_origin"] = checkin_checkout_origin
                result["checkin_checkout_completeness"] = classify_checkin_checkout_completeness(checkin_checkout)

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

    return enriched[
        [
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
            "fit_confidence",
            "ranking_score",
            "priority_score",
            "priority_band",
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

    first_file = processed_files[-1]
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
    )
    enriched_df, reused_previous_rows = reuse_previous_public_web_fields(
        enriched_df=enriched_df,
        previous_df=previous_enriched_df,
    )
    enriched_df["factual_summary"] = enriched_df.apply(
        lambda row: build_factual_summary(row, unknown_value_label),
        axis=1,
    )
    output_path = save_enriched_file(enriched_df, first_file.name)

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
