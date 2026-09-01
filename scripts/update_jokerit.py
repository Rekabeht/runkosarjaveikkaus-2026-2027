import json
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

BASE_URL = "https://liiga.fi/api/v2"
JOKERIT_TEAM_ID = "238306801:jokerit"
HELSINKI = ZoneInfo("Europe/Helsinki")


def fetch_json(url):
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json",
        },
    )
    with urllib.request.urlopen(req, timeout=30) as response:
        return json.load(response)


def finish_label(finished_type):
    if finished_type == "ENDED_DURING_EXTENDED_GAME_TIME":
        return "JA"
    if finished_type == "ENDED_DURING_WINNING_SHOT_COMPETITION":
        return "VL"
    return ""


def parse_local_start(value):
    if not value:
        return None

    try:
        return datetime.fromisoformat(
            value.replace("Z", "+00:00")
        ).astimezone(HELSINKI)
    except (ValueError, TypeError):
        return None


def jokerit_players_from_detail(detail, item):
    if item["homeTeamId"] == JOKERIT_TEAM_ID:
        players = detail.get("homeTeamPlayers") or []
    elif item["awayTeamId"] == JOKERIT_TEAM_ID:
        players = detail.get("awayTeamPlayers") or []
    else:
        players = []

    jokerit_players = []

    for player in players:
        if player.get("teamId") != JOKERIT_TEAM_ID:
            continue

        jokerit_players.append({
            "id": player.get("id"),
            "firstName": player.get("firstName"),
            "lastName": player.get("lastName"),
            "jersey": player.get("jersey"),
            "line": player.get("line"),
            "role": player.get("role"),
            "roleCode": player.get("roleCode"),
            "captain": player.get("captain", False),
            "alternateCaptain": player.get(
                "alternateCaptain", False
            ),
        })

    jokerit_players.sort(
        key=lambda p: (
            p.get("line")
            if p.get("line") is not None
            else 99,
            p.get("role") or "",
            p.get("jersey")
            if p.get("jersey") is not None
            else 999,
        )
    )

    return jokerit_players


now_utc = datetime.now(timezone.utc)
now_helsinki = now_utc.astimezone(HELSINKI)

weeks_data = fetch_json(
    f"{BASE_URL}/gameweeks?season=2027&tournament=runkosarja"
)

nb_weeks = weeks_data["nbWeeks"]

jokerit_games = []


for week in range(1, nb_weeks + 1):
    games = fetch_json(
        f"{BASE_URL}/games?tournament=runkosarja&week={week}"
    )

    for game in games:
        home = game.get("homeTeam") or {}
        away = game.get("awayTeam") or {}

        if (
            home.get("teamId") != JOKERIT_TEAM_ID
            and away.get("teamId") != JOKERIT_TEAM_ID
        ):
            continue

        game_id = game.get("id")

        local_time = (
            home.get("gameStartDateTime")
            or away.get("gameStartDateTime")
            or game.get("start")
        )

        item = {
            "id": game_id,
            "week": game.get("gameWeek", week),
            "start": game.get("start"),
            "localStart": local_time,

            "homeTeam": home.get("teamName"),
            "awayTeam": away.get("teamName"),

            "homeTeamId": home.get("teamId"),
            "awayTeamId": away.get("teamId"),

            "homeGoals": home.get("goals"),
            "awayGoals": away.get("goals"),

            "started": game.get("started", False),
            "ended": game.get("ended", False),

            "finishedType": game.get("finishedType"),
            "finishLabel": "",

            "rink": (game.get("iceRink") or {}).get("name"),
            "city": (game.get("iceRink") or {}).get("city"),

            "lineupPublished": False,
            "lineup": [],
        }

        item["finishLabel"] = finish_label(
            item["finishedType"]
        )

        game_local = parse_local_start(local_time)

        # Tarkempi otteludata haetaan:
        # - aina päättyneistä peleistä
        # - Jokerien pelipäivänä klo 13 jälkeen
        should_fetch_detail = item["ended"]

        if game_local:
            is_game_day = (
                game_local.date()
                == now_helsinki.date()
            )

            after_lineup_time = (
                now_helsinki.hour >= 13
            )

            if is_game_day and after_lineup_time:
                should_fetch_detail = True

        if should_fetch_detail and game_id:
            try:
                detail = fetch_json(
                    f"{BASE_URL}/games/2027/{game_id}"
                )

                detailed_game = detail.get("game") or {}

                if item["ended"]:
                    detailed_home = (
                        detailed_game.get("homeTeam") or {}
                    )
                    detailed_away = (
                        detailed_game.get("awayTeam") or {}
                    )

                    item["homeGoals"] = detailed_home.get(
                        "goals",
                        item["homeGoals"],
                    )

                    item["awayGoals"] = detailed_away.get(
                        "goals",
                        item["awayGoals"],
                    )

                    item["finishedType"] = (
                        detailed_game.get(
                            "finishedType",
                            item["finishedType"],
                        )
                    )

                    item["finishLabel"] = finish_label(
                        item["finishedType"]
                    )

                players = jokerit_players_from_detail(
                    detail,
                    item,
                )

                if players:
                    item["lineup"] = players
                    item["lineupPublished"] = True

            except Exception as exc:
                print(
                    f"Varoitus: ottelun {game_id} "
                    f"tarkemman datan haku epäonnistui: {exc}"
                )

        jokerit_games.append(item)


jokerit_games.sort(
    key=lambda x: x.get("start") or ""
)


output = {
    "season": "2026-2027",
    "team": "Jokerit",
    "teamId": JOKERIT_TEAM_ID,
    "updated": now_utc.isoformat(),
    "games": jokerit_games,
}


with open(
    "data/jokerit.json",
    "w",
    encoding="utf-8",
) as f:
    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2,
    )


print(
    f"Tallennettiin {len(jokerit_games)} Jokerien ottelua."
)
