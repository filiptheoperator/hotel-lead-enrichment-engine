# Current State and Target State

## Current state

### Source layer
- Apify raw lead export.

### Cleaning layer
- Codex agenti čistia a mapujú dáta do ClickUp-ready formátu.

### Enrichment layer
- manuálny ChatGPT hotel-by-hotel workflow.

### CRM layer
- ClickUp architektúra existuje, ale sync nie je plne dobudovaný.

### Email layer
- personalization je silná, ale pomalá a ručná.

## Main bottleneck
Najväčší bottleneck je enrichment a následná personalizácia.

## Target state

### Step 1
Raw export sa uloží do `data/raw`.

### Step 2
Normalizer vytvorí štruktúrované ranked account outputs.

### Step 3
Batch enrichment engine spracuje top N hotelov.

### Step 4
Engine vytvorí:
- structured CSV/JSON,
- markdown hotel briefs,
- email angle blocks,
- cold email draft,
- follow-up draft.

### Step 5
CRM sync layer pripraví import-ready outputs.

### Step 6
Používateľ reviewne len top priority leads.

## Primary target
Znížiť ručnú prácu bez pádu kvality.

## Secondary target
Udržať enrichment ako hlavný komerčný asset.
