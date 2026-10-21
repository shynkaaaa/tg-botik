# tg-botik

Telegram-бот с расписанием метро и командами FACEIT.

## Запуск

Установите [uv](https://docs.astral.sh/uv/getting-started/installation/), затем из корня репозитория выполните:

```sh
uv sync --locked
```

Создайте файл `.env` в корне проекта и укажите токен бота:

```dotenv
BOT_TOKEN=your_telegram_bot_token
FACEIT_API_KEY=your_faceit_api_key
```

`FACEIT_API_KEY` нужен для команд FACEIT. При необходимости можно задать `FACEIT_GAME` (по умолчанию `cs2`) и `FACEIT_ACCOUNTS_PATH` (по умолчанию `data/faceit_accounts.json`).

Запустите бота:

```sh
uv run --locked python src/app.py
```

Зависимости меняются командой `uv add <пакет>` или `uv remove <пакет>`; `uv` обновит `pyproject.toml` и `uv.lock`. После этого обновите также прямые зависимости в `requirements.txt`, который использует хостинг.

## Деплой на bot-hosting.net

После коммита отправьте изменения в GitHub. В [панели bot-hosting.net](https://bot-hosting.net/) создайте проект и новое развертывание типа **Application** на тарифе **Free**. Источник — **GitHub**, репозиторий `https://github.com/shynkaaaa/tg-botik.git`, ветка `main`; среда выполнения — **Python 3.12**. После создания проверьте во вкладке **Startup**:

| Настройка | Значение |
| --- | --- |
| Entry File (`STARTUP_FILE`) | `src/app.py` |
| Start Command | Оставьте команду Python по умолчанию: она установит `requirements.txt` и запустит входной файл |

Команда запуска бота после установки зависимостей — `python -u src/app.py`. Если нужно задать Start Command вручную, используйте `pip install -r requirements.txt && exec python -u src/app.py`: команда установки должна оставаться частью запуска. Файлы `requirements.txt` и `src/` должны лежать в корне развертывания. Бот работает через long polling; домен, порт и webhook не требуются.

Во вкладке **Environment** задайте переменные (токен и ключ отметьте как секретные):

| Переменная | Значение |
| --- | --- |
| `BOT_TOKEN` | Токен Telegram-бота от BotFather; обязателен |
| `FACEIT_API_KEY` | Ключ FACEIT API, если нужны команды FACEIT |
| `FACEIT_GAME` | Необязательно; по умолчанию `cs2` |
| `FACEIT_ACCOUNTS_PATH` | Необязательно; по умолчанию `data/faceit_accounts.json` в корне проекта |

Для команд со списком аккаунтов FACEIT загрузите `faceit_accounts.json` через вкладку **Files** в папку `data/` корня развертывания. Эта папка исключена из Git. При [повторной синхронизации с GitHub](https://bot-hosting.net/docs/guides/clone-a-github-repository) выберите **Merge**, чтобы сохранить загруженный файл. Не загружайте `.env` с реальными ключами; пример переменных — `.env.example`.

Содержимое `data/faceit_accounts.json`:

```json
{
  "accounts": {
    "123456789": "PlayerOne",
    "987654321": {
      "nickname": "PlayerTwo",
      "profile_url": "https://www.faceit.com/en/players/PlayerTwo"
    }
  }
}
```

Замените числовые ключи на Telegram ID пользователей, а `PlayerOne` и `PlayerTwo` — на их ники FACEIT. `/faceit_me` ищет запись по Telegram ID отправителя; `/faceit_top` использует все записи. Можно указать только ник: ссылку на профиль бот составит сам. JSON должен быть без комментариев и лишних запятых. `FACEIT_API_KEY` храните отдельно во вкладке **Environment**, не в этом файле.

Перед запуском остановите прежний экземпляр бота с тем же токеном. Затем запустите развертывание и проверьте вывод во вкладке **Console**. На [тарифе Free](https://bot-hosting.net/ru/pricing) доступны 256 МБ RAM, 25% CPU, 512 МБ хранилища и одно развертывание. Режима сна нет, но бесплатный тариф необходимо [продлевать вручную каждые четыре дня](https://bot-hosting.net/docs/faqs-and-information/billing-and-payments); следите также за потреблением памяти в панели.
