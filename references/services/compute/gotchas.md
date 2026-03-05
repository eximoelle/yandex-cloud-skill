# Compute Gotchas

## ResourceExhausted

Причина: недостаточная квота CPU/RAM/дисков в зоне.

Фикс:
- Уменьшить размер ресурса или выбрать другую зону.

## InvalidArgument

Причина: несовместимые параметры образа, платформы или сети.

Фикс:
- Сверить параметры с документацией и минимальным working example.

## PermissionDenied

Причина: не хватает прав на create/list instance.

Фикс:
- Проверить IAM роль на folder scope.
