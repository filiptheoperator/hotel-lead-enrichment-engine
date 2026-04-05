# Manual Fallback Without Make

## Kedy použiť

- Make je blokovaný
- ClickUp vetva je pripravená
- operátor potrebuje pokračovať ručne

## Postup

1. otvoriť finálny ClickUp CSV export
2. potvrdiť gate stav
3. pri `NO_GO` nič neimportovať
4. pri `GO` použiť len schválený import postup
5. uložiť operator evidence ručne

## Pravidlo

Manual fallback nemení business logiku.
