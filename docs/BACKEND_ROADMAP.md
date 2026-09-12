# HOTEL AI DISCOVERY — Backend Roadmap

Canonical business authority: Google Drive / Google Sheets.
Canonical backend codebase: this repository.
Business website: https://thehoteloperator.com/

## TECH_RUN_01 — Discovery Backend Foundation

### 0. Baseline
- run existing tests;
- inventory modules/configs/prompts;
- identify obsolete ClickUp-first and city-profile assumptions;
- map donor components before migration.

### 1. Versioned contracts
Create technical contracts/adapters for:
- Community Intelligence;
- Hotel Intelligence;
- Competitor Intelligence;
- Market Signal;
- Opportunity;
- Run State / Audit Event.

### 2. Exact-ID Drive read layer
Port/adapt proven patterns from `filip-ai-os`:
- exact runtime IDs;
- read-only OAuth first;
- ignored local mirror;
- revision/hash metadata;
- fail-closed validation;
- safe logs/secret checks.

### 3. Canonical Sheet adapters
Parse the canonical source-domain sheets into stable typed objects while preserving record IDs, evidence/provenance, timestamps and evidence status.

### 4. Entity resolution
- deterministic hotel IDs;
- conservative person identity matching;
- duplicate/ambiguity records rather than silent merge.

### 5. Evidence/provenance
Preserve and validate VERIFIED / PUBLIC_SIGNAL / EXPLICIT_CLAIM / INFERENCE / HYPOTHESIS / UNKNOWN / NOT_OBSERVED / ABSENT_VERIFIED semantics where applicable.

### 6. Explainable scoring
Move business scoring to config-driven components. Every overall score should expose its inputs, confidence and missing-data effect.

### 7. Run state / QA / audit
Record code SHA, manifest/schema versions, inputs, counts, duplicates, ambiguities, validation failures, proposed/performed writes and result status.

### 8. Controlled write-back
Implement plan/dry-run before live mutation. Any live writer must be exact-ID allowlisted, schema-checked, stable-key upsert based, idempotent, audited and explicitly authorized.

## Phase 2 — blocked until business gate
Not part of TECH_RUN_01 completion:
- live HubSpot sync;
- full CRM migration;
- broad dashboard automation;
- automatic outreach sending.

## Donor repositories

`filip-ai-os`: Drive/security/healthcheck patterns.

`codex_acquisition_orchestrator`: ingest/review/run/test patterns only; do not port ClickUp-as-source-of-truth or Bratislava/Košice/Praha architecture.

`hotel-aios-kitchen-demo`: optional UI/dashboard/evidence-state patterns.

## Merge gates

Before merging substantial backend changes:

```bash
python3 -m unittest discover -s tests -v
git diff --check
```

Also run any project-specific healthcheck introduced by TECH_RUN_01.

No merge should introduce raw private data, credentials or automatic outbound communication.