# Tutorials: SDK/API/CLI

## Preferred Sources

- SDK quickstart: `https://yandex.cloud/ru/docs/overview/sdk/quickstart`
- SDK overview: `https://yandex.cloud/ru/docs/overview/sdk/overview`
- YC CLI command reference: `https://yandex.cloud/ru/docs/cli/cli-ref/`
- Unified Cloud SDK repos:
  - `https://github.com/yandex-cloud/python-sdk`
  - `https://github.com/yandex-cloud/go-sdk`
  - `https://github.com/yandex-cloud/nodejs-sdk`
  - `https://github.com/yandex-cloud/java-sdk`
  - `https://github.com/yandex-cloud/dotnet-sdk`
- Service SDK docs:
  - AI Studio SDK -> `https://yandex.cloud/ru/docs/ai-studio/sdk/`
  - SpeechKit SDK (Python) -> `https://yandex.cloud/ru/docs/speechkit/sdk/python/`
  - Video SDK -> `https://yandex.cloud/ru/docs/video/sdk/`
  - YDB SDK -> `https://ydb.tech/docs/ru/reference/ydb-sdk/`
  - AWS SDK for Object Storage -> `https://yandex.cloud/ru/docs/storage/tools/sdk`
- `cloudapi` для fallback-методов.

## SDK Catalog (from Overview)

Используй как справочник "что вообще есть":

- Unified Cloud SDK:
  - Python -> `https://github.com/yandex-cloud/python-sdk`
  - Go -> `https://github.com/yandex-cloud/go-sdk`
  - Node.js -> `https://github.com/yandex-cloud/nodejs-sdk`
  - Java -> `https://github.com/yandex-cloud/java-sdk`
  - .NET -> `https://github.com/yandex-cloud/dotnet-sdk`
- Service SDK:
  - AI Studio Foundation Models -> `https://github.com/yandex-cloud/yandex-ai-studio-sdk`
  - SpeechKit -> `https://yandex.cloud/ru/docs/speechkit/sdk/python/`
  - Video SDK docs -> `https://yandex.cloud/ru/docs/video/sdk/`
  - YDB SDK docs -> `https://ydb.tech/docs/ru/reference/ydb-sdk/`
- AWS SDK (для Object Storage API) -> `https://yandex.cloud/ru/docs/storage/tools/sdk`

## Interface Selection Rule

Используй правило минимальной сложности:

1. Для разовых live-операций и быстрой диагностики выбирай `yc` CLI.
2. Для кода и повторяемых интеграций выбирай SDK.
3. Если метода нет в SDK, используй Cloud API fallback.

## YC CLI Fast Bricks (read-only by default)

Эти блоки ускоряют быстрые проверки существующей инфраструктуры:

1. Контекст профиля и identity:
   - `yc config profile list`
   - `yc iam whoami`
2. Быстрая проверка Compute в scope:
   - `yc compute instance list --folder-id <folder_id>`
3. Быстрая проверка сети в scope:
   - `yc vpc subnet list --folder-id <folder_id>`
4. Быстрая проверка папок:
   - `yc resource-manager folder list --cloud-id <cloud_id>`

Mutating-команды через `yc` CLI выполняй только после явного подтверждения пользователя.

## Auth Modes From SDK README

Используй эту матрицу перед генерацией кода:

1. Python SDK (`python-sdk`):
   - сервисный аккаунт через authorized key file;
   - сервисный аккаунт ВМ через metadata;
   - IAM token.
2. Go SDK (`go-sdk`):
   - пользовательский OAuth token (через `yc`);
   - сервисный аккаунт ВМ через metadata;
   - сервисный аккаунт через authorized key file.
3. Node.js SDK (`nodejs-sdk`):
   - IAM token;
   - OAuth token;
   - сервисный аккаунт ВМ через metadata.
4. .NET SDK (`dotnet-sdk`):
   - пользовательский OAuth token;
   - сервисный аккаунт ВМ через metadata;
   - сервисный аккаунт через authorized key file.
5. Java SDK (`java-sdk`):
   - в README нет полной матрицы auth, для старта используй quickstart-команды и `references/workflows/auth.md`.

## Quickstart Bricks (copy and adapt)

Эти блоки ускоряют "старт с нуля", затем адаптируй под `primary_service/dependent_services`:

1. Node.js:
   - `git clone https://github.com/yandex-cloud-examples/yc-sdk-quickstart-node-js.git`
   - `cd yc-sdk-quickstart-node-js`
   - `npm install`
   - `node index.js --secret-key <path_to_authorized_key.json>`
2. Go:
   - `git clone https://github.com/yandex-cloud-examples/yc-sdk-quickstart-go.git`
   - `cd yc-sdk-quickstart-go`
   - `go run list_versions.go --sa-key-path <path_to_authorized_key.json>`
3. Java:
   - `git clone https://github.com/yandex-cloud-examples/yc-sdk-quickstart-java.git`
   - `cd yc-sdk-quickstart-java`
   - `export IAM_TOKEN="<your_iam_token>"`
   - `mvn compile exec:java -Dexec.mainClass='yandex.cloud.examples.list.Compute' -Dexec.args='--key-file <path_to_auth_key_file>'`
4. .NET:
   - `git clone https://github.com/yandex-cloud-examples/yc-sdk-quickstart-dotnet.git`
   - `cd yc-sdk-quickstart-dotnet`
   - `dotnet run --key-file <path_to_auth_key_file>`
5. Python:
   - `git clone https://github.com/yandex-cloud-examples/yc-sdk-quickstart-python.git`
   - `cd yc-sdk-quickstart-python`
   - `python3 list-versions.py --service-account-key <path_to_auth_key_file>`

## Adaptation Checklist

1. Выбери интерфейс с минимальной сложностью: `yc` CLI, SDK или Cloud API.
2. Если быстрее через `yc` CLI, начни с preflight: `yc config profile list` и `yc iam whoami`, затем согласуй активный профиль с пользователем; при необходимости выполни `yc config profile activate <profile>` и повтори `yc iam whoami`.
3. Если нужен код, начни с quickstart brick для нужного языка.
4. Проставь auth/scope параметры из задачи (`folder_id/cloud_id/region/zone`).
5. Для production по умолчанию выбирай service account path из `references/workflows/auth.md`.
6. Если метода нет в SDK, добавь Cloud API fallback с явной пометкой.
7. Для mutating-команд через `yc` CLI сначала запроси явное подтверждение пользователя.
8. Заверши коротким smoke-check.
