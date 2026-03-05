# Navigation Map (Derived)

Канонический источник правил:
- `references/contracts/skill_manifest.yaml`

## Load Order

1. Определи `task_type`.
2. Открой workflow из карты ниже.
3. При необходимости открой языковой профиль.
4. Для MCP задач используй каталог серверов.

## Task -> Workflow

- `api_sdk` -> `references/workflows/api_sdk.md`
- `auth` -> `references/workflows/auth.md`
- `billing_detail` -> `references/workflows/billing_detail.md`
- `inventory` -> `references/workflows/inventory.md`
- `mcp_setup` -> `references/workflows/mcp_setup.md`
- `terraform_iac` -> `references/workflows/terraform_iac.md`
- `troubleshooting` -> `references/workflows/troubleshooting.md`

## Language -> Profile

- `cli` -> `references/languages/cli.md`
- `dotnet` -> `references/languages/dotnet.md`
- `go` -> `references/languages/go.md`
- `java` -> `references/languages/java.md`
- `nodejs` -> `references/languages/nodejs.md`
- `python` -> `references/languages/python.md`
- `terraform` -> `references/languages/terraform.md`

## MCP

- Catalog -> `references/mcp/catalog.yaml`
- Selection -> `uv run scripts/yc_mcp_catalog.py resolve-mcp ...`
- Install plan -> `uv run scripts/yc_mcp_catalog.py plan-mcp-install ...`
