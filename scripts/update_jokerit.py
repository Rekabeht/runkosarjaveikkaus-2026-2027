import json
import urllib.request
from datetime import datetime, timezone

BASE_URL = "https://liiga.fi/api/v2"
JOKERIT_TEAM_ID = "238306801:jokerit"

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


# 1. Selvitetään runkosarjan peliviikkojen määrä.
weeks_data = fetch_json(
    f"{BASE_URL}/gameweeks?season=2027&tournament=runkosarja"
)

nb_weeks = weeks_data["nbWeeks"]

jokerit_games = []


# 2. Haetaan kaikki runkosarjaviikot.
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
        }

        # 3. Päättyneestä ottelusta haetaan tarkempi otteludata.
        if item["ended"] and game_id:
            try:
                detail = fetch_json(
                    f"{BASE_URL}/game/{game_id}"
                )

                detailed_game = detail.get("game") or {}

                detailed_home = detailed_game.get("homeTeam") or {}
                detailed_away = detailed_game.get("awayTeam") or {}

                item["homeGoals"] = detailed_home.get(
                    "goals", item["homeGoals"]
                )
                item["awayGoals"] = detailed_away.get(
                    "goals", item["awayGoals"]
                )

                item["finishedType"] = detailed_game.get(
                    "finishedType",
                    item["finishedType"]
                )

                item["finishLabel"] = finish_label(
                    item["finishedType"]
                )

            except Exception as exc:
                print(
                    f"Varoitus: ottelun {game_id} tarkemman datan haku epäonnistui: {exc}"
                )

        jokerit_games.append(item)


# 4. Järjestetään ottelut aikajärjestykseen.
jokerit_games.sort(
    key=lambda x: x.get("start") or ""
)


output = {
    "season": "2026-2027",
    "team": "Jokerit",
    "teamId": JOKERIT_TEAM_ID,
    "updated": datetime.now(timezone.utc).isoformat(),
    "games": jokerit_games,
}


with open(
    "data/jokerit.json",
    "w",
    encoding="utf-8"
) as f:
    json.dump(
        output,
        f,
        ensure_ascii=False,
        indent=2
    )


print(
    f"Tallennettiin {len(jokerit_games)} Jokerien ottelua."
)
