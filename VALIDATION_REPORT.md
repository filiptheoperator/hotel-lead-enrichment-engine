# VALIDATION REPORT

## Scope

Táto validácia bola zameraná na najbezpečnejšie dostupné overenie kanonickej runtime cesty po unifikácii:

- `src/main.py`
- `src/orchestrate.py`
- `src/enrich_hotels.py`
- `src/commercial_synthesizer.py`
- `src/ranking_refresh.py`
- downstream moduly:
  - `src/email_drafts.py`
  - `src/master_exports.py`
  - `src/render_full_enrichment_md.py`
  - `src/clickup_export.py`
  - `src/qa_checks.py`
  - `src/clickup_import_gate.py`

Nebola spustená plná live end-to-end pipeline exekúcia, pretože canonical commercial vrstva závisí od externých vstupov a taký run by už nebol najbezpečnejšia validačná voľba. Namiesto toho prebehla:

- syntax validácia cez `compile()`
- import sanity check modulov
- kontrola reálneho wrapper poradia
- kontraktná kontrola medzi modulmi
- kontrola existujúcich artifactov a ich schema verzií

## 1. Wrapper Truth

### Stav

`src/orchestrate.py` teraz uvádza kanonický krokový order:

1. `normalize`
2. `factual/source_bundle`
3. `commercial_synthesizer (v3-lite)`
4. `ranking refresh`
5. `email drafts`
6. `master exports`
7. `render full enrichment markdown`
8. `ClickUp export`
9. `QA`
10. až potom supporting/operator/archive/Make kroky

### Záver

- Wrapper truth je zosúladená s potvrdenou architektúrou.
- Nenašiel sa konkurenčný default executable path v `src/main.py`.
- `--orchestration-only` ostáva explicitne oddelený režim, nie konkurenčný enrichment runtime.

## 2. Factual -> Commercial Boundary

### `src/enrich_hotels.py`

Overené:

- fallback boundary neobsahuje neúplný komentár, rozbitý riadok ani syntax chybu
- factual flow ostáva primárny:
  - `source_bundle`
  - `factual_enrichment`
- heuristická commercial vrstva je za guardom:
  - `ENRICHMENT_ENABLE_LEGACY_COMMERCIAL_FALLBACK`

### Záver

- Legacy heuristic commercial logic už nie je primary-by-default.
- Canonical commercial truth je presunutá do `src/commercial_synthesizer.py`.

## 3. Commercial -> Ranking Boundary

### Kódová kompatibilita

`src/ranking_refresh.py` číta canonical commercial artifact z:

- `outputs/commercial_synthesis/<batch>/<account_id>.json`

Používa structured fields ako:

- `schema_version`
- `verdict`
- `business_interest_summary`
- `why_commercially_interesting`
- `best_entry_angle`
- `recommended_hook`
- `service_complexity_read`
- `uncertainty_notes`

### Reálny artifact stav

Na latest `ranked` CSV bolo overené:

- required Wave 4 ranked polia sú prítomné
- ale `commercial_schema_version` je zmiešané:
  - `commercial_synthesis/v1`
  - `commercial_synthesis/v3-lite`

### Záver

- Kódová hranica medzi commercial a ranking vrstvou je funkčná.
- Aktuálne committed outputs ešte nie sú čistá kanonická baseline.
- To je validačný signál proti cleanupu, nie proti runtime unifikácii samotnej.

## 4. Ranking -> Outreach / Export Boundary

### Overené downstream napojenie

- `src/email_drafts.py` číta:
  - factual artifact
  - commercial artifact
  - ranked CSV
- `src/master_exports.py` číta:
  - processed
  - enrichment
  - ranked
  - email drafts
- `src/render_full_enrichment_md.py` číta:
  - source_bundle
  - factual_enrichment
  - commercial_synthesis
  - ranked
  - optional email drafts
- `src/clickup_export.py` ostáva downstream export vrstva nad enrichment/email/export artifacts

### Reálny artifact stav

Overené na latest files:

- `outputs/ranked/*_ranking_refreshed*.csv` existuje
- `outputs/email_drafts/*_email_drafts*.csv` existuje
- `outputs/master/*` existuje
- `outputs/hotel_markdown/*` existuje
- `outputs/clickup/*` existuje

Schema coherence:

- required ranked columns z `OUTPUT_CSV_SCHEMAS.md` nechýbajú
- email drafts obsahujú commercial-derived fields:
  - `recommended_hook`
  - `best_entry_angle`
  - `business_interest_summary`

### Záver

- Downstream chain je kontraktovo konzistentná.
- Existing outputs dokazujú, že tieto vrstvy vedia spolu existovať.
- Latest sample však stále nesie známky prechodného mixed-version stavu.

## 5. QA / Gate Boundary

### Overené

- `src/qa_checks.py` a `src/clickup_import_gate.py` sa bez chyby importujú
- `data/qa/run_manifest.json` existuje
- `data/qa/clickup_import_gate.json` existuje
- `data/qa/qa_summary.txt` existuje

Aktuálny gate stav z existujúcich artifacts:

- `decision = NO_GO`
- `stop_conditions = ['global_fetch_incident', 'qa_blocking_rows_present']`
- `batch_readiness_score = 30`
- `batch_readiness_band = red`

### Záver

- QA/gate vrstva po unifikácii ostáva koherentná.
- Aktuálne NO_GO je business/runtime readiness problém batchu, nie syntax alebo module-wiring problém z runtime unifikácie.

## 6. Syntax / Runtime Sanity

### Overené priamo

- `compile()` úspešne prešlo pre 11 kritických modulov
- import sanity check úspešne prešiel pre:
  - `orchestrate`
  - `enrich_hotels`
  - `commercial_synthesizer`
  - `ranking_refresh`
  - `email_drafts`
  - `master_exports`
  - `render_full_enrichment_md`
  - `clickup_export`
  - `qa_checks`
  - `clickup_import_gate`

### Neoverené v tomto kroku

- plná live end-to-end exekúcia cez externé API / LLM volania
- nový clean canonical batch run od nuly
- čerstvo prepočítaný full QA/gate po novom kanonickom behu

## Validation Verdict

### Passed

- wrapper order je kanonický
- neexistuje konkurenčný default runtime path
- fallback boundary v `src/enrich_hotels.py` je syntakticky čistá
- legacy commercial logika je defaultne neprimárna
- canonical downstream moduly sa importujú a kontraktovo na seba nadväzujú
- ranked schema required fields sú prítomné
- QA/gate vrstva zostáva zapojená a čitateľná

### Failed / Blocked

- latest existing `ranked` artifact nie je čistý canonical baseline, lebo mieša `commercial_synthesis/v1` a `commercial_synthesis/v3-lite`
- neprebehol nový clean end-to-end canonical run, takže runtime validácia je zatiaľ “structurally validated”, nie “fresh-run validated”

### Cleanup Readiness

Cleanup ešte nie je bezpečné spustiť.

Dôvod:

- outputs stále nesú mixed-version historický stav
- bez jedného čerstvého canonical batch runu by cleanup mohol zmazať alebo zamiešať dôležité porovnávacie baseline artifacts

## Recommended Next Move

Spustiť jeden kontrolovaný canonical smoke run bez cleanupu a potom hneď znova:

1. overiť `commercial_schema_version` v ranked outpute
2. potvrdiť, že nový batch je 100% `commercial_synthesis/v3-lite`
3. pregenerovať QA/gate artifacts na tom istom batchi
4. až potom rozhodovať o cleanup a fixture politike
