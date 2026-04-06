import json
from pathlib import Path
from typing import Any


QA_DIR = Path("data/qa")


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def summarize_sequence(name: str, sequence_path: Path) -> dict[str, Any]:
    payload = load_json(sequence_path)
    steps = payload.get("steps", [])
    retry_count = sum(1 for step in steps if step.get("action") == "retry")
    escalation_count = sum(1 for step in steps if step.get("action") == "escalate")
    fix_count = sum(1 for step in steps if step.get("action") == "request_fix")
    final = steps[-1] if steps else {}
    summary = {
        "scenario": name,
        "step_count": len(steps),
        "retry_count": retry_count,
        "escalation_count": escalation_count,
        "request_fix_count": fix_count,
        "final_status": final.get("status", ""),
        "final_failure_type": final.get("failure_type", ""),
        "final_decision": final.get("decision", ""),
        "expected_outcome": payload.get("expected_outcome", ""),
        "matches_expected_outcome": final.get("status", "") == payload.get("expected_outcome", ""),
    }
    output_dir = sequence_path.parent / "output"
    save_json(output_dir / "stateful_summary.json", summary)
    return summary


def main() -> None:
    scenario_paths = {
        "stateful_http_5xx_retry_escalation": QA_DIR / "stateful_http_5xx_retry_escalation" / "sequence.json",
        "stateful_http_4xx_request_fix_recovery": QA_DIR / "stateful_http_4xx_request_fix_recovery" / "sequence.json",
        "stateful_network_error_retry_success": QA_DIR / "stateful_network_error_retry_success" / "sequence.json",
        "stateful_network_error_missing_archive_manifest": QA_DIR / "stateful_network_error_missing_archive_manifest" / "sequence.json",
    }
    summaries = {name: summarize_sequence(name, path) for name, path in scenario_paths.items()}
    save_json(QA_DIR / "orchestration_stateful_scenarios.json", summaries)
    print(json.dumps(summaries, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
