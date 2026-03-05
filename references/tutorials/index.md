# Tutorials Index

Используй этот индекс, когда запрос выглядит как практический гайд:
- `пошагово` / `step-by-step`;
- `как развернуть` / `quickstart`;
- `reference architecture` / типовой deployment-сценарий.

## Official Tutorials Catalog (Tier 1)

Категория -> `task_type` -> ссылка:
- Security -> `auth | troubleshooting | terraform_iac` -> `https://yandex.cloud/ru/docs/tutorials/security/`
- Archive and backups -> `terraform_iac | troubleshooting` -> `https://yandex.cloud/ru/docs/tutorials/archive-and-backups/`
- Development and testing -> `api_sdk | terraform_iac | troubleshooting` -> `https://yandex.cloud/ru/docs/tutorials/dev/`
- Basic infrastructure -> `terraform_iac | inventory | troubleshooting` -> `https://yandex.cloud/ru/docs/tutorials/infrastructure-management/`
- Container infrastructure -> `terraform_iac | api_sdk | troubleshooting` -> `https://yandex.cloud/ru/docs/tutorials/container-infrastructure/`
- Applied solutions -> `api_sdk | terraform_iac` -> `https://yandex.cloud/ru/docs/tutorials/apps/`
- Data Platform -> `api_sdk | terraform_iac | billing_detail` -> `https://yandex.cloud/ru/docs/tutorials/data-platform/`
- Microsoft products -> `terraform_iac | troubleshooting` -> `https://yandex.cloud/ru/docs/tutorials/microsoft/`
- Architecture and networking -> `terraform_iac | troubleshooting | inventory` -> `https://yandex.cloud/ru/docs/tutorials/routing/`
- Analytics and visualization -> `api_sdk | billing_detail | inventory` -> `https://yandex.cloud/ru/docs/tutorials/analytics/`
- Serverless -> `api_sdk | terraform_iac | troubleshooting` -> `https://yandex.cloud/ru/docs/tutorials/serverless/`
- ML and AI -> `api_sdk | terraform_iac` -> `https://yandex.cloud/ru/docs/tutorials/ml-ai/`

## SDK Quickstart And Catalog (Tier 1)

Используй этот блок как fast-path для `task_type=api_sdk`, когда нужно быстро стартовать с кодом:
- SDK quickstart -> `https://yandex.cloud/ru/docs/overview/sdk/quickstart`
- SDK overview (полный список SDK) -> `https://yandex.cloud/ru/docs/overview/sdk/overview`

## YC CLI Reference (Tier 1)

Используй этот блок как fast-path для разовых live-задач, когда `yc` CLI быстрее и проще, чем писать API/SDK-код:
- CLI command reference -> `https://yandex.cloud/ru/docs/cli/cli-ref/`

## Terraform In Infrastructure Tools (Tier 1)

Используй этот блок как fast-path для `task_type=terraform_iac`, особенно для задач про подготовку окружения, VPC, VM и группы VM:
- Раздел инструментов (базовая инфраструктура) -> `https://yandex.cloud/ru/docs/tutorials/infrastructure/#tools`
- Начало работы с Terraform -> `https://yandex.cloud/ru/docs/tutorials/infrastructure-management/terraform-quickstart`
- Источники данных Terraform -> `https://yandex.cloud/ru/docs/tutorials/infrastructure-management/terraform-data-sources`
- Загрузка состояний Terraform в Object Storage -> `https://yandex.cloud/ru/docs/tutorials/infrastructure-management/terraform-state-storage`
- Использование модулей Yandex Cloud в Terraform -> `https://yandex.cloud/ru/docs/tutorials/infrastructure-management/terraform-modules`
- Создание VM и группы VM с помощью Terraform (пример) -> `https://yandex.cloud/ru/docs/tutorials/infrastructure/coi-with-terraform`

## Local Tutorial Packs

- Terraform patterns -> `references/tutorials/terraform.md`
- SDK/API/CLI patterns -> `references/tutorials/sdk.md`

## Fast Selection Rule

1. Выбери категорию по домену задачи.
2. Выбери интерфейс с минимальной сложностью: `yc` CLI, SDK или Cloud API.
3. Если задача разовая/операционная и `yc` CLI быстрее, используй CLI-path из `references/tutorials/sdk.md` и блок `YC CLI Reference (Tier 1)`.
4. Если нужен код (`api_sdk`), сначала проверь блок `SDK Quickstart And Catalog (Tier 1)`.
5. Для `terraform_iac` сначала проверь блок `Terraform In Infrastructure Tools (Tier 1)`.
6. Возьми минимум одну Tier 1 ссылку из каталога выше.
7. Адаптируй шаги под контекст (`folder_id/cloud_id/region/zone`, IAM, quotas).
8. При использовании Tier 2 примеров (`yandex-cloud-examples`) подтверди критичные параметры по Tier 1.

Корневая страница каталога: `https://yandex.cloud/ru/docs/tutorials/`.
