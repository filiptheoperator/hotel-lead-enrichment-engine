import argparse
import json
import os
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


ENV_PATH = Path(".env")


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


def env_value(key: str, env_values: dict[str, str]) -> str:
    return str(os.environ.get(key, env_values.get(key, ""))).strip()


def api_get(base_url: str, token: str, path: str, query: dict[str, str]) -> dict:
    request = Request(
        f"{base_url.rstrip('/')}{path}?{urlencode(query)}",
        headers={"Authorization": f"Token {token}"},
        method="GET",
    )
    with urlopen(request, timeout=30) as response:
        raw = response.read().decode("utf-8", errors="replace")
        return json.loads(raw) if raw else {}


def main() -> None:
    parser = argparse.ArgumentParser(description="Tiny helper pre Make IDs.")
    parser.add_argument("--mode", choices=["teams", "folders"], required=True)
    args = parser.parse_args()

    env_values = load_env_file()
    token = env_value("MAKE_API_TOKEN", env_values)
    base_url = env_value("MAKE_API_BASE_URL", env_values) or "https://eu1.make.com/api/v2"
    organization_id = env_value("MAKE_ORGANIZATION_ID", env_values)
    team_id = env_value("MAKE_TEAM_ID", env_values)

    if not token:
        raise SystemExit("Chýba MAKE_API_TOKEN v .env")

    try:
        if args.mode == "teams":
            if not organization_id:
                raise SystemExit("Chýba MAKE_ORGANIZATION_ID v .env")
            payload = api_get(base_url, token, "/teams", {"organizationId": organization_id})
        else:
            if not team_id:
                raise SystemExit("Chýba MAKE_TEAM_ID v .env")
            payload = api_get(base_url, token, "/scenarios-folders", {"teamId": team_id})
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    except HTTPError as error:
        print(json.dumps({"error": f"HTTP {error.code}", "body": error.read().decode('utf-8', errors='replace')}, ensure_ascii=False, indent=2))
        raise SystemExit(1)
    except URLError as error:
        print(json.dumps({"error": f"Network error: {error.reason}"}, ensure_ascii=False, indent=2))
        raise SystemExit(1)


if __name__ == "__main__":
    main()
