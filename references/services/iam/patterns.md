# IAM Patterns

## Pattern: Service Account For Automation

- Создать service account под конкретный workload.
- Выдать минимальные роли на нужный scope.
- Хранить исходные секреты в CI secret store.
- Короткоживущий IAM токен обновлять по расписанию.

## Pattern: VM Metadata Auth

- Для кода на VM использовать metadata-based токен.
- Не сохранять токен в файлах.
- Добавить health-check на истечение токена.
