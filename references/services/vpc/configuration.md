# VPC Configuration

## Required Inputs

- `folder_id`
- `network_name`
- `subnet_cidr`
- `zone`
- security policy (ingress/egress)

## Baseline Steps

1. Создать VPC network.
2. Создать subnet в нужной зоне.
3. Настроить security groups по принципу least exposure.
4. Проверить связность целевых ресурсов.

## Validation

- Ресурсы в correct subnet.
- Security rules соответствуют требуемым портам.
