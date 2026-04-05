import json
from pathlib import Path


QA_DIR = Path("data/qa")


def artifact_ready(path: Path) -> bool:
    return path.exists()


def main() -> None:
    required = {
        "phase1_preview": QA_DIR / "clickup_api_mapping_preview_phase1_minimal.json",
        "full_preview": QA_DIR / "clickup_api_mapping_preview_full_ranked.json",
        "phase1_validation": QA_DIR / "clickup_api_mapping_validation_phase1_minimal.json",
        "full_validation": QA_DIR / "clickup_api_mapping_validation_full_ranked.json",
        "export_mode_diff": QA_DIR / "clickup_export_mode_diff.json",
        "phase1_checklist": QA_DIR / "phase1_import_checklist.json",
        "full_review_checklist": QA_DIR / "full_ranked_review_checklist.json",
        "phase1_pass_fail": QA_DIR / "phase1_import_pass_fail_summary.txt",
        "full_review_pass_fail": QA_DIR / "full_ranked_review_pass_fail_summary.txt",
        "top20_summary": QA_DIR / "top_20_reasons_summary.txt",
        "review_bucket_summary": QA_DIR / "review_bucket_reasons_summary.txt",
        "rank_bucket_summary": QA_DIR / "rank_bucket_summary.json",
        "website_quality_summary": QA_DIR / "website_quality_summary.json",
        "contact_gap_summary": QA_DIR / "contact_gap_summary.json",
        "operator_command_sheet": QA_DIR / "operator_import_command_sheet.txt",
    }

    results = {name: artifact_ready(path) for name, path in required.items()}
    ready = all(results.values())
    payload = {
        "ready": ready,
        "checks": results,
        "note": "Preflight len pre ClickUp operator pack a dry run packet.",
    }
    output_path = QA_DIR / "clickup_import_preflight.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"ClickUp import preflight uložený do: {output_path}")
    print(json.dumps(payload, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
