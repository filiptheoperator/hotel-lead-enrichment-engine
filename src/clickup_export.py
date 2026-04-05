from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


EMAIL_OUTPUT_DIR = Path("outputs/email_drafts")
CLICKUP_OUTPUT_DIR = Path("outputs/clickup")
ENRICHMENT_OUTPUT_DIR = Path("outputs/enrichment")
PROJECT_CONFIG_PATH = Path("configs/project.yaml")
CLICKUP_REQUIRED_COLUMNS = ["Task name"]
CLICKUP_SUPPORTED_CORE_COLUMNS = [
    "Task name",
    "Description content",
    "Status",
    "Priority",
]
CLICKUP_ALLOWED_PRIORITY_VALUES = {"", "1", "2", "3", "4"}
CLICKUP_EXPORT_MODES = {"phase1_minimal", "full_ranked"}
CLICKUP_PHASE1_REQUIRED_FIELDS = [
    "Task name",
    "Status",
    "Priority",
    "Account Status",
    "Hotel name",
    "Country",
    "City / Region",
    "Priority score",
    "Priority Level",
    "ICP Fit",
    "Subject line",
    "Source file",
]


def list_email_draft_files(email_dir: Path = EMAIL_OUTPUT_DIR) -> list[Path]:
    if not email_dir.exists():
        return []
    return sorted(email_dir.glob("*_email_drafts.csv"), key=lambda path: path.stat().st_mtime)


def get_preferred_email_draft_file() -> Optional[Path]:
    enrichment_files = sorted(
        ENRICHMENT_OUTPUT_DIR.glob("*_enriched.csv"),
        key=lambda path: path.stat().st_mtime,
    )
    if enrichment_files:
        expected = EMAIL_OUTPUT_DIR / f"{Path(enrichment_files[-1].name).stem}_email_drafts.csv"
        if expected.exists():
            return expected
    email_files = list_email_draft_files()
    return email_files[-1] if email_files else None


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def load_project_config(config_path: Path = PROJECT_CONFIG_PATH) -> dict:
    if not config_path.exists():
        return {}
    with config_path.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def get_clickup_export_mode(project_config: Optional[dict] = None) -> str:
    config = project_config or load_project_config()
    export_mode = normalize_text(config.get("clickup_export_mode")) or "phase1_minimal"
    return export_mode if export_mode in CLICKUP_EXPORT_MODES else "phase1_minimal"


def get_clickup_required_columns_for_mode(export_mode: str) -> list[str]:
    if export_mode == "phase1_minimal":
        return CLICKUP_PHASE1_REQUIRED_FIELDS
    return ["Task name", "Description content", "Status", "Priority"]


def build_clickup_mode_notes(export_mode: str) -> str:
    if export_mode == "phase1_minimal":
        return "Phase 1 minimal export: jednoduchý ClickUp account layer bez dlhého enrichment textu."
    return "Full ranked export: bohatší review export s Description content."


def build_clickup_task_name(row: pd.Series) -> str:
    hotel_name = row["hotel_name"] or "Hotel lead"
    return f"Lead outreach - {hotel_name}"


def map_clickup_priority(priority_band: str) -> str:
    normalized = normalize_text(priority_band).lower()
    if normalized == "high":
        return "2"
    if normalized in {"medium-high", "medium high"}:
        return "2"
    if normalized == "medium":
        return "3"
    if normalized == "low":
        return "4"
    return ""


def build_clickup_status(row: pd.Series) -> str:
    return "to do"


def normalize_rooms_range(row: pd.Series) -> str:
    raw_value = normalize_text(row.get("rooms_range"))
    return raw_value


def normalize_ota_dependency_signal(value: object) -> str:
    text = normalize_text(value)
    normalized = text.lower()
    if normalized == "high":
        return "High"
    if normalized == "medium":
        return "Medium"
    if normalized in {"low", "low visible"}:
        return "Low"
    if normalized in {"", "unknown", "unknown / likely higher ota reliance"}:
        return "Unknown"
    return "Unknown"


def normalize_direct_booking_weakness(value: object) -> str:
    text = normalize_text(value)
    normalized = text.lower()
    if normalized == "strong":
        return "Strong"
    if normalized in {"medium", "needs direct booking clarity"}:
        return "Medium"
    if normalized == "low":
        return "Low"
    if normalized in {"", "unknown", "website missing"}:
        return "Unknown"
    return "Unknown"


def build_account_status(row: pd.Series) -> str:
    reply_outcome = normalize_text(row.get("reply_outcome")).lower()
    if reply_outcome not in {"", "no_reply", "pending"}:
        return "Activated"
    if normalize_text(row.get("non_icp_but_keep")).lower() == "yes":
        return "Not a Fit"
    if normalize_text(row.get("review_flag")) == "yes":
        return "Researching"
    if normalize_text(row.get("priority_band")) in {"High", "Medium-High"}:
        return "Prioritized"
    return "Parked"


def build_clickup_notes(row: pd.Series) -> str:
    parts = [
        f"Account ID: {normalize_text(row.get('account_id', ''))}",
        f"Hotel: {normalize_text(row.get('hotel_name', ''))}",
        f"Krajina: {normalize_text(row.get('country_code', ''))}",
        f"Mesto: {normalize_text(row.get('city', ''))}",
        f"Hotel type: {normalize_text(row.get('hotel_type_class', ''))}",
        f"Independent / Chain: {normalize_text(row.get('independent_chain_class', ''))}",
        f"Priorita band: {normalize_text(row.get('priority_band', ''))}",
        f"Skóre: {normalize_text(row.get('priority_score', ''))}",
        f"Ranking score: {normalize_text(row.get('ranking_score', ''))}",
        f"Rank bucket: {normalize_text(row.get('rank_bucket', ''))}",
        f"ICP fit score: {normalize_text(row.get('icp_fit_score', ''))}",
        f"ICP fit class: {normalize_text(row.get('icp_fit_class', ''))}",
        f"Fit confidence: {normalize_text(row.get('fit_confidence', ''))}",
        f"Why not top tier: {normalize_text(row.get('why_not_top_tier', ''))}",
        f"Chain signal confidence: {normalize_text(row.get('chain_signal_confidence', ''))}",
        f"Review flag: {normalize_text(row.get('review_flag', ''))}",
        f"Review reason: {normalize_text(row.get('review_reason', ''))}",
        f"Dedupe status: {normalize_text(row.get('dedupe_status', ''))}",
        f"Manual merge candidate: {normalize_text(row.get('manual_merge_candidate', ''))}",
        f"Ranking reason: {normalize_text(row.get('ranking_reason', ''))}",
        f"Web: {normalize_text(row.get('website', '')) or 'Verejne nepotvrdené'}",
        f"Telefón: {normalize_text(row.get('phone', '')) or 'Verejne nepotvrdené'}",
        f"OTA dependency signal: {normalize_text(row.get('ota_dependency_signal_label', ''))}",
        f"Direct booking weakness: {normalize_text(row.get('direct_booking_weakness', ''))}",
        f"Email angle: {normalize_text(row.get('email_angle', ''))}",
        f"CTA type: {normalize_text(row.get('cta_type', ''))}",
        f"Variant ID: {normalize_text(row.get('variant_id', ''))}",
        f"Test batch: {normalize_text(row.get('test_batch', ''))}",
        f"Reply outcome: {normalize_text(row.get('reply_outcome', ''))}",
        "",
        f"Email hook: {normalize_text(row.get('email_hook', row.get('hook', '')))}",
        f"Give-first insight: {normalize_text(row.get('give_first_insight', ''))}",
        f"Main observed issue: {normalize_text(row.get('main_observed_issue', ''))}",
        f"Proof snippet: {normalize_text(row.get('proof_snippet', ''))}",
        f"Micro CTA: {normalize_text(row.get('micro_cta', ''))}",
        f"Primary email goal: {normalize_text(row.get('primary_email_goal', ''))}",
        "",
        "Cold email:",
        normalize_text(row.get("cold_email", "")),
        "",
        "Follow-up email:",
        normalize_text(row.get("followup_email", "")),
    ]
    return "\n".join(parts)


def build_clickup_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    export_df = df.copy()

    for column in export_df.columns:
        if export_df[column].dtype == object:
            export_df[column] = export_df[column].apply(normalize_text)

    for column in [
        "account_id",
        "country_code",
        "hotel_type_class",
        "ranking_score",
        "icp_fit_score",
        "icp_fit_class",
        "fit_confidence",
        "ranking_reason",
        "review_flag",
        "review_reason",
        "direct_booking_weakness",
        "ota_dependency_signal_label",
        "manual_merge_candidate",
        "active_icp_profile",
        "rank_bucket",
        "rank_bucket_reason",
        "why_not_top_tier",
        "chain_signal_confidence",
    ]:
        if column not in export_df.columns:
            export_df[column] = ""

    for column in [
        "email_angle",
        "cta_type",
        "variant_id",
        "test_batch",
        "reply_outcome",
        "give_first_insight",
        "main_observed_issue",
        "email_hook",
        "micro_cta",
        "proof_snippet",
        "primary_email_goal",
    ]:
        if column in export_df.columns:
            export_df[column] = export_df[column].apply(normalize_text)

    export_df["task_name"] = export_df.apply(build_clickup_task_name, axis=1)
    export_df["clickup_priority"] = export_df["priority_band"].apply(map_clickup_priority)
    export_df["clickup_status"] = export_df.apply(build_clickup_status, axis=1)
    export_df["account_status"] = export_df.apply(build_account_status, axis=1)
    export_df["contact_phone"] = export_df["phone"]
    export_df["contact_website"] = export_df["website"]
    export_df["source"] = export_df["source_file"].apply(
        lambda value: f"Raw lead sheet: {value}" if normalize_text(value) else "Raw lead sheet"
    )
    export_df["task_notes"] = export_df.apply(build_clickup_notes, axis=1)
    export_df["rooms_range"] = export_df.apply(normalize_rooms_range, axis=1)
    export_df["priority_level"] = export_df["priority_band"]
    export_df["icp_fit"] = export_df["icp_fit_class"]
    export_df["ota_dependency_signal"] = export_df["ota_dependency_signal_label"].apply(normalize_ota_dependency_signal)
    export_df["city_region"] = export_df["city"]
    export_df["direct_booking_weakness"] = export_df["direct_booking_weakness"].apply(normalize_direct_booking_weakness)
    export_df["main_pain_hypothesis"] = export_df["main_observed_issue"]
    export_df = export_df.sort_values(
        by=["ranking_score", "priority_score", "hotel_name"],
        ascending=[False, False, True],
    ).reset_index(drop=True)

    return export_df[
        [
            "task_name",
            "task_notes",
            "clickup_status",
            "clickup_priority",
            "account_id",
            "account_status",
            "hotel_name",
            "country_code",
            "city_region",
            "hotel_type_class",
            "rooms_range",
            "source",
            "priority_score",
            "priority_level",
            "icp_fit",
            "rank_bucket",
            "rank_bucket_reason",
            "why_not_top_tier",
            "chain_signal_confidence",
            "ranking_reason",
            "ota_dependency_signal",
            "direct_booking_weakness",
            "main_pain_hypothesis",
            "contact_phone",
            "contact_website",
            "subject_line",
            "source_file",
            "email_angle",
            "cta_type",
            "variant_id",
            "test_batch",
            "reply_outcome",
            "give_first_insight",
            "main_observed_issue",
            "email_hook",
            "micro_cta",
            "proof_snippet",
            "primary_email_goal",
        ]
    ].rename(
        columns={
            "task_name": "Task name",
            "task_notes": "Description content",
            "clickup_status": "Status",
            "clickup_priority": "Priority",
            "account_id": "Account ID",
            "account_status": "Account Status",
            "hotel_name": "Hotel name",
            "country_code": "Country",
            "city_region": "City / Region",
            "hotel_type_class": "Hotel Type",
            "rooms_range": "Rooms Range",
            "source": "Source",
            "priority_score": "Priority score",
            "priority_level": "Priority Level",
            "icp_fit": "ICP Fit",
            "rank_bucket": "Rank bucket",
            "rank_bucket_reason": "Rank bucket reason",
            "why_not_top_tier": "Why not top tier",
            "chain_signal_confidence": "Chain signal confidence",
            "ranking_reason": "Ranking reason",
            "ota_dependency_signal": "OTA Dependency Signal",
            "direct_booking_weakness": "Direct Booking Weakness",
            "main_pain_hypothesis": "Main Pain Hypothesis",
            "contact_phone": "Contact phone",
            "contact_website": "Contact website",
            "subject_line": "Subject line",
            "source_file": "Source file",
            "email_angle": "Email angle",
            "cta_type": "CTA type",
            "variant_id": "Variant ID",
            "test_batch": "Test batch",
            "reply_outcome": "Reply outcome",
            "give_first_insight": "Give-first insight",
            "main_observed_issue": "Main observed issue",
            "email_hook": "Email hook",
            "micro_cta": "Micro CTA",
            "proof_snippet": "Proof snippet",
            "primary_email_goal": "Primary email goal",
        }
    ).copy()


def build_clickup_phase1_minimal_dataframe(df: pd.DataFrame) -> pd.DataFrame:
    full_df = build_clickup_dataframe(df)
    minimal_columns = [
        "Task name",
        "Status",
        "Priority",
        "Account Status",
        "Hotel name",
        "Country",
        "City / Region",
        "Hotel Type",
        "Rooms Range",
        "Contact website",
        "Source",
        "Priority score",
        "Priority Level",
        "ICP Fit",
        "OTA Dependency Signal",
        "Direct Booking Weakness",
        "Main Pain Hypothesis",
        "Subject line",
        "Source file",
    ]
    return full_df[[column for column in minimal_columns if column in full_df.columns]].copy()


def validate_clickup_import_readiness(df: pd.DataFrame, export_mode: str = "phase1_minimal") -> list[str]:
    issues: list[str] = []

    required_columns = get_clickup_required_columns_for_mode(export_mode)
    missing_required_columns = [column for column in required_columns if column not in df.columns]
    if missing_required_columns:
        issues.append(
            "Chýbajú povinné ClickUp stĺpce: " + ", ".join(missing_required_columns)
        )
        return issues

    missing_supported_core_columns = [
        column for column in CLICKUP_SUPPORTED_CORE_COLUMNS if column not in df.columns
    ]
    if export_mode != "phase1_minimal" and missing_supported_core_columns:
        issues.append(
            "Chýbajú odporúčané ClickUp core stĺpce: "
            + ", ".join(missing_supported_core_columns)
        )

    if len(df) > 10000:
        issues.append("CSV prekračuje ClickUp import limit 10 000 riadkov.")

    empty_task_name_count = (
        df["Task name"].fillna("").astype(str).str.strip().eq("").sum()
    )
    if empty_task_name_count:
        issues.append(f"Task name chýba v {int(empty_task_name_count)} riadkoch.")

    if "Priority" in df.columns:
        normalized_priorities = (
            df["Priority"]
            .fillna("")
            .astype(str)
            .str.strip()
            .map(lambda value: str(int(float(value))) if value not in {"", "nan"} else "")
        )
        invalid_priority_count = (~normalized_priorities.isin(CLICKUP_ALLOWED_PRIORITY_VALUES)).sum()
        if invalid_priority_count:
            issues.append(
                f"Priority má neplatnú ClickUp hodnotu v {int(invalid_priority_count)} riadkoch."
            )

    if "Status" in df.columns:
        empty_status_count = df["Status"].fillna("").astype(str).str.strip().eq("").sum()
        if empty_status_count:
            issues.append(f"Status chýba v {int(empty_status_count)} riadkoch.")

    return issues


def save_clickup_file(df: pd.DataFrame, source_file: str) -> Path:
    CLICKUP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLICKUP_OUTPUT_DIR / f"{Path(source_file).stem}_clickup_import.csv"
    df.to_csv(output_path, index=False)
    return output_path


def save_clickup_full_ranked_file(df: pd.DataFrame, source_file: str) -> Path:
    CLICKUP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLICKUP_OUTPUT_DIR / f"{Path(source_file).stem}_clickup_full_ranked.csv"
    df.to_csv(output_path, index=False)
    return output_path


def save_clickup_phase1_minimal_file(df: pd.DataFrame, source_file: str) -> Path:
    CLICKUP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLICKUP_OUTPUT_DIR / f"{Path(source_file).stem}_clickup_phase1_minimal.csv"
    df.to_csv(output_path, index=False)
    return output_path


def save_high_leads_clickup_file(df: pd.DataFrame, source_file: str) -> Path:
    CLICKUP_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    output_path = CLICKUP_OUTPUT_DIR / f"{Path(source_file).stem}_clickup_import_high_only.csv"
    df.to_csv(output_path, index=False)
    return output_path


def main() -> None:
    first_file = get_preferred_email_draft_file()

    if first_file is None:
        print("V priečinku outputs/email_drafts nie je žiadny email draft CSV súbor.")
        return

    try:
        email_df = pd.read_csv(first_file)
    except Exception as error:
        print(f"Nepodarilo sa načítať email draft CSV súbor: {first_file.name}")
        print(f"Dôvod: {error}")
        return

    clickup_df = build_clickup_dataframe(email_df)
    clickup_phase1_minimal_df = build_clickup_phase1_minimal_dataframe(email_df)
    high_clickup_df = build_clickup_dataframe(
        email_df[email_df["priority_band"].fillna("").astype(str).str.strip().eq("High")].copy()
    )
    project_config = load_project_config()
    clickup_export_mode = get_clickup_export_mode(project_config)
    default_export_df = clickup_phase1_minimal_df if clickup_export_mode == "phase1_minimal" else clickup_df
    readiness_issues = validate_clickup_import_readiness(default_export_df, clickup_export_mode)
    output_path = save_clickup_file(default_export_df, first_file.name)
    full_ranked_output_path = save_clickup_full_ranked_file(clickup_df, first_file.name)
    minimal_output_path = save_clickup_phase1_minimal_file(clickup_phase1_minimal_df, first_file.name)
    high_output_path = save_high_leads_clickup_file(high_clickup_df, first_file.name)

    print(f"Načítaný email draft súbor: {first_file.name}")
    print(f"Počet riadkov: {len(clickup_df)}")
    print(f"Default export mode: {clickup_export_mode}")
    print(build_clickup_mode_notes(clickup_export_mode))
    print(f"Výstup uložený do: {output_path}")
    print(f"Full ranked výstup uložený do: {full_ranked_output_path}")
    print(f"Phase 1 minimal výstup uložený do: {minimal_output_path}")
    print(f"High-only výstup uložený do: {high_output_path}")
    if readiness_issues:
        print("\nClickUp import readiness:\n")
        for issue in readiness_issues:
            print(f"- {issue}")
    else:
        print("\nClickUp import readiness:\n")
        print("- OK: export vyzerá pripravený pre Spreadsheet importer.")
    print("\nNáhľad prvých 5 riadkov:\n")
    print(
        clickup_df[
            [
                "Task name",
                "Priority",
                "Subject line",
            ]
        ]
        .head(5)
        .to_string(index=False)
    )


if __name__ == "__main__":
    main()
