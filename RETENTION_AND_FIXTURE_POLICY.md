# RETENTION_AND_FIXTURE_POLICY

## Cieľ

Tento dokument určuje, ako sa majú chápať generated súbory v repozitári. V tomto kroku nič nemaže a nič nearchivuje. Definuje len pravidlá pre neskorší kontrolovaný cleanup.

## Kategórie

### Canonical artifact

Generated súbor alebo rodina, ktorá zodpovedá potvrdenej kanonickej flow a je súčasťou source-of-truth prevádzky.

Príklady rodín:

- `outputs/source_bundles/`
- `outputs/factual_enrichment/`
- `outputs/commercial_synthesis/`
- `outputs/ranked/`
- `outputs/email_drafts/`
- `outputs/master/`
- `outputs/hotel_markdown/`
- `outputs/clickup/`
- kľúčové `data/qa/` gate a orchestration artifacty

### Fixture

Commitnutý generated alebo raw súbor, ktorý zostáva v repo zámerne ako:

- testovací baseline
- contract example
- reproducibility sample
- simulation scenario

Fixture nie je „latest run by accident“. Fixture musí byť vedome ponechaný a neskôr jasne označený.

### Historical

Súbor, ktorý má dokumentačnú alebo porovnávaciu hodnotu, ale nie je súčasťou aktuálneho source-of-truth workflow.

Príklady:

- `wave*`
- `batch10`
- `v2/v3/v4/v5`
- `smoke`
- diff a QC exporty v `outputs/export/`

### Archived

Historical materiál presunutý mimo aktívnu pracovnú plochu repa alebo do explicitnej archive vrstvy. V tomto kroku sa nič ešte nepresúva.

## Čo má zostať commitnuté

### Má zostať

- všetky runtime contracts v `configs/`
- root canonical docs
- hlavné architektúrne a payload contract docs
- minimálny set raw fixture vstupov
- minimálny set canonical generated fixtures na overenie:
  - factual/source_bundle
  - commercial_synthesis
  - ranked
  - email
  - clickup
  - qa/gate
  - orchestration simulation

### Nemá zostať vo veľkom objeme

- neobmedzené latest-run generated outputs
- paralelné verzie toho istého batchu bez explicitného fixture účelu
- dlhé historické rady `wave/batch/v2-v5`
- duplikované packet copy sety bez jasného testovacieho dôvodu

## Čo je fixture

Za fixture sa neskôr bude považovať iba to, čo spĺňa všetky podmienky:

1. je potrebné na test, contract understanding alebo baseline comparison
2. má stabilný dôvod zostať v repo
3. je identifikované ako fixture, nie ako náhodný latest output
4. neexistuje rovnaká redundantná kópia inde v repo

## Čo je historical

Historical je najmä:

- staré wave outputy
- porovnávacie exporty
- QC diffy
- smoke-only výstupy mimo fixture baseline
- predošlé iterácie toho istého batchu

## Čo sa má neskôr archivovať

Neskorší archive candidates:

- `data/archive/`
- historical output variants v `outputs/`
- staré operator packet kópie
- staré checkpoint generated artifacty bez fixture funkcie

## Čo sa má neskôr gitignorovať

Po potvrdení fixture setu by sa mali zvážiť na `.gitignore` najmä:

- latest generated outputs v `outputs/master/`
- latest generated outputs v `outputs/source_bundles/`
- latest generated outputs v `outputs/factual_enrichment/`
- latest generated outputs v `outputs/commercial_synthesis/`
- latest generated outputs v `outputs/ranked/`
- latest generated outputs v `outputs/hotel_markdown/`
- latest generated outputs v `outputs/export/`
- latest archive runy v `data/archive/`
- vybrané top-level runtime outputs v `data/qa/`, okrem fixture scenario folders

Pozor:
nič z toho sa nemá meniť skôr, než bude explicitne oddelené:

- canonical fixture
- historical
- runtime leftovers

## Naming rules for canonical artifacts

### Canonical generated artifact naming

- jeden batch = jeden jasný source stem
- kanonické artifacty nemajú niesť marketingové alebo nejasné suffixy
- suffix má hovoriť len o funkcii, nie o pocite finality

### Povolené funkčné suffixy

- `_normalized_scored`
- `_enriched`
- `_ranking_refreshed`
- `_email_drafts`
- `_accounts_master`
- `_enrichment_master`
- `_outreach_drafts`
- `_operator_shortlist`
- `_top_20_export`
- `_clickup_import`
- `_clickup_phase1_minimal`
- `_clickup_full_ranked`

### Nepreferované naming patterns pre budúcnosť

- `_final`
- `_reallyfinal`
- neobmedzené `_v2/_v3/_v4/_v5`
- paralelné `waveX_batchY_vZ` bez explicitného fixture účelu

## Policy for `data/qa`

### Má zostať ako canonical/supporting

- gate outputs
- payload validation
- run manifest
- evidence log
- retry / reconciliation outputs

### Má zostať ako fixture

- `simulated_*`
- `stateful_*`
- explicitné regression case súbory

### Needs review before later cleanup

- `clickup_operator_pack/`
- `clickup_dry_run_packet/`
- duplikované generated packet copy families

## Policy for `project info/`

- nie je active source-of-truth
- nie je delete candidate
- je to legacy bootstrap material
- neskôr sa má presunúť do archivovanej docs vrstvy
