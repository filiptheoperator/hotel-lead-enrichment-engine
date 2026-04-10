# CURRENT_SYSTEM_STATUS

## Project identity

- názov: `Hotel Lead Enrichment Engine OS`
- typ: Python-first hotel lead enrichment a operator handoff system
- primárny CRM target: ClickUp
- orchestration target: Make
- jazyk operátorskej a outreach vrstvy: slovenčina

## Current stage

`Canonical runtime aligned, post-fix baseline established, cleanup executed, branch in final merge decision state.`

Prakticky:

- kanonická flow je potvrdená a zosúladená v kóde
- `src/orchestrate.py` už nepredstavuje konkurenčnú runtime truth
- kanonická `commercial_synthesizer(v3-lite)` vrstva je aktívna commercial truth
- ranking boundary už neberie `commercial_synthesis/v1` ako aktívnu structured truth
- canonical post-fix retained baseline existuje
- jeden historical regression fixture set je ponechaný
- cleanup execution aj fixture retention policy už boli vykonané
- branch je pripravený na finálny owner merge verdict

## Canonical runtime flow

`normalize -> factual/source_bundle -> commercial_synthesizer(v3-lite) -> ranking_refresh -> email_drafts -> master_exports -> render_full_enrichment_md -> clickup_export -> QA/gate -> Make`

## What is actually operational now

### Operačné lokálne vrstvy

- `normalize_score`
- `enrich_hotels` pre factual/source-bundle artifacty
- `commercial_synthesizer(v3-lite)` ako kanonická commercial vrstva
- `ranking_refresh` ako kanonická ranking vrstva
- `email_drafts`
- `master_exports`
- `render_full_enrichment_md`
- `clickup_export`
- `qa_checks`
- `clickup_import_gate`
- `make_orchestration_runner` pre dry-run / validate / execution control layer

### Reálna poznámka k behu

- default wrapper v `src/orchestrate.py` je zosúladený s kanonickou flow
- fallback commercial logika v `src/enrich_hotels.py` ostáva explicitne len za env guardom
- Make ostáva thin execution/orchestration vrstva nad uzamknutými Python artifactmi

## What is validated vs unvalidated

### Validated alebo silno podložené

- normalize/scoring vrstva
- factual/source-bundle artifact line
- `commercial_synthesizer(v3-lite)` ako kanonická commercial vrstva
- `ranking_refresh` boundary s pravdivým schema markerom
- email draft generation
- master export generation
- markdown operator presentation layer
- ClickUp export layers
- QA/gate artifact generation
- cleanup-executed retained fixture baseline

### Čiastočne validované alebo neuzavreté

- end-to-end live Make execution
- posledná míľa Make -> ClickUp live path v reálnych externých podmienkach
- finálny owner merge verdict pre túto branch

## Active source-of-truth files

### Status a orientácia

- [CURRENT_SYSTEM_STATUS.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/CURRENT_SYSTEM_STATUS.md)
- [README.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/README.md)
- [CODEX_PROJECT_BRIEF.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/CODEX_PROJECT_BRIEF.md)

### Runtime architecture

- [PHASE_1_ENRICHMENT_ARCHITECTURE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md)
- [CANONICAL_RUNBOOK.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/CANONICAL_RUNBOOK.md)

### Runtime contracts

- [configs/project.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/project.yaml)
- [configs/scoring.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/scoring.yaml)
- [configs/enrichment.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/enrichment.yaml)
- [configs/commercial_synthesis.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/commercial_synthesis.yaml)
- [configs/ranking_tuning.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/ranking_tuning.yaml)
- [configs/email.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/email.yaml)
- [configs/qa.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/qa.yaml)
- [configs/orchestration.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/orchestration.yaml)
- [configs/make_execution_payload_contract.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/make_execution_payload_contract.yaml)

### Output a payload contract docs

- [OUTPUT_CSV_SCHEMAS.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/OUTPUT_CSV_SCHEMAS.md)
- [MAKE_EXECUTION_PAYLOAD_CONTRACT.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_EXECUTION_PAYLOAD_CONTRACT.md)
- [CLICKUP_API_PAYLOAD_CONTRACT_FINAL.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CLICKUP_API_PAYLOAD_CONTRACT_FINAL.md)
- [RETENTION_AND_FIXTURE_POLICY.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/RETENTION_AND_FIXTURE_POLICY.md)

## Current retained baseline

### Canonical verification baseline

- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_post_fix_regen_20260410.csv`
- corresponding retained downstream set v:
  - `outputs/master/`
  - `outputs/email_drafts/`
  - `outputs/clickup/`
  - `outputs/hotel_markdown/`
- retained structured evidence set v:
  - `outputs/source_bundles/Sydney 100/`
  - `outputs/factual_enrichment/Sydney 100/`
  - `outputs/commercial_synthesis/Sydney 100/`

### Historical regression fixture

- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave4_v3lite_smoke.csv`
- matching retained `wave4_v3lite_smoke` family v `outputs/master/`

### Archive location

- `data/archive/cleanup_2026-04-10_outputs_archive/`

## Frozen / legacy / archive zones

### Frozen canonical zones

- `configs/`
- kanonické runtime moduly v `src/`
- root canonical docs
- retained canonical fixture baseline

### Legacy zones

- `project info/`
- heuristická commercial generation vo vnútri `src/enrich_hotels.py` ako fallback-only logic
- starý brief v `docs/project/CODEX_PROJECT_BRIEF.md`

### Historical zones

- retained `wave4_v3lite_smoke` regression fixture
- staré phase closeout docs
- orchestration wave closeout summaries

### Archive zones

- `data/archive/`
- cleanup archive subtree v `data/archive/cleanup_2026-04-10_outputs_archive/`

## Next 3 moves

1. Urobiť finálny owner review a merge verdict pre branch.
2. Rozhodnúť, či cleanup archive subtree má zostať dlhodobo v repo alebo sa má neskôr presunúť mimo core snapshot.
3. Rozhodnúť, či downstream exporty majú v budúcnosti explicitne niesť aj `commercial_source_mode` a `commercial_fallback_used`.
