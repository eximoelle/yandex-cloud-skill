# Workflow: billing_detail

Derived file. Не редактируй вручную.
Канонический контракт: `references/contracts/skill_manifest.yaml`

## Policy

- Все правила intake/routing/output берутся из manifest.
- Для MCP-сценариев используй команды `resolve-mcp`, `plan-mcp-install`, `report-mcp-install`.
- Ответы формируй только через envelope v2.

## Output

- `version`, `status`, `data`, `checks`, `limitations`, `sources`, `errors`.

Workflow path: `references/workflows/billing_detail.md`
