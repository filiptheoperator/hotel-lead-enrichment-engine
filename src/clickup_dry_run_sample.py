from pathlib import Path
from typing import Optional

import pandas as pd
import yaml

from clickup_export import get_clickup_export_mode, get_clickup_required_columns_for_mode


PROJECT_CONFIG_PATH = Path("configs/project.yaml")
CLICKUP_DIR = Path("outputs/clickup")
QA_DIR = Path("data/qa")
DRY_RUN_SAMPLE_PATH = QA_DIR / "clickup_import_dry_run_sample.csv"
DRY_RUN_NOTES_PATH = QA_DIR / "clickup_import_dry_run_notes.txt"
HIGH_DRY_RUN_SAMPLE_PATH = QA_DIR / "clickup_import_dry_run_sample_high_only.csv"
HIGH_DRY_RUN_NOTES_PATH = QA_DIR / "clickup_import_dry_run_notes_high_only.txt"


def load_project_config() -> dict:
    if not PROJECT_CONFIG_PATH.exists():
        return {}
    with PROJECT_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def get_latest_clickup_file() -> Optional[Path]:
    files = sorted(CLICKUP_DIR.glob("*_clickup_import.csv"))
    return files[-1] if files else None


def normalize_priority(value: object) -> str:
    if pd.isna(value):
        return ""
    text = str(value).strip()
    if not text:
        return ""
    try:
        return str(int(float(text)))
    except ValueError:
        return text


def build_dry_run_sample() -> tuple[pd.DataFrame, list[str], str]:
    config = load_project_config()
    export_mode = get_clickup_export_mode(config)
    required_columns = set(get_clickup_required_columns_for_mode(export_mode))
    sample_size = int(config.get("clickup_dry_run_sample_size", 5))
    clickup_path = get_latest_clickup_file()
    if clickup_path is None or not clickup_path.exists():
        return pd.DataFrame(), ["Chýba ClickUp CSV artifact."], ""

    clickup_df = pd.read_csv(clickup_path)
    normalized_priority = (
        clickup_df["Priority"].apply(normalize_priority)
        if "Priority" in clickup_df.columns
        else pd.Series("", index=clickup_df.index, dtype="object")
    )

    ready_mask = (
        clickup_df["Task name"].fillna("").astype(str).str.strip().ne("")
        & clickup_df["Status"].fillna("").astype(str).str.strip().ne("")
        & normalized_priority.isin(["", "1", "2", "3", "4"])
    )
    if "Description content" in required_columns and "Description content" in clickup_df.columns:
        ready_mask = ready_mask & clickup_df["Description content"].fillna("").astype(str).str.strip().ne("")
    sample_df = clickup_df[ready_mask].head(sample_size).copy()

    notes = [
        f"Zdrojový ClickUp CSV: {clickup_path}",
        f"ClickUp export mode: {export_mode}",
        f"Požadovaná veľkosť sample: {sample_size}",
        f"Vybraná veľkosť sample: {len(sample_df)}",
        "Toto je suchý importný sample, nie ostrý import.",
        "Field-by-field check template:",
        "1. Task name: nie je prázdny a zodpovedá hotelu.",
        "2. Description content: kontroluj len pri full_ranked režime.",
        "3. Status: je bezpečne mapovaný na ClickUp import status.",
        "4. Priority: je v sete 1-4 alebo prázdne podľa pravidla.",
        "5. Hotel name / City: sedí s leadom.",
        "6. Contact phone / Contact website: neobsahujú zjavný parsing šum.",
        "7. Subject line: je použiteľný pre outreach task.",
        "Neoverené: správanie konkrétneho ClickUp workspace pri importe.",
    ]
    return sample_df, notes, str(clickup_path)


def save_dry_run_sample(sample_df: pd.DataFrame, notes: list[str]) -> tuple[Path, Path]:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    sample_df.to_csv(DRY_RUN_SAMPLE_PATH, index=False)
    DRY_RUN_NOTES_PATH.write_text("\n".join(notes), encoding="utf-8")
    return DRY_RUN_SAMPLE_PATH, DRY_RUN_NOTES_PATH


def build_high_only_dry_run_sample() -> tuple[pd.DataFrame, list[str]]:
    sample_df, _, _ = build_dry_run_sample()
    high_sample_df = sample_df.copy()
    if "Priority" in high_sample_df.columns:
        high_sample_df = high_sample_df[
            high_sample_df["Priority"].fillna("").astype(str).str.strip().isin(["2", "2.0"])
        ].copy()
    notes = [
        "High-only dry run sample.",
        f"Vybraná veľkosť High-only sample: {len(high_sample_df)}",
        "Field-by-field check template platí rovnako ako pre full sample.",
        "Neoverené: správanie konkrétneho ClickUp workspace pri importe.",
    ]
    return high_sample_df, notes


def save_high_only_dry_run_sample(sample_df: pd.DataFrame, notes: list[str]) -> tuple[Path, Path]:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    sample_df.to_csv(HIGH_DRY_RUN_SAMPLE_PATH, index=False)
    HIGH_DRY_RUN_NOTES_PATH.write_text("\n".join(notes), encoding="utf-8")
    return HIGH_DRY_RUN_SAMPLE_PATH, HIGH_DRY_RUN_NOTES_PATH


def main() -> None:
    sample_df, notes, _ = build_dry_run_sample()
    sample_path, notes_path = save_dry_run_sample(sample_df, notes)
    high_sample_df, high_notes = build_high_only_dry_run_sample()
    high_sample_path, high_notes_path = save_high_only_dry_run_sample(high_sample_df, high_notes)
    print(f"ClickUp dry run sample uložený do: {sample_path}")
    print(f"ClickUp dry run notes uložené do: {notes_path}")
    print(f"ClickUp high-only dry run sample uložený do: {high_sample_path}")
    print(f"ClickUp high-only dry run notes uložené do: {high_notes_path}")
    print("\nNáhľad:\n")
    if sample_df.empty:
        print("Sample je prázdny.")
    else:
        print(sample_df.head(5).to_string(index=False))


if __name__ == "__main__":
    main()
