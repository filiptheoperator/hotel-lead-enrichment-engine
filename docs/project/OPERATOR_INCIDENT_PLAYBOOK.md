# Operator Incident Playbook

## Cieľ

Dať operátorovi stručný postup pri integračnom incidente bez hľadania v detailných dokumentoch.

## Incident typy

- missing artifact
- wrong payload
- ClickUp external blocker
- partial write risk
- unknown external error

## Univerzálny postup

1. zastav affected vetvu
2. potvrď batch decision
3. otvor relevantný QA artifact
4. skontroluj, či ide o interný alebo externý problém
5. ak ide o externý blocker, nezačni improvizovaný fix mimo repo
6. zapíš decision a next step

## Pri partial write

- zapíš task IDs
- zapíš task URLs
- nepokračuj batchom
- rozhodni o cleanup až po kontrole

## Pri ClickUp external blocker

- označ incident ako `external blocker`
- nespochybňuj mapping bez dôkazu
- pokračuj v neblokovaných plánovacích krokoch
