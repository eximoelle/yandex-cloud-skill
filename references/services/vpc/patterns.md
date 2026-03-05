# VPC Patterns

## Pattern: Minimal Private Network

- Один network, один subnet в целевой зоне.
- Security group с минимальным набором ingress.
- Явные egress-правила для необходимых outbound вызовов.

## Pattern: Compute + VPC Baseline

- Создать сеть до VM provisioning.
- Привязать VM к subnet явно.
- Проверить доступность до/после применения SG.
