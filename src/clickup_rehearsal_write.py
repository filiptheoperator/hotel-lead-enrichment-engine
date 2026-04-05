import argparse
import csv
import json
import os
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml

from clickup_export import get_clickup_export_mode


ENV_PATH = Path(".env")
DRY_RUN_SAMPLE_PATH = Path("data/qa/clickup_import_dry_run_sample.csv")
CUSTOM_FIELDS_CONFIG_PATH = Path("configs/clickup_custom_fields.yaml")
DROPDOWN_NORMALIZATION_CONFIG_PATH = Path("configs/clickup_dropdown_normalization.yaml")
OUTPUT_PATH = Path("data/qa/clickup_rehearsal_execution.json")
API_BASE = "https://api.clickup.com/api/v2"
MAX_ROWS = 3
VERIFY_MODES = {"full", "sample", "none"}


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


def load_dropdown_normalization_config(
    config_path: Path = DROPDOWN_NORMALIZATION_CONFIG_PATH,
) -> dict[str, Any]:
    if not config_path.exists():
        return {}
    return yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}


def load_sample_rows(csv_path: Path = DRY_RUN_SAMPLE_PATH, max_rows: int = MAX_ROWS) -> list[dict[str, str]]:
    if not csv_path.exists():
        raise RuntimeError(f"Chýba sample CSV: {csv_path}")
    with csv_path.open(newline="", encoding="utf-8") as file:
        rows = list(csv.DictReader(file))
    return rows if max_rows <= 0 else rows[:max_rows]


def normalize_priority(value: str) -> Optional[int]:
    text = str(value).strip()
    if not text:
        return None
    return int(float(text))


def create_task(list_id: str, token: str, row: dict[str, str]) -> dict[str, Any]:
    payload: dict[str, Any] = {
        "name": row["Task name"],
        "status": row["Status"],
    }
    description = str(row.get("Description content", "")).strip()
    if description:
        payload["description"] = description
    priority = normalize_priority(row["Priority"])
    if priority is not None:
        payload["priority"] = priority
    return clickup_request("POST", f"/list/{list_id}/task", token, payload)


def set_custom_field(task_id: str, token: str, field: dict[str, Any]) -> dict[str, Any]:
    field_id = str(field.get("field_id", "")).strip()
    value = str(field.get("value", ""))
    payload = {"value": value}
    field_type = str(field.get("field_type", "")).strip()
    option_ids = field.get("option_ids", {}) or {}
    if field_type == "drop_down":
        mapped_option_id = str(option_ids.get(value, "")).strip()
        if mapped_option_id and mapped_option_id != "UNVERIFIED_TBD":
            payload = {"value": mapped_option_id}
    return clickup_request("POST", f"/task/{task_id}/field/{field_id}", token, payload)


def get_task(task_id: str, token: str) -> dict[str, Any]:
    query = urlencode({"custom_task_ids": "false", "include_subtasks": "false"})
    return clickup_request("GET", f"/task/{task_id}?{query}", token)


def build_custom_field_values(row: dict[str, str], config: dict[str, Any]) -> list[dict[str, str]]:
    fields = config["clickup_custom_fields"]["fields"]
    required_mapping = [
        ("hotel_name", "Hotel name"),
        ("city", "City / Region"),
        ("priority_score", "Priority score"),
        ("contact_phone", "Contact phone"),
        ("contact_website", "Contact website"),
        ("subject_line", "Subject line"),
        ("source_file", "Source file"),
    ]
    optional_mapping = [
        ("account_status", "Account Status"),
        ("country", "Country"),
        ("hotel_type", "Hotel Type"),
        ("rooms_range", "Rooms Range"),
        ("source", "Source"),
        ("priority_level", "Priority Level"),
        ("icp_fit", "ICP Fit"),
        ("main_pain_hypothesis", "Main Pain Hypothesis"),
    ]
    values: list[dict[str, str]] = []
    for field_key, csv_column in required_mapping:
        field_id = str(fields[field_key].get("clickup_field_id", "")).strip()
        if not field_id or field_id == "UNVERIFIED_TBD":
            raise RuntimeError(f"Field ID nie je potvrdený pre: {field_key}")
        values.append(
            {
                "field_key": field_key,
                "field_id": field_id,
                "field_name": str(fields[field_key].get("live_clickup_field_name") or fields[field_key].get("clickup_field_name")),
                "field_type": str(fields[field_key].get("clickup_field_type", "")),
                "option_ids": fields[field_key].get("clickup_option_ids", {}) or {},
                "option_orderindex": fields[field_key].get("clickup_option_orderindex", {}) or {},
                "value": row.get(csv_column, row.get("City", "")) if field_key == "city" else row.get(csv_column, ""),
            }
        )
    for field_key, csv_column in optional_mapping:
        item = fields.get(field_key, {})
        field_id = str(item.get("clickup_field_id", "")).strip()
        if not field_id or field_id == "UNVERIFIED_TBD":
            continue
        values.append(
            {
                "field_key": field_key,
                "field_id": field_id,
                "field_name": str(item.get("live_clickup_field_name") or item.get("clickup_field_name")),
                "field_type": str(item.get("clickup_field_type", "")),
                "option_ids": item.get("clickup_option_ids", {}) or {},
                "option_orderindex": item.get("clickup_option_orderindex", {}) or {},
                "value": row.get(csv_column, ""),
            }
        )
    return values


def normalize_dropdown_value(field: dict[str, Any], normalization_root: dict[str, Any]) -> Optional[str]:
    field_key = str(field.get("field_key", "")).strip()
    field_type = str(field.get("field_type", "")).strip()
    raw_value = str(field.get("value", "")).strip()
    if field_type != "drop_down":
        return raw_value

    field_rules = (normalization_root.get("clickup_dropdown_normalization", {}) or {}).get(field_key, {}) or {}
    mappings = field_rules.get("mappings", {}) or {}
    fallback = str(field_rules.get("fallback", "")).strip()
    option_ids = field.get("option_ids", {}) or {}

    if raw_value in mappings:
        normalized_value = str(mappings.get(raw_value, "")).strip()
    elif raw_value and raw_value in option_ids:
        normalized_value = raw_value
    else:
        normalized_value = ""
    if normalized_value:
        return normalized_value
    if fallback:
        return fallback
    return None


def verify_custom_fields(task_payload: dict[str, Any], expected_fields: list[dict[str, str]]) -> list[dict[str, Any]]:
    task_fields = {item.get("id"): item for item in task_payload.get("custom_fields", [])}
    results: list[dict[str, Any]] = []
    for expected in expected_fields:
        found = task_fields.get(expected["field_id"])
        actual_value = ""
        if found is not None and "value" in found and found["value"] is not None:
            actual_value = str(found["value"])
        expected_value = str(expected["value"])
        field_type = str(expected.get("field_type", "")).strip()
        option_ids = expected.get("option_ids", {}) or {}
        option_orderindex = expected.get("option_orderindex", {}) or {}
        match = actual_value == expected_value
        if field_type == "drop_down":
            expected_option_id = str(option_ids.get(expected_value, "")).strip()
            expected_orderindex = str(option_orderindex.get(expected_value, "")).strip()
            match = actual_value in {expected_value, expected_option_id, expected_orderindex}
        results.append(
            {
                "field_key": expected["field_key"],
                "field_id": expected["field_id"],
                "field_name": expected["field_name"],
                "expected_value": expected_value,
                "actual_value": actual_value,
                "match": match,
            }
        )
    return results


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Controlled ClickUp write for demo or rehearsal.")
    parser.add_argument(
        "--csv",
        dest="csv_path",
        default=str(DRY_RUN_SAMPLE_PATH),
        help="Vstupný ClickUp-ready CSV súbor.",
    )
    parser.add_argument(
        "--max-rows",
        dest="max_rows",
        type=int,
        default=MAX_ROWS,
        help="Počet riadkov na zápis. 0 = všetky riadky.",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        default=str(OUTPUT_PATH),
        help="Kam uložiť JSON výsledok.",
    )
    parser.add_argument(
        "--verify-mode",
        dest="verify_mode",
        default="full",
        choices=sorted(VERIFY_MODES),
        help="Režim overenia: full / sample / none.",
    )
    parser.add_argument(
        "--verify-sample-size",
        dest="verify_sample_size",
        type=int,
        default=5,
        help="Koľko riadkov overiť pri sample režime.",
    )
    parser.add_argument(
        "--progress-every",
        dest="progress_every",
        type=int,
        default=25,
        help="Po koľkých riadkoch vypísať progress.",
    )
    return parser


def build_verify_index_set(row_count: int, verify_mode: str, verify_sample_size: int) -> set[int]:
    if verify_mode == "full":
        return set(range(1, row_count + 1))
    if verify_mode == "none" or row_count <= 0:
        return set()
    sample_size = max(1, min(verify_sample_size, row_count))
    if sample_size >= row_count:
        return set(range(1, row_count + 1))
    first_half = max(1, sample_size // 2)
    last_half = sample_size - first_half
    indices = set(range(1, first_half + 1))
    indices.update(range(row_count - last_half + 1, row_count + 1))
    return indices


def main() -> None:
    args = build_parser().parse_args()
    load_dotenv()
    token = get_required_env("CLICKUP_API_TOKEN")
    config = load_config()
    dropdown_normalization = load_dropdown_normalization_config()
    export_mode = get_clickup_export_mode()
    list_id = str(config["clickup_custom_fields"].get("selected_test_list_id", "")).strip()
    if not list_id:
        raise RuntimeError("Chýba selected_test_list_id v clickup_custom_fields.yaml")

    input_csv_path = Path(args.csv_path)
    output_path = Path(args.output_path)
    rows = load_sample_rows(input_csv_path, args.max_rows)
    execution_rows: list[dict[str, Any]] = []

    payload: dict[str, Any] = {
        "list_id": list_id,
        "clickup_export_mode": export_mode,
        "source_csv": str(input_csv_path),
        "requested_rows": len(rows),
        "verify_mode": args.verify_mode,
        "verify_sample_size": args.verify_sample_size,
        "rehearsal_status": "PASS",
        "rows": execution_rows,
    }
    verify_indices = build_verify_index_set(len(rows), args.verify_mode, args.verify_sample_size)

    try:
        for index, row in enumerate(rows, start=1):
            created_task = create_task(list_id, token, row)
            task_id = str(created_task.get("id", "")).strip()
            custom_field_values = build_custom_field_values(row, config)

            for item in custom_field_values:
                normalized_value = normalize_dropdown_value(item, dropdown_normalization)
                if normalized_value is None:
                    continue
                item["value"] = normalized_value
                set_custom_field(task_id, token, item)

            row_payload: dict[str, Any] = {
                "row_ref": f"row_{index}",
                "task_id": task_id,
                "task_name": row["Task name"],
                "status_sent": row["Status"],
                "priority_sent": row["Priority"],
                "verified": index in verify_indices,
            }

            if index in verify_indices:
                fetched_task = get_task(task_id, token)
                field_verification = verify_custom_fields(fetched_task, custom_field_values)
                row_payload.update(
                    {
                        "task_url": str(fetched_task.get("url", "")).strip(),
                        "name_match": str(fetched_task.get("name", "")).strip() == row["Task name"],
                        "description_expected": str(row.get("Description content", "")).strip(),
                        "description_match": (
                            str(fetched_task.get("description", "")).strip() == str(row.get("Description content", "")).strip()
                            if str(row.get("Description content", "")).strip()
                            else True
                        ),
                        "field_verification": field_verification,
                    }
                )
            else:
                row_payload.update(
                    {
                        "task_url": "",
                        "name_match": None,
                        "description_expected": str(row.get("Description content", "")).strip(),
                        "description_match": None,
                        "field_verification": [],
                    }
                )

            execution_rows.append(row_payload)

            if args.progress_every > 0 and index % args.progress_every == 0:
                print(f"Progress: {index}/{len(rows)}")

        verified_rows = [row for row in execution_rows if row.get("verified")]
        payload["verified_row_count"] = len(verified_rows)
        payload["created_task_count"] = len(execution_rows)
        payload["rehearsal_status"] = "PASS" if all(
            row["name_match"]
            and row["description_match"]
            and all(item["match"] for item in row["field_verification"])
            for row in verified_rows
        ) else "FAIL"
    except Exception as error:
        payload["rehearsal_status"] = "BLOCKED"
        payload["error"] = str(error)
        payload["partial_write_detected"] = len(execution_rows) > 0

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Rehearsal execution uložený do: {output_path}")
    print(f"Rehearsal status: {payload['rehearsal_status']}")


if __name__ == "__main__":
    main()
