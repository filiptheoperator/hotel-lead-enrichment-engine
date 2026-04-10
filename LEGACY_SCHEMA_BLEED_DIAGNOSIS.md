# LEGACY SCHEMA BLEED DIAGNOSIS

## Scope

Táto diagnostika rieši úzky problém po smoke rune:

- čerstvé kanonické commercial JSON artifacty sa zapisujú ako `commercial_synthesis/v3-lite`
- downstream business fields už vo veľkej miere zodpovedajú `v3-lite`
- ale `commercial_schema_version` v ranked CSV stále ukazoval mix `v1` a `v3-lite`

## Root Cause

Problém nebol v `src/orchestrate.py` ani v enrichment CSV schema markeri.

### Zistenia

1. `outputs/enrichment/*_enriched*.csv` nenesie samostatný `commercial_schema_version` stĺpec.
2. `src/ranking_refresh.py` čítal `commercial_schema_version` priamo z JSON artifactu v `outputs/commercial_synthesis/<batch>/<account_id>.json`.
3. V aktuálnom batch priečinku reálne existovala zmiešaná sada artifactov:
   - 5x `commercial_synthesis/v3-lite`
   - 5x `commercial_synthesis/v1`
4. `src/ranking_refresh.py` doteraz považoval akýkoľvek nájdený commercial JSON za aktívny structured source, bez rozlíšenia, či ide o kanonický `v3-lite` alebo starý `v1`.

### Praktický dôsledok

To znamenalo dve veci naraz:

- metadata bleed:
  - `commercial_schema_version` v ranked CSV ukazoval `v1`
- partial business-logic bleed:
  - ranking vrstva vedela čítať legacy `v1` JSON ako structured commercial source, ak ten súbor stále existoval pod rovnakým batch/account path

Takže problém nebol len kozmetický stĺpec. Metadata ho odhaľovali, ale za určitých okolností sa do ranking boundary vedel dostať aj legacy artifact.

## Surgical Fix

Fix bol implementovaný len v `src/ranking_refresh.py`.

### Zmena správania

1. Zaviedol sa explicitný kanonický marker:
   - `CANONICAL_COMMERCIAL_SCHEMA_VERSION = "commercial_synthesis/v3-lite"`
2. `build_structured_row_context()` teraz považuje commercial JSON za kanonický structured source iba vtedy, keď:
   - `schema_version == commercial_synthesis/v3-lite`
3. Ak commercial JSON nie je kanonický:
   - jeho structured fields sa už nepoužijú ako primary commercial source v ranking boundary
   - `commercial_schema_version` sa už nevyplní hodnotou `v1`
4. Pribudli explicitné metadata stĺpce:
   - `commercial_source_mode`
   - `commercial_fallback_used`

### Nový význam stĺpcov

- `commercial_schema_version`
  - reprezentuje iba kanonický commercial artifact skutočne použitý v ranking boundary
  - pri legacy/missing stave ostane prázdny
- `commercial_source_mode`
  - `canonical_v3_lite`
  - `legacy_fallback_or_missing`
- `commercial_fallback_used`
  - `yes` / `no`

## What Was Not Changed

- neprepisovali sa historické JSON artifacty v `outputs/commercial_synthesis`
- nemažali sa staré `v1` súbory
- neprestavovala sa architektúra pipeline
- nemenili sa master/email/clickup/markdown moduly, pretože bleed vznikal upstream v ranking boundary

## Verification

Po zmene bolo overené:

- `src/ranking_refresh.py` prejde `compile()`
- modul sa korektne importuje
- nasucho postavený ranked dataframe už ukazuje:
  - `commercial_schema_version = commercial_synthesis/v3-lite` len pre kanonické riadky
  - pre legacy/missing riadky je `commercial_schema_version` prázdny
  - `commercial_source_mode` jasne odlišuje `canonical_v3_lite` vs `legacy_fallback_or_missing`

## Conclusion

Root cause bol:

- starý `v1` commercial JSON stále fyzicky prítomný v batch priečinku
- ranking boundary ho doteraz nerozlišovala od kanonického `v3-lite`

Surgical fix zabezpečuje, že:

- `v1` už nepresakuje ako aktívna schema truth do fresh canonical ranked outputu
- kanonická schema marker vrstva ostáva pravdivá
- fallback zostáva explicitný a oddelený
