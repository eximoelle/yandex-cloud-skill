# Object Storage API/SDK Notes

## Canonical Sources

- Docs: `https://yandex.cloud/ru/docs/storage/`
- Cloud API proto: `https://github.com/yandex-cloud/cloudapi`
- Language SDK repos in `references/sources.md`

## Typical Operations

- list buckets/objects
- upload/download object
- manage ACL/policies
- run S3 Select (`s3api select-object-content`) for server-side CSV filtering

## Rule

- Для language SDK используй профили из `references/languages/`.
- Для операций вне SDK покрытия используй API fallback.
- Для Billing CSV в бакете предпочитай S3 Select для ранней фильтрации по дате/ресурсу/сервису.
