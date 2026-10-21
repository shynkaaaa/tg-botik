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

Зависимости меняются командой `uv add <пакет>` или `uv remove <пакет>`; `uv` обновит `pyproject.toml` и `uv.lock`.
