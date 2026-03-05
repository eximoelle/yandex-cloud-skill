# Billing Patterns

## Pattern: Top-N Cost Drivers

- Для API-mode использовать `ConsumptionCoreService.Get*UsageReport`:
  - обычно `GetResourceUsageReport` для top по ресурсам;
  - `GetSKUUsageReport`/`GetServiceUsageReport` для SKU/Service срезов.
- Нормализовать строку:
  - `cost`
  - `credits_total = sum(credit_details[].credit)`
  - `expense`
- Группировать по `resource_id` (предпочтительно), fallback: `service_id` или `sku_id`.
- Сортировать по убыванию и брать `top_n`.

## Pattern: Reconciliation Block

- Считать:
  - `cost_total`
  - `credits_total`
  - `expense_total`
- Явно выводить сверку: `expense_total = cost_total + credits_total`.

## Pattern: Locale Handling

- Для API запросов придерживаться default policy: `locale=ru`, если метод поддерживает параметр.
- Для методов Billing Usage API без `locale` в request:
  - не подставлять фиктивный параметр;
  - явно фиксировать ограничение в `limitations`.
- Для CSV-детализации нормализовать `locale` с fallback в `ru`.

## Pattern: S3 Select Pre-Filter

- Для `csv_s3_select` выполнять раннюю фильтрацию прямо в Object Storage:
  - `WHERE "date" BETWEEN ...`
  - `AND service_id IN (...)`
  - `AND resource_id = ...`
- Возвращать поля в каноническом порядке billing CSV:
  - `billing_account_id, billing_account_name, cloud_id, cloud_name, folder_id, folder_name, resource_id`
  - `service_id, service_name, sku_id, sku_name, date, currency, pricing_quantity, pricing_unit`
  - `cost, credit, monetary_grant_credit, volume_incentive_credit, cud_credit, misc_credit, locale, updated_at, exported_at`.
- После выборки через S3 Select продолжать стандартный flow:
  - нормализация;
  - расчет агрегатов;
  - top-N.

## Pattern: Metadata Enrichment

- Для человекочитаемого отчета обогащай `service_id/sku_id` через:
  - `MetadataService.GetService`
  - `MetadataService.GetSku`
