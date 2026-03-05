# YC MCP Setup For Codex (Derived)

Канонический источник правил:
- `references/contracts/skill_manifest.yaml`

## Commands

```bash
uv run scripts/yc_mcp_catalog.py validate-contracts
uv run scripts/yc_mcp_catalog.py refresh-mcp-catalog
uv run scripts/yc_mcp_catalog.py resolve-mcp --task-type mcp_setup --service resource-manager --intent docs
uv run scripts/yc_mcp_catalog.py plan-mcp-install --task-type mcp_setup --service resource-manager --intent docs
uv run scripts/yc_mcp_catalog.py report-mcp-install --task-type mcp_setup --service resource-manager --intent docs
```

## Notes

- При `status=mcp_unavailable` продолжай через `data.non_mcp_fallback`.
- При ответе YC `Permission denied` в tool-вызове используй сообщение: `Yandex Cloud вернул Permission denied, проверьте роли сервисного аккаунта или установку и актуальность переменной YC_IAM_TOKEN и перезапустите Codex, если дело в ней`
- Установку MCP выполнять только после явного подтверждения пользователя.
