# Repo Cleanup Proposal

No destructive action should happen without approval. This is a safe review-first proposal only.

## Safe Cleanup Candidates

- tracked `.DS_Store` files
- stale generated outputs in `outputs/export/` that are purely comparison/debug artifacts
- redundant historical output versions in `outputs/master/` once a canonical fixture set is chosen
- redundant generated packet copies in `data/qa/clickup_operator_pack/` and `data/qa/clickup_dry_run_packet/` if not required as committed fixtures
- `project info/` after confirming it is legacy bootstrap material

## Archive Proposals

### Proposal 1: archive `project info/`

Reason:

- it documents the repo’s origin well
- it is not the active runtime source of truth
- it duplicates configs/docs/README concepts

Suggested destination:

- `docs/archive/project-info-bootstrap/`
or a top-level `archive/` area outside active runtime paths

### Proposal 2: archive historical export waves

Reason:

- current repo contains many `wave*`, `batch10`, `v2/v3/v4/v5` files
- they are useful for analysis but harmful to clarity if left mixed with canonical outputs

Suggested structure:

- keep one canonical fixture set in `outputs/fixtures/` or equivalent
- move older run history to `outputs/archive_runs/` or external storage

### Proposal 3: archive superseded status docs

Reason:

- many closeout/checkpoint files report similar milestone progress
- a smaller set of canonical docs would be easier to maintain

Suggested keepers:

- architecture doc
- output/schema doc
- current readiness/status doc
- unified operator runbook
- contract docs

## `.gitignore` Recommendations

Current `.gitignore` only ignores some generated outputs. It should be reviewed to cover whichever generated paths are not meant to be versioned.

Candidates to consider ignoring:

- `outputs/master/*`
- `outputs/export/*`
- `outputs/source_bundles/*`
- `outputs/factual_enrichment/*`
- `outputs/commercial_synthesis/*`
- `data/archive/*`
- specific generated `data/qa/*` runtime outputs, while keeping fixture scenario folders if needed

Important note:

- do not ignore these blindly before deciding which generated artifacts are intentional fixtures
- some committed outputs currently act as evidence/examples/contracts

## Repo Hygiene Issues

1. Phase/status drift across `README`, project brief, and Phase 6 docs.
2. Large volume of committed generated artifacts.
3. Legacy scaffold lives beside active runtime.
4. Top-level `src/` scripts have grown large and overlap conceptually.
5. Prompt policy is split between prompt files and embedded instructions in code.
6. Two commercial synthesis paths are present.
7. Default pipeline does not reflect the newest intended architecture.

## Safe Cleanup Sequence

1. Label each major directory/file family as `canonical`, `fixture`, `historical`, or `legacy`.
2. Freeze the canonical runtime path.
3. Freeze the canonical docs set.
4. Move legacy scaffold and superseded docs into an archive area.
5. Move or prune historical generated outputs after confirming they are not active fixtures.
6. Update `.gitignore` to match the final retention decision.

## Recommended No-Risk Decisions Before Any Deletion

1. Confirm whether committed outputs are test fixtures or merely run leftovers.
2. Confirm whether `project info/` must stay in-repo for provenance.
3. Confirm whether Wave 5 markdown outputs are official deliverables.
4. Confirm whether orchestration simulation artifacts in `data/qa/` are part of the intended permanent evidence base.
