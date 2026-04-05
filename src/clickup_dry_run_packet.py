import json
import shutil
from pathlib import Path
from typing import Optional


QA_DIR = Path("data/qa")
PACK_DIR = QA_DIR / "clickup_dry_run_packet"


def safe_copy(path: Path, target_dir: Path) -> None:
    if path.exists():
        shutil.copy2(path, target_dir / path.name)


def optional_path(path_str: str) -> Optional[Path]:
    if not path_str:
        return None
    path = Path(path_str)
    return path if path.exists() else None


def main() -> None:
    PACK_DIR.mkdir(parents=True, exist_ok=True)
    run_manifest_path = QA_DIR / "run_manifest.json"
    manifest = json.loads(run_manifest_path.read_text(encoding="utf-8")) if run_manifest_path.exists() else {}
    artifacts = manifest.get("artifacts", {})

    files_to_copy = [
        optional_path(artifacts.get("clickup_import_csv", "")),
        optional_path(artifacts.get("clickup_phase1_minimal_csv", "")),
        optional_path(artifacts.get("clickup_full_ranked_csv", "")),
        QA_DIR / "clickup_import_dry_run_sample.csv",
        QA_DIR / "clickup_import_dry_run_notes.txt",
        QA_DIR / "clickup_api_mapping_validation_phase1_minimal.json",
        QA_DIR / "clickup_api_mapping_validation_full_ranked.json",
        QA_DIR / "clickup_export_mode_diff.json",
        QA_DIR / "phase1_import_checklist.json",
        QA_DIR / "full_ranked_review_checklist.json",
        QA_DIR / "operator_import_command_sheet.txt",
        QA_DIR / "run_summary.txt",
    ]

    for path in files_to_copy:
        if path is not None:
            safe_copy(path, PACK_DIR)

    packet_manifest = {
        "packet_dir": str(PACK_DIR),
        "source_run_manifest": str(run_manifest_path) if run_manifest_path.exists() else "",
        "included_files": sorted([item.name for item in PACK_DIR.iterdir() if item.is_file()]),
    }
    (PACK_DIR / "clickup_dry_run_packet_manifest.json").write_text(
        json.dumps(packet_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"ClickUp dry run packet uložený do: {PACK_DIR}")
    print(json.dumps(packet_manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
