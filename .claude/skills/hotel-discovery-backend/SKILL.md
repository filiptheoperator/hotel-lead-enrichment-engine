---
name: hotel-discovery-backend
description: Review, design, implement, or challenge HOTEL AI DISCOVERY backend changes while preserving Drive business authority, evidence provenance, phase gates, and safe technical boundaries.
---

# HOTEL AI DISCOVERY Backend Skill

Use this skill for repo-scale backend work in `hotel-lead-enrichment-engine`.

## Read first

1. `CLAUDE.md`
2. `AGENTS.md`
3. `docs/BUSINESS_CONTEXT.md`
4. `docs/BACKEND_ROADMAP.md`
5. task-specific manifest/RUN/TECH_RUN handoff supplied by the operator

## Authority

- Google Drive/Sheets = canonical business/evidence/decision truth.
- GitHub = code/config/test truth.
- Local mirror = temporary technical snapshot only.

Never infer canonical business rules from stale repo artifacts when the active handoff says otherwise.

## Review sequence

1. Restate the requested technical outcome and current phase gate.
2. Identify current modules/contracts affected.
3. Identify any conflicting legacy assumptions.
4. Check data/provenance/security boundaries.
5. Prefer reuse over new framework introduction.
6. Propose the smallest coherent change set.
7. Define tests before or alongside consequential changes.
8. Implement only within approved mode/scope.
9. Run tests + `git diff --check`.
10. Return findings as `ACCEPT`, `FIX`, `DEFER`, or `OPTIONAL` with evidence.

## Domain invariants

Keep these canonical domains distinct:
- Community Intelligence
- Hotel Intelligence
- Competitor Intelligence

Derived layers:
- Market Research
- Lead Engine
- Discovery Command Center

Do not silently collapse raw domain records into one schema.

## Evidence invariants

Preserve distinctions among:
- VERIFIED / FACT
- PUBLIC_SIGNAL
- EXPLICIT_CLAIM / SELF_REPORTED
- INFERENCE
- HYPOTHESIS
- UNKNOWN
- NOT_OBSERVED
- ABSENT_VERIFIED when explicitly supported

`NOT_OBSERVED` must never be promoted to verified absence.

## Entity resolution

Favor deterministic strong identifiers.
If identity is uncertain, emit ambiguity/QA rather than merging.

## Google Drive

Use Drive only through the explicitly approved integration/handoff.
For technical foundation work:
- prefer exact-ID reads;
- read-only first;
- fail closed on manifest/schema mismatch;
- never log secrets;
- never treat local mirror changes as canonical edits.

Any write path must be allowlisted, schema-checked, dry-run capable, idempotent and audited.

## Forbidden without explicit future authorization

- automatic email/DM/outreach sending;
- generic Google Drive mutation;
- raw community/lead data committed to Git;
- guest PII/private hotel secrets;
- prohibited scraping;
- live HubSpot/CRM synchronization before Phase 2;
- changing business source-of-truth semantics from code.

## Good Claude Code use cases

- architecture review across many files;
- complex refactor planning;
- schema consistency review;
- security/permission boundary review;
- Drive adapter review;
- entity-resolution edge-case review;
- test design and gap analysis;
- independent challenge of a Codex implementation;
- multi-module implementation after plan approval.

## Business identity

The Hotel Operator — https://thehoteloperator.com/

The public website is positioning, not canonical validation evidence.