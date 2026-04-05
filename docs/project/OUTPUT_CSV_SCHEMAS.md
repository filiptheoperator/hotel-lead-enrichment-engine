# OUTPUT CSV SCHEMAS

Potvrdené podľa existujúcich lokálnych artifactov v repozitári k 2026-04-04.

## Scope

Tento dokument uzamyká aktuálny output contract pre:

- `data/processed`
- `outputs/enrichment`
- `outputs/email_drafts`
- `outputs/master`
- `outputs/clickup`
- `data/qa`

Ak niečo nie je potvrdené existujúcim súborom alebo runtime správaním, je to označené ako `Neoverené`.

## data/processed

### Súborový pattern

- `*_normalized_scored.csv`

### Potvrdené stĺpce

1. `hotel_name`
2. `hotel_name_normalized`
3. `review_score`
4. `reviews_count`
5. `street`
6. `city`
7. `state`
8. `country_code`
9. `website`
10. `website_domain`
11. `phone`
12. `category_name`
13. `hotel_type_class`
14. `geography_fit`
15. `independent_chain_class`
16. `ownership_type`
17. `source_url`
18. `all_categories`
19. `source_file`
20. `dedupe_status`
21. `duplicate_group_id`
22. `contact_duplicate_flag`
23. `review_flag`
24. `review_reason`
25. `icp_fit_score`
26. `icp_fit_class`
27. `fit_confidence`
28. `ranking_score`
29. `priority_score`
30. `priority_band`

## outputs/enrichment

### Súborový pattern

- `*_normalized_scored_enriched.csv`

### Potvrdené stĺpce

1. `hotel_name`
2. `hotel_name_normalized`
3. `city`
4. `country_code`
5. `website`
6. `website_domain`
7. `phone`
8. `category_name`
9. `hotel_type_class`
10. `geography_fit`
11. `independent_chain_class`
12. `ownership_type`
13. `direct_booking_weakness`
14. `ota_dependency_signal_label`
15. `all_categories`
16. `review_score`
17. `reviews_count`
18. `dedupe_status`
19. `duplicate_group_id`
20. `contact_duplicate_flag`
21. `review_flag`
22. `review_reason`
23. `icp_fit_score`
24. `icp_fit_class`
25. `fit_confidence`
26. `ranking_score`
27. `priority_score`
28. `priority_band`
29. `hotel_opening_hours`
30. `hotel_opening_hours_status`
31. `hotel_opening_hours_source_url`
32. `hotel_opening_hours_source_type`
33. `checkin_checkout_info`
34. `checkin_checkout_status`
35. `checkin_checkout_source_url`
36. `checkin_checkout_source_type`
37. `checkin_checkout_source_origin`
38. `checkin_checkout_completeness`
39. `public_source_reachable`
40. `public_source_fetch_status`
41. `contact_status`
42. `factual_summary`
43. `give_first_insight`
44. `main_observed_issue`
45. `email_hook`
46. `micro_cta`
47. `primary_email_goal`
48. `proof_snippet`
49. `email_angle`
50. `cta_type`
51. `variant_id`
52. `test_batch`
53. `reply_outcome`
54. `source_url`
55. `source_file`

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
2. `hotel_name_normalized`
3. `city`
4. `country_code`
5. `priority_band`
6. `priority_score`
7. `ranking_score`
8. `icp_fit_score`
9. `icp_fit_class`
10. `fit_confidence`
11. `review_flag`
12. `review_reason`
13. `website`
14. `website_domain`
15. `phone`
16. `contact_status`
17. `hotel_type_class`
18. `geography_fit`
19. `independent_chain_class`
20. `ownership_type`
21. `direct_booking_weakness`
22. `ota_dependency_signal_label`
23. `dedupe_status`
24. `duplicate_group_id`
25. `contact_duplicate_flag`
26. `factual_summary`
27. `subject_line`
28. `hook`
29. `give_first_insight`
30. `main_observed_issue`
31. `email_hook`
32. `micro_cta`
33. `primary_email_goal`
34. `proof_snippet`
35. `email_angle`
36. `cta_type`
37. `variant_id`
38. `test_batch`
39. `reply_outcome`
40. `personalization_line`
41. `give_first_line`
42. `relevance_line`
43. `low_friction_cta`
44. `proof_line`
45. `cold_email`
46. `followup_email`
47. `source_file`

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
5. `Account Status`
6. `Hotel name`
7. `Country`
8. `City / Region`
9. `Hotel Type`
10. `Rooms Range`
11. `City`
12. `Priority score`
13. `Priority Level`
14. `ICP Fit`
15. `OTA Dependency Signal`
16. `Direct Booking Weakness`
17. `Main Pain Hypothesis`
18. `Contact phone`
19. `Contact website`
20. `Subject line`
21. `Source file`
22. `Email angle`
23. `CTA type`
24. `Variant ID`
25. `Test batch`
26. `Reply outcome`
27. `Give-first insight`
28. `Main observed issue`
29. `Email hook`
30. `Micro CTA`
31. `Proof snippet`
32. `Primary email goal`

### Poznámky

- `Task name`, `Description content`, `Status`, `Priority` sú potvrdené ako minimálny importný contract.
- ClickUp export má držať broad lead coverage a radenie `best -> worst`, nie skorý discard.
- Reálna kompatibilita s cieľovým ClickUp workspace ostáva `Neoverené`.
- nové testing a copy polia sú určené pre operator review, reporting a neskoršie meranie reply kvality

## outputs/master

### Súborové patterny

- `*_accounts_master.csv`
- `*_enrichment_master.csv`
- `*_outreach_drafts.csv`
- `*_dedupe_review.csv`

### `accounts_master.csv`

1. `account_id`
2. `record_rank`
3. `source_file`
4. `hotel_name`
5. `hotel_name_normalized`
6. `country_code`
7. `city`
8. `state`
9. `street`
10. `website`
11. `website_domain`
12. `phone`
13. `category_name`
14. `hotel_type_class`
15. `geography_fit`
16. `independent_chain_class`
17. `ownership_type`
18. `review_score`
19. `reviews_count`
20. `icp_fit_score`
21. `icp_fit_class`
22. `fit_confidence`
23. `ranking_score`
24. `priority_score`
25. `priority_band`
26. `dedupe_status`
27. `duplicate_group_id`
28. `contact_duplicate_flag`
29. `review_flag`
30. `review_reason`
31. `source_url`

### `enrichment_master.csv`

1. `account_id`
2. `hotel_name`
3. `country_code`
4. `city`
5. `website`
6. `phone`
7. `hotel_type_class`
8. `independent_chain_class`
9. `direct_booking_weakness`
10. `ota_dependency_signal_label`
11. `hotel_opening_hours`
12. `hotel_opening_hours_status`
13. `hotel_opening_hours_source_url`
14. `checkin_checkout_info`
15. `checkin_checkout_status`
16. `checkin_checkout_source_url`
17. `checkin_checkout_completeness`
18. `public_source_reachable`
19. `public_source_fetch_status`
20. `contact_status`
21. `factual_summary`
22. `give_first_insight`
23. `main_observed_issue`
24. `proof_snippet`
25. `primary_email_goal`
26. `email_angle`
27. `cta_type`
28. `variant_id`
29. `test_batch`
30. `reply_outcome`
31. `review_flag`
32. `review_reason`
33. `source_file`

### `outreach_drafts.csv`

1. `account_id`
2. `hotel_name`
3. `city`
4. `subject_line`
5. `hook`
6. `personalization_line`
7. `give_first_line`
8. `relevance_line`
9. `proof_line`
10. `low_friction_cta`
11. `cold_email`
12. `followup_email`
13. `primary_email_goal`
14. `email_angle`
15. `cta_type`
16. `variant_id`
17. `test_batch`
18. `reply_outcome`
19. `ranking_score`
20. `priority_band`
21. `review_flag`
22. `review_reason`
23. `source_file`

### `dedupe_review.csv`

1. `account_id`
2. `hotel_name`
3. `city`
4. `website_domain`
5. `source_file`
6. `dedupe_status`
7. `duplicate_group_id`
8. `contact_duplicate_flag`
9. `dedupe_type`
10. `match_basis`
11. `merge_recommended`
12. `manual_review_needed`
13. `manual_review_reason`

### Poznámky

- `outputs/master` je nový štruktúrovaný layer nad existujúcou pipeline.
- `accounts_master` drží broad retention a ranking.
- `enrichment_master` drží research a public-source zistenia.
- `outreach_drafts` drží email bloky a drafty.
- `dedupe_review` drží len dedupe-relevantné alebo kontakt-duplicitné prípady.

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
