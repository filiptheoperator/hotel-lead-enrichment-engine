# Fáza 2 - Definition of Done

## Stav
Fáza 2 je uzatvorená po dokončení stabilization a QA hardening vrstvy pre lokálny Python-first workflow.

## Čo je potvrdené
- `src/main.py` spúšťa orchestrace flow end-to-end.
- Pipeline vytvára enrichment output, email drafty, ClickUp export, QA výstupy a run summary.
- ClickUp import readiness check je súčasťou QA.
- Manual review shortlist prioritizuje `High` a `Medium-High` leady.
- Source attribution je sprísnený pre opening hours aj check-in / check-out.
- Check-in / check-out heuristiky majú offline regression set a curated spot-check set.
- Run summary obsahuje fetch health, fallback metriku a run-to-run delta report.
- DNS incident guardrail rozlišuje infra problém od reálne unreachable webu.
- Pri systémovom DNS probléme fallback zachová predchádzajúce overené public-web údaje, ak existujú.

## Acceptance kritériá
- Full demo run funguje lokálne end-to-end.
- `python3 src/checkin_checkout_regression.py` prejde bez failu.
- `python3 src/checkin_checkout_spotcheck.py` prejde bez failu.
- `python3 src/qa_checks.py` vygeneruje `qa_issues.csv`, `qa_summary.txt` a `manual_review_shortlist.csv`.
- `python3 src/run_report.py` vygeneruje `run_summary.txt` a `run_delta_report.txt`.
- Neoverené údaje zostávajú jasne označené.
- Raw input súbory sa neprepisujú.

## Známe limity
- Live web fetch je citlivý na DNS / sieťové obmedzenia prostredia.
- Reálny dopad check-in / check-out heuristík na živých weboch zostáva čiastočne neoverený, ak fetch vrstva padá.
- ClickUp export je pripravený na import, ale ešte to nie je živá ClickUp integrácia.
- Make a ďalšie externé orchestration vrstvy ešte nie sú súčasťou runtime.

## Výstup Fázy 2
- Stabilné lokálne jadro pipeline.
- QA a reporting vrstva pripravená pre operátorský workflow.
- Dôveryhodnejší shortlist pre ručný review.
