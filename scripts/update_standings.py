import json
from datetime import datetime, timezone
from pathlib import Path
from urllib.request import Request, urlopen

API_URL = "https://liiga.fi/api/v2/teams/stats?seasonFrom=2027&seasonTo=2027&tournament=runkosarja&dataType=standings"
OUT = Path(__file__).resolve().parents[1] / "data" / "standings.json"

EXPECTED_TEAMS = {
    "HIFK", "HPK", "Ilves", "Jokerit", "Jukurit", "JYP", "KalPa",
    "K-Espoo", "KooKoo", "Kärpät", "Lukko", "Pelicans", "SaiPa",
    "Sport", "Tappara", "TPS", "Ässät"
}

def as_int(value, default=0):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default

req = Request(API_URL, headers={"User-Agent": "Mozilla/5.0", "Accept": "application/json"})
with urlopen(req, timeout=30) as response:
    raw = json.load(response)

team_stats = raw.get("teamStats")
if not isinstance(team_stats, list):
    raise RuntimeError("Liiga API: teamStats puuttuu tai ei ole lista.")
if len(team_stats) != 17:
    raise RuntimeError(f"Liiga API: odotettiin 17 joukkuetta, saatiin {len(team_stats)}.")

names = {str(x.get("teamName", "")).strip() for x in team_stats}
if names != EXPECTED_TEAMS:
    missing = sorted(EXPECTED_TEAMS - names)
    extra = sorted(names - EXPECTED_TEAMS)
    raise RuntimeError(f"Joukkuelista ei täsmää. Puuttuu={missing}, ylimääräiset={extra}")

standings = []
for x in team_stats:
    standings.append({
        "rank": as_int(x.get("ranking")),
        "team": str(x.get("teamName", "")).strip(),
        "teamId": x.get("teamId"),
        "games": as_int(x.get("games")),
        "wins": as_int(x.get("wins")),
        "ties": as_int(x.get("ties")),
        "losses": as_int(x.get("losses")),
        "points": as_int(x.get("points")),
        "goalsFor": as_int(x.get("goalsFor")),
        "goalsAgainst": as_int(x.get("goalsAgainst")),
        "goalDifference": as_int(x.get("goalDifference")),
    })
standings.sort(key=lambda x: x["rank"])

payload = {
    "updated": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
    "season": "2026-2027",
    "tournament": "runkosarja",
    "source": API_URL,
    "playoffsLines": raw.get("playoffsLines", [4, 12, 14]),
    "standings": standings,
}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(f"Päivitetty {OUT}: {len(standings)} joukkuetta.")
