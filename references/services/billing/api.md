# Billing API/SDK Notes

## Canonical Sources

- Docs: `https://yandex.cloud/ru/docs/billing/`
- Get charges via API: `https://yandex.cloud/ru/docs/billing/operations/get-charges-via-api`
- Folder report format: `https://yandex.cloud/ru/docs/billing/operations/get-folder-report#format`
- S3 Select language: `https://yandex.cloud/ru/docs/storage/concepts/s3-select-language`
- Billing resource detailing tutorial: `https://yandex.cloud/ru/docs/billing/tutorials/billing-resource-detailing`
- Billing resource detailing tutorial (Object Storage): `https://yandex.cloud/ru/docs/storage/tutorials/billing-resource-detailing`
- Cloud API proto: `https://github.com/yandex-cloud/cloudapi`
- ConsumptionCore gRPC: `https://yandex.cloud/ru/docs/billing/usage/api-ref/grpc/ConsumptionCore/`
- MetadataService gRPC: `https://yandex.cloud/ru/docs/billing/usage/api-ref/grpc/MetadataService/`

## Transport And Endpoint

- Billing Usage API доступен через gRPC endpoint: `billing.api.cloud.yandex.net:443`.
- Основные сервисы:
  - `yandex.cloud.billing.usage_records.v1.ConsumptionCoreService`
  - `yandex.cloud.billing.usage_records.v1.MetadataService`

## Access

- Для чтения отчета нужен доступ к платежному аккаунту:
  - роль `billing.accounts.viewer`; или
  - роль `billing.accounts.getReport`.

## Main Methods

- `ConsumptionCoreService.GetBillingAccountUsageReport`
- `ConsumptionCoreService.GetCloudUsageReport`
- `ConsumptionCoreService.GetFolderUsageReport`
- `ConsumptionCoreService.GetServiceUsageReport`
- `ConsumptionCoreService.GetSKUUsageReport`
- `ConsumptionCoreService.GetResourceUsageReport`
- `ConsumptionCoreService.GetLabelKeyUsageReport`

Все методы выше принимают `UsageReportRequest` с полями:
- `billing_account_id`
- `start_date/end_date` (Timestamp)
- фильтры `cloud_ids | folder_ids | service_ids | sku_ids | resource_ids | labels`
- `aggregation_period` (`DAY|WEEK|MONTH|QUARTER|YEAR`)

## Locale Policy

- Базовое правило: если API-метод поддерживает параметр локали, по умолчанию использовать `locale=ru`.
- По текущему gRPC-справочнику Billing Usage API параметр `locale` в request отсутствует.
- Значение `locale` (`ru|en`) присутствует в формате CSV выгрузки детализации (колонка `locale`), но это поле результата, а не входной параметр методов ConsumptionCore/Metadata.
- В разных разделах документации могут встречаться разные имена операций (`GetDetailedUsage/GetUsage` и `*UsageReport`), но в проверенных request-схемах поле `locale` не обнаружено.

Проверка по методам из `get-charges-via-api`:
- `ConsumptionCoreService.GetBillingAccountUsageReport` -> `locale` в request: нет
- `ConsumptionCoreService.GetCloudUsageReport` -> `locale` в request: нет
- `ConsumptionCoreService.GetFolderUsageReport` -> `locale` в request: нет
- `ConsumptionCoreService.GetServiceUsageReport` -> `locale` в request: нет
- `ConsumptionCoreService.GetSKUUsageReport` -> `locale` в request: нет
- `ConsumptionCoreService.GetResourceUsageReport` -> `locale` в request: нет
- `ConsumptionCoreService.GetLabelKeyUsageReport` -> `locale` в request: нет
- `MetadataService.GetUsage` -> `locale` в request: нет
- `MetadataService.GetCloud` -> `locale` в request: нет
- `MetadataService.GetLabel` -> `locale` в request: нет
- `MetadataService.GetResourceIDs` -> `locale` в request: нет

## Filters And Grouping

- В `UsageReportRequest` доступны фильтры:
  - `service_ids`, `sku_ids`, `cloud_ids`, `folder_ids`, `resource_ids`, `labels`.
- Группировка определяется выбранным API-методом:
  - `GetResourceUsageReport` -> ресурсный срез;
  - `GetSKUUsageReport` -> SKU-срез;
  - `GetServiceUsageReport` -> сервисный срез;
  - и т.д.

## Data Model For Reconciliation

- На строке детализации учитывай:
  - `cost`
  - `credit_details[].credit`
  - `expense`
- Для агрегатов используй:
  - `cost_total`
  - `credits_total = sum(credit_details[].credit)`
  - `expense_total`
- Формула сверки: `expense_total = cost_total + credits_total`.

## Canonical Normalized Row Order

Для унификации API и CSV используй фиксированный порядок полей:

- `billing_account_id, billing_account_name, cloud_id, cloud_name, folder_id, folder_name, resource_id`
- `service_id, service_name, service, sku_id, sku_name, sku`
- `date, currency, pricing_quantity, pricing_unit`
- `cost, credit, expense, monetary_grant_credit, volume_incentive_credit, cud_credit, misc_credit`
- `label, locale, updated_at, exported_at`

## Data Sources

- `api_direct` для автоматизации и near-real-time сверки.
- `csv_local` для офлайн-аналитики и fallback.
- `csv_s3_select`: CSV детализация в Object Storage + SQL-предфильтрация через `s3api select-object-content`.

## CSV In Bucket + S3 Select

- Поддерживаемый flow:
  - включить регулярную выгрузку поресурсной детализации в бакет;
  - читать CSV из бакета через S3 Select;
  - отдавать результат в нормализатор и агрегатор.
- В Yandex Object Storage S3 Select доступен через запрос в техподдержку.
- Ключевые ограничения S3 Select языка:
  - нет `JOIN`;
  - нет вложенных запросов;
  - ориентируйся на простые фильтры и агрегации по одной таблице `S3Object`.

Пример запроса для нормализованной выборки:
- `SELECT billing_account_id, billing_account_name, cloud_id, cloud_name, folder_id, folder_name, resource_id, service_id, service_name, sku_id, sku_name, "date", currency, pricing_quantity, pricing_unit, cost, credit, monetary_grant_credit, volume_incentive_credit, cud_credit, misc_credit, locale, updated_at, exported_at FROM S3Object`

## Rule

Если API недоступен или не покрывает конкретный сценарий, допускается `csv`-mode с явной пометкой ограничений.
