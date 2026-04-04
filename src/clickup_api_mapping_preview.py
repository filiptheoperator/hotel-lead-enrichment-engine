import json
from pathlib import Path
from typing import Optional

import pandas as pd
import yaml


CLICKUP_DIR = Path("outputs/clickup")
CONFIG_PATH = Path("configs/clickup_api_mapping.yaml")
QA_DIR = Path("data/qa")
OUTPUT_PATH = QA_DIR / "clickup_api_mapping_preview.json"
VALIDATION_PATH = QA_DIR / "clickup_api_mapping_validation.json"


def get_latest_clickup_file() -> Optional[Path]:
    files = sorted(CLICKUP_DIR.glob("*_clickup_import.csv"))
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


def save_mapping_preview(preview: dict) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(preview, ensure_ascii=False, indent=2), encoding="utf-8")
    return OUTPUT_PATH


def save_mapping_validation(validation: dict) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    VALIDATION_PATH.write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding="utf-8")
    return VALIDATION_PATH


def main() -> None:
    preview = build_mapping_preview()
    output_path = save_mapping_preview(preview)
    validation = validate_mapping_preview(preview)
    validation_path = save_mapping_validation(validation)
    print(f"ClickUp API mapping preview uložený do: {output_path}")
    print(f"ClickUp API mapping validation uložený do: {validation_path}")
    print("\nNáhľad:\n")
    print(json.dumps(preview, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
