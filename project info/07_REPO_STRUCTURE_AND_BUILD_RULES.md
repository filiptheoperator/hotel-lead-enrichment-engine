# Repo Structure and Build Rules

## Odporúčaná štruktúra

```text
hotel-lead-enrichment-engine/
├── README.md
├── .env.example
├── .gitignore
├── requirements.txt
├── configs/
│   ├── project.yaml
│   ├── scoring.yaml
│   ├── enrichment.yaml
│   └── email.yaml
├── data/
│   ├── raw/
│   ├── processed/
│   └── qa/
├── outputs/
│   ├── ranked/
│   ├── enrichment/
│   ├── hotel_markdown/
│   ├── email_drafts/
│   └── clickup/
├── prompts/
│   ├── enrichment/
│   └── email/
├── src/
│   ├── main.py
│   ├── ingest/
│   ├── normalize/
│   ├── scoring/
│   ├── enrich/
│   ├── compose/
│   ├── export/
│   └── utils/
└── docs/
    └── project/
```

## Build rules
- Žiadne voľné súbory po projekte.
- Každý výstup musí mať pevné miesto.
- Configy musia byť oddelené od kódu.
- Prompty musia byť oddelené od kódu.
- Raw dáta sa nesmú prepisovať.
- Processed dáta sa môžu regenerovať.
- Outputs sú finálne použiteľné exporty.

## Naming rules
- názvy priečinkov: malé písmená,
- názvy configov: zrozumiteľné,
- názvy outputov: stabilné a popisné,
- žiadne náhodné verzie typu `final_final_reallyfinal.csv`.

## Beginner rule
Každá zmena štruktúry musí byť zapísaná do README.
