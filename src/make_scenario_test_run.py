import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Optional
from urllib.error import HTTPError, URLError

from make_scenario_deploy import api_request, build_runtime, save_json


def build_plan(runtime: dict[str, Any], mode: str) -> dict[str, Any]:
    return {
        "mode": mode,
        "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"),
        "scenario_id_present": bool(runtime["scenario_id"]),
        "token_present": runtime["token_present"],
        "base_url": runtime["base_url"],
        "ready_for_live_test": bool(runtime["token_present"] and runtime["scenario_id"]),
    }


def get_interface(runtime: dict[str, Any]) -> dict[str, Any]:
    return api_request(runtime, "GET", f"/scenarios/{runtime['scenario_id']}/interface")


def get_logs(runtime: dict[str, Any]) -> dict[str, Any]:
    return api_request(runtime, "GET", f"/scenarios/{runtime['scenario_id']}/logs")


def run_scenario(runtime: dict[str, Any], input_payload: dict[str, Any]) -> dict[str, Any]:
    return api_request(runtime, "POST", f"/scenarios/{runtime['scenario_id']}/run", body={"input": input_payload})


def load_input_payload(path: Optional[Path]) -> dict[str, Any]:
    if not path or not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> None:
    parser = argparse.ArgumentParser(description="Make scenario test helper.")
    parser.add_argument("--mode", choices=["plan", "interface", "logs", "run"], default="plan")
    parser.add_argument("--input-json", default="", help="Voliteľný JSON payload pre run režim.")
    args = parser.parse_args()

    runtime = build_runtime()
    result_path = Path(str(runtime["config"].get("test_result_path", "data/qa/make_scenario_test_result.json")))
    result: dict[str, Any] = {"mode": args.mode, "timestamp": datetime.now().astimezone().isoformat(timespec="seconds"), "success": False}

    try:
        if args.mode == "plan":
            result = build_plan(runtime, args.mode)
            result["success"] = True
        else:
            if not runtime["token_present"]:
                raise RuntimeError("Chýba MAKE_API_TOKEN.")
            if not runtime["scenario_id"]:
                raise RuntimeError("Chýba MAKE_SCENARIO_ID.")
            if args.mode == "interface":
                result["api_result"] = get_interface(runtime)
            elif args.mode == "logs":
                result["api_result"] = get_logs(runtime)
            elif args.mode == "run":
                input_payload = load_input_payload(Path(args.input_json)) if args.input_json else {}
                result["input_payload_keys"] = sorted(input_payload.keys())
                result["api_result"] = run_scenario(runtime, input_payload)
            result["success"] = True
    except HTTPError as error:
        result["error"] = f"HTTP {error.code}"
        result["response_body"] = error.read().decode("utf-8", errors="replace")
    except URLError as error:
        result["error"] = f"Network error: {error.reason}"
    except Exception as error:  # noqa: BLE001
        result["error"] = str(error)

    save_json(result_path, result)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
