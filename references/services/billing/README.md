# Billing Module

## Scope

Модуль для задач Cloud Billing: детализация через Billing Usage API (gRPC), CSV в бакете (S3 Select), агрегаты и top-N анализ.

## In This Module

- `configuration.md` -> входы по периоду и scope
- `api.md` -> endpoint, методы, фильтры и модель данных API/CSV/S3 Select
- `patterns.md` -> аналитические паттерны
- `gotchas.md` -> проблемы сверки и полноты данных

## Reading Order

- Аналитика расходов -> `configuration.md` -> `patterns.md` -> `api.md`
- Расхождения в цифрах -> `gotchas.md`
