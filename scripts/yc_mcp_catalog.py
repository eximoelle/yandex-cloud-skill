#!/usr/bin/env python3
"""Manifest-first YC skill CLI for MCP catalog management and derived docs."""

from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import subprocess
import time
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import yaml
from jsonschema import Draft202012Validator


REPO_ROOT = Path(__file__).resolve().parent.parent

MANIFEST_PATH_DEFAULT = Path("references/contracts/skill_manifest.yaml")
MANIFEST_SCHEMA_PATH_DEFAULT = Path("references/contracts/skill_manifest.schema.json")
MCP_CATALOG_PATH_DEFAULT = Path("references/mcp/catalog.yaml")
MCP_CATALOG_SCHEMA_PATH_DEFAULT = Path("references/contracts/mcp_catalog.schema.json")
MCP_REGISTRY_PATH_DEFAULT = Path("references/mcp/registry.md")
MCP_CODEX_SETUP_PATH_DEFAULT = Path("references/mcp/codex-setup.md")
NAVIGATION_PATH_DEFAULT = Path("references/navigation.md")

REPO_API_SERVERS_URL = "https://api.github.com/repos/yandex-cloud/mcp/contents/servers"
RAW_README_URL_TEMPLATE = (
    "https://raw.githubusercontent.com/yandex-cloud/mcp/master/servers/{server}/README.md"
)

AUTH_MODES = {"none", "iam_token", "other", "unknown"}
HEADER_MODES = {"required", "optional", "unsupported"}
TRANSPORT_MODES = {"http", "stdio"}
STATUS_MODES = {"active", "experimental", "deprecated"}

NO_MATCH_ERROR = (
    "No MCP server matched requested tags. Refresh catalog or continue in non-MCP mode."
)


@dataclass
class ResolveResult:
    server: dict[str, Any]
    matched_tags: list[str]


@dataclass
class NonMCPFallback:
    mode: str
    selection_principle: str
    reason: str
    task_type: str
    service: str
    intent: str
    operation: str
    workflow_hint: str
    interfaces: list[str]
    context_sources: list[str]
    official_sources: list[str]
    next_steps: list[str]


def _now_date() -> str:
    return datetime.now(UTC).date().isoformat()


def _resolve_path(path_value: str | Path) -> Path:
    path = Path(path_value)
    if path.is_absolute():
        return path
    if path.exists():
        return path
    return REPO_ROOT / path


def _normalize_tag(tag: str) -> str:
    return tag.strip().lower().replace("_", "-")


def _normalize_service(value: str) -> str:
    return value.strip().lower().replace("_", "-")


def _normalize_task_type(value: str) -> str:
    return value.strip().lower().replace("-", "_")


def _normalize_operation(value: str | None) -> str:
    return (value or "").strip().lower().replace("-", "_")


def _normalize_intents(values: list[str]) -> list[str]:
    normalized = {_normalize_tag(item) for item in values if _normalize_tag(item)}
    return sorted(normalized)


def _error(code: str, message: str, details: dict[str, Any] | None = None) -> dict[str, Any]:
    payload: dict[str, Any] = {"code": code, "message": message}
    if details is not None:
        payload["details"] = details
    return payload


def _envelope(
    *,
    status: str,
    data: dict[str, Any] | None = None,
    checks: list[str] | None = None,
    limitations: list[str] | None = None,
    sources: list[str] | None = None,
    errors: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    return {
        "version": "2.0",
        "status": status,
        "data": data or {},
        "checks": checks or [],
        "limitations": limitations or [],
        "sources": sources or [],
        "errors": errors or [],
    }


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2))


def _load_json(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    parsed = json.loads(raw)
    if not isinstance(parsed, dict):
        raise ValueError(f"JSON at {path} must be an object")
    return parsed


def _load_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    parsed = yaml.safe_load(path.read_text(encoding="utf-8"))
    if parsed is None:
        return {}
    if not isinstance(parsed, dict):
        raise ValueError(f"YAML at {path} must be a mapping")
    return parsed


def _dump_yaml(data: dict[str, Any], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump(data, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )


def _schema_errors(data: dict[str, Any], schema: dict[str, Any]) -> list[str]:
    validator = Draft202012Validator(schema, format_checker=Draft202012Validator.FORMAT_CHECKER)
    items: list[str] = []
    for err in validator.iter_errors(data):
        path = ".".join(str(part) for part in err.path)
        location = path if path else "$"
        items.append(f"{location}: {err.message}")
    return sorted(items)


def _load_manifest(
    manifest_path: Path,
    manifest_schema_path: Path,
) -> tuple[dict[str, Any], list[str]]:
    manifest = _load_yaml(manifest_path)
    schema = _load_json(manifest_schema_path)
    errors = _schema_errors(manifest, schema)
    return manifest, errors


def _load_catalog(
    catalog_path: Path,
    catalog_schema_path: Path,
) -> tuple[dict[str, Any], list[str]]:
    catalog = _load_yaml(catalog_path)
    schema = _load_json(catalog_schema_path)
    errors = _schema_errors(catalog, schema)
    return catalog, errors


def _request_text(url: str, timeout: int = 20, retries: int = 3, backoff_sec: float = 1.0) -> str:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            req = Request(
                url,
                headers={
                    "User-Agent": "yandex-cloud-skill/manifest-cli",
                    "Accept": "application/vnd.github+json, text/plain;q=0.9, */*;q=0.8",
                },
            )
            with urlopen(req, timeout=timeout) as response:
                return response.read().decode("utf-8", "ignore")
        except (URLError, HTTPError, TimeoutError, ValueError) as exc:
            last_error = exc
            if attempt == retries - 1:
                break
            time.sleep(backoff_sec * (2**attempt))
    assert last_error is not None
    raise RuntimeError(f"Network request failed after retries: {last_error}")


def _extract_readme_metadata(
    server_name: str,
    readme: str,
    intent_hints: dict[str, list[str]],
) -> dict[str, Any]:
    readme_lower = readme.lower()
    url_match = re.search(r"https://[a-z0-9.-]+\.mcp\.cloud\.yandex\.net/mcp", readme, re.IGNORECASE)
    endpoint = url_match.group(0) if url_match else ""

    if "no authorization credentials needed" in readme_lower:
        auth_mode = "none"
    elif "authorization: bearer" in readme_lower or "iam token" in readme_lower:
        auth_mode = "iam_token"
    else:
        auth_mode = "unknown"

    folder_state = "required" if "folder-id" in readme_lower else "unsupported"
    cloud_state = "required" if "cloud-id" in readme_lower else "unsupported"

    if "(preview)" in readme_lower:
        status = "experimental"
    elif "deprecated" in readme_lower:
        status = "deprecated"
    else:
        status = "active"

    intents = intent_hints.get(server_name, [server_name.replace("-mcp-server", "")])

    return {
        "name": server_name,
        "repo_path": f"servers/{server_name}",
        "discovery_priority": 100,
        "intents": _normalize_intents(list(intents)),
        "auth": {
            "mode": auth_mode,
            "note": "Extracted from upstream README; verify on change.",
        },
        "install": {
            "transport": "http",
            "url": endpoint,
        },
        "headers": {
            "folder_id": folder_state,
            "cloud_id": cloud_state,
        },
        "readme_url": f"https://github.com/yandex-cloud/mcp/tree/master/servers/{server_name}",
        "verified_at": _now_date(),
        "verified_by": "script",
        "status": status,
    }


def _fetch_servers_from_api() -> list[str]:
    raw = _request_text(REPO_API_SERVERS_URL)
    payload = json.loads(raw)
    if not isinstance(payload, list):
        raise RuntimeError("Unexpected GitHub API payload for servers list")
    return sorted(
        item["name"]
        for item in payload
        if isinstance(item, dict) and item.get("type") == "dir" and isinstance(item.get("name"), str)
    )


def _fetch_server_readme(server_name: str) -> str:
    return _request_text(RAW_README_URL_TEMPLATE.format(server=server_name))


def _existing_servers_map(catalog: dict[str, Any]) -> dict[str, dict[str, Any]]:
    mapping: dict[str, dict[str, Any]] = {}
    for item in catalog.get("servers", []):
        if isinstance(item, dict) and isinstance(item.get("name"), str):
            mapping[item["name"]] = item
    return mapping


def _render_registry(catalog: dict[str, Any], catalog_path: Path, manifest_path: Path) -> str:
    servers = catalog.get("servers", [])
    lines = [
        "# YC MCP Registry (Derived)",
        "",
        "Этот файл генерируется из manifest + MCP catalog.",
        f"Manifest: `{manifest_path}`",
        f"Catalog: `{catalog_path}`",
        "",
        f"Generated at: `{catalog.get('generated_at', _now_date())}`",
        "",
        "| Name | Intents | Auth | Headers | Install | Status |",
        "| --- | --- | --- | --- | --- | --- |",
    ]

    for server in servers:
        name = str(server.get("name", ""))
        readme_url = str(server.get("readme_url", ""))
        intents = ", ".join(server.get("intents", []))
        auth = server.get("auth", {})
        auth_cell = f"{auth.get('mode', 'unknown')}"
        headers = server.get("headers", {})
        headers_cell = (
            f"folder:{headers.get('folder_id', 'unsupported')}, "
            f"cloud:{headers.get('cloud_id', 'unsupported')}"
        )
        install = server.get("install", {})
        if install.get("transport") == "http":
            install_cell = f"http {install.get('url', '')}".strip()
        else:
            install_cell = f"stdio {install.get('command', '')}".strip()
        status = str(server.get("status", ""))

        link = f"[{name}]({readme_url})" if readme_url else name
        row = [link, intents, auth_cell, headers_cell, install_cell, status]
        safe = [str(cell).replace("|", "\\|") for cell in row]
        lines.append("| " + " | ".join(safe) + " |")

    lines.extend(
        [
            "",
            "## Usage",
            "",
            "```bash",
            "uv run scripts/yc_mcp_catalog.py resolve-mcp --task-type mcp_setup --service resource-manager --intent docs",
            "uv run scripts/yc_mcp_catalog.py plan-mcp-install --task-type mcp_setup --service resource-manager --intent docs",
            "```",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_navigation(manifest: dict[str, Any], manifest_path: Path) -> str:
    routing = manifest.get("routing", {}).get("task_workflow", {})
    languages = manifest.get("languages", {}).get("profiles", {})
    mcp_catalog_path = manifest.get("mcp", {}).get("catalog_path", "references/mcp/catalog.yaml")

    lines = [
        "# Navigation Map (Derived)",
        "",
        "Канонический источник правил:",
        f"- `{manifest_path}`",
        "",
        "## Load Order",
        "",
        "1. Определи `task_type`.",
        "2. Открой workflow из карты ниже.",
        "3. При необходимости открой языковой профиль.",
        "4. Для MCP задач используй каталог серверов.",
        "",
        "## Task -> Workflow",
        "",
    ]

    for task_type in sorted(routing):
        lines.append(f"- `{task_type}` -> `{routing[task_type]}`")

    lines.extend(["", "## Language -> Profile", ""])
    for language in sorted(languages):
        lines.append(f"- `{language}` -> `{languages[language]}`")

    lines.extend(
        [
            "",
            "## MCP",
            "",
            f"- Catalog -> `{mcp_catalog_path}`",
            "- Selection -> `uv run scripts/yc_mcp_catalog.py resolve-mcp ...`",
            "- Install plan -> `uv run scripts/yc_mcp_catalog.py plan-mcp-install ...`",
        ]
    )
    return "\n".join(lines) + "\n"


def _render_workflow_doc(task_type: str, workflow_path: str, manifest_path: Path) -> str:
    return "\n".join(
        [
            f"# Workflow: {task_type}",
            "",
            "Derived file. Не редактируй вручную.",
            f"Канонический контракт: `{manifest_path}`",
            "",
            "## Policy",
            "",
            "- Все правила intake/routing/output берутся из manifest.",
            "- Для MCP-сценариев используй команды `resolve-mcp`, `plan-mcp-install`, `report-mcp-install`.",
            "- Ответы формируй только через envelope v2.",
            "",
            "## Output",
            "",
            "- `version`, `status`, `data`, `checks`, `limitations`, `sources`, `errors`.",
            "",
            f"Workflow path: `{workflow_path}`",
            "",
        ]
    )


def _render_language_doc(language: str, profile_path: str, manifest_path: Path) -> str:
    return "\n".join(
        [
            f"# Language Profile: {language}",
            "",
            "Derived file. Не редактируй вручную.",
            f"Канонический контракт: `{manifest_path}`",
            "",
            "## Policy",
            "",
            "- Для Python-утилит использовать только `uv run ...`.",
            "- Для live YC CLI соблюдать preflight/safety правила из manifest (`yc_cli_policy`).",
            "- Все ответы и машинные артефакты должны соответствовать envelope v2.",
            "",
            f"Profile path: `{profile_path}`",
            "",
        ]
    )


def _render_codex_setup(manifest: dict[str, Any], manifest_path: Path) -> str:
    permission_denied_message = _permission_denied_chat_message(manifest)
    return "\n".join(
        [
            "# YC MCP Setup For Codex (Derived)",
            "",
            "Канонический источник правил:",
            f"- `{manifest_path}`",
            "",
            "## Commands",
            "",
            "```bash",
            "uv run scripts/yc_mcp_catalog.py validate-contracts",
            "uv run scripts/yc_mcp_catalog.py refresh-mcp-catalog",
            "uv run scripts/yc_mcp_catalog.py resolve-mcp --task-type mcp_setup --service resource-manager --intent docs",
            "uv run scripts/yc_mcp_catalog.py plan-mcp-install --task-type mcp_setup --service resource-manager --intent docs",
            "uv run scripts/yc_mcp_catalog.py report-mcp-install --task-type mcp_setup --service resource-manager --intent docs",
            "```",
            "",
            "## Notes",
            "",
            "- При `status=mcp_unavailable` продолжай через `data.non_mcp_fallback`.",
            f"- При ответе YC `Permission denied` в tool-вызове используй сообщение: `{permission_denied_message}`",
            "- Установку MCP выполнять только после явного подтверждения пользователя.",
            "",
        ]
    )


def _tokenize_intent(intent: str | None) -> list[str]:
    if not intent:
        return []
    parts = re.split(r"[,\s]+", intent.strip())
    return [item for item in parts if item]


def _collect_requested_tags(
    task_type: str | None,
    service: str | None,
    intent: str | None,
    manifest: dict[str, Any],
) -> tuple[list[str], list[str]]:
    tags: list[str] = []
    service_tags: list[str] = []

    tags.extend(_tokenize_intent(intent))

    service_map = manifest.get("mcp", {}).get("service_intents", {})
    task_map = manifest.get("mcp", {}).get("task_type_intents", {})

    if service:
        resolved_service = _normalize_service(service)
        service_values = service_map.get(resolved_service, [])
        if isinstance(service_values, list):
            tags.extend(service_values)
            service_tags.extend(service_values)

    if task_type:
        resolved_task = _normalize_task_type(task_type)
        task_values = task_map.get(resolved_task, [])
        if isinstance(task_values, list):
            tags.extend(task_values)

    return _normalize_intents(tags), _normalize_intents(service_tags)


def _is_toolkit_service_supported(service: str | None, manifest: dict[str, Any]) -> bool:
    if not service:
        return True
    supported = {
        _normalize_service(item)
        for item in manifest.get("mcp", {}).get("toolkit_supported_services", [])
    }
    return _normalize_service(service) in supported


def _is_toolkit_operation_supported(operation: str | None, manifest: dict[str, Any]) -> bool:
    if not operation:
        return True
    supported = {
        _normalize_operation(item)
        for item in manifest.get("mcp", {}).get("toolkit_supported_tools", [])
    }
    return _normalize_operation(operation) in supported


def _resolve_server(
    catalog: dict[str, Any],
    manifest: dict[str, Any],
    task_type: str | None,
    service: str | None,
    intent: str | None,
    operation: str | None,
) -> ResolveResult:
    requested_tags, service_tags = _collect_requested_tags(task_type, service, intent, manifest)
    servers = [server for server in catalog.get("servers", []) if server.get("status") != "deprecated"]

    if not servers:
        raise ValueError("Catalog has no active servers")

    candidates: list[tuple[int, int, str, dict[str, Any], list[str]]] = []

    for server in servers:
        server_name = str(server.get("name", ""))
        server_tags = {_normalize_tag(tag) for tag in server.get("intents", [])}

        if service_tags and not any(tag in server_tags for tag in service_tags):
            continue

        if server_name == "toolkit-mcp-server":
            if not _is_toolkit_service_supported(service, manifest):
                continue
            if not _is_toolkit_operation_supported(operation, manifest):
                continue

        matched = [tag for tag in requested_tags if tag in server_tags]
        if requested_tags and not matched:
            continue

        score = len(set(matched))
        priority = int(server.get("discovery_priority", 999))
        candidates.append((score, priority, server_name, server, sorted(set(matched))))

    if not candidates:
        raise ValueError(NO_MATCH_ERROR)

    candidates.sort(key=lambda item: (-item[0], item[1], item[2]))
    best = candidates[0]
    return ResolveResult(server=best[3], matched_tags=best[4])


def _build_non_mcp_fallback(
    manifest: dict[str, Any],
    task_type: str | None,
    service: str | None,
    intent: str | None,
    operation: str | None,
    reason: str,
) -> NonMCPFallback:
    task_key = _normalize_task_type(task_type or "")
    routing = manifest.get("routing", {}).get("task_workflow", {})
    workflow_hint = routing.get(task_key, "references/navigation.md")

    policy_root = manifest.get("mcp", {}).get("non_mcp_policy", {})
    policy_default = policy_root.get("default", {})
    selection_principle = str(
        policy_root.get("selection_principle", "mcp_first_then_generic_fallback")
    )
    interfaces = list(policy_default.get("interfaces") or [])
    official_sources = list(policy_default.get("official_sources") or [])
    next_steps = list(policy_default.get("next_steps") or [])

    if not next_steps:
        next_steps = [
            "Сначала попытайся решить задачу через подходящий MCP сервер.",
            "Если MCP для контекста не найден, переходи на generic non-MCP интерфейсы.",
            "Продолжить выполнение задачи без MCP через workflow и Tier 1 источники.",
            "Выбрать минимально сложный интерфейс из interfaces.",
        ]

    return NonMCPFallback(
        mode="autonomous_non_mcp",
        selection_principle=selection_principle,
        reason=reason,
        task_type=task_type or "",
        service=service or "",
        intent=intent or "",
        operation=operation or "",
        workflow_hint=workflow_hint,
        interfaces=interfaces,
        context_sources=[
            "references/contracts/skill_manifest.yaml",
            "references/navigation.md",
            workflow_hint,
        ],
        official_sources=official_sources,
        next_steps=next_steps,
    )


def _non_mcp_data(
    manifest: dict[str, Any],
    task_type: str | None,
    service: str | None,
    intent: str | None,
    operation: str | None,
) -> dict[str, Any]:
    fallback = _build_non_mcp_fallback(
        manifest,
        task_type=task_type,
        service=service,
        intent=intent,
        operation=operation,
        reason=NO_MATCH_ERROR,
    )
    return {
        "server": None,
        "status": "mcp_unavailable",
        "matched_tags": [],
        "install_plan": None,
        "non_mcp_fallback": {
            "mode": fallback.mode,
            "selection_principle": fallback.selection_principle,
            "reason": fallback.reason,
            "task_type": fallback.task_type,
            "service": fallback.service,
            "intent": fallback.intent,
            "operation": fallback.operation,
            "workflow_hint": fallback.workflow_hint,
            "interfaces": fallback.interfaces,
            "context_sources": fallback.context_sources,
            "official_sources": fallback.official_sources,
            "next_steps": fallback.next_steps,
        },
    }


def _build_install_plan(server: dict[str, Any]) -> dict[str, Any]:
    name = str(server["name"])
    install = server["install"]
    transport = str(install["transport"])
    auth_mode = str(server["auth"]["mode"])

    if transport == "http":
        command_args = ["codex", "mcp", "add", name, "--url", str(install["url"])]
    else:
        stdio_command = shlex.split(str(install["command"]))
        command_args = ["codex", "mcp", "add", name, "--", *stdio_command]

    required_env: list[str] = []
    optional_env: list[str] = []

    if auth_mode == "iam_token":
        command_args.extend(["--bearer-token-env-var", "YC_IAM_TOKEN"])
        required_env.append("YC_IAM_TOKEN")

    headers = server.get("headers", {})

    folder_state = headers.get("folder_id", "unsupported")
    cloud_state = headers.get("cloud_id", "unsupported")

    if folder_state == "required":
        required_env.append("YC_FOLDER_ID")
    elif folder_state == "optional":
        optional_env.append("YC_FOLDER_ID")

    if cloud_state == "required":
        required_env.append("YC_CLOUD_ID")
    elif cloud_state == "optional":
        optional_env.append("YC_CLOUD_ID")

    return {
        "server": name,
        "transport": transport,
        "auth_mode": auth_mode,
        "command_args": command_args,
        "command": shlex.join(command_args),
        "required_env": sorted(required_env),
        "optional_env": sorted(optional_env),
    }


def _decode_json_output(stdout: str, stderr: str) -> Any:
    candidate = stdout.strip()
    if candidate:
        try:
            return json.loads(candidate)
        except json.JSONDecodeError:
            pass

    merged = f"{stdout}\n{stderr}".strip()
    if not merged:
        raise RuntimeError("Command returned empty output; expected JSON")

    for marker in ("[", "{"):
        idx = merged.find(marker)
        if idx >= 0:
            fragment = merged[idx:]
            try:
                return json.loads(fragment)
            except json.JSONDecodeError:
                continue

    raise RuntimeError("Command output is not valid JSON")


def _run_cmd(args: list[str]) -> tuple[str, str, int]:
    proc = subprocess.run(
        args,
        check=False,
        text=True,
        capture_output=True,
    )
    return proc.stdout or "", proc.stderr or "", proc.returncode


def _permission_denied_chat_message(manifest: dict[str, Any]) -> str:
    message = (
        manifest.get("mcp", {})
        .get("tool_error_messages", {})
        .get("permission_denied", "")
    )
    if isinstance(message, str) and message.strip():
        return message
    return (
        "Yandex Cloud вернул Permission denied, проверьте роли сервисного аккаунта "
        "или установку и актуальность переменной YC_IAM_TOKEN и перезапустите Codex, "
        "если дело в ней"
    )


def _missing_required_env_vars(install_plan: dict[str, Any]) -> list[str]:
    required = install_plan.get("required_env", [])
    if not isinstance(required, list):
        return []
    missing: list[str] = []
    for var_name in required:
        if not isinstance(var_name, str):
            continue
        value = os.getenv(var_name)
        if value is None or not value.strip():
            missing.append(var_name)
    return sorted(missing)


def _auth_env_state(install_plan: dict[str, Any]) -> dict[str, Any]:
    required_env = install_plan.get("required_env", [])
    optional_env = install_plan.get("optional_env", [])
    if not isinstance(required_env, list):
        required_env = []
    if not isinstance(optional_env, list):
        optional_env = []

    missing_env = _missing_required_env_vars(install_plan)
    missing_env_set = set(missing_env)
    provided_required_env = sorted(
        item
        for item in required_env
        if isinstance(item, str) and item not in missing_env_set
    )

    return {
        "required_env": sorted(item for item in required_env if isinstance(item, str)),
        "optional_env": sorted(item for item in optional_env if isinstance(item, str)),
        "missing_env": missing_env,
        "provided_required_env": provided_required_env,
        "ready": not missing_env,
    }


def _mcp_list_json() -> tuple[list[dict[str, Any]], dict[str, Any]]:
    stdout, stderr, returncode = _run_cmd(["codex", "mcp", "list", "--json"])
    if returncode != 0:
        raise RuntimeError((stderr or stdout).strip() or "`codex mcp list --json` failed")

    payload = _decode_json_output(stdout, stderr)
    if not isinstance(payload, list):
        raise RuntimeError("`codex mcp list --json` returned non-list payload")

    servers: list[dict[str, Any]] = [item for item in payload if isinstance(item, dict)]
    return servers, {"stdout": stdout.strip(), "stderr": stderr.strip()}


def _mcp_get_json(name: str) -> tuple[dict[str, Any], dict[str, Any]]:
    stdout, stderr, returncode = _run_cmd(["codex", "mcp", "get", name, "--json"])
    if returncode != 0:
        raise RuntimeError((stderr or stdout).strip() or f"`codex mcp get {name} --json` failed")

    payload = _decode_json_output(stdout, stderr)
    if not isinstance(payload, dict):
        raise RuntimeError("`codex mcp get --json` returned non-object payload")
    return payload, {"stdout": stdout.strip(), "stderr": stderr.strip()}


def _render_files(
    *,
    manifest: dict[str, Any],
    manifest_path: Path,
    catalog: dict[str, Any],
    catalog_path: Path,
    navigation_path: Path,
    registry_path: Path,
    codex_setup_path: Path,
) -> list[str]:
    written: list[str] = []

    navigation_text = _render_navigation(manifest, manifest_path)
    navigation_path.parent.mkdir(parents=True, exist_ok=True)
    navigation_path.write_text(navigation_text, encoding="utf-8")
    written.append(str(navigation_path))

    registry_text = _render_registry(catalog, catalog_path, manifest_path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(registry_text, encoding="utf-8")
    written.append(str(registry_path))

    codex_setup_text = _render_codex_setup(manifest, manifest_path)
    codex_setup_path.parent.mkdir(parents=True, exist_ok=True)
    codex_setup_path.write_text(codex_setup_text, encoding="utf-8")
    written.append(str(codex_setup_path))

    routing = manifest.get("routing", {}).get("task_workflow", {})
    for task_type in sorted(routing):
        workflow_path = _resolve_path(routing[task_type])
        workflow_path.parent.mkdir(parents=True, exist_ok=True)
        workflow_path.write_text(
            _render_workflow_doc(task_type, routing[task_type], manifest_path),
            encoding="utf-8",
        )
        written.append(str(workflow_path))

    profiles = manifest.get("languages", {}).get("profiles", {})
    for language in sorted(profiles):
        profile_path = _resolve_path(profiles[language])
        profile_path.parent.mkdir(parents=True, exist_ok=True)
        profile_path.write_text(
            _render_language_doc(language, profiles[language], manifest_path),
            encoding="utf-8",
        )
        written.append(str(profile_path))

    return written


def _cmd_validate_contracts(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    manifest_path = _resolve_path(args.manifest)
    manifest_schema_path = _resolve_path(args.manifest_schema)
    mcp_catalog_path = _resolve_path(args.mcp_catalog)
    mcp_catalog_schema_path = _resolve_path(args.mcp_catalog_schema)

    errors: list[dict[str, Any]] = []

    manifest, manifest_errors = _load_manifest(manifest_path, manifest_schema_path)
    if manifest_errors:
        errors.append(
            _error(
                "contract_manifest_invalid",
                "Manifest validation failed",
                {"issues": manifest_errors},
            )
        )

    catalog, catalog_errors = _load_catalog(mcp_catalog_path, mcp_catalog_schema_path)
    if catalog_errors:
        errors.append(
            _error(
                "contract_mcp_catalog_invalid",
                "MCP catalog validation failed",
                {"issues": catalog_errors},
            )
        )

    if errors:
        return (
            _envelope(
                status="error",
                data={
                    "manifest_path": str(manifest_path),
                    "manifest_schema_path": str(manifest_schema_path),
                    "mcp_catalog_path": str(mcp_catalog_path),
                    "mcp_catalog_schema_path": str(mcp_catalog_schema_path),
                },
                checks=[
                    "Fix validation issues and rerun validate-contracts.",
                ],
                errors=errors,
            ),
            1,
        )

    return (
        _envelope(
            status="ok",
            data={
                "manifest_path": str(manifest_path),
                "mcp_catalog_path": str(mcp_catalog_path),
                "manifest_version": manifest.get("version"),
                "mcp_catalog_version": catalog.get("version"),
                "servers_total": len(catalog.get("servers", [])),
            },
            checks=["Manifest and MCP catalog match their schemas."],
        ),
        0,
    )


def _cmd_refresh_mcp_catalog(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    manifest_path = _resolve_path(args.manifest)
    manifest_schema_path = _resolve_path(args.manifest_schema)
    mcp_catalog_schema_path = _resolve_path(args.mcp_catalog_schema)

    manifest, manifest_errors = _load_manifest(manifest_path, manifest_schema_path)
    if manifest_errors:
        return (
            _envelope(
                status="error",
                errors=[
                    _error(
                        "contract_manifest_invalid",
                        "Manifest validation failed",
                        {"issues": manifest_errors},
                    )
                ],
            ),
            1,
        )

    mcp_catalog_path = _resolve_path(args.mcp_catalog or manifest.get("mcp", {}).get("catalog_path"))
    registry_path = _resolve_path(args.registry or manifest.get("mcp", {}).get("registry_path"))

    catalog_schema = _load_json(mcp_catalog_schema_path)

    if args.offline:
        catalog = _load_yaml(mcp_catalog_path)
        errors = _schema_errors(catalog, catalog_schema)
        if errors:
            return (
                _envelope(
                    status="error",
                    errors=[
                        _error(
                            "contract_mcp_catalog_invalid",
                            "Offline catalog is invalid",
                            {"issues": errors},
                        )
                    ],
                    limitations=["Offline mode requires a valid local MCP catalog."],
                ),
                1,
            )

        registry_text = _render_registry(catalog, mcp_catalog_path, manifest_path)
        registry_path.parent.mkdir(parents=True, exist_ok=True)
        registry_path.write_text(registry_text, encoding="utf-8")

        return (
            _envelope(
                status="offline_used_cache",
                data={
                    "catalog_path": str(mcp_catalog_path),
                    "registry_path": str(registry_path),
                    "servers_total": len(catalog.get("servers", [])),
                },
                checks=["Offline mode used local validated catalog."],
            ),
            0,
        )

    existing_catalog = _load_yaml(mcp_catalog_path)
    existing_map = _existing_servers_map(existing_catalog)

    try:
        server_names = _fetch_servers_from_api()
    except (RuntimeError, json.JSONDecodeError) as exc:
        return (
            _envelope(
                status="error",
                errors=[
                    _error(
                        "network_refresh_failed",
                        "Failed to fetch MCP server list from GitHub API",
                        {"exception": str(exc)},
                    )
                ],
                limitations=["Retry later or rerun with --offline if local catalog is valid."],
            ),
            1,
        )

    hints = manifest.get("mcp", {}).get("intent_hints_by_name", {})

    refreshed: list[dict[str, Any]] = []
    fetch_warnings: list[str] = []

    for idx, server_name in enumerate(server_names, start=1):
        try:
            readme = _fetch_server_readme(server_name)
        except RuntimeError as exc:
            fetch_warnings.append(f"{server_name}: {exc}")
            continue

        generated = _extract_readme_metadata(server_name, readme, hints)
        existing = existing_map.get(server_name)

        if existing:
            if isinstance(existing.get("discovery_priority"), int):
                generated["discovery_priority"] = existing["discovery_priority"]

            existing_intents = existing.get("intents")
            if isinstance(existing_intents, list):
                generated["intents"] = _normalize_intents([str(item) for item in existing_intents])

            existing_auth = existing.get("auth")
            if isinstance(existing_auth, dict):
                mode = existing_auth.get("mode")
                note = existing_auth.get("note")
                if mode in AUTH_MODES:
                    generated["auth"]["mode"] = mode
                if isinstance(note, str) and note:
                    generated["auth"]["note"] = note

            existing_headers = existing.get("headers")
            if isinstance(existing_headers, dict):
                for key in ("folder_id", "cloud_id"):
                    if existing_headers.get(key) in HEADER_MODES:
                        generated["headers"][key] = existing_headers[key]

            status = existing.get("status")
            if status in STATUS_MODES:
                generated["status"] = status
        else:
            generated["discovery_priority"] = 100 + idx

        generated["verified_at"] = _now_date()
        generated["verified_by"] = "script"
        generated["intents"] = _normalize_intents(generated.get("intents", []))
        refreshed.append(generated)

    refreshed.sort(key=lambda item: (int(item.get("discovery_priority", 999)), item.get("name", "")))

    new_catalog = {
        "version": 1,
        "source_repo": manifest.get("mcp", {}).get("source_repo", "https://github.com/yandex-cloud/mcp"),
        "generated_at": _now_date(),
        "servers": refreshed,
    }

    validation_errors = _schema_errors(new_catalog, catalog_schema)
    if validation_errors:
        return (
            _envelope(
                status="error",
                errors=[
                    _error(
                        "contract_mcp_catalog_invalid",
                        "Generated MCP catalog failed schema validation",
                        {"issues": validation_errors},
                    )
                ],
                limitations=["Catalog write aborted to prevent invalid state."],
            ),
            1,
        )

    _dump_yaml(new_catalog, mcp_catalog_path)

    registry_text = _render_registry(new_catalog, mcp_catalog_path, manifest_path)
    registry_path.parent.mkdir(parents=True, exist_ok=True)
    registry_path.write_text(registry_text, encoding="utf-8")

    return (
        _envelope(
            status="ok",
            data={
                "catalog_path": str(mcp_catalog_path),
                "registry_path": str(registry_path),
                "servers_total": len(new_catalog.get("servers", [])),
                "warnings": fetch_warnings,
            },
            checks=[
                "Catalog is validated by schema before saving.",
                "Use --offline to operate on last valid local catalog.",
            ],
            limitations=(
                ["Some servers were skipped due to README fetch failures."] if fetch_warnings else []
            ),
        ),
        0,
    )


def _load_validated_runtime(
    args: argparse.Namespace,
) -> tuple[dict[str, Any], dict[str, Any], Path, list[dict[str, Any]]]:
    manifest_path = _resolve_path(args.manifest)
    manifest_schema_path = _resolve_path(args.manifest_schema)
    mcp_catalog_path = _resolve_path(args.mcp_catalog)
    mcp_catalog_schema_path = _resolve_path(args.mcp_catalog_schema)

    errors: list[dict[str, Any]] = []

    manifest, manifest_errors = _load_manifest(manifest_path, manifest_schema_path)
    if manifest_errors:
        errors.append(
            _error(
                "contract_manifest_invalid",
                "Manifest validation failed",
                {"issues": manifest_errors},
            )
        )

    catalog, catalog_errors = _load_catalog(mcp_catalog_path, mcp_catalog_schema_path)
    if catalog_errors:
        errors.append(
            _error(
                "contract_mcp_catalog_invalid",
                "MCP catalog validation failed",
                {"issues": catalog_errors},
            )
        )

    return manifest, catalog, manifest_path, errors


def _cmd_resolve_mcp(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    manifest, catalog, _manifest_path, errors = _load_validated_runtime(args)
    if errors:
        return _envelope(status="error", errors=errors), 1

    try:
        result = _resolve_server(
            catalog,
            manifest,
            task_type=args.task_type or None,
            service=args.service or None,
            intent=args.intent or None,
            operation=args.operation or None,
        )
    except ValueError as exc:
        if str(exc) != NO_MATCH_ERROR:
            return (
                _envelope(status="error", errors=[_error("resolve_failed", str(exc))]),
                1,
            )

        data = _non_mcp_data(
            manifest,
            task_type=args.task_type or None,
            service=args.service or None,
            intent=args.intent or None,
            operation=args.operation or None,
        )

        return (
            _envelope(
                status="mcp_unavailable",
                data=data,
                checks=["Continue using non_mcp_fallback interfaces and sources."],
                sources=data["non_mcp_fallback"].get("official_sources", []),
            ),
            0,
        )

    plan = _build_install_plan(result.server)
    checks = [
        "Install command must be confirmed by user before execution.",
        "For auth.mode=none command must not include bearer token env var.",
    ]

    if result.server.get("name") == "toolkit-mcp-server":
        checks.append(
            "Use only canonical toolkit operation IDs from the official tools reference."
        )

    return (
        _envelope(
            status="ok",
            data={
                "server": result.server,
                "matched_tags": result.matched_tags,
                "install_plan": plan,
            },
            checks=checks,
            sources=[
                str(result.server.get("readme_url", "")),
                str(manifest.get("mcp", {}).get("tools_reference", "")),
            ],
        ),
        0,
    )


def _resolve_server_from_args(
    args: argparse.Namespace,
    manifest: dict[str, Any],
    catalog: dict[str, Any],
) -> tuple[dict[str, Any] | None, list[str], dict[str, Any] | None]:
    if args.name:
        for server in catalog.get("servers", []):
            if server.get("name") == args.name:
                return server, [], None
        raise ValueError(f"Server `{args.name}` not found in MCP catalog")

    try:
        result = _resolve_server(
            catalog,
            manifest,
            task_type=args.task_type or None,
            service=args.service or None,
            intent=args.intent or None,
            operation=args.operation or None,
        )
    except ValueError as exc:
        if str(exc) != NO_MATCH_ERROR:
            raise
        return None, [], _non_mcp_data(
            manifest,
            task_type=args.task_type or None,
            service=args.service or None,
            intent=args.intent or None,
            operation=args.operation or None,
        )

    return result.server, result.matched_tags, None


def _cmd_plan_mcp_install(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    manifest, catalog, _manifest_path, errors = _load_validated_runtime(args)
    if errors:
        return _envelope(status="error", errors=errors), 1

    try:
        server, matched_tags, unavailable_data = _resolve_server_from_args(args, manifest, catalog)
    except ValueError as exc:
        return _envelope(status="error", errors=[_error("resolve_failed", str(exc))]), 1

    if unavailable_data is not None:
        return (
            _envelope(
                status="mcp_unavailable",
                data=unavailable_data,
                checks=["No install command should run in mcp_unavailable state."],
                sources=unavailable_data["non_mcp_fallback"].get("official_sources", []),
            ),
            0,
        )

    assert server is not None
    install_plan = _build_install_plan(server)
    auth_env = _auth_env_state(install_plan)

    try:
        installed_servers, list_raw = _mcp_list_json()
    except RuntimeError as exc:
        return _envelope(status="error", errors=[_error("mcp_list_failed", str(exc))]), 1

    installed = any(item.get("name") == server.get("name") for item in installed_servers)
    status = "already_installed" if installed else "needs_install"

    data = {
        "server": server.get("name"),
        "status": status,
        "matched_tags": matched_tags,
        "install_plan": install_plan,
        "auth_env": auth_env,
        "tool_error_guidance": {
            "permission_denied_chat_message": _permission_denied_chat_message(manifest),
            "interpret_permission_denied_only_after_yc_error": True,
        },
        "codex_mcp_list": {
            "items": installed_servers,
            "raw": list_raw,
        },
    }

    checks = [
        "Ask explicit user confirmation before executing install command.",
        "After install run report-mcp-install to verify status.",
        "Interpret Permission denied only after MCP tool invocation returns Yandex Cloud error.",
    ]
    limitations: list[str] = []
    missing_env = auth_env["missing_env"]
    if missing_env:
        checks.append(
            "Set all variables from data.auth_env.missing_env before MCP tool invocation to avoid auth failures."
        )
        limitations.append(
            "Missing required auth env vars can cause MCP tool invocation to fail until configured."
        )

    return (
        _envelope(
            status=status,
            data=data,
            checks=checks,
            limitations=limitations,
            sources=[str(server.get("readme_url", ""))],
        ),
        0,
    )


def _cmd_report_mcp_install(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    manifest, catalog, _manifest_path, errors = _load_validated_runtime(args)
    if errors:
        return _envelope(status="error", errors=errors), 1

    try:
        server, matched_tags, unavailable_data = _resolve_server_from_args(args, manifest, catalog)
    except ValueError as exc:
        return _envelope(status="error", errors=[_error("resolve_failed", str(exc))]), 1

    if unavailable_data is not None:
        unavailable_data["installed"] = False
        unavailable_data["codex_mcp_list"] = {"items": [], "raw": {"stdout": "", "stderr": ""}}
        unavailable_data["codex_mcp_get"] = {"item": {}, "raw": {"stdout": "", "stderr": ""}}
        unavailable_data["server_config"] = {}
        return (
            _envelope(
                status="mcp_unavailable",
                data=unavailable_data,
                checks=["Use non_mcp_fallback for this context."],
                sources=unavailable_data["non_mcp_fallback"].get("official_sources", []),
            ),
            0,
        )

    assert server is not None
    install_plan = _build_install_plan(server)
    auth_env = _auth_env_state(install_plan)

    try:
        installed_servers, list_raw = _mcp_list_json()
    except RuntimeError as exc:
        return _envelope(status="error", errors=[_error("mcp_list_failed", str(exc))]), 1

    installed = any(item.get("name") == server.get("name") for item in installed_servers)
    get_item: dict[str, Any] = {}
    get_raw = {"stdout": "", "stderr": ""}

    if installed:
        try:
            get_item, get_raw = _mcp_get_json(str(server.get("name")))
        except RuntimeError as exc:
            return _envelope(status="error", errors=[_error("mcp_get_failed", str(exc))]), 1

    status = "installed" if installed else "not_installed"

    data = {
        "server": server.get("name"),
        "status": status,
        "installed": installed,
        "matched_tags": matched_tags,
        "install_plan": install_plan,
        "auth_env": auth_env,
        "tool_error_guidance": {
            "permission_denied_chat_message": _permission_denied_chat_message(manifest),
            "interpret_permission_denied_only_after_yc_error": True,
        },
        "codex_mcp_list": {
            "items": installed_servers,
            "raw": list_raw,
        },
        "codex_mcp_get": {
            "item": get_item,
            "raw": get_raw,
        },
        "server_config": get_item,
    }

    checks = [
        "Machine consumers should read data.status/data.install_plan/data.server_config.",
        "If token changed in another shell, restart Codex session.",
        "Interpret Permission denied only after MCP tool invocation returns Yandex Cloud error.",
    ]
    limitations: list[str] = []
    missing_env = auth_env["missing_env"]
    if missing_env:
        checks.append(
            "Set all variables from data.auth_env.missing_env before MCP tool invocation to avoid auth failures."
        )
        limitations.append(
            "Missing required auth env vars can cause MCP tool invocation to fail until configured."
        )

    return (
        _envelope(
            status=status,
            data=data,
            checks=checks,
            limitations=limitations,
            sources=[str(server.get("readme_url", ""))],
        ),
        0,
    )


def _cmd_render_docs(args: argparse.Namespace) -> tuple[dict[str, Any], int]:
    manifest_path = _resolve_path(args.manifest)
    manifest_schema_path = _resolve_path(args.manifest_schema)
    mcp_catalog_path = _resolve_path(args.mcp_catalog)
    mcp_catalog_schema_path = _resolve_path(args.mcp_catalog_schema)
    navigation_path = _resolve_path(args.navigation)
    registry_path = _resolve_path(args.registry)
    codex_setup_path = _resolve_path(args.codex_setup)

    manifest, manifest_errors = _load_manifest(manifest_path, manifest_schema_path)
    if manifest_errors:
        return (
            _envelope(
                status="error",
                errors=[
                    _error(
                        "contract_manifest_invalid",
                        "Manifest validation failed",
                        {"issues": manifest_errors},
                    )
                ],
            ),
            1,
        )

    catalog, catalog_errors = _load_catalog(mcp_catalog_path, mcp_catalog_schema_path)
    if catalog_errors:
        return (
            _envelope(
                status="error",
                errors=[
                    _error(
                        "contract_mcp_catalog_invalid",
                        "MCP catalog validation failed",
                        {"issues": catalog_errors},
                    )
                ],
            ),
            1,
        )

    written = _render_files(
        manifest=manifest,
        manifest_path=manifest_path,
        catalog=catalog,
        catalog_path=mcp_catalog_path,
        navigation_path=navigation_path,
        registry_path=registry_path,
        codex_setup_path=codex_setup_path,
    )

    return (
        _envelope(
            status="ok",
            data={"written_files": sorted(written)},
            checks=["Derived docs regenerated from manifest + catalog."],
        ),
        0,
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Manifest-first YC skill CLI")
    parser.add_argument("--manifest", default=str(MANIFEST_PATH_DEFAULT))
    parser.add_argument("--manifest-schema", default=str(MANIFEST_SCHEMA_PATH_DEFAULT))
    parser.add_argument("--mcp-catalog", default=str(MCP_CATALOG_PATH_DEFAULT))
    parser.add_argument("--mcp-catalog-schema", default=str(MCP_CATALOG_SCHEMA_PATH_DEFAULT))

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("validate-contracts", help="Validate manifest and MCP catalog against schemas")

    refresh = sub.add_parser("refresh-mcp-catalog", help="Refresh MCP catalog from GitHub API")
    refresh.add_argument("--offline", action="store_true", help="Use last valid local catalog only")
    refresh.add_argument("--registry", default=str(MCP_REGISTRY_PATH_DEFAULT))

    resolve = sub.add_parser("resolve-mcp", help="Resolve MCP server by context")
    resolve.add_argument("--task-type", default="")
    resolve.add_argument("--service", default="")
    resolve.add_argument("--intent", default="")
    resolve.add_argument("--operation", default="")

    plan = sub.add_parser("plan-mcp-install", help="Build install plan + installed state")
    plan.add_argument("--name", default="")
    plan.add_argument("--task-type", default="")
    plan.add_argument("--service", default="")
    plan.add_argument("--intent", default="")
    plan.add_argument("--operation", default="")

    report = sub.add_parser("report-mcp-install", help="Report installed state + server config")
    report.add_argument("--name", default="")
    report.add_argument("--task-type", default="")
    report.add_argument("--service", default="")
    report.add_argument("--intent", default="")
    report.add_argument("--operation", default="")

    render = sub.add_parser("render-docs", help="Render derived docs from manifest + catalog")
    render.add_argument("--navigation", default=str(NAVIGATION_PATH_DEFAULT))
    render.add_argument("--registry", default=str(MCP_REGISTRY_PATH_DEFAULT))
    render.add_argument("--codex-setup", default=str(MCP_CODEX_SETUP_PATH_DEFAULT))

    return parser.parse_args()


def main() -> int:
    args = parse_args()

    if args.command == "validate-contracts":
        payload, code = _cmd_validate_contracts(args)
    elif args.command == "refresh-mcp-catalog":
        payload, code = _cmd_refresh_mcp_catalog(args)
    elif args.command == "resolve-mcp":
        payload, code = _cmd_resolve_mcp(args)
    elif args.command == "plan-mcp-install":
        payload, code = _cmd_plan_mcp_install(args)
    elif args.command == "report-mcp-install":
        payload, code = _cmd_report_mcp_install(args)
    elif args.command == "render-docs":
        payload, code = _cmd_render_docs(args)
    else:
        payload = _envelope(
            status="error",
            errors=[_error("unsupported_command", f"Unsupported command: {args.command}")],
        )
        code = 1

    _print_json(payload)
    return code


if __name__ == "__main__":
    raise SystemExit(main())
