# Make API Access Blocker Note

## Stav

Aktuálny blocker je externý network/security blocker.

Potvrdené fakty:

- `MAKE_API_BASE_URL=https://eu1.make.com/api/v2` je správne
- token nie je potvrdený ako root cause
- `MAKE_TEAM_ID` nie je root cause
- `MAKE_SCENARIO_ID` nie je root cause
- `GET /teams` vracia `HTTP 403`
- `GET /scenarios/{id}/interface` vracia `HTTP 403`
- aj `GET /ping` je blokovaný
- response je `Cloudflare error 1010`

Záver:

- request je zablokovaný ešte pred normálnym Make API spracovaním
- Make integration debugging sa teraz neeskaluje ďalej
- interný Make kód sa nemení

## Minimálny retest po obnovení prístupu

1. `python3 src/make_id_helper.py --mode teams`
2. `python3 src/make_scenario_test_run.py --mode interface`
3. `python3 src/make_scenario_test_run.py --mode logs`
4. ak `interface` a `logs` prejdú, pokračovať na `python3 src/make_scenario_test_run.py --mode run --input-json data/qa/make_execution_payload.json`

## Stop pravidlo

Ak prvý krok znova vráti `HTTP 403` alebo `1010`, Make debugging ostáva pozastavený.
