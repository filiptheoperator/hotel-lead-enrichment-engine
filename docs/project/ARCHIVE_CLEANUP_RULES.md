# Archive Cleanup Rules

## Cieľ

Nedovoliť, aby sa `data/archive` kopilo bez limitu.

## Aktuálne pravidlo

- držať posledných `5` batch archívov

## Runtime artifact

- [data/qa/archive_cleanup_report.txt](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/archive_cleanup_report.txt)

## Správanie

- cleanup beží po archive kroku
- odstraňuje najstaršie archive directory nad limit
- nezasahuje do `data/raw`
- nezasahuje do aktuálnych live artifactov v `data/qa`, `outputs/`, `data/processed`

## Neoverené

- budúca retention politika pre remote storage
- budúce odlišné pravidlá pre produkčné vs test batchy
