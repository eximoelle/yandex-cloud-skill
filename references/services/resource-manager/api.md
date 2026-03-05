# Resource Manager API/SDK Notes

## Canonical Sources

- Cloud API proto: `https://github.com/yandex-cloud/cloudapi`
- Docs: `https://yandex.cloud/ru/docs/resource-manager/`

## Typical Operations

- Листинг organizations/clouds/folders
- Поиск ресурса по id/name
- Проверка и передача контекста scope в другие сервисы

## Integration Rule

Любая downstream операция (Compute, VPC, Storage, Billing) должна получать
валидированный `scope` из этого модуля.
