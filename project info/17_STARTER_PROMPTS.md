# Starter Prompts

## Prompt 1 — založenie repo projektu
Vytvárame projekt pre automatizáciu workflowu independent 3–4★ hotel lead enrichmentu.
Drž sa iba slovenčiny.
Odpovede drž čo najkratšie.
Keď ide o technický krok, rozdeľ odpoveď na:
Diagnóza / VS Code / Codex web / Validácia.
Nepridávaj zbytočné nástroje.
Cieľ je buildnúť stabilný systém pre:
raw ingest → normalize → score → enrich → email drafts → ClickUp exports.

## Prompt 2 — build first implementation phase
Chcem implementovať iba Fázu 1: repo structure + configs + env + README.
Nerob nič navyše.
Veď ma presne krok po kroku.
Po dokončení mi pripomeň GitHub commit a push.

## Prompt 3 — build enrichment engine
Chcem implementovať enrichment engine v1.
Vstup je ranked hotel dataset.
Výstup musí byť:
- structured enrichment CSV,
- per-hotel markdown file,
- personalization angles,
- cold email draft,
- follow-up draft.
Nič nevymýšľaj. Neoverené veci označ ako nepotvrdené.

## Prompt 4 — build clickup export layer
Chcem buildnúť export layer pre ClickUp.
Výstup má vytvoriť import-ready CSV súbory pre accounts, contacts a outbound queue.
Drž sa jednoduchej architektúry.
