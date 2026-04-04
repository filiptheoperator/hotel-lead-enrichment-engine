import json
import shutil
from pathlib import Path

import yaml


PROJECT_CONFIG_PATH = Path("configs/project.yaml")
QA_DIR = Path("data/qa")
RUN_MANIFEST_PATH = QA_DIR / "run_manifest.json"


def load_project_config() -> dict:
    if not PROJECT_CONFIG_PATH.exists():
        return {}
    with PROJECT_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_manifest() -> dict:
    if not RUN_MANIFEST_PATH.exists():
        return {}
    with RUN_MANIFEST_PATH.open("r", encoding="utf-8") as file:
        return json.load(file)


def build_archive_dirname(manifest: dict) -> str:
    source_files = manifest.get("batch", {}).get("source_files", [])
    batch_label = Path(source_files[0]).stem if source_files else "unknown_batch"
    generated_at = str(manifest.get("generated_at", ""))
    safe_generated_at = generated_at.replace(":", "-").replace("+", "_").replace("T", "__")
    return f"{batch_label}__{safe_generated_at}"


def archive_run_artifacts() -> Path:
    project_config = load_project_config()
    archive_root = Path(project_config.get("archive_folder", "data/archive"))
    manifest = load_manifest()
    archive_dir = archive_root / build_archive_dirname(manifest)
    archive_dir.mkdir(parents=True, exist_ok=True)

    artifact_paths = manifest.get("artifacts", {})
    copied_files: dict[str, str] = {}
    for artifact_name, artifact_path in artifact_paths.items():
        if not artifact_path:
            continue
        source_path = Path(artifact_path)
        if not source_path.exists():
            continue
        destination_path = archive_dir / source_path.name
        shutil.copy2(source_path, destination_path)
        copied_files[artifact_name] = str(destination_path)

    if RUN_MANIFEST_PATH.exists():
        run_manifest_destination = archive_dir / RUN_MANIFEST_PATH.name
        shutil.copy2(RUN_MANIFEST_PATH, run_manifest_destination)
        copied_files["run_manifest_json"] = str(run_manifest_destination)

    archive_manifest = {
        "archive_dir": str(archive_dir),
        "copied_artifacts": copied_files,
        "source_run_manifest": str(RUN_MANIFEST_PATH),
    }
    (archive_dir / "archive_manifest.json").write_text(
        json.dumps(archive_manifest, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    return archive_dir


def main() -> None:
    archive_dir = archive_run_artifacts()
    print(f"Run artifacts archivované do: {archive_dir}")


if __name__ == "__main__":
    main()
