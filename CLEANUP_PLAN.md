# CLEANUP_PLAN

## 1. CANONICAL FIXTURE SET TO KEEP

Tento set má zostať v repo ako kanonický post-fix verification baseline.

### Ranked

- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_post_fix_regen_20260410.csv`

### Email

- `outputs/email_drafts/Sydney 100_normalized_scored_enriched_batch10_email_drafts.csv`

Poznámka:
- email file nemá vlastný post-fix suffix, ale je to aktuálny downstream output naviazaný na nový ranked baseline.

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

- `outputs/hotel_markdown/Sydney 100/acc_30048fcea764.md`
- `outputs/hotel_markdown/Sydney 100/acc_401880adbecd.md`
- `outputs/hotel_markdown/Sydney 100/acc_40da1daa32cc.md`
- `outputs/hotel_markdown/Sydney 100/acc_462634ba1b0d.md`
- `outputs/hotel_markdown/Sydney 100/acc_50ce289c9223.md`
- `outputs/hotel_markdown/Sydney 100/acc_5970be661818.md`
- `outputs/hotel_markdown/Sydney 100/acc_6bb4cbb1a3e4.md`
- `outputs/hotel_markdown/Sydney 100/acc_85a1025fc0d6.md`
- `outputs/hotel_markdown/Sydney 100/acc_9f2cb7250cf5.md`
- `outputs/hotel_markdown/Sydney 100/acc_d7e3595aefb6.md`
- `outputs/hotel_markdown/Sydney 100/operator_shortlist_summary.md`
- `outputs/hotel_markdown/Sydney 100/review_queue_summary.md`
- `outputs/hotel_markdown/Sydney 100/top_export_summary.md`
- `outputs/hotel_markdown/Sydney 100/wave5_render_qa_report.csv`

### Structured upstream evidence for the same Sydney 100 baseline

Keep the current `Sydney 100` structured artifacts as the canonical evidence bundle for the canonical verification line:

- `outputs/source_bundles/Sydney 100/acc_30048fcea764.json`
- `outputs/source_bundles/Sydney 100/acc_401880adbecd.json`
- `outputs/source_bundles/Sydney 100/acc_40da1daa32cc.json`
- `outputs/source_bundles/Sydney 100/acc_462634ba1b0d.json`
- `outputs/source_bundles/Sydney 100/acc_50ce289c9223.json`
- `outputs/source_bundles/Sydney 100/acc_5970be661818.json`
- `outputs/source_bundles/Sydney 100/acc_6bb4cbb1a3e4.json`
- `outputs/source_bundles/Sydney 100/acc_85a1025fc0d6.json`
- `outputs/source_bundles/Sydney 100/acc_9f2cb7250cf5.json`
- `outputs/source_bundles/Sydney 100/acc_d7e3595aefb6.json`
- `outputs/factual_enrichment/Sydney 100/acc_30048fcea764.json`
- `outputs/factual_enrichment/Sydney 100/acc_401880adbecd.json`
- `outputs/factual_enrichment/Sydney 100/acc_40da1daa32cc.json`
- `outputs/factual_enrichment/Sydney 100/acc_462634ba1b0d.json`
- `outputs/factual_enrichment/Sydney 100/acc_50ce289c9223.json`
- `outputs/factual_enrichment/Sydney 100/acc_5970be661818.json`
- `outputs/factual_enrichment/Sydney 100/acc_6bb4cbb1a3e4.json`
- `outputs/factual_enrichment/Sydney 100/acc_85a1025fc0d6.json`
- `outputs/factual_enrichment/Sydney 100/acc_9f2cb7250cf5.json`
- `outputs/factual_enrichment/Sydney 100/acc_d7e3595aefb6.json`
- `outputs/commercial_synthesis/Sydney 100/acc_30048fcea764.json`
- `outputs/commercial_synthesis/Sydney 100/acc_401880adbecd.json`
- `outputs/commercial_synthesis/Sydney 100/acc_40da1daa32cc.json`
- `outputs/commercial_synthesis/Sydney 100/acc_462634ba1b0d.json`
- `outputs/commercial_synthesis/Sydney 100/acc_50ce289c9223.json`
- `outputs/commercial_synthesis/Sydney 100/acc_5970be661818.json`
- `outputs/commercial_synthesis/Sydney 100/acc_6bb4cbb1a3e4.json`
- `outputs/commercial_synthesis/Sydney 100/acc_85a1025fc0d6.json`
- `outputs/commercial_synthesis/Sydney 100/acc_9f2cb7250cf5.json`
- `outputs/commercial_synthesis/Sydney 100/acc_d7e3595aefb6.json`

### Contract and evidence docs to keep

- `CURRENT_SYSTEM_STATUS.md`
- `README.md`
- `CODEX_PROJECT_BRIEF.md`
- `RETENTION_AND_FIXTURE_POLICY.md`
- `CANONICAL_RUNBOOK.md`
- `VALIDATION_REPORT.md`
- `LEGACY_SCHEMA_BLEED_DIAGNOSIS.md`
- `POST_FIX_REGEN_VERIFICATION.md`
- `UNIFICATION_CHANGELOG.md`
- `docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md`
- `docs/project/OUTPUT_CSV_SCHEMAS.md`
- `docs/project/MAKE_EXECUTION_PAYLOAD_CONTRACT.md`
- `docs/project/CLICKUP_API_PAYLOAD_CONTRACT_FINAL.md`

## 2. HISTORICAL REGRESSION FIXTURE TO KEEP

Tento set má zostať ako pre-fix regression evidence, nie ako kanonická truth.

### Mixed ranked regression fixture

- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave4_v3lite_smoke.csv`

### Historical downstream pairing for the same mixed regression state

- `outputs/master/Sydney 100_accounts_master_wave4_v3lite_smoke.csv`
- `outputs/master/Sydney 100_enrichment_master_wave4_v3lite_smoke.csv`
- `outputs/master/Sydney 100_outreach_drafts_wave4_v3lite_smoke.csv`
- `outputs/master/Sydney 100_dedupe_review_wave4_v3lite_smoke.csv`
- `outputs/master/Sydney 100_operator_shortlist_wave4_v3lite_smoke.csv`
- `outputs/master/Sydney 100_review_queue_wave4_v3lite_smoke.csv`
- `outputs/master/Sydney 100_top_20_export_wave4_v3lite_smoke.csv`

### Why keep

- ukazuje presne pre-fix mixed schema bleed stav
- dá sa použiť ako regression comparator pre budúce boundary kontroly
- je menší a čistejší než ponechať všetky staré `v2/v3/v4/v5` varianty

## 3. ARCHIVE CANDIDATES

Tieto položky sú vhodné na presun do explicitnej archival vrstvy, nie na ponechanie v aktívnom working set-e.

### Old ranked iterations beyond one regression fixture

- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_batch10_v2.csv`
- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_batch10_v3.csv`
- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_batch10_v4.csv`
- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave3_final5.csv`
- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave4_batch10.csv`
- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave4_batch10_v2.csv`
- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave4_batch10_v3.csv`
- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave4_batch10_v4.csv`
- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave4_batch10_v5.csv`

### Old master export families beyond canonical + one regression pair

- všetky `outputs/master/Sydney 100_*` bez suffixu `post_fix_regen_20260410`
- výnimka:
  - `*_wave4_v3lite_smoke.csv` ponechať ako historical regression fixture

To prakticky znamená archivovať najmä:

- `outputs/master/*_batch10*.csv`
- `outputs/master/*_wave3_final5.csv`
- `outputs/master/*_wave4_batch10*.csv`
- root-like older exports bez suffixu:
  - `outputs/master/Sydney 100_accounts_master.csv`
  - `outputs/master/Sydney 100_enrichment_master.csv`
  - `outputs/master/Sydney 100_outreach_drafts.csv`
  - `outputs/master/Sydney 100_dedupe_review.csv`
  - `outputs/master/Sydney 100_operator_shortlist.csv`
  - `outputs/master/Sydney 100_top_20_export.csv`

### Duplicate ClickUp families with older naming stem

- `outputs/clickup/Sydney 100_normalized_scored_enriched_email_drafts_clickup_full_ranked.csv`
- `outputs/clickup/Sydney 100_normalized_scored_enriched_email_drafts_clickup_import.csv`
- `outputs/clickup/Sydney 100_normalized_scored_enriched_email_drafts_clickup_import_high_only.csv`
- `outputs/clickup/Sydney 100_normalized_scored_enriched_email_drafts_clickup_phase1_minimal.csv`

### QA packet duplication families

Archive candidates:

- `data/qa/clickup_dry_run_packet/`
- `data/qa/clickup_operator_pack/`

Dôvod:

- sú veľké
- obsahujú duplicity naprieč batchmi
- majú skôr evidenčný/ops význam než aktívny runtime význam

### Existing archive tree

- `data/archive/`

Poznámka:
- toto už je archival zóna, takže nemá zostať v aktívnom fixture sete
- neskôr možno presunúť mimo git alebo mimo core repo snapshot

## 4. DELETE CANDIDATES

Delete candidates definujem úzko. Bez vykonania a až po poslednom potvrdení.

### Safe delete candidates

- `outputs/hotel_markdown/.gitkeep`
  - iba ak priečinok ostane commitnutý cez reálne fixture súbory
- `outputs/ranked/.gitkeep`
  - iba ak priečinok ostane commitnutý cez reálne fixture súbory
- `outputs/email_drafts/.gitkeep`
  - iba ak priečinok ostane commitnutý cez reálne fixture súbory
- `outputs/clickup/.gitkeep`
  - iba ak priečinok ostane commitnutý cez reálne fixture súbory
- `data/qa/.gitkeep`
  - iba ak priečinok ostane commitnutý cez reálne fixture / gate súbory

### Extra structured artifacts not in the selected Sydney 100 canonical baseline

Needs careful delete review after confirmation:

- `outputs/source_bundles/Sydney 100/acc_2dcdede0d879.json`
- `outputs/source_bundles/Sydney 100/acc_42f76f030265.json`
- `outputs/source_bundles/Sydney 100/acc_b00f68991e06.json`
- `outputs/factual_enrichment/Sydney 100/acc_2dcdede0d879.json`
- `outputs/factual_enrichment/Sydney 100/acc_42f76f030265.json`
- `outputs/factual_enrichment/Sydney 100/acc_b00f68991e06.json`

Dôvod:

- nie sú súčasťou 10-riadkového kanonického post-fix baseline
- zvyšujú nejasnosť, čo presne je fixture dataset
- momentálne sú navyše untracked/extra a pôsobia ako leftovers

### Not delete candidates right now

Nemažte zatiaľ:

- `outputs/commercial_synthesis/Sydney 100/*.json`
- `outputs/source_bundles/Sydney 100/*.json` v kanonickej 10-riadkovej sade
- `outputs/factual_enrichment/Sydney 100/*.json` v kanonickej 10-riadkovej sade
- `outputs/ranked/*wave4_v3lite_smoke.csv`
- súvisiacu historical regression master rodinu

## 5. .GITIGNORE UPDATES TO APPLY

Aktuálny `.gitignore` už ignoruje časť generated outputs, ale nie všetky relevantné rodiny.

### Add after fixture selection is physically separated

Odporúčané doplniť:

- `outputs/source_bundles/*`
- `outputs/factual_enrichment/*`
- `outputs/commercial_synthesis/*`
- `outputs/master/*`
- `data/archive/*`

### Keep explicit exceptions for committed fixtures

Použiť pattern štýlu:

- ignore whole family
- potom explicitne unignore fixture paths

Príklad smerovania, nie finálny patch:

- ignore `outputs/ranked/*`
- unignore:
  - `.gitkeep`
  - `Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_post_fix_regen_20260410.csv`
  - `Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_wave4_v3lite_smoke.csv`

Rovnaký model odporúčam pre:

- `outputs/master/`
- `outputs/clickup/`
- `outputs/email_drafts/`
- `outputs/hotel_markdown/`
- `outputs/source_bundles/Sydney 100/`
- `outputs/factual_enrichment/Sydney 100/`
- `outputs/commercial_synthesis/Sydney 100/`

### Important note

Keďže viaceré generated files sú už tracknuté, samotný `.gitignore` ich z gitu neodstráni. Preto musí ísť `.gitignore` update až po vedomom retain/archive/delete rozhodnutí.

## 6. RISKS IF CLEANUP IS EXECUTED

### Fixture ambiguity risk

- ak sa neoddelí 10-riadková Sydney 100 canonical baseline od extra structured leftovers, repo ostane nejasné

### Regression evidence loss risk

- ak sa omylom odstráni `wave4_v3lite_smoke` rodina, stratí sa pre-fix comparator

### QA evidence loss risk

- `data/qa/` je veľmi preplnené, ale obsahuje aj dôležité gate/readiness dôkazy
- hromadný cleanup bez whitelistu by mohol odstrániť operátorsky dôležité manifesty a gate outputs

### Gitignore mismatch risk

- ak sa `.gitignore` spraví skôr než sa fyzicky oddelí fixture set, repo začne tajiť dôležité generated dôkazy

### Historical archive confusion risk

- `data/archive/` je už archival zóna; miešať ju s aktívnym cleanup krokom bez presného cieľa by bolo riskantné

## 7. SAFE EXECUTION ORDER

1. Označiť a zamknúť presný fixture whitelist.
2. Potvrdiť, že canonical Sydney 100 post-fix baseline je jediný aktívny fixture set.
3. Potvrdiť, že `wave4_v3lite_smoke` rodina ostáva ako jediný historical regression fixture.
4. Oddeliť archive candidates zo `Sydney 100` variant sprawl v `outputs/ranked/` a `outputs/master/`.
5. Oddeliť duplicate ClickUp naming family bez `batch10`.
6. Rozhodnúť o `data/qa/`:
   - čo je canonical evidence
   - čo je operator pack historical
   - čo je duplicita
7. Až potom upraviť `.gitignore`.
8. Až po `.gitignore` a po potvrdení whitelistu vykonať fyzický cleanup.
