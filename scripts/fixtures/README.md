# Fixtures For Scripts

Этот каталог содержит примеры входных данных для утилит и workflow скилла.

## Files

- `billing_sample.csv`: минимальная выборка (10 строк) из анонимизированного YC billing CSV,
  с тем же порядком и именами колонок, что в экспорте детализации (per-resource).
- `billing_detail_overall_sanitized_sample.csv`: сокращенная (320 строк) анонимизированная выборка
  из CSV детализации "общая".
- `billing_detail_per_resource_sanitized_sample.csv`: сокращенная (320 строк) анонимизированная
  выборка из CSV детализации "поресурсная".
- `billing_api_resource_usage_sample.json`: sample-ответ `ConsumptionCoreService.GetResourceUsageReport`
  для replay/офлайн-проверки `source_mode=api_direct` в billing workflow.
- `billing_s3_select_resource_detailing.sql`: SQL-шаблон S3 Select для выборки колонок
  в каноническом порядке billing CSV.

## Schema Notes

`billing_sample.csv` и `billing_detail_*_sanitized_sample.csv` используют реальные названия полей
YC CSV export schema, включая:

- идентификаторы и контекст: `billing_account_id`, `cloud_id`, `folder_id`, `resource_id`;
- сервисные поля: `service_id`, `service_name`, `sku_id`, `sku_name`;
- денежные поля: `cost`, `credit`, `monetary_grant_credit`, `volume_incentive_credit`,
  `cud_credit`, `misc_credit`;
- служебные поля: `locale`, `updated_at`, `exported_at`.

## Sanitization Notes

Для `billing_detail_*_sanitized_sample.csv` замаскированы идентификаторы и labels:

- `billing_account_id`, `billing_account_name`
- `cloud_id`, `cloud_name`
- `folder_id`, `folder_name`
- `resource_id`, `service_id`, `sku_id`
- все колонки вида `label.user_labels.*`

Числовые поля (`cost`, `credit`, `pricing_quantity`) сохранены для реалистичного анализа агрегатов.
