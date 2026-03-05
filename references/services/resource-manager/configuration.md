# Resource Manager Configuration

## Scope Rules

- Для большинства операций фиксируй `folder_id`.
- Для межпроектных задач дополнительно фиксируй `cloud_id`.
- Для org-level задач фиксируй `organization_id`.

## Baseline Inputs

- `organization_id` (опционально)
- `cloud_id` (опционально)
- `folder_id` (часто обязателен)

## Validation

- Убедись, что все ID соответствуют одному контуру задачи.
- Проверь IAM роли на выбранном уровне иерархии.
