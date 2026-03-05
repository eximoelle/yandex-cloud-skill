# Billing Gotchas

## API Works Over gRPC

Причина: Billing Usage API вызывается через `billing.api.cloud.yandex.net:443`, а не через REST endpoint.

Фикс:
- Для API-mode использовать gRPC stubs/SDK.
- Если нужен офлайн-пайплайн, переходить в `csv`-mode и явно фиксировать ограничения.

## Access Denied On Billing Account

Причина: нет прав на платежный аккаунт.

Фикс:
- Проверить роль `billing.accounts.viewer` или `billing.accounts.getReport`.
- Уточнить, к какому `billing_account_id` есть доступ.

## Locale Expected But Ignored

Причина: в текущих request схемах методов Billing Usage API нет поля `locale`.

Фикс:
- Использовать правило `locale=ru` по умолчанию только для методов, где параметр действительно существует.
- Для `ConsumptionCore/Metadata` явно указывать, что локаль в запросе не поддерживается.
- Для CSV-выгрузки нормализовать колонку `locale` (`ru|en`) и применять fallback `ru`.

## S3 Select Is Not Available

Причина: S3 Select в Object Storage не включен для аккаунта.

Фикс:
- Проверить доступность функции через техподдержку Yandex Cloud.
- Если недоступно, использовать `csv_local` (полная выгрузка и локальная обработка).

## S3 Select Query Fails

Причина: в S3 Select языке не поддерживаются `JOIN` и вложенные запросы.

Фикс:
- Упростить SQL до single-table запроса по `S3Object`.
- Применять фильтрацию и базовые агрегации, а сложную логику делать после выгрузки.

## Access Denied On S3 Select

Причина: не настроены access key/secret key или нет прав на чтение объекта в бакете.

Фикс:
- Проверить профиль AWS CLI для Object Storage.
- Проверить права на объект и bucket для `select-object-content`.

## Totals Do Not Match

Причина: смешение валют, пропущенные строки, неверная трактовка credit.

Фикс:
- Нормализовать валюту.
- Проверить полноту входных данных.
- Суммировать `credit_details[].credit` в `credits_total`.
- Явно проверять формулу: `expense_total = cost_total + credits_total`.

## Missing Resource IDs

Причина: источник не содержит `resource_id` для части SKU.

Фикс:
- Использовать fallback группировку по `service`/`sku`.

## Partial Scope

Причина: нет доступа к части облаков/folders.

Фикс:
- Явно отмечать `incomplete_scope` в limitations.

## Wrong Time Window

Причина: неверные `start_time/end_time` (timezone/границы периода) приводят к неполному отчету.

Фикс:
- Передавать `start_time` и `end_time` в UTC (RFC3339).
- Для суммарной сверки использовать одинаковое окно и одинаковые фильтры для выбранного набора `Get*UsageReport` вызовов.
