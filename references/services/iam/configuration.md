# IAM Configuration

## Required Context

- Целевой `scope`: organization/cloud/folder/resource
- Субъект: user, federated user, service account
- Минимально нужное действие (least privilege)

## Baseline Steps

1. Определи минимальную роль для операции.
2. Назначь роль на минимально возможный scope.
3. Настрой путь выдачи IAM-токена.
4. Для automation зафиксируй ротацию токена.

## Validation

- Проверить, что токен действует в нужном scope.
- Проверить, что операция выполняется без прав "с запасом".
