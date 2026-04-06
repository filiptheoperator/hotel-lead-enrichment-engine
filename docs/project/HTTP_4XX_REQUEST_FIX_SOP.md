# HTTP 4xx Request Fix SOP

## Cieľ

Dať operátorovi presný fix postup, ak Make vetva vráti `HTTP 4xx`.

## Postup

1. označ incident ako `http_client_error`
2. nespúšťaj retry naslepo
3. skontroluj request export, payload a endpoint konfiguráciu
4. oprav request príčinu
5. zopakuj len kontrolovaný test po oprave
6. až potom vráť scenár do live-ready stavu

## Nerobiť

- neopakovať ten istý request bez zmeny
- neoznačiť chybu ako transient network issue
- nepreskočiť nový artifact review po oprave
