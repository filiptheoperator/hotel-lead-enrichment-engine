# Make Execution Payload Contract

## Stav

Tento dokument uzamyká payload, ktorý má lokálny Python workflow odovzdať do Make vrstvy.

## Source of truth

- [configs/make_execution_payload_contract.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/make_execution_payload_contract.yaml)
- [docs/project/MAKE_READY_HANDOFF_SPEC.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_READY_HANDOFF_SPEC.md)
- [data/qa/run_manifest.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_manifest.json)

## Locked payload

```json
{
  "decision": "GO | NO_GO",
  "run_manifest_json": "data/qa/run_manifest.json",
  "clickup_import_gate_json": "data/qa/clickup_import_gate.json",
  "clickup_import_csv": "outputs/clickup/..._clickup_import.csv",
  "clickup_import_dry_run_sample_csv": "data/qa/clickup_import_dry_run_sample.csv",
  "high_leads_preimport_checklist_csv": "data/qa/high_leads_preimport_checklist.csv",
  "operator_decision_summary_txt": "data/qa/operator_decision_summary.txt",
  "archive_dir": "data/archive/<batch_archive_dir>",
  "clickup_import_gate_high_only_json": "data/qa/clickup_import_gate_high_only.json",
  "operator_decision_summary_high_txt": "data/qa/operator_decision_summary_high.txt",
  "batch_readiness_explanation_json": "data/qa/batch_readiness_explanation.json",
  "clickup_api_mapping_validation_json": "data/qa/clickup_api_mapping_validation.json"
}
```

## Required fields

- `decision`
- `run_manifest_json`
- `clickup_import_gate_json`
- `clickup_import_csv`
- `clickup_import_dry_run_sample_csv`
- `high_leads_preimport_checklist_csv`
- `operator_decision_summary_txt`
- `archive_dir`

## Optional fields

- `clickup_import_gate_high_only_json`
- `operator_decision_summary_high_txt`
- `batch_readiness_explanation_json`
- `clickup_api_mapping_validation_json`

## Rules

- všetky path hodnoty ostávajú relatívne voči rootu repo
- Make iba číta artifacty, nič neprepočítava
- Make scenario provisioning vrstva má nasadiť iba tento uzamknutý contract
- pri `decision = NO_GO` nesmie nastať pokus o live ClickUp execution
- chýbajúci required artifact je hard stop
- Make nevymýšľa outbound copy, iba pracuje s artifactmi pripravenými lokálnym Python flow
- outreach testing polia cestujú v `clickup_import_csv`, nie ako samostatná Make business logika

## Provisioning poznámka

- Make scenario blueprint musí zostať tenký
- trigger vrstva iba prijme payload a odovzdá artifact paths ďalej
- connections a secrets môžu vyžadovať jednorazový manuálny bind v Make
- blueprint template je v [configs/make_scenario_blueprint.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/make_scenario_blueprint.json)

## Neoverené

- presný scenár volania Make webhooku alebo modulu
- live orchestration medzi Make a ClickUp
