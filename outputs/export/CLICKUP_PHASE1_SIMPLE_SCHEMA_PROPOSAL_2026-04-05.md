# ClickUp Phase 1 Simple Schema Proposal

Dátum: 2026-04-05

## Cieľ

ClickUp má byť len jednoduchá account a operator vrstva.
Plný enrichment a plné outreach texty majú zostať mimo ClickUp.

## Finálna praktická vrstva

### Phase 1 minimal ClickUp

Použiť ako default import:

- `Task name`
- `Status`
- `Priority`
- `Account Status`
- `Hotel name`
- `Country`
- `City / Region`
- `Hotel Type`
- `Rooms Range`
- `Contact website`
- `Source`
- `Priority score`
- `Priority Level`
- `ICP Fit`
- `OTA Dependency Signal`
- `Direct Booking Weakness`
- `Main Pain Hypothesis`
- `Subject line`
- `Source file`

### Full ranked ClickUp

Použiť len na review alebo detailnejší import.
Obsahuje aj:

- `Description content`
- explainability polia
- outreach tracking polia
- review signály

## Deterministický Account Status

- `Prioritized`
  - vysoká priorita a bez review blockeru
- `Researching`
  - review flag alebo neistota fitu
- `Activated`
  - lead už je v aktívnej outbound práci alebo má reply outcome
- `Parked`
  - lead ostáva v databáze, ale nie je aktuálna priorita
- `Not a Fit`
  - nízky ICP fit, ale lead sa nemaže

## Fill policy

Nikdy nevymýšľať dáta.

Required ClickUp polia sa plnia len z:

- raw sheet
- normalizácie
- ranking/scoring vrstvy
- enrichment vrstvy, ak ide o krátky grounded údaj

Ak chýba detail:

- nechaj pole prázdne, ak je optional
- alebo použi deterministic fallback, ak je required

## Mimo ClickUp

Mimo ClickUp majú zostať:

- plné research notes
- opening hours detail
- kontaktné varianty
- long-form enrichment text
- plné email bodies
- dedupe review internals

## Praktický výsledok

Pipeline má robiť:

1. vziať 1 raw lead sheet
2. nechať všetky non-duplicate leady
3. zoradiť ich best -> worst
4. vytvoriť full enrichment per hotel
5. vytvoriť outreach drafts
6. vytvoriť jednoduchý ClickUp import
7. podporiť live ClickUp write
