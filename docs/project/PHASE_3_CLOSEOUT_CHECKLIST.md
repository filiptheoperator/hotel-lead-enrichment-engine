# Phase 3 Closeout Checklist

## Cieľ

Jasne vidieť, čo ešte chýba pred prechodom do integračnej fázy.

## Potvrdené hotové

- operator summary existuje v TXT aj CSV
- ClickUp gate existuje
- batch readiness score existuje
- High-only ClickUp export existuje
- full aj High-only dry run sample existujú
- archive workflow a cleanup pravidlá existujú
- ClickUp API mapping preview a validation existujú

## Ešte chýba pred integračnou fázou

- potvrdiť reálny ClickUp import rehearsal v cieľovom workspace
- potvrdiť finálne custom field mapping IDs
- definovať finálny Go/No-Go threshold pre ostrý import
- uzamknúť retention politiku pre archive storage
- spísať finálny Make execution contract pre ostrý handoff

## Exit signal pre Fázu 3

Fáza 3 je pripravená na uzavretie, keď budú potvrdené:

1. controlled ClickUp rehearsal
2. API payload contract
3. final operator import rules
4. Make handoff payload a error branches
