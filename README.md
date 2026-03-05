# Yandex Cloud Skill

Манифестный скилл для практических задач в Yandex Cloud: API/SDK, Terraform, troubleshooting, billing и MCP.

## Что это и когда использовать

Скилл рассказывает агенту про Yandex Cloud и показывает информацию и правила работы, которые нужно учитывать при выполнении релевантных задач, снимая с пользователя задачу по указанию источников непосредственно в промпте. Модульная структура должна решить задачу экономии контекста: сначала роутинг решения из описания задачи, а затем подключение лишь релевантной информации о платформе.

Скилл полезен, когда нужно:

- получить рабочий скрипт под задачу в Yandex Cloud без необходимости рассказывать агенту о существовании SDK от Yandex Cloud; при этом если в описанных SDK нужного метода нет — агент будет самостоятельно изучать протобуфы в Cloud API для решения задачи;
- подготовить Terraform-конфигурацию для типовых инфраструктурных сценариев с понятными шагами проверки;
- разобрать эксплуатационные проблемы (конфигурация, API/SDK, сеть, квоты) с конкретным планом проверки и исправления;
- обработать данные по расходам, ресурсам, прайс-листу из Cloud Billing API или csv-файла, и вывести в удобном формате;
- опираться на встроенную базу источников, разделённых на три Tier от официальной документации и библиотеки решений до внешних материалов, что позволит не передавать источники в промпте; при этом критичные утверждения сверяются по Tier 1 (по официальной документации);
- решить YC-задачу от запроса до результата без долгого ручного поиска по документации.

## Базовые принципы и допущения

- Один исполняемый скрипт: `scripts/yc_mcp_catalog.py`.
- Один источник истины: `references/contracts/skill_manifest.yaml`.
- Manifest-first архитектура (а не Markdown-first): в `SKILL.md` описывает только: 
    - когда активировать скилл
    - явный приоритет источников (manifest — canonical, при конфликте он главнее)
    - минимальный load order
    - список доступных подкоманд.
- Все правила routing, policy, auth, fallback хранятся только в `skill_manifest.yaml`.
- Жесткая валидация схем:
- `references/contracts/skill_manifest.schema.json`
- `references/contracts/mcp_catalog.schema.json`
- Единый runtime-формат ответа: JSON envelope v2.
- Производные markdown-файлы не редактируются вручную и не используются как источник истины в случае конфликтов логики.
- `README.md` остаётся как подробное human-friendly руководство.
- В скрипте есть риск гонки, который можно решить блокировками и атомарной записью, но это сознательно не сделано с допущением, что в один момент времени не будет параллельно запущено два агента или две сессии внутри одного агента, в которых будут запускаться команды по работе с MCP. Остаётся риск аварийного прерывания во время записи, который можно покрыть дисциплиной: после `refresh-mcp-catalog` и `render-docs` прогонять `validate-contracts`.
- Структура скилла делалась с расчётом на возможное расширение, научение агента конкретным юзкейсам и прнципам работы с конкретными сервисами. В качестве референсной модели использовался скилл [Cloudflare Deploy](https://github.com/openai/skills/tree/main/skills/.curated/cloudflare-deploy) от OpenAI.

## Быстрый старт

Предусловия:

- `uv` установлен (см. [официальную инструкцию](https://docs.astral.sh/uv/getting-started/installation/))
- при первом вызове агентом `uv run ...` на чистой системе `uv` сам создаст `.venv` и установит зависимости из `uv.lock` (или `pyproject.toml`), поэтому отдельный шаг установки виртуального окружения обычно не нужен
- если в окружении запрещена автозагрузка интерпретатора, предварительно установи `Python 3.11+`.
- Все Python-команды в этом репозитории запускаются через `uv run ...` (то есть, без `pip`/`poetry`/`pipenv`).
- Текущие runtime-зависимости скриптов: `pyyaml`, `jsonschema` (установятся автоматически при первом `uv run`).
- `uv sync` можно выполнить отдельно при необходимости (например, прогрев окружения в CI или перед офлайн-работой).

Установка:

Предполагается, что скилл используется в предварительно установленном [OpenAI Codex](https://openai.com/ru-RU/codex/). Для работы достаточно Codex CLI и [плагина для Visual Studio Code](https://marketplace.visualstudio.com/items?itemName=openai.chatgpt).

1. Перейти в `~/.codex/` и клонировать репозиторий `git clone https://github.com/eximoelle/yandex-cloud-skill.git`
2. MCP-сервер генеративного поиска по документации Yandex Cloud можно сразу же самостоятельно прописать в конфиг Codex. Для этого открыть `~/.codex/config.toml`:
```toml
[mcp_servers.documentation-mcp-server]
url = "https://docs.mcp.cloud.yandex.net/mcp"
```

Как агент выбирает скилл:

1. Агент просматривает доступные скиллы и сравнивает задачу с их `description`.
2. Если задача про YC (API/SDK, IAM, Terraform, troubleshooting, billing, MCP), выбирается `yandex-cloud-skill`.
3. Если нужно принудительно использовать именно этот скилл, укажи его явно в запросе:
- `$yandex-cloud-skill: помоги настроить доступ к Object Storage через Terraform`
- `Используй yandex-cloud-skill для диагностики Permission denied в IAM`

Примеры пользовательских промпты и как агент решает задачу:

1. `Напиши Python-скрипт, который покажет мне все имеющиеся облачные ресурсы во всех облаках и каталогах моей организации Yandex Cloud`
- Агент относит запрос к `inventory`.
- Выбирает MCP-first путь для discovery, а при недоступности MCP автоматически переходит на fallback (`yc` CLI / SDK / Cloud API).
- Готовит рабочий скрипт (обычно с обходом organization -> clouds -> folders -> сервисы), добавляет запуск, формат вывода и ограничения покрытия.

2. `Собери Terraform-проект для VPC, подсетей и группы VM в двух зонах, чтобы можно было сразу сделать plan/apply`
- Агент относит запрос к `terraform_iac`.
- Формирует структуру Terraform (provider, modules, variables, outputs) под YC-практики и выбранный сервисный scope.
- Добавляет команды проверки (`fmt`, `validate`, `plan`) и поясняет, какие параметры пользователь должен подставить перед `apply`.

3. `У меня Permission denied при создании/чтении ресурсов, найди причину и дай план исправления`
- Агент относит запрос к `auth` или `troubleshooting`.
- Проверяет auth-контекст (аккаунт, роли, folder/cloud scope, IAM token), затем локализует причину по шагам.
- Возвращает минимальный и проверяемый план исправления (какие роли, где выдать, что перепроверить, чем подтвердить фиксацию).

4. `Напиши скрипт для выгрузки детализации расходов по всем облакам и каталогам за прошлый месяц в CSV`
- Агент относит запрос к `billing_detail`.
- Подбирает интерфейс получения биллинга, учитывает фильтры по периоду и разрезам.
- Возвращает готовый скрипт/пайплайн выгрузки, формат колонок и проверку полноты данных.

## Канонические файлы и роль каждого

- `references/contracts/skill_manifest.yaml`: routing, policies, MCP-логика, источники, auth decision table.
- `references/mcp/catalog.yaml`: машиночитаемый реестр MCP-серверов.
- `references/navigation.md`: производная навигация task_type/language.
- `references/mcp/registry.md`: производная таблица MCP-серверов.
- `references/mcp/codex-setup.md`: производная памятка по MCP setup.

## Команды скрипта

1. `validate-contracts`
- Валидирует manifest и MCP catalog по JSON Schema.

2. `refresh-mcp-catalog`
- Обновляет `references/mcp/catalog.yaml` из `https://github.com/yandex-cloud/mcp`.
- Валидирует результат до записи в файл.
- При `--offline` использует последний валидный локальный каталог.

3. `resolve-mcp`
- Выбирает лучший MCP-сервер по `task_type/service/intent/operation`.
- Если подходящего MCP нет, возвращает `status=mcp_unavailable` с `data.non_mcp_fallback`.

4. `plan-mcp-install`
- Возвращает install command, installed-state и состояние auth env.
- Проверка установленности идет через:
- `codex mcp list --json`

5. `report-mcp-install`
- Возвращает статус установленности и текущий config сервера.
- Использует:
- `codex mcp list --json`
- `codex mcp get <name> --json`

6. `render-docs`
- Перегенерирует все производные docs из manifest + catalog.

## Единый формат вывода (Envelope v2)

Все subcommands возвращают:

- `version`
- `status`
- `data`
- `checks`
- `limitations`
- `sources`
- `errors`

Это обязательный контракт для автоматизации и тестов.

## Как агент понимает, какой workflow применять

Порядок принятия решения:

1. Нормализация `task_type`:
- lower-case, `-` -> `_`.

2. Поиск workflow через `routing.task_workflow` в manifest:
- `auth` -> `references/workflows/auth.md`
- `api_sdk` -> `references/workflows/api_sdk.md`
- `terraform_iac` -> `references/workflows/terraform_iac.md`
- `troubleshooting` -> `references/workflows/troubleshooting.md`
- `inventory` -> `references/workflows/inventory.md`
- `billing_detail` -> `references/workflows/billing_detail.md`
- `mcp_setup` -> `references/workflows/mcp_setup.md`

3. При необходимости берется language profile из `languages.profiles`.

4. Для MCP-контекстов запускается `resolve-mcp`.

## Как работает MCP-резолв

`resolve-mcp` собирает теги из:

- входного `intent`;
- `mcp.service_intents[service]`;
- `mcp.task_type_intents[task_type]`.

Дальше:

1. Берет только `status != deprecated`.
2. Для `toolkit-mcp-server` применяет ограничения:
- сервис должен быть в `mcp.toolkit_supported_services`;
- операция должна быть в `mcp.toolkit_supported_tools`.
3. Считает пересечение тегов.
4. Выбирает лучший кандидат по сортировке:
- больше match score;
- ниже `discovery_priority`;
- лексикографически по `name`.

Если совпадений нет:

- возвращается `status=mcp_unavailable`;
- заполняется `data.non_mcp_fallback`.

## Что происходит, если задача не решается через MCP

При `mcp_unavailable` скилл не останавливается, а отдает fallback-план из `mcp.non_mcp_policy`:

- `mode=autonomous_non_mcp`;
- `selection_principle=mcp_first_then_generic_fallback`;
- `interfaces`: `yc_cli`, `sdk`, `cloudapi`, `terraform`;
- `workflow_hint`: куда перейти дальше;
- `official_sources`: какие ссылки использовать;
- `next_steps`: пошаговое продолжение без MCP.

Упрощенный принцип в текущем контракте:

- все, что покрывает MCP, пробуем через MCP;
- если MCP не найден под контекст, идем по generic non-MCP интерфейсам.

## Permission denied и IAM token

Если сервер MCP требует IAM token (`auth.mode=iam_token`), install plan включает `--bearer-token-env-var YC_IAM_TOKEN`.

Если required env отсутствуют или пустые:

- `plan-mcp-install` и `report-mcp-install` не возвращают `status=permission_denied` только из-за missing env;
- в `data.auth_env.missing_env` перечисляются недостающие переменные;
- это предупреждение, а не финальная интерпретация ошибки YC.

Когда ошибка реально пришла из Yandex Cloud через MCP tool-вызов:

- если это `Permission denied`, в чат возвращается каноническое сообщение из manifest:
   `Yandex Cloud вернул Permission denied, проверьте роли сервисного аккаунта или установку и актуальность переменной YC_IAM_TOKEN и перезапустите Codex, если дело в ней`;
- если это другая ошибка YC, в чат возвращается исходная ошибка + рекомендации по проверке и исправлению.

TODO: разобрать, какие это «другие ошибки», и добавить в хэлпер наряду с `Permission denied`. Но пока MCP в превью, контракт и API могут меняться со стороны YC, поэтому не делаем.

Отдельно важно:

- интерпретация `Permission denied` делается только по фактическому ответу YC, а не по локальному precheck;
- проверка installed-state использует только JSON-CLI (`codex mcp list/get --json`).

## Какие источники и в каком порядке используются

Порядок использования источников установлен политикой `sources_policy` в манифесте:

1. Tier 1:
- официальная документация YC, Cloud API, официальные SDK, YC Terraform provider.

2. Tier 2:
- библиотека решений `https://github.com/yandex-cloud-examples`.

3. Tier 3:
- внешние источники с релевантными туториалами.

Правила:

- по умолчанию язык документации: `ru`;
- сначала Tier 1;
- Tier 2/3 только как дополнение, критичные вещи подтверждаются Tier 1.

## Папка `references/services/<service>`

Сейчас готовы модули:

- `billing`
- `compute`
- `iam`
- `object-storage`
- `resource-manager`
- `vpc`

В каждом модуле одинаковая структура:

- `README.md`: scope модуля и порядок чтения;
- `configuration.md`: входные параметры и базовые настройки;
- `api.md`: API/SDK точки входа;
- `patterns.md`: типовые рабочие паттерны;
- `gotchas.md`: частые ошибки и диагностика.

Как добавить новый сервисный модуль:

1. Создать `references/services/<new-service>/`.
2. Добавить 5 файлов: `README.md`, `configuration.md`, `api.md`, `patterns.md`, `gotchas.md`.
3. В `README.md` модуля явно прописать Scope и Reading Order.
4. Если сервис должен участвовать в MCP-резолве, дополнить manifest:
- `mcp.service_intents`;
- при необходимости `mcp.toolkit_supported_services`.
5. Запустить:
- `uv run scripts/yc_mcp_catalog.py validate-contracts`
- `uv run scripts/yc_mcp_catalog.py render-docs`

## Папка `references/workflows`

`references/workflows/*.md` сейчас производные файлы (генерируются командой `render-docs`) и содержат короткую policy-рамку для task_type.

Как добавить новый предопределенный workflow:

1. Добавить новый ключ в `routing.task_workflow` манифеста, например:
   `new_task: references/workflows/new_task.md`
2. При необходимости добавить `mcp.task_type_intents.new_task`.
3. Запустить `render-docs` для генерации файла workflow.
4. Проверить, что `validate-contracts` проходит.

Порядок сопоставления задачи workflow:

1. Агент определяет `task_type` из пользовательской формулировки.
2. Нормализует формат (`-` -> `_`).
3. Ищет в `routing.task_workflow`.
4. Если workflow не найден в явном виде, для fallback-подсказки используется `references/navigation.md`.

## Детерминизм и стабильность

За стабильность отвечают:

- строгие JSON Schema валидации до записи;
- сортировки при генерации и резолве;
- единый envelope v2;
- retry/backoff для сетевых запросов при refresh;
- `--offline` режим на последнем валидном каталоге;
- unit-тесты на контракт, fallback, MCP JSON parsing и deterministic render.

## Производные файлы (не редактировать вручную)

- `references/navigation.md`
- `references/workflows/*.md`
- `references/languages/*.md`
- `references/mcp/registry.md`
- `references/mcp/codex-setup.md`

Обновление только через:

```bash
uv run scripts/yc_mcp_catalog.py render-docs
```

## Рекомендуемый цикл изменений

1. Меняй только канонические источники истины:
- `references/contracts/skill_manifest.yaml`
- `references/mcp/catalog.yaml` (обычно через `refresh-mcp-catalog`)

2. Делай проверки:

```bash
uv run scripts/yc_mcp_catalog.py validate-contracts
uv run python -m unittest discover -s tests -p "test_*.py"
```

3. Заново генерируй зависимые документы:

```bash
uv run scripts/yc_mcp_catalog.py render-docs
```

4. Повторно проверяй `validate-contracts`.
