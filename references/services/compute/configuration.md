# Compute Configuration

## Required Inputs

- `folder_id`
- `zone`
- образ/платформа
- network/subnet
- service account (если нужен доступ к другим сервисам)

## Baseline Steps

1. Проверить quota в зоне.
2. Проверить network/subnet и правила доступа.
3. Проверить IAM роли для create/list/start/stop операций.
4. Подготовить минимальный bootstrap без лишних опций.

## Validation

- VM создана в правильной зоне.
- Доступность/статус подтверждены после создания.
