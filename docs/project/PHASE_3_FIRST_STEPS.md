# Fáza 3 - Prvých 5 krokov

## Cieľ Fázy 3
Posunúť systém z `stabilized local pipeline` do `operator-ready workflow` bez pridania novej architektúry.

## Prvých 5 krokov
1. Uzamknúť output contract pre enrichment, QA, ClickUp export a run summary.
2. Doplniť jednoduchý operator checklist pre jeden batch run: čo skontrolovať, v akom poradí a podľa ktorých artifactov.
3. Zaviesť run manifest pre batch-level evidenciu vstupu, artefaktov a použitého fallback režimu.
4. Spraviť shortlist triage pravidlá pre `High` leady, aby bolo jasné čo ide hneď do ClickUp a čo čaká na manual review.
5. Pripraviť presný integračný brief pre budúcu ClickUp / Make fázu, ale bez implementácie integrácií.

## Ready-to-start vstupy
- `data/qa/manual_review_shortlist.csv`
- `data/qa/qa_issues.csv`
- `data/qa/run_summary.txt`
- `data/qa/run_delta_report.txt`
- `outputs/clickup/*_clickup_import.csv`

## Definition of Done pre vstup do Fázy 3
- Operátor vie po jednom rune jasne povedať:
  - čo je potvrdené
  - čo je neoverené
  - čo blokuje import
  - čo treba ručne skontrolovať
  - čo je infra incident a nie dátový problém
