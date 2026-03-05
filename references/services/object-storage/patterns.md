# Object Storage Patterns

## Pattern: Safe Upload Pipeline

- Нормализуй путь объекта (`prefix/date/id`).
- Проверяй размер/тип перед upload.
- Возвращай checksum и итоговый URI.

## Pattern: Inventory Export

- Собирать список объектов постранично.
- Нормализовать поля: `bucket, key, size, modified_at`.
- Для больших выборок использовать потоковый вывод (`jsonl`).

## Pattern: S3 Select For Billing CSV

- Для CSV детализации в бакете применять `s3api select-object-content` вместо полной выгрузки.
- Ограничивать запросы фильтрами по `date`, `service_id`, `resource_id`, `sku_id`.
- Передавать только нужные колонки в downstream-анализ.
