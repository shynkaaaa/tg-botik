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
    extract_game_stats_from_player_data,
    fetch_player_data,
    fetch_player_game_stats,
    fetch_game_stats_from_api,
    build_recent_stats,
    load_accounts,
)

router = Router()

RECENT_LIMITS = (10, 30)


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


def _format_ratio(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"{value:.2f}"


def _format_percent(value: Optional[float]) -> str:
    if value is None:
        return "—"
    return f"{value:.1f}%"


def _format_int(value: Optional[int]) -> str:
    if value is None:
        return "—"
    return str(value)


def _build_recent_page(
    header: str,
    limit: int,
    stats: Dict[str, Any],
) -> str:
    lines = [header, f"Последние {limit} матчей:"]
    matches = stats.get("matches", 0)
    skipped = stats.get("skipped", 0)
    if matches == 0:
        lines.append("Нет данных по матчам за этот период.")
        return "\n".join(lines)

    result_matches = stats.get("result_matches", 0)
    wins = stats.get("wins", 0)
    winrate = None
    if result_matches > 0:
        winrate = (wins / result_matches) * 100

    kills = stats.get("kills") if stats.get("has_kills") else None
    deaths = stats.get("deaths") if stats.get("has_deaths") else None
    assists = stats.get("assists") if stats.get("has_assists") else None
    headshots = stats.get("headshots") if stats.get("has_headshots") else None
    rounds = stats.get("rounds") if stats.get("has_rounds") else None

    kd = None
    if kills is not None and deaths is not None and deaths > 0:
        kd = kills / deaths
    elif kills is not None and deaths == 0:
        kd = float(kills)

    kr = None
    if kills is not None and rounds is not None and rounds > 0:
        kr = kills / rounds

    hs_percent = None
    if headshots is not None and kills is not None and kills > 0:
        hs_percent = (headshots / kills) * 100

    lines.append(f"Матчи: {matches} (пропущено: {skipped})")
    if result_matches > 0:
        lines.append(f"Победы: {wins}/{result_matches} ({_format_percent(winrate)})")
    else:
        lines.append(f"Победы: {wins}")

    lines.append(
        " | ".join(
            [
                f"K/D: {_format_ratio(kd)}",
                f"K/R: {_format_ratio(kr)}",
                f"HS%: {_format_percent(hs_percent)}",
            ]
        )
    )

    summary_parts = []
    if kills is not None:
        summary_parts.append(f"K {kills}")
    if deaths is not None:
        summary_parts.append(f"D {deaths}")
    if assists is not None:
        summary_parts.append(f"A {assists}")
    if headshots is not None:
        summary_parts.append(f"HS {headshots}")
    if summary_parts:
        lines.append("Суммарно: " + " / ".join(summary_parts))

    avg_parts = []
    if matches > 0:
        if kills is not None:
            avg_parts.append(f"K {kills / matches:.1f}")
        if deaths is not None:
            avg_parts.append(f"D {deaths / matches:.1f}")
        if assists is not None:
            avg_parts.append(f"A {assists / matches:.1f}")
    if avg_parts:
        lines.append("В среднем: " + " / ".join(avg_parts))

    if rounds is not None:
        lines.append(f"Раунды: {_format_int(rounds)}")

    return "\n".join(lines)


def _build_lifetime_page(
    header: str,
    lifetime: Optional[Dict[str, Any]],
) -> str:
    lines = [header, "Lifetime:"]
    if not lifetime:
        lines.append("Нет данных по lifetime.")
        return "\n".join(lines)

    fields = [
        ("Matches", "Матчи"),
        ("Wins", "Победы"),
        ("Win Rate %", "Winrate"),
        ("K/D Ratio", "K/D"),
        ("K/R Ratio", "K/R"),
        ("Average K/D Ratio", "Avg K/D"),
        ("Average K/R Ratio", "Avg K/R"),
        ("Average Headshots %", "HS%"),
        ("Average Kills", "Avg Kills"),
        ("Average Deaths", "Avg Deaths"),
        ("Average Assists", "Avg Assists"),
        ("Average MVPs", "Avg MVPs"),
        ("Longest Win Streak", "Макс винстрик"),
        ("Current Win Streak", "Текущая серия"),
    ]

    added = False
    for key, label in fields:
        value = lifetime.get(key)
        if value is None:
            continue
        lines.append(f"{label}: {value}")
        added = True

    recent = lifetime.get("Recent Results")
    if isinstance(recent, list) and recent:
        mapped = ["W" if item == "1" else "L" for item in recent[:10]]
        lines.append("Последние результаты: " + " ".join(mapped))
        added = True

    if not added:
        lines.append("Нет деталей по lifetime.")

    return "\n".join(lines)


def _build_faceit_pages(nickname: str, profile_url: str) -> List[str]:
    player_data = fetch_player_data(nickname, Config.FACEIT_API_KEY)
    player_id = player_data.get("player_id")
    if not player_id:
        raise ValueError("Faceit player_id not found")

    display_name = nickname or profile_url
    safe_name = html.escape(display_name)
    header = f"<a href=\"{profile_url}\">{safe_name}</a> — {Config.FACEIT_GAME}"

    game_stats = extract_game_stats_from_player_data(player_data, Config.FACEIT_GAME)
    if game_stats:
        elo, level = game_stats
        header = f"{header} | {elo} elo (lvl {level})"

    pages: List[str] = []
    for limit in RECENT_LIMITS:
        recent = build_recent_stats(
            player_id,
            Config.FACEIT_GAME,
            Config.FACEIT_API_KEY,
            limit,
        )
        pages.append(_build_recent_page(header, limit, recent))

    lifetime_data = fetch_player_game_stats(
        player_id,
        Config.FACEIT_GAME,
        Config.FACEIT_API_KEY,
    )
    lifetime = lifetime_data.get("lifetime") if isinstance(lifetime_data, dict) else None
    pages.append(_build_lifetime_page(header, lifetime))

    return pages


async def _safe_delete(message: Message) -> None:
    try:
        await message.delete()
    except Exception:
        return


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

    wait_message = await message.answer(
        "Собираю статистику Faceit. Это может занять несколько минут..."
    )

    try:
        pages = await asyncio.to_thread(_build_faceit_pages, nickname, profile_url)
    except FaceitApiError as exc:
        await _safe_delete(wait_message)
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
    except ValueError:
        await _safe_delete(wait_message)
        await message.answer("Не удалось получить данные Faceit.")
        return
    except Exception:
        await _safe_delete(wait_message)
        await message.answer("Ошибка при запросе Faceit API.")
        return

    await _safe_delete(wait_message)
    for page in pages:
        await message.answer(page)


def register_faceit_handlers(dp) -> None:
    dp.include_router(router)
