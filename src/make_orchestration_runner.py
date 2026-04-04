import json
import argparse
from datetime import datetime
from pathlib import Path
from typing import Any, Optional

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


def save_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def latest_archive_dir() -> str:
    if not ARCHIVE_DIR.exists():
        return ""
    candidates = sorted([path for path in ARCHIVE_DIR.iterdir() if path.is_dir()])
    return str(candidates[-1]) if candidates else ""


def resolve_archive_dir(manifest: dict[str, Any]) -> str:
    artifacts = manifest.get("artifacts", {})
    expected_clickup_csv = Path(str(artifacts.get("clickup_import_csv", "")).strip()).name
    source_files = set(manifest.get("batch", {}).get("source_files", []))

    if ARCHIVE_DIR.exists():
        candidates = sorted([path for path in ARCHIVE_DIR.iterdir() if path.is_dir()], reverse=True)
        for archive_dir in candidates:
            archive_manifest_path = archive_dir / "archive_manifest.json"
            if not archive_manifest_path.exists():
                continue
            archive_manifest = load_json(archive_manifest_path)
            copied_artifacts = archive_manifest.get("copied_artifacts", {})
            copied_clickup_csv = Path(str(copied_artifacts.get("clickup_import_csv", "")).strip()).name
            if expected_clickup_csv and copied_clickup_csv == expected_clickup_csv:
                return str(archive_dir)
            archive_name = archive_dir.name
            if source_files and any(source_file.replace(".csv", "") in archive_name for source_file in source_files):
                return str(archive_dir)

    return latest_archive_dir()


def build_make_payload(
    manifest: dict[str, Any],
    gate: dict[str, Any],
    manifest_path: Path,
    gate_path: Path,
) -> dict[str, str]:
    artifacts = manifest.get("artifacts", {})
    return {
        "decision": str(gate.get("decision", "")).strip(),
        "run_manifest_json": str(manifest_path),
        "clickup_import_gate_json": str(gate_path),
        "clickup_import_csv": str(artifacts.get("clickup_import_csv", "")).strip(),
        "clickup_import_dry_run_sample_csv": str(artifacts.get("clickup_import_dry_run_sample_csv", "")).strip(),
        "high_leads_preimport_checklist_csv": str(artifacts.get("high_leads_preimport_checklist_csv", "")).strip(),
        "operator_decision_summary_txt": str(artifacts.get("operator_decision_summary_txt", "")).strip(),
        "archive_dir": resolve_archive_dir(manifest),
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


def build_artifact_check(
    payload: dict[str, str],
    config: dict[str, Any],
) -> dict[str, Any]:
    orchestration_config = config.get("orchestration", {})
    required_keys = set(orchestration_config.get("required_artifact_keys", []))
    optional_keys = set(orchestration_config.get("optional_artifact_keys", []))
    checks = []
    for key, value in payload.items():
        normalized = str(value).strip()
        path_like = key != "decision"
        exists = Path(normalized).exists() if normalized and path_like else None
        checks.append(
            {
                "key": key,
                "required": key in required_keys,
                "optional": key in optional_keys,
                "path": normalized,
                "path_like": path_like,
                "exists": exists,
            }
        )
    return {"checks": checks}


def build_failure_notification(
    payload: dict[str, str],
    gate: dict[str, Any],
    rehearsal: dict[str, Any],
    validation_issues: list[str],
    config: dict[str, Any],
    gate_path: Path,
    rehearsal_path: Path,
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
        affected_artifact = str(gate_path)
    elif rehearsal_status == "BLOCKED" and external_blocker_detected:
        failure_type = failure_types.get("clickup_external_blocker", "clickup_external_blocker")
        operator_action = "Neevidovať to ako interný mapping fail a nepokračovať ďalším live write pokusom."
        retry_allowed = "no"
        next_step = "Pokračovať v neblokovaných planning krokoch a blocker evidovať bokom."
        affected_artifact = str(rehearsal_path)
    elif partial_write_detected:
        failure_type = failure_types.get("partial_write_risk", "partial_write_risk")
        operator_action = "Skontrolovať vytvorené tasky a rozhodnúť o cleanup."
        retry_allowed = "no"
        next_step = "Použiť partial write cleanup SOP."
        affected_artifact = str(rehearsal_path)
    elif decision == "GO" and rehearsal_status == "PASS":
        failure_type = "none"
        operator_action = "Payload je pripravený pre Make handoff."
        retry_allowed = "n/a"
        next_step = "Pokračovať do Make execution vetvy alebo ďalšieho testu."
        affected_artifact = str(gate_path)
    else:
        failure_type = failure_types.get("unknown_external_error", "unknown_external_error")
        operator_action = "Zastaviť execution vetvu a skontrolovať incident evidence."
        retry_allowed = "no"
        next_step = "Doplniť incident review."
        affected_artifact = str(rehearsal_path) if rehearsal_path.exists() else str(gate_path)

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
    execution_path: str,
) -> dict[str, Any]:
    rows = rehearsal.get("rows", [])
    affected_task_ids = [str(row.get("task_id", "")).strip() for row in rows if row.get("task_id")]
    affected_task_urls = [str(row.get("task_url", "")).strip() for row in rows if row.get("task_url")]
    external_blocker_detected = "FIELD_033" in str(rehearsal.get("error", ""))
    return {
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "phase": "phase_5_orchestration_implementation",
        "batch_decision": payload.get("decision", ""),
        "execution_path": execution_path,
        "status": status,
        "validation_issues": validation_issues,
        "payload_used": payload,
        "notification_payload": notification_payload,
        "external_blocker": external_blocker_detected,
        "partial_write_detected": bool(rehearsal.get("partial_write_detected", False)),
        "affected_task_ids": affected_task_ids,
        "affected_task_urls": affected_task_urls,
    }


def build_decision_summary(
    payload: dict[str, str],
    status: str,
    validation_issues: list[str],
    notification_payload: dict[str, Any],
    rehearsal: dict[str, Any],
    would_execute_make: bool,
    scenario_label: str,
) -> dict[str, Any]:
    return {
        "scenario_label": scenario_label,
        "decision": payload.get("decision", ""),
        "status": status,
        "would_execute_make": would_execute_make,
        "validation_issues": validation_issues,
        "failure_type": notification_payload.get("failure_type", ""),
        "external_blocker_detected": notification_payload.get("external_blocker_detected", False),
        "partial_write_detected": bool(rehearsal.get("partial_write_detected", False)),
        "next_step": notification_payload.get("next_step", ""),
    }


def build_txt_summary(
    decision_summary: dict[str, Any],
    payload: dict[str, str],
    validation_issues: list[str],
) -> str:
    lines = [
        "Make orchestration run summary",
        f"scenario_label: {decision_summary['scenario_label']}",
        f"decision: {decision_summary['decision']}",
        f"status: {decision_summary['status']}",
        f"would_execute_make: {'yes' if decision_summary['would_execute_make'] else 'no'}",
        f"failure_type: {decision_summary['failure_type']}",
        f"external_blocker_detected: {'yes' if decision_summary['external_blocker_detected'] else 'no'}",
        f"partial_write_detected: {'yes' if decision_summary['partial_write_detected'] else 'no'}",
        f"archive_dir: {payload.get('archive_dir', '')}",
        f"validation_issues: {', '.join(validation_issues) if validation_issues else 'none'}",
        f"next_step: {decision_summary['next_step']}",
    ]
    return "\n".join(lines) + "\n"


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


def resolve_output_path(
    config: dict[str, Any],
    key: str,
    output_dir: Optional[Path],
) -> Path:
    configured_path = Path(config.get("orchestration", {}).get(key, ""))
    if output_dir is None:
        return configured_path
    return output_dir / configured_path.name


def run(
    mode: str = "dry_run",
    manifest_path: Path = RUN_MANIFEST_PATH,
    gate_path: Path = CLICKUP_GATE_PATH,
    rehearsal_path: Path = CLICKUP_REHEARSAL_PATH,
    output_dir: Optional[Path] = None,
    scenario_label: str = "default",
) -> dict[str, Any]:
    config = load_config()
    manifest = load_json(manifest_path)
    gate = load_json(gate_path)
    rehearsal = load_json(rehearsal_path)

    payload = build_make_payload(manifest, gate, manifest_path, gate_path)
    validation_issues, _missing_paths = validate_make_payload(payload, config)
    artifact_check = build_artifact_check(payload, config)
    notification_payload = build_failure_notification(
        payload,
        gate,
        rehearsal,
        validation_issues,
        config,
        gate_path,
        rehearsal_path,
    )
    status = classify_runtime_status(payload, rehearsal, validation_issues)
    execution_path = "validate_only" if mode == "validate_only" else "dry_run"
    evidence_log = build_evidence_log(
        payload,
        status,
        validation_issues,
        notification_payload,
        rehearsal,
        execution_path,
    )
    status_output = build_status_matrix_output(status, payload, validation_issues, rehearsal)
    would_execute_make = payload.get("decision") == "GO" and not validation_issues and mode != "validate_only"
    decision_summary = build_decision_summary(
        payload,
        status,
        validation_issues,
        notification_payload,
        rehearsal,
        would_execute_make,
        scenario_label,
    )
    txt_summary = build_txt_summary(decision_summary, payload, validation_issues)

    make_payload_path = resolve_output_path(config, "make_payload_path", output_dir)
    failure_notification_path = resolve_output_path(config, "failure_notification_path", output_dir)
    evidence_log_path = resolve_output_path(config, "evidence_log_path", output_dir)
    status_matrix_path = resolve_output_path(config, "status_matrix_path", output_dir)
    artifact_check_path = resolve_output_path(config, "artifact_check_path", output_dir)
    decision_summary_path = resolve_output_path(config, "decision_summary_path", output_dir)
    txt_summary_path = resolve_output_path(config, "txt_summary_path", output_dir)
    dry_run_result_path = resolve_output_path(config, "dry_run_result_path", output_dir)

    save_json(make_payload_path, payload)
    save_json(failure_notification_path, notification_payload)
    save_json(evidence_log_path, evidence_log)
    save_json(status_matrix_path, status_output)
    save_json(artifact_check_path, artifact_check)
    save_json(decision_summary_path, decision_summary)
    save_text(txt_summary_path, txt_summary)

    dry_run_result = {
        "mode": mode,
        "scenario_label": scenario_label,
        "status": status,
        "would_execute_make": would_execute_make,
        "validation_issues": validation_issues,
        "payload_path": str(make_payload_path),
        "failure_notification_path": str(failure_notification_path),
        "evidence_log_path": str(evidence_log_path),
        "status_matrix_path": str(status_matrix_path),
        "artifact_check_path": str(artifact_check_path),
        "decision_summary_path": str(decision_summary_path),
        "txt_summary_path": str(txt_summary_path),
    }
    save_json(dry_run_result_path, dry_run_result)
    return dry_run_result


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Local Make orchestration runner.")
    parser.add_argument(
        "--mode",
        choices=["dry_run", "validate_only"],
        default="dry_run",
        help="Režim runnera.",
    )
    parser.add_argument(
        "--manifest",
        default=str(RUN_MANIFEST_PATH),
        help="Cesta na run manifest JSON.",
    )
    parser.add_argument(
        "--gate",
        default=str(CLICKUP_GATE_PATH),
        help="Cesta na clickup import gate JSON.",
    )
    parser.add_argument(
        "--rehearsal",
        default=str(CLICKUP_REHEARSAL_PATH),
        help="Cesta na clickup rehearsal JSON.",
    )
    parser.add_argument(
        "--output-dir",
        default="",
        help="Voliteľný output priečinok pre generated orchestration artifacty.",
    )
    parser.add_argument(
        "--scenario-label",
        default="default",
        help="Label scenára pre decision summary.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir) if args.output_dir else None
    result = run(
        mode=args.mode,
        manifest_path=Path(args.manifest),
        gate_path=Path(args.gate),
        rehearsal_path=Path(args.rehearsal),
        output_dir=output_dir,
        scenario_label=args.scenario_label,
    )
    print("Make orchestration run dokončený.")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
