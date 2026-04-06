import json
from pathlib import Path

from make_orchestration_runner import run
from orchestration_stateful_scenarios import summarize_sequence


QA_DIR = Path("data/qa")
SIM_GO_DIR = QA_DIR / "simulated_go"
SIM_GO_OUTPUT_DIR = SIM_GO_DIR / "output"
SIM_GO_SAFE_NOOP_OUTPUT_DIR = SIM_GO_DIR / "output_safe_noop"
SIM_NO_GO_DIR = QA_DIR / "simulated_no_go"
SIM_NO_GO_OUTPUT_DIR = SIM_NO_GO_DIR / "output"
SIM_BLOCKED_DIR = QA_DIR / "simulated_blocked_external_cloudflare"
SIM_BLOCKED_OUTPUT_DIR = SIM_BLOCKED_DIR / "output"
SIM_PARTIAL_DIR = QA_DIR / "simulated_partial_write"
SIM_PARTIAL_OUTPUT_DIR = SIM_PARTIAL_DIR / "output"
SIM_HTTP_5XX_DIR = QA_DIR / "simulated_http_5xx"
SIM_HTTP_5XX_OUTPUT_DIR = SIM_HTTP_5XX_DIR / "output"
SIM_HTTP_4XX_DIR = QA_DIR / "simulated_http_4xx"
SIM_HTTP_4XX_OUTPUT_DIR = SIM_HTTP_4XX_DIR / "output"
SIM_NETWORK_ERROR_DIR = QA_DIR / "simulated_network_error"
SIM_NETWORK_ERROR_OUTPUT_DIR = SIM_NETWORK_ERROR_DIR / "output"
SIM_BAD_RESPONSE_DIR = QA_DIR / "simulated_missing_http_status"
SIM_BAD_RESPONSE_OUTPUT_DIR = SIM_BAD_RESPONSE_DIR / "output"
SIM_MISSING_ARCHIVE_MANIFEST_DIR = QA_DIR / "simulated_missing_archive_manifest"
SIM_MISSING_ARCHIVE_MANIFEST_OUTPUT_DIR = SIM_MISSING_ARCHIVE_MANIFEST_DIR / "output"
SIM_RUN_MANIFEST_MISMATCH_DIR = QA_DIR / "simulated_run_manifest_mismatch"
SIM_RUN_MANIFEST_MISMATCH_OUTPUT_DIR = SIM_RUN_MANIFEST_MISMATCH_DIR / "output"
SIM_MISSING_DIR = QA_DIR / "simulated_missing_artifact"
SIM_MISSING_OUTPUT_DIR = SIM_MISSING_DIR / "output"


EXPECTED = {
    "default_cli": {"status": "READY_FOR_PLANNING", "would_execute_make": False},
    "validate_only": {"status": "READY_FOR_PLANNING", "would_execute_make": False},
    "simulated_go": {"status": "READY_FOR_LIVE_CUTOVER", "would_execute_make": True},
    "simulated_go_live_send_safe_noop": {"status": "READY_FOR_LIVE_CUTOVER", "would_execute_make": True},
    "simulated_no_go": {"status": "READY_FOR_PLANNING", "would_execute_make": False},
    "simulated_blocked_external_cloudflare": {"status": "BLOCKED_EXTERNAL", "would_execute_make": True},
    "simulated_partial_write": {"status": "BLOCKED_EXTERNAL", "would_execute_make": True},
    "simulated_http_5xx": {"status": "READY_FOR_LIVE_CUTOVER", "would_execute_make": True},
    "simulated_http_4xx": {"status": "READY_FOR_LIVE_CUTOVER", "would_execute_make": True},
    "simulated_network_error": {"status": "READY_FOR_LIVE_CUTOVER", "would_execute_make": True},
    "simulated_missing_http_status": {"status": "READY_FOR_LIVE_CUTOVER", "would_execute_make": True},
    "simulated_missing_archive_manifest": {"status": "READY_FOR_LIVE_CUTOVER", "would_execute_make": True},
    "simulated_run_manifest_mismatch": {"status": "READY_FOR_LIVE_CUTOVER", "would_execute_make": True},
    "simulated_missing_artifact": {"status": "BLOCKED_INTERNAL", "would_execute_make": False},
    "simulated_go_external_blocker_malformed_response": {"status": "BLOCKED_EXTERNAL", "would_execute_make": True},
}

EXPECTED_STATEFUL = {
    "stateful_http_5xx_retry_escalation": "ESCALATED_AFTER_RETRY_LIMIT",
    "stateful_http_4xx_request_fix_recovery": "READY_FOR_LIVE_CUTOVER",
    "stateful_network_error_retry_success": "READY_FOR_LIVE_CUTOVER",
    "stateful_network_error_missing_archive_manifest": "REMEDIATION_REQUIRED",
}


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def save_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def assert_generated_artifacts(result: dict) -> dict:
    decision_summary = load_json(Path(result["decision_summary_path"]))
    status_board = load_json(Path(result["runtime_status_board_path"]))
    handoff_bundle = load_json(Path(result["handoff_bundle_path"]))
    launch_checklist = load_json(Path(result["launch_checklist_path"]))
    reconciliation = load_json(Path(result["post_webhook_reconciliation_path"]))
    handoff_txt = Path(result["handoff_txt_bundle_path"]).read_text(encoding="utf-8")
    reconciliation_txt = Path(result["post_webhook_reconciliation_txt_path"]).read_text(encoding="utf-8")
    checks = {
        "decision_summary_has_status": decision_summary.get("status", "") == result["status"],
        "decision_summary_has_next_step": bool(decision_summary.get("next_step", "").strip()),
        "runtime_status_board_has_phase": bool(status_board.get("phase", "").strip()),
        "runtime_status_board_has_sources": bool(status_board.get("source_artifacts", {}).get("manifest_path", "").strip()),
        "handoff_bundle_has_next_step": bool(handoff_bundle.get("next_step", "").strip()),
        "handoff_bundle_has_ready_to_transition": "ready_to_transition" in handoff_bundle,
        "launch_checklist_has_safe_to_launch": "safe_to_launch" in launch_checklist,
        "reconciliation_has_status": bool(reconciliation.get("reconciliation_status", "").strip()),
        "handoff_txt_has_ready_to_transition": "ready_to_transition:" in handoff_txt,
        "reconciliation_txt_has_status": "reconciliation_status:" in reconciliation_txt,
    }
    if not all(checks.values()):
        failed = [name for name, passed in checks.items() if not passed]
        raise SystemExit(f"Generated artifact check failed: {', '.join(failed)}")
    return checks


def main() -> None:
    results = {
        "default_cli": run(mode="dry_run", scenario_label="smoke_default"),
        "validate_only": run(mode="validate_only", scenario_label="smoke_validate"),
        "simulated_go": run(
            mode="dry_run",
            manifest_path=SIM_GO_DIR / "run_manifest_go.json",
            gate_path=SIM_GO_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_GO_DIR / "clickup_rehearsal_pass.json",
            output_dir=SIM_GO_OUTPUT_DIR,
            scenario_label="smoke_simulated_go",
        ),
        "simulated_go_live_send_safe_noop": run(
            mode="dry_run",
            manifest_path=SIM_GO_DIR / "run_manifest_go.json",
            gate_path=SIM_GO_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_GO_DIR / "clickup_rehearsal_pass.json",
            output_dir=SIM_GO_SAFE_NOOP_OUTPUT_DIR,
            scenario_label="smoke_simulated_go_live_send_safe_noop",
            live_webhook_requested=True,
        ),
        "simulated_no_go": run(
            mode="dry_run",
            manifest_path=SIM_NO_GO_DIR / "run_manifest_no_go.json",
            gate_path=SIM_NO_GO_DIR / "clickup_import_gate_no_go.json",
            rehearsal_path=SIM_NO_GO_DIR / "clickup_rehearsal_no_go.json",
            output_dir=SIM_NO_GO_OUTPUT_DIR,
            scenario_label="smoke_simulated_no_go",
        ),
        "simulated_blocked_external_cloudflare": run(
            mode="dry_run",
            manifest_path=SIM_BLOCKED_DIR / "run_manifest_blocked.json",
            gate_path=SIM_BLOCKED_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_BLOCKED_DIR / "clickup_rehearsal_blocked_cloudflare.json",
            output_dir=SIM_BLOCKED_OUTPUT_DIR,
            scenario_label="smoke_simulated_blocked_external_cloudflare",
        ),
        "simulated_partial_write": run(
            mode="dry_run",
            manifest_path=SIM_PARTIAL_DIR / "run_manifest_partial.json",
            gate_path=SIM_PARTIAL_DIR / "clickup_import_gate_partial.json",
            rehearsal_path=SIM_PARTIAL_DIR / "clickup_rehearsal_partial.json",
            output_dir=SIM_PARTIAL_OUTPUT_DIR,
            scenario_label="smoke_simulated_partial_write",
        ),
        "simulated_http_5xx": run(
            mode="dry_run",
            manifest_path=SIM_HTTP_5XX_DIR / "run_manifest_http_5xx.json",
            gate_path=SIM_HTTP_5XX_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_HTTP_5XX_DIR / "clickup_rehearsal_pass.json",
            output_dir=SIM_HTTP_5XX_OUTPUT_DIR,
            scenario_label="smoke_simulated_http_5xx",
            live_webhook_requested=True,
            simulated_response_path=SIM_HTTP_5XX_DIR / "simulated_response_5xx.json",
        ),
        "simulated_http_4xx": run(
            mode="dry_run",
            manifest_path=SIM_HTTP_4XX_DIR / "run_manifest_http_4xx.json",
            gate_path=SIM_HTTP_4XX_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_HTTP_4XX_DIR / "clickup_rehearsal_pass.json",
            output_dir=SIM_HTTP_4XX_OUTPUT_DIR,
            scenario_label="smoke_simulated_http_4xx",
            live_webhook_requested=True,
            simulated_response_path=SIM_HTTP_4XX_DIR / "simulated_response_4xx.json",
        ),
        "simulated_network_error": run(
            mode="dry_run",
            manifest_path=SIM_NETWORK_ERROR_DIR / "run_manifest_network_error.json",
            gate_path=SIM_NETWORK_ERROR_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_NETWORK_ERROR_DIR / "clickup_rehearsal_pass.json",
            output_dir=SIM_NETWORK_ERROR_OUTPUT_DIR,
            scenario_label="smoke_simulated_network_error",
            live_webhook_requested=True,
            simulated_response_path=SIM_NETWORK_ERROR_DIR / "simulated_response_network_error.json",
        ),
        "simulated_missing_http_status": run(
            mode="dry_run",
            manifest_path=SIM_BAD_RESPONSE_DIR / "run_manifest_missing_http_status.json",
            gate_path=SIM_BAD_RESPONSE_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_BAD_RESPONSE_DIR / "clickup_rehearsal_pass.json",
            output_dir=SIM_BAD_RESPONSE_OUTPUT_DIR,
            scenario_label="smoke_simulated_missing_http_status",
            live_webhook_requested=True,
            simulated_response_path=SIM_BAD_RESPONSE_DIR / "simulated_response_missing_http_status.json",
        ),
        "simulated_missing_archive_manifest": run(
            mode="dry_run",
            manifest_path=SIM_MISSING_ARCHIVE_MANIFEST_DIR / "run_manifest_missing_archive_manifest.json",
            gate_path=SIM_MISSING_ARCHIVE_MANIFEST_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_MISSING_ARCHIVE_MANIFEST_DIR / "clickup_rehearsal_pass.json",
            output_dir=SIM_MISSING_ARCHIVE_MANIFEST_OUTPUT_DIR,
            scenario_label="smoke_simulated_missing_archive_manifest",
            simulated_archive_crosscheck_path=SIM_MISSING_ARCHIVE_MANIFEST_DIR / "simulated_archive_crosscheck_missing_manifest.json",
        ),
        "simulated_run_manifest_mismatch": run(
            mode="dry_run",
            manifest_path=SIM_RUN_MANIFEST_MISMATCH_DIR / "run_manifest_run_manifest_mismatch.json",
            gate_path=SIM_RUN_MANIFEST_MISMATCH_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_RUN_MANIFEST_MISMATCH_DIR / "clickup_rehearsal_pass.json",
            output_dir=SIM_RUN_MANIFEST_MISMATCH_OUTPUT_DIR,
            scenario_label="smoke_simulated_run_manifest_mismatch",
            simulated_archive_crosscheck_path=SIM_RUN_MANIFEST_MISMATCH_DIR / "simulated_archive_crosscheck_run_manifest_mismatch.json",
        ),
        "simulated_go_external_blocker_malformed_response": run(
            mode="dry_run",
            manifest_path=SIM_BLOCKED_DIR / "run_manifest_blocked.json",
            gate_path=SIM_BLOCKED_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_BLOCKED_DIR / "clickup_rehearsal_blocked_cloudflare.json",
            output_dir=SIM_BLOCKED_DIR / "output_malformed_response",
            scenario_label="smoke_simulated_go_external_blocker_malformed_response",
            live_webhook_requested=True,
            simulated_response_path=SIM_BAD_RESPONSE_DIR / "simulated_response_missing_http_status.json",
        ),
        "simulated_missing_artifact": run(
            mode="validate_only",
            manifest_path=SIM_MISSING_DIR / "run_manifest_missing.json",
            gate_path=SIM_MISSING_DIR / "clickup_import_gate_go.json",
            rehearsal_path=SIM_MISSING_DIR / "clickup_rehearsal_pass.json",
            output_dir=SIM_MISSING_OUTPUT_DIR,
            scenario_label="smoke_simulated_missing_artifact",
        ),
    }
    stateful_scenarios = {
        "stateful_http_5xx_retry_escalation": summarize_sequence(
            "stateful_http_5xx_retry_escalation",
            QA_DIR / "stateful_http_5xx_retry_escalation" / "sequence.json",
        ),
        "stateful_http_4xx_request_fix_recovery": summarize_sequence(
            "stateful_http_4xx_request_fix_recovery",
            QA_DIR / "stateful_http_4xx_request_fix_recovery" / "sequence.json",
        ),
        "stateful_network_error_retry_success": summarize_sequence(
            "stateful_network_error_retry_success",
            QA_DIR / "stateful_network_error_retry_success" / "sequence.json",
        ),
        "stateful_network_error_missing_archive_manifest": summarize_sequence(
            "stateful_network_error_missing_archive_manifest",
            QA_DIR / "stateful_network_error_missing_archive_manifest" / "sequence.json",
        ),
    }
    output_path = QA_DIR / "orchestration_smoke_test.json"
    comparison_path = QA_DIR / "orchestration_scenario_comparison.json"
    comparison_txt_path = QA_DIR / "orchestration_scenario_comparison.txt"
    comparison = {
        scenario: {
            "status": result["status"],
            "would_execute_make": result["would_execute_make"],
            "validation_issues": result["validation_issues"],
            "matches_expectation": result["status"] == EXPECTED[scenario]["status"]
            and result["would_execute_make"] == EXPECTED[scenario]["would_execute_make"],
        }
        for scenario, result in results.items()
    }
    expectation_checks = {
        scenario: {
            "expected_status": EXPECTED[scenario]["status"],
            "actual_status": result["status"],
            "expected_would_execute_make": EXPECTED[scenario]["would_execute_make"],
            "actual_would_execute_make": result["would_execute_make"],
            "pass": result["status"] == EXPECTED[scenario]["status"]
            and result["would_execute_make"] == EXPECTED[scenario]["would_execute_make"],
        }
        for scenario, result in results.items()
    }
    artifact_checks = {
        scenario: assert_generated_artifacts(result)
        for scenario, result in results.items()
    }
    http_behavior_checks = {
        "simulated_http_5xx": {
            "retry_allowed_now": load_json(Path(results["simulated_http_5xx"]["retry_eligibility_path"])).get("retry_allowed_now", False),
            "failure_type": load_json(Path(results["simulated_http_5xx"]["failure_notification_path"])).get("failure_type", ""),
        },
        "simulated_http_4xx": {
            "retry_allowed_now": load_json(Path(results["simulated_http_4xx"]["retry_eligibility_path"])).get("retry_allowed_now", False),
            "failure_type": load_json(Path(results["simulated_http_4xx"]["failure_notification_path"])).get("failure_type", ""),
        },
        "simulated_network_error": {
            "retry_allowed_now": load_json(Path(results["simulated_network_error"]["retry_eligibility_path"])).get("retry_allowed_now", False),
            "failure_type": load_json(Path(results["simulated_network_error"]["failure_notification_path"])).get("failure_type", ""),
        },
    }
    blocker_checks = {
        "simulated_blocked_external_cloudflare": {
            "external_blocker_code": load_json(Path(results["simulated_blocked_external_cloudflare"]["decision_summary_path"])).get("external_blocker_code", ""),
        }
    }
    ready_to_transition_checks = {
        "simulated_go": load_json(Path(results["simulated_go"]["handoff_bundle_path"])).get("ready_to_transition", False),
        "simulated_no_go": load_json(Path(results["simulated_no_go"]["handoff_bundle_path"])).get("ready_to_transition", True),
    }
    severity_order_report = load_json(QA_DIR / "orchestration_regression_report.json") if (QA_DIR / "orchestration_regression_report.json").exists() else {}
    if http_behavior_checks["simulated_http_5xx"]["retry_allowed_now"] is not True:
        raise SystemExit("Simulated HTTP 5xx did not allow retry.")
    if http_behavior_checks["simulated_http_4xx"]["retry_allowed_now"] is not False:
        raise SystemExit("Simulated HTTP 4xx incorrectly allowed retry.")
    if http_behavior_checks["simulated_network_error"]["retry_allowed_now"] is not True:
        raise SystemExit("Simulated network_error did not allow retry.")
    if blocker_checks["simulated_blocked_external_cloudflare"]["external_blocker_code"] != "CLOUDFLARE_1010":
        raise SystemExit("Cloudflare blocker code check failed.")
    if ready_to_transition_checks["simulated_go"] is not True:
        raise SystemExit("ready_to_transition failed for GO scenario.")
    if ready_to_transition_checks["simulated_no_go"] is not False:
        raise SystemExit("ready_to_transition failed for NO_GO scenario.")
    missing_http_status_reconciliation = load_json(Path(results["simulated_missing_http_status"]["post_webhook_reconciliation_path"]))
    if "response_without_http_status" not in missing_http_status_reconciliation.get("mismatch_reasons", []):
        raise SystemExit("Missing http_status reconciliation mismatch not detected.")
    missing_archive_manifest_reconciliation = load_json(Path(results["simulated_missing_archive_manifest"]["post_webhook_reconciliation_path"]))
    if "archive_manifest_missing" not in missing_archive_manifest_reconciliation.get("mismatch_reasons", []):
        raise SystemExit("Missing archive manifest reconciliation mismatch not detected.")
    run_manifest_mismatch_reconciliation = load_json(Path(results["simulated_run_manifest_mismatch"]["post_webhook_reconciliation_path"]))
    if "run_manifest_mismatch" not in run_manifest_mismatch_reconciliation.get("mismatch_reasons", []):
        raise SystemExit("Run manifest mismatch reconciliation not detected.")
    existing_scenarios_by_severity = severity_order_report.get("scenarios_by_severity", [])
    if existing_scenarios_by_severity:
        if existing_scenarios_by_severity[0].get("status", "") not in {"BLOCKED_INTERNAL", "BLOCKED_EXTERNAL"}:
            raise SystemExit("scenarios_by_severity is not ordered by severity.")
    for scenario, summary in stateful_scenarios.items():
        if summary.get("final_status", "") != EXPECTED_STATEFUL[scenario]:
            raise SystemExit(f"Stateful scenario failed: {scenario}")
    comparison_txt = "\n".join(
        [
            "Orchestration scenario comparison",
            *[
                f"{scenario}: status={result['status']}, would_execute_make={'yes' if result['would_execute_make'] else 'no'}, validation_issues={','.join(result['validation_issues']) if result['validation_issues'] else 'none'}, matches_expectation={'yes' if comparison[scenario]['matches_expectation'] else 'no'}"
                for scenario, result in comparison.items()
            ],
        ]
    ) + "\n"
    save_json(output_path, results)
    save_json(comparison_path, comparison)
    save_json(QA_DIR / "orchestration_expectation_checks.json", expectation_checks)
    save_json(QA_DIR / "orchestration_artifact_checks.json", artifact_checks)
    save_json(QA_DIR / "orchestration_http_behavior_checks.json", http_behavior_checks)
    save_json(QA_DIR / "orchestration_blocker_checks.json", blocker_checks)
    save_json(QA_DIR / "orchestration_ready_to_transition_checks.json", ready_to_transition_checks)
    save_json(QA_DIR / "orchestration_stateful_scenarios.json", stateful_scenarios)
    save_text(comparison_txt_path, comparison_txt)
    if not all(item["pass"] for item in expectation_checks.values()):
        raise SystemExit("Smoke test expectation mismatch.")
    print(f"Orchestration smoke test uložený do: {output_path}")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
