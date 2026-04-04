import json
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml


QA_DIR = Path("data/qa")
ARCHIVE_DIR = Path("data/archive")
ORCHESTRATION_CONFIG_PATH = Path("configs/orchestration.yaml")
RUN_MANIFEST_PATH = QA_DIR / "run_manifest.json"
CLICKUP_GATE_PATH = QA_DIR / "clickup_import_gate.json"
CLICKUP_REHEARSAL_PATH = QA_DIR / "clickup_rehearsal_execution.json"


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as file:
        return json.load(file)


def load_config() -> dict[str, Any]:
    if not ORCHESTRATION_CONFIG_PATH.exists():
        return {}
    with ORCHESTRATION_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def save_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def latest_archive_dir() -> str:
    if not ARCHIVE_DIR.exists():
        return ""
    candidates = sorted([path for path in ARCHIVE_DIR.iterdir() if path.is_dir()])
    return str(candidates[-1]) if candidates else ""


def build_make_payload(manifest: dict[str, Any], gate: dict[str, Any]) -> dict[str, str]:
    artifacts = manifest.get("artifacts", {})
    return {
        "decision": str(gate.get("decision", "")).strip(),
        "run_manifest_json": str(RUN_MANIFEST_PATH),
        "clickup_import_gate_json": str(CLICKUP_GATE_PATH),
        "clickup_import_csv": str(artifacts.get("clickup_import_csv", "")).strip(),
        "clickup_import_dry_run_sample_csv": str(artifacts.get("clickup_import_dry_run_sample_csv", "")).strip(),
        "high_leads_preimport_checklist_csv": str(artifacts.get("high_leads_preimport_checklist_csv", "")).strip(),
        "operator_decision_summary_txt": str(artifacts.get("operator_decision_summary_txt", "")).strip(),
        "archive_dir": latest_archive_dir(),
        "clickup_import_gate_high_only_json": str(artifacts.get("clickup_import_gate_high_only_json", "")).strip(),
        "operator_decision_summary_high_txt": str(artifacts.get("operator_decision_summary_high_txt", "")).strip(),
        "batch_readiness_explanation_json": str(artifacts.get("batch_readiness_explanation_json", "")).strip(),
        "clickup_api_mapping_validation_json": str(artifacts.get("clickup_api_mapping_validation_json", "")).strip(),
    }


def validate_make_payload(
    payload: dict[str, str],
    config: dict[str, Any],
) -> tuple[list[str], list[str]]:
    orchestration_config = config.get("orchestration", {})
    required_keys = orchestration_config.get("required_artifact_keys", [])
    issues: list[str] = []
    missing_paths: list[str] = []

    decision = payload.get("decision", "")
    if decision not in {"GO", "NO_GO"}:
        issues.append("invalid_decision")

    for key in required_keys:
        value = str(payload.get(key, "")).strip()
        if not value:
            issues.append(f"missing_required_key:{key}")
            continue
        if key.endswith("_json") or key.endswith("_csv") or key.endswith("_txt") or key == "archive_dir":
            if not Path(value).exists():
                missing_paths.append(key)
                issues.append(f"missing_required_artifact:{key}")

    return issues, missing_paths


def build_failure_notification(
    payload: dict[str, str],
    gate: dict[str, Any],
    rehearsal: dict[str, Any],
    validation_issues: list[str],
    config: dict[str, Any],
) -> dict[str, Any]:
    failure_types = config.get("orchestration", {}).get("failure_types", {})
    decision = payload.get("decision", "")
    rehearsal_status = str(rehearsal.get("rehearsal_status", "")).strip()
    rehearsal_error = str(rehearsal.get("error", "")).strip()
    partial_write_detected = bool(rehearsal.get("partial_write_detected", False))

    external_blocker_detected = "FIELD_033" in rehearsal_error

    if validation_issues:
        failure_type = failure_types.get("missing_required_artifact", "missing_required_artifact")
        operator_action = "Doplniť chýbajúce artifacty a nespúšťať Make execution."
        retry_allowed = "no"
        next_step = "Opraviť payload alebo artifact path a zopakovať len dry run validáciu."
        affected_artifact = validation_issues[0]
    elif decision == "NO_GO":
        failure_type = failure_types.get("no_go_batch", "no_go_batch")
        operator_action = "Nepokračovať live execution vetvou."
        retry_allowed = "no"
        next_step = "Zostať v planning alebo remediation vetve podľa gate."
        affected_artifact = str(CLICKUP_GATE_PATH)
    elif rehearsal_status == "BLOCKED" and external_blocker_detected:
        failure_type = failure_types.get("clickup_external_blocker", "clickup_external_blocker")
        operator_action = "Neevidovať to ako interný mapping fail a nepokračovať ďalším live write pokusom."
        retry_allowed = "no"
        next_step = "Pokračovať v neblokovaných planning krokoch a blocker evidovať bokom."
        affected_artifact = str(CLICKUP_REHEARSAL_PATH)
    elif partial_write_detected:
        failure_type = failure_types.get("partial_write_risk", "partial_write_risk")
        operator_action = "Skontrolovať vytvorené tasky a rozhodnúť o cleanup."
        retry_allowed = "no"
        next_step = "Použiť partial write cleanup SOP."
        affected_artifact = str(CLICKUP_REHEARSAL_PATH)
    else:
        failure_type = failure_types.get("unknown_external_error", "unknown_external_error")
        operator_action = "Zastaviť execution vetvu a skontrolovať incident evidence."
        retry_allowed = "no"
        next_step = "Doplniť incident review."
        affected_artifact = str(CLICKUP_REHEARSAL_PATH) if CLICKUP_REHEARSAL_PATH.exists() else str(CLICKUP_GATE_PATH)

    return {
        "failure_stage": "make_orchestration_runner",
        "failure_type": failure_type,
        "batch_decision": decision,
        "affected_artifact": affected_artifact,
        "operator_action": operator_action,
        "retry_allowed": retry_allowed,
        "next_step": next_step,
        "gate_operator_action": gate.get("operator_action", ""),
        "external_blocker_detected": external_blocker_detected,
        "external_blocker_code": "FIELD_033" if external_blocker_detected else "",
    }


def classify_runtime_status(
    payload: dict[str, str],
    rehearsal: dict[str, Any],
    validation_issues: list[str],
) -> str:
    if validation_issues:
        return "BLOCKED_INTERNAL"
    if payload.get("decision") == "NO_GO":
        return "READY_FOR_PLANNING"
    rehearsal_status = str(rehearsal.get("rehearsal_status", "")).strip()
    if rehearsal_status == "PASS":
        return "READY_FOR_LIVE_CUTOVER"
    if rehearsal_status == "BLOCKED":
        return "BLOCKED_EXTERNAL"
    return "READY_FOR_REHEARSAL"


def build_evidence_log(
    payload: dict[str, str],
    status: str,
    validation_issues: list[str],
    notification_payload: dict[str, Any],
    rehearsal: dict[str, Any],
) -> dict[str, Any]:
    rows = rehearsal.get("rows", [])
    affected_task_ids = [str(row.get("task_id", "")).strip() for row in rows if row.get("task_id")]
    affected_task_urls = [str(row.get("task_url", "")).strip() for row in rows if row.get("task_url")]
    external_blocker_detected = "FIELD_033" in str(rehearsal.get("error", ""))
    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "phase": "phase_5_orchestration_implementation",
        "batch_decision": payload.get("decision", ""),
        "execution_path": "dry_run",
        "status": status,
        "validation_issues": validation_issues,
        "payload_used": payload,
        "notification_payload": notification_payload,
        "external_blocker": external_blocker_detected,
        "partial_write_detected": bool(rehearsal.get("partial_write_detected", False)),
        "affected_task_ids": affected_task_ids,
        "affected_task_urls": affected_task_urls,
    }


def build_status_matrix_output(
    status: str,
    payload: dict[str, str],
    validation_issues: list[str],
    rehearsal: dict[str, Any],
) -> dict[str, Any]:
    return {
        "status": status,
        "decision": payload.get("decision", ""),
        "validation_issues": validation_issues,
        "rehearsal_status": rehearsal.get("rehearsal_status", ""),
        "external_blocker_detected": "FIELD_033" in str(rehearsal.get("error", "")),
        "partial_write_detected": bool(rehearsal.get("partial_write_detected", False)),
    }


def run() -> dict[str, Any]:
    config = load_config()
    orchestration_config = config.get("orchestration", {})
    manifest = load_json(RUN_MANIFEST_PATH)
    gate = load_json(CLICKUP_GATE_PATH)
    rehearsal = load_json(CLICKUP_REHEARSAL_PATH)

    payload = build_make_payload(manifest, gate)
    validation_issues, _missing_paths = validate_make_payload(payload, config)
    notification_payload = build_failure_notification(payload, gate, rehearsal, validation_issues, config)
    status = classify_runtime_status(payload, rehearsal, validation_issues)
    evidence_log = build_evidence_log(payload, status, validation_issues, notification_payload, rehearsal)
    status_output = build_status_matrix_output(status, payload, validation_issues, rehearsal)

    save_json(Path(orchestration_config["make_payload_path"]), payload)
    save_json(Path(orchestration_config["failure_notification_path"]), notification_payload)
    save_json(Path(orchestration_config["evidence_log_path"]), evidence_log)
    save_json(Path(orchestration_config["status_matrix_path"]), status_output)

    dry_run_result = {
        "mode": orchestration_config.get("mode_default", "dry_run"),
        "status": status,
        "would_execute_make": payload.get("decision") == "GO" and not validation_issues,
        "validation_issues": validation_issues,
        "payload_path": orchestration_config["make_payload_path"],
        "failure_notification_path": orchestration_config["failure_notification_path"],
        "evidence_log_path": orchestration_config["evidence_log_path"],
        "status_matrix_path": orchestration_config["status_matrix_path"],
    }
    save_json(Path(orchestration_config["dry_run_result_path"]), dry_run_result)
    return dry_run_result


def main() -> None:
    result = run()
    print("Make orchestration dry run dokončený.")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
