# Billing Configuration

## Required Inputs

- `source_mode`: `api_direct | csv_local | csv_s3_select`
- период:
  - для API: `start_time` и `end_time` (RFC3339, UTC)
  - для CSV: `month=YYYY-MM` или `date_from/date_to`
- `billing_account_id` (обязательно для `api_direct`)
- `aggregation_period`: `daily | weekly | monthly | quarterly | yearly` (для UsageReport API)
- `api_method` (для `api_direct`): `billing_account | cloud | folder | service | sku | resource | label`
- `iam_token` (для `api_direct`): `--iam-token` или `YC_IAM_TOKEN`
- `api_endpoint` (default `billing.api.cloud.yandex.net:443`)
- `locale`: `ru | en` (default: `ru` для запросов, где параметр доступен)
- для `csv_local`: `csv_path`
- для `csv_s3_select`:
  - `bucket`
  - `key` (путь к объекту CSV)
  - `s3_select_query`
  - `s3_select_query_file` (опционально, вместо inline SQL)
  - `s3_endpoint` (default `https://storage.yandexcloud.net`)
  - настроенный AWS CLI профиль для Object Storage (access key/secret key + права чтения объекта)
- опциональные фильтры API:
  - `service_ids`, `sku_ids`, `cloud_ids`, `folder_ids`, `resource_ids`, `labels`
- опциональный `group_by`:
  - `resource_id | service_id | sku_id | cloud_id | folder_id | label`
- валюта и формат вывода

## Baseline Steps

1. Зафиксировать границы периода.
2. Проверить права на платежный аккаунт (`billing.accounts.viewer` или `billing.accounts.getReport`).
3. Для `csv_s3_select` проверить, что регулярная выгрузка детализации в бакет включена и S3 Select доступен.
4. Получить данные из API или CSV.
5. Применить policy локали: `ru` по умолчанию; если метод не поддерживает `locale`, зафиксировать это в limitations.
6. Нормализовать строки в канонический формат:
   - `billing_account_id, billing_account_name, cloud_id, cloud_name, folder_id, folder_name, resource_id`
   - `service_id, service_name, service, sku_id, sku_name, sku`
   - `date, currency, pricing_quantity, pricing_unit`
   - `cost, credit, expense, monetary_grant_credit, volume_incentive_credit, cud_credit, misc_credit`
   - `label, locale, updated_at, exported_at`
7. Рассчитать агрегаты и сверку формулы.

## Validation

- Все строки в одной валюте или помечена конвертация.
- `expense_total = cost_total + credits_total`.
