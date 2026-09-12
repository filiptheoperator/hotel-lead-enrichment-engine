# VS Code Setup — HOTEL AI DISCOVERY Backend

Use VS Code as the local development/review surface. It is not canonical business memory.

## Recommended sibling-clone layout

```text
HOTEL_AI_DISCOVERY_CODE/
  hotel-lead-enrichment-engine/      # active backend
  hotel-ai-clarity/                  # website
  filip-ai-os/                       # infra donor, separate system
  codex_acquisition_orchestrator/    # legacy donor
  hotel-aios-kitchen-demo/           # UI donor
```

Only edit the repository assigned by the current task. Cross-repo clones are primarily for comparison/reuse.

## Core backend setup

```bash
cd hotel-lead-enrichment-engine
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 -m unittest discover -s tests -v
git diff --check
```

Populate runtime secrets and canonical IDs locally only.

## Private/runtime data

Do not place canonical Drive datasets in tracked folders.

Use ignored local paths for:
- Drive mirror/snapshots;
- OAuth credentials/tokens;
- temporary XLSX/CSV exports containing real records;
- raw community or lead data;
- database/cache files.

## Agent usage

### Codex
Read `AGENTS.md` first. Codex is the primary implementation agent.

### Claude Code
Read `CLAUDE.md` and `AGENTS.md`. Start repo-scale architecture/refactor work in Plan mode. Use implementation mode only for an explicitly approved task.

## Branch discipline

For substantial work:

```bash
git switch -c tech/<short-task-name>
# edit + test
git status
git diff --check
python3 -m unittest discover -s tests -v
```

Open a PR after tests pass.

## Donor rule

Do not copy whole donor repositories into this repo. Port the minimum useful module/pattern, write tests, and record the provenance of the migrated technical idea in the PR/commit description.

## Website

The Hotel Operator: https://thehoteloperator.com/

Website source belongs in `hotel-ai-clarity`, not this backend repo.