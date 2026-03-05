# IAM API/SDK Notes

## Canonical Sources

- Cloud API proto: `https://github.com/yandex-cloud/cloudapi`
- IAM docs: `https://yandex.cloud/ru/docs/iam/`
- Python SDK: `https://github.com/yandex-cloud/python-sdk`

## Typical Operations

- Получение IAM токена
- Проверка текущего субъекта и scope
- Назначение ролей субъектам
- Аудит действующих прав

## SDK First, API Fallback

1. Сначала проверить метод в SDK выбранного языка.
2. При отсутствии метода использовать Cloud API и задокументировать fallback.
