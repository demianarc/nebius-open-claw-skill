#!/usr/bin/env python3
"""
Discover Nebius Token Factory models and wire them into OpenClaw.

Default behavior is safe: print the exact `openclaw config set` commands that
would be executed. Pass --apply to run them.
"""

from __future__ import annotations

import argparse
import json
import os
import shlex
import shutil
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request

DEFAULT_BASE_URL = "https://api.tokenfactory.nebius.com/v1/"
DEFAULT_PROVIDER_ID = "nebius"
DEFAULT_ENV_VARS = ("NEBIUS_API_KEY", "NEBIUS_TOKEN_FACTORY_API_KEY")
DEFAULT_MODELS = (
    ("moonshotai/Kimi-K2.5", "kimi"),
    ("meta-llama/Llama-3.3-70B-Instruct-fast", "llama70b"),
    ("deepseek-ai/DeepSeek-R1-0528", "deepseek"),
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Configure OpenClaw to use Nebius Token Factory."
    )
    parser.add_argument(
        "--base-url",
        default=DEFAULT_BASE_URL,
        help="Token Factory base URL. Defaults to the global Nebius endpoint.",
    )
    parser.add_argument(
        "--provider-id",
        default=DEFAULT_PROVIDER_ID,
        help="Provider id to write under models.providers.",
    )
    parser.add_argument(
        "--env-var",
        default="",
        help="Explicit env var name for the API key. Defaults to NEBIUS_API_KEY, then NEBIUS_TOKEN_FACTORY_API_KEY.",
    )
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List live Token Factory models and exit.",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Skip live model discovery. Requires explicit --model values.",
    )
    parser.add_argument(
        "--model",
        action="append",
        default=[],
        metavar="MODEL_ID[:ALIAS]",
        help="Model id plus optional alias. Repeat to add multiple models.",
    )
    parser.add_argument(
        "--primary-model",
        default="",
        help="Primary OpenClaw model id. Defaults to the first selected model.",
    )
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Run the generated openclaw config commands.",
    )
    parser.add_argument(
        "--restart",
        action="store_true",
        help="Restart the OpenClaw gateway after applying config.",
    )
    return parser.parse_args()


def normalize_base_url(url: str) -> str:
    trimmed = url.strip()
    if not trimmed:
        raise ValueError("Base URL cannot be empty.")
    trimmed = trimmed.rstrip("/")
    if not trimmed.endswith("/v1"):
        trimmed += "/v1"
    return trimmed + "/"


def discover_env_var(explicit: str) -> tuple[str, str]:
    candidates = [explicit] if explicit else list(DEFAULT_ENV_VARS)
    for name in candidates:
        if name and os.environ.get(name):
            return name, os.environ[name]
    expected = explicit or " or ".join(DEFAULT_ENV_VARS)
    raise SystemExit(
        f"Missing API key. Export {expected} before running this script."
    )


def fetch_models(base_url: str, api_key: str) -> list[dict]:
    url = urllib.parse.urljoin(base_url, "models?verbose=true")
    request = urllib.request.Request(
        url,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Accept": "application/json",
            "User-Agent": "openclaw-nebius-skill/1.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=20) as response:
            payload = json.load(response)
    except urllib.error.HTTPError as exc:
        message = exc.read().decode("utf-8", errors="replace").strip()
        raise SystemExit(f"Token Factory request failed: {exc.code} {message}") from exc
    except urllib.error.URLError as exc:
        raise SystemExit(f"Token Factory request failed: {exc.reason}") from exc

    if isinstance(payload, dict):
        items = payload.get("data", payload.get("models", payload))
        if isinstance(items, list):
            return [item for item in items if isinstance(item, dict)]
    if isinstance(payload, list):
        return [item for item in payload if isinstance(item, dict)]
    raise SystemExit("Unexpected /models response format from Token Factory.")


def normalize_model_id(model_id: str) -> str:
    return "".join(ch.lower() for ch in model_id if ch.isalnum())


def model_context_window(model: dict) -> int | None:
    for key in ("contextWindow", "context_window", "contextLength", "context_length"):
        value = model.get(key)
        if isinstance(value, int):
            return value
    return None


def parse_requested_models(values: list[str]) -> list[tuple[str, str | None]]:
    parsed: list[tuple[str, str | None]] = []
    for value in values:
        raw = value.strip()
        if not raw:
            continue
        if ":" in raw:
            model_id, alias = raw.split(":", 1)
            parsed.append((model_id.strip(), alias.strip() or None))
        else:
            parsed.append((raw, None))
    return parsed


def fuzzy_lookup(available: list[dict], wanted_id: str) -> dict | None:
    wanted_norm = normalize_model_id(wanted_id)
    for model in available:
        model_id = str(model.get("id", ""))
        if model_id == wanted_id:
            return model
    for model in available:
        model_id = str(model.get("id", ""))
        if normalize_model_id(model_id) == wanted_norm:
            return model
    for model in available:
        model_id = str(model.get("id", ""))
        if normalize_model_id(model_id).startswith(wanted_norm):
            return model
    return None


def infer_reasoning(model_id: str) -> bool:
    lowered = model_id.lower()
    return "deepseek-r1" in lowered or "reasoning" in lowered or "thinking" in lowered


def pretty_name(model_id: str) -> str:
    tail = model_id.split("/")[-1]
    return tail.replace("-", " ")


def select_models(
    available: list[dict], requested: list[tuple[str, str | None]]
) -> list[dict]:
    selected: list[dict] = []

    if requested:
        for wanted_id, alias in requested:
            match = fuzzy_lookup(available, wanted_id) if available else None
            model_id = match.get("id", wanted_id) if match else wanted_id
            selected.append(
                {
                    "id": model_id,
                    "alias": alias,
                    "name": (match or {}).get("name") or pretty_name(model_id),
                    "contextWindow": model_context_window(match or {}),
                    "reasoning": infer_reasoning(model_id),
                }
            )
        return selected

    for wanted_id, alias in DEFAULT_MODELS:
        match = fuzzy_lookup(available, wanted_id)
        if not match:
            continue
        model_id = str(match.get("id", wanted_id))
        selected.append(
            {
                "id": model_id,
                "alias": alias,
                "name": match.get("name") or pretty_name(model_id),
                "contextWindow": model_context_window(match),
                "reasoning": infer_reasoning(model_id),
            }
        )

    if selected:
        return selected

    raise SystemExit(
        "Could not infer a good default model set from Token Factory. "
        "Run with --list-models and pass explicit --model MODEL_ID[:ALIAS] values."
    )


def unique_models(items: list[dict]) -> list[dict]:
    deduped: list[dict] = []
    seen: set[str] = set()
    for item in items:
        model_id = item["id"]
        if model_id in seen:
            continue
        seen.add(model_id)
        deduped.append(item)
    return deduped


def build_provider_models(selected: list[dict]) -> list[dict]:
    output: list[dict] = []
    for item in selected:
        entry = {
            "id": item["id"],
            "name": item["name"],
        }
        if item.get("contextWindow"):
            entry["contextWindow"] = item["contextWindow"]
        if item.get("reasoning"):
            entry["reasoning"] = True
        output.append(entry)
    return output


def build_allowlist(provider_id: str, selected: list[dict]) -> dict:
    allowlist = {}
    for item in selected:
        alias = item.get("alias")
        key = f"{provider_id}/{item['id']}"
        allowlist[key] = {"alias": alias or item["id"].split("/")[-1].lower()}
    return allowlist


def merge_provider_models(existing: object, selected: list[dict]) -> list[dict]:
    merged: list[dict] = []
    by_id: dict[str, dict] = {}

    if isinstance(existing, list):
        for item in existing:
            if not isinstance(item, dict):
                continue
            model_id = str(item.get("id", "")).strip()
            if not model_id:
                continue
            copy = dict(item)
            by_id[model_id] = copy
            merged.append(copy)

    for item in build_provider_models(selected):
        model_id = item["id"]
        if model_id in by_id:
            by_id[model_id].update(item)
            continue
        by_id[model_id] = dict(item)
        merged.append(by_id[model_id])

    return merged


def merge_allowlist(existing: object, provider_id: str, selected: list[dict]) -> dict:
    merged = dict(existing) if isinstance(existing, dict) else {}
    merged.update(build_allowlist(provider_id, selected))
    return merged


def current_json_value(path: str, default: object) -> object:
    if shutil.which("openclaw") is None:
        return default
    command = ["openclaw", "config", "get", path, "--json"]
    result = subprocess.run(
        command,
        check=False,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return default
    payload = result.stdout.strip()
    if not payload:
        return default
    try:
        return json.loads(payload)
    except json.JSONDecodeError:
        return default


def build_batch_operations(
    provider_id: str,
    provider_config: dict,
    allowlist: dict,
    primary_model_id: str,
) -> list[dict]:
    primary_ref = f"{provider_id}/{primary_model_id}"
    return [
        {"path": "models.mode", "value": "merge"},
        {"path": f"models.providers.{provider_id}", "value": provider_config},
        {"path": "agents.defaults.model.primary", "value": primary_ref},
        {"path": "agents.defaults.models", "value": allowlist},
    ]


def build_commands(batch_operations: list[dict]) -> list[list[str]]:
    return [
        [
            "openclaw",
            "config",
            "set",
            "--batch-json",
            json.dumps(batch_operations, separators=(",", ":")),
        ]
    ]


def print_model_table(models: list[dict]) -> None:
    print("Available Token Factory models:")
    for model in models:
        model_id = str(model.get("id", ""))
        if not model_id:
            continue
        window = model_context_window(model)
        suffix = f"  context={window}" if window else ""
        print(f"- {model_id}{suffix}")


def run_commands(commands: list[list[str]], restart: bool) -> None:
    if shutil.which("openclaw") is None:
        raise SystemExit(
            "openclaw is not installed. Install it first with `npm install -g @openclaw/cli`."
        )

    for command in commands:
        print("+", shlex.join(command))
        subprocess.run(command, check=True)

    if restart:
        restart_cmd = ["openclaw", "gateway", "restart"]
        print("+", shlex.join(restart_cmd))
        subprocess.run(restart_cmd, check=True)


def main() -> None:
    args = parse_args()
    base_url = normalize_base_url(args.base_url)
    env_var, api_key = discover_env_var(args.env_var)
    live_models: list[dict] = []

    if args.list_models:
        live_models = fetch_models(base_url, api_key)
        print_model_table(live_models)
        return

    if args.offline and not args.model:
        raise SystemExit("--offline requires at least one --model MODEL_ID[:ALIAS].")

    if not args.offline:
        live_models = fetch_models(base_url, api_key)

    requested = parse_requested_models(args.model)
    selected = unique_models(select_models(live_models, requested))
    primary_model_id = args.primary_model or selected[0]["id"]

    if not any(item["id"] == primary_model_id for item in selected):
        selected.insert(
            0,
            {
                "id": primary_model_id,
                "alias": None,
                "name": pretty_name(primary_model_id),
                "contextWindow": None,
                "reasoning": infer_reasoning(primary_model_id),
            },
        )
        selected = unique_models(selected)

    existing_provider_config = current_json_value(
        f"models.providers.{args.provider_id}", {}
    )
    provider_models = merge_provider_models(
        (existing_provider_config or {}).get("models", [])
        if isinstance(existing_provider_config, dict)
        else [],
        selected,
    )
    allowlist = merge_allowlist(
        current_json_value("agents.defaults.models", {}),
        args.provider_id,
        selected,
    )
    provider_config = (
        dict(existing_provider_config) if isinstance(existing_provider_config, dict) else {}
    )
    provider_config.update(
        {
            "baseUrl": base_url,
            "apiKey": "${" + env_var + "}",
            "api": "openai-completions",
            "models": provider_models,
        }
    )
    batch_operations = build_batch_operations(
        provider_id=args.provider_id,
        provider_config=provider_config,
        allowlist=allowlist,
        primary_model_id=primary_model_id,
    )

    commands = build_commands(batch_operations)

    print("Selected Nebius models:")
    for item in selected:
        alias = f" alias={item['alias']}" if item.get("alias") else ""
        primary = " primary" if item["id"] == primary_model_id else ""
        print(f"- {item['id']}{alias}{primary}")

    print("\nOpenClaw config commands:")
    for command in commands:
        print(shlex.join(command))

    if args.apply:
        print()
        run_commands(commands, restart=args.restart)
    else:
        print(
            "\nNo changes were applied. Re-run with --apply to execute the commands."
        )

    print("\nVerify with:")
    for command in (
        "openclaw models list",
        "openclaw models status",
        "openclaw dashboard",
    ):
        print(command)


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as exc:
        sys.exit(exc.returncode)
