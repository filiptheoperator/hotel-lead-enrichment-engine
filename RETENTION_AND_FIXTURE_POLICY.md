# RETENTION_AND_FIXTURE_POLICY

## Cieľ

Tento dokument opisuje aktuálny retenčný model generated súborov v repozitári po vykonanom cleanupe. Neplánuje budúci cleanup krok. Uzamyká current-state truth:

- čo je retained canonical fixture
- čo je retained historical regression fixture
- čo už bolo archivované
- ako sa má repo správať ďalej

## Kategórie

### Canonical fixture

Commitnutý generated set, ktorý reprezentuje aktuálnu kanonickú post-fix pravdu systému.

### Historical regression fixture

Commitnutý generated set, ktorý zostáva zámerne ako pre-fix comparator, nie ako source-of-truth runtime baseline.

### Archived

Historical materiál presunutý do explicitnej archival zóny mimo aktívnej working plochy repa.

## Aktuálne retained fixture sety

## Canonical fixture set to keep

### Ranked

- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_post_fix_regen_20260410.csv`

### Email

- `outputs/email_drafts/Sydney 100_normalized_scored_enriched_batch10_email_drafts.csv`

### Master exports

- `outputs/master/Sydney 100_accounts_master_post_fix_regen_20260410.csv`
- `outputs/master/Sydney 100_enrichment_master_post_fix_regen_20260410.csv`
- `outputs/master/Sydney 100_outreach_drafts_post_fix_regen_20260410.csv`
- `outputs/master/Sydney 100_dedupe_review_post_fix_regen_20260410.csv`
- `outputs/master/Sydney 100_operator_shortlist_post_fix_regen_20260410.csv`
- `outputs/master/Sydney 100_review_queue_post_fix_regen_20260410.csv`
- `outputs/master/Sydney 100_top_20_export_post_fix_regen_20260410.csv`

### ClickUp exports

- `outputs/clickup/Sydney 100_normalized_scored_enriched_batch10_email_drafts_clickup_import.csv`
- `outputs/clickup/Sydney 100_normalized_scored_enriched_batch10_email_drafts_clickup_full_ranked.csv`
- `outputs/clickup/Sydney 100_normalized_scored_enriched_batch10_email_drafts_clickup_phase1_minimal.csv`
- `outputs/clickup/Sydney 100_normalized_scored_enriched_batch10_email_drafts_clickup_import_high_only.csv`

### Markdown outputs

- `outputs/hotel_markdown/Sydney 100/*.md`
- `outputs/hotel_markdown/Sydney 100/operator_shortlist_summary.md`
- `outputs/hotel_markdown/Sydney 100/review_queue_summary.md`
- `outputs/hotel_markdown/Sydney 100/top_export_summary.md`
- `outputs/hotel_markdown/Sydney 100/wave5_render_qa_report.csv`

### Structured evidence set

Retained canonical upstream evidence:

- `outputs/source_bundles/Sydney 100/`
- `outputs/factual_enrichment/Sydney 100/`
- `outputs/commercial_synthesis/Sydney 100/`

Presne retained je 10-riadková Sydney 100 baseline, nie širší leftover set.

## Historical regression fixture to keep

### Ranked regression comparator

- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave4_v3lite_smoke.csv`

### Matching retained master family

- `outputs/master/Sydney 100_*_wave4_v3lite_smoke.csv`

Účel:

- pre-fix schema bleed comparator
- regression evidence
- nie canonical truth

## Čo už bolo archivované

Archive location:

- `data/archive/cleanup_2026-04-10_outputs_archive/`

Do tejto zóny boli presunuté:

- staré ranked iterácie mimo canonical post-fix a regression smoke baseline
- staré `outputs/master` varianty mimo retained canonical + regression rodín
- duplicate ClickUp rodina s namingom `...normalized_scored_enriched_email_drafts...`
- veľké QA packet rodiny:
  - `clickup_dry_run_packet/`
  - `clickup_operator_pack/`

## Retention model going forward

### Čo má zostať commitnuté

- root source-of-truth docs
- runtime contracts v `configs/`
- retained canonical fixture set
- retained historical regression fixture set
- minimálny retained QA/gate evidence set
- explicitná archive zóna z cleanup execution

### Čo sa už nemá vracať do aktívnej plochy

- paralelné `v2/v3/v4/v5` output rodiny toho istého batchu
- neoznačené latest-run output sprawl
- duplicate packet copy families bez fixture dôvodu
- duplicate ClickUp naming families

## Naming reality

### Canonical retained truth

Aktuálna canonical baseline je zámerne identifikovaná explicitným suffixom:

- `post_fix_regen_20260410`

### Historical retained truth

Aktuálny retained regression comparator je zámerne identifikovaný:

- `wave4_v3lite_smoke`

### Future preference

Do budúcnosti preferovať:

- jeden jasný canonical verification suffix
- jeden jasný regression suffix
- nevracať sa k neobmedzeným `v2/v3/v4/v5` sériám v aktívnej ploche

## Policy for `data/qa`

### Currently retained in active repo surface

- `run_manifest.json`
- `clickup_import_gate.json`
- `clickup_import_gate.txt`
- `clickup_import_gate_high_only.json`
- `clickup_import_gate_high_only.txt`
- `batch_readiness_explanation.json`
- `batch_readiness_explanation.txt`

### Already archived

- veľké packet duplication families presunuté do cleanup archive zóny

## Policy for `project info/`

- nie je active source-of-truth
- nie je fixture baseline
- je to legacy bootstrap material
- neskôr sa môže presunúť do archivovanej docs vrstvy, ale v tomto retained stave ostáva mimo aktívnej runtime truth
