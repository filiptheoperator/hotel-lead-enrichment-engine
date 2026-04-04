# OUTPUT CSV SCHEMAS

Potvrdené podľa existujúcich lokálnych artifactov v repozitári k 2026-04-04.

## Scope

Tento dokument uzamyká aktuálny output contract pre:

- `data/processed`
- `outputs/enrichment`
- `outputs/email_drafts`
- `outputs/clickup`
- `data/qa`

Ak niečo nie je potvrdené existujúcim súborom alebo runtime správaním, je to označené ako `Neoverené`.

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
14. `hotel_opening_hours_source_url`
15. `hotel_opening_hours_source_type`
16. `checkin_checkout_info`
17. `checkin_checkout_status`
18. `checkin_checkout_source_url`
19. `checkin_checkout_source_type`
20. `checkin_checkout_source_origin`
21. `checkin_checkout_completeness`
22. `public_source_reachable`
23. `public_source_fetch_status`
24. `contact_status`
25. `factual_summary`
26. `give_first_insight`
27. `main_observed_issue`
28. `email_hook`
29. `micro_cta`
30. `primary_email_goal`
31. `proof_snippet`
32. `email_angle`
33. `cta_type`
34. `variant_id`
35. `test_batch`
36. `reply_outcome`
37. `source_url`
38. `source_file`

### Poznámky

- `hotel_opening_hours_status` a `checkin_checkout_status` držia explicitné označenie overenia.
- `public_source_fetch_status` odlišuje live fetch, fallback a fetch incident.
- `checkin_checkout_source_origin` je dnes potvrdené ako `text`, `jsonld`, `raw_input` alebo prázdne.
- `checkin_checkout_completeness` je dnes potvrdené ako `paired`, `single_side`, `none`.
- nové outreach polia slúžia len na krátke copy-ready bloky, nie na vymýšľanie neoverených tvrdení
- `reply_outcome` je tracking pole a pri prvom exporte môže zostať prázdne

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
11. `give_first_insight`
12. `main_observed_issue`
13. `email_hook`
14. `micro_cta`
15. `primary_email_goal`
16. `proof_snippet`
17. `email_angle`
18. `cta_type`
19. `variant_id`
20. `test_batch`
21. `reply_outcome`
22. `personalization_line`
23. `give_first_line`
24. `relevance_line`
25. `low_friction_cta`
26. `proof_line`
27. `cold_email`
28. `followup_email`
29. `source_file`

### Poznámky

- email drafting používa blokový systém `personalization_line -> give_first_line -> relevance_line -> low_friction_cta`
- `proof_line` je voliteľný a má byť prázdny, ak nemáme krátky grounded proof
- jeden email má mať len jeden cieľ a jeden CTA krok

## outputs/clickup

### Súborový pattern

- `*_normalized_scored_enriched_email_drafts_clickup_import.csv`

### Potvrdené stĺpce

1. `Task name`
2. `Description content`
3. `Status`
4. `Priority`
5. `Hotel name`
6. `City`
7. `Priority score`
8. `Contact phone`
9. `Contact website`
10. `Subject line`
11. `Source file`
12. `Email angle`
13. `CTA type`
14. `Variant ID`
15. `Test batch`
16. `Reply outcome`
17. `Give-first insight`
18. `Main observed issue`
19. `Email hook`
20. `Micro CTA`
21. `Proof snippet`
22. `Primary email goal`

### Poznámky

- `Task name`, `Description content`, `Status`, `Priority` sú potvrdené ako minimálny importný contract.
- Reálna kompatibilita s cieľovým ClickUp workspace ostáva `Neoverené`.
- nové testing a copy polia sú určené pre operator review, reporting a neskoršie meranie reply kvality

## data/qa

### `qa_issues.csv`

#### Potvrdené stĺpce

1. `issue_type`
2. `severity`
3. `blocking`
4. `hotel_name`
5. `city`
6. `priority_band`
7. `details`
8. `source_file`

### `manual_review_shortlist.csv`

#### Potvrdené stĺpce

1. `hotel_name`
2. `city`
3. `priority_band`
4. `priority_score`
5. `review_bucket`
6. `operator_triage_priority`
7. `operator_triage_action`
8. `hotel_opening_hours_status`
9. `checkin_checkout_status`
10. `checkin_checkout_source_origin`
11. `checkin_checkout_completeness`
12. `public_source_reachable`
13. `public_source_fetch_status`
14. `manual_review_reason`
15. `source_file`

### Poznámky

- `review_bucket` je shortlist segmentácia pre review workflow.
- `operator_triage_priority` a `operator_triage_action` sú operátorské odporúčania, nie produkčné CRM statusy.

## Non-CSV runtime artifact

### `data/qa/run_manifest.json`

- Potvrdené runtime artifact pole pre batch-level snapshot.
- Obsahuje:
  - batch source files
  - artifact paths
  - row counts
  - quality snapshot
  - fetch health
  - shortlist snapshot
  - import snapshot

### `data/qa/clickup_import_gate.json`

- Potvrdené runtime artifact pole pre ClickUp `Go / No-Go` rozhodnutie.
- Obsahuje:
  - `decision`
  - `operator_action`
  - `inputs`
  - `checks`
  - `stop_conditions`
  - `go_rules`
  - `no_go_rules`

### `data/qa/clickup_import_dry_run_sample.csv`

- Potvrdený suchý importný sample z aktuálneho ClickUp CSV.
- Slúži iba na malý test vzorky, nie na ostrý import.

## Zhrnutie

- Output contract pre hlavné CSV artefakty je uzamknutý podľa aktuálnych reálnych hlavičiek.
- `run_manifest.json` je nový ne-CSV batch artifact pre operátorský workflow.
- ClickUp gate a dry run sample sú nové operátorské artifacty pre importné rozhodovanie.
- Neoverené ostáva len to, čo závisí od externých systémov alebo live siete.
