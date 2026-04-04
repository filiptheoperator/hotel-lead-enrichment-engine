# Make Payload Example Pack

## GO payload example

```json
{
  "decision": "GO",
  "run_manifest_json": "data/qa/run_manifest.json",
  "clickup_import_gate_json": "data/qa/clickup_import_gate.json",
  "clickup_import_csv": "outputs/clickup/raw_bratislava region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv",
  "clickup_import_dry_run_sample_csv": "data/qa/clickup_import_dry_run_sample.csv",
  "high_leads_preimport_checklist_csv": "data/qa/high_leads_preimport_checklist.csv",
  "operator_decision_summary_txt": "data/qa/operator_decision_summary.txt",
  "archive_dir": "data/archive/raw_bratislava region_2026-04-01_21-01-58-857__2026-04-04__22-36-44_02-00",
  "clickup_import_gate_high_only_json": "data/qa/clickup_import_gate_high_only.json",
  "operator_decision_summary_high_txt": "data/qa/operator_decision_summary_high.txt",
  "batch_readiness_explanation_json": "data/qa/batch_readiness_explanation.json",
  "clickup_api_mapping_validation_json": "data/qa/clickup_api_mapping_validation.json"
}
```

## NO_GO payload example

```json
{
  "decision": "NO_GO",
  "run_manifest_json": "data/qa/run_manifest.json",
  "clickup_import_gate_json": "data/qa/clickup_import_gate.json",
  "clickup_import_csv": "outputs/clickup/raw_bratislava region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv",
  "clickup_import_dry_run_sample_csv": "data/qa/clickup_import_dry_run_sample.csv",
  "high_leads_preimport_checklist_csv": "data/qa/high_leads_preimport_checklist.csv",
  "operator_decision_summary_txt": "data/qa/operator_decision_summary.txt",
  "archive_dir": "data/archive/raw_bratislava region_2026-04-01_21-01-58-857__2026-04-04__22-36-44_02-00"
}
```

## External blocker notification payload example

```json
{
  "failure_stage": "clickup_rehearsal_write",
  "failure_type": "clickup_external_blocker",
  "batch_decision": "NO_GO",
  "affected_artifact": "data/qa/clickup_rehearsal_execution.json",
  "operator_action": "Nepokracovat dalsim write pokusom.",
  "retry_allowed": "no",
  "next_step": "Evidovat blocker a pokracovat v ostatnych Phase 4 artefaktoch."
}
```
