# Hotel Lead Enrichment Engine OS

Python-first systém na spracovanie hotel leadov do podoby:

- normalizované a scored accounty
- factual/source-bundle artifacty
- commercial synthesis `v3-lite`
- finálny ranking a decisioning
- email drafty
- master exporty
- operator markdown briefy
- ClickUp-ready exporty
- QA/gate artifacty
- Make handoff payload

## Čo tento repo robí

Repo premieňa raw hotel lead exporty na kontrolovaný operátorský a CRM-ready workflow. Cieľ nie je len generovať CSV, ale držať:

- stabilný pipeline beh
- grounded enrichment
- kvalitný ranking
- relevanciu outreachu
- čistotu CRM importu

Make nie je mozog systému. Make je len tenká execution/orchestration vrstva nad artifactmi pripravenými lokálnym Python flow.

## Kanonická flow

`normalize -> factual/source_bundle -> commercial_synthesizer(v3-lite) -> ranking_refresh -> email_drafts -> master_exports -> render_full_enrichment_md -> clickup_export -> QA/gate -> Make`

## Aktuálna realita

- kanonická architektúra je týmto repom už definovaná
- veľká časť lokálnej pipeline a artifacts vrstvy je postavená
- Make live execution stále nie je plne validovaný end-to-end
- niektoré staršie wrappery a historické outputy ešte v repo existujú, ale nie sú source-of-truth

## Hlavné dokumenty

- [CURRENT_SYSTEM_STATUS.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/CURRENT_SYSTEM_STATUS.md)
- [CANONICAL_RUNBOOK.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/CANONICAL_RUNBOOK.md)
- [CODEX_PROJECT_BRIEF.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/CODEX_PROJECT_BRIEF.md)
- [RETENTION_AND_FIXTURE_POLICY.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/RETENTION_AND_FIXTURE_POLICY.md)
- [PHASE_1_ENRICHMENT_ARCHITECTURE.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/PHASE_1_ENRICHMENT_ARCHITECTURE.md)
- [OUTPUT_CSV_SCHEMAS.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/OUTPUT_CSV_SCHEMAS.md)
- [MAKE_EXECUTION_PAYLOAD_CONTRACT.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/docs/project/MAKE_EXECUTION_PAYLOAD_CONTRACT.md)

## Prioritné poradie

1. pipeline stability
2. data quality
3. enrichment quality
4. email relevance
5. CRM cleanliness
6. only then further automation

## Repo map

- `src/` runtime a supporting skripty
- `configs/` runtime contracts
- `prompts/` podporné prompt/policy assets
- `data/raw/` immutable raw vstupy
- `data/processed/` medzivrstvy po normalizácii
- `data/qa/` QA, gate, rehearsal a orchestration artifacts
- `outputs/` canonical output families a historical variants
- `docs/project/` architektúra, contracts, SOP a historické checkpointy
- `project info/` legacy bootstrap materiál

## Lokálne spustenie

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python3 src/main.py
```

Poznámka:
Kým `src/orchestrate.py` nebude zosúladený s kanonickou flow, tento command je stále technický entrypoint, nie definitívny popis finálneho canonical run order. Presný source-of-truth pre flow je v [CANONICAL_RUNBOOK.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/CANONICAL_RUNBOOK.md) a [CURRENT_SYSTEM_STATUS.md](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/CURRENT_SYSTEM_STATUS.md).
