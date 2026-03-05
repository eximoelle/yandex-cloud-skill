# Resource Manager Patterns

## Pattern: Scope Normalization

1. Получить `organization_id`, `cloud_id`, `folder_id`.
2. Сохранить как единый блок `scope`.
3. Пробрасывать `scope` в каждый SDK/API вызов.

## Pattern: Inventory Seed

- Сначала собрать список folders.
- Затем запускать inventory по сервисам внутри каждого folder.
- Отмечать ошибки доступа как `permission_gap`.
