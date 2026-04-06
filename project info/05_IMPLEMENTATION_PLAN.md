# Implementation Plan

## Fáza 1 — Repo a základ
Cieľ:
- založiť repo,
- nastaviť priečinky,
- pripraviť config,
- pripraviť env.

Výstup:
- stabilný projektový základ.

## Fáza 2 — Raw ingest
Cieľ:
- vedieť načítať raw CSV export z Apify,
- uložiť ho do správneho priečinka,
- pripraviť loader.

Výstup:
- spoľahlivý vstupný bod.

## Fáza 3 — Normalize and rank
Cieľ:
- premeniť raw dáta na konzistentný account dataset,
- dedupe,
- score,
- priority.

Výstup:
- `accounts_ranked.csv`

## Fáza 4 — Enrichment engine v1
Cieľ:
- na top N hoteloch robiť enrichment do štruktúrovaného výstupu.

Výstup:
- `hotel_enrichment_master.csv`
- `outputs/hotel_markdown/*.md`

## Fáza 5 — Email compose system
Cieľ:
- zo structured enrichmentu vytvoriť email blocks a drafty.

Výstup:
- `email_drafts.csv`

## Fáza 6 — CRM sync layer
Cieľ:
- vytvoriť import-ready exporty pre ClickUp.

Výstup:
- `clickup_import_accounts.csv`
- `clickup_import_contacts.csv`
- `clickup_import_outbound.csv`

## Fáza 7 — QA and review
Cieľ:
- overiť kvalitu dát,
- overiť kvalitu enrichmentu,
- overiť kvalitu personalizácie.

Výstup:
- review checklist,
- manual QA gate.

## Fáza 8 — Automation wiring
Cieľ:
- prepojiť kroky do jedného workflowu,
- neskôr prípadne schedule cez Make.

Výstup:
- single-run workflow.

## Pravidlo poradia
Nepreskakovať poradie.
Najprv základ, potom enrichment, potom CRM sync, potom orchestration.
