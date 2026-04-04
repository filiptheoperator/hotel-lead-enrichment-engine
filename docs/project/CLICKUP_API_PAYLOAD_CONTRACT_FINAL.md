# ClickUp API Payload Contract - Final

## Stav

Tento contract uzamyká finálny payload shape pre integračnú fázu.
Kompatibilita s reálnym ClickUp workspace je stále čiastočne `Neoverené`, kým nebudú potvrdené live field IDs.

## Source of truth

- [configs/clickup_api_mapping.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/clickup_api_mapping.yaml)
- [configs/clickup_custom_fields.yaml](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/configs/clickup_custom_fields.yaml)
- [data/qa/clickup_api_mapping_preview.json](/Users/aios/Desktop/Codex/hotel-lead-enrichment-engine/data/qa/clickup_api_mapping_preview.json)

## Locked top-level payload

```json
{
  "name": "string",
  "description": "string",
  "status": "string",
  "priority": "string",
  "custom_fields": {
    "custom.hotel_name": "string",
    "custom.city": "string",
    "custom.priority_score": "string",
    "custom.contact_phone": "string",
    "custom.contact_website": "string",
    "custom.subject_line": "string",
    "custom.source_file": "string"
  }
}
```

## Locked source mapping

- `Task name` -> `name`
- `Description content` -> `description`
- `Status` -> `status`
- `Priority` -> `priority`
- `Hotel name` -> `custom.hotel_name`
- `City` -> `custom.city`
- `Priority score` -> `custom.priority_score`
- `Contact phone` -> `custom.contact_phone`
- `Contact website` -> `custom.contact_website`
- `Subject line` -> `custom.subject_line`
- `Source file` -> `custom.source_file`

## Required fields

- `name`
- `description`
- `status`
- `priority`
- `custom_fields.custom.hotel_name`
- `custom_fields.custom.city`
- `custom_fields.custom.priority_score`
- `custom_fields.custom.subject_line`
- `custom_fields.custom.source_file`

## Optional fields

- `custom_fields.custom.contact_phone`
- `custom_fields.custom.contact_website`

## CSV extra columns mimo API payload

Tieto stĺpce môžu byť v ClickUp import CSV prítomné, ale nie sú súčasťou uzamknutého API payload contractu:

- `Email angle`
- `CTA type`
- `Variant ID`
- `Test batch`
- `Reply outcome`
- `Give-first insight`
- `Main observed issue`
- `Email hook`
- `Micro CTA`
- `Proof snippet`
- `Primary email goal`

Slúžia pre operator review a outreach testing, nie pre zmenu top-level API shape.

## Validation rules

- payload musí obsahovať rovnaké top-level keys ako preview artifact
- required field nesmie byť prázdny string
- missing optional field nesmie zablokovať rehearsal
- mapping z CSV hlavičiek sa nesmie meniť bez update configu

## Neoverené

- presný formát `priority` v cieľovej ClickUp API implementácii
- presné custom field IDs v live workspace
- či finálny write path pôjde cez API alebo import bridge
