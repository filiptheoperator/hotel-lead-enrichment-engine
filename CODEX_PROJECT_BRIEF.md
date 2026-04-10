# CODEX PROJECT BRIEF

## Project

Hotel Lead Enrichment Engine OS

## Core goal

Udržať jeden stabilný Python-first workflow, ktorý premieňa raw hotel lead export na grounded enrichment, ranking, outreach a ClickUp-ready handoff.

## Canonical flow

`normalize -> factual/source_bundle -> commercial_synthesizer(v3-lite) -> ranking_refresh -> email_drafts -> master_exports -> render_full_enrichment_md -> clickup_export -> QA/gate -> Make`

## Priority order

1. pipeline stability
2. data quality
3. enrichment quality
4. email relevance
5. CRM cleanliness
6. only then further automation

## Build rules

- jedna kanonická flow
- Python ostáva primárna runtime vrstva
- Make je tenká execution vrstva, nie business logic layer
- configs sú oddelené od kódu
- raw vstupy sa neprepisujú
- neoverené údaje musia byť explicitne označené
- commercial layer je `commercial_synthesis/v3-lite`
- heuristic commercial generation v `enrich_hotels.py` je iba legacy fallback
- ranking source of truth je `ranking_refresh.py`
- final operator presentation source of truth je `render_full_enrichment_md.py`

## Working language

- guidance a operator-facing text po slovensky
- outreach po slovensky

## Current reality

- kanonická architektúra je potvrdená a runtime aligned
- canonical post-fix retained baseline existuje
- historical regression fixture je ponechaný
- cleanup execution a fixture retention policy už boli vykonané
- live Make execution nie je plne uzavretý ako validated end-to-end path
- branch je vo finálnej merge decision fáze

## Reference docs

- [CURRENT_SYSTEM_STATUS.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/CURRENT_SYSTEM_STATUS.md)
- [CANONICAL_RUNBOOK.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/CANONICAL_RUNBOOK.md)
- [RETENTION_AND_FIXTURE_POLICY.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/RETENTION_AND_FIXTURE_POLICY.md)
