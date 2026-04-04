# Hotel Lead Enrichment Engine OS

Jednoduchý Python-first repozitár pre stabilný workflow enrichmentu hotelových leadov pre nezávislé 3-4 hviezdičkové hotely.

## Aktuálna fáza

Aktívna je **Fáza 3: Operator-ready workflow**.

Lokálny Python-first pipeline už beží end-to-end:

- `normalize + score`
- `enrich`
- `email drafts`
- `ClickUp export`
- `QA`
- `run summary`

Aktuálne sa uzamyká output contract, operátorský checklist, run manifest a integračný handoff pre budúci ClickUp / Make krok.

## Core workflow

`raw ingest -> normalize -> score -> enrich -> email drafts -> ClickUp export -> QA -> run summary`

## Princípy

- architektúra má zostať jednoduchá
- Python je primárna runtime vrstva
- configy sú oddelené od kódu
- prompty sú oddelené od kódu
- raw vstupy sa nikdy neprepisujú
- neoverené údaje musia byť jasne označené
- ak sú verejne dostupné, enrichment má obsahovať aj otváracie / prevádzkové hodiny
- Make je až neskoršia glue vrstva, nie súčasť tejto fázy

## Štruktúra repozitára

- `configs/` - YAML konfigurácie projektu, scoringu, enrichmentu a emailov
- `data/raw/` - nemenené vstupné dáta
- `data/processed/` - medzikroky po normalizácii a scoringu
- `data/qa/` - manuálne kontroly a QA podklady
- `docs/` - ľahká projektová dokumentácia
- `outputs/enrichment/` - finálne enrichment výstupy
- `outputs/email_drafts/` - email drafty
- `outputs/clickup/` - exporty pre ClickUp
- `prompts/enrichment/` - prompty pre enrichment
- `prompts/email/` - prompty pre email drafty
- `src/` - pipeline kroky, QA, reporting a orchestrácia

## Lokálne spustenie

### 1. Virtuálne prostredie

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 2. Environment

```bash
cp .env.example .env
```

Potom doplň lokálne tajomstvá do `.env`.

### 3. Demo run

```bash
python3 src/main.py
```

Očakávaný výsledok:

- spracuje latest batch cez celý lokálny flow
- vygeneruje enrichment, email drafty a ClickUp export
- vytvorí QA výstupy a run summary v `data/qa/`

## Konfigurácia

Hlavné nastavenia sú v:

- `configs/project.yaml`
- `configs/scoring.yaml`
- `configs/enrichment.yaml`
- `configs/email.yaml`
- `configs/qa.yaml`

Environment premenné sú mimo kódu v `.env`.

## Poznámky k dátam

- vstupy ukladaj iba do `data/raw/`
- súbory v `data/raw/` neupravuj a neprepisuj
- všetko odvodené ukladaj do `data/processed/` alebo `outputs/`
- každú neoverenú hodnotu označ podľa konfigurácie ako `Verejne nepotvrdené`

## Čo už dnes funguje

- full local demo run end-to-end
- run summary artifact po každom behu
- ClickUp import readiness check
- QA issue export a manual review shortlist
- sample batch mode
- source attribution pre opening hours aj check-in/check-out
- DNS fallback ochrana pri verejnom web fetchi
- run-to-run delta report

## Mimo aktuálneho rozsahu

Zatiaľ ešte nie sú hotové produkčné integrácie:

- živé ClickUp API prepojenie
- Make orchestration
- scheduled automation
- externé ops workflow
