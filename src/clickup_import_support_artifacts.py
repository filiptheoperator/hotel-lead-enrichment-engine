import json
from pathlib import Path
from typing import Optional

import pandas as pd


MASTER_DIR = Path("outputs/master")
CLICKUP_DIR = Path("outputs/clickup")
EMAIL_DIR = Path("outputs/email_drafts")
QA_DIR = Path("data/qa")
PHASE1_CHECKLIST_PATH = QA_DIR / "phase1_import_checklist.json"
FULL_REVIEW_CHECKLIST_PATH = QA_DIR / "full_ranked_review_checklist.json"
TOP20_REASONS_PATH = QA_DIR / "top_20_reasons_summary.txt"
REVIEW_BUCKET_REASONS_PATH = QA_DIR / "review_bucket_reasons_summary.txt"
COMMAND_SHEET_PATH = QA_DIR / "operator_import_command_sheet.txt"
PHASE1_PASS_FAIL_PATH = QA_DIR / "phase1_import_pass_fail_summary.txt"
FULL_REVIEW_PASS_FAIL_PATH = QA_DIR / "full_ranked_review_pass_fail_summary.txt"
RANK_BUCKET_SUMMARY_PATH = QA_DIR / "rank_bucket_summary.json"
WEBSITE_QUALITY_SUMMARY_PATH = QA_DIR / "website_quality_summary.json"
CONTACT_GAP_SUMMARY_PATH = QA_DIR / "contact_gap_summary.json"


def get_latest(folder: Path, pattern: str) -> Optional[Path]:
    files = sorted(folder.glob(pattern), key=lambda path: path.stat().st_mtime)
    return files[-1] if files else None


def load_csv(path: Optional[Path]) -> pd.DataFrame:
    if path is None or not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def build_phase1_import_checklist(clickup_path: Optional[Path]) -> dict:
    clickup_df = load_csv(clickup_path)
    return {
        "artifact": str(clickup_path) if clickup_path else "",
        "required_checks": [
            {"check": "task_name_present", "result": bool(not clickup_df.empty and "Task name" in clickup_df.columns)},
            {"check": "status_present", "result": bool(not clickup_df.empty and "Status" in clickup_df.columns)},
            {"check": "priority_present", "result": bool(not clickup_df.empty and "Priority" in clickup_df.columns)},
            {"check": "rank_bucket_present", "result": bool(not clickup_df.empty and "Rank bucket" in clickup_df.columns)},
            {"check": "rank_bucket_reason_present", "result": bool(not clickup_df.empty and "Rank bucket reason" in clickup_df.columns)},
            {"check": "chain_signal_confidence_present", "result": bool(not clickup_df.empty and "Chain signal confidence" in clickup_df.columns)},
        ],
        "note": "Phase1 import checklist pre krátky ClickUp import.",
    }


def build_full_ranked_review_checklist(clickup_path: Optional[Path]) -> dict:
    clickup_df = load_csv(clickup_path)
    return {
        "artifact": str(clickup_path) if clickup_path else "",
        "required_checks": [
            {"check": "description_present", "result": bool(not clickup_df.empty and "Description content" in clickup_df.columns)},
            {"check": "contact_phone_present", "result": bool(not clickup_df.empty and "Contact phone" in clickup_df.columns)},
            {"check": "contact_website_present", "result": bool(not clickup_df.empty and "Contact website" in clickup_df.columns)},
            {"check": "main_observed_issue_present", "result": bool(not clickup_df.empty and "Main observed issue" in clickup_df.columns)},
            {"check": "proof_snippet_present", "result": bool(not clickup_df.empty and "Proof snippet" in clickup_df.columns)},
        ],
        "note": "Full ranked review checklist pre bohatý operator review export.",
    }


def summarize_value_counts(df: pd.DataFrame, column: str, top_n: int = 10) -> str:
    if df.empty or column not in df.columns:
        return "Neoverené"
    counts = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", "blank")
        .value_counts()
        .head(top_n)
    )
    return "\n".join([f"- {index}: {int(value)}" for index, value in counts.items()]) or "Neoverené"


def build_operator_import_command_sheet() -> str:
    commands = [
        "python3 src/normalize_score.py",
        "python3 src/enrich_hotels.py",
        "python3 src/email_drafts.py",
        "python3 src/master_exports.py",
        "python3 src/clickup_export.py",
        "python3 src/clickup_dry_run_sample.py",
        "python3 src/clickup_api_mapping_preview.py",
        "python3 src/clickup_import_support_artifacts.py",
        "python3 src/clickup_import_preflight.py",
        "python3 src/clickup_import_operator_pack.py",
        "python3 src/run_report.py",
        "python3 src/run_manifest.py",
        "python3 src/clickup_import_gate.py",
    ]
    return "\n".join(commands)


def build_pass_fail_summary(title: str, checks: list[dict]) -> str:
    passed = sum(1 for item in checks if item.get("result") is True)
    failed = sum(1 for item in checks if item.get("result") is not True)
    status = "PASS" if failed == 0 else "FAIL"
    lines = [title, "", f"status: {status}", f"passed_checks: {passed}", f"failed_checks: {failed}", ""]
    for item in checks:
        lines.append(f"- {item.get('check')}: {'pass' if item.get('result') is True else 'fail'}")
    return "\n".join(lines)


def build_distribution_summary(df: pd.DataFrame, column: str) -> dict:
    if df.empty or column not in df.columns:
        return {"column": column, "counts": {}, "note": "Neoverené"}
    counts = (
        df[column]
        .fillna("")
        .astype(str)
        .str.strip()
        .replace("", "blank")
        .value_counts()
        .to_dict()
    )
    return {"column": column, "counts": {str(key): int(value) for key, value in counts.items()}}


def main() -> None:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    phase1_path = get_latest(CLICKUP_DIR, "*_clickup_phase1_minimal.csv")
    full_ranked_path = get_latest(CLICKUP_DIR, "*_clickup_full_ranked.csv")
    top20_path = get_latest(MASTER_DIR, "*_top_20_export.csv")
    accounts_master_path = get_latest(MASTER_DIR, "*_accounts_master.csv")

    phase1_checklist = build_phase1_import_checklist(phase1_path)
    full_review_checklist = build_full_ranked_review_checklist(full_ranked_path)
    PHASE1_CHECKLIST_PATH.write_text(json.dumps(phase1_checklist, ensure_ascii=False, indent=2), encoding="utf-8")
    FULL_REVIEW_CHECKLIST_PATH.write_text(json.dumps(full_review_checklist, ensure_ascii=False, indent=2), encoding="utf-8")
    PHASE1_PASS_FAIL_PATH.write_text(
        build_pass_fail_summary("Phase1 import pass/fail summary", phase1_checklist["required_checks"]),
        encoding="utf-8",
    )
    FULL_REVIEW_PASS_FAIL_PATH.write_text(
        build_pass_fail_summary("Full ranked review pass/fail summary", full_review_checklist["required_checks"]),
        encoding="utf-8",
    )

    top20_df = load_csv(top20_path)
    accounts_master_df = load_csv(accounts_master_path)
    TOP20_REASONS_PATH.write_text(
        "Top 20 reasons summary\n\n" + summarize_value_counts(top20_df, "ranking_reason"),
        encoding="utf-8",
    )
    REVIEW_BUCKET_REASONS_PATH.write_text(
        "Review bucket reasons summary\n\n" + summarize_value_counts(accounts_master_df, "review_bucket"),
        encoding="utf-8",
    )
    COMMAND_SHEET_PATH.write_text(build_operator_import_command_sheet(), encoding="utf-8")
    RANK_BUCKET_SUMMARY_PATH.write_text(
        json.dumps(build_distribution_summary(accounts_master_df, "rank_bucket"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    WEBSITE_QUALITY_SUMMARY_PATH.write_text(
        json.dumps(build_distribution_summary(accounts_master_df, "website_quality"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    CONTACT_GAP_SUMMARY_PATH.write_text(
        json.dumps(build_distribution_summary(accounts_master_df, "contact_gap_count"), ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"Phase1 checklist uložený do: {PHASE1_CHECKLIST_PATH}")
    print(f"Full ranked checklist uložený do: {FULL_REVIEW_CHECKLIST_PATH}")
    print(f"Top 20 reasons summary uložený do: {TOP20_REASONS_PATH}")
    print(f"Review bucket reasons summary uložený do: {REVIEW_BUCKET_REASONS_PATH}")
    print(f"Operator import command sheet uložený do: {COMMAND_SHEET_PATH}")
    print(f"Phase1 pass/fail summary uložený do: {PHASE1_PASS_FAIL_PATH}")
    print(f"Full ranked pass/fail summary uložený do: {FULL_REVIEW_PASS_FAIL_PATH}")


if __name__ == "__main__":
    main()
