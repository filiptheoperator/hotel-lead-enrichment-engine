# ClickUp Required Fields Create Spec

## Cieľ

Doplniť do test listu `Acquisition / Pipeline / Target Accounts` chýbajúce required custom fields pre Phase 4 rehearsal.

## Target list

- workspace: `90121598651`
- list: `Acquisition / Pipeline / Target Accounts`
- list_id: `901216789251`

## Chýbajúce required fields

### 1. Priority score

- field name: `Priority score`
- recommended type: `short_text`
- source column: `Priority score`
- target key: `custom.priority_score`
- required_for_phase_4_cutover: `yes`
- sample value: `9.37`

### 2. Subject line

- field name: `Subject line`
- recommended type: `short_text`
- source column: `Subject line`
- target key: `custom.subject_line`
- required_for_phase_4_cutover: `yes`
- sample value: `Loft Hotel Bratislava: krátky nápad`

### 3. Source file

- field name: `Source file`
- recommended type: `short_text`
- source column: `Source file`
- target key: `custom.source_file`
- required_for_phase_4_cutover: `yes`
- sample value: `raw_bratislava region_2026-04-01_21-01-58-857.csv`

## Už potvrdené fields

- `Hotel Name`
- `City`
- `Phone`
- `Website`

## Pravidlá

- nemení sa uzamknutý payload contract
- nepridáva sa nová business logika
- ak sa field vytvorí s inom názve, treba to explicitne zapísať ako alias
- preferovaný typ je `short_text`, aby sedel na aktuálny CSV contract

## Po vytvorení

1. znovu spustiť live field discovery
2. potvrdiť nové field IDs
3. až potom spraviť isolated rehearsal write pre 3 sample riadky

## Poznámka

Podľa oficiálnej ClickUp API dokumentácie je cez API potvrdené:

- čítanie dostupných list custom fields
- nastavovanie hodnoty existujúceho custom fieldu na tasku

V tomto repozitári nie je potvrdený oficiálny API endpoint na vytvorenie nového custom fieldu.
Preto tento krok ostáva manuálny v ClickUp UI.
