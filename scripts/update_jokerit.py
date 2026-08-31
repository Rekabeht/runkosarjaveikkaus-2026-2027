import json
import urllib.request
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

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

# 1. Selvitetään montako peliviikkoa runkosarjassa on.
weeks_data = fetch_json(
    f"{BASE_URL}/gameweeks?season=2027&tournament=runkosarja"
)

nb_weeks = weeks_data["nbWeeks"]

jokerit_games = []

# 2. Haetaan kaikki viikot.
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

        local_time = (
            home.get("gameStartDateTime")
            or away.get("gameStartDateTime")
            or game.get("start")
        )

        jokerit_games.append(
            {
                "id": game.get("id"),
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
                "rink": (game.get("iceRink") or {}).get("name"),
                "city": (game.get("iceRink") or {}).get("city"),
            }
        )

# 3. Järjestetään ottelut aikajärjestykseen.
jokerit_games.sort(key=lambda x: x.get("start") or "")

output = {
    "season": "2026-2027",
    "team": "Jokerit",
    "teamId": JOKERIT_TEAM_ID,
    "updated": datetime.now(timezone.utc).isoformat(),
    "games": jokerit_games,
}

with open("data/jokerit.json", "w", encoding="utf-8") as f:
    json.dump(output, f, ensure_ascii=False, indent=2)

print(f"Tallennettiin {len(jokerit_games)} Jokerien ottelua.")
