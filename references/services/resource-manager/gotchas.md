# Resource Manager Gotchas

## NotFound Across Services

Причина: ресурс запрашивается в чужом folder/cloud.

Фикс:
- Нормализуй `scope` один раз и переиспользуй везде.

## Partial Inventory

Причина: доступ только к части folders.

Фикс:
- Явно пометь неполное покрытие и покажи, какие folders пропущены.
