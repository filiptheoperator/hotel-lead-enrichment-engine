# OUTPUT CSV SCHEMAS

Potvrdené podľa existujúcich lokálnych CSV súborov v repozitári k 2026-04-04.

## Scope

Tento dokument popisuje aktuálne potvrdené schémy pre:

- `data/processed`
- `outputs/enrichment`
- `outputs/email_drafts`
- `outputs/clickup`
- `data/qa`

Ak niečo nie je potvrdené existujúcim súborom alebo reálnym importom, je to označené ako `Neoverené`.

## data/processed

### Súborový pattern

- `*_normalized_scored.csv`

### Potvrdené stĺpce

1. `hotel_name`
2. `review_score`
3. `reviews_count`
4. `street`
5. `city`
6. `country_code`
7. `website`
8. `phone`
9. `category_name`
10. `source_url`
11. `all_categories`
12. `source_file`
13. `priority_score`
14. `priority_band`

### Stav

- Potvrdené existujúcim súborom:
  - `data/processed/raw_bratislava region_2026-04-01_21-01-58-857_normalized_scored.csv`

## outputs/enrichment

### Súborový pattern

- `*_normalized_scored_enriched.csv`

### Potvrdené stĺpce

1. `hotel_name`
2. `city`
3. `country_code`
4. `website`
5. `phone`
6. `category_name`
7. `all_categories`
8. `review_score`
9. `reviews_count`
10. `priority_score`
11. `priority_band`
12. `hotel_opening_hours`
13. `hotel_opening_hours_status`
14. `checkin_checkout_info`
15. `checkin_checkout_status`
16. `contact_status`
17. `factual_summary`
18. `source_url`
19. `source_file`

### Poznámky

- `hotel_opening_hours` je v aktuálnom výstupe prítomné.
- Verejná dostupnosť a presnosť `hotel_opening_hours` je po riadkoch rôzna a musí zostať explicitne označená stavovým poľom.
- `checkin_checkout_info` je v aktuálnom výstupe factual minimum.

### Stav

- Potvrdené existujúcim súborom:
  - `outputs/enrichment/raw_bratislava region_2026-04-01_21-01-58-857_normalized_scored_enriched.csv`

## outputs/email_drafts

### Súborový pattern

- `*_normalized_scored_enriched_email_drafts.csv`

### Potvrdené stĺpce

1. `hotel_name`
2. `city`
3. `priority_band`
4. `priority_score`
5. `website`
6. `phone`
7. `contact_status`
8. `factual_summary`
9. `subject_line`
10. `hook`
11. `cold_email`
12. `followup_email`
13. `source_file`

### Poznámky

- `cold_email` a `followup_email` sú multiline text polia.
- Schéma potvrdzuje aktuálny safe minimum export, nie kvalitatívny cieľ pre ďalšiu iteráciu.

### Stav

- Potvrdené existujúcim súborom:
  - `outputs/email_drafts/raw_bratislava region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts.csv`

## outputs/clickup

### Súborový pattern

- `*_normalized_scored_enriched_email_drafts_clickup_import.csv`

### Potvrdené stĺpce

1. `task_name`
2. `task_priority`
3. `task_status`
4. `hotel_name`
5. `city`
6. `priority_score`
7. `contact_phone`
8. `contact_website`
9. `subject_line`
10. `task_notes`
11. `source_file`

### Poznámky

- `task_notes` je multiline text pole.
- Táto CSV schéma je potvrdená lokálnym exportom.
- Reálny ClickUp import formát a kompatibilita s ClickUp importrom sú zatiaľ `Neoverené`.

### Stav

- Potvrdené existujúcim súborom:
  - `outputs/clickup/raw_bratislava region_2026-04-01_21-01-58-857_normalized_scored_enriched_email_drafts_clickup_import.csv`

## data/qa

### Súborový pattern

- `qa_issues.csv`

### Potvrdené stĺpce

1. `issue_type`
2. `severity`
3. `hotel_name`
4. `city`
5. `priority_band`
6. `details`
7. `source_file`

### Poznámky

- Aktuálny QA output zachytáva issue-level záznamy.
- Presné blocking vs warning pravidlá pre ďalšiu etapu sú zatiaľ `Neoverené`.

### Stav

- Potvrdené existujúcim súborom:
  - `data/qa/qa_issues.csv`

## Zhrnutie

- Všetkých 5 cieľových CSV schém je aktuálne potvrdených existujúcimi súbormi.
- Neoverené ostáva iba:
  - reálna kompatibilita `outputs/clickup` s ClickUp importom
  - budúce pravidlá pre `blocking` vs `warning` v QA
