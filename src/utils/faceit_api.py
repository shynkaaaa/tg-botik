import json
import os
import re
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

FACEIT_PROFILE_BASE_URL = "https://www.faceit.com/en/players"
FACEIT_API_BASE_URL = "https://open.faceit.com/data/v4"


class FaceitPageError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


class FaceitApiError(RuntimeError):
    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(message)
        self.status_code = status_code


def load_accounts(file_path: str) -> Dict[str, Any]:
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Accounts file not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    accounts = data.get("accounts")
    if not isinstance(accounts, dict):
        raise ValueError("Invalid accounts format: expected 'accounts' dict")

    return accounts


def extract_nickname(value: Any) -> Optional[str]:
    if isinstance(value, str):
        if value.strip().startswith("http"):
            return extract_nickname_from_url(value)
        return value.strip() or None
    if isinstance(value, dict):
        for key in ("nickname", "faceit_nickname", "nick"):
            nick = value.get(key)
            if isinstance(nick, str) and nick.strip():
                return nick.strip()
    return None


def extract_profile_url(value: Any) -> Optional[str]:
    if isinstance(value, str) and value.strip().startswith("http"):
        return value.strip()
    if isinstance(value, dict):
        for key in ("profile_url", "url", "link", "href"):
            url = value.get(key)
            if isinstance(url, str) and url.strip().startswith("http"):
                return url.strip()
    return None


def extract_account_entry(value: Any) -> Optional[Tuple[Optional[str], str]]:
    nickname = extract_nickname(value)
    profile_url = extract_profile_url(value)

    if not profile_url and nickname:
        profile_url = build_profile_url(nickname)

    if profile_url and not nickname:
        nickname = extract_nickname_from_url(profile_url)

    if not profile_url:
        return None

    return nickname, profile_url


def extract_nickname_from_url(url: str) -> Optional[str]:
    try:
        parsed = urlparse(url)
    except ValueError:
        return None

    path = parsed.path.strip("/")
    if not path:
        return None

    parts = path.split("/")
    if "players" in parts:
        idx = parts.index("players")
        if idx + 1 < len(parts):
            return parts[idx + 1] or None

    return parts[-1] or None


def build_profile_url(nickname: str) -> str:
    return f"{FACEIT_PROFILE_BASE_URL}/{nickname}"


def fetch_profile_html(profile_url: str) -> str:
    headers = {"User-Agent": "Mozilla/5.0 (compatible; tg-botik/1.0)"}
    response = requests.get(profile_url, headers=headers, timeout=15)

    if response.status_code != 200:
        raise FaceitPageError(response.status_code, response.text)

    return response.text


def fetch_player_data(nickname: str, api_key: str) -> Dict[str, Any]:
    if not api_key:
        raise ValueError("FACEIT_API_KEY is required")
    if not nickname:
        raise ValueError("nickname is required")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    response = requests.get(
        f"{FACEIT_API_BASE_URL}/players",
        headers=headers,
        params={"nickname": nickname},
        timeout=15,
    )

    if response.status_code != 200:
        raise FaceitApiError(response.status_code, response.text)

    return response.json()


def extract_game_stats_from_player_data(
    data: Dict[str, Any],
    game_id: str,
) -> Optional[Tuple[int, int]]:
    games = data.get("games")
    if not isinstance(games, dict):
        return None

    game = games.get(game_id)
    if not isinstance(game, dict):
        return None

    elo = game.get("faceit_elo")
    level = game.get("skill_level")
    if elo is None or level is None:
        return None

    try:
        return int(elo), int(level)
    except (TypeError, ValueError):
        return None


def fetch_game_stats_from_api(
    nickname: str,
    game_id: str,
    api_key: str,
) -> Optional[Tuple[int, int]]:
    data = fetch_player_data(nickname, api_key)
    return extract_game_stats_from_player_data(data, game_id)


def fetch_player_game_stats(
    player_id: str,
    game_id: str,
    api_key: str,
) -> Dict[str, Any]:
    if not api_key:
        raise ValueError("FACEIT_API_KEY is required")
    if not player_id:
        raise ValueError("player_id is required")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    response = requests.get(
        f"{FACEIT_API_BASE_URL}/players/{player_id}/stats/{game_id}",
        headers=headers,
        timeout=15,
    )

    if response.status_code != 200:
        raise FaceitApiError(response.status_code, response.text)

    return response.json()


def fetch_player_history(
    player_id: str,
    game_id: str,
    api_key: str,
    limit: int,
) -> Dict[str, Any]:
    if not api_key:
        raise ValueError("FACEIT_API_KEY is required")
    if not player_id:
        raise ValueError("player_id is required")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    response = requests.get(
        f"{FACEIT_API_BASE_URL}/players/{player_id}/history",
        headers=headers,
        params={"game": game_id, "limit": limit},
        timeout=15,
    )

    if response.status_code != 200:
        raise FaceitApiError(response.status_code, response.text)

    return response.json()


def fetch_match_stats(match_id: str, api_key: str) -> Dict[str, Any]:
    if not api_key:
        raise ValueError("FACEIT_API_KEY is required")
    if not match_id:
        raise ValueError("match_id is required")

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "application/json",
    }
    response = requests.get(
        f"{FACEIT_API_BASE_URL}/matches/{match_id}/stats",
        headers=headers,
        timeout=15,
    )

    if response.status_code != 200:
        raise FaceitApiError(response.status_code, response.text)

    return response.json()


def build_recent_stats(
    player_id: str,
    game_id: str,
    api_key: str,
    limit: int,
) -> Dict[str, Any]:
    history = fetch_player_history(player_id, game_id, api_key, limit)
    items = history.get("items")
    if not isinstance(items, list):
        return {
            "matches": 0,
            "wins": 0,
            "result_matches": 0,
            "kills": 0,
            "deaths": 0,
            "assists": 0,
            "headshots": 0,
            "rounds": 0,
            "skipped": 0,
            "has_kills": False,
            "has_deaths": False,
            "has_assists": False,
            "has_headshots": False,
            "has_rounds": False,
        }

    aggregate = {
        "matches": 0,
        "wins": 0,
        "result_matches": 0,
        "kills": 0,
        "deaths": 0,
        "assists": 0,
        "headshots": 0,
        "rounds": 0,
        "skipped": 0,
        "has_kills": False,
        "has_deaths": False,
        "has_assists": False,
        "has_headshots": False,
        "has_rounds": False,
    }

    for item in items:
        if not isinstance(item, dict):
            aggregate["skipped"] += 1
            continue

        match_id = item.get("match_id") or item.get("matchId")
        if not match_id:
            aggregate["skipped"] += 1
            continue

        try:
            match_stats = fetch_match_stats(match_id, api_key)
        except FaceitApiError:
            aggregate["skipped"] += 1
            continue

        player_stats = _extract_player_stats(match_stats, player_id)
        if not player_stats:
            aggregate["skipped"] += 1
            continue

        aggregate["matches"] += 1

        kills = _get_stat_int(player_stats, ("Kills", "K"))
        if kills is not None:
            aggregate["kills"] += kills
            aggregate["has_kills"] = True

        deaths = _get_stat_int(player_stats, ("Deaths", "D"))
        if deaths is not None:
            aggregate["deaths"] += deaths
            aggregate["has_deaths"] = True

        assists = _get_stat_int(player_stats, ("Assists", "A"))
        if assists is not None:
            aggregate["assists"] += assists
            aggregate["has_assists"] = True

        headshots = _get_stat_int(player_stats, ("Headshots", "HS"))
        if headshots is not None:
            aggregate["headshots"] += headshots
            aggregate["has_headshots"] = True

        rounds = _get_stat_int(player_stats, ("Rounds", "Rounds Played"))
        if rounds is not None:
            aggregate["rounds"] += rounds
            aggregate["has_rounds"] = True

        result_value = _get_stat_value(player_stats, ("Result", "Match Result"))
        result = _parse_match_result(result_value)
        if result is not None:
            aggregate["result_matches"] += 1
            if result:
                aggregate["wins"] += 1

    return aggregate


def _extract_player_stats(match_stats: Dict[str, Any], player_id: str) -> Optional[Dict[str, Any]]:
    rounds = match_stats.get("rounds")
    if not isinstance(rounds, list):
        return None

    for round_item in rounds:
        if not isinstance(round_item, dict):
            continue
        teams = round_item.get("teams")
        if not isinstance(teams, list):
            continue
        for team in teams:
            if not isinstance(team, dict):
                continue
            players = team.get("players")
            if not isinstance(players, list):
                continue
            for player in players:
                if not isinstance(player, dict):
                    continue
                if player.get("player_id") != player_id:
                    continue
                stats = player.get("player_stats")
                if isinstance(stats, dict):
                    return stats
    return None


def _parse_stat_value(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(" ", "").replace(",", ".")
        if not text:
            return None
        if text.endswith("%"):
            text = text[:-1]
        try:
            return float(text)
        except ValueError:
            return None
    return None


def _get_stat_value(stats: Dict[str, Any], keys: Tuple[str, ...]) -> Any:
    for key in keys:
        if key in stats:
            return stats.get(key)
    return None


def _get_stat_int(stats: Dict[str, Any], keys: Tuple[str, ...]) -> Optional[int]:
    value = _get_stat_value(stats, keys)
    parsed = _parse_stat_value(value)
    if parsed is None:
        return None
    try:
        return int(parsed)
    except (TypeError, ValueError):
        return None


def _parse_match_result(value: Any) -> Optional[bool]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return int(value) == 1
    if isinstance(value, str):
        text = value.strip().lower()
        if text in ("1", "w", "win", "victory", "true"):
            return True
        if text in ("0", "l", "loss", "lose", "false"):
            return False
    return None


def extract_game_stats_from_html(html: str, game_id: str) -> Optional[Tuple[int, int]]:
    soup = BeautifulSoup(html, "html.parser")
    next_data = soup.find("script", id="__NEXT_DATA__")
    if next_data and next_data.string:
        try:
            data = json.loads(next_data.string)
            stats = _find_game_stats_in_data(data, game_id)
            if stats:
                return stats
        except (json.JSONDecodeError, TypeError):
            pass

    # Fallback: try to find stats in raw HTML
    pattern = re.compile(
        rf'"{re.escape(game_id)}"\s*:\s*\{{[^\}}]*?"faceit_elo"\s*:\s*(\d+)[^\}}]*?"skill_level"\s*:\s*(\d+)',
        re.DOTALL,
    )
    match = pattern.search(html)
    if match:
        try:
            return int(match.group(1)), int(match.group(2))
        except (TypeError, ValueError):
            return None

    return None


def _find_game_stats_in_data(data: Any, game_id: str) -> Optional[Tuple[int, int]]:
    if isinstance(data, dict):
        games = data.get("games")
        if isinstance(games, dict):
            game = games.get(game_id)
            if isinstance(game, dict):
                elo = game.get("faceit_elo")
                level = game.get("skill_level")
                if elo is not None and level is not None:
                    try:
                        return int(elo), int(level)
                    except (TypeError, ValueError):
                        return None

        for value in data.values():
            result = _find_game_stats_in_data(value, game_id)
            if result:
                return result

    if isinstance(data, list):
        for item in data:
            result = _find_game_stats_in_data(item, game_id)
            if result:
                return result

    return None
