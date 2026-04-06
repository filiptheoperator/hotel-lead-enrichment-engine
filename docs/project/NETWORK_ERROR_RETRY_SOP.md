# Network Error Retry SOP

## Cieľ

Dať operátorovi presný postup pri `network_error` počas Make vetvy.

## Postup

1. označ incident ako `network_error`
2. skontroluj sieť, DNS a lokálny prístup
3. potvrď, že request payload ostal nezmenený
4. použi retry eligibility a backoff plan
5. zopakuj len kontrolovaný retry
6. ak sa chyba opakuje, eskaluj ako sieťový alebo infra problém

## Nerobiť

- neposielať viac retry naraz
- nemeniť payload scope pri sieťovej chybe
- nepreskočiť evidence a reconciliation
