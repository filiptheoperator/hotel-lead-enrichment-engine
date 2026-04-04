import csv
import json
import os
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml


ENV_PATH = Path(".env")
DRY_RUN_SAMPLE_PATH = Path("data/qa/clickup_import_dry_run_sample.csv")
CUSTOM_FIELDS_CONFIG_PATH = Path("configs/clickup_custom_fields.yaml")
OUTPUT_PATH = Path("data/qa/clickup_rehearsal_execution.json")
API_BASE = "https://api.clickup.com/api/v2"
MAX_ROWS = 3


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


def clickup_request(method: str, path: str, token: str, body: Optional[dict[str, Any]] = None) -> dict[str, Any]:
    data = None
    headers = {
        "Authorization": token,
        "Content-Type": "application/json",
    }
    if body is not None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")

    request = Request(
        f"{API_BASE}{path}",
        headers=headers,
        data=data,
        method=method,
    )

    try:
        with urlopen(request, timeout=30) as response:
            raw = response.read().decode("utf-8")
            return json.loads(raw) if raw else {}
    except HTTPError as error:
        body_text = error.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"ClickUp HTTP error {error.code}: {body_text}") from error
    except URLError as error:
        raise RuntimeError(f"ClickUp network error: {error.reason}") from error


def load_config(config_path: Path = CUSTOM_FIELDS_CONFIG_PATH) -> dict[str, Any]:
    if not config_path.exists():
        raise RuntimeError(f"Chýba config súbor: {config_path}")
    return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}


def load_sample_rows(csv_path: Path = DRY_RUN_SAMPLE_PATH, max_rows: int = MAX_ROWS) -> list[dict[str, str]]:
    if not csv_path.exists():
        raise RuntimeError(f"Chýba sample CSV: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    return rows[:max_rows]


def normalize_priority(value: str) -> Optional[int]:
    text = str(value).strip()
    if not text:
        return None
    return int(float(text))


def create_task(list_id: str, token: str, row: dict[str, str]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": row["Task name"],
        "description": row["Description content"],
        "status": row["Status"],
    }
    priority = normalize_priority(row["Priority"])
    if priority is not None:
        payload["priority"] = priority
    return clickup_request("POST", f"/list/{list_id}/task", token, payload)


def set_custom_field(task_id: str, field_id: str, token: str, value: str) -> dict[str, Any]:
    payload = {"value": value}
    return clickup_request("POST", f"/task/{task_id}/field/{field_id}", token, payload)


def get_task(task_id: str, token: str) -> dict[str, Any]:
    query = urlencode({"custom_task_ids": "false", "include_subtasks": "false"})
    return clickup_request("GET", f"/task/{task_id}?{query}", token)


def build_custom_field_values(row: dict[str, str], config: dict[str, Any]) -> list[dict[str, str]]:
    fields = config["clickup_custom_fields"]["fields"]
    mapping = [
        ("hotel_name", "Hotel name"),
        ("city", "City"),
        ("priority_score", "Priority score"),
        ("contact_phone", "Contact phone"),
        ("contact_website", "Contact website"),
        ("subject_line", "Subject line"),
        ("source_file", "Source file"),
    ]
    values: list[dict[str, str]] = []
    for field_key, csv_column in mapping:
        field_id = str(fields[field_key].get("clickup_field_id", "")).strip()
        if not field_id or field_id == "UNVERIFIED_TBD":
            raise RuntimeError(f"Field ID nie je potvrdený pre: {field_key}")
        values.append(
            {
                "field_key": field_key,
                "field_id": field_id,
                "field_name": str(fields[field_key].get("live_clickup_field_name") or fields[field_key].get("clickup_field_name")),
                "value": row[csv_column],
            }
        )
    return values


def verify_custom_fields(task_payload: dict[str, Any], expected_fields: list[dict[str, str]]) -> list[dict[str, Any]]:
    task_fields = {item.get("id"): item for item in task_payload.get("custom_fields", [])}
    results: list[dict[str, Any]] = []
    for expected in expected_fields:
        found = task_fields.get(expected["field_id"])
        actual_value = ""
        if found is not None and "value" in found and found["value"] is not None:
            actual_value = str(found["value"])
        expected_value = str(expected["value"])
        results.append(
            {
                "field_key": expected["field_key"],
                "field_id": expected["field_id"],
                "field_name": expected["field_name"],
                "expected_value": expected_value,
                "actual_value": actual_value,
                "match": actual_value == expected_value,
            }
        )
    return results


def main() -> None:
    load_dotenv()
    token = get_required_env("CLICKUP_API_TOKEN")
    config = load_config()
    list_id = str(config["clickup_custom_fields"].get("selected_test_list_id", "")).strip()
    if not list_id:
        raise RuntimeError("Chýba selected_test_list_id v clickup_custom_fields.yaml")

    rows = load_sample_rows()
    execution_rows: list[dict[str, Any]] = []

    payload: dict[str, Any] = {
        "list_id": list_id,
        "rehearsal_status": "PASS",
        "rows": execution_rows,
    }

    try:
        for index, row in enumerate(rows, start=1):
            created_task = create_task(list_id, token, row)
            task_id = str(created_task.get("id", "")).strip()
            custom_field_values = build_custom_field_values(row, config)

            for item in custom_field_values:
                set_custom_field(task_id, item["field_id"], token, item["value"])

            fetched_task = get_task(task_id, token)
            field_verification = verify_custom_fields(fetched_task, custom_field_values)

            execution_rows.append(
                {
                    "row_ref": f"row_{index}",
                    "task_id": task_id,
                    "task_name": row["Task name"],
                    "task_url": str(fetched_task.get("url", "")).strip(),
                    "status_sent": row["Status"],
                    "priority_sent": row["Priority"],
                    "name_match": str(fetched_task.get("name", "")).strip() == row["Task name"],
                    "description_match": str(fetched_task.get("description", "")).strip() == row["Description content"],
                    "field_verification": field_verification,
                }
            )

        payload["rehearsal_status"] = "PASS" if all(
            row["name_match"]
            and row["description_match"]
            and all(item["match"] for item in row["field_verification"])
            for row in execution_rows
        ) else "FAIL"
    except Exception as error:
        payload["rehearsal_status"] = "BLOCKED"
        payload["error"] = str(error)
        payload["partial_write_detected"] = len(execution_rows) > 0

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Rehearsal execution uložený do: {OUTPUT_PATH}")
    print(f"Rehearsal status: {payload['rehearsal_status']}")


if __name__ == "__main__":
    main()
