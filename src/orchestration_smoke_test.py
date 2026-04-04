import json
from pathlib import Path

from make_orchestration_runner import run


QA_DIR = Path("data/qa")
SIM_GO_DIR = QA_DIR / "simulated_go"
SIM_GO_OUTPUT_DIR = SIM_GO_DIR / "output"
SIM_PARTIAL_DIR = QA_DIR / "simulated_partial_write"
SIM_PARTIAL_OUTPUT_DIR = SIM_PARTIAL_DIR / "output"
SIM_MISSING_DIR = QA_DIR / "simulated_missing_artifact"
SIM_MISSING_OUTPUT_DIR = SIM_MISSING_DIR / "output"


def save_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


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
        "simulated_partial_write": run(
            mode="dry_run",
            manifest_path=SIM_PARTIAL_DIR / "run_manifest_partial.json",
            gate_path=SIM_PARTIAL_DIR / "clickup_import_gate_partial.json",
            rehearsal_path=SIM_PARTIAL_DIR / "clickup_rehearsal_partial.json",
            output_dir=SIM_PARTIAL_OUTPUT_DIR,
            scenario_label="smoke_simulated_partial_write",
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
    output_path = QA_DIR / "orchestration_smoke_test.json"
    save_json(output_path, results)
    print(f"Orchestration smoke test uložený do: {output_path}")
    print(json.dumps(results, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
