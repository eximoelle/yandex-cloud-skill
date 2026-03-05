---
name: yandex-cloud-skill
description: Use when tasks involve Yandex Cloud infrastructure, APIs, IAM, Terraform, troubleshooting, billing, or MCP integration.
---

# Yandex Cloud Skill

Цель: минимальная и детерминированная оркестрация YC-задач через один контракт и один исполняемый скрипт.

## Canonical Source Of Truth

- Manifest (источник истины): `references/contracts/skill_manifest.yaml`
- Manifest schema: `references/contracts/skill_manifest.schema.json`
- MCP catalog schema: `references/contracts/mcp_catalog.schema.json`

Все runtime-правила intake/routing/output/safety берутся только из manifest.

## Runtime CLI (Single Script)

Используй только:

```bash
uv run scripts/yc_mcp_catalog.py <subcommand>
```

Доступные subcommands:

1. `validate-contracts`
2. `refresh-mcp-catalog`
3. `resolve-mcp`
4. `plan-mcp-install`
5. `report-mcp-install`
6. `render-docs`

## Output Contract

Все subcommands возвращают единый envelope v2:

- `version`
- `status`
- `data`
- `checks`
- `limitations`
- `sources`
- `errors`

Другие форматы вывода не поддерживаются.

## MCP Workflow

- Перед резолвом/установкой валидация: `validate-contracts`.
- Каталог MCP обновляется только через `refresh-mcp-catalog`.
- Если `status=mcp_unavailable`, продолжай через `data.non_mcp_fallback`.
- Проверка installed-state использует только JSON API:
  - `codex mcp list --json`
  - `codex mcp get <name> --json`

## YC CLI Safety

YC CLI policy задается в manifest (`yc_cli_policy`):

- preflight-команды;
- read-only/mutating классификация;
- правила подтверждения;
- запрет секрето-утечек.

Никогда не дублируй эту политику в workflow/language файлах.

## Derived Docs

Файлы в `references/navigation.md`, `references/workflows/*.md`, `references/languages/*.md`, `references/mcp/registry.md`, `references/mcp/codex-setup.md` считаются производными.

Обновление:

```bash
uv run scripts/yc_mcp_catalog.py render-docs
```

Ручные правки производных файлов запрещены.

## Python Tooling

- Запуск: `uv run ...`
- Зависимости: `uv add ...` / `uv sync`
- Не использовать `pip`/`poetry`/`pipenv`, если пользователь явно не просил.
