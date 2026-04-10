# POST-FIX REGEN VERIFICATION

## Scope

Tento krok overuje, že ranking boundary fix bol naozaj vykonaný do nového output setu a že downstream chain bola pregenerovaná nad tým istým post-fix batchom.

## 1. Fix Presence In Code

V `src/ranking_refresh.py` je fix prítomný:

- `CANONICAL_COMMERCIAL_SCHEMA_VERSION = "commercial_synthesis/v3-lite"`
- `commercial_schema_version` sa plní len pre kanonický `v3-lite`
- prítomné nové metadata stĺpce:
  - `commercial_source_mode`
  - `commercial_fallback_used`

## 2. New Ranked Output Produced

Bol vygenerovaný nový ranked artifact:

- `outputs/ranked/Sydney 100_normalized_scored_enriched_batch10_ranking_refreshed_post_fix_regen_20260410.csv`

Tento súbor je nový post-fix output set a nie iba starý `wave4_v3lite_smoke` artifact.

## 3. Commercial Schema Result

Overenie nového ranked súboru:

- `commercial_schema_version` obsahuje len:
  - `commercial_synthesis/v3-lite`
  - prázdnu hodnotu
- `commercial_synthesis/v1` sa v novom ranked outpute už nevyskytuje

Výsledok:

- `HAS_V1 = 0`

## 4. Metadata Columns

V novom ranked súbore sú prítomné:

- `commercial_source_mode`
- `commercial_fallback_used`

Koherencia:

- kanonické riadky:
  - `commercial_schema_version = commercial_synthesis/v3-lite`
  - `commercial_source_mode = canonical_v3_lite`
  - `commercial_fallback_used = no`
- fallback/missing riadky:
  - `commercial_schema_version = blank`
  - `commercial_source_mode = legacy_fallback_or_missing`
  - `commercial_fallback_used = yes`

## 5. Downstream Regeneration

Pregenerované downstream artefakty:

- email:
  - `outputs/email_drafts/Sydney 100_normalized_scored_enriched_batch10_email_drafts.csv`
- master:
  - `outputs/master/Sydney 100_accounts_master_post_fix_regen_20260410.csv`
  - `outputs/master/Sydney 100_enrichment_master_post_fix_regen_20260410.csv`
  - `outputs/master/Sydney 100_outreach_drafts_post_fix_regen_20260410.csv`
  - `outputs/master/Sydney 100_dedupe_review_post_fix_regen_20260410.csv`
  - `outputs/master/Sydney 100_operator_shortlist_post_fix_regen_20260410.csv`
  - `outputs/master/Sydney 100_review_queue_post_fix_regen_20260410.csv`
  - `outputs/master/Sydney 100_top_20_export_post_fix_regen_20260410.csv`
- clickup:
  - `outputs/clickup/Sydney 100_normalized_scored_enriched_batch10_email_drafts_clickup_import.csv`
  - `outputs/clickup/Sydney 100_normalized_scored_enriched_batch10_email_drafts_clickup_full_ranked.csv`
  - `outputs/clickup/Sydney 100_normalized_scored_enriched_batch10_email_drafts_clickup_phase1_minimal.csv`
  - `outputs/clickup/Sydney 100_normalized_scored_enriched_batch10_email_drafts_clickup_import_high_only.csv`
- markdown:
  - `outputs/hotel_markdown/Sydney 100/*.md`
  - `outputs/hotel_markdown/Sydney 100/wave5_render_qa_report.csv`

## 6. Downstream Consistency Notes

### What matches the fixed batch

- email, master, clickup a markdown boli pregenerované po novom ranked súbore
- v email/master/clickup outputs sa nenašiel literal `commercial_synthesis/v1`
- markdown summaries tiež neobsahujú literal `commercial_synthesis/v1`

### Important nuance

- email a master exports momentálne nepropagujú nové metadata stĺpce `commercial_source_mode` a `commercial_fallback_used`
- to však nie je dôkaz zlyhania regenerácie; je to aktuálna export contract voľba
- rozhodujúce je, že nový ranked artifact je čistý a downstream chain bola spustená nad ním

## 7. Additional Stability Fix

Počas regenerácie sa ukázal lokálny downstream problém v `src/master_exports.py`:

- triedenie zlyhalo na mixe `float` / `str` v `ranking_score_final`

Bol doplnený malý stabilizačný fix:

- numeric coercion guard pre sort stĺpce pred exportom

Tento fix nemení architektúru, len umožňuje spoľahlivú post-fix regeneráciu master exportov.

## Verdict

- ranking boundary fix bol reálne vykonaný do nového output setu
- nový ranked artifact už nehlási `commercial_synthesis/v1` ako aktívnu schema truth
- downstream chain bola pregenerovaná nad týmto novým batchom
- cleanup ešte stále netreba spúšťať automaticky, ale repo je po tejto verifikácii výrazne bližšie k bezpečnému cleanup kroku
