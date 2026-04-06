# PHASE 1 ENRICHMENT ARCHITECTURE

## Cieľ

Postaviť enrichment vrstvu, ktorá sa čo najviac priblíži starému manuálnemu hotel enrichment template, ale bude:

- automatizovaná
- grounded na verejne dohľadateľných dátach
- použiteľná pre ClickUp
- použiteľná pre outreach
- bezpečná voči vymýšľaniu dát

## Presné zaradenie v pipeline

Finálne odporúčané poradie pre `Phase 1`:

1. `raw lead sheet`
2. `normalize + dedupe + light score`
3. `factual enrichment`
4. `commercial synthesis`
5. `final ranking refresh`
6. `outreach drafts`
7. `master exports`
8. `ClickUp export`
9. `QA / import gate`
10. `live ClickUp write`

## Prečo enrichment patrí sem

Enrichment nesmie ísť až po ClickUpe, lebo:

- ClickUp už potrebuje enrichment-derived polia:
  - `OTA Dependency Signal`
  - `Direct Booking Weakness`
  - `Main Pain Hypothesis`
  - lepší `Hotel Type`
  - lepší `Priority Level`
- outreach drafts tiež potrebujú grounded enrichment
- finálne poradie leadov má byť silnejšie po enrichment vrstve než len po raw score

Zároveň enrichment nemá ísť úplne pred normalize vrstvu, lebo:

- najprv potrebujeme očistiť identity hotelov
- odstrániť duplicity
- získať stabilný `account_id`
- mať light triage score pre budget-aware fetch

## Finálny model rankingu

`Phase 1` má mať 2 scoring momenty:

### 1. Light pre-enrichment score

Použitie:

- základný sort
- batch prioritization
- source-fetch order

Vstupy:

- raw contacts
- web
- kategórie
- review signal
- geo signal

### 2. Final post-enrichment ranking

Použitie:

- finálne poradie v ClickUp
- shortlist
- outreach priorita

Pridáva navyše:

- `OTA Dependency Signal`
- `Direct Booking Weakness`
- `service complexity`
- `contactability`
- `fit confidence`
- `commercial relevance`

## Phase 1 architektúra

### A. Normalize layer

Vstup:

- `data/raw/*.csv`

Úlohy:

- rename raw columns
- normalize text
- normalize phone / website / country
- build `account_id`
- dedupe accounts
- dedupe identical contacts
- compute light pre-enrichment score

Výstup:

- `data/processed/*_normalized_scored.csv`

### B. Source collector

Vstup:

- `account_id`
- `hotel_name`
- `city`
- `country_code`
- `website`

Zdroje:

- Google Places / Place Details API
- oficiálny web hotela
- max 1-3 relevantné subpages

Výstup:

- `source_bundle.json` per hotel

Obsah:

- `google_place_name`
- `formatted_address`
- `website`
- `international_phone`
- `rating`
- `user_rating_count`
- `opening_hours`
- `google_maps_url`
- `official_pages_crawled`
- `fetch_status`

### C. Factual extractor

Pravidlo:

- bez vymýšľania
- len verejne dohľadateľné alebo raw-confirmed dáta
- neoverené explicitne označiť

Extrahované bloky:

- základná identita hotela
- kontakty
- adresa
- operating hours
- check-in / check-out
- room count signal
- service mix:
  - wellness
  - restaurant
  - event / congress
  - spa
  - parking
  - bowling
- review trust signal
- ownership / company signal, ak verejne dohľadateľný

Výstup:

- `factual_enrichment.json`

### D. Commercial synthesizer

Technológia:

- OpenAI API / structured output

Vstupy:

- processed row
- `source_bundle.json`
- `factual_enrichment.json`

Generuje:

- `business_interest_summary`
- `strengths`
- `opportunity_gaps`
- `main_bottleneck_hypothesis`
- `pain_point_hypothesis`
- `personalization_angles`
- `recommended_hook`
- `call_hypothesis`
- `verdict`

Pravidlá:

- Slovak only
- grounded only
- uncertain -> explicitne označiť

### E. Final ranking refresh

Po enrichment vrstve sa dopočíta:

- `ranking_score_final`
- `priority_level_final`
- `rank_bucket`
- `ranking_reason`

Tu sa už používajú aj enrichment-derived signály.

### F. Outreach writer

Vstupy:

- factual block
- commercial synthesis
- final ranking context

Výstup:

- `subject_line`
- `personalization_line`
- `give_first_line`
- `relevance_line`
- `proof_line`
- `low_friction_cta`
- `cold_email`
- `followup_email`

### G. ClickUp layer

Do ClickUpu ide len krátka account vrstva:

- `Account Status`
- `Hotel name`
- `Country`
- `City / Region`
- `Hotel Type`
- `Rooms Range`
- `Contact website`
- `Source`
- `Priority score`
- `Priority Level`
- `ICP Fit`
- `OTA Dependency Signal`
- `Direct Booking Weakness`
- `Main Pain Hypothesis`
- `Subject line`
- `Source file`

Dlhé enrichment texty ostávajú mimo ClickUp.

## Mapovanie starého manuálneho template do Phase 1

### Do factual enrichment

- základný profil hotela
- kontaktné údaje
- prevádzkové hodiny
- check-in / check-out
- room count poznámka
- review trust signal

### Do commercial synthesis

- čo je obchodne zaujímavé
- čo je silné
- kde je priestor
- bottleneck hypothesis
- pain hypothesis
- verdict

### Do outreach layer

- personalizačné uhly
- odporúčaný háčik
- prvý e-mail
- follow-up
- krátka call hypotéza

### Do ClickUp

- len stručný account summary
- nie full markdown enrichment

## Presné Phase 1 output vrstvy

### 1. `accounts_master.csv`

1 riadok = 1 hotel/account

Drží:

- identity
- final ranking
- ClickUp summary fields

### 2. `enrichment_master.csv`

1 riadok = 1 hotel/account

Drží:

- factual enrichment
- commercial synthesis
- research notes

### 3. `outreach_drafts.csv`

1 riadok = 1 hotel/account

Drží:

- outreach copy blocks
- email drafts
- CTA logic

### 4. `dedupe_review.csv`

Drží:

- duplicate groups
- merge candidates
- contact duplicate review

## Čo je ešte mimo aktuálneho hotového stavu

Aktuálne už máme:

- normalize
- dedupe
- light ranking
- basic public web enrichment
- short outreach drafting
- ClickUp export/write

Chýba dokončiť:

1. `Google Places factual collector`
2. `source_bundle per hotel`
3. `room-count / star-rating stronger extraction`
4. `commercial synthesis podľa starého template`
5. `post-enrichment ranking refresh`
6. `full markdown enrichment renderer`

## Najkratší implementačný plán

### Wave 1

- pridať `source_bundle` vrstvu
- napojiť Google Places API
- ukladať raw factual evidence

### Wave 2

- rozšíriť `enrich_hotels.py` na factual extractor
- doplniť:
  - contacts
  - opening hours
  - room signal
  - service mix
  - review signal

### Wave 3

- pridať `commercial_synthesizer.py`
- structured output podľa starého template

### Wave 4

- pridať `ranking_refresh.py`
- prepísať finálne poradie leadov po enrichmente

### Wave 5

- pridať `render_full_enrichment_md.py`
- generovať 1 `.md` enrichment per hotel

## Odporúčanie

Pre `Phase 1`:

- core logika v Pythone
- factual sourcing z Google Places + official web
- synthesis cez OpenAI API
- Make len ako orchestration wrapper, nie ako enrichment engine

To je najkratšia cesta k výstupu, ktorý sa čo najviac podobá starému manuálnemu enrichmentu, ale je škálovateľný.
