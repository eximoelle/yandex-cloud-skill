# YC MCP Registry (Derived)

Этот файл генерируется из manifest + MCP catalog.
Manifest: `references/contracts/skill_manifest.yaml`
Catalog: `references/mcp/catalog.yaml`

Generated at: `2026-02-18`

| Name | Intents | Auth | Headers | Install | Status |
| --- | --- | --- | --- | --- | --- |
| [documentation-mcp-server](https://github.com/yandex-cloud/mcp/tree/master/servers/documentation-mcp-server) | docs, documentation, reference | none | folder:unsupported, cloud:unsupported | http https://docs.mcp.cloud.yandex.net/mcp | active |
| [toolkit-mcp-server](https://github.com/yandex-cloud/mcp/tree/master/servers/toolkit-mcp-server) | toolkit, infrastructure, compute, vpc, iam, storage, object-storage, ydb | iam_token | folder:optional, cloud:optional | http https://toolkit.mcp.cloud.yandex.net/mcp | active |
| [functions-mcp-server](https://github.com/yandex-cloud/mcp/tree/master/servers/functions-mcp-server) | functions, serverless | iam_token | folder:required, cloud:unsupported | http https://functions.mcp.cloud.yandex.net/mcp | experimental |
| [containers-mcp-server](https://github.com/yandex-cloud/mcp/tree/master/servers/containers-mcp-server) | containers, serverless | iam_token | folder:required, cloud:unsupported | http https://containers.mcp.cloud.yandex.net/mcp | experimental |
| [workflows-mcp-server](https://github.com/yandex-cloud/mcp/tree/master/servers/workflows-mcp-server) | workflows, serverless | iam_token | folder:required, cloud:unsupported | http https://workflows.mcp.cloud.yandex.net/mcp | experimental |
| [triggers-mcp-server](https://github.com/yandex-cloud/mcp/tree/master/servers/triggers-mcp-server) | triggers, serverless | iam_token | folder:required, cloud:unsupported | http https://triggers.mcp.cloud.yandex.net/mcp | experimental |
| [apigateway-mcp-server](https://github.com/yandex-cloud/mcp/tree/master/servers/apigateway-mcp-server) | apigateway, api-gateway | iam_token | folder:required, cloud:unsupported | http https://apigateway.mcp.cloud.yandex.net/mcp | experimental |
| [search-mcp-server](https://github.com/yandex-cloud/mcp/tree/master/servers/search-mcp-server) | search | iam_token | folder:required, cloud:unsupported | http https://search.mcp.cloud.yandex.net/mcp | active |
| [mcpgateway-mcp-server](https://github.com/yandex-cloud/mcp/tree/master/servers/mcpgateway-mcp-server) | mcpgateway, integration, serverless | iam_token | folder:required, cloud:unsupported | http https://mcpgateway.mcp.cloud.yandex.net/mcp | experimental |
| [datacatalog-consumer-mcp-server](https://github.com/yandex-cloud/mcp/tree/master/servers/datacatalog-consumer-mcp-server) | datacatalog, metadata-catalog, inventory | iam_token | folder:unsupported, cloud:unsupported | http https://datacatalog-consumer.mcp.cloud.yandex.net/mcp | active |

## Usage

```bash
uv run scripts/yc_mcp_catalog.py resolve-mcp --task-type mcp_setup --service resource-manager --intent docs
uv run scripts/yc_mcp_catalog.py plan-mcp-install --task-type mcp_setup --service resource-manager --intent docs
```
