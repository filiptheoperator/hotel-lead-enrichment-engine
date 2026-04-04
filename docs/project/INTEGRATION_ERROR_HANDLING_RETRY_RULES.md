# Integration Error Handling And Retry Rules

## Cieľ

Definovať minimálne a pevné pravidlá pre integračnú fázu bez pridania novej architektúry.

## Kategórie chýb

### 1. Hard stop

- chýba required artifact
- `decision = NO_GO`
- `fetch_incident_flag = yes`
- `qa_blocking_rows > 0`
- nepotvrdený required custom field ID

Pravidlo:
- bez retry
- bez live ClickUp write
- okamžitá notifikácia operátorovi

### 2. Config mismatch

- CSV hlavička nesedí na mapping config
- ClickUp field type nesedí s contractom
- live field ID smeruje na nesprávne pole

Pravidlo:
- bez automatického retry
- najprv opraviť config
- potom zopakovať iba rehearsal sample

### 3. Transient external failure

- dočasný HTTP timeout
- rate limit
- dočasný ClickUp / Make outage

Pravidlo:
- max `3` retry
- backoff: `30s`, `120s`, `300s`
- retry iba pre identický payload
- po vyčerpaní retry prechod do `BLOCKED`

### 4. Partial write risk

- časť sample taskov sa zapísala a časť zlyhala

Pravidlo:
- zastaviť ďalší write
- zapísať zoznam úspešne vytvorených taskov
- nepokračovať batchom
- operátor rozhodne o cleanup alebo pokračovaní

## Idempotency pravidlo

- každý rehearsal alebo live batch musí mať jednoznačný run context z [data/qa/run_manifest.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/run_manifest.json)
- retry nesmie meniť source CSV ani payload shape
- ak existuje podozrenie na duplicate write, ďalší retry je zakázaný do ručného overenia

## Operator notification minimum

- typ chyby
- affected artifact alebo field
- či prebehol retry
- odporúčaný ďalší krok

## Záver

Automatický retry je povolený len pre transient external failure.
Všetky ostatné vetvy ostávajú operator-driven.
