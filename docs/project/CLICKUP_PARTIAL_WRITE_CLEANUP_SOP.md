# ClickUp Partial Write Cleanup SOP

## Cieľ

Štandardizovať ručný cleanup po partial write incidente v ClickUp.

## Scope

Aktuálne potvrdený partial write task:

- task_id: `869ct12ah`
- task_url: [869ct12ah](https://app.clickup.com/t/869ct12ah)

## Postup

1. otvor task podľa `task_url`
2. skontroluj, či ide o test task z rehearsal
3. skontroluj, či nie sú zapísané business-relevant údaje navyše
4. rozhodni:
- ponechať ako audit sample
- alebo ručne odstrániť
5. zapíš rozhodnutie do incident logu alebo operator notes

## Pravidlá

- žiadny automatický delete z lokálneho scriptu
- cleanup je ručný a operator-driven
- ak nie je isté, čo task obsahuje, najprv ho ponechať

## Exit condition

- task je buď vedome ponechaný
- alebo vedome odstránený
- rozhodnutie je zdokumentované
