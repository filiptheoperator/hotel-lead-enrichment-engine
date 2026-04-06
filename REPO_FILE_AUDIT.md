# Repo File Audit

## Key Directories

### `src/`

Role: active execution logic.

Important files:

- `main.py`: CLI entrypoint
- `orchestrate.py`: current default pipeline order
- `normalize_score.py`: normalization, dedupe, initial ranking
- `enrich_hotels.py`: enrichment engine and structured artifact generation
- `email_drafts.py`: outreach draft generation
- `master_exports.py`: merged export layer
- `clickup_export.py`: ClickUp CSV layer
- `qa_checks.py`: QA and manual-review issue generation
- `run_manifest.py`: artifact manifest and run metadata
- `clickup_import_gate.py`: GO/NO_GO gate
- `make_orchestration_runner.py`: Make orchestration core

Assessment: `MUST KEEP`

### `configs/`

Role: primary runtime contracts and policy.

Notable files:

- `project.yaml`
- `scoring.yaml`
- `enrichment.yaml`
- `email.yaml`
- `ranking_tuning.yaml`
- `orchestration.yaml`
- `make_execution_payload_contract.yaml`
- `clickup_custom_fields.yaml`

Assessment: `MUST KEEP`

### `docs/project/`

Role: operational architecture, phase history, SOPs, cutover materials.

Assessment: mixed.

- contracts/runbooks/status docs: `MUST KEEP`
- duplicated phase closeouts/checkpoint summaries: `NEEDS REVIEW`

### `data/raw/`

Role: immutable raw inputs.

Assessment: `MUST KEEP`

### `data/processed/`

Role: normalized/scored intermediates.

Assessment: `MUST KEEP` as runtime outputs, but probably not all versions need to stay committed.

### `data/qa/`

Role: runtime QA outputs, rehearsal artifacts, simulated scenarios, orchestration reports.

Assessment: mixed.

- scenario fixtures and contracts: `MUST KEEP`
- generated run artifacts and duplicated packet copies: `NEEDS REVIEW`

### `data/archive/`

Role: archived batch bundles and evidence packs.

Assessment: `NEEDS REVIEW`

Reason: operationally useful, but large and version-heavy for a source repo.

### `outputs/`

Role: generated output layers.

Sub-areas:

- `outputs/enrichment`, `outputs/email_drafts`, `outputs/clickup`, `outputs/ranked`, `outputs/master`
- `outputs/source_bundles`, `outputs/factual_enrichment`, `outputs/commercial_synthesis`
- `outputs/hotel_markdown`
- `outputs/export`

Assessment: mixed.

- representative fixtures/examples: `MUST KEEP`
- mass historical waves and diffs: `NEEDS REVIEW` or `LIKELY ARCHIVE`

### `project info/`

Role: original scaffold/bootstrapping package.

Assessment: `LIKELY ARCHIVE`

Reason: useful for origin story, but not active runtime source of truth.

### `prompts/`

Role: lightweight prompt/policy assets.

Assessment: `MUST KEEP`

## Key Files and Roles

### Runtime core

- [`src/main.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/main.py): pipeline entrypoint
- [`src/orchestrate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestrate.py): active pipeline sequencing
- [`src/normalize_score.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/normalize_score.py): raw-to-processed conversion
- [`src/enrich_hotels.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/enrich_hotels.py): enrichment runtime and artifact creation
- [`src/email_drafts.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/email_drafts.py): email compose
- [`src/master_exports.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/master_exports.py): export composition
- [`src/clickup_export.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_export.py): ClickUp CSVs
- [`src/qa_checks.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/qa_checks.py): QA rules
- [`src/run_report.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/run_report.py): run summaries
- [`src/run_manifest.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/run_manifest.py): manifest contract
- [`src/clickup_import_gate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_import_gate.py): import decisioning

Assessment: `MUST KEEP`

### Newer structured stack

- [`src/commercial_synthesizer.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/commercial_synthesizer.py): LLM commercial synthesis v3-lite
- [`src/ranking_refresh.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/ranking_refresh.py): final decision engine
- [`src/render_full_enrichment_md.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/render_full_enrichment_md.py): markdown renderer

Assessment: `MUST KEEP`, but `NEEDS REVIEW` for integration status

### ClickUp live/integration files

- [`src/clickup_live_field_discovery.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_live_field_discovery.py)
- [`src/clickup_rehearsal_write.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_rehearsal_write.py)
- [`configs/clickup_custom_fields.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/clickup_custom_fields.yaml)
- [`configs/clickup_dropdown_normalization.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/clickup_dropdown_normalization.yaml)

Assessment: `MUST KEEP`

### Make/orchestration files

- [`src/make_orchestration_runner.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_orchestration_runner.py)
- [`src/make_scenario_deploy.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_scenario_deploy.py)
- [`src/make_scenario_test_run.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_scenario_test_run.py)
- [`src/orchestration_smoke_test.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestration_smoke_test.py)
- [`src/orchestration_regression_report.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestration_regression_report.py)

Assessment: `MUST KEEP`

### Primary docs

- [`README.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/README.md): onboarding summary, but outdated on phase
- [`docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md): strongest architecture doc
- [`docs/project/OUTPUT_CSV_SCHEMAS.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/OUTPUT_CSV_SCHEMAS.md): strongest output contract doc
- [`docs/project/PHASE_6_READINESS_SUMMARY.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_READINESS_SUMMARY.md): strongest current-state doc

Assessment: `MUST KEEP`

## Suspected Duplicates

- `project info/configs/*.yaml` duplicates main `configs/*.yaml`
- `project info/src/main.py` duplicates the concept of root `src/main.py`
- `project info/README.md` duplicates root `README.md`
- many `outputs/master/Sydney 100_*_v2/v3/v4/v5.csv` are iterative variants of the same logical export families
- `data/qa/clickup_operator_pack/*` and `data/qa/clickup_dry_run_packet/*` contain repeated copies of similar artifact sets

## Archive Candidates

- `project info/`
- historical comparative exports in `outputs/export/`
- old wave/version output files in `outputs/master/`
- stale archived run copies in `data/archive/` beyond the retention rule if already backed up elsewhere
- phase closeout/checkpoint docs that have been superseded by later consolidated docs

## Unclear Files Needing Review

- [`docs/project/CODEX_PROJECT_BRIEF.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CODEX_PROJECT_BRIEF.md)
Reason: phase status conflicts with newer docs.

- [`README.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/README.md)
Reason: describes Phase 5 as active while repo also claims Phase 6 readiness.

- [`src/enrich_hotels.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/enrich_hotels.py) vs [`src/commercial_synthesizer.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/commercial_synthesizer.py)
Reason: two commercial synthesis implementations.

- [`src/orchestrate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestrate.py)
Reason: does not include newer structured-stack scripts.

- `outputs/master/*wave*`, `outputs/ranked/*wave*`, `outputs/export/*diff*`
Reason: historical but not clearly labeled as canonical, fixture, or archive.

## Classification

### MUST KEEP

- `src/`
- `configs/`
- `prompts/`
- core docs in `docs/project/` covering architecture/contracts/readiness/runbooks
- representative raw/processed/qa/output fixtures needed to understand contracts

### NEEDS REVIEW

- `README.md`
- `docs/project/CODEX_PROJECT_BRIEF.md`
- most phase closeout/checkpoint summaries
- `data/archive/`
- `data/qa/` generated artifacts
- `outputs/master/`, `outputs/export/`, `outputs/hotel_markdown/`

### LIKELY ARCHIVE

- `project info/`
- historical wave/version export clutter
- comparative diff outputs once findings are captured elsewhere

### UNKNOWN PURPOSE

- tracked `.DS_Store` files
- some generated JSON/TXT files in `data/qa/` with very similar names and overlapping content unless actively used in SOPs
