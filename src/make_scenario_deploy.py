import argparse
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import yaml


CONFIG_PATH = Path("configs/make_api.yaml")
ENV_PATH = Path(".env")


def load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return yaml.safe_load(path.read_text(encoding="utf-8")) or {}


def load_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def load_env_file(path: Path = ENV_PATH) -> dict[str, str]:
    if not path.exists():
        return {}
    values: dict[str, str] = {}
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def get_env_value(key: str, env_values: dict[str, str]) -> str:
    return str(os.environ.get(key, env_values.get(key, ""))).strip()


def save_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_runtime() -> dict[str, Any]:
    config = load_yaml(CONFIG_PATH).get("make_api", {})
    env_values = load_env_file()
    base_url = get_env_value(str(config.get("base_url_env_var", "MAKE_API_BASE_URL")), env_values) or "https://eu1.make.com/api/v2"
    token = get_env_value(str(config.get("token_env_var", "MAKE_API_TOKEN")), env_values)
    team_id = get_env_value(str(config.get("team_id_env_var", "MAKE_TEAM_ID")), env_values)
    scenario_id = get_env_value(str(config.get("scenario_id_env_var", "MAKE_SCENARIO_ID")), env_values)
    blueprint_path = Path(str(config.get("blueprint_path", "configs/make_scenario_blueprint.json")))
    blueprint = load_json(blueprint_path)
    placeholders = [item for item in config.get("required_blueprint_placeholders", []) if item in json.dumps(blueprint, ensure_ascii=False)]
    return {
        "config": config,
        "base_url": base_url.rstrip("/"),
        "token_present": bool(token),
        "token": token,
        "team_id": team_id,
        "scenario_id": scenario_id,
        "blueprint_path": str(blueprint_path),
        "blueprint": blueprint,
        "blueprint_placeholders": placeholders,
        "timeout_seconds": int(config.get("timeout_seconds", 30) or 30),
        "scenario_name": str(config.get("scenario_name", "Hotel Lead Enrichment Engine OS")).strip(),
        "scenario_folder_id": config.get("scenario_folder_id"),
        "activate_after_deploy": bool(config.get("activate_after_deploy", False)),
        "confirmed_installations": bool(config.get("confirmed_installations", False)),
        "result_path": Path(str(config.get("deploy_result_path", "data/qa/make_scenario_deploy_result.json"))),
    }


def api_request(
    runtime: dict[str, Any],
    method: str,
    path: str,
    body: Optional[dict[str, Any]] = None,
    query: Optional[dict[str, Any]] = None,
) -> dict[str, Any]:
    query_string = f"?{urlencode(query)}" if query else ""
    request = Request(
        f"{runtime['base_url']}{path}{query_string}",
        data=json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None,
        headers={
            "Authorization": f"Token {runtime['token']}",
            "Content-Type": "application/json",
        },
        method=method,
    )
    with urlopen(request, timeout=runtime["timeout_seconds"]) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return {
            "http_status": response.getcode(),
            "body": json.loads(raw) if raw else {},
        }


def build_plan(runtime: dict[str, Any]) -> dict[str, Any]:
    blueprint = runtime["blueprint"]
    return {
        "mode": "plan",
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "base_url": runtime["base_url"],
        "token_present": runtime["token_present"],
        "team_id_present": bool(runtime["team_id"]),
        "scenario_id_present": bool(runtime["scenario_id"]),
        "scenario_name": runtime["scenario_name"],
        "blueprint_path": runtime["blueprint_path"],
        "blueprint_status": blueprint.get("blueprint_status", ""),
        "blueprint_placeholders": runtime["blueprint_placeholders"],
        "actions": [
            "create_scenario_via_post_scenarios",
            "update_blueprint_via_patch_scenarios_id",
            "activate_scenario_via_post_scenarios_id_start",
        ],
        "ready_for_live_deploy": bool(runtime["token_present"] and runtime["team_id"] and not runtime["blueprint_placeholders"]),
    }


def create_scenario(runtime: dict[str, Any]) -> dict[str, Any]:
    if not runtime["team_id"]:
        raise RuntimeError("Chýba MAKE_TEAM_ID.")
    body = {
        "name": runtime["scenario_name"],
        "blueprint": json.dumps(runtime["blueprint"], ensure_ascii=False),
    }
    if runtime["scenario_folder_id"] is not None:
        body["folderId"] = runtime["scenario_folder_id"]
    return api_request(
        runtime,
        "POST",
        "/scenarios",
        body=body,
        query={
            "teamId": runtime["team_id"],
            "confirmed": "true" if runtime["confirmed_installations"] else "false",
        },
    )


def update_scenario(runtime: dict[str, Any]) -> dict[str, Any]:
    if not runtime["scenario_id"]:
        raise RuntimeError("Chýba MAKE_SCENARIO_ID.")
    body = {
        "name": runtime["scenario_name"],
        "blueprint": json.dumps(runtime["blueprint"], ensure_ascii=False),
    }
    return api_request(
        runtime,
        "PATCH",
        f"/scenarios/{runtime['scenario_id']}",
        body=body,
        query={"confirmed": "true" if runtime["confirmed_installations"] else "false"},
    )


def activate_scenario(runtime: dict[str, Any]) -> dict[str, Any]:
    if not runtime["scenario_id"]:
        raise RuntimeError("Chýba MAKE_SCENARIO_ID.")
    return api_request(runtime, "POST", f"/scenarios/{runtime['scenario_id']}/start")


def main() -> None:
    parser = argparse.ArgumentParser(description="Make scenario provisioning helper.")
    parser.add_argument("--mode", choices=["plan", "create", "update", "activate"], default="plan")
    args = parser.parse_args()

    runtime = build_runtime()
    result: dict[str, Any] = {
        "mode": args.mode,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "success": False,
        "ready_for_live_deploy": False,
    }
    try:
        if args.mode == "plan":
            result = build_plan(runtime)
            result["success"] = True
        else:
            if not runtime["token_present"]:
                raise RuntimeError("Chýba MAKE_API_TOKEN.")
            if runtime["blueprint_placeholders"]:
                raise RuntimeError("Blueprint stále obsahuje neoverené placeholdery.")
            if args.mode == "create":
                result["api_result"] = create_scenario(runtime)
            elif args.mode == "update":
                result["api_result"] = update_scenario(runtime)
            elif args.mode == "activate":
                result["api_result"] = activate_scenario(runtime)
            result["success"] = True
            result["ready_for_live_deploy"] = True
    except HTTPError as error:
        result["error"] = f"HTTP {error.code}"
        result["response_body"] = error.read().decode("utf-8", errors="replace")
    except URLError as error:
        result["error"] = f"Network error: {error.reason}"
    except Exception as error:  # noqa: BLE001
        result["error"] = str(error)

    save_json(runtime["result_path"], result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
