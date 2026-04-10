# CURRENT_SYSTEM_STATUS

## Project identity

- názov: `Hotel Lead Enrichment Engine OS`
- typ: Python-first hotel lead enrichment a operator handoff system
- primárny CRM target: ClickUp
- orchestration target: Make
- jazyk operátorskej a outreach vrstvy: slovenčina

## Current stage

`Canonical architecture confirmed, documentation aligned, runtime wrapper not yet fully aligned.`

Prakticky:

- kanonická flow je definitívne určená
- kanonické moduly sú známe
- veľká časť artifact pipeline existuje
- Make live path ostáva čiastočne nevalidovaný
- `src/orchestrate.py` ešte musí byť zosúladený s touto pravdou

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

- moduly existujú a sú použiteľné
- default wrapper v `src/orchestrate.py` ešte nie je finálne zosúladený s kanonickou flow
- teda: architektúra je potvrdená, ale wrapper truth ešte nie je úplne uprataná

## What is validated vs unvalidated

### Validated alebo silno podložené

- normalize/scoring vrstva
- factual/source-bundle artifact line
- email draft generation
- ClickUp export layers
- QA/gate artifact generation
- orchestration dry-run, regression a simulated scenáre
- operator SOP/document layer pre controlled execution

### Čiastočne validované alebo neuzavreté

- plne zosúladený canonical run order cez jeden wrapper entrypoint
- end-to-end live Make execution
- posledná míľa Make -> ClickUp live path v reálnych externých podmienkach
- finálne fixture/retenčné pravidlá pre generated artifacts

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

## Frozen / legacy / archive zones

### Frozen canonical zones

- `configs/`
- kanonické runtime moduly v `src/`
- root canonical docs

### Legacy zones

- `project info/`
- heuristická commercial generation vo vnútri `src/enrich_hotels.py` ako fallback-only logic
- starý brief v `docs/project/CODEX_PROJECT_BRIEF.md`

### Historical zones

- staré phase closeout docs
- orchestration wave closeout summaries
- historické `wave/batch/v2-v5/smoke` output variants
- `outputs/export/` diff a QC materiál

### Archive candidate zones

- `data/archive/`
- neskôr vybrané historical output families po potvrdení fixture policy

## Next 3 moves

1. Zosúladiť `src/orchestrate.py` na confirmed canonical flow ako tenký wrapper bez konkurenčnej runtime pravdy.
2. Explicitne oddeliť kanonickú factual vrstvu v `src/enrich_hotels.py` od legacy heuristic commercial fallback logiky.
3. Zaviesť minimálnu kanonickú fixture/retenčnú politiku pre `outputs/` a `data/qa/` bez okamžitého cleanupu.
