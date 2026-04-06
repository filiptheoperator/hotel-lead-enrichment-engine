# PHASE 1 ENRICHMENT THREAD HANDOFF

## Účel

Tento dokument je copy-paste handoff pre nový thread, aby sa dalo hneď pokračovať na `Phase 1 enrichment architecture` bez opakovania celého kontextu.

## Source of truth

Pred začiatkom práce si vždy načítaj:

- [PHASE_1_ENRICHMENT_ARCHITECTURE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md)
- [OUTPUT_CSV_SCHEMAS.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/OUTPUT_CSV_SCHEMAS.md)
- [37 Hotel Magnus Trenčín Enrichment.md](/Users/aios/Library/CloudStorage/GoogleDrive-filip@thehoteloperator.com/My%20Drive/Leads/Owners/Denis/1.%20lead%20sheet/Hotel%20Leads%20Enrichment/37%20Hotel%20Magnus%20Trenc%CC%8Ci%CC%81n%20Enrichment.md)
- [clickup_export.py](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/clickup_export.py)
- [enrich_hotels.py](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/src/enrich_hotels.py)

## Aktuálny stav

Máme hotové:

- raw -> normalize -> dedupe -> light score
- basic public web enrichment
- outreach drafts
- ClickUp export
- live ClickUp write

Máme rozhodnuté:

- enrichment patrí po `normalize + light score`
- final ranking sa má refreshnúť po enrichmente
- ClickUp ostáva jednoduchý
- bohatý enrichment ostáva mimo ClickUp

Otvorené:

1. `source_collector`
2. `source_bundle` per hotel
3. `Google Places factual collector`
4. `commercial_synthesizer`
5. `post-enrichment ranking refresh`
6. `full markdown enrichment renderer`

## Master handoff prompt

Použi tento prompt, ak chceš otvoriť nový thread a pokračovať na enrichment architektúre:

```text
Pokračujeme v projekte Hotel Lead Enrichment Engine OS.

Najprv si načítaj tieto source-of-truth súbory:
- docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md
- docs/project/OUTPUT_CSV_SCHEMAS.md
- src/enrich_hotels.py
- src/clickup_export.py
- /Users/aios/Library/CloudStorage/GoogleDrive-filip@thehoteloperator.com/My Drive/Leads/Owners/Denis/1. lead sheet/Hotel Leads Enrichment/37 Hotel Magnus Trenčín Enrichment.md

Kontext:
- raw -> normalize -> dedupe -> light score -> enrichment -> final ranking -> outreach -> ClickUp
- ClickUp mapping je už final pre Phase 1
- enrichment má byť výrazne bohatší a viac sa podobať starému manuálnemu template
- nechceme vymýšľať dáta
- chceme grounded factual sourcing + LLM synthesis

Tvoja úloha:
1. over aktuálny stav enrichment pipeline
2. pokračuj presne podľa PHASE_1_ENRICHMENT_ARCHITECTURE.md
3. navrhni alebo implementuj ďalší najbližší krok bez zbytočného redesignu
4. drž ClickUp jednoduchý a enrichment rich mimo ClickUp
5. Slovak only
6. short, technical, practical, no fluff
```

## Prompt pre Wave 1

Použi, ak chceš začať `source_collector`:

```text
Pokračuj na Wave 1 v projekte Hotel Lead Enrichment Engine OS.

Najprv si načítaj:
- docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md
- src/enrich_hotels.py
- data/processed/Sydney 100_normalized_scored.csv

Tvoja úloha:
1. navrhni a implementuj minimálny `source_bundle` layer per hotel
2. priprav output contract pre factual sourcing
3. priprav miesto pre Google Places / official web inputs
4. neimplementuj ešte veľký synthesis layer
5. drž scope úzky a praktický

Cieľ:
- 1 hotel = 1 source bundle
- factual evidence uložené oddelene od ClickUp
- pripravené pre ďalší extractor krok

Výstup chcem:
- presné file changes
- output schema
- krátky test na jednom hoteli
```

## Prompt pre Wave 2

Použi, ak chceš rozšíriť factual enrichment:

```text
Pokračuj na Wave 2 v projekte Hotel Lead Enrichment Engine OS.

Najprv si načítaj:
- docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md
- src/enrich_hotels.py
- ak existuje source_bundle vrstva, použi ju ako vstup

Tvoja úloha:
1. rozšír factual enrichment tak, aby sa priblížil starému manuálnemu template
2. extrahuj len grounded facts
3. pokry minimálne:
   - contacts
   - address
   - opening hours
   - check-in / check-out
   - room count signal
   - service mix
   - review signal
4. nechoď ešte do full outreach synthesis

Cieľ:
- enrichment_master má bohatší factual layer
- nič nevymýšľať
- neoverené explicitne označiť
```

## Prompt pre Wave 3

Použi, ak chceš pridať commercial synthesis podľa starého template:

```text
Pokračuj na Wave 3 v projekte Hotel Lead Enrichment Engine OS.

Najprv si načítaj:
- docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md
- starý template: 37 Hotel Magnus Trenčín Enrichment.md
- aktuálny enrichment output

Tvoja úloha:
1. navrhni a implementuj `commercial_synthesizer`
2. používaj len grounded factual input
3. vygeneruj structured fields pre:
   - čo je obchodne zaujímavé
   - čo je silné
   - kde je priestor
   - main bottleneck hypothesis
   - pain point hypothesis
   - personalization angles
   - recommended hook
   - call hypothesis
   - verdict
4. nie markdown-first, ale structured-output-first

Cieľ:
- výsledok sa má čo najviac podobať starému manuálnemu enrichmentu
- ale musí byť strojovo spracovateľný
```

## Prompt pre Wave 4

Použi, ak chceš dorobiť finálny ranking po enrichmente:

```text
Pokračuj na Wave 4 v projekte Hotel Lead Enrichment Engine OS.

Najprv si načítaj:
- docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md
- configs/scoring.yaml
- configs/ranking_tuning.yaml
- aktuálny processed + enrichment output

Tvoja úloha:
1. navrhni `post-enrichment ranking refresh`
2. oddeľ pre-enrichment light score od final ranking
3. pridaj enrichment-derived ranking signals bez zbytočnej zložitosti
4. zachov broad lead retention

Cieľ:
- finálne poradie leadov po enrichmente
- lepší shortlist
- lepší ClickUp priority layer
```

## Prompt pre Wave 5

Použi, ak chceš generovať full markdown enrichment:

```text
Pokračuj na Wave 5 v projekte Hotel Lead Enrichment Engine OS.

Najprv si načítaj:
- docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md
- starý template: 37 Hotel Magnus Trenčín Enrichment.md
- aktuálny enrichment_master output

Tvoja úloha:
1. navrhni renderer, ktorý vygeneruje 1 markdown enrichment per hotel
2. markdown má byť render z already-structured data
3. nesmie sa z markdownu stať primary database format

Cieľ:
- zachovať richness starého template
- ale primárny systém nechať structured-first
```

## Odporúčaný štart

Ak chceš najlepší ďalší thread, použi tento prompt:

```text
Pokračuj na Wave 1 v projekte Hotel Lead Enrichment Engine OS podľa docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md.
Najprv načítaj architecture doc, OUTPUT_CSV_SCHEMAS.md, src/enrich_hotels.py a starý template 37 Hotel Magnus Trenčín Enrichment.md.
Potom navrhni a implementuj minimálny source_bundle layer per hotel ako základ pre factual enrichment.
Slovak only. Short, technical, practical, no fluff.
```
