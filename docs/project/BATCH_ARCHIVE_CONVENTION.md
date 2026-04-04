# Batch Archive Convention

## Cieľ

Po každom rune uložiť snapshot hlavných artifactov do archívu bez prepisovania raw inputov.

## Archive root

- `data/archive/`

## Názvoslovie batch archívu

- `{source_file_stem}__{generated_at}`

Príklad:

- `raw_bratislava region_2026-04-01_21-01-58-857__2026-04-04__22-30-00_02-00`

## Čo sa archivuje

- processed CSV
- enrichment CSV
- email drafts CSV
- ClickUp import CSV
- QA issues CSV
- manual review shortlist CSV
- run summary TXT
- run delta report TXT
- run manifest JSON
- ClickUp gate JSON/TXT
- ClickUp dry run sample CSV a notes TXT

## Manifest v archíve

Každý archive folder obsahuje:

- `archive_manifest.json`

Ten drží:
- archívny adresár
- skopírované artifacty
- referenciu na source `run_manifest.json`

## Poznámka

- Toto je lokálna archive konvencia.
- Neoverené: budúca retention politika a remote storage.
