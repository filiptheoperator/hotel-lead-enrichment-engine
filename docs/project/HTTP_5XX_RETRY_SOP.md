# HTTP 5xx Retry SOP

## Cieľ

Dať operátorovi presný retry postup, ak Make vetva vráti `HTTP 5xx`.

## Postup

1. označ incident ako `http_server_error`
2. skontroluj evidence a response capture
3. nepotvrdzuj úspech runu
4. použi retry eligibility a backoff plan
5. zopakuj pokus až po backoffe
6. po druhom zlyhaní eskaluj ako server-side problém

## Nerobiť

- neposielať retry okamžite bez backoffu
- nemeniť payload scope počas retry
- nepreskočiť reconciliation po každom pokuse
