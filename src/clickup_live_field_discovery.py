import argparse
import json
import os
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml


ENV_PATH = Path(".env")
QA_DIR = Path("data/qa")
CUSTOM_FIELDS_CONFIG_PATH = Path("configs/clickup_custom_fields.yaml")
API_BASE = "https://api.clickup.com/api/v2"
REQUIRED_FIELD_NAMES = {
    "Hotel name",
    "City",
    "Priority score",
    "Subject line",
    "Source file",
}
PRIORITY_DROPDOWN_FIELD_NAMES = {
    "Account Status",
    "Country",
    "Hotel Type",
    "Rooms Range",
    "Source",
    "Priority Level",
    "ICP Fit",
    "Direct Booking Weakness",
    "OTA Dependency Signal",
    "Main Pain Hypothesis",
}
FIELD_NAME_ALIASES = {
    "Account Status": ["Account Status"],
    "Hotel name": ["Hotel name", "Hotel Name"],
    "Country": ["Country"],
    "City": ["City", "City / Region"],
    "Hotel Type": ["Hotel Type"],
    "Rooms Range": ["Rooms Range"],
    "Source": ["Source"],
    "Priority score": ["Priority score"],
    "Priority Level": ["Priority Level"],
    "ICP Fit": ["ICP Fit"],
    "Contact phone": ["Contact phone", "Phone"],
    "Contact website": ["Contact website", "Website"],
    "Direct Booking Weakness": ["Direct Booking Weakness"],
    "OTA Dependency Signal": ["OTA Dependency Signal", "OTA Dependancy Signal"],
    "Main Pain Hypothesis": ["Main Pain Hypothesis"],
    "Subject line": ["Subject line"],
    "Source file": ["Source file"],
}


def load_dotenv(env_path: Path = ENV_PATH) -> None:
    if not env_path.exists():
        return

    for line in env_path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def get_required_env(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"Chýba required env premenná: {name}")
    return value


def clickup_get(path: str, token: str) -> dict[str, Any]:
    request = Request(
        f"{API_BASE}{path}",
        headers={
            "Authorization": token,
            "Content-Type": "application/json",
        },
        method="GET",
    )

    try:
        with urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ClickUp HTTP error {error.code}: {body}") from error
    except URLError as error:
        raise RuntimeError(f"ClickUp network error: {error.reason}") from error


def fetch_spaces(workspace_id: str, token: str) -> list[dict[str, Any]]:
    payload = clickup_get(f"/team/{workspace_id}/space?archived=false", token)
    return payload.get("spaces", [])


def fetch_workspace_fields(workspace_id: str, token: str) -> list[dict[str, Any]]:
    payload = clickup_get(f"/team/{workspace_id}/field", token)
    return payload.get("fields", [])


def fetch_folders(space_id: str, token: str) -> list[dict[str, Any]]:
    payload = clickup_get(f"/space/{space_id}/folder?archived=false", token)
    return payload.get("folders", [])


def fetch_folder_lists(folder_id: str, token: str) -> list[dict[str, Any]]:
    payload = clickup_get(f"/folder/{folder_id}/list?archived=false", token)
    return payload.get("lists", [])


def fetch_space_lists(space_id: str, token: str) -> list[dict[str, Any]]:
    payload = clickup_get(f"/space/{space_id}/list?archived=false", token)
    return payload.get("lists", [])


def fetch_list_fields(list_id: str, token: str) -> list[dict[str, Any]]:
    payload = clickup_get(f"/list/{list_id}/field", token)
    return payload.get("fields", [])


def build_workspace_snapshot(workspace_id: str, token: str) -> dict[str, Any]:
    spaces = fetch_spaces(workspace_id, token)
    snapshot_spaces: list[dict[str, Any]] = []

    for space in spaces:
        space_id = str(space.get("id", "")).strip()
        folders = fetch_folders(space_id, token)
        folder_entries: list[dict[str, Any]] = []

        for folder in folders:
            folder_id = str(folder.get("id", "")).strip()
            folder_entries.append(
                {
                    "id": folder_id,
                    "name": str(folder.get("name", "")).strip(),
                    "lists": [
                        {
                            "id": str(item.get("id", "")).strip(),
                            "name": str(item.get("name", "")).strip(),
                        }
                        for item in fetch_folder_lists(folder_id, token)
                    ],
                }
            )

        space_lists = [
            {
                "id": str(item.get("id", "")).strip(),
                "name": str(item.get("name", "")).strip(),
            }
            for item in fetch_space_lists(space_id, token)
        ]

        snapshot_spaces.append(
            {
                "id": space_id,
                "name": str(space.get("name", "")).strip(),
                "folders": folder_entries,
                "space_lists": space_lists,
            }
        )

    return {
        "workspace_id": workspace_id,
        "spaces": snapshot_spaces,
    }


def build_field_snapshot(workspace_snapshot: dict[str, Any], list_id: str, token: str) -> dict[str, Any]:
    fields = fetch_list_fields(list_id, token)
    normalized_fields = []

    for field in fields:
        type_config = field.get("type_config", {}) or {}
        normalized_options = []
        for option in type_config.get("options", []) or []:
            normalized_options.append(
                {
                    "id": str(option.get("id", "")).strip(),
                    "name": str(option.get("name", "")).strip(),
                    "orderindex": str(option.get("orderindex", "")).strip(),
                    "color": str(option.get("color", "")).strip(),
                }
            )
        normalized_fields.append(
            {
                "id": str(field.get("id", "")).strip(),
                "name": str(field.get("name", "")).strip(),
                "type": str(field.get("type", "")).strip(),
                "type_config": type_config,
                "options": normalized_options,
                "required_for_phase_4_cutover": str(field.get("name", "")).strip() in REQUIRED_FIELD_NAMES,
            }
        )

    return {
        "workspace_snapshot": workspace_snapshot,
        "selected_list_id": list_id,
        "fields": normalized_fields,
    }


def normalize_field(field: dict[str, Any]) -> dict[str, Any]:
    type_config = field.get("type_config", {}) or {}
    normalized_options = []
    for option in type_config.get("options", []) or []:
        normalized_options.append(
            {
                "id": str(option.get("id", "")).strip(),
                "name": str(option.get("name", "")).strip(),
                "orderindex": str(option.get("orderindex", "")).strip(),
                "color": str(option.get("color", "")).strip(),
            }
        )
    return {
        "id": str(field.get("id", "")).strip(),
        "name": str(field.get("name", "")).strip(),
        "type": str(field.get("type", "")).strip(),
        "type_config": type_config,
        "options": normalized_options,
        "required_for_phase_4_cutover": str(field.get("name", "")).strip() in REQUIRED_FIELD_NAMES,
    }


def enrich_missing_dropdown_options(fields: list[dict[str, Any]], workspace_id: str, token: str) -> list[dict[str, Any]]:
    workspace_fields = [normalize_field(field) for field in fetch_workspace_fields(workspace_id, token)]
    workspace_by_id = {field["id"]: field for field in workspace_fields if field.get("id")}
    workspace_by_name = {field["name"]: field for field in workspace_fields if field.get("name")}
    enriched_fields: list[dict[str, Any]] = []

    for field in fields:
        if field.get("type") != "drop_down":
            enriched_fields.append(field)
            continue
        if field.get("options"):
            enriched_fields.append(field)
            continue
        if field.get("name") not in PRIORITY_DROPDOWN_FIELD_NAMES:
            enriched_fields.append(field)
            continue
        fallback = workspace_by_id.get(field.get("id", "")) or workspace_by_name.get(field.get("name", ""))
        if fallback and fallback.get("options"):
            field = {
                **field,
                "type_config": fallback.get("type_config", {}),
                "options": fallback.get("options", []),
            }
        enriched_fields.append(field)
    return enriched_fields


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def update_custom_fields_config(config_path: Path, field_snapshot: dict[str, Any], list_id: str) -> tuple[Path, list[str]]:
    if not config_path.exists():
        raise RuntimeError(f"Chýba config súbor: {config_path}")

    config = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    root = config.get("clickup_custom_fields", {})
    fields_map = root.get("fields", {})
    live_fields = {field["name"]: field for field in field_snapshot.get("fields", [])}
    updated_names: list[str] = []

    for field_key, item in fields_map.items():
        clickup_field_name = str(item.get("clickup_field_name", "")).strip()
        alias_candidates = FIELD_NAME_ALIASES.get(clickup_field_name, [clickup_field_name])
        live_field = None
        matched_alias = ""
        for alias_name in alias_candidates:
            live_field = live_fields.get(alias_name)
            if live_field:
                matched_alias = alias_name
                break
        if not live_field:
            continue
        item["clickup_field_id"] = live_field["id"]
        item["clickup_field_type"] = live_field["type"]
        item["live_clickup_field_name"] = matched_alias
        if live_field["type"] == "drop_down":
            item["clickup_option_ids"] = {
                str(option.get("name", "")).strip(): str(option.get("id", "")).strip()
                for option in live_field.get("options", [])
                if str(option.get("name", "")).strip() and str(option.get("id", "")).strip()
            }
            item["clickup_option_orderindex"] = {
                str(option.get("name", "")).strip(): str(option.get("orderindex", "")).strip()
                for option in live_field.get("options", [])
                if str(option.get("name", "")).strip() and str(option.get("orderindex", "")).strip()
            }
        updated_names.append(field_key)

    root["workspace_status"] = "LIVE_FIELDS_PARTIALLY_CONFIRMED"
    root["selected_test_list_id"] = list_id
    root["last_live_discovery_artifact"] = "data/qa/clickup_live_field_discovery.json"
    config["clickup_custom_fields"] = root

    config_path.write_text(
        yaml.safe_dump(config, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return config_path, updated_names


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Zistí ClickUp workspace hierarchiu a voliteľne custom fields pre konkrétny list."
    )
    parser.add_argument(
        "--list-id",
        dest="list_id",
        help="ClickUp list ID pre načítanie custom fields.",
    )
    parser.add_argument(
        "--update-config",
        action="store_true",
        help="Doplní nájdené field IDs do configs/clickup_custom_fields.yaml.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    load_dotenv()
    token = get_required_env("CLICKUP_API_TOKEN")

    if not args.list_id:
        workspace_id = get_required_env("CLICKUP_WORKSPACE_ID")
        workspace_snapshot = build_workspace_snapshot(workspace_id, token)
        output_path = QA_DIR / "clickup_workspace_discovery.json"
        save_json(output_path, workspace_snapshot)
        print(f"Workspace discovery uložený do: {output_path}")
        print("Pre ďalší krok spusti script s --list-id <ID>.")
        return

    workspace_id = os.environ.get("CLICKUP_WORKSPACE_ID", "").strip()
    fields = [normalize_field(field) for field in fetch_list_fields(args.list_id, token)]
    if workspace_id:
        fields = enrich_missing_dropdown_options(fields, workspace_id, token)

    field_snapshot = {
        "workspace_snapshot": {},
        "selected_list_id": args.list_id,
        "fields": fields,
    }
    output_path = QA_DIR / "clickup_live_field_discovery.json"
    save_json(output_path, field_snapshot)
    print(f"Live field discovery uložený do: {output_path}")

    if args.update_config:
        config_path, updated_names = update_custom_fields_config(
            CUSTOM_FIELDS_CONFIG_PATH,
            field_snapshot,
            args.list_id,
        )
        print(f"Config aktualizovaný: {config_path}")
        print("Aktualizované polia: " + (", ".join(updated_names) if updated_names else "žiadne"))


if __name__ == "__main__":
    main()
