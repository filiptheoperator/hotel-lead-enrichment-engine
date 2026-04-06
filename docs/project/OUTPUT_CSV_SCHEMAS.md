# OUTPUT CSV SCHEMAS

Potvrdené podľa existujúcich lokálnych artifactov v repozitári k 2026-04-04.

## Scope

Tento dokument uzamyká aktuálny output contract pre:

- `data/processed`
- `outputs/enrichment`
- `outputs/ranked`
- `outputs/email_drafts`
- `outputs/master`
- `outputs/clickup`
- `outputs/hotel_markdown`
- `data/qa`

Ak niečo nie je potvrdené existujúcim súborom alebo runtime správaním, je to označené ako `Neoverené`.

## outputs/source_bundles

### Súborový pattern

- `outputs/source_bundles/<source_file_stem>/<account_id>.json`

### Účel

- 1 hotel = 1 `source_bundle`
- drží source-of-truth pre factual enrichment mimo CSV vrstvy
- oddeľuje `zdrojové dôkazy` od `vyťažených factual polí`
- pripravuje miesto pre neskorší `Google Places` input bez zmeny CSV contractu

### Minimálny JSON contract

- `schema_version`
- `generated_at_utc`
- `account_id`
- `source_file`
- `hotel_identity`
- `raw_contact_hints`
- `sources.google_places.status`
- `sources.google_places.place_id`
- `sources.google_places.google_maps_url`
- `sources.google_places.fields_requested[]`
- `sources.google_places.result`
- `sources.official_website.base_url`
- `sources.official_website.fetch_status`
- `sources.official_website.reachable`
- `sources.official_website.pages[]`
- `extracted_candidates.hotel_opening_hours`
- `extracted_candidates.checkin_checkout`
- `extracted_candidates.ownership_company`

### `sources.official_website.pages[]`

- `url`
- `source_type`
- `jsonld_detected`
- `text_length`
- `opening_hours_candidate`
- `opening_hours_origin`
- `opening_hours_valid`
- `checkin_checkout_candidate`
- `checkin_checkout_origin`
- `checkin_checkout_valid`

### Poznámky

- `google_places` je optional collector na `Places API (New)`; bez enable flagu alebo API key ostáva explicitne `not_enabled` / `not_configured`.
- CSV enrichment zatiaľ ostáva backward-compatible; `source_bundle` je side artifact.
- extractor má v ďalšom kroku čítať primárne z `source_bundle`, nie znova fetchovať HTML logiku ad hoc.

## outputs/factual_enrichment

### Súborový pattern

- `outputs/factual_enrichment/<source_file_stem>/<account_id>.json`

### Účel

- strojovo čitateľný factual block per hotel
- číta primárne z `source_bundle` + `processed row`
- drží len grounded alebo raw-confirmed údaje

### Minimálny JSON contract

- `schema_version`
- `generated_at_utc`
- `account_id`
- `source_file`
- `source_bundle_ref`
- `identity`
- `contacts`
- `address`
- `operating_hours`
- `checkin_checkout`
- `room_count_signal`
- `service_mix`
- `review_trust_signal`
- `google_review_signal`
- `ownership_company_signal`
- `source_reachability`

### Poznámky

- `room_count_signal` je zatiaľ len `processed-row` signal alebo explicitne `verejne nepotvrdené`.
- `service_mix` je v tejto verzii minimálny heuristic layer z raw kategórií a web URL markerov.
- `service_mix` vie byť zosilnený cez Google Places `types` a `primaryType`, ak sú dostupné.
- `google_review_signal` a časť identity/contact/address sa doplní len ak `sources.google_places.status = ok`.
- `ownership_company_signal` preferuje official web JSON-LD kandidáta pred raw ownership labelom.
- tento artifact je pripravený ako vstup pre neskorší `commercial_synthesizer`.

## outputs/commercial_synthesis

### Súborový pattern

- `outputs/commercial_synthesis/<source_file_stem>/<account_id>.json`

### Účel

- structured-first commercial layer nad `processed row` + `source_bundle` + `factual_enrichment`
- canonical Wave 3 output layer pre commercial reasoning
- grounded-only, s explicitným uncertainty outputom
- heuristický `v1` ostáva už len ako fallback / legacy

### Minimálny JSON contract

- `schema_version`
- `generated_at_utc`
- `account_id`
- `source_file`
- `source_bundle_ref`
- `factual_enrichment_ref`
- `business_interest_summary`
- `why_commercially_interesting`
- `property_positioning_summary`
- `strengths[]`
- `opportunity_gaps[]`
- `main_bottleneck_hypothesis`
- `pain_point_hypothesis`
- `best_entry_angle`
- `personalization_angles[]`
- `recommended_hook`
- `recommended_first_contact_route`
- `likely_decision_maker_hypothesis`
- `demand_mix_hypothesis[]`
- `service_complexity_read`
- `commercial_complexity_read`
- `direct_booking_friction_hypothesis`
- `contact_route_friction_hypothesis`
- `call_hypothesis`
- `verdict`
- `uncertainty_notes[]`

### Poznámky

- canonical verzia je `commercial_synthesis/v3-lite`.
- `commercial_synthesis/v1` je legacy fallback a nemá sa ďalej rozširovať.
- LLM vstup je compact grounded view nad `processed row` + `source_bundle` + `factual_enrichment`.
- finálny style contract pre `v3-lite`:
  - `business_interest_summary`: max 1 veta
  - `why_commercially_interesting`: max 2 vety
  - `property_positioning_summary`: max 1 veta
  - `best_entry_angle`: max 1 veta
  - `recommended_hook`: max 1 veta
  - `main_bottleneck_hypothesis`: max 1 veta, sales-practical
  - `pain_point_hypothesis`: max 1 veta
- `recommended_first_contact_route` a `likely_decision_maker_hypothesis` majú byť krátke, praktické a explicitne opatrné.
- generic sales fluff sa má pri `v2` odfiltrovať.
- verdict ostáva striktne len `silný prospect` / `zaujímavý prospect` / `opatrný prospect`.
- pri API/quota blockeri môže v outputs ešte dočasne ostať starší heuristický artifact.

## outputs/ranked

### Súborový pattern

- `outputs/ranked/<enrichment_stem>_ranking_refreshed*.csv`

### Účel

- samostatná post-enrichment ranking refresh vrstva
- používa `commercial_synthesis` + factual confidence namiesto inline logiky v `master_exports.py`
- canonical Wave 4 decision engine
- rozhoduje `outreach_now` / `manual_review` / `hold_later`

### Minimálne finálne polia

- `commercial_bonus`
- `factual_completeness_score`
- `ranking_score_final`
- `priority_level_final`
- `rank_bucket_final`
- `ranking_refresh_reason`
- `ranking_upside_reasons`
- `ranking_downside_reasons`
- `ranking_missingness_notes`
- `uncertainty_penalty`
- `decision_status`
- `manual_review_needed`
- `review_queue_reason_codes`
- `outreach_ready`
- `shortlist_candidate`

### Scoring policy contract

- scoring sa má čítať z `configs/ranking_tuning.yaml`
- explicitné skupiny váh:
  - `weights.commercial_verdict`
  - `weights.ownership_confidence`
  - `weights.factual_completeness`
  - `weights.review_strength`
  - `weights.missingness_penalties`
  - `weights.uncertainty_penalties`
- explicitné thresholdy:
  - `thresholds.priority_levels`
  - `thresholds.rank_buckets`
  - `thresholds.review_score_strong_min`
  - `thresholds.review_score_weak_max`
- shortlist policy:
  - `shortlist.operator_shortlist_priority_levels`
  - `shortlist.operator_shortlist_limit`
  - `shortlist.top_export_limit`
- review queue policy:
  - `review_queue.low_factual_completeness_max`
  - `review_queue.weak_ownership_statuses`
  - `review_queue.review_queue_limit`

## outputs/hotel_markdown

### Súborový pattern

- `outputs/hotel_markdown/<source_file_stem>/<account_id>.md`
- `outputs/hotel_markdown/<source_file_stem>/operator_shortlist_summary.md`
- `outputs/hotel_markdown/<source_file_stem>/review_queue_summary.md`
- `outputs/hotel_markdown/<source_file_stem>/top_export_summary.md`
- `outputs/hotel_markdown/<source_file_stem>/wave5_render_qa_report.csv`

### Účel

- Wave 5 renderer
- 1 hotel = 1 markdown summary
- renderuje len z existujúcich structured artifactov a ranked vrstvy
- canonical final operator presentation layer
- renderer nesmie robiť nové inferencie; len skladá už existujúce structured fields

### Canonical renderer input

- `outputs/source_bundles/<source_file_stem>/<account_id>.json`
- `outputs/factual_enrichment/<source_file_stem>/<account_id>.json`
- `outputs/commercial_synthesis/<source_file_stem>/<account_id>.json`
- `outputs/ranked/<enrichment_stem>_ranking_refreshed*.csv`
- optional: `outputs/email_drafts/*_email_drafts.csv`

### Per-hotel section schema

- `Header`
- `operator_brief`:
  - `Executive Summary`
  - `Decision Block`
  - `Factual Block`
  - `Evidence Block`
  - `Uncertainty Block`
  - `Outreach Block`
  - `Operator Action Block`
- `old_template_full`:
  - `Základný profil hotela`
  - `Kontaktné údaje`
  - `Prevádzkové hodiny a dôležité časy`
  - `Čo je na hoteli obchodne zaujímavé`
  - `Dôvera a recenzie`
  - `Rýchle zhodnotenie`
  - `Personalizačné uhly`
  - `Odporúčaný háčik`
  - `Návrh prvého e-mailu`
  - `Návrh následného e-mailu`
  - `Hypotéza na krátky úvodný rozhovor`
  - `Verdikt`
  - `Neistoty a čo treba overiť`

### Rendering rules

- section order musí byť fixný a diff-friendly
- renderer má explicitne označovať:
  - `Overené vo verejnom zdroji`
  - `raw_confirmed`
  - `Verejne nepotvrdené`
- prázdne alebo noisy fields sa nemajú umelo nafukovať
- uncertainty block musí byť oddelený od factual blocku
- dlhé texty sa majú skracovať, nie prepisovať

### Mandatory vs optional fields

- mandatory pre per-hotel render:
  - `account_id`
  - `hotel_name`
  - `city`
  - `country_code`
  - `priority_level_final`
  - `decision_status`
  - `ranking_score_final`
  - `ranking_refresh_reason`
  - `commercial.verdict`
  - `commercial.business_interest_summary`
  - `commercial.main_bottleneck_hypothesis`
- optional:
  - `email_drafts` block
  - `source URLs`
  - `uncertainty notes`
  - `review queue reasons`
  - `service mix` evidence detail

### Batch modes

- `single`
- `batch`
- `shortlist`
- `review_queue`
- `top_export`
- `all`

### Template modes

- `MARKDOWN_TEMPLATE=operator_brief`
- `MARKDOWN_TEMPLATE=old_template_full`

### Poznámky

- `operator_shortlist_summary.md` má renderovať len `decision_status = outreach_now`
- `review_queue_summary.md` má renderovať len `decision_status = manual_review`
- `top_export_summary.md` je lightweight executive pack
- `wave5_render_qa_report.csv` je malý QA artifact pre renderer stabilitu a readability
- `old_template_full` má byť bohatší presentation mode, ale stále len render nad structured artifactmi

## outputs/master

### Wave 4 relevant exports

- `*_accounts_master*.csv`
- `*_operator_shortlist*.csv`
- `*_review_queue*.csv`
- `*_top_20_export*.csv`

### Poznámky

- `operator_shortlist` je primary operator view pre `outreach_now`
- `review_queue` je primary operator view pre `manual_review`
- `top_20_export` ostáva lightweight export view

## Wave 4 Run Order

- `python3 src/commercial_synthesizer.py`
- `python3 src/ranking_refresh.py`
- `python3 src/email_drafts.py`
- `python3 src/master_exports.py`
- `python3 src/clickup_export.py`

## Wave 5 Run Order

- `python3 src/commercial_synthesizer.py`
- `python3 src/ranking_refresh.py`
- `python3 src/email_drafts.py`
- `python3 src/master_exports.py`
- `python3 src/render_full_enrichment_md.py`

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
28. `non_icp_but_keep`
29. `fit_confidence`
30. `confidence_reason`
31. `review_bucket`
32. `owner_gm_decision_cycle_signal`
33. `contact_discovery_likelihood`
34. `ota_visibility_signal`
35. `ranking_reason`
36. `ranking_score`
37. `priority_score`
38. `priority_band`
39. `manual_merge_candidate`
40. `active_icp_profile`

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
26. `non_icp_but_keep`
27. `fit_confidence`
28. `confidence_reason`
29. `review_bucket`
30. `owner_gm_decision_cycle_signal`
31. `contact_discovery_likelihood`
32. `ota_visibility_signal`
33. `rooms_range`
34. `room_count_value`
35. `room_count_status`
36. `ranking_reason`
37. `ranking_score`
38. `priority_score`
39. `priority_band`
40. `manual_merge_candidate`
41. `active_icp_profile`
42. `hotel_opening_hours`
43. `hotel_opening_hours_status`
44. `hotel_opening_hours_source_url`
45. `hotel_opening_hours_source_type`
46. `checkin_checkout_info`
47. `checkin_checkout_status`
48. `checkin_checkout_source_url`
49. `checkin_checkout_source_type`
50. `checkin_checkout_source_origin`
51. `checkin_checkout_completeness`
52. `public_source_reachable`
53. `public_source_fetch_status`
54. `contact_status`
55. `factual_summary`
56. `business_interest_summary`
57. `main_bottleneck_hypothesis`
58. `pain_point_hypothesis`
59. `recommended_hook`
60. `commercial_verdict`
61. `give_first_insight`
62. `main_observed_issue`
63. `email_hook`
64. `micro_cta`
65. `primary_email_goal`
66. `proof_snippet`
67. `email_angle`
68. `cta_type`
69. `variant_id`
70. `test_batch`
71. `reply_outcome`
72. `source_url`
73. `source_file`

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
11. `non_icp_but_keep`
12. `fit_confidence`
13. `confidence_reason`
14. `review_bucket`
15. `owner_gm_decision_cycle_signal`
16. `contact_discovery_likelihood`
17. `ota_visibility_signal`
18. `ranking_reason`
19. `review_flag`
20. `review_reason`
21. `website`
22. `website_domain`
23. `phone`
24. `contact_status`
25. `hotel_type_class`
26. `geography_fit`
27. `independent_chain_class`
28. `ownership_type`
29. `direct_booking_weakness`
30. `ota_dependency_signal_label`
31. `dedupe_status`
32. `duplicate_group_id`
33. `contact_duplicate_flag`
34. `manual_merge_candidate`
35. `active_icp_profile`
36. `factual_summary`
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

- pri `clickup_export_mode: phase1_minimal` je minimálny contract:
  - `Task name`
  - `Status`
  - `Priority`
- `Description content` ostáva povinný len pre `full_ranked`
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
- `*_operator_shortlist.csv`
- `*_top_20_export.csv`

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
22. `non_icp_but_keep`
23. `fit_confidence`
24. `confidence_reason`
25. `review_bucket`
26. `owner_gm_decision_cycle_signal`
27. `contact_discovery_likelihood`
28. `ota_visibility_signal`
29. `website_quality`
30. `chain_signal_confidence`
31. `contact_gap_reason`
32. `contact_gap_count`
33. `why_not_top_tier`
34. `rank_bucket`
35. `rank_bucket_reason`
36. `ranking_reason`
37. `ranking_score`
38. `priority_score`
39. `priority_band`
40. `dedupe_status`
41. `duplicate_group_id`
42. `contact_duplicate_flag`
43. `review_flag`
44. `review_reason`
45. `manual_merge_candidate`
46. `source_url`

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
31. `website_quality`
32. `chain_signal_confidence`
33. `contact_gap_reason`
34. `contact_gap_count`
35. `why_not_top_tier`
36. `rank_bucket`
37. `rank_bucket_reason`
38. `review_flag`
39. `review_reason`
40. `active_icp_profile`
41. `source_file`

### `operator_shortlist.csv`

1. `account_id`
2. `record_rank`
3. `source_file`
4. `hotel_name`
5. `country_code`
6. `city`
7. `priority_score`
8. `priority_band`
9. `review_bucket`
10. `rank_bucket`
11. `ranking_reason`
12. `shortlist_reason`
13. `rank_bucket_reason`
14. `review_flag`
15. `review_reason`

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
21. `why_not_top_tier`
22. `rank_bucket`
23. `rank_bucket_reason`
24. `ranking_reason`
25. `review_flag`
26. `review_reason`
27. `active_icp_profile`
28. `source_file`

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
13. `account_merge_notes`
14. `manual_review_needed`
15. `manual_review_reason`

### Poznámky

- `outputs/master` je nový štruktúrovaný layer nad existujúcou pipeline.
- `accounts_master` drží broad retention a ranking.
- `enrichment_master` drží research a public-source zistenia.
- `outreach_drafts` drží email bloky a drafty.
- `dedupe_review` drží len dedupe-relevantné alebo kontakt-duplicitné prípady.
- `operator_shortlist` drží prvý operator-ready výber bez mazania zvyšku datasetu.
- `top_20_export` je len pracovný top slice, nie discard vrstva.

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
