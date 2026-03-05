# Compute Patterns

## Pattern: Minimal VM Provision

- Создать VPC/subnet заранее.
- Развернуть минимальную VM.
- Проверить статус и network reachability.

## Pattern: Safe Change

- Для изменения конфигурации сначала получить текущее состояние.
- Применять изменения малыми шагами.
- После каждого шага выполнять health-check.
