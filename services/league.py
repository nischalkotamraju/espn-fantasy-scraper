import os
import json
import requests
from dotenv import load_dotenv

load_dotenv()

BASE = "https://lm-api-reads.fantasy.espn.com/apis/v3/games/fba"

def _session():
    s = requests.Session()
    s.cookies.set("espn_s2", os.getenv("ESPN_S2", ""))
    s.cookies.set("SWID", os.getenv("ESPN_SWID", ""))
    s.headers.update({"User-Agent": "Mozilla/5.0"})
    h = os.getenv("PROXY_HOST")
    p = os.getenv("PROXY_PORT")
    u = os.getenv("PROXY_USER")
    w = os.getenv("PROXY_PASS")
    if h and p and u and w:
        proxy_url = f"http://{u}:{w}@{h}:{p}"
        s.proxies = {"http": proxy_url, "https": proxy_url}
    return s

def _url():
    return f"{BASE}/seasons/{os.getenv('SEASON_YEAR','2024')}/segments/0/leagues/{os.getenv('LEAGUE_ID')}"

def _fetch(views):
    r = _session().get(_url(), params={"view": views}, timeout=15)
    r.raise_for_status()
    return r.json()

def _team_name(t):
    return t.get("name", "Unknown")

def _owner(t):
    owners = t.get("owners", [])
    if owners and isinstance(owners[0], dict):
        o = owners[0]
        return f"{o.get('firstName','')} {o.get('lastName','')}".strip()
    return ""

def get_league():
    return _fetch(["mTeam","mRoster","mMatchup","mMatchupScore","mStandings"])

def get_standings():
    data = _fetch(["mTeam","mMatchup","mMatchupScore","mStandings"])
    current = data.get("status", {}).get("currentMatchupPeriod", 1)
    week_scores = {}
    for m in data.get("schedule", []):
        if m.get("matchupPeriodId") != current:
            continue
        h = m.get("home", {})
        a = m.get("away", {})
        if h: week_scores[h.get("teamId")] = round(h.get("totalPoints", 0), 1)
        if a: week_scores[a.get("teamId")] = round(a.get("totalPoints", 0), 1)
    teams = sorted(data.get("teams", []), key=lambda t: week_scores.get(t["id"], 0), reverse=True)
    return [{"rank": i+1, "team_name": _team_name(t), "owner": _owner(t),
             "wins": t.get("record",{}).get("overall",{}).get("wins",0),
             "losses": t.get("record",{}).get("overall",{}).get("losses",0),
             "week_points": week_scores.get(t["id"], 0)} for i, t in enumerate(teams)]

def get_current_matchups():
    data = _fetch(["mTeam","mMatchup","mMatchupScore"])
    current = data.get("status", {}).get("currentMatchupPeriod", 1)
    teams_by_id = {t["id"]: t for t in data.get("teams", [])}
    matchups = []
    seen = set()
    for m in data.get("schedule", []):
        if m.get("matchupPeriodId") != current:
            continue
        h_id = m.get("home", {}).get("teamId")
        a_id = m.get("away", {}).get("teamId")
        if not h_id or not a_id:
            continue
        pair = tuple(sorted([h_id, a_id]))
        if pair in seen:
            continue
        seen.add(pair)
        matchups.append({
            "home_team": _team_name(teams_by_id.get(h_id, {})),
            "home_score": round(m.get("home", {}).get("totalPoints", 0), 1),
            "away_team": _team_name(teams_by_id.get(a_id, {})),
            "away_score": round(m.get("away", {}).get("totalPoints", 0), 1),
        })
    return matchups

def get_injury_report():
    data = _fetch(["mTeam","mRoster"])
    report = []
    for team in data.get("teams", []):
        injured = []
        for entry in team.get("roster", {}).get("entries", []):
            pool = entry.get("playerPoolEntry", {})
            player = pool.get("player", {})
            status = player.get("injuryStatus", "ACTIVE")
            if status and status.upper() not in ("ACTIVE","NORMAL","NA","NONE",""):
                injured.append({"name": player.get("fullName","?"), "status": status})
        if injured:
            report.append({"team_name": _team_name(team), "owner": _owner(team), "injured_players": injured})
    return report

def get_free_agent_suggestions(position=None, top_n=15):
    data = _fetch(["mFreeAgent"])
    suggestions = []
    for entry in data.get("players", []):
        player = entry.get("player", {})
        if not player:
            continue
        name = player.get("fullName", "")
        if not name:
            continue
        status = player.get("injuryStatus", "ACTIVE").upper()
        if status in ("OUT","INJURED_RESERVE"):
            continue
        pos_id = player.get("defaultPositionId", 0)
        pos_map = {1:"PG",2:"SG",3:"SF",4:"PF",5:"C"}
        pos = pos_map.get(pos_id, "?")
        if position and position.upper() not in pos:
            continue
        ratings = entry.get("ratings", {})
        avg_pts = round(float(ratings.get("0", {}).get("averageRating", 0) or 0), 1)
        suggestions.append({"name": name, "position": pos, "avg_points": avg_pts, "injury_status": status})
        if len(suggestions) >= top_n:
            break
    suggestions.sort(key=lambda p: p["avg_points"], reverse=True)
    return suggestions

def _get_owner(team):
    return _owner(team)
