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

1. `account_id`
2. `hotel_name`
3. `hotel_name_normalized`
4. `review_score`
5. `reviews_count`
6. `street`
7. `city`
8. `state`
9. `country_code`
10. `website`
11. `website_domain`
12. `phone`
13. `category_name`
14. `hotel_type_class`
15. `geography_fit`
16. `independent_chain_class`
17. `ownership_type`
18. `source_url`
19. `all_categories`
20. `source_file`
21. `dedupe_status`
22. `duplicate_group_id`
23. `contact_duplicate_flag`
24. `review_flag`
25. `review_reason`
26. `icp_fit_score`
27. `icp_fit_class`
28. `fit_confidence`
29. `ranking_reason`
30. `ranking_score`
31. `priority_score`
32. `priority_band`
33. `manual_merge_candidate`
34. `active_icp_profile`

## outputs/enrichment

### Súborový pattern

- `*_normalized_scored_enriched.csv`

### Potvrdené stĺpce

1. `account_id`
2. `hotel_name`
3. `hotel_name_normalized`
4. `city`
5. `country_code`
6. `website`
7. `website_domain`
8. `phone`
9. `category_name`
10. `hotel_type_class`
11. `geography_fit`
12. `independent_chain_class`
13. `ownership_type`
14. `direct_booking_weakness`
15. `ota_dependency_signal_label`
16. `all_categories`
17. `review_score`
18. `reviews_count`
19. `dedupe_status`
20. `duplicate_group_id`
21. `contact_duplicate_flag`
22. `review_flag`
23. `review_reason`
24. `icp_fit_score`
25. `icp_fit_class`
26. `fit_confidence`
27. `ranking_reason`
28. `ranking_score`
29. `priority_score`
30. `priority_band`
31. `manual_merge_candidate`
32. `active_icp_profile`
33. `hotel_opening_hours`
34. `hotel_opening_hours_status`
35. `hotel_opening_hours_source_url`
36. `hotel_opening_hours_source_type`
37. `checkin_checkout_info`
38. `checkin_checkout_status`
39. `checkin_checkout_source_url`
40. `checkin_checkout_source_type`
41. `checkin_checkout_source_origin`
42. `checkin_checkout_completeness`
43. `public_source_reachable`
44. `public_source_fetch_status`
45. `contact_status`
46. `factual_summary`
47. `give_first_insight`
48. `main_observed_issue`
49. `email_hook`
50. `micro_cta`
51. `primary_email_goal`
52. `proof_snippet`
53. `email_angle`
54. `cta_type`
55. `variant_id`
56. `test_batch`
57. `reply_outcome`
58. `source_url`
59. `source_file`

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

1. `account_id`
2. `hotel_name`
3. `hotel_name_normalized`
4. `city`
5. `country_code`
6. `priority_band`
7. `priority_score`
8. `ranking_score`
9. `icp_fit_score`
10. `icp_fit_class`
11. `fit_confidence`
12. `ranking_reason`
13. `review_flag`
14. `review_reason`
15. `website`
16. `website_domain`
17. `phone`
18. `contact_status`
19. `hotel_type_class`
20. `geography_fit`
21. `independent_chain_class`
22. `ownership_type`
23. `direct_booking_weakness`
24. `ota_dependency_signal_label`
25. `dedupe_status`
26. `duplicate_group_id`
27. `contact_duplicate_flag`
28. `manual_merge_candidate`
29. `active_icp_profile`
30. `factual_summary`
31. `subject_line`
32. `hook`
33. `give_first_insight`
34. `main_observed_issue`
35. `email_hook`
36. `micro_cta`
37. `primary_email_goal`
38. `proof_snippet`
39. `email_angle`
40. `cta_type`
41. `variant_id`
42. `test_batch`
43. `reply_outcome`
44. `personalization_line`
45. `give_first_line`
46. `relevance_line`
47. `low_friction_cta`
48. `proof_line`
49. `cold_email`
50. `followup_email`
51. `source_file`

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
6. `Account ID`
7. `Hotel name`
8. `Country`
9. `City / Region`
10. `Hotel Type`
11. `Rooms Range`
12. `City`
13. `Priority score`
14. `Priority Level`
15. `ICP Fit`
16. `Ranking reason`
17. `OTA Dependency Signal`
18. `Direct Booking Weakness`
19. `Main Pain Hypothesis`
20. `Contact phone`
21. `Contact website`
22. `Subject line`
23. `Source file`
24. `Email angle`
25. `CTA type`
26. `Variant ID`
27. `Test batch`
28. `Reply outcome`
29. `Give-first insight`
30. `Main observed issue`
31. `Email hook`
32. `Micro CTA`
33. `Proof snippet`
34. `Primary email goal`

### Poznámky

- `Task name`, `Description content`, `Status`, `Priority` sú potvrdené ako minimálny importný contract.
- ClickUp export má držať broad lead coverage a radenie `best -> worst`, nie skorý discard.
- Reálna kompatibilita s cieľovým ClickUp workspace ostáva `Neoverené`.
- nové testing a copy polia sú určené pre operator review, reporting a neskoršie meranie reply kvality
- doplnkové exporty:
  - `*_clickup_phase1_minimal.csv`
  - `*_clickup_full_ranked.csv`

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
23. `ranking_reason`
24. `ranking_score`
25. `priority_score`
26. `priority_band`
27. `dedupe_status`
28. `duplicate_group_id`
29. `contact_duplicate_flag`
30. `review_flag`
31. `review_reason`
32. `manual_merge_candidate`
33. `source_url`

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
33. `active_icp_profile`
34. `source_file`

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
21. `ranking_reason`
22. `review_flag`
23. `review_reason`
24. `active_icp_profile`
25. `source_file`

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
12. `manual_merge_candidate`
13. `manual_review_needed`
14. `manual_review_reason`

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
