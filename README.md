# Hotel Lead Enrichment Engine OS

Jednoduchý Python-first repozitár pre stabilný workflow enrichmentu hotelových leadov pre nezávislé 3-4 hviezdičkové hotely.

## Aktuálna fáza

Aktívna je iba **Phase 1: repo structure + configs + env + README**.

V tejto fáze repo zámerne neobsahuje produkčný pipeline runner, orchestration vrstvu ani integračné automaty. Cieľom je pripraviť čistý, reprodukovateľný základ.

## Core workflow

`raw ingest -> normalize -> score -> enrich -> email drafts -> ClickUp exports`

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
- `src/` - minimálny Python bootstrap

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

### 3. Základná kontrola

```bash
python3 src/main.py
```

Očakávaný výsledok:

- vypíše názov projektu
- potvrdí, že Phase 1 je pripravená

## Konfigurácia

Hlavné nastavenia sú v:

- `configs/project.yaml`
- `configs/scoring.yaml`
- `configs/enrichment.yaml`
- `configs/email.yaml`

Environment premenné sú mimo kódu v `.env`.

## Poznámky k dátam

- vstupy ukladaj iba do `data/raw/`
- súbory v `data/raw/` neupravuj a neprepisuj
- všetko odvodené ukladaj do `data/processed/` alebo `outputs/`
- každú neoverenú hodnotu označ podľa konfigurácie ako `Verejne nepotvrdené`

## Mimo rozsahu tejto fázy

Zatiaľ vedome nepridávame:

- Apify runner
- ClickUp export logiku
- Make orchestration
- email generation engine
- scoring engine
- enrichment scraping workflow
