# Cloudflare 1010 Unblock Escalation SOP

## Cieľ

Dať operátorovi presný postup pri `HTTP 403 / Cloudflare 1010`.

## Postup

1. označ incident ako `BLOCKED_EXTERNAL`
2. potvrď `external_blocker_code = CLOUDFLARE_1010`
3. nepokračuj ďalším live write pokusom
4. skús inú sieť alebo stroj len podľa schváleného postupu
5. eviduj blocker a escalation artifact
6. po unbloku spusti len minimálny retest sled

## Nerobiť

- neoznačiť blocker ako interný bug pipeline
- nespúšťať opakované pokusy z tej istej blokovanej siete
- nerozširovať scope runu počas unblock testu
