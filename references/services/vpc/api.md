# VPC API/SDK Notes

## Canonical Sources

- Cloud API proto: `https://github.com/yandex-cloud/cloudapi`
- Docs: `https://yandex.cloud/ru/docs/vpc/`
- Terraform examples: `terraform-provider-yandex/examples`

## Typical Operations

- create/list/get network
- create/list/get subnet
- manage security groups and rules

## Rule

При troubleshooting сначала проверяй `scope` и `zone`, затем правила доступа.
