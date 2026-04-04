import json
from pathlib import Path

import pandas as pd
import yaml


PROJECT_CONFIG_PATH = Path("configs/project.yaml")
QA_DIR = Path("data/qa")
RUN_MANIFEST_PATH = QA_DIR / "run_manifest.json"
CLICKUP_GATE_JSON_PATH = QA_DIR / "clickup_import_gate.json"
CLICKUP_GATE_TXT_PATH = QA_DIR / "clickup_import_gate.txt"


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


def normalize_text(value: object) -> str:
    if pd.isna(value):
        return ""
    return str(value).strip()


def compute_batch_readiness_score(
    fetch_incident_flag: str,
    qa_blocking_rows: int,
    clickup_import_ready_rows: int,
    clickup_rows: int,
    high_hold_count: int,
) -> int:
    score = 100
    if fetch_incident_flag == "yes":
        score -= 40
    if qa_blocking_rows > 0:
        score -= 30
    if clickup_rows > 0 and clickup_import_ready_rows < clickup_rows:
        score -= 10
    if high_hold_count > 0:
        score -= 20
    return max(score, 0)


def build_clickup_import_gate() -> dict:
    manifest = load_manifest()
    qa_issues_path = Path(manifest.get("artifacts", {}).get("qa_issues_csv", ""))
    shortlist_path = Path(manifest.get("artifacts", {}).get("manual_review_shortlist_csv", ""))
    qa_df = pd.read_csv(qa_issues_path) if qa_issues_path.exists() else pd.DataFrame()
    shortlist_df = pd.read_csv(shortlist_path) if shortlist_path.exists() else pd.DataFrame()

    fetch_incident_flag = normalize_text(manifest.get("fetch_health", {}).get("fetch_incident_flag"))
    qa_blocking_rows = int(manifest.get("import_snapshot", {}).get("qa_blocking_rows", 0) or 0)
    clickup_import_ready_rows = int(manifest.get("import_snapshot", {}).get("clickup_import_ready_rows", 0) or 0)
    clickup_rows = int(manifest.get("row_counts", {}).get("clickup_rows", 0) or 0)

    high_shortlist_df = shortlist_df[
        shortlist_df.get("priority_band", pd.Series(dtype="object"))
        .fillna("")
        .astype(str)
        .str.strip()
        .eq("High")
    ].copy() if not shortlist_df.empty else pd.DataFrame()
    high_hold_count = 0
    if not high_shortlist_df.empty and "operator_triage_action" in high_shortlist_df.columns:
        high_hold_count = int(
            high_shortlist_df["operator_triage_action"]
            .fillna("")
            .astype(str)
            .str.strip()
            .isin(["hold_batch_due_to_dns_incident", "manual_review_before_clickup", "review_before_clickup"])
            .sum()
        )

    stop_conditions: list[str] = []
    if fetch_incident_flag == "yes":
        stop_conditions.append("global_fetch_incident")
    if qa_blocking_rows > 0:
        stop_conditions.append("qa_blocking_rows_present")
    if clickup_rows == 0:
        stop_conditions.append("missing_clickup_rows")
    if clickup_import_ready_rows < clickup_rows:
        stop_conditions.append("clickup_rows_not_fully_ready")
    if high_hold_count > 0:
        stop_conditions.append("high_leads_require_manual_review")

    if stop_conditions:
        decision = "NO_GO"
        operator_action = "Neimportovať do ClickUp. Najprv odstrániť stop conditions."
    else:
        decision = "GO"
        operator_action = "Batch je pripravený na suchý alebo ostrý ClickUp import."

    readiness_score = compute_batch_readiness_score(
        fetch_incident_flag=fetch_incident_flag or "no",
        qa_blocking_rows=qa_blocking_rows,
        clickup_import_ready_rows=clickup_import_ready_rows,
        clickup_rows=clickup_rows,
        high_hold_count=high_hold_count,
    )

    return {
        "decision": decision,
        "operator_action": operator_action,
        "batch_readiness_score": readiness_score,
        "inputs": {
            "run_manifest_json": str(RUN_MANIFEST_PATH),
            "clickup_import_csv": manifest.get("artifacts", {}).get("clickup_import_csv", ""),
            "qa_issues_csv": manifest.get("artifacts", {}).get("qa_issues_csv", ""),
            "manual_review_shortlist_csv": manifest.get("artifacts", {}).get("manual_review_shortlist_csv", ""),
        },
        "checks": {
            "fetch_incident_flag": fetch_incident_flag or "no",
            "qa_blocking_rows": qa_blocking_rows,
            "clickup_rows": clickup_rows,
            "clickup_import_ready_rows": clickup_import_ready_rows,
            "high_leads_requiring_manual_review": high_hold_count,
        },
        "stop_conditions": stop_conditions,
        "go_rules": [
            "fetch_incident_flag musí byť no",
            "qa_blocking_rows musí byť 0",
            "clickup_import_ready_rows musí byť rovné clickup_rows",
            "High leady nesmú zostať v hold/manual review stave pred importom",
        ],
        "no_go_rules": [
            "globálny DNS/fetch incident",
            "akýkoľvek blocking QA issue",
            "neúplne pripravený ClickUp CSV",
            "High leady ešte čakajú na ručný review",
        ],
    }


def save_clickup_import_gate(gate: dict) -> tuple[Path, Path]:
    QA_DIR.mkdir(parents=True, exist_ok=True)
    CLICKUP_GATE_JSON_PATH.write_text(
        json.dumps(gate, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "ClickUp Import Gate",
        "",
        f"- decision: {gate['decision']}",
        f"- operator_action: {gate['operator_action']}",
        f"- batch_readiness_score: {gate['batch_readiness_score']}",
        f"- fetch_incident_flag: {gate['checks']['fetch_incident_flag']}",
        f"- qa_blocking_rows: {gate['checks']['qa_blocking_rows']}",
        f"- clickup_rows: {gate['checks']['clickup_rows']}",
        f"- clickup_import_ready_rows: {gate['checks']['clickup_import_ready_rows']}",
        f"- high_leads_requiring_manual_review: {gate['checks']['high_leads_requiring_manual_review']}",
        "",
        "Stop conditions",
    ]
    for condition in gate["stop_conditions"] or ["none"]:
        lines.append(f"- {condition}")
    CLICKUP_GATE_TXT_PATH.write_text("\n".join(lines), encoding="utf-8")
    return CLICKUP_GATE_JSON_PATH, CLICKUP_GATE_TXT_PATH


def main() -> None:
    gate = build_clickup_import_gate()
    json_path, txt_path = save_clickup_import_gate(gate)
    print(f"ClickUp import gate uložený do: {json_path}")
    print(f"ClickUp import gate text uložený do: {txt_path}")
    print("\nNáhľad:\n")
    print(json.dumps(gate, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
