# Object Storage Configuration

## Required Inputs

- `bucket_name`
- `folder_id` (если требуется в контексте задачи)
- auth strategy (IAM token/HMAC/SDK creds)
- naming and retention constraints

## Baseline Steps

1. Создать или выбрать bucket.
2. Настроить права на bucket/object scope.
3. Выбрать формат путей и именования объектов.
4. Проверить list/get/put на тестовом объекте.

## Validation

- Корректный доступ на нужном уровне (bucket/object).
- Ошибки авторизации отсутствуют в smoke-check.
