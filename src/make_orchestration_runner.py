import json
import argparse
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml


QA_DIR = Path("data/qa")
ARCHIVE_DIR = Path("data/archive")
ORCHESTRATION_CONFIG_PATH = Path("configs/orchestration.yaml")
ORCHESTRATION_OVERRIDE_CONFIG_PATH = Path("configs/orchestration_overrides.yaml")
PROJECT_CONFIG_PATH = Path("configs/project.yaml")
RUN_MANIFEST_PATH = QA_DIR / "run_manifest.json"
CLICKUP_GATE_PATH = QA_DIR / "clickup_import_gate.json"
CLICKUP_REHEARSAL_PATH = QA_DIR / "clickup_rehearsal_execution.json"


def is_path_like_key(key: str) -> bool:
    return key.endswith("_json") or key.endswith("_csv") or key.endswith("_txt") or key == "archive_dir"


def detect_external_blocker_code(text: str) -> str:
    normalized = str(text).strip()
    if "Cloudflare 1010" in normalized or "1010" in normalized:
        return "CLOUDFLARE_1010"
    if "HTTP 403" in normalized or normalized == "403":
        return "HTTP_403"
    if "FIELD_033" in normalized:
        return "FIELD_033"
    return ""


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


def load_project_config() -> dict[str, Any]:
    if not PROJECT_CONFIG_PATH.exists():
        return {}
    with PROJECT_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_override_config() -> dict[str, Any]:
    if not ORCHESTRATION_OVERRIDE_CONFIG_PATH.exists():
        return {}
    with ORCHESTRATION_OVERRIDE_CONFIG_PATH.open("r", encoding="utf-8") as file:
        return yaml.safe_load(file) or {}


def load_env_file(path: Path = Path(".env")) -> dict[str, str]:
    if not path.exists():
        return {}
    env_values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        env_values[key.strip()] = value.strip()
    return env_values


def save_json(path: Path, payload: dict[str, Any]) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return path


def save_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def acquire_execution_lock(path: Path, scenario_label: str) -> dict[str, Any]:
    existing = load_json(path)
    if existing.get("active") is True:
        raise RuntimeError(f"Execution lock už existuje pre scenario {existing.get('scenario_label', '')}")
    payload = {
        "active": True,
        "scenario_label": scenario_label,
        "acquired_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "lock_version": 2,
    }
    save_json(path, payload)
    return payload


def release_execution_lock(path: Path, scenario_label: str) -> dict[str, Any]:
    payload = {
        "active": False,
        "scenario_label": scenario_label,
        "released_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "lock_version": 2,
    }
    save_json(path, payload)
    return payload


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
    override_config: dict[str, Any],
) -> dict[str, str]:
    artifacts = manifest.get("artifacts", {})
    decision = str(gate.get("decision", "")).strip()
    overrides = override_config.get("orchestration_overrides", {})
    if decision == "NO_GO" and overrides.get("allow_make_execution_when_no_go", False):
        decision = "GO"
    return {
        "decision": decision,
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
    payload_required_keys = orchestration_config.get("payload_required_keys", [])
    issues: list[str] = []
    missing_paths: list[str] = []

    decision = payload.get("decision", "")
    if decision not in {"GO", "NO_GO"}:
        issues.append("invalid_decision")

    for key in payload_required_keys:
        value = str(payload.get(key, "")).strip()
        if not value:
            issues.append(f"missing_payload_key:{key}")

    for key in required_keys:
        value = str(payload.get(key, "")).strip()
        if not value:
            issues.append(f"missing_required_key:{key}")
            continue
        if is_path_like_key(key):
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
        path_like = is_path_like_key(key)
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


def build_payload_validation(
    payload: dict[str, str],
    validation_issues: list[str],
    config: dict[str, Any],
) -> dict[str, Any]:
    orchestration_config = config.get("orchestration", {})
    return {
        "valid": len(validation_issues) == 0,
        "validation_issues": validation_issues,
        "payload_required_keys": orchestration_config.get("payload_required_keys", []),
        "required_artifact_keys": orchestration_config.get("required_artifact_keys", []),
        "payload_keys_present": sorted(payload.keys()),
    }


def build_archive_crosscheck(
    payload: dict[str, str],
    manifest: dict[str, Any],
) -> dict[str, Any]:
    archive_dir = Path(str(payload.get("archive_dir", "")).strip())
    archive_manifest_path = archive_dir / "archive_manifest.json"
    archive_manifest = load_json(archive_manifest_path) if archive_manifest_path.exists() else {}
    copied_artifacts = archive_manifest.get("copied_artifacts", {})
    copied_clickup_csv = Path(str(copied_artifacts.get("clickup_import_csv", "")).strip()).name
    payload_clickup_csv = Path(str(payload.get("clickup_import_csv", "")).strip()).name
    source_run_manifest = str(archive_manifest.get("source_run_manifest", "")).strip()
    return {
        "archive_dir": str(archive_dir),
        "archive_dir_exists": archive_dir.exists(),
        "archive_manifest_exists": archive_manifest_path.exists(),
        "clickup_csv_match": bool(copied_clickup_csv) and copied_clickup_csv == payload_clickup_csv,
        "run_manifest_match": bool(source_run_manifest) and Path(source_run_manifest).name == Path(str(payload.get("run_manifest_json", "")).strip()).name,
        "source_file_count": manifest.get("batch", {}).get("source_file_count", 0),
    }


def build_archive_retention_crosscheck(project_config: dict[str, Any]) -> dict[str, Any]:
    keep_last_batches = int(project_config.get("archive_keep_last_batches", 0) or 0)
    archive_dirs = sorted([path.name for path in ARCHIVE_DIR.iterdir() if path.is_dir()]) if ARCHIVE_DIR.exists() else []
    return {
        "archive_dir_count": len(archive_dirs),
        "archive_keep_last_batches": keep_last_batches,
        "within_limit": len(archive_dirs) <= keep_last_batches if keep_last_batches > 0 else True,
        "archive_dirs": archive_dirs[-10:],
    }


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

    external_blocker_code = detect_external_blocker_code(rehearsal_error)
    external_blocker_detected = bool(external_blocker_code)

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
        "external_blocker_code": external_blocker_code,
    }


def build_retry_eligibility(notification_payload: dict[str, Any]) -> dict[str, Any]:
    failure_type = str(notification_payload.get("failure_type", "")).strip()
    retry_allowed = failure_type in {"none", "http_server_error", "network_error"}
    return {
        "failure_type": failure_type,
        "retry_allowed_now": retry_allowed,
        "reason": "retry je povolený pre retry-eligible stav" if retry_allowed else "retry nie je povolený pre aktuálny failure type",
    }


def build_retry_backoff_plan(config: dict[str, Any], retry_eligibility: dict[str, Any]) -> dict[str, Any]:
    orchestration_config = config.get("orchestration", {})
    max_attempts = int(orchestration_config.get("make_webhook_max_attempts", 1) or 1)
    backoff_seconds = [int(value) for value in orchestration_config.get("make_webhook_backoff_seconds", [])]
    attempts = []
    for attempt_number in range(1, max_attempts + 1):
        attempts.append(
            {
                "attempt_number": attempt_number,
                "backoff_seconds": 0 if attempt_number == 1 else backoff_seconds[min(attempt_number - 2, len(backoff_seconds) - 1)] if backoff_seconds else 0,
            }
        )
    return {
        "retry_allowed_now": retry_eligibility.get("retry_allowed_now", False),
        "max_attempts": max_attempts,
        "attempts": attempts,
    }


def classify_runtime_status(
    payload: dict[str, str],
    rehearsal: dict[str, Any],
    validation_issues: list[str],
) -> str:
    if validation_issues:
        return "BLOCKED_INTERNAL"
    if bool(rehearsal.get("partial_write_detected", False)):
        return "BLOCKED_EXTERNAL"
    if payload.get("decision") == "NO_GO":
        return "READY_FOR_PLANNING"
    rehearsal_status = str(rehearsal.get("rehearsal_status", "")).strip()
    if rehearsal_status == "FAIL":
        return "READY_FOR_REMEDIATION"
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
    response_capture: dict[str, Any],
    live_webhook_requested: bool,
) -> dict[str, Any]:
    rows = rehearsal.get("rows", [])
    affected_task_ids = [str(row.get("task_id", "")).strip() for row in rows if row.get("task_id")]
    affected_task_urls = [str(row.get("task_url", "")).strip() for row in rows if row.get("task_url")]
    external_blocker_code = detect_external_blocker_code(str(rehearsal.get("error", "")))
    external_blocker_detected = bool(external_blocker_code)
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
        "external_blocker_code": external_blocker_code,
        "partial_write_detected": bool(rehearsal.get("partial_write_detected", False)),
        "affected_task_ids": affected_task_ids,
        "affected_task_urls": affected_task_urls,
        "live_webhook_requested": live_webhook_requested,
        "webhook_delivery": {
            "response_received": response_capture.get("response_received", False),
            "http_status": response_capture.get("http_status", ""),
            "http_classification": response_capture.get("http_classification", ""),
            "note": response_capture.get("note", ""),
        },
    }


def build_decision_summary(
    payload: dict[str, str],
    status: str,
    validation_issues: list[str],
    notification_payload: dict[str, Any],
    rehearsal: dict[str, Any],
    would_execute_make: bool,
    scenario_label: str,
    live_webhook_requested: bool,
) -> dict[str, Any]:
    launch_blockers: list[str] = []
    if validation_issues:
        launch_blockers.extend(validation_issues)
    if notification_payload.get("external_blocker_detected", False):
        launch_blockers.append(f"external_blocker:{notification_payload.get('external_blocker_code', '')}")
    if bool(rehearsal.get("partial_write_detected", False)):
        launch_blockers.append("partial_write_detected")
    return {
        "scenario_label": scenario_label,
        "decision": payload.get("decision", ""),
        "status": status,
        "would_execute_make": would_execute_make,
        "live_webhook_requested": live_webhook_requested,
        "validation_issues": validation_issues,
        "failure_type": notification_payload.get("failure_type", ""),
        "external_blocker_detected": notification_payload.get("external_blocker_detected", False),
        "external_blocker_code": notification_payload.get("external_blocker_code", ""),
        "partial_write_detected": bool(rehearsal.get("partial_write_detected", False)),
        "retry_allowed_now": notification_payload.get("retry_allowed", "no") == "yes",
        "operator_action": notification_payload.get("operator_action", ""),
        "launch_blockers": launch_blockers,
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
        f"live_webhook_requested: {'yes' if decision_summary['live_webhook_requested'] else 'no'}",
        f"failure_type: {decision_summary['failure_type']}",
        f"external_blocker_detected: {'yes' if decision_summary['external_blocker_detected'] else 'no'}",
        f"external_blocker_code: {decision_summary.get('external_blocker_code', '')}",
        f"partial_write_detected: {'yes' if decision_summary['partial_write_detected'] else 'no'}",
        f"retry_allowed_now: {'yes' if decision_summary.get('retry_allowed_now', False) else 'no'}",
        f"archive_dir: {payload.get('archive_dir', '')}",
        f"validation_issues: {', '.join(validation_issues) if validation_issues else 'none'}",
        f"launch_blockers: {', '.join(decision_summary.get('launch_blockers', [])) if decision_summary.get('launch_blockers') else 'none'}",
        f"next_step: {decision_summary['next_step']}",
    ]
    return "\n".join(lines) + "\n"


def build_incident_summary(
    decision_summary: dict[str, Any],
    notification_payload: dict[str, Any],
    evidence_log: dict[str, Any],
) -> str:
    lines = [
        "Integration incident summary",
        f"scenario_label: {decision_summary['scenario_label']}",
        f"decision: {decision_summary['decision']}",
        f"status: {decision_summary['status']}",
        f"failure_type: {decision_summary['failure_type']}",
        f"external_blocker_detected: {'yes' if decision_summary['external_blocker_detected'] else 'no'}",
        f"partial_write_detected: {'yes' if decision_summary['partial_write_detected'] else 'no'}",
        f"operator_action: {notification_payload['operator_action']}",
        f"next_step: {notification_payload['next_step']}",
        f"affected_task_ids: {', '.join(evidence_log['affected_task_ids']) if evidence_log['affected_task_ids'] else 'none'}",
    ]
    return "\n".join(lines) + "\n"


def build_escalation_artifact(
    decision_summary: dict[str, Any],
    notification_payload: dict[str, Any],
    evidence_log: dict[str, Any],
) -> dict[str, Any]:
    escalation_needed = bool(
        decision_summary.get("external_blocker_detected") or decision_summary.get("partial_write_detected")
    )
    return {
        "escalation_needed": escalation_needed,
        "escalation_type": notification_payload.get("failure_type", ""),
        "external_blocker_code": notification_payload.get("external_blocker_code", ""),
        "operator_action": notification_payload.get("operator_action", ""),
        "next_step": notification_payload.get("next_step", ""),
        "affected_task_ids": evidence_log.get("affected_task_ids", []),
        "affected_task_urls": evidence_log.get("affected_task_urls", []),
        "retry_allowed": decision_summary.get("retry_allowed_now", False),
    }


def build_handoff_bundle(
    payload: dict[str, str],
    decision_summary: dict[str, Any],
    notification_payload: dict[str, Any],
    archive_crosscheck: dict[str, Any],
) -> dict[str, Any]:
    archive_crosscheck_ok = (
        archive_crosscheck.get("archive_dir_exists", False)
        and archive_crosscheck.get("archive_manifest_exists", False)
        and archive_crosscheck.get("clickup_csv_match", False)
        and archive_crosscheck.get("run_manifest_match", False)
    )
    ready_to_transition = (
        decision_summary.get("status", "") == "READY_FOR_LIVE_CUTOVER"
        and decision_summary.get("decision", "") == "GO"
        and archive_crosscheck.get("archive_dir_exists", False)
        and archive_crosscheck.get("archive_manifest_exists", False)
        and archive_crosscheck.get("clickup_csv_match", False)
        and not decision_summary.get("external_blocker_detected", False)
        and not decision_summary.get("partial_write_detected", False)
    )
    return {
        "decision": payload.get("decision", ""),
        "status": decision_summary.get("status", ""),
        "would_execute_make": decision_summary.get("would_execute_make", False),
        "run_manifest_json": payload.get("run_manifest_json", ""),
        "clickup_import_gate_json": payload.get("clickup_import_gate_json", ""),
        "archive_dir": payload.get("archive_dir", ""),
        "archive_crosscheck_ok": archive_crosscheck_ok,
        "notification_failure_type": notification_payload.get("failure_type", ""),
        "operator_action": notification_payload.get("operator_action", ""),
        "retry_allowed_now": decision_summary.get("retry_allowed_now", False),
        "external_blocker_code": notification_payload.get("external_blocker_code", ""),
        "launch_blockers": decision_summary.get("launch_blockers", []),
        "ready_to_transition": ready_to_transition,
        "next_step": notification_payload.get("next_step", ""),
    }


def build_handoff_txt_bundle(
    decision_summary: dict[str, Any],
    handoff_bundle: dict[str, Any],
    retry_eligibility: dict[str, Any],
) -> str:
    lines = [
        "Operator handoff bundle",
        f"decision: {handoff_bundle['decision']}",
        f"status: {handoff_bundle['status']}",
        f"would_execute_make: {'yes' if handoff_bundle['would_execute_make'] else 'no'}",
        f"live_webhook_requested: {'yes' if decision_summary['live_webhook_requested'] else 'no'}",
        f"archive_crosscheck_ok: {'yes' if handoff_bundle['archive_crosscheck_ok'] else 'no'}",
        f"failure_type: {handoff_bundle['notification_failure_type']}",
        f"retry_allowed_now: {'yes' if retry_eligibility['retry_allowed_now'] else 'no'}",
        f"external_blocker_code: {handoff_bundle.get('external_blocker_code', '')}",
        f"operator_action: {handoff_bundle.get('operator_action', '')}",
        f"ready_to_transition: {'yes' if handoff_bundle.get('ready_to_transition', False) else 'no'}",
        f"launch_blockers: {', '.join(handoff_bundle.get('launch_blockers', [])) if handoff_bundle.get('launch_blockers') else 'none'}",
        f"next_step: {handoff_bundle['next_step']}",
        f"scenario_label: {decision_summary['scenario_label']}",
    ]
    return "\n".join(lines) + "\n"


def build_webhook_request_export(
    payload: dict[str, str],
    scenario_label: str,
    webhook_url: str,
    webhook_enabled: bool,
    no_op_mode: bool,
) -> dict[str, Any]:
    return {
        "scenario_label": scenario_label,
        "webhook_target": webhook_url if webhook_url else "UNVERIFIED_MAKE_WEBHOOK",
        "webhook_enabled": webhook_enabled,
        "no_op_mode": no_op_mode,
        "method": "POST",
        "headers": {
            "Content-Type": "application/json"
        },
        "body": payload,
    }


def build_response_capture_template(
    scenario_label: str,
) -> dict[str, Any]:
    return {
        "scenario_label": scenario_label,
        "response_received": False,
        "http_status": "",
        "response_body": {},
        "captured_at": "",
        "note": "Template pre budúce Make response capture.",
    }


def load_simulated_response_capture(path: Optional[Path]) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def load_simulated_archive_crosscheck(path: Optional[Path]) -> dict[str, Any]:
    if path is None or not path.exists():
        return {}
    payload = load_json(path)
    return payload if isinstance(payload, dict) else {}


def to_bool(value: str) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def resolve_webhook_runtime(config: dict[str, Any], override_config: dict[str, Any]) -> dict[str, Any]:
    orchestration_config = config.get("orchestration", {})
    overrides = override_config.get("orchestration_overrides", {})
    env_file_values = load_env_file()
    enabled_key = str(orchestration_config.get("make_webhook_enabled_env_var", "MAKE_WEBHOOK_ENABLED")).strip()
    url_key = str(orchestration_config.get("make_webhook_url_env_var", "MAKE_WEBHOOK_URL")).strip()
    timeout_seconds = int(orchestration_config.get("make_webhook_timeout_seconds", 30) or 30)

    enabled_value = os.environ.get(enabled_key, env_file_values.get(enabled_key, "false"))
    webhook_url = os.environ.get(url_key, env_file_values.get(url_key, ""))
    force_noop = bool(overrides.get("force_noop_webhook", True))
    production_safe_noop_mode = bool(overrides.get("production_safe_noop_mode", True))

    return {
        "webhook_enabled": to_bool(enabled_value),
        "webhook_url": str(webhook_url).strip(),
        "timeout_seconds": timeout_seconds,
        "force_noop": force_noop,
        "production_safe_noop_mode": production_safe_noop_mode,
    }


def execute_make_webhook(
    payload: dict[str, str],
    decision_summary: dict[str, Any],
    runtime: dict[str, Any],
    live_webhook_requested: bool,
    simulated_response_capture: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    captured_at = datetime.now().astimezone().isoformat(timespec="seconds")
    response_payload = {
        "scenario_label": decision_summary.get("scenario_label", ""),
        "response_received": False,
        "http_status": "",
        "response_body": {},
        "captured_at": captured_at,
        "note": "",
        "webhook_enabled": runtime["webhook_enabled"],
        "no_op_mode": runtime["force_noop"],
        "production_safe_noop_mode": runtime["production_safe_noop_mode"],
        "live_webhook_requested": live_webhook_requested,
        "webhook_target": runtime["webhook_url"] if runtime["webhook_url"] else "UNVERIFIED_MAKE_WEBHOOK",
        "http_classification": "not_attempted",
        "retry_recommended": False,
    }

    if simulated_response_capture:
        response_payload.update(simulated_response_capture)
        response_payload["captured_at"] = simulated_response_capture.get("captured_at", captured_at)
        response_payload["note"] = str(simulated_response_capture.get("note", "Simulated response capture použitý.")).strip()
        response_payload["simulated_response_used"] = True
        return response_payload

    if not decision_summary.get("would_execute_make", False):
        response_payload["note"] = "Webhook nebol spustený, lebo scenár nie je execution-ready."
        return response_payload
    if not live_webhook_requested:
        response_payload["note"] = "Webhook nebol spustený, lebo live webhook CLI flag nebol zapnutý."
        return response_payload
    if not runtime["webhook_enabled"]:
        response_payload["note"] = "Webhook nebol spustený, lebo feature flag je vypnutý."
        return response_payload
    if not runtime["webhook_url"]:
        response_payload["note"] = "Webhook nebol spustený, lebo chýba MAKE_WEBHOOK_URL."
        return response_payload
    if runtime["force_noop"] or runtime["production_safe_noop_mode"]:
        response_payload["note"] = "Webhook nebol spustený, lebo force_noop_webhook=true."
        if runtime["production_safe_noop_mode"] and not runtime["force_noop"]:
            response_payload["note"] = "Webhook nebol spustený, lebo production_safe_noop_mode=true."
        return response_payload

    request_body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    request = Request(
        runtime["webhook_url"],
        data=request_body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urlopen(request, timeout=runtime["timeout_seconds"]) as response:
            response_text = response.read().decode("utf-8", errors="replace")
            response_payload["response_received"] = True
            response_payload["http_status"] = response.getcode()
            response_payload["http_classification"] = "success"
            response_payload["response_body"] = {
                "raw_text": response_text,
            }
            response_payload["note"] = "Webhook bol úspešne odoslaný."
    except HTTPError as exc:
        response_payload["response_received"] = True
        response_payload["http_status"] = exc.code
        response_payload["http_classification"] = "client_error" if 400 <= int(exc.code) < 500 else "server_error"
        response_payload["retry_recommended"] = int(exc.code) >= 500
        response_payload["response_body"] = {
            "raw_text": exc.read().decode("utf-8", errors="replace"),
        }
        response_payload["note"] = "Webhook request skončil HTTP chybou."
    except URLError as exc:
        response_payload["http_classification"] = "network_error"
        response_payload["retry_recommended"] = True
        response_payload["note"] = f"Webhook request zlyhal na sieťovej chybe: {exc.reason}"

    return response_payload


def apply_response_to_notification(
    notification_payload: dict[str, Any],
    response_capture: dict[str, Any],
    config: dict[str, Any],
) -> dict[str, Any]:
    failure_types = config.get("orchestration", {}).get("failure_types", {})
    classification = str(response_capture.get("http_classification", "")).strip()
    updated = dict(notification_payload)
    if classification == "client_error":
        updated["failure_type"] = failure_types.get("http_client_error", "http_client_error")
        updated["operator_action"] = "Skontrolovať Make webhook payload a endpoint konfiguráciu."
        updated["next_step"] = "Opraviť request a zopakovať dry run alebo live send."
    elif classification == "server_error":
        updated["failure_type"] = failure_types.get("http_server_error", "http_server_error")
        updated["operator_action"] = "Nechať endpoint stabilizovať a použiť retry backoff pravidlá."
        updated["next_step"] = "Zopakovať send podľa retry plánu."
    elif classification == "network_error":
        updated["failure_type"] = failure_types.get("network_error", "network_error")
        updated["operator_action"] = "Overiť sieťovú dostupnosť a zopakovať send podľa retry plánu."
        updated["next_step"] = "Spustiť retry po krátkom backoffe."
    return updated


def build_launch_checklist(
    decision_summary: dict[str, Any],
    archive_crosscheck: dict[str, Any],
    payload_validation: dict[str, Any],
    retry_eligibility: dict[str, Any],
    live_webhook_requested: bool,
    response_capture: dict[str, Any],
) -> dict[str, Any]:
    archive_crosscheck_ok = (
        archive_crosscheck.get("archive_dir_exists", False)
        and archive_crosscheck.get("archive_manifest_exists", False)
        and archive_crosscheck.get("clickup_csv_match", False)
        and archive_crosscheck.get("run_manifest_match", False)
    )
    response_ok = (
        not live_webhook_requested
        or response_capture.get("response_received", False)
        or response_capture.get("no_op_mode", False)
        or response_capture.get("production_safe_noop_mode", False)
    )
    return {
        "decision_is_go": decision_summary.get("decision") == "GO",
        "status_ready_for_live_cutover": decision_summary.get("status") == "READY_FOR_LIVE_CUTOVER",
        "payload_valid": payload_validation.get("valid", False),
        "archive_crosscheck_ok": archive_crosscheck_ok,
        "retry_allowed_now": retry_eligibility.get("retry_allowed_now", False),
        "safe_to_launch": response_ok,
        "launch_blocked_by_external": decision_summary.get("external_blocker_detected", False),
        "launch_blocked_by_partial_write": decision_summary.get("partial_write_detected", False),
    }


def build_launch_checklist_txt(
    decision_summary: dict[str, Any],
    launch_checklist: dict[str, Any],
) -> str:
    lines = [
        "Pre-launch checklist",
        f"scenario_label: {decision_summary['scenario_label']}",
        f"decision_is_go: {'yes' if launch_checklist.get('decision_is_go', False) else 'no'}",
        f"status_ready_for_live_cutover: {'yes' if launch_checklist.get('status_ready_for_live_cutover', False) else 'no'}",
        f"payload_valid: {'yes' if launch_checklist.get('payload_valid', False) else 'no'}",
        f"archive_crosscheck_ok: {'yes' if launch_checklist.get('archive_crosscheck_ok', False) else 'no'}",
        f"safe_to_launch: {'yes' if launch_checklist.get('safe_to_launch', False) else 'no'}",
        f"launch_blocked_by_external: {'yes' if launch_checklist.get('launch_blocked_by_external', False) else 'no'}",
        f"launch_blocked_by_partial_write: {'yes' if launch_checklist.get('launch_blocked_by_partial_write', False) else 'no'}",
    ]
    return "\n".join(lines) + "\n"


def build_launch_gating_summary(
    decision_summary: dict[str, Any],
    launch_checklist: dict[str, Any],
    response_capture: dict[str, Any],
) -> str:
    lines = [
        "Launch gating summary",
        f"scenario_label: {decision_summary['scenario_label']}",
        f"decision: {decision_summary['decision']}",
        f"status: {decision_summary['status']}",
        f"live_webhook_requested: {'yes' if decision_summary['live_webhook_requested'] else 'no'}",
        f"response_received: {'yes' if response_capture.get('response_received', False) else 'no'}",
        f"http_classification: {response_capture.get('http_classification', '')}",
        f"safe_to_launch: {'yes' if launch_checklist.get('safe_to_launch', False) else 'no'}",
        f"launch_ready: {'yes' if all(launch_checklist.values()) else 'no'}",
    ]
    return "\n".join(lines) + "\n"


def build_post_webhook_reconciliation(
    payload: dict[str, str],
    response_capture: dict[str, Any],
    archive_crosscheck: dict[str, Any],
) -> dict[str, Any]:
    response_received = response_capture.get("response_received", False)
    archive_crosscheck_ok = (
        archive_crosscheck.get("archive_dir_exists", False)
        and archive_crosscheck.get("archive_manifest_exists", False)
        and archive_crosscheck.get("clickup_csv_match", False)
        and archive_crosscheck.get("run_manifest_match", False)
    )
    local_test_mode = not response_received and (
        response_capture.get("no_op_mode", False) or response_capture.get("production_safe_noop_mode", False)
    )
    mismatch_reasons: list[str] = []
    if not archive_crosscheck.get("archive_dir_exists", False):
        mismatch_reasons.append("archive_dir_missing")
    if not archive_crosscheck.get("archive_manifest_exists", False):
        mismatch_reasons.append("archive_manifest_missing")
    if not archive_crosscheck.get("clickup_csv_match", False):
        mismatch_reasons.append("clickup_csv_mismatch")
    if not archive_crosscheck.get("run_manifest_match", False):
        mismatch_reasons.append("run_manifest_mismatch")
    if response_received and not response_capture.get("http_status", ""):
        mismatch_reasons.append("response_without_http_status")
    if response_capture.get("http_classification", "") in {"client_error", "server_error", "network_error"}:
        mismatch_reasons.append(f"http_classification:{response_capture.get('http_classification', '')}")
    return {
        "request_decision": payload.get("decision", ""),
        "request_clickup_import_csv": payload.get("clickup_import_csv", ""),
        "response_received": response_capture.get("response_received", False),
        "http_status": response_capture.get("http_status", ""),
        "http_classification": response_capture.get("http_classification", ""),
        "archive_crosscheck_ok": archive_crosscheck_ok,
        "local_test_mode": local_test_mode,
        "request_export_ready": bool(payload.get("clickup_import_csv", "")),
        "archive_dir_exists": archive_crosscheck.get("archive_dir_exists", False),
        "archive_manifest_exists": archive_crosscheck.get("archive_manifest_exists", False),
        "clickup_csv_match": archive_crosscheck.get("clickup_csv_match", False),
        "run_manifest_match": archive_crosscheck.get("run_manifest_match", False),
        "mismatch_reasons": mismatch_reasons,
        "reconciliation_status": "local_simulated_match" if local_test_mode and archive_crosscheck_ok else "matched" if archive_crosscheck_ok else "review_required",
    }


def build_post_webhook_reconciliation_txt(reconciliation: dict[str, Any]) -> str:
    lines = [
        "Post-webhook reconciliation summary",
        f"request_decision: {reconciliation.get('request_decision', '')}",
        f"response_received: {'yes' if reconciliation.get('response_received', False) else 'no'}",
        f"http_status: {reconciliation.get('http_status', '')}",
        f"http_classification: {reconciliation.get('http_classification', '')}",
        f"archive_crosscheck_ok: {'yes' if reconciliation.get('archive_crosscheck_ok', False) else 'no'}",
        f"reconciliation_status: {reconciliation.get('reconciliation_status', '')}",
        f"mismatch_reasons: {', '.join(reconciliation.get('mismatch_reasons', [])) if reconciliation.get('mismatch_reasons') else 'none'}",
    ]
    return "\n".join(lines) + "\n"


def build_runtime_metrics_snapshot(
    validation_issues: list[str],
    payload: dict[str, str],
    response_capture: dict[str, Any],
    retry_backoff_plan: dict[str, Any],
) -> dict[str, Any]:
    payload_path_keys = [key for key in payload if is_path_like_key(key)]
    return {
        "validation_issue_count": len(validation_issues),
        "payload_key_count": len(payload),
        "payload_path_key_count": len(payload_path_keys),
        "response_received": response_capture.get("response_received", False),
        "http_classification": response_capture.get("http_classification", ""),
        "retry_attempt_count_planned": len(retry_backoff_plan.get("attempts", [])),
    }


def build_lock_contention_test(config: dict[str, Any], output_dir: Optional[Path]) -> dict[str, Any]:
    scenario_label = "lock_contention_probe"
    lock_path = resolve_output_path(config, "execution_lock_path", output_dir).with_name("orchestration_execution_lock_test.json")
    first_lock = acquire_execution_lock(lock_path, scenario_label)
    try:
        acquire_execution_lock(lock_path, f"{scenario_label}_second")
        second_lock_blocked = False
        error_message = ""
    except RuntimeError as exc:
        second_lock_blocked = True
        error_message = str(exc)
    finally:
        released = release_execution_lock(lock_path, scenario_label)
    final_state = load_json(lock_path)
    return {
        "first_lock_active": first_lock.get("active", False),
        "second_lock_blocked": second_lock_blocked,
        "error_message": error_message,
        "release_written": released.get("active", True) is False,
        "final_lock_inactive": final_state.get("active", True) is False,
    }


def build_runtime_status_board(
    decision_summary: dict[str, Any],
    retry_eligibility: dict[str, Any],
    launch_checklist: dict[str, Any],
    payload: dict[str, str],
    manifest_path: Path,
    gate_path: Path,
    rehearsal_path: Path,
) -> dict[str, Any]:
    return {
        "phase": "phase_6_execution_readiness",
        "scenario_label": decision_summary.get("scenario_label", ""),
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "decision": decision_summary.get("decision", ""),
        "status": decision_summary.get("status", ""),
        "failure_type": decision_summary.get("failure_type", ""),
        "retry_allowed_now": retry_eligibility.get("retry_allowed_now", False),
        "launch_ready": all(launch_checklist.values()) if launch_checklist else False,
        "live_webhook_requested": decision_summary.get("live_webhook_requested", False),
        "external_blocker_detected": decision_summary.get("external_blocker_detected", False),
        "external_blocker_code": decision_summary.get("external_blocker_code", ""),
        "partial_write_detected": decision_summary.get("partial_write_detected", False),
        "operator_action": decision_summary.get("operator_action", ""),
        "launch_blockers": decision_summary.get("launch_blockers", []),
        "source_artifacts": {
            "manifest_path": str(manifest_path),
            "gate_path": str(gate_path),
            "rehearsal_path": str(rehearsal_path),
            "archive_dir": payload.get("archive_dir", ""),
        },
    }


def build_progress_tracker(
    decision_summary: dict[str, Any],
    validation_issues: list[str],
) -> dict[str, Any]:
    return {
        "phase": "phase_6_execution_readiness",
        "progress_band": "implementation_active",
        "runner_cli_modes_ready": True,
        "artifact_checker_ready": True,
        "decision_summary_ready": True,
        "txt_summary_ready": True,
        "archive_resolver_ready": True,
        "flow_integration_ready": True,
        "simulated_go_ready": True,
        "open_validation_issues": validation_issues,
        "current_status": decision_summary.get("status", ""),
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
        "external_blocker_detected": bool(detect_external_blocker_code(str(rehearsal.get("error", "")))),
        "external_blocker_code": detect_external_blocker_code(str(rehearsal.get("error", ""))),
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
    live_webhook_requested: bool = False,
    simulated_response_path: Optional[Path] = None,
    simulated_archive_crosscheck_path: Optional[Path] = None,
) -> dict[str, Any]:
    config = load_config()
    project_config = load_project_config()
    override_config = load_override_config()
    webhook_runtime = resolve_webhook_runtime(config, override_config)
    simulated_response_capture = load_simulated_response_capture(simulated_response_path)
    simulated_archive_crosscheck = load_simulated_archive_crosscheck(simulated_archive_crosscheck_path)
    manifest = load_json(manifest_path)
    gate = load_json(gate_path)
    rehearsal = load_json(rehearsal_path)
    lock_path = resolve_output_path(config, "execution_lock_path", output_dir)
    acquire_execution_lock(lock_path, scenario_label)

    try:
        payload = build_make_payload(manifest, gate, manifest_path, gate_path, override_config)
        validation_issues, _missing_paths = validate_make_payload(payload, config)
        artifact_check = build_artifact_check(payload, config)
        payload_validation = build_payload_validation(payload, validation_issues, config)
        notification_payload = build_failure_notification(
            payload,
            gate,
            rehearsal,
            validation_issues,
            config,
            gate_path,
            rehearsal_path,
        )
        retry_eligibility = build_retry_eligibility(notification_payload)
        status = classify_runtime_status(payload, rehearsal, validation_issues)
        execution_path = "validate_only" if mode == "validate_only" else "dry_run"
        status_output = build_status_matrix_output(status, payload, validation_issues, rehearsal)
        would_execute_make = payload.get("decision") == "GO" and not validation_issues and mode != "validate_only"
        archive_crosscheck = build_archive_crosscheck(payload, manifest)
        if simulated_archive_crosscheck:
            archive_crosscheck.update(simulated_archive_crosscheck)
        archive_retention_crosscheck = build_archive_retention_crosscheck(project_config)
        retry_backoff_plan = build_retry_backoff_plan(config, retry_eligibility)
        webhook_request_export = build_webhook_request_export(
            payload,
            scenario_label,
            webhook_runtime["webhook_url"],
            webhook_runtime["webhook_enabled"],
            webhook_runtime["force_noop"],
        )
        response_capture_template = build_response_capture_template(scenario_label)
        decision_summary = build_decision_summary(
            payload,
            status,
            validation_issues,
            notification_payload,
            rehearsal,
            would_execute_make,
            scenario_label,
            live_webhook_requested,
        )
        response_capture = execute_make_webhook(payload, decision_summary, webhook_runtime, live_webhook_requested, simulated_response_capture)
        notification_payload = apply_response_to_notification(notification_payload, response_capture, config)
        retry_eligibility = build_retry_eligibility(notification_payload)
        retry_backoff_plan = build_retry_backoff_plan(config, retry_eligibility)
        decision_summary = build_decision_summary(
            payload,
            status,
            validation_issues,
            notification_payload,
            rehearsal,
            would_execute_make,
            scenario_label,
            live_webhook_requested,
        )
        evidence_log = build_evidence_log(
            payload,
            status,
            validation_issues,
            notification_payload,
            rehearsal,
            execution_path,
            response_capture,
            live_webhook_requested,
        )
        txt_summary = build_txt_summary(decision_summary, payload, validation_issues)
        incident_summary = build_incident_summary(decision_summary, notification_payload, evidence_log)
        escalation_artifact = build_escalation_artifact(decision_summary, notification_payload, evidence_log)
        handoff_bundle = build_handoff_bundle(payload, decision_summary, notification_payload, archive_crosscheck)
        handoff_txt_bundle = build_handoff_txt_bundle(decision_summary, handoff_bundle, retry_eligibility)
        progress_tracker = build_progress_tracker(decision_summary, validation_issues)
        launch_checklist = build_launch_checklist(decision_summary, archive_crosscheck, payload_validation, retry_eligibility, live_webhook_requested, response_capture)
        launch_checklist_txt = build_launch_checklist_txt(decision_summary, launch_checklist)
        launch_gating_summary = build_launch_gating_summary(decision_summary, launch_checklist, response_capture)
        runtime_status_board = build_runtime_status_board(decision_summary, retry_eligibility, launch_checklist, payload, manifest_path, gate_path, rehearsal_path)
        post_webhook_reconciliation = build_post_webhook_reconciliation(payload, response_capture, archive_crosscheck)
        post_webhook_reconciliation_txt = build_post_webhook_reconciliation_txt(post_webhook_reconciliation)
        runtime_metrics_snapshot = build_runtime_metrics_snapshot(validation_issues, payload, response_capture, retry_backoff_plan)
        lock_contention_test = build_lock_contention_test(config, output_dir)
    finally:
        release_execution_lock(lock_path, scenario_label)

    make_payload_path = resolve_output_path(config, "make_payload_path", output_dir)
    failure_notification_path = resolve_output_path(config, "failure_notification_path", output_dir)
    evidence_log_path = resolve_output_path(config, "evidence_log_path", output_dir)
    status_matrix_path = resolve_output_path(config, "status_matrix_path", output_dir)
    artifact_check_path = resolve_output_path(config, "artifact_check_path", output_dir)
    decision_summary_path = resolve_output_path(config, "decision_summary_path", output_dir)
    txt_summary_path = resolve_output_path(config, "txt_summary_path", output_dir)
    payload_validation_path = resolve_output_path(config, "payload_validation_path", output_dir)
    archive_crosscheck_path = resolve_output_path(config, "archive_crosscheck_path", output_dir)
    incident_summary_path = resolve_output_path(config, "incident_summary_path", output_dir)
    escalation_path = resolve_output_path(config, "escalation_path", output_dir)
    handoff_bundle_path = resolve_output_path(config, "handoff_bundle_path", output_dir)
    progress_tracker_path = resolve_output_path(config, "progress_tracker_path", output_dir)
    retry_eligibility_path = resolve_output_path(config, "retry_eligibility_path", output_dir)
    webhook_request_export_path = resolve_output_path(config, "webhook_request_export_path", output_dir)
    response_capture_template_path = resolve_output_path(config, "response_capture_template_path", output_dir)
    handoff_txt_bundle_path = resolve_output_path(config, "handoff_txt_bundle_path", output_dir)
    launch_checklist_path = resolve_output_path(config, "launch_checklist_path", output_dir)
    launch_checklist_txt_path = resolve_output_path(config, "launch_checklist_txt_path", output_dir)
    launch_gating_summary_path = resolve_output_path(config, "launch_gating_summary_path", output_dir)
    post_webhook_reconciliation_path = resolve_output_path(config, "post_webhook_reconciliation_path", output_dir)
    post_webhook_reconciliation_txt_path = post_webhook_reconciliation_path.with_suffix(".txt")
    runtime_metrics_snapshot_path = resolve_output_path(config, "runtime_metrics_snapshot_path", output_dir)
    lock_contention_test_path = resolve_output_path(config, "lock_contention_test_path", output_dir)
    runtime_status_board_path = resolve_output_path(config, "status_matrix_path", output_dir).with_name("phase_6_runtime_status_board.json")
    archive_retention_crosscheck_path = resolve_output_path(config, "archive_crosscheck_path", output_dir).with_name("archive_retention_crosscheck.json")
    dry_run_result_path = resolve_output_path(config, "dry_run_result_path", output_dir)

    save_json(make_payload_path, payload)
    save_json(failure_notification_path, notification_payload)
    save_json(evidence_log_path, evidence_log)
    save_json(status_matrix_path, status_output)
    save_json(artifact_check_path, artifact_check)
    save_json(decision_summary_path, decision_summary)
    save_text(txt_summary_path, txt_summary)
    save_json(payload_validation_path, payload_validation)
    save_json(archive_crosscheck_path, archive_crosscheck)
    save_text(incident_summary_path, incident_summary)
    save_json(escalation_path, escalation_artifact)
    save_json(handoff_bundle_path, handoff_bundle)
    save_json(progress_tracker_path, progress_tracker)
    save_json(retry_eligibility_path, retry_eligibility)
    save_json(webhook_request_export_path, webhook_request_export)
    response_capture_template.update(response_capture)
    save_json(response_capture_template_path, response_capture_template)
    save_text(handoff_txt_bundle_path, handoff_txt_bundle)
    save_json(launch_checklist_path, launch_checklist)
    save_text(launch_checklist_txt_path, launch_checklist_txt)
    save_text(launch_gating_summary_path, launch_gating_summary)
    save_json(post_webhook_reconciliation_path, post_webhook_reconciliation)
    save_text(post_webhook_reconciliation_txt_path, post_webhook_reconciliation_txt)
    save_json(runtime_metrics_snapshot_path, runtime_metrics_snapshot)
    save_json(lock_contention_test_path, lock_contention_test)
    save_json(runtime_status_board_path, runtime_status_board)
    save_json(archive_retention_crosscheck_path, archive_retention_crosscheck)
    save_json(lock_path, {"active": False, "scenario_label": scenario_label, "released_at": datetime.now().astimezone().isoformat(timespec="seconds")})

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
        "payload_validation_path": str(payload_validation_path),
        "archive_crosscheck_path": str(archive_crosscheck_path),
        "incident_summary_path": str(incident_summary_path),
        "escalation_path": str(escalation_path),
        "handoff_bundle_path": str(handoff_bundle_path),
        "progress_tracker_path": str(progress_tracker_path),
        "retry_eligibility_path": str(retry_eligibility_path),
        "webhook_request_export_path": str(webhook_request_export_path),
        "response_capture_template_path": str(response_capture_template_path),
        "handoff_txt_bundle_path": str(handoff_txt_bundle_path),
        "launch_checklist_path": str(launch_checklist_path),
        "launch_checklist_txt_path": str(launch_checklist_txt_path),
        "launch_gating_summary_path": str(launch_gating_summary_path),
        "post_webhook_reconciliation_path": str(post_webhook_reconciliation_path),
        "post_webhook_reconciliation_txt_path": str(post_webhook_reconciliation_txt_path),
        "runtime_metrics_snapshot_path": str(runtime_metrics_snapshot_path),
        "lock_contention_test_path": str(lock_contention_test_path),
        "runtime_status_board_path": str(runtime_status_board_path),
        "archive_retention_crosscheck_path": str(archive_retention_crosscheck_path),
        "execution_lock_path": str(lock_path),
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
    parser.add_argument(
        "--live-webhook",
        action="store_true",
        help="Povolí live webhook vetvu, stále gated cez env a safe no-op pravidlá.",
    )
    parser.add_argument(
        "--simulated-response",
        default="",
        help="Voliteľný JSON so simulovaným Make response capture payloadom.",
    )
    parser.add_argument(
        "--simulated-archive-crosscheck",
        default="",
        help="Voliteľný JSON so simulovaným archive crosscheck override payloadom.",
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
        live_webhook_requested=args.live_webhook,
        simulated_response_path=Path(args.simulated_response) if args.simulated_response else None,
        simulated_archive_crosscheck_path=Path(args.simulated_archive_crosscheck) if args.simulated_archive_crosscheck else None,
    )
    print("Make orchestration run dokončený.")
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
