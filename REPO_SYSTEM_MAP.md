# Repo System Map

## Executive Summary

`Hotel Lead Enrichment Engine OS` is a Python-first lead-processing and enrichment system for hotel prospecting. Its business purpose is to turn raw hotel lead exports into scored, enriched, outreach-ready, and ClickUp-ready lead packets with QA gates and operator handoff artifacts.

The repo is not a single clean architecture. It currently contains:

- a working local batch pipeline for `raw -> normalize/score -> enrich -> email -> ClickUp export -> QA -> reporting`
- a newer structured-artifact track for `source_bundle -> factual_enrichment -> commercial_synthesis/v3-lite -> ranking_refresh -> markdown render`
- a strong orchestration/governance layer for Make and ClickUp live execution
- a legacy bootstrap/scaffold package under `project info/`

Current overall state: structurally built, partially operational locally, but not fully unified and not fully validated end-to-end in the intended final live path.

## What This Repo Is

### Project identity

- Project name: `Hotel Lead Enrichment Engine OS`
- Primary language: Slovak in user-facing logic and docs
- Runtime: Python scripts, config-driven, file-based batch processing
- Target CRM: ClickUp
- Intended glue/orchestration layer: Make

### Problem it is solving

The project is trying to replace slow, manual hotel lead enrichment and outreach prep with a repeatable batch system that:

- ingests raw lead exports
- normalizes and ranks hotel accounts
- enriches factual hotel details from public sources
- generates commercial reasoning and outreach material
- prepares ClickUp import or API handoff artifacts
- blocks unsafe imports through QA and operator gates

### Who it is for

- the operator/founder running hotel lead generation
- human reviewers who need shortlists, QA packets, and import checklists
- eventually a Make/ClickUp live execution flow

### Intended end-to-end workflow

`raw CSV -> normalize + dedupe + score -> public-source enrichment -> commercial synthesis -> ranking refresh -> email drafts -> master exports -> ClickUp export -> QA -> run manifest/gate -> archive -> Make orchestration -> ClickUp live write`

### Business and operational purpose

- reduce manual enrichment effort
- preserve enrichment quality and grounding
- improve outreach relevance
- keep CRM imports clean
- move from manual ops to controlled semi-automation without moving business logic into Make

## Original Plan

### Inferred original architecture

The earliest explicit architecture lives in `project info/` and early docs:

- `project info/05_IMPLEMENTATION_PLAN.md`
- `project info/06_TARGET_ARCHITECTURE.md`
- `project info/07_REPO_STRUCTURE_AND_BUILD_RULES.md`
- `docs/project/CODEX_PROJECT_BRIEF.md`

Original intent:

- build a simple modular Python repo
- use folders like `src/normalize`, `src/scoring`, `src/enrich`, `src/export`
- keep Make as a later thin automation layer
- treat enrichment as the core value layer
- use ClickUp as the CRM surface, not as the logic engine

### Target system the repo aims toward

A file-driven operating system for hotel lead enrichment with:

- raw lead intake
- account identity normalization
- factual source collection
- grounded commercial synthesis
- outreach copy generation
- ranked shortlist exports
- ClickUp handoff
- Make-triggered live execution with rollback/evidence handling

### Intended final destination

The most mature intended end-state appears in:

- `docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md`
- `docs/project/OUTPUT_CSV_SCHEMAS.md`
- `docs/project/MAKE_EXECUTION_PAYLOAD_CONTRACT.md`
- `docs/project/PHASE_6_READINESS_SUMMARY.md`

That end-state is:

- local Python remains source of truth for scoring, QA, and artifact generation
- structured JSON artifacts become canonical for factual and commercial reasoning
- ranking refresh decides `outreach_now` vs review
- markdown/operator briefs become final presentation layer
- Make only routes locked payloads and execution evidence
- ClickUp live write is controlled, gated, and reversible

## Current State

### What is already built

Built and executable today:

- raw CSV ingestion via [`src/ingest/raw_loader.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/ingest/raw_loader.py)
- normalization, dedupe, ICP scoring, priority scoring via [`src/normalize_score.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/normalize_score.py)
- enrichment with public-site scraping, source-bundle JSON, factual enrichment JSON, and heuristic commercial artifact creation via [`src/enrich_hotels.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/enrich_hotels.py)
- email draft generation via [`src/email_drafts.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/email_drafts.py)
- ClickUp CSV export variants via [`src/clickup_export.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_export.py)
- QA issue generation and manual review shortlist via [`src/qa_checks.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/qa_checks.py)
- run summaries, manifests, archive bundles, operator packet artifacts
- ClickUp field discovery and rehearsal write tooling
- Make orchestration dry-run/validate/live-noop framework with many simulated scenarios

### What is partially built

Partially built but not integrated into the default pipeline:

- LLM-based `commercial_synthesizer` v3-lite
- `ranking_refresh` post-enrichment scoring layer
- `render_full_enrichment_md` markdown/operator brief renderer
- Make scenario deployment and scenario test tooling

These modules exist and have outputs in the repo, but they are not called from the default `src/orchestrate.py` run path.

### What is stubbed or placeholder

- `configs/make_scenario_blueprint.json` is explicitly an unverified template
- Make live execution remains blocked externally
- some ClickUp live path assumptions remain documented as partially confirmed
- prompt files are lightweight policy assets, not deeply integrated prompt orchestration

### What appears broken, disconnected, duplicated, abandoned, or unclear

- `project info/` is a full parallel scaffold and is no longer the active runtime system
- `README.md` says active phase is Phase 5, while docs say Phase 6 readiness is prepared and waiting for unblock
- `docs/project/CODEX_PROJECT_BRIEF.md` still says current phase is Phase 3
- `src/enrich_hotels.py` generates `commercial_synthesis/v1` heuristics, while [`src/commercial_synthesizer.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/commercial_synthesizer.py) generates `commercial_synthesis/v3-lite`
- default pipeline does not run the newer ranking refresh or markdown renderer
- tracked outputs contain multiple historical “waves”, “batch10”, “v2/v3/v4/v5”, which blur what is canonical

### Production-relevant vs experimental

Most production-relevant:

- `configs/`
- `src/main.py`
- `src/orchestrate.py`
- `src/normalize_score.py`
- `src/enrich_hotels.py`
- `src/email_drafts.py`
- `src/clickup_export.py`
- `src/qa_checks.py`
- `src/run_manifest.py`
- `src/clickup_import_gate.py`
- `src/make_orchestration_runner.py`
- `docs/project/*Phase 4-6*`, Make/ClickUp contracts, SOPs

More experimental or transitional:

- `project info/`
- many historical `outputs/master/*wave*`, `outputs/export/*diff*`
- newer v3/v4/v5 modules not yet in the main run chain

## Architecture Map

### Inputs

- raw lead CSVs in `data/raw/`
- `.env` secrets for OpenAI, Google Places, ClickUp, Make
- YAML configs in `configs/`
- lightweight prompt policy files in `prompts/`
- optional prior enrichment output reused as fallback

### Core modules

1. Ingest
- File: [`src/ingest/raw_loader.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/ingest/raw_loader.py)
- Reads raw CSV files and previews them

2. Normalize + score
- File: [`src/normalize_score.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/normalize_score.py)
- Maps raw columns, normalizes identities, computes dedupe and ranking fields

3. Enrichment + source collection
- File: [`src/enrich_hotels.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/enrich_hotels.py)
- Fetches official pages, extracts opening hours/check-in-room signals, emits CSV and JSON artifacts

4. Commercial synthesis
- Legacy path: heuristic generation inside `enrich_hotels.py`
- New path: [`src/commercial_synthesizer.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/commercial_synthesizer.py)

5. Ranking refresh
- File: [`src/ranking_refresh.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/ranking_refresh.py)
- Uses structured artifacts to compute final decisioning

6. Email compose
- File: [`src/email_drafts.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/email_drafts.py)

7. Export layer
- Files:
- [`src/master_exports.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/master_exports.py)
- [`src/clickup_export.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_export.py)
- [`src/render_full_enrichment_md.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/render_full_enrichment_md.py)

8. QA and operator readiness
- Files:
- [`src/qa_checks.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/qa_checks.py)
- [`src/run_report.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/run_report.py)
- [`src/run_manifest.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/run_manifest.py)
- [`src/clickup_import_gate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_import_gate.py)

9. ClickUp live prep/rehearsal
- Files:
- [`src/clickup_live_field_discovery.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_live_field_discovery.py)
- [`src/clickup_rehearsal_write.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_rehearsal_write.py)

10. Make orchestration
- Files:
- [`src/make_orchestration_runner.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_orchestration_runner.py)
- [`src/make_scenario_deploy.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_scenario_deploy.py)
- [`src/make_scenario_test_run.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_scenario_test_run.py)
- smoke/regression scripts

### Orchestration flow

Current default pipeline:

`main.py -> orchestrate.py -> normalize_score -> enrich_hotels -> email_drafts -> master_exports -> clickup_export -> qa_checks -> run_report -> run_manifest -> clickup_import_gate -> dry run sample -> mapping preview -> checklist -> operator summary -> archive -> archive cleanup -> make_orchestration_runner`

Intended newer canonical flow:

`normalize_score -> enrich_hotels/source_bundle/factual -> commercial_synthesizer(v3-lite) -> ranking_refresh -> email_drafts(with ranked context) -> master_exports -> render_full_enrichment_md -> clickup_export -> QA/gate -> Make`

### Data transformations

- raw Apify/lead CSV columns mapped to normalized account schema
- text and contact normalization
- account identity hashing into `account_id`
- enrichment fields merged into flat CSV plus structured JSON
- commercial reasoning turned into outreach fields
- master export join across processed/enrichment/email/ranked layers
- ClickUp flat CSV built from master data
- run manifest summarizes outputs and gating metrics
- archive copies batch artifacts into timestamped folders

### Storage and export layers

- immutable inputs: `data/raw/`
- intermediate normalized data: `data/processed/`
- QA/runtime artifacts: `data/qa/`
- archived batch bundles: `data/archive/`
- flat outputs: `outputs/enrichment`, `outputs/email_drafts`, `outputs/clickup`, `outputs/master`, `outputs/ranked`
- structured outputs: `outputs/source_bundles`, `outputs/factual_enrichment`, `outputs/commercial_synthesis`
- human-readable presentation: `outputs/hotel_markdown`

### QA / validation layers

- field-level QA rules in `src/qa_checks.py`
- ClickUp export readiness checks
- batch readiness scoring
- operator decision summaries
- orchestration payload validation
- archive cross-checks
- simulated orchestration scenarios and regression reports

### Reporting layers

- `run_summary.txt`
- `run_delta_report.txt`
- `run_manifest.json`
- operator summaries and checklists
- markdown hotel briefs and shortlist summaries
- regression reports for orchestration

### Human handoff points

- review of manual shortlist
- ClickUp import gate GO/NO_GO
- ClickUp rehearsal verification
- Phase 6 operator runbook and evidence templates
- live-day decision logs and SOPs

### External tool assumptions

- raw source likely comes from Apify/Google Maps-style exports
- optional Google Places API
- OpenAI API for v3-lite commercial synthesis
- ClickUp workspace/list/custom fields exist and are partly validated
- Make scenario exists or can be provisioned

## Source-of-Truth Assessment

### Architecture

Likely canonical:

- [`docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md)
- [`docs/project/OUTPUT_CSV_SCHEMAS.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/OUTPUT_CSV_SCHEMAS.md)

Legacy/bootstrapping:

- `project info/06_TARGET_ARCHITECTURE.md`
- `project info/07_REPO_STRUCTURE_AND_BUILD_RULES.md`

### Workflow

Actual current runtime source of truth:

- [`src/orchestrate.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/orchestrate.py)
- [`src/main.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/main.py)

Intended future/canonical workflow docs:

- [`docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md)
- [`docs/project/PHASE_6_UNIFIED_OPERATOR_RUNBOOK.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_UNIFIED_OPERATOR_RUNBOOK.md)

### Schemas

Canonical:

- configs in `configs/*.yaml`
- [`docs/project/OUTPUT_CSV_SCHEMAS.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/OUTPUT_CSV_SCHEMAS.md)
- [`configs/make_execution_payload_contract.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/make_execution_payload_contract.yaml)

### Orchestration

Canonical code:

- [`src/make_orchestration_runner.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/make_orchestration_runner.py)

Canonical contracts/docs:

- [`configs/orchestration.yaml`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/orchestration.yaml)
- [`docs/project/MAKE_EXECUTION_PAYLOAD_CONTRACT.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_EXECUTION_PAYLOAD_CONTRACT.md)

### Exports

Canonical logic:

- [`src/master_exports.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/master_exports.py)
- [`src/clickup_export.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_export.py)

Canonical schema guide:

- [`docs/project/OUTPUT_CSV_SCHEMAS.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/OUTPUT_CSV_SCHEMAS.md)

### Prompts

Current prompt files:

- [`prompts/enrichment/hotel_enrichment.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/prompts/enrichment/hotel_enrichment.md)
- [`prompts/email/cold_email.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/prompts/email/cold_email.md)

Reality:

- prompts are lightweight policy references, not the primary behavior engine
- for commercial synthesis, the real prompt source is mostly embedded in [`src/commercial_synthesizer.py`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/commercial_synthesizer.py)

### Docs

Most current status docs:

- [`docs/project/INTEGRATION_STATUS_SNAPSHOT.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/INTEGRATION_STATUS_SNAPSHOT.md)
- [`docs/project/PHASE_6_READINESS_SUMMARY.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_READINESS_SUMMARY.md)
- [`docs/project/PHASE_6_FINAL_READINESS_CLOSEOUT_SUMMARY.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_6_FINAL_READINESS_CLOSEOUT_SUMMARY.md)

Conflicting legacy docs:

- [`README.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/README.md) still frames current phase as Phase 5
- [`docs/project/CODEX_PROJECT_BRIEF.md`](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/CODEX_PROJECT_BRIEF.md) still says Phase 3

## Build Status

### Project stage classification

`structurally built but unvalidated`

### Why

- major local pipeline components exist and produce artifacts
- orchestration and operator-control layers are unusually complete
- the intended live Make path is externally blocked, so full end-to-end validation is missing
- the newer structured artifact architecture exists, but the default pipeline still uses an older execution path
- there is no single unified canonical run path covering all modern modules

## Gaps: Plan vs Reality

### Intended architecture

- structured commercial synthesis v3-lite
- ranking refresh as explicit decision engine
- markdown renderer as final operator layer
- Make as thin transport only

### Actual implementation

- local core pipeline works, but mostly through older flat-script flow
- v3-lite/ranking/renderer exist beside, not inside, the default orchestration
- docs describe a cleaner target system than the runtime currently enforces

### Missing layers

- one canonical pipeline that runs old and new layers together
- unified phase/status source of truth
- consistent batch naming/version retention policy
- automated test harness outside script-driven smoke checks

### Weak layers

- source-of-truth clarity
- repo hygiene around committed artifacts and legacy scaffolds
- prompt/config/code alignment for commercial synthesis

### Unnecessary or overbuilt layers

- large number of operational docs relative to codebase size
- many duplicate historical output versions committed in repo

### Underbuilt layers

- integration of `commercial_synthesizer`, `ranking_refresh`, and `render_full_enrichment_md` into main pipeline
- test coverage for data transformations at unit level
- cleanup/canonicalization of exports and docs

## Risks

### Architecture risks

- two competing commercial architectures: heuristic `v1` inside enrichment vs LLM `v3-lite`
- runtime pipeline and schema docs are diverging
- main pipeline does not execute the newest intended architecture

### Workflow risks

- operator may trust docs that do not match current runtime
- phase naming drift can cause wrong assumptions during cutover
- manual invocation of sidecar scripts may create inconsistent artifact sets

### Data quality risks

- fetch failures can still produce superficially complete downstream artifacts
- older heuristic commercial text can be mixed with newer ranked artifacts
- cross-batch fallback reuse in enrichment can obscure provenance if not watched carefully

### Maintenance risks

- large top-level script files instead of smaller modules
- historical outputs and docs make it harder to know what to edit safely
- no package structure enforcing boundaries

### Scaling risks

- file-system artifact sprawl
- batch/version naming explosion
- repo size growth from committed outputs

### Repo hygiene risks

- `.gitignore` ignores some outputs but not `outputs/master`, `outputs/export`, `outputs/source_bundles`, `outputs/factual_enrichment`, `outputs/commercial_synthesis`
- `.DS_Store` files are present in tracked tree
- `project info/` duplicates the main repo story

### Documentation gaps

- no single “current canonical architecture” doc tying old and new flows together
- no single table mapping every script to whether it is active, legacy, or optional

### Ownership ambiguity

- unclear whether `README`, phase docs, or runtime code should win when they conflict
- unclear whether v3-lite stack is experimental or intended canonical path today

### Dead-code / dead-file risks

- `project info/` is effectively legacy
- some outputs in `outputs/export` look purely comparative/debug-oriented
- some docs appear superseded by later checkpoint summaries

## Next Recommended Build Sequence

1. Declare one canonical runtime path and update `src/orchestrate.py` to match it, even if that means explicitly keeping legacy mode as a separate path.
2. Decide which commercial path is canonical: heuristic `commercial_synthesis/v1` inside enrichment or `commercial_synthesizer.py` v3-lite.
3. Decide whether `ranking_refresh.py` is required for production outputs; if yes, make it part of the main pipeline.
4. Decide whether `render_full_enrichment_md.py` is official output or optional reporting.
5. Collapse phase/status drift by updating `README`, `CODEX_PROJECT_BRIEF`, and Phase docs to one current status line.
6. Mark `project info/` as legacy scaffold or archive candidate.
7. Separate canonical example artifacts from historical output clutter.
8. Tighten `.gitignore` and decide what artifacts belong in git.
9. Add one “current source of truth” document for architecture/workflow/modules.
10. After that cleanup, perform a true end-to-end validation pass on the chosen canonical path.
