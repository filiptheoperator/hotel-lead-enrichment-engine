import json
from pathlib import Path


QA_DIR = Path("data/qa")


def load_json(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    comparison = load_json(QA_DIR / "orchestration_scenario_comparison.json")
    expectation_checks = load_json(QA_DIR / "orchestration_expectation_checks.json")
    artifact_checks = load_json(QA_DIR / "orchestration_artifact_checks.json")
    http_behavior_checks = load_json(QA_DIR / "orchestration_http_behavior_checks.json")
    blocker_checks = load_json(QA_DIR / "orchestration_blocker_checks.json")
    ready_to_transition_checks = load_json(QA_DIR / "orchestration_ready_to_transition_checks.json")
    smoke_test = load_json(QA_DIR / "orchestration_smoke_test.json")
    stateful_scenarios = load_json(QA_DIR / "orchestration_stateful_scenarios.json")

    all_http_behavior_checks_pass = (
        http_behavior_checks.get("simulated_http_5xx", {}).get("retry_allowed_now", False) is True
        and http_behavior_checks.get("simulated_http_4xx", {}).get("retry_allowed_now", True) is False
        and http_behavior_checks.get("simulated_network_error", {}).get("retry_allowed_now", False) is True
    )
    status_summary = {
        "READY": sum(1 for scenario in comparison.values() if str(scenario.get("status", "")).startswith("READY")),
        "BLOCKED": sum(1 for scenario in comparison.values() if str(scenario.get("status", "")).startswith("BLOCKED")),
        "FAIL_like": sum(1 for scenario in comparison.values() if "FAIL" in str(scenario.get("status", "")).upper()),
    }
    failure_type_summary: dict[str, int] = {}
    for result in smoke_test.values():
        failure_notification_path = result.get("failure_notification_path", "")
        if not failure_notification_path:
            continue
        failure_type = str(load_json(Path(failure_notification_path)).get("failure_type", "")).strip() or "unknown"
        failure_type_summary[failure_type] = failure_type_summary.get(failure_type, 0) + 1
    severity_order = {
        "BLOCKED_INTERNAL": 0,
        "BLOCKED_EXTERNAL": 1,
        "READY_FOR_REMEDIATION": 2,
        "READY_FOR_PLANNING": 3,
        "READY_FOR_LIVE_CUTOVER": 4,
    }
    scenarios_by_severity = [
        {
            "scenario": name,
            "status": scenario.get("status", ""),
        }
        for name, scenario in sorted(
            comparison.items(),
            key=lambda item: (severity_order.get(str(item[1].get("status", "")), 99), item[0]),
        )
    ]
    report = {
        "scenario_count": len(comparison),
        "all_expectations_pass": all(item.get("pass", False) for item in expectation_checks.values()),
        "all_artifact_checks_pass": all(all(checks.values()) for checks in artifact_checks.values()),
        "all_http_behavior_checks_pass": all_http_behavior_checks_pass,
        "status_summary": status_summary,
        "http_behavior_checks": http_behavior_checks,
        "blocker_checks": blocker_checks,
        "ready_to_transition_checks": ready_to_transition_checks,
        "failure_type_summary": failure_type_summary,
        "trend_summary": {
            "wave_1": "smoke test baseline established",
            "wave_2": "http and blocker simulation coverage added",
            "wave_3": "operator packet and sop layer added",
            "wave_4": "archive and transition gating coverage added",
            "wave_5": "incident index and evidence pack layer added",
        },
        "stateful_scenarios": stateful_scenarios,
        "scenarios_by_severity": scenarios_by_severity,
        "scenarios": comparison,
    }

    txt_lines = [
        "Orchestration regression report",
        f"scenario_count: {report['scenario_count']}",
        f"all_expectations_pass: {'yes' if report['all_expectations_pass'] else 'no'}",
        f"all_artifact_checks_pass: {'yes' if report['all_artifact_checks_pass'] else 'no'}",
        f"all_http_behavior_checks_pass: {'yes' if report['all_http_behavior_checks_pass'] else 'no'}",
        f"ready_count: {status_summary['READY']}",
        f"blocked_count: {status_summary['BLOCKED']}",
        f"fail_like_count: {status_summary['FAIL_like']}",
        f"http_5xx_retry_allowed: {'yes' if http_behavior_checks.get('simulated_http_5xx', {}).get('retry_allowed_now', False) else 'no'}",
        f"http_4xx_retry_allowed: {'yes' if http_behavior_checks.get('simulated_http_4xx', {}).get('retry_allowed_now', False) else 'no'}",
        f"network_error_retry_allowed: {'yes' if http_behavior_checks.get('simulated_network_error', {}).get('retry_allowed_now', False) else 'no'}",
        f"cloudflare_blocker_code_ok: {'yes' if blocker_checks.get('simulated_blocked_external_cloudflare', {}).get('external_blocker_code', '') == 'CLOUDFLARE_1010' else 'no'}",
        f"ready_to_transition_go: {'yes' if ready_to_transition_checks.get('simulated_go', False) else 'no'}",
        f"ready_to_transition_no_go: {'yes' if ready_to_transition_checks.get('simulated_no_go', False) else 'no'}",
        "trend_summary:",
        "- wave_1: smoke test baseline established",
        "- wave_2: http and blocker simulation coverage added",
        "- wave_3: operator packet and SOP layer added",
        "- wave_4: archive and transition gating coverage added",
        "- wave_5: incident index and evidence pack layer added",
        "failure_type_summary:",
        *[f"- {name}: {count}" for name, count in sorted(failure_type_summary.items())],
        "stateful_scenarios:",
        *[
            f"- {name}: final_status={summary.get('final_status', '')}, matches_expected_outcome={'yes' if summary.get('matches_expected_outcome', False) else 'no'}"
            for name, summary in stateful_scenarios.items()
        ],
        "severity_order:",
        *[f"- {item['scenario']}: {item['status']}" for item in scenarios_by_severity],
    ]

    (QA_DIR / "orchestration_regression_report.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    (QA_DIR / "orchestration_regression_report.txt").write_text(
        "\n".join(txt_lines) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
