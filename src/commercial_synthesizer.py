import json
import os
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml
from dotenv import load_dotenv
from openai import OpenAI
from pydantic import BaseModel, Field


PROCESSED_DIR = Path("data/processed")
SOURCE_BUNDLE_DIR = Path("outputs/source_bundles")
FACTUAL_ENRICHMENT_DIR = Path("outputs/factual_enrichment")
COMMERCIAL_SYNTHESIS_DIR = Path("outputs/commercial_synthesis")
COMMERCIAL_CONFIG_PATH = Path("configs/commercial_synthesis.yaml")
COMMERCIAL_SYNTHESIS_SCHEMA_VERSION = "commercial_synthesis/v3-lite"


class CommercialSynthesisOutput(BaseModel):
    business_interest_summary: str = Field(..., description="Krátke grounded obchodné zhrnutie po slovensky, max 1 veta.")
    why_commercially_interesting: str = Field(..., description="Prečo je hotel obchodne zaujímavý, 1-2 krátke vety.")
    property_positioning_summary: str = Field(..., description="Krátke prirodzené zhrnutie typu a pozicioningu hotela, max 1 veta.")
    strengths: list[str] = Field(default_factory=list, description="Silné stránky podložené len vstupnými dátami.")
    opportunity_gaps: list[str] = Field(default_factory=list, description="Medzery alebo nejasnosti viditeľné z verejných zdrojov.")
    main_bottleneck_hypothesis: str = Field(..., description="Najpravdepodobnejší sales-practical bottleneck, max 1 veta, explicitne opatrne formulovaný.")
    pain_point_hypothesis: str = Field(..., description="Najpravdepodobnejší grounded pain point, max 1 veta.")
    best_entry_angle: str = Field(..., description="Najlepší prvý obchodný uhol, max 1 veta.")
    personalization_angles: list[str] = Field(default_factory=list, description="2-3 vety pripravené priamo do outreachu, prirodzené a grounded.")
    recommended_hook: str = Field(..., description="Krátky odporúčaný hook pre outreach, max 1 veta.")
    recommended_first_contact_route: str = Field(..., description="Odporúčaný prvý kontakt alebo route, krátka veta.")
    likely_decision_maker_hypothesis: str = Field(..., description="Kto je pravdepodobný prvý decision maker alebo owner-side kontakt, opatrne formulované.")
    demand_mix_hypothesis: list[str] = Field(default_factory=list, description="Krátke hypotézy o typoch dopytu, len ak sú grounded.")
    service_complexity_read: str = Field(..., description="Krátky read o šírke služieb a zložitosti ponuky.")
    commercial_complexity_read: str = Field(..., description="Krátky read o obchodnej a komunikačnej zložitosti hotela.")
    direct_booking_friction_hypothesis: str = Field(..., description="Krátka grounded hypotéza o frictione pred priamym dopytom alebo rezerváciou.")
    contact_route_friction_hypothesis: str = Field(..., description="Krátka grounded hypotéza o frictione v prvom kontakte alebo ceste k správnemu tímu.")
    call_hypothesis: str = Field(..., description="Richer hypotéza na prvý krátky hovor, 2-4 krátke vety.")
    verdict: str = Field(..., description="Jeden z labelov: silný prospect, zaujímavý prospect, opatrný prospect.")
    uncertainty_notes: list[str] = Field(default_factory=list, description="Čo ostáva neoverené alebo neisté.")


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_environment() -> None:
    load_dotenv(".env", override=False)


def load_config(config_path: Path = COMMERCIAL_CONFIG_PATH) -> dict:
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def list_processed_files() -> list[Path]:
    if not PROCESSED_DIR.exists():
        return []
    return sorted(PROCESSED_DIR.glob("*_normalized_scored.csv"), key=lambda path: path.stat().st_mtime)


def build_bundle_file_stem(row: pd.Series) -> str:
    account_id = normalize_text(row.get("account_id"))
    if account_id:
        return account_id
    hotel_name = normalize_text(row.get("hotel_name")).lower()
    safe = "".join(char if char.isalnum() else "-" for char in hotel_name)
    safe = "-".join(part for part in safe.split("-") if part)
    return safe or "unknown_hotel"


def build_account_id(row: pd.Series) -> str:
    account_id = normalize_text(row.get("account_id"))
    if account_id:
        return account_id
    return build_bundle_file_stem(row)


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        with path.open("r", encoding="utf-8") as file:
            payload = json.load(file)
    except Exception:
        return {}
    return payload if isinstance(payload, dict) else {}


def build_artifact_path(base_dir: Path, source_file_stem: str, file_stem: str) -> Path:
    return base_dir / source_file_stem / f"{file_stem}.json"


def build_grounded_input(row: pd.Series, source_bundle: dict, factual_enrichment: dict) -> dict:
    processed_row = {
        "account_id": normalize_text(row.get("account_id")),
        "hotel_name": normalize_text(row.get("hotel_name")),
        "city": normalize_text(row.get("city")),
        "country_code": normalize_text(row.get("country_code")),
        "website": normalize_text(row.get("website")),
        "category_name": normalize_text(row.get("category_name")),
        "hotel_type_class": normalize_text(row.get("hotel_type_class")),
        "ownership_type": normalize_text(row.get("ownership_type")),
        "review_score": normalize_text(row.get("review_score")),
        "reviews_count": normalize_text(row.get("reviews_count")),
        "ranking_score": normalize_text(row.get("ranking_score")),
        "priority_band": normalize_text(row.get("priority_band")),
        "ranking_reason": normalize_text(row.get("ranking_reason")),
    }
    compact_source_bundle = {
        "hotel_identity": source_bundle.get("hotel_identity", {}),
        "raw_contact_hints": source_bundle.get("raw_contact_hints", {}),
        "sources": {
            "google_places": {
                "status": normalize_text(source_bundle.get("sources", {}).get("google_places", {}).get("status")),
                "place_id": normalize_text(source_bundle.get("sources", {}).get("google_places", {}).get("place_id")),
                "fields_requested": source_bundle.get("sources", {}).get("google_places", {}).get("fields_requested", []),
                "result": source_bundle.get("sources", {}).get("google_places", {}).get("result", {}),
            },
            "official_website": {
                "base_url": normalize_text(source_bundle.get("sources", {}).get("official_website", {}).get("base_url")),
                "fetch_status": normalize_text(source_bundle.get("sources", {}).get("official_website", {}).get("fetch_status")),
                "reachable": source_bundle.get("sources", {}).get("official_website", {}).get("reachable"),
                "pages": source_bundle.get("sources", {}).get("official_website", {}).get("pages", []),
            },
        },
        "extracted_candidates": source_bundle.get("extracted_candidates", {}),
    }
    return {
        "processed_row": processed_row,
        "source_bundle": compact_source_bundle,
        "factual_enrichment": factual_enrichment,
    }


def build_prompt_payload(grounded_input: dict) -> str:
    return json.dumps(grounded_input, ensure_ascii=False, indent=2)


def build_instructions() -> str:
    return (
        "Si commercial_synthesizer pre hotel lead enrichment. "
        "Odpovedaj len po slovensky. "
        "Používaj len údaje, ktoré sú vo vstupe. "
        "Nevymýšľaj žiadne nové fakty. "
        "Ak niečo nie je jasne potvrdené, explicitne to označ ako neisté alebo verejne nepotvrdené. "
        "Nevypĺňaj silné tvrdenia bez podkladu. "
        "business_interest_summary musí byť presne 1 krátka veta. "
        "Nehovor všeobecne, že hotel je fit, atraktívny target alebo komerčne zaujímavý bez vysvetlenia. "
        "Vždy pomenuj konkrétne: kde sa môže strácať dopyt, kde sa môže miešať typ záujmu, kde môže byť friction pred dopytom alebo rezerváciou, čo sa oplatí preveriť ako prvé. "
        "why_commercially_interesting majú byť najviac 2 krátke vety a majú byť konkrétne, nie abstraktné. "
        "property_positioning_summary musí byť prirodzený hotelový popis, nie interná taxonómia. "
        "recommended_hook musí byť presne 1 krátka veta. "
        "best_entry_angle musí byť presne 1 krátka veta. "
        "recommended_first_contact_route musí byť krátka praktická veta, nie všeobecná rada. "
        "likely_decision_maker_hypothesis musí byť opatrná a grounded. "
        "service_complexity_read a commercial_complexity_read musia byť krátke a consulting-grade, bez flufu. "
        "direct_booking_friction_hypothesis a contact_route_friction_hypothesis musia byť explicitne opatrné. "
        "main_bottleneck_hypothesis musí byť presne 1 krátka veta a má byť viac sales-practical než opisná. "
        "recommended_hook musí byť audit-first, pokojný, observačný a low-pressure. "
        "Preferuj formulácie ako: všimli sme si, pri takomto type hotela býva, často sa tu stráca, oplatí sa preveriť. "
        "Zakázané sú offer-ish a sales frázy ako radi by sme pomohli, atraktívny target, silná ICP zhoda, komerčne zaujímavý hotel. "
        "personalization_angles musia byť mini paragrafy po 2-3 vetách, priamo použiteľné do emailu, nie jednoslovné labely. "
        "call_hypothesis má byť bohatší: čo overiť najprv, kde sa môže miešať dopyt, kde môže byť manual burden na recepcii alebo GM, kto zrejme rozhoduje. "
        "Nepíš odseky navyše; preferuj krátke, prirodzené formulácie. "
        "Verdict musí byť len jeden z: silný prospect, zaujímavý prospect, opatrný prospect."
    )


def collapse_whitespace(value: str) -> str:
    return " ".join(normalize_text(value).split())


def keep_first_sentence(value: str) -> str:
    text = collapse_whitespace(value)
    if not text:
        return ""
    for delimiter in [". ", "? ", "! "]:
        if delimiter in text:
            head = text.split(delimiter, 1)[0].strip()
            if head and head[-1:] not in ".!?":
                head += "."
            return head
    if text[-1:] not in ".!?":
        text += "."
    return text


def truncate_text(value: str, max_len: int) -> str:
    text = collapse_whitespace(value)
    if len(text) <= max_len:
        return text
    cut = text[: max_len - 1].rstrip(" ,;:-")
    return cut + "…"


def sanitize_sentence(value: str, max_len: int) -> str:
    return truncate_text(keep_first_sentence(value), max_len=max_len)


def sanitize_list(values: list[str], max_items: int = 4, max_len: int = 140) -> list[str]:
    sanitized: list[str] = []
    for item in values[:max_items]:
        text = truncate_text(collapse_whitespace(item), max_len=max_len)
        if text:
            sanitized.append(text)
    return sanitized


def sanitize_paragraph(value: str, max_len: int = 260, max_sentences: int = 3) -> str:
    text = collapse_whitespace(value)
    if not text:
        return ""
    sentences: list[str] = []
    current = ""
    for char in text:
        current += char
        if char in ".!?":
            sentence = collapse_whitespace(current)
            if sentence:
                sentences.append(sentence)
            current = ""
            if len(sentences) >= max_sentences:
                break
    if not sentences and current.strip():
        sentences.append(collapse_whitespace(current).rstrip(".!?") + ".")
    joined = " ".join(sentences[:max_sentences]).strip()
    if joined and joined[-1] not in ".!?":
        joined += "."
    return truncate_text(joined, max_len=max_len)


def sanitize_paragraph_list(values: list[str], max_items: int = 3, max_len: int = 280) -> list[str]:
    sanitized: list[str] = []
    for item in values[:max_items]:
        text = sanitize_paragraph(item, max_len=max_len, max_sentences=3)
        if text:
            sanitized.append(text)
    return sanitized


def make_text_less_generic(value: str) -> str:
    text = collapse_whitespace(value)
    if not text:
        return ""
    replacements = {
        "silná ICP zhoda": "dobrá zhoda s cieľovým typom hotela",
        "silný ICP fit": "dobrá zhoda s cieľovým typom hotela",
        "atraktívny cieľ pre spoluprácu": "zaujímavý najmä cez konkrétnu prevádzkovú a obchodnú logiku",
        "komerčne zaujímavý": "zaujímavý najmä tým, kde sa môže strácať dopyt alebo vzniká friction",
        "komerčne zaujímavé": "zaujímavé najmä tým, kde sa môže strácať dopyt alebo vzniká friction",
        "silná spokojnosť zákazníkov": "dobrá verejná spokojnosť hostí",
        "mohli pomôcť": "sa oplatí preveriť",
        "s našimi riešeniami": "",
        "našimi riešeniami": "",
        "príležitosťami na rozšírenie služieb": "miestami, kde sa môže miešať dopyt medzi viacerými službami",
        "príležitosti na rozšírenie služieb": "miesta, kde sa môže miešať dopyt medzi viacerými službami",
        "obchodné možnosti": "miesta, kde sa môže strácať časť záujmu pred dopytom",
        "implementácii nových služieb": "úpravách prevádzky alebo komunikácie",
        "implementácii nových riešení": "zmenách v procese alebo komunikácii",
        "flexibilitu v rozhodovaní": "kratší rozhodovací okruh",
        "príležitosti na zlepšenie": "miesta, kde sa môže strácať časť záujmu pred dopytom",
        "môžeme pomôcť lepšie zvládnuť": "sa oplatí presnejšie preveriť",
        "môžeme pomôcť": "sa oplatí preveriť",
        "optimalizovať": "spresniť",
        "radi by sme pochopili": "opláca sa preveriť",
        "je zaujímavé preskúmať": "sa opláca preveriť",
        "unikátna kombinácia": "kombinácia",
        "príležitosti na zefektívnenie": "miesta, kde sa môže strácať časť záujmu pred dopytom",
        "príležitosti na rozšírenie": "miesta, kde sa môže strácať časť záujmu pred dopytom",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    banned_fragments = [
        "atraktívny target",
        "target pre spoluprácu",
        "možnosti spolupráce",
        "silnú zhodu",
        "silná zhodu",
        "zaujímavalo by nás",
    ]
    for fragment in banned_fragments:
        text = text.replace(fragment, "")
    return " ".join(text.split())


def starts_with_audit_phrase(value: str) -> bool:
    lowered = collapse_whitespace(value).lower()
    return lowered.startswith(("všimli sme si", "pri takomto type hotela", "často sa tu", "oplatí sa preveriť", "niekedy sa"))


def make_audit_first_sentence(value: str, topic_hint: str = "") -> str:
    text = make_text_less_generic(sanitize_sentence(value, max_len=170))
    if not text:
        return ""
    if starts_with_audit_phrase(text):
        return text
    topic = extract_topic_phrase(text) or topic_hint
    if topic:
        return sanitize_sentence(
            f"Všimli sme si, že pri tomto type hotela sa oplatí preveriť oblasť {topic}.",
            max_len=170,
        )
    lowered = text[:1].lower() + text[1:] if text else ""
    return sanitize_sentence(
        f"Pri takomto type hotela býva užitočné preveriť, či {lowered.rstrip('.!?')}.",
        max_len=170,
    )


def make_why_more_concrete(value: str, bottleneck: str, pain_point: str) -> str:
    text = make_text_less_generic(sanitize_paragraph(value, max_len=260, max_sentences=2))
    if not text:
        text = ""
    generic_markers = [
        "dobrá zhoda s cieľovým typom hotela",
        "zaujímavý najmä",
        "obchodné možnosti",
        "príležitosti",
    ]
    if not text or any(marker in text.lower() for marker in generic_markers):
        parts = [bottleneck, pain_point]
        concrete = " ".join(part for part in parts if part).strip()
        if concrete:
            return sanitize_paragraph(concrete, max_len=260, max_sentences=2)
    return text


def expand_personalization_angle(value: str, positioning: str, bottleneck: str, pain_point: str) -> str:
    base = make_text_less_generic(sanitize_paragraph(value, max_len=320, max_sentences=3))
    sentences = [segment.strip() for segment in base.replace("?", ".").replace("!", ".").split(".") if segment.strip()]
    if len(sentences) >= 2:
        return base
    extra: list[str] = []
    if positioning:
        extra.append(f"Pri takomto profile sa často mieša viac typov záujmu naraz.")
    topic = extract_topic_phrase(bottleneck) or extract_topic_phrase(pain_point)
    if topic:
        extra.append(f"Oplatí sa preto najprv preveriť oblasť {topic}.")
    elif bottleneck:
        extra.append(make_audit_first_sentence(bottleneck))
    parts = [base] if base else []
    for item in extra:
        cleaned = sanitize_sentence(item, max_len=170)
        if cleaned and cleaned not in parts:
            parts.append(cleaned)
        if len(parts) >= 3:
            break
    joined = " ".join(parts).strip()
    return sanitize_paragraph(joined, max_len=320, max_sentences=3)


def enrich_call_hypothesis(value: str, decision_maker: str, bottleneck: str, pain_point: str) -> str:
    base = make_text_less_generic(sanitize_paragraph(value, max_len=380, max_sentences=4))
    sentences = [segment.strip() for segment in base.replace("?", ".").replace("!", ".").split(".") if segment.strip()]
    additions: list[str] = []
    topic = extract_topic_phrase(bottleneck) or extract_topic_phrase(pain_point)
    if topic:
        additions.append(f"Na začiatku hovoru by sa oplatilo potvrdiť práve oblasť {topic}.")
    if decision_maker:
        decision_hint = collapse_whitespace(decision_maker)
        for prefix in [
            "Prvým rozhodujúcim kontaktom bude pravdepodobne ",
            "Pravdepodobne ",
        ]:
            if decision_hint.startswith(prefix):
                decision_hint = decision_hint[len(prefix):]
        additions.append(f"Popri tom dáva zmysel zistiť, či to rieši skôr {decision_hint.rstrip('.')} alebo iný prevádzkový kontakt.")
    if len(sentences) < 2:
        additions.append("Už krátky prvý hovor by mal ukázať, kde sa mieša typ dopytu a kde vzniká manuálna záťaž.")
    joined = " ".join([base] + additions).strip()
    return sanitize_paragraph(joined, max_len=380, max_sentences=4)


def extract_topic_phrase(value: str) -> str:
    text = sanitize_sentence(value, max_len=140).rstrip(".!? ").strip()
    if not text:
        return ""
    lowered = text.lower()
    blockers = [
        " môže ",
        " môžu ",
        " môže byť ",
        " môžu byť ",
        " vie ",
        " vedia ",
        " brzdí ",
        " bráni ",
        " znižuje ",
    ]
    for prefix in ["Neistota ohľadom ", "Chýbajú potvrdené údaje o ", "Chýbajú údaje o "]:
        if text.startswith(prefix):
            topic = text[len(prefix):]
            lowered_topic = topic.lower()
            cut_idx = len(topic)
            for blocker in blockers:
                idx = lowered_topic.find(blocker.strip())
                if idx != -1:
                    cut_idx = min(cut_idx, idx)
            return topic[:cut_idx].strip(" ,;:-")
    return ""


def polish_hook_sentence(value: str) -> str:
    text = sanitize_sentence(value, max_len=120)
    if not text:
        return ""
    lowered = text.lower()
    ugly_markers = [
        "krátky postreh k ",
        "vidíme priestor spresniť detailov ",
        "vidíme priestor spresniť prevádzkových ",
        "vidíme priestor spresniť check-in/check-out",
    ]
    if any(marker in lowered for marker in ugly_markers):
        return ""
    return text


def is_generic_hook(value: str) -> bool:
    lowered = collapse_whitespace(value).lower()
    if not lowered:
        return True
    generic_markers = [
        "radi by sme",
        "rád by som",
        "môžeme pomôcť",
        "mohli pomôcť",
        "pomohli využiť",
        "predstavili možnosti spolupráce",
        "možnosti spolupráce",
        "naším riešením",
        "vzhľadom na",
        "zaujali",
        "zaujíma nás",
        "zaujímalo by nás",
        "krátky postreh k neistota",
        "krátky postreh k chýbajú",
        "krátky postreh k nejasn",
        "krátky postreh k tomu",
        "krátky postreh k tomu, ako",
        "krátky postreh k tomu, kde",
        "našimi riešeniami",
        "zvýšenie príjmov",
        "atraktívny cieľ",
        "silná icp",
    ]
    return any(marker in lowered for marker in generic_markers)


def sentence_to_hook_candidate(value: str) -> str:
    text = sanitize_sentence(value, max_len=110)
    if not text:
        return ""
    topic = extract_topic_phrase(text)
    if topic:
        if text.startswith("Neistota ohľadom "):
            return sanitize_sentence(f"Všimli sme si, že pri tomto type hotela sa oplatí preveriť verejné informácie v oblasti {topic}.", max_len=150)
        if text.startswith("Chýbajú potvrdené údaje o "):
            return sanitize_sentence(f"Všimli sme si, že pri tomto type hotela často chýbajú verejné údaje v oblasti {topic}.", max_len=150)
        if text.startswith("Chýbajú údaje o "):
            return sanitize_sentence(f"Často sa tu oplatí preveriť, či sa časť záujmu nestráca pri údajoch v oblasti {topic}.", max_len=150)

    base = text.rstrip(".!? ").strip()
    lowered = base[:1].lower() + base[1:] if base else ""

    replacements = [
        ("Neistota ohľadom ", "Vidíme priestor spresniť "),
        ("Chýbajú potvrdené údaje o ", "Vidíme priestor doplniť verejné údaje o "),
        ("Chýbajú údaje o ", "Vidíme priestor doplniť údaje o "),
        ("Nejasné sú ", "Vidíme priestor spresniť "),
        ("Nejasný je ", "Vidíme priestor spresniť "),
        ("Nejasná je ", "Vidíme priestor spresniť "),
    ]
    for source, target in replacements:
        if base.startswith(source):
            return sanitize_sentence(f"{target}{base[len(source):]}.", max_len=150)

    if lowered.startswith("neistota ohľadom "):
        return sanitize_sentence(f"Pri takomto type hotela býva užitočné preveriť {lowered[len('neistota ohľadom '):]}.", max_len=150)
    if lowered.startswith("chýbajú potvrdené údaje o "):
        return sanitize_sentence(f"Všimli sme si, že sa tu môže časť záujmu strácať pri verejných údajoch o {lowered[len('chýbajú potvrdené údaje o '):]}.", max_len=150)
    if lowered.startswith("chýbajú údaje o "):
        return sanitize_sentence(f"Oplatí sa preveriť, či sa časť záujmu nestráca pri údajoch o {lowered[len('chýbajú údaje o '):]}.", max_len=150)

    return sanitize_sentence(f"Pri takomto type hotela býva dôležité preveriť, či {lowered}.", max_len=150)


def build_fallback_hook(summary: str, bottleneck: str, pain_point: str) -> str:
    for candidate in [bottleneck, pain_point, summary]:
        hook = sentence_to_hook_candidate(candidate)
        if hook and not is_generic_hook(hook):
            return hook
    return "Pri takomto type hotela sa často oplatí preveriť, kde sa časť záujmu stráca ešte pred dopytom."


def sanitize_parsed_output(parsed: CommercialSynthesisOutput) -> CommercialSynthesisOutput:
    business_interest_summary = make_text_less_generic(sanitize_sentence(parsed.business_interest_summary, max_len=180))
    property_positioning_summary = sanitize_sentence(parsed.property_positioning_summary, max_len=180)
    main_bottleneck_hypothesis = make_text_less_generic(sanitize_sentence(parsed.main_bottleneck_hypothesis, max_len=150))
    pain_point_hypothesis = make_text_less_generic(sanitize_sentence(parsed.pain_point_hypothesis, max_len=150))
    why_commercially_interesting = make_why_more_concrete(
        parsed.why_commercially_interesting,
        bottleneck=main_bottleneck_hypothesis,
        pain_point=pain_point_hypothesis,
    )
    best_entry_angle = make_audit_first_sentence(parsed.best_entry_angle, topic_hint=extract_topic_phrase(main_bottleneck_hypothesis))
    recommended_hook = polish_hook_sentence(parsed.recommended_hook)
    if is_generic_hook(recommended_hook):
        recommended_hook = build_fallback_hook(
            summary=business_interest_summary,
            bottleneck=main_bottleneck_hypothesis,
            pain_point=pain_point_hypothesis,
        )
    else:
        recommended_hook = make_audit_first_sentence(recommended_hook, topic_hint=extract_topic_phrase(main_bottleneck_hypothesis))
    likely_decision_maker_hypothesis = sanitize_sentence(parsed.likely_decision_maker_hypothesis, max_len=160)
    personalization_angles: list[str] = []
    for item in (parsed.personalization_angles or [])[:3]:
        expanded = expand_personalization_angle(
            item,
            positioning=property_positioning_summary,
            bottleneck=main_bottleneck_hypothesis,
            pain_point=pain_point_hypothesis,
        )
        if expanded:
            personalization_angles.append(expanded)

    return CommercialSynthesisOutput(
        business_interest_summary=business_interest_summary,
        why_commercially_interesting=why_commercially_interesting,
        property_positioning_summary=property_positioning_summary,
        strengths=sanitize_list(parsed.strengths, max_items=4, max_len=140),
        opportunity_gaps=sanitize_list(parsed.opportunity_gaps, max_items=4, max_len=140),
        main_bottleneck_hypothesis=main_bottleneck_hypothesis,
        pain_point_hypothesis=pain_point_hypothesis,
        best_entry_angle=best_entry_angle,
        personalization_angles=personalization_angles,
        recommended_hook=recommended_hook,
        recommended_first_contact_route=sanitize_sentence(parsed.recommended_first_contact_route, max_len=140),
        likely_decision_maker_hypothesis=likely_decision_maker_hypothesis,
        demand_mix_hypothesis=sanitize_list(parsed.demand_mix_hypothesis, max_items=5, max_len=140),
        service_complexity_read=sanitize_sentence(parsed.service_complexity_read, max_len=160),
        commercial_complexity_read=sanitize_sentence(parsed.commercial_complexity_read, max_len=160),
        direct_booking_friction_hypothesis=sanitize_sentence(parsed.direct_booking_friction_hypothesis, max_len=160),
        contact_route_friction_hypothesis=sanitize_sentence(parsed.contact_route_friction_hypothesis, max_len=160),
        call_hypothesis=enrich_call_hypothesis(
            parsed.call_hypothesis,
            decision_maker=likely_decision_maker_hypothesis,
            bottleneck=main_bottleneck_hypothesis,
            pain_point=pain_point_hypothesis,
        ),
        verdict=collapse_whitespace(parsed.verdict),
        uncertainty_notes=sanitize_list(parsed.uncertainty_notes, max_items=5, max_len=140),
    )


def call_llm_synth(
    client: OpenAI,
    model: str,
    grounded_input: dict,
    max_output_tokens: int,
) -> CommercialSynthesisOutput:
    response = client.responses.parse(
        model=model,
        instructions=build_instructions(),
        input=build_prompt_payload(grounded_input),
        text_format=CommercialSynthesisOutput,
        max_output_tokens=max_output_tokens,
        temperature=0.2,
        store=False,
    )
    parsed = response.output_parsed
    if parsed is None:
        raise ValueError("LLM commercial synthesis vrátil prázdny parsed output.")
    return sanitize_parsed_output(parsed)


def build_output_artifact(
    row: pd.Series,
    source_file_stem: str,
    file_stem: str,
    parsed: CommercialSynthesisOutput,
    model: str,
) -> dict:
    return {
        "schema_version": COMMERCIAL_SYNTHESIS_SCHEMA_VERSION,
        "generated_at_utc": pd.Timestamp.utcnow().isoformat(),
        "account_id": build_account_id(row),
        "source_file": normalize_text(row.get("source_file")),
        "source_bundle_ref": str(build_artifact_path(SOURCE_BUNDLE_DIR, source_file_stem, file_stem)),
        "factual_enrichment_ref": str(build_artifact_path(FACTUAL_ENRICHMENT_DIR, source_file_stem, file_stem)),
        "model": model,
        **parsed.model_dump(),
    }


def save_output_artifact(artifact: dict, source_file_stem: str, file_stem: str) -> Path:
    output_dir = COMMERCIAL_SYNTHESIS_DIR / source_file_stem
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"{file_stem}.json"
    with output_path.open("w", encoding="utf-8") as file:
        json.dump(artifact, file, ensure_ascii=False, indent=2)
    return output_path


def main() -> None:
    load_environment()
    config = load_config().get("commercial_synthesis", {})
    processed_files = list_processed_files()
    if not processed_files:
        print("V data/processed nie je žiadny processed CSV súbor.")
        return

    preferred_source_file = normalize_text(os.getenv("COMMERCIAL_SOURCE_FILE"))
    processed_path = processed_files[-1]
    if preferred_source_file:
        for candidate in processed_files:
            if candidate.name == preferred_source_file:
                processed_path = candidate
                break

    processed_df = pd.read_csv(processed_path)
    for column in processed_df.columns:
        if processed_df[column].dtype == object:
            processed_df[column] = processed_df[column].apply(normalize_text)

    batch_limit_raw = normalize_text(os.getenv("COMMERCIAL_BATCH_LIMIT"))
    if batch_limit_raw:
        try:
            batch_limit = int(batch_limit_raw)
        except ValueError:
            batch_limit = 0
        if batch_limit > 0:
            processed_df = processed_df.head(batch_limit).copy()

    account_filter_raw = normalize_text(os.getenv("COMMERCIAL_ACCOUNT_IDS"))
    if account_filter_raw:
        allowed_ids = {
            item.strip()
            for item in account_filter_raw.split(",")
            if item.strip()
        }
        if allowed_ids and "account_id" in processed_df.columns:
            processed_df = processed_df[
                processed_df["account_id"].fillna("").astype(str).str.strip().isin(allowed_ids)
            ].copy()

    api_key = normalize_text(os.getenv("OPENAI_API_KEY"))
    if not api_key:
        print("Chýba OPENAI_API_KEY pre commercial_synthesizer.")
        return

    model = normalize_text(os.getenv("COMMERCIAL_MODEL")) or normalize_text(config.get("model")) or "gpt-4.1-mini"
    max_output_tokens_raw = normalize_text(os.getenv("COMMERCIAL_MAX_OUTPUT_TOKENS"))
    if max_output_tokens_raw:
        try:
            max_output_tokens = int(max_output_tokens_raw)
        except ValueError:
            max_output_tokens = int(config.get("max_output_tokens", 1200) or 1200)
    else:
        max_output_tokens = int(config.get("max_output_tokens", 1200) or 1200)
    source_file_stem = processed_path.stem.replace("_normalized_scored", "")
    client = OpenAI(api_key=api_key)

    output_paths: list[Path] = []
    errors: list[str] = []
    for _, row in processed_df.iterrows():
        file_stem = build_bundle_file_stem(row)
        source_bundle = load_json(build_artifact_path(SOURCE_BUNDLE_DIR, source_file_stem, file_stem))
        factual_enrichment = load_json(build_artifact_path(FACTUAL_ENRICHMENT_DIR, source_file_stem, file_stem))
        if not source_bundle or not factual_enrichment:
            continue

        grounded_input = build_grounded_input(row, source_bundle, factual_enrichment)
        try:
            parsed = call_llm_synth(
                client=client,
                model=model,
                grounded_input=grounded_input,
                max_output_tokens=max_output_tokens,
            )
            artifact = build_output_artifact(
                row=row,
                source_file_stem=source_file_stem,
                file_stem=file_stem,
                parsed=parsed,
                model=model,
            )
            output_paths.append(save_output_artifact(artifact, source_file_stem, file_stem))
        except Exception as error:
            errors.append(f"{build_account_id(row)}: {error}")

    print(f"Processed source: {processed_path.name}")
    print(f"Commercial synthesis count: {len(output_paths)}")
    if output_paths:
        print(f"Last output: {output_paths[-1]}")
    if errors:
        print("Errors:")
        for item in errors[:10]:
            print(f"- {item}")


if __name__ == "__main__":
    main()
