# MODULE INVENTORY

## Legend

- `canonical`
- `active supporting`
- `optional`
- `sim/test`
- `legacy`
- `archive candidate`

## Entry a flow control

- [`src/main.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/main.py): `canonical`
- [`src/orchestrate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestrate.py): `active supporting`

Poznámka:
`orchestrate.py` je dnes hlavný wrapper, ale nie je plne zosúladený s intended canonical flow.

## Ingest / Normalize / Enrichment / Ranking

- [`src/ingest/raw_loader.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/ingest/raw_loader.py): `active supporting`
- [`src/normalize_score.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/normalize_score.py): `canonical`
- [`src/enrich_hotels.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/enrich_hotels.py): `canonical`
- [`src/commercial_synthesizer.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/commercial_synthesizer.py): `canonical`
- [`src/ranking_refresh.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/ranking_refresh.py): `canonical`

## Outreach / Exports / Render

- [`src/email_drafts.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/email_drafts.py): `canonical`
- [`src/master_exports.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/master_exports.py): `canonical`
- [`src/render_full_enrichment_md.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/render_full_enrichment_md.py): `canonical`
- [`src/clickup_export.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_export.py): `canonical`

## QA / Reporting / Operator Gate

- [`src/qa_checks.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/qa_checks.py): `canonical`
- [`src/clickup_import_gate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_import_gate.py): `canonical`
- [`src/run_manifest.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/run_manifest.py): `active supporting`
- [`src/run_report.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/run_report.py): `active supporting`
- [`src/high_leads_preimport_checklist.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/high_leads_preimport_checklist.py): `active supporting`
- [`src/operator_decision_summary.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/operator_decision_summary.py): `active supporting`

## ClickUp support / rehearsal / packets

- [`src/clickup_dry_run_sample.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_dry_run_sample.py): `active supporting`
- [`src/clickup_api_mapping_preview.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_api_mapping_preview.py): `active supporting`
- [`src/clickup_import_preflight.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_import_preflight.py): `active supporting`
- [`src/clickup_import_support_artifacts.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_import_support_artifacts.py): `active supporting`
- [`src/clickup_import_operator_pack.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_import_operator_pack.py): `active supporting`
- [`src/clickup_dry_run_packet.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_dry_run_packet.py): `active supporting`
- [`src/clickup_live_field_discovery.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_live_field_discovery.py): `active supporting`
- [`src/clickup_rehearsal_write.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_rehearsal_write.py): `active supporting`

## Make orchestration / provisioning

- [`src/make_orchestration_runner.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_orchestration_runner.py): `canonical`
- [`src/make_scenario_deploy.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_scenario_deploy.py): `active supporting`
- [`src/make_scenario_test_run.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_scenario_test_run.py): `active supporting`
- [`src/make_id_helper.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_id_helper.py): `active supporting`

## Archive management

- [`src/archive_run_artifacts.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/archive_run_artifacts.py): `active supporting`
- [`src/archive_cleanup.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/archive_cleanup.py): `active supporting`

## Sim / test / regression

- [`src/orchestration_smoke_test.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestration_smoke_test.py): `sim/test`
- [`src/orchestration_regression_report.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestration_regression_report.py): `sim/test`
- [`src/orchestration_stateful_scenarios.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestration_stateful_scenarios.py): `sim/test`
- [`src/checkin_checkout_regression.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/checkin_checkout_regression.py): `sim/test`
- [`src/checkin_checkout_spotcheck.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/checkin_checkout_spotcheck.py): `sim/test`

## Legacy / archive candidate

- v `src/` momentálne nemám jednoznačný samostatný runtime skript, ktorý by som označil ako čistý `legacy`.
- v `src/` momentálne nemám jednoznačný samostatný runtime skript, ktorý by som označil ako `archive candidate` bez ďalšieho owner rozhodnutia.

Najbližšie k tejto hrane je:

- [`src/orchestrate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestrate.py): nie je legacy, ale potrebuje review
- heuristická commercial logika vo vnútri [`src/enrich_hotels.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/enrich_hotels.py): nie je samostatný modul, ale je to vnútorný conflict point

## Non-module artifacts

- `src/.DS_Store`: mimo inventára modulov, technicky delete candidate
