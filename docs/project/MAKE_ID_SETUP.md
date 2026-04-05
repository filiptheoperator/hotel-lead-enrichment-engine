# Make ID Setup

## 1. Získaj `MAKE_TEAM_ID`

```bash
curl -s \
  -H "Authorization: Token $MAKE_API_TOKEN" \
  "https://eu1.make.com/api/v2/teams?organizationId=$MAKE_ORGANIZATION_ID"
```

Skopíruj pole:

- `id`

Príklad do `.env`:

```bash
MAKE_TEAM_ID=123456
```

## 2. Získaj `MAKE_FOLDER_ID`

```bash
curl -s \
  -H "Authorization: Token $MAKE_API_TOKEN" \
  "https://eu1.make.com/api/v2/scenarios-folders?teamId=$MAKE_TEAM_ID"
```

Skopíruj pole:

- `id`

Príklad do `.env`:

```bash
MAKE_FOLDER_ID=789012
```

## 3. Čo má byť v `.env`

```bash
MAKE_API_TOKEN=...
MAKE_ORGANIZATION_ID=...
MAKE_TEAM_ID=...
MAKE_FOLDER_ID=...
```
