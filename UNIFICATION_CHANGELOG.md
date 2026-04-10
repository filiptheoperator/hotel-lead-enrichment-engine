# UNIFICATION_CHANGELOG

## Cieľ zmeny

Zosúladiť aktívnu executable path s potvrdenou kanonickou flow bez širokého refaktoru a bez cleanup zásahov.

## Runtime zmeny

### `src/orchestrate.py`

- wrapper flow bol zoradený podľa kanonického poradia:
  - `normalize`
  - `factual/source_bundle`
  - `commercial_synthesizer(v3-lite)`
  - `ranking_refresh`
  - `email_drafts`
  - `master_exports`
  - `render_full_enrichment_md`
  - `clickup_export`
  - `QA`
  - supporting manifest/report/gate/operator steps
  - `Make orchestration`

### `src/main.py`

- CLI description a help text boli zosúladené s kanonickou flow
- orchestration-only režim je explicitne opísaný ako práca nad existujúcimi artifactmi

### `src/enrich_hotels.py`

- heuristic commercial generation už nie je implicitná primárna runtime pravda
- bola ponechaná len ako explicitný legacy fallback
- defaultne je vypnutá
- zapína sa len cez `ENRICHMENT_ENABLE_LEGACY_COMMERCIAL_FALLBACK=true`
- enrichment CSV už defaultne nečíta commercial artifact ako primárnu truth vrstvu

## Boundary rozhodnutie

### Faktická vrstva

- `src/enrich_hotels.py` ostáva kanonická pre:
  - `source_bundle`
  - `factual_enrichment`
  - `outputs/enrichment/*_enriched.csv`

### Commercial vrstva

- kanonická commercial truth je až:
  - `src/commercial_synthesizer.py`
  - `commercial_synthesis/v3-lite`

### Ranking vrstva

- kanonická ranking truth je:
  - `src/ranking_refresh.py`

### Operator presentation vrstva

- kanonická final operator presentation truth je:
  - `src/render_full_enrichment_md.py`

## Čo nebolo menené

- neprebehol cleanup outputs
- neprebehol cleanup docs
- neodstraňovala sa fallback logika
- nerobili sa široké interné refaktory modulov

## Zostávajúce riziko

- wrapper flow je už zosúladený, ale niektoré staršie supporting kroky stále existujú kvôli prevádzkovej stabilite
- heuristic commercial builder v `enrich_hotels.py` stále fyzicky existuje, len už nie je defaultná primárna truth vrstva
