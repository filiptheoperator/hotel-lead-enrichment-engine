# ClickUp Go / No-Go Rules

## Cieľ

Presne uzamknúť, kedy batch môže a nemôže ísť do ClickUp importu.

## Primárny artifact

- [data/qa/clickup_import_gate.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.json)
- [data/qa/clickup_import_gate.txt](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_import_gate.txt)

## GO

Batch je `GO`, iba ak naraz platí:

1. `fetch_incident_flag = no`
2. `qa_blocking_rows = 0`
3. `clickup_import_ready_rows = clickup_rows`
4. žiadny `High` lead nezostáva v hold alebo manual review stave pred importom

## NO-GO

Batch je `NO_GO`, ak platí aspoň jedno:

1. globálny DNS / fetch incident
2. akýkoľvek blocking QA issue
3. ClickUp CSV nie je úplne import-ready
4. `High` leady ešte čakajú na manual review pred importom

## Operátorský postup

1. otvor `run_manifest.json`
2. otvor `clickup_import_gate.txt`
3. ak je `NO_GO`, neimportovať
4. ak je `GO`, najprv skontrolovať suchý sample
5. až potom robiť ostrý import

## Poznámka

- Neoverené: správanie konkrétneho ClickUp workspace pri reálnom importe.
