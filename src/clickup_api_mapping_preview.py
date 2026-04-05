import json
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


CLICKUP_DIR = Path("outputs/clickup")
EMAIL_DIR = Path("outputs/email_drafts")
CONFIG_PATH = Path("configs/clickup_api_mapping.yaml")
QA_DIR = Path("data/qa")
OUTPUT_PATH = QA_DIR / "clickup_api_mapping_preview.json"
VALIDATION_PATH = QA_DIR / "clickup_api_mapping_validation.json"
DIFF_PATH = QA_DIR / "clickup_api_payload_diff.json"
SIDE_BY_SIDE_DIFF_PATH = QA_DIR / "clickup_export_mode_diff.json"


def get_latest_clickup_file() -> Optional[Path]:
    email_files = sorted(EMAIL_DIR.glob("*_email_drafts.csv"), key=lambda path: path.stat().st_mtime)
    if email_files:
        expected = CLICKUP_DIR / f"{Path(email_files[-1].name).stem}_clickup_import.csv"
        if expected.exists():
            return expected
    files = sorted(CLICKUP_DIR.glob("*_clickup_import.csv"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def get_latest_high_only_clickup_file() -> Optional[Path]:
    email_files = sorted(EMAIL_DIR.glob("*_email_drafts.csv"), key=lambda path: path.stat().st_mtime)
    if email_files:
        expected = CLICKUP_DIR / f"{Path(email_files[-1].name).stem}_clickup_import_high_only.csv"
        if expected.exists():
            return expected
    files = sorted(CLICKUP_DIR.glob("*_clickup_import_high_only.csv"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def get_latest_phase1_minimal_file() -> Optional[Path]:
    email_files = sorted(EMAIL_DIR.glob("*_email_drafts.csv"), key=lambda path: path.stat().st_mtime)
    if email_files:
        expected = CLICKUP_DIR / f"{Path(email_files[-1].name).stem}_clickup_phase1_minimal.csv"
        if expected.exists():
            return expected
    files = sorted(CLICKUP_DIR.glob("*_clickup_phase1_minimal.csv"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def get_latest_full_ranked_file() -> Optional[Path]:
    email_files = sorted(EMAIL_DIR.glob("*_email_drafts.csv"), key=lambda path: path.stat().st_mtime)
    if email_files:
        expected = CLICKUP_DIR / f"{Path(email_files[-1].name).stem}_clickup_full_ranked.csv"
        if expected.exists():
            return expected
    files = sorted(CLICKUP_DIR.glob("*_clickup_full_ranked.csv"), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def load_mapping_config() -> dict:
    if not CONFIG_PATH.exists():
        return {}
    with CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def build_mapping_preview() -> dict:
    clickup_path = get_latest_clickup_file()
    mapping_config = load_mapping_config().get("clickup_api_mapping", {})
    clickup_df = pd.read_csv(clickup_path) if clickup_path and clickup_path.exists() else pd.DataFrame()

    if clickup_df.empty:
        return {
            "source_csv": str(clickup_path) if clickup_path else "",
            "preview_rows": [],
            "note": "Neoverené: chýba ClickUp CSV.",
        }

    preview_rows = []
    for _, row in clickup_df.head(3).iterrows():
        mapped = {}
        for mapping_name, mapping_def in mapping_config.items():
            if mapping_name == "custom_fields":
                custom_payload = {}
                for custom_name, custom_def in mapping_def.items():
                    source_column = custom_def.get("source_column", "")
                    target_field = custom_def.get("target_field", "")
                    custom_payload[target_field] = str(row.get(source_column, "")).strip()
                mapped["custom_fields"] = custom_payload
                continue
            source_column = mapping_def.get("source_column", "")
            target_field = mapping_def.get("target_field", "")
            mapped[target_field] = str(row.get(source_column, "")).strip()
        preview_rows.append(mapped)

    return {
        "source_csv": str(clickup_path),
        "preview_rows": preview_rows,
        "note": "Návrh mapping preview bez ostrej ClickUp API integrácie.",
    }


def build_high_only_mapping_preview() -> dict:
    clickup_path = get_latest_high_only_clickup_file()
    mapping_config = load_mapping_config().get("clickup_api_mapping", {})
    clickup_df = pd.read_csv(clickup_path) if clickup_path and clickup_path.exists() else pd.DataFrame()

    if clickup_df.empty:
        return {
            "source_csv": str(clickup_path) if clickup_path else "",
            "preview_rows": [],
            "note": "Neoverené: chýba High-only ClickUp CSV.",
        }

    preview_rows = []
    for _, row in clickup_df.head(3).iterrows():
        mapped = {}
        for mapping_name, mapping_def in mapping_config.items():
            if mapping_name == "custom_fields":
                custom_payload = {}
                for _, custom_def in mapping_def.items():
                    source_column = custom_def.get("source_column", "")
                    target_field = custom_def.get("target_field", "")
                    custom_payload[target_field] = str(row.get(source_column, "")).strip()
                mapped["custom_fields"] = custom_payload
                continue
            source_column = mapping_def.get("source_column", "")
            target_field = mapping_def.get("target_field", "")
            mapped[target_field] = str(row.get(source_column, "")).strip()
        preview_rows.append(mapped)
    return {
        "source_csv": str(clickup_path),
        "preview_rows": preview_rows,
        "note": "Návrh High-only mapping preview bez ostrej ClickUp API integrácie.",
    }


def validate_mapping_preview(preview: dict) -> dict:
    required_top_fields = ["name", "description", "status", "priority", "custom_fields"]
    required_custom_fields = [
        "custom.hotel_name",
        "custom.city",
        "custom.priority_score",
        "custom.contact_phone",
        "custom.contact_website",
        "custom.subject_line",
        "custom.source_file",
    ]
    issues: list[str] = []
    preview_rows = preview.get("preview_rows", [])
    if not preview_rows:
        issues.append("missing_preview_rows")
    for index, row in enumerate(preview_rows):
        for field in required_top_fields:
            if field not in row:
                issues.append(f"row_{index}_missing_{field}")
        custom_fields = row.get("custom_fields", {})
        for field in required_custom_fields:
            if field not in custom_fields:
                issues.append(f"row_{index}_missing_{field}")

    return {
        "valid": len(issues) == 0,
        "preview_row_count": len(preview_rows),
        "issues": issues,
        "note": "Validation len nad preview payloadom, nie nad živou ClickUp API odpoveďou.",
    }


def build_payload_diff(full_preview: dict, high_preview: dict) -> dict:
    full_rows = full_preview.get("preview_rows", [])
    high_rows = high_preview.get("preview_rows", [])
    full_keys = set(full_rows[0].keys()) if full_rows else set()
    high_keys = set(high_rows[0].keys()) if high_rows else set()
    return {
        "full_preview_row_count": len(full_rows),
        "high_only_preview_row_count": len(high_rows),
        "same_top_level_keys": sorted(list(full_keys & high_keys)),
        "note": "Diff porovnáva shape payloadu, nie business obsah všetkých riadkov.",
    }


def build_export_mode_diff() -> dict:
    phase1_path = get_latest_phase1_minimal_file()
    full_ranked_path = get_latest_full_ranked_file()
    phase1_df = pd.read_csv(phase1_path) if phase1_path and phase1_path.exists() else pd.DataFrame()
    full_ranked_df = pd.read_csv(full_ranked_path) if full_ranked_path and full_ranked_path.exists() else pd.DataFrame()
    return {
        "phase1_minimal_csv": str(phase1_path) if phase1_path else "",
        "full_ranked_csv": str(full_ranked_path) if full_ranked_path else "",
        "phase1_minimal_columns": list(phase1_df.columns),
        "full_ranked_columns": list(full_ranked_df.columns),
        "phase1_minimal_row_count": len(phase1_df),
        "full_ranked_row_count": len(full_ranked_df),
        "phase1_only_columns": sorted(list(set(phase1_df.columns) - set(full_ranked_df.columns))),
        "full_only_columns": sorted(list(set(full_ranked_df.columns) - set(phase1_df.columns))),
        "shared_columns": sorted(list(set(phase1_df.columns) & set(full_ranked_df.columns))),
        "note": "Side-by-side diff medzi full_ranked a phase1_minimal export shape.",
    }


def save_mapping_preview(preview: dict) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
    return OUTPUT_PATH


def save_mapping_validation(validation: dict) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
    return VALIDATION_PATH


def save_payload_diff(diff: dict) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    DIFF_PATH.write_text(json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8")
    return DIFF_PATH


def save_export_mode_diff(diff: dict) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    SIDE_BY_SIDE_DIFF_PATH.write_text(json.dumps(diff, ensure_ascii=False, indent=2), encoding="utf-8")
    return SIDE_BY_SIDE_DIFF_PATH


def main() -> None:
    preview = build_mapping_preview()
    output_path = save_mapping_preview(preview)
    high_preview = build_high_only_mapping_preview()
    validation = validate_mapping_preview(preview)
    validation_path = save_mapping_validation(validation)
    diff = build_payload_diff(preview, high_preview)
    diff_path = save_payload_diff(diff)
    export_mode_diff = build_export_mode_diff()
    export_mode_diff_path = save_export_mode_diff(export_mode_diff)
    print(f"ClickUp API mapping preview uložený do: {output_path}")
    print(f"ClickUp API mapping validation uložený do: {validation_path}")
    print(f"ClickUp API payload diff uložený do: {diff_path}")
    print(f"ClickUp export mode diff uložený do: {export_mode_diff_path}")
    print("\nNáhľad:\n")
    print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
