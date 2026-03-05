# Object Storage Gotchas

## AccessDenied

Причина: недостаточные права на bucket или объект.

Фикс:
- Проверить роль/политику на точном scope.

## Signature/Auth Errors

Причина: неверный тип credential или просроченный токен.

Фикс:
- Проверить выбранную схему аутентификации и ротацию.

## Unexpected Object Listing

Причина: неверный prefix или пагинация.

Фикс:
- Явно задавать prefix/page token и проверять полноту выборки.
