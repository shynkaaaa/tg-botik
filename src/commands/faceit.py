import asyncio
import html
from typing import Any, Dict, List, Optional, Tuple

from aiogram.filters import Command
from aiogram.types import Message
from aiogram.dispatcher.router import Router

from config.config import Config
from utils.faceit_api import (
    FaceitApiError,
    extract_account_entry,
    fetch_game_stats_from_api,
    load_accounts,
)

router = Router()


def _load_accounts_safe() -> Dict[str, Any]:
    return load_accounts(Config.FACEIT_ACCOUNTS_PATH)


def _entries_from_accounts(accounts: Dict[str, Any]) -> List[Tuple[Optional[str], str]]:
    seen_urls = set()
    result: List[Tuple[Optional[str], str]] = []
    for value in accounts.values():
        entry = extract_account_entry(value)
        if not entry:
            continue
        nickname, profile_url = entry
        if profile_url in seen_urls:
            continue
        seen_urls.add(profile_url)
        result.append((nickname, profile_url))
    return result


async def _fetch_game_stats(nickname: str) -> Optional[Tuple[int, int]]:
    return await asyncio.to_thread(
        fetch_game_stats_from_api,
        nickname,
        Config.FACEIT_GAME,
        Config.FACEIT_API_KEY,
    )


@router.message(Command("faceit_top"))
async def cmd_faceit_top(message: Message) -> None:
    try:
        accounts = _load_accounts_safe()
    except FileNotFoundError:
        await message.answer("Не найден файл с аккаунтами Faceit. Создай data/faceit_accounts.json.")
        return
    except ValueError:
        await message.answer("Неверный формат data/faceit_accounts.json (нужен объект 'accounts').")
        return

    entries = _entries_from_accounts(accounts)
    if not entries:
        await message.answer("В базе нет ни одного Faceit-аккаунта.")
        return

    if not Config.FACEIT_API_KEY:
        await message.answer("Не задан FACEIT_API_KEY. Добавь ключ в .env.")
        return

    results: List[Tuple[str, str, int, int]] = []
    skipped: List[str] = []

    for nickname, profile_url in entries:
        if not nickname:
            skipped.append(profile_url)
            continue

        try:
            stats = await _fetch_game_stats(nickname)
        except FaceitApiError as exc:
            if exc.status_code == 404:
                skipped.append(nickname or profile_url)
                continue
            if exc.status_code in (401, 403):
                await message.answer("Нет доступа к Faceit API. Проверь FACEIT_API_KEY.")
                return
            if exc.status_code == 429:
                await message.answer("Лимит запросов Faceit API. Попробуй позже.")
                return
            await message.answer("Faceit API временно недоступен. Попробуй позже.")
            return
        except Exception:
            await message.answer("Ошибка при запросе Faceit API.")
            return

        if not stats:
            skipped.append(nickname or profile_url)
            continue

        elo, level = stats
        display_name = nickname or profile_url
        results.append((display_name, profile_url, elo, level))

    if not results:
        await message.answer("Нет данных по Elo для текущей игры.")
        return

    results.sort(key=lambda item: item[2], reverse=True)

    lines = [f"Топ Faceit по Elo ({Config.FACEIT_GAME}):"]
    for idx, (display_name, profile_url, elo, level) in enumerate(results, start=1):
        safe_name = html.escape(display_name)
        lines.append(
            f"{idx}. <a href=\"{profile_url}\">{safe_name}</a> — {elo} Elo (lvl {level})"
        )

    if skipped:
        lines.append("")
        lines.append("Пропущены (нет данных/не найдено): " + ", ".join(skipped))

    await message.answer("\n".join(lines))


@router.message(Command("faceit_me"))
async def cmd_faceit_me(message: Message) -> None:
    try:
        accounts = _load_accounts_safe()
    except FileNotFoundError:
        await message.answer("Не найден файл с аккаунтами Faceit. Создай data/faceit_accounts.json.")
        return
    except ValueError:
        await message.answer("Неверный формат data/faceit_accounts.json (нужен объект 'accounts').")
        return

    user_id = str(message.from_user.id)
    entry = extract_account_entry(accounts.get(user_id)) if accounts.get(user_id) else None

    if not entry:
        await message.answer("Твой Faceit-аккаунт не указан в базе.")
        return

    if not Config.FACEIT_API_KEY:
        await message.answer("Не задан FACEIT_API_KEY. Добавь ключ в .env.")
        return

    nickname, profile_url = entry

    if not nickname:
        await message.answer("Не удалось определить Faceit-ник.")
        return

    try:
        stats = await _fetch_game_stats(nickname)
    except FaceitApiError as exc:
        if exc.status_code == 404:
            await message.answer("Faceit-аккаунт не найден.")
            return
        if exc.status_code in (401, 403):
            await message.answer("Нет доступа к Faceit API. Проверь FACEIT_API_KEY.")
            return
        if exc.status_code == 429:
            await message.answer("Лимит запросов Faceit API. Попробуй позже.")
            return
        await message.answer("Faceit API временно недоступен. Попробуй позже.")
        return
    except Exception:
        await message.answer("Ошибка при запросе Faceit API.")
        return

    display_name = nickname or profile_url
    safe_name = html.escape(display_name)

    if not stats:
        await message.answer(
            f"<a href=\"{profile_url}\">{safe_name}</a>: не получилось извлечь Elo."
        )
        return

    elo, level = stats
    await message.answer(
        f"<a href=\"{profile_url}\">{safe_name}</a>: {elo} elo (lvl {level})"
    )


def register_faceit_handlers(dp) -> None:
    dp.include_router(router)
