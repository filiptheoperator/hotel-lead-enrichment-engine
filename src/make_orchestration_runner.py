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
    }
    save_json(path, payload)
    return payload


def release_execution_lock(path: Path, scenario_label: str) -> dict[str, Any]:
    payload = {
        "active": False,
        "scenario_label": scenario_label,
        "released_at": datetime.now().astimezone().isoformat(timespec="seconds"),
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


def build_retry_eligibility(notification_payload: dict[str, Any]) -> dict[str, Any]:
    failure_type = str(notification_payload.get("failure_type", "")).strip()
    retry_allowed = failure_type in {"none"}
    return {
        "failure_type": failure_type,
        "retry_allowed_now": retry_allowed,
        "reason": "retry iba pri bezchybnom alebo explicitne povolenom stave" if retry_allowed else "retry nie je povolený pre aktuálny failure type",
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
    }


def build_handoff_bundle(
    payload: dict[str, str],
    decision_summary: dict[str, Any],
    notification_payload: dict[str, Any],
    archive_crosscheck: dict[str, Any],
) -> dict[str, Any]:
    return {
        "decision": payload.get("decision", ""),
        "status": decision_summary.get("status", ""),
        "would_execute_make": decision_summary.get("would_execute_make", False),
        "run_manifest_json": payload.get("run_manifest_json", ""),
        "clickup_import_gate_json": payload.get("clickup_import_gate_json", ""),
        "archive_dir": payload.get("archive_dir", ""),
        "archive_crosscheck_ok": archive_crosscheck.get("archive_manifest_exists", False)
        and archive_crosscheck.get("clickup_csv_match", False),
        "notification_failure_type": notification_payload.get("failure_type", ""),
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
        f"archive_crosscheck_ok: {'yes' if handoff_bundle['archive_crosscheck_ok'] else 'no'}",
        f"failure_type: {handoff_bundle['notification_failure_type']}",
        f"retry_allowed_now: {'yes' if retry_eligibility['retry_allowed_now'] else 'no'}",
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

    return {
        "webhook_enabled": to_bool(enabled_value),
        "webhook_url": str(webhook_url).strip(),
        "timeout_seconds": timeout_seconds,
        "force_noop": force_noop,
    }


def execute_make_webhook(
    payload: dict[str, str],
    decision_summary: dict[str, Any],
    runtime: dict[str, Any],
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
        "webhook_target": runtime["webhook_url"] if runtime["webhook_url"] else "UNVERIFIED_MAKE_WEBHOOK",
    }

    if not decision_summary.get("would_execute_make", False):
        response_payload["note"] = "Webhook nebol spustený, lebo scenár nie je execution-ready."
        return response_payload
    if not runtime["webhook_enabled"]:
        response_payload["note"] = "Webhook nebol spustený, lebo feature flag je vypnutý."
        return response_payload
    if not runtime["webhook_url"]:
        response_payload["note"] = "Webhook nebol spustený, lebo chýba MAKE_WEBHOOK_URL."
        return response_payload
    if runtime["force_noop"]:
        response_payload["note"] = "Webhook nebol spustený, lebo force_noop_webhook=true."
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
            response_payload["response_body"] = {
                "raw_text": response_text,
            }
            response_payload["note"] = "Webhook bol úspešne odoslaný."
    except HTTPError as exc:
        response_payload["response_received"] = True
        response_payload["http_status"] = exc.code
        response_payload["response_body"] = {
            "raw_text": exc.read().decode("utf-8", errors="replace"),
        }
        response_payload["note"] = "Webhook request skončil HTTP chybou."
    except URLError as exc:
        response_payload["note"] = f"Webhook request zlyhal na sieťovej chybe: {exc.reason}"

    return response_payload


def build_launch_checklist(
    decision_summary: dict[str, Any],
    archive_crosscheck: dict[str, Any],
    payload_validation: dict[str, Any],
    retry_eligibility: dict[str, Any],
) -> dict[str, Any]:
    return {
        "decision_is_go": decision_summary.get("decision") == "GO",
        "status_ready_for_live_cutover": decision_summary.get("status") == "READY_FOR_LIVE_CUTOVER",
        "payload_valid": payload_validation.get("valid", False),
        "archive_crosscheck_ok": archive_crosscheck.get("archive_manifest_exists", False) and archive_crosscheck.get("clickup_csv_match", False),
        "retry_allowed_now": retry_eligibility.get("retry_allowed_now", False),
    }


def build_runtime_status_board(
    decision_summary: dict[str, Any],
    retry_eligibility: dict[str, Any],
    launch_checklist: dict[str, Any],
) -> dict[str, Any]:
    return {
        "phase": "phase_5_orchestration_implementation",
        "scenario_label": decision_summary.get("scenario_label", ""),
        "decision": decision_summary.get("decision", ""),
        "status": decision_summary.get("status", ""),
        "failure_type": decision_summary.get("failure_type", ""),
        "retry_allowed_now": retry_eligibility.get("retry_allowed_now", False),
        "launch_ready": all(launch_checklist.values()) if launch_checklist else False,
    }


def build_progress_tracker(
    decision_summary: dict[str, Any],
    validation_issues: list[str],
) -> dict[str, Any]:
    return {
        "phase": "phase_5_orchestration_implementation",
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
    project_config = load_project_config()
    override_config = load_override_config()
    webhook_runtime = resolve_webhook_runtime(config, override_config)
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
        archive_crosscheck = build_archive_crosscheck(payload, manifest)
        archive_retention_crosscheck = build_archive_retention_crosscheck(project_config)
        incident_summary = build_incident_summary(decision_summary, notification_payload, evidence_log)
        escalation_artifact = build_escalation_artifact(decision_summary, notification_payload, evidence_log)
        handoff_bundle = build_handoff_bundle(payload, decision_summary, notification_payload, archive_crosscheck)
        handoff_txt_bundle = build_handoff_txt_bundle(decision_summary, handoff_bundle, retry_eligibility)
        progress_tracker = build_progress_tracker(decision_summary, validation_issues)
        webhook_request_export = build_webhook_request_export(
            payload,
            scenario_label,
            webhook_runtime["webhook_url"],
            webhook_runtime["webhook_enabled"],
            webhook_runtime["force_noop"],
        )
        response_capture_template = build_response_capture_template(scenario_label)
        launch_checklist = build_launch_checklist(decision_summary, archive_crosscheck, payload_validation, retry_eligibility)
        runtime_status_board = build_runtime_status_board(decision_summary, retry_eligibility, launch_checklist)
        response_capture = execute_make_webhook(payload, decision_summary, webhook_runtime)
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
    runtime_status_board_path = resolve_output_path(config, "status_matrix_path", output_dir).with_name("phase_5_runtime_status_board.json")
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
