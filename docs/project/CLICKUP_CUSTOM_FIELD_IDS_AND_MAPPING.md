# ClickUp Custom Field IDs And Mapping

## Stav

Logické mapovanie je uzamknuté.
Finálne live `clickup_field_id` ostávajú `Neoverené`, kým neprebehne potvrdenie v reálnom workspace.

## Source of truth

- [configs/clickup_custom_fields.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/clickup_custom_fields.yaml)
- [configs/clickup_api_mapping.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/clickup_api_mapping.yaml)

## Locked logical mapping

| CSV column | Target key | ClickUp field name | Required for cutover | Live field ID |
| --- | --- | --- | --- | --- |
| `Hotel name` | `custom.hotel_name` | `Hotel name` | yes | `UNVERIFIED_TBD` |
| `City` | `custom.city` | `City` | yes | `UNVERIFIED_TBD` |
| `Priority score` | `custom.priority_score` | `Priority score` | yes | `UNVERIFIED_TBD` |
| `Contact phone` | `custom.contact_phone` | `Contact phone` | no | `UNVERIFIED_TBD` |
| `Contact website` | `custom.contact_website` | `Contact website` | no | `UNVERIFIED_TBD` |
| `Subject line` | `custom.subject_line` | `Subject line` | yes | `UNVERIFIED_TBD` |
| `Source file` | `custom.source_file` | `Source file` | yes | `UNVERIFIED_TBD` |

## Potvrdenie v live workspace

Pred live cutover treba pre každý field potvrdiť:

1. názov fieldu v ClickUp sedí s configom
2. type fieldu sedí s očakávaným payloadom
3. field ID je doplnené do configu
4. rehearsal task po write vráti hodnotu v správnom fielde

## Stop condition

Ak čo i len jedno `required for cutover = yes` pole nemá potvrdený live field ID, live cutover ostáva `NO_GO`.
