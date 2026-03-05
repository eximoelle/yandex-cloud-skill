# Compute API/SDK Notes

## Canonical Sources

- Cloud API proto: `https://github.com/yandex-cloud/cloudapi`
- Docs: `https://yandex.cloud/ru/docs/compute/`
- Terraform resource docs: `terraform-provider-yandex`

## Typical Operations

- create/list/get instance
- start/stop/restart
- attach metadata/service account

## Rule

- SDK first for common lifecycle.
- Cloud API fallback for missing SDK operations.
