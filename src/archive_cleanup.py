import json
import shutil
from pathlib import Path

import yaml


PROJECT_CONFIG_PATH = Path("configs/project.yaml")
ARCHIVE_CLEANUP_REPORT_PATH = Path("data/qa/archive_cleanup_report.txt")


def load_project_config() -> dict:
    if not PROJECT_CONFIG_PATH.exists():
        return {}
    with PROJECT_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def cleanup_archive() -> dict:
    config = load_project_config()
    archive_root = Path(config.get("archive_folder", "data/archive"))
    keep_last = int(config.get("archive_keep_last_batches", 5))
    archive_dirs = sorted([path for path in archive_root.glob("*") if path.is_dir()])

    removed_dirs: list[str] = []
    if len(archive_dirs) > keep_last:
        for archive_dir in archive_dirs[: len(archive_dirs) - keep_last]:
            shutil.rmtree(archive_dir, ignore_errors=True)
            removed_dirs.append(str(archive_dir))

    result = {
        "archive_root": str(archive_root),
        "keep_last_batches": keep_last,
        "remaining_dirs": [str(path) for path in sorted([path for path in archive_root.glob("*") if path.is_dir()])],
        "removed_dirs": removed_dirs,
    }
    return result


def save_cleanup_report(result: dict) -> Path:
    ARCHIVE_CLEANUP_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        "Archive Cleanup Report",
        "",
        f"- archive_root: {result['archive_root']}",
        f"- keep_last_batches: {result['keep_last_batches']}",
        f"- removed_dirs_count: {len(result['removed_dirs'])}",
        f"- remaining_dirs_count: {len(result['remaining_dirs'])}",
        "",
        "Removed dirs",
    ]
    for directory in result["removed_dirs"] or ["none"]:
        lines.append(f"- {directory}")
    lines.extend(["", "Remaining dirs"])
    for directory in result["remaining_dirs"] or ["none"]:
        lines.append(f"- {directory}")
    ARCHIVE_CLEANUP_REPORT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return ARCHIVE_CLEANUP_REPORT_PATH


def main() -> None:
    result = cleanup_archive()
    report_path = save_cleanup_report(result)
    print(f"Archive cleanup report uložený do: {report_path}")
    print("\nNáhľad:\n")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
