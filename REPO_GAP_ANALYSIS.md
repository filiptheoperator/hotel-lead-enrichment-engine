# Repo Gap Analysis

## Intended vs Actual

### Intended

- one clear Python-first operating system
- structured enrichment and commercial reasoning
- explicit ranking refresh
- clean operator-facing markdown layer
- thin Make orchestration over locked payloads
- ClickUp live execution after rehearsal and gating

### Actual

- a real local Python pipeline exists
- a newer structured stack also exists
- the default run path still reflects an older integrated flow
- Make live path is blocked externally
- docs and phases drift across multiple generations

## Major Missing Components

1. A single canonical execution path for the whole intended architecture.
2. A formal decision on whether `commercial_synthesis/v1` or `v3-lite` is the real standard.
3. Integration of `ranking_refresh.py` into the default pipeline if it is meant to be authoritative.
4. Integration of `render_full_enrichment_md.py` into default reporting if Wave 5 is official.
5. A single current status doc that overrides stale phase references.
6. A repo-level retention/archive policy for generated outputs committed to git.
7. Unit-style regression coverage for normalization/enrichment/export logic.
8. Explicit labeling of legacy vs canonical docs and files.

## Weak Layers

### Architecture coherence

- codebase has progressed faster than its top-level narrative
- active runtime and intended target architecture are not the same thing

### Commercial reasoning

- old heuristic commercial generation still sits in the main enrichment path
- newer LLM commercial synthesis exists but is not the default engine

### Ranking and presentation

- ranking refresh and markdown rendering look like intended canonical layers
- but they are effectively sidecar scripts today

### Repo hygiene

- output sprawl
- committed generated files
- duplicated scaffold material

## Overbuilt Parts

- operational documentation for Make/ClickUp cutover is extensive relative to the still-unified code path
- many closeout/checkpoint summaries repeat similar status information

## Underbuilt Parts

- codebase unification
- canonical status signaling
- small automated tests at module level
- archival/fixture discipline

## What To Ignore For Now

- rewriting the entire architecture before choosing the canonical path
- deleting outputs or docs without a retention decision
- replacing Make/ClickUp docs while the external blocker still exists
- refactoring `src/` into a package tree before resolving source-of-truth conflicts

## Next 10 Highest-Leverage Actions

1. Write one `CURRENT_SYSTEM_STATUS.md` or equivalent canonical doc that names the active phase, canonical flow, and legacy zones.
2. Decide whether the canonical commercial layer is:
`enrich_hotels.py` heuristic `commercial_synthesis/v1`
or
`commercial_synthesizer.py` `commercial_synthesis/v3-lite`
3. Decide whether `ranking_refresh.py` is required for production outputs.
4. If yes, add `commercial_synthesizer -> ranking_refresh` into the main pipeline, or explicitly mark them optional/experimental.
5. Update `README.md` and `docs/project/CODEX_PROJECT_BRIEF.md` to match the actual current state.
6. Mark `project info/` as legacy scaffold or move it to an archive/docs-history area.
7. Create a canonical output naming policy and mark which files in `outputs/` are fixtures vs historical runs.
8. Tighten `.gitignore` for generated output families that should not keep accumulating in git.
9. Add a module inventory doc listing every script as `active`, `supporting`, `test/sim`, `legacy`, or `optional`.
10. Run one deliberate end-to-end validation on the chosen canonical path and record it as the baseline build state.
