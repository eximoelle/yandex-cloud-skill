# VPC Gotchas

## Connectivity Failure

Причина: неверные security group правила или route.

Фикс:
- Проверить ingress/egress и целевой CIDR.

## Zone Mismatch

Причина: subnet и VM в разных зонах.

Фикс:
- Согласовать `zone` во всех ресурсах.

## Overexposed Rules

Причина: слишком широкие правила (`0.0.0.0/0`) без необходимости.

Фикс:
- Сузить источники и порты до фактической потребности.
