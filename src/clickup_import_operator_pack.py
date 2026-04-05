import json
import shutil
from pathlib import Path
from typing import Optional


QA_DIR = Path("data/qa")
CLICKUP_DIR = Path("outputs/clickup")
PACK_DIR = QA_DIR / "clickup_operator_pack"
PACK_MANIFEST_PATH = PACK_DIR / "clickup_operator_pack_manifest.json"


def safe_copy(path: Path, target_dir: Path) -> None:
    if path.exists():
        shutil.copy2(path, target_dir / path.name)


def get_latest(pattern: str, folder: Path) -> Optional[Path]:
    files = sorted(folder.glob(pattern), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def build_operator_pack() -> dict:
    PACK_DIR.mkdir(parents=True, exist_ok=True)

    phase1 = get_latest("*_clickup_phase1_minimal.csv", CLICKUP_DIR)
    full_ranked = get_latest("*_clickup_full_ranked.csv", CLICKUP_DIR)
    default_import = get_latest("*_clickup_import.csv", CLICKUP_DIR)

    files_to_copy = [
        phase1,
        full_ranked,
        default_import,
        get_latest("*_top_20_export.csv", Path("outputs/master")),
        get_latest("*_operator_shortlist.csv", Path("outputs/master")),
        QA_DIR / "clickup_import_dry_run_sample.csv",
        QA_DIR / "clickup_import_dry_run_notes.txt",
        QA_DIR / "clickup_api_mapping_preview_phase1_minimal.json",
        QA_DIR / "clickup_api_mapping_preview_full_ranked.json",
        QA_DIR / "clickup_api_mapping_validation_phase1_minimal.json",
        QA_DIR / "clickup_api_mapping_validation_full_ranked.json",
        QA_DIR / "clickup_export_mode_diff.json",
        QA_DIR / "clickup_import_gate.json",
        QA_DIR / "phase1_import_checklist.json",
        QA_DIR / "full_ranked_review_checklist.json",
        QA_DIR / "phase1_import_decision.json",
        QA_DIR / "full_ranked_review_decision.json",
        QA_DIR / "phase1_import_pass_fail_summary.txt",
        QA_DIR / "full_ranked_review_pass_fail_summary.txt",
        QA_DIR / "top_20_reasons_summary.txt",
        QA_DIR / "review_bucket_reasons_summary.txt",
        QA_DIR / "top_20_operator_notes_template.csv",
        QA_DIR / "review_followup_queue.csv",
        QA_DIR / "clickup_import_packet_index.txt",
        QA_DIR / "operator_pack_health.json",
        QA_DIR / "phase1_import_row_sample.json",
        QA_DIR / "full_ranked_row_sample.json",
        QA_DIR / "rank_bucket_top_examples.txt",
        QA_DIR / "review_bucket_top_examples.txt",
        QA_DIR / "rank_bucket_summary.json",
        QA_DIR / "website_quality_summary.json",
        QA_DIR / "contact_gap_summary.json",
        QA_DIR / "operator_import_command_sheet.txt",
        QA_DIR / "clickup_import_preflight.json",
        QA_DIR / "run_summary.txt",
    ]

    for path in files_to_copy:
        if path is not None:
            safe_copy(path, PACK_DIR)

    manifest = {
        "pack_dir": str(PACK_DIR),
        "phase1_minimal_csv": str(phase1) if phase1 else "",
        "full_ranked_csv": str(full_ranked) if full_ranked else "",
        "default_import_csv": str(default_import) if default_import else "",
        "included_files": sorted([item.name for item in PACK_DIR.iterdir() if item.is_file()]),
    }
    PACK_MANIFEST_PATH.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return manifest


def main() -> None:
    manifest = build_operator_pack()
    print(f"ClickUp operator pack uložený do: {manifest['pack_dir']}")
    print(json.dumps(manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
