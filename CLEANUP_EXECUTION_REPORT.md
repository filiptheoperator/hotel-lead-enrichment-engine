# CLEANUP_EXECUTION_REPORT

## Scope

Cleanup bol vykonaný striktne podľa:

- `CLEANUP_PLAN.md`
- `RETENTION_AND_FIXTURE_POLICY.md`

V tomto kroku:

- runtime kód nebol upravovaný
- docs neboli prepísané, okrem `.gitignore` a tohto cleanup reportu
- neprebehlo žiadne heuristické mazanie mimo explicitného delete listu

## 1. Preserved Fixture Sets

### Canonical post-fix fixture set preserved

Zachované:

- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_post_fix_regen_20260410.csv`
- `outputs/email_drafts/Sydney 100_normalized_scored_enriched_batch10_email_drafts.csv`
- `outputs/master/Sydney 100_*_post_fix_regen_20260410.csv`
- `outputs/clickup/Sydney 100_normalized_scored_enriched_batch10_email_drafts_clickup_*.csv`
- `outputs/hotel_markdown/Sydney 100/*`
- selected 10-row Sydney 100 structured evidence set in:
  - `outputs/source_bundles/Sydney 100/`
  - `outputs/factual_enrichment/Sydney 100/`
  - `outputs/commercial_synthesis/Sydney 100/`

### Historical regression fixture set preserved

Zachované:

- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave4_v3lite_smoke.csv`
- matching `outputs/master/Sydney 100_*_wave4_v3lite_smoke.csv`

## 2. Archived

Archive root created:

- `data/archive/cleanup_2026-04-10_outputs_archive/`

### Archived ranked variants

Moved:

- all old Sydney 100 ranked variants except:
  - `...post_fix_regen_20260410.csv`
  - `...wave4_v3lite_smoke.csv`

### Archived master variants

Moved:

- all `outputs/master/Sydney 100_*.csv` except:
  - `*_post_fix_regen_20260410.csv`
  - `*_wave4_v3lite_smoke.csv`

### Archived duplicate ClickUp naming family

Moved:

- `outputs/clickup/Sydney 100_normalized_scored_enriched_email_drafts_clickup_full_ranked.csv`
- `outputs/clickup/Sydney 100_normalized_scored_enriched_email_drafts_clickup_import.csv`
- `outputs/clickup/Sydney 100_normalized_scored_enriched_email_drafts_clickup_import_high_only.csv`
- `outputs/clickup/Sydney 100_normalized_scored_enriched_email_drafts_clickup_phase1_minimal.csv`

### Archived QA packet folders

Moved:

- `data/qa/clickup_dry_run_packet/`
- `data/qa/clickup_operator_pack/`

## 3. Deleted

Deleted exactly as approved:

### `.gitkeep` files

- `outputs/hotel_markdown/.gitkeep`
- `outputs/ranked/.gitkeep`
- `outputs/email_drafts/.gitkeep`
- `outputs/clickup/.gitkeep`
- `data/qa/.gitkeep`

### Extra non-baseline Sydney 100 leftovers

- `outputs/source_bundles/Sydney 100/acc_2dcdede0d879.json`
- `outputs/source_bundles/Sydney 100/acc_42f76f030265.json`
- `outputs/source_bundles/Sydney 100/acc_b00f68991e06.json`
- `outputs/factual_enrichment/Sydney 100/acc_2dcdede0d879.json`
- `outputs/factual_enrichment/Sydney 100/acc_42f76f030265.json`
- `outputs/factual_enrichment/Sydney 100/acc_b00f68991e06.json`

## 4. `.gitignore` Update Applied

Updated:

- added ignore coverage for:
  - `data/archive/*`
  - `outputs/master/*`
  - `outputs/source_bundles/*`
  - `outputs/factual_enrichment/*`
  - `outputs/commercial_synthesis/*`
- kept explicit unignore rules for:
  - canonical post-fix fixture files
  - historical regression fixture files
  - selected QA/gate evidence files
  - cleanup archive location

## 5. Verification

Verified preserved files still exist:

- canonical ranked fixture
- historical ranked regression fixture
- canonical email fixture
- canonical master fixture example
- historical master regression fixture example
- canonical ClickUp fixture example
- markdown QA fixture
- canonical docs:
  - `CURRENT_SYSTEM_STATUS.md`
  - `README.md`
  - `CODEX_PROJECT_BRIEF.md`
  - `CANONICAL_RUNBOOK.md`
  - `RETENTION_AND_FIXTURE_POLICY.md`
  - `CLEANUP_PLAN.md`

Verified cleanup actions:

- sample ranked archive file exists in archive root
- sample master archive file exists in archive root
- sample duplicate ClickUp archive file exists in archive root
- archived QA packet directory exists in archive root
- deleted extra structured leftovers no longer exist
- deleted `.gitkeep` no longer exists

## 6. Important Repo State Note

`git status` still shows pre-existing runtime/output diffs outside the scope of this cleanup execution, notably:

- modified `src/master_exports.py`
- modified selected `outputs/source_bundles/Sydney 100/*.json`
- modified selected `outputs/factual_enrichment/Sydney 100/*.json`

Tieto neboli menené v tomto cleanup kroku. Sú to už existujúce pracovné zmeny z predchádzajúcich krokov.

## 7. Result

Repo je po tomto kroku citeľne čistejší:

- canonical fixture line je oddelená
- one regression fixture line je ponechaná
- variant sprawl v `outputs/master/` a `outputs/ranked/` je odstránený z aktívnej plochy
- duplicate ClickUp family je odsunutá
- QA packet duplication je odsunutá

Repo ešte nie je “final polished”, ale je už výrazne bližšie k finálnemu review stavu.
