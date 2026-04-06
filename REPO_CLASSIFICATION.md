# REPO CLASSIFICATION

## Klasifikačné pravidlo pre tento dokument

Táto klasifikácia rozlišuje dve rôzne pravdy:

- `aktuálna runtime pravda`: čo dnes reálne používa default pipeline v [`src/orchestrate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestrate.py)
- `intended architecture truth`: cieľová kanonická flow, ktorú si explicitne určil

Pri konfliktoch som klasifikoval podľa prevádzkovej dôležitosti, stability pipeline a rizika pre budúce cleanup rozhodnutia.

## Top-Level Rodiny

### `src/`
- Klasifikácia: `CANONICAL`
- Dôvod: obsahuje všetku aktívnu pipeline a integračné vrstvy. Nie všetky skripty vnútri sú rovnako kanonické, ale celá rodina je súčasné centrum systému.

### `configs/`
- Klasifikácia: `CANONICAL`
- Dôvod: configs sú runtime contract layer, rozhodujú scoring, enrichment, ClickUp, orchestration a payload shape.

### `prompts/`
- Klasifikácia: `ACTIVE SUPPORTING`
- Dôvod: prompt assets existujú a sú dôležité ako policy vrstva, ale nie sú hlavný source-of-truth pre správanie celej pipeline.

### `docs/`
- Klasifikácia: `NEEDS REVIEW`
- Dôvod: obsahuje veľa silných a aktívnych dokumentov, ale zároveň viacero konfliktov, starších fáz a checkpoint closeoutov.

### `outputs/`
- Klasifikácia: `NEEDS REVIEW`
- Dôvod: časť outputov funguje ako fixture/evidence/canonical artifact example, časť je historická, časť je evidentne porovnávací alebo diffačný materiál.

### `data/qa/`
- Klasifikácia: `ACTIVE SUPPORTING`
- Dôvod: je to živá operačná, QA a orchestration podporná vrstva; vo vnútri sú aj fixture a generated runtime files.

### `data/archive/`
- Klasifikácia: `ARCHIVE CANDIDATE`
- Dôvod: prevádzkovo zmysluplné, ale nie vhodné ako dlhodobo rastúca primárna pracovná plocha repa.

### `project info/`
- Klasifikácia: `LEGACY`
- Dôvod: zachytáva pôvodný bootstrap a pôvodnú architektúrnu predstavu, ale nie je aktuálny runtime source of truth.

## `src/` Rodiny

### Canonical runtime flow scripts

- [`src/main.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/main.py): `CANONICAL`
- [`src/normalize_score.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/normalize_score.py): `CANONICAL`
- [`src/commercial_synthesizer.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/commercial_synthesizer.py): `CANONICAL`
- [`src/ranking_refresh.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/ranking_refresh.py): `CANONICAL`
- [`src/email_drafts.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/email_drafts.py): `CANONICAL`
- [`src/master_exports.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/master_exports.py): `CANONICAL`
- [`src/render_full_enrichment_md.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/render_full_enrichment_md.py): `CANONICAL`
- [`src/clickup_export.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_export.py): `CANONICAL`
- [`src/qa_checks.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/qa_checks.py): `CANONICAL`
- [`src/clickup_import_gate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_import_gate.py): `CANONICAL`
- [`src/make_orchestration_runner.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_orchestration_runner.py): `CANONICAL`

Poznámka:
`src/orchestrate.py` ešte túto flow neodráža naplno. To je source-of-truth konflikt, nie dôvod znížiť klasifikáciu vyššie uvedených modulov.

### Runtime entry / orchestration wrapper

- [`src/orchestrate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestrate.py): `NEEDS REVIEW`
- Dôvod: je to aktuálna default pipeline wrapper vrstva, ale nie je zosúladená s intended canonical flow.

### Enrichment source/factual layer

- [`src/enrich_hotels.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/enrich_hotels.py): `CANONICAL`
- Dôvod: aj pri novej flow ostáva kanonická pre `factual/source_bundle` vrstvu.

Pozor:
heuristický commercial generation vo vnútri tohto súboru nie je kanonický podľa zadanej flow a treba ho chápať ako interný konflikt vo vnútri kanonického súboru.

### Runtime supporting scripts

- [`src/run_manifest.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/run_manifest.py): `ACTIVE SUPPORTING`
- [`src/run_report.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/run_report.py): `ACTIVE SUPPORTING`
- [`src/archive_run_artifacts.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/archive_run_artifacts.py): `ACTIVE SUPPORTING`
- [`src/archive_cleanup.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/archive_cleanup.py): `ACTIVE SUPPORTING`
- [`src/high_leads_preimport_checklist.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/high_leads_preimport_checklist.py): `ACTIVE SUPPORTING`
- [`src/operator_decision_summary.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/operator_decision_summary.py): `ACTIVE SUPPORTING`
- [`src/clickup_dry_run_sample.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_dry_run_sample.py): `ACTIVE SUPPORTING`
- [`src/clickup_api_mapping_preview.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_api_mapping_preview.py): `ACTIVE SUPPORTING`
- [`src/clickup_import_preflight.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_import_preflight.py): `ACTIVE SUPPORTING`
- [`src/clickup_import_support_artifacts.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_import_support_artifacts.py): `ACTIVE SUPPORTING`
- [`src/clickup_import_operator_pack.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_import_operator_pack.py): `ACTIVE SUPPORTING`
- [`src/clickup_dry_run_packet.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_dry_run_packet.py): `ACTIVE SUPPORTING`

### ClickUp live validation and mapping tools

- [`src/clickup_live_field_discovery.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_live_field_discovery.py): `ACTIVE SUPPORTING`
- [`src/clickup_rehearsal_write.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_rehearsal_write.py): `ACTIVE SUPPORTING`

### Make provisioning and external integration tools

- [`src/make_scenario_deploy.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_scenario_deploy.py): `ACTIVE SUPPORTING`
- [`src/make_scenario_test_run.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_scenario_test_run.py): `ACTIVE SUPPORTING`
- [`src/make_id_helper.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_id_helper.py): `ACTIVE SUPPORTING`

### Sim / regression / test scripts

- [`src/orchestration_smoke_test.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestration_smoke_test.py): `FIXTURE`
- [`src/orchestration_regression_report.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestration_regression_report.py): `FIXTURE`
- [`src/orchestration_stateful_scenarios.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestration_stateful_scenarios.py): `FIXTURE`
- [`src/checkin_checkout_regression.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/checkin_checkout_regression.py): `FIXTURE`
- [`src/checkin_checkout_spotcheck.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/checkin_checkout_spotcheck.py): `FIXTURE`

### Ingest helper

- [`src/ingest/raw_loader.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/ingest/raw_loader.py): `ACTIVE SUPPORTING`

### Non-project artifacts

- `src/.DS_Store`: `DELETE CANDIDATE`

## `configs/`

### Core runtime contracts

- [`configs/project.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/project.yaml): `CANONICAL`
- [`configs/scoring.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/scoring.yaml): `CANONICAL`
- [`configs/enrichment.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/enrichment.yaml): `CANONICAL`
- [`configs/commercial_synthesis.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/commercial_synthesis.yaml): `CANONICAL`
- [`configs/ranking_tuning.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/ranking_tuning.yaml): `CANONICAL`
- [`configs/email.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/email.yaml): `CANONICAL`
- [`configs/qa.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/qa.yaml): `CANONICAL`
- [`configs/icp_profiles.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/icp_profiles.yaml): `CANONICAL`

### ClickUp contracts

- [`configs/clickup_custom_fields.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/clickup_custom_fields.yaml): `CANONICAL`
- [`configs/clickup_dropdown_normalization.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/clickup_dropdown_normalization.yaml): `CANONICAL`
- [`configs/clickup_api_mapping.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/clickup_api_mapping.yaml): `ACTIVE SUPPORTING`

### Make/orchestration contracts

- [`configs/orchestration.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/orchestration.yaml): `CANONICAL`
- [`configs/orchestration_overrides.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/orchestration_overrides.yaml): `ACTIVE SUPPORTING`
- [`configs/make_execution_payload_contract.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/make_execution_payload_contract.yaml): `CANONICAL`
- [`configs/make_api.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/make_api.yaml): `ACTIVE SUPPORTING`
- [`configs/make_scenario_blueprint.json`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/make_scenario_blueprint.json): `ACTIVE SUPPORTING`

### Non-project artifacts

- `configs/.DS_Store`: `DELETE CANDIDATE`

## `prompts/`

- [`prompts/enrichment/hotel_enrichment.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/prompts/enrichment/hotel_enrichment.md): `ACTIVE SUPPORTING`
- [`prompts/email/cold_email.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/prompts/email/cold_email.md): `ACTIVE SUPPORTING`
- `prompts/.DS_Store`: `DELETE CANDIDATE`

Dôvod:
Prompty sú dôležité policy assets, ale reálne commercial prompt instructions sú dnes vo veľkej miere zadrôtované priamo v [`src/commercial_synthesizer.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/commercial_synthesizer.py).

## `docs/project/`

### Canonical docs

- [`docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md): `CANONICAL`
- [`docs/project/OUTPUT_CSV_SCHEMAS.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/OUTPUT_CSV_SCHEMAS.md): `CANONICAL`
- [`docs/project/MAKE_EXECUTION_PAYLOAD_CONTRACT.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_EXECUTION_PAYLOAD_CONTRACT.md): `CANONICAL`
- [`docs/project/CLICKUP_API_PAYLOAD_CONTRACT_FINAL.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CLICKUP_API_PAYLOAD_CONTRACT_FINAL.md): `CANONICAL`
- [`docs/project/PHASE_6_READINESS_SUMMARY.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_READINESS_SUMMARY.md): `CANONICAL`
- [`docs/project/PHASE_6_UNIFIED_OPERATOR_RUNBOOK.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_UNIFIED_OPERATOR_RUNBOOK.md): `CANONICAL`
- [`docs/project/INTEGRATION_STATUS_SNAPSHOT.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/INTEGRATION_STATUS_SNAPSHOT.md): `CANONICAL`

### Active supporting docs

- väčšina Make/ClickUp SOP, checklist, evidence a runbook dokumentov: `ACTIVE SUPPORTING`

Konkrétne:

- `CLICKUP_*` operátorské a rehearsal dokumenty
- `MAKE_*` provisioning, runbook, payload, retry, response a unblock dokumenty
- `HTTP_*`, `NETWORK_*`, `CLOUDFLARE_*` incident SOP dokumenty
- `OPERATOR_*`, `UNIFIED_INCIDENT_SOP_INDEX.md`, `PRE_LIVE_CUTOVER_CHECKLIST.md`

### Historical docs

- [`docs/project/PHASE_2_DONE.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_2_DONE.md): `HISTORICAL`
- [`docs/project/PHASE_3_DONE.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_3_DONE.md): `HISTORICAL`
- [`docs/project/PHASE_3_CLOSING_SUMMARY.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_3_CLOSING_SUMMARY.md): `HISTORICAL`
- [`docs/project/PHASE_4_CLOSEOUT_SUMMARY.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_4_CLOSEOUT_SUMMARY.md): `HISTORICAL`
- [`docs/project/PHASE_5_CLOSEOUT_SUMMARY.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_5_CLOSEOUT_SUMMARY.md): `HISTORICAL`
- orchestration wave closeout summaries a smoke-test closeouty: `HISTORICAL`
- dashboard summary snapshoty s dátumom: `HISTORICAL`

### Legacy docs

- [`docs/project/CODEX_PROJECT_BRIEF.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CODEX_PROJECT_BRIEF.md): `LEGACY`
- Dôvod: obsahovo cenné, ale fáza v ňom je zastaraná.

### Needs review docs

- [`docs/project/PHASE_4_INTEGRATION_DECISION_LOG.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_4_INTEGRATION_DECISION_LOG.md): `NEEDS REVIEW`
- Dôvod: stále dôležité, ale časť reality sa presunula ďalej do Phase 6 readiness.

- [`docs/project/INTEGRATION_READINESS_REPORT.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/INTEGRATION_READINESS_REPORT.md): `NEEDS REVIEW`
- Dôvod: treba potvrdiť, či ešte pridáva niečo nad novšie readiness summary.

- `docs/project/.DS_Store`: `DELETE CANDIDATE`

## `outputs/`

### Canonical output families podľa intended architecture

- `outputs/source_bundles/`: `CANONICAL`
- `outputs/factual_enrichment/`: `CANONICAL`
- `outputs/commercial_synthesis/`: `CANONICAL`
- `outputs/ranked/`: `CANONICAL`
- `outputs/email_drafts/`: `CANONICAL`
- `outputs/master/`: `CANONICAL`
- `outputs/hotel_markdown/`: `CANONICAL`
- `outputs/clickup/`: `CANONICAL`

Pozor:
Rodiny sú kanonické, ale nie všetky súbory vo vnútri sú rovnako kanonické. Veľa verziovaných wave/batch výstupov vo vnútri je historických.

### Needs review inside canonical output families

- staršie `wave*`, `batch10`, `v2/v3/v4/v5`, `smoke` varianty: `NEEDS REVIEW`
- Dôvod: nie je jasné, ktoré sú fixture baseline a ktoré už len historický clutter.

### Historical output family

- `outputs/export/`: `HISTORICAL`
- Dôvod: slúži najmä na diffy, QC porovnania a debugging medzi vlnami, nie ako hlavná runtime output vrstva.

### Non-project artifacts

- `outputs/hotel_markdown/.DS_Store`: `DELETE CANDIDATE`

## `data/qa/`

### Active supporting QA/runtime files

- top-level runtime artifacts ako `run_manifest.json`, `clickup_import_gate.json`, `make_execution_payload.json`, `retry_eligibility.json`, `integration_evidence_log.json`, `phase_5_progress_tracker.json`: `ACTIVE SUPPORTING`

### Fixture subfamilies

- `data/qa/simulated_*`: `FIXTURE`
- `data/qa/stateful_*`: `FIXTURE`
- `data/qa/checkin_checkout_regression_cases.csv`: `FIXTURE`

### Needs review subfamilies

- `data/qa/clickup_operator_pack/`: `NEEDS REVIEW`
- `data/qa/clickup_dry_run_packet/`: `NEEDS REVIEW`
- Dôvod: sú užitočné, ale zároveň obsahujú veľa kopírovaných generated artifactov.

### Delete candidate

- `data/qa/.DS_Store`: `DELETE CANDIDATE`

## `data/archive/`

- celá rodina `data/archive/`: `ARCHIVE CANDIDATE`
- Dôvod: je to batch evidence history, nie primárna pracovná vrstva repa.

## `data/raw/`

- `data/raw/`: `FIXTURE`
- Dôvod: raw vstupy sú neprepisovateľné a zároveň v tomto repo fungujú ako testovacie / referenčné dataset fixture pre pipeline.

## `data/processed/`

- `data/processed/`: `ACTIVE SUPPORTING`
- Dôvod: je to runtime-derived medzivrstva; dôležitá pre beh, ale nie primárny canonical knowledge layer.

## `project info/`

### Celá rodina

- `project info/`: `LEGACY`

### Dôvod

- odráža starý bootstrap, počiatočný plán a starter kit
- stále pomáha pri rekonštrukcii evolúcie projektu
- nie je aktuálny source-of-truth pre runtime, configs ani docs

### Vnútorné súbory

- všetky `project info/*.md`, `project info/configs/*`, `project info/src/*`: `LEGACY`

## Root súbory

- [`README.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/README.md): `NEEDS REVIEW`
- Dôvod: je dôležitý, ale jeho status/fáza je zastaraná oproti novším dokumentom.

- [`requirements.txt`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/requirements.txt): `ACTIVE SUPPORTING`
- [`.gitignore`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/.gitignore): `NEEDS REVIEW`
- [`.env.example`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/.env.example): `ACTIVE SUPPORTING`

## Najdôležitejšie klasifikačné poznámky

1. `src/orchestrate.py` je dnes runtime pravda, ale nie intended canonical truth.
2. `src/enrich_hotels.py` je kanonický súbor, ale nesie v sebe aj nekanonickú heuristickú commercial vrstvu.
3. `outputs/source_bundles -> factual_enrichment -> commercial_synthesis -> ranked -> hotel_markdown` je kanonická artifact line, aj keď default pipeline ešte nie je plne zosúladená.
4. `project info/` nie je delete candidate; je to `LEGACY`, nie odpad.
5. `.DS_Store` sú jediné jednoznačné `DELETE CANDIDATE` položky bez architektonického rizika.
