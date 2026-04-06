# GitHub Backup SOP

## Účel
Tento SOP chráni projekt pred stratou práce.

## Kedy commitovať
Commit sprav po každej väčšej fáze:
- po vytvorení repo štruktúry,
- po pridaní configov,
- po dokončení raw ingest,
- po dokončení normalize vrstvy,
- po dokončení enrichment engine kroku,
- po dokončení email compose kroku,
- po dokončení ClickUp export vrstvy.

## Kedy pushovať
Push sprav:
- po každom zmysluplnom commite,
- pred väčšou zmenou,
- po úspešnom testovaní kroku.

## Commit message formát
Používaj krátke správy:
- `init repo structure`
- `add config files`
- `build raw ingest`
- `add scoring pipeline`
- `build enrichment outputs`
- `add clickup export layer`

## Minimum GitHub disciplíny
Po každom väčšom kroku:
1. `git status`
2. `git add .`
3. `git commit -m "kratka sprava"`
4. `git push`

## Rule for assistant
Keď je dokončená väčšia fáza, pripomeň GitHub commit a push.
