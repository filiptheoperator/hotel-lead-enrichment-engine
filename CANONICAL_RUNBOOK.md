# CANONICAL_RUNBOOK

## Cieľ

Toto je jediný kanonický run order pre systém `Hotel Lead Enrichment Engine OS`.

## Exact canonical run order

1. `normalize_score`
2. `enrich_hotels`
3. `commercial_synthesizer(v3-lite)`
4. `ranking_refresh`
5. `email_drafts`
6. `master_exports`
7. `render_full_enrichment_md`
8. `clickup_export`
9. `qa_checks`
10. `clickup_import_gate`
11. `make_orchestration_runner`

## Required inputs

### Filesystem inputs

- raw CSV v `data/raw/`
- `.env`
- configs v `configs/`

### External inputs

- `OPENAI_API_KEY` pre canonical commercial layer
- voliteľne `GOOGLE_PLACES_API_KEY`, ak bude collector zapnutý
- ClickUp env values pre rehearsal/live support vrstvu
- Make env values pre orchestration vrstvu

## Required configs

- [configs/project.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/project.yaml)
- [configs/scoring.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/scoring.yaml)
- [configs/enrichment.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/enrichment.yaml)
- [configs/commercial_synthesis.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/commercial_synthesis.yaml)
- [configs/ranking_tuning.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/ranking_tuning.yaml)
- [configs/email.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/email.yaml)
- [configs/qa.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/qa.yaml)
- [configs/orchestration.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/orchestration.yaml)
- [configs/make_execution_payload_contract.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/make_execution_payload_contract.yaml)

## Step-by-step outputs

### 1. `normalize_score`

Input:

- `data/raw/*.csv`

Output:

- `data/processed/*_normalized_scored.csv`

Checkpoint:

- account identity exists
- dedupe fields exist
- scoring fields exist

### 2. `enrich_hotels`

Input:

- latest or selected `*_normalized_scored.csv`

Output:

- `outputs/source_bundles/<batch>/<account_id>.json`
- `outputs/factual_enrichment/<batch>/<account_id>.json`
- `outputs/enrichment/*_enriched.csv`

Checkpoint:

- factual/source-bundle artifacts exist
- unknown values are explicitly marked
- heuristic commercial content in this step is not treated as canonical source-of-truth

### 3. `commercial_synthesizer(v3-lite)`

Input:

- processed row
- source bundle
- factual enrichment

Output:

- `outputs/commercial_synthesis/<batch>/<account_id>.json`

Checkpoint:

- schema version is `commercial_synthesis/v3-lite`
- grounded-only output
- no fallback heuristics should override this layer

### 4. `ranking_refresh`

Input:

- enriched CSV
- structured factual/commercial artifacts

Output:

- `outputs/ranked/*_ranking_refreshed*.csv`

Checkpoint:

- `ranking_score_final`
- `priority_level_final`
- `decision_status`
- review queue signals

### 5. `email_drafts`

Input:

- enriched CSV
- ranked context
- commercial/factual artifacts

Output:

- `outputs/email_drafts/*_email_drafts.csv`

Checkpoint:

- email blocks are present
- relevance stays grounded
- CTA stays low-friction

### 6. `master_exports`

Input:

- processed
- enrichment
- ranked
- email

Output:

- `outputs/master/*_accounts_master.csv`
- `outputs/master/*_enrichment_master.csv`
- `outputs/master/*_outreach_drafts.csv`
- `outputs/master/*_operator_shortlist.csv`
- `outputs/master/*_top_20_export.csv`

Checkpoint:

- joins are consistent on account identity
- master exports reflect ranked canonical decisioning

### 7. `render_full_enrichment_md`

Input:

- source bundle
- factual enrichment
- commercial synthesis
- ranked
- optional email context

Output:

- `outputs/hotel_markdown/<batch>/<account_id>.md`
- shortlist/review/top summary markdown files

Checkpoint:

- renderer does not invent new business logic
- markdown is presentation layer only

### 8. `clickup_export`

Input:

- canonical ranked/master/email context

Output:

- `outputs/clickup/*_clickup_import.csv`
- optional export variants

Checkpoint:

- required ClickUp columns exist
- CRM cleanliness wins over verbosity

### 9. `qa_checks`

Input:

- processed
- enrichment
- clickup export

Output:

- `data/qa/qa_issues.csv`
- `data/qa/manual_review_shortlist.csv`
- supporting QA summaries

Checkpoint:

- blocking issues are explicit
- fetch incidents are explicit
- low-confidence records are routed correctly

### 10. `clickup_import_gate`

Input:

- run manifest
- QA results
- clickup export readiness

Output:

- `data/qa/clickup_import_gate.json`
- `data/qa/clickup_import_gate.txt`

Checkpoint:

- one clear `GO` or `NO_GO`
- no soft ambiguity

### 11. `make_orchestration_runner`

Input:

- locked gate
- run manifest
- required payload artifacts

Output:

- Make payload
- validation artifacts
- evidence/reconciliation/runtime status artifacts

Checkpoint:

- Make reads locked artifacts only
- Make does not recompute business logic

## QA / gate checkpoints

### Hard stops

- missing required artifact
- invalid payload shape
- `decision = NO_GO`
- blocking QA issues
- unresolved external blocker

### Pass conditions before Make execution

- canonical artifacts exist
- ranked decisioning exists
- ClickUp export is structurally ready
- QA blocking rows are zero
- gate says `GO`

## Pass / fail logic

### PASS

- all required artifacts exist
- canonical ranking and QA completed
- gate result is `GO`
- payload validates
- orchestration layer is ready for planning or controlled execution

### FAIL / STOP

- missing artifacts
- stale or invalid payload
- unresolved QA block
- fetch/global incident crossing threshold
- external blocker on live path

## What Make does

- receives locked payload
- validates artifact presence and execution readiness
- routes execution state
- records evidence and reconciliation outputs
- acts as thin transport/execution layer

## What Make does not do

- neprepočítava scoring
- negeneruje enrichment
- nevytvára commercial reasoning
- nepíše email copy logiku
- nemení QA pravidlá
- nerozhoduje business priority mimo uzamknutých artifactov
