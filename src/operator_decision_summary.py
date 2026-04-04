import json
from pathlib import Path

import pandas as pd


QA_DIR = Path("data/qa")
RUN_MANIFEST_PATH = QA_DIR / "run_manifest.json"
CLICKUP_GATE_PATH = QA_DIR / "clickup_import_gate.json"
SHORTLIST_PATH = QA_DIR / "manual_review_shortlist.csv"
OUTPUT_PATH = QA_DIR / "operator_decision_summary.txt"


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame()
    return pd.read_csv(path)


def build_operator_decision_summary() -> str:
    manifest = load_json(RUN_MANIFEST_PATH)
    gate = load_json(CLICKUP_GATE_PATH)
    shortlist_df = load_csv(SHORTLIST_PATH)

    batch_sources = manifest.get("batch", {}).get("source_files", [])
    fetch_health = manifest.get("fetch_health", {})
    import_snapshot = manifest.get("import_snapshot", {})
    quality_snapshot = manifest.get("quality_snapshot", {})

    high_shortlist_df = shortlist_df[
        shortlist_df.get("priority_band", pd.Series(dtype="object"))
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("High")
    ].copy() if not shortlist_df.empty else pd.DataFrame()

    top_high_preview = []
    if not high_shortlist_df.empty:
        preview_cols = [
            "hotel_name",
            "review_bucket",
            "operator_triage_action",
            "priority_score",
        ]
        preview_cols = [col for col in preview_cols if col in high_shortlist_df.columns]
        top_high_preview = high_shortlist_df[preview_cols].head(5).to_dict("records")

    lines = [
        "Operator Decision Summary",
        "",
        f"- batch_source: {batch_sources[0] if batch_sources else 'Neoverené'}",
        f"- clickup_decision: {gate.get('decision', 'Neoverené')}",
        f"- operator_action: {gate.get('operator_action', 'Neoverené')}",
        f"- fetch_incident_flag: {fetch_health.get('fetch_incident_flag', 'Neoverené')}",
        f"- qa_blocking_rows: {import_snapshot.get('qa_blocking_rows', 'Neoverené')}",
        f"- clickup_import_ready_rows: {import_snapshot.get('clickup_import_ready_rows', 'Neoverené')}",
        f"- verified_checkin_checkout: {quality_snapshot.get('verified_checkin_checkout', 'Neoverené')}",
        f"- single_side_checkin_checkout_verified: {quality_snapshot.get('single_side_checkin_checkout_verified', 'Neoverené')}",
        f"- manual_review_shortlist_rows: {manifest.get('row_counts', {}).get('manual_review_shortlist_rows', 'Neoverené')}",
        "",
        "Stop conditions",
    ]
    for condition in gate.get("stop_conditions", []) or ["none"]:
        lines.append(f"- {condition}")

    lines.append("")
    lines.append("Top High Leads Preview")
    if not top_high_preview:
        lines.append("- žiadne High leady v shortlist preview")
    else:
        for row in top_high_preview:
            lines.append(
                "- {hotel_name} | {review_bucket} | {operator_triage_action} | {priority_score}".format(
                    hotel_name=row.get("hotel_name", "Neoverené"),
                    review_bucket=row.get("review_bucket", "Neoverené"),
                    operator_triage_action=row.get("operator_triage_action", "Neoverené"),
                    priority_score=row.get("priority_score", "Neoverené"),
                )
            )

    return "\n".join(lines)


def save_operator_decision_summary(summary_text: str) -> Path:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(summary_text, encoding="utf-8")
    return OUTPUT_PATH


def main() -> None:
    summary_text = build_operator_decision_summary()
    output_path = save_operator_decision_summary(summary_text)
    print(f"Operator decision summary uložený do: {output_path}")
    print("\nNáhľad:\n")
    print(summary_text)


if __name__ == "__main__":
    main()
