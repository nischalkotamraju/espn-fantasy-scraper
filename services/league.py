"""
Core ESPN Fantasy Basketball service.
All ESPN API interactions live here — shared by the CLI and REST API.
"""

import os
from dotenv import load_dotenv
from espn_api.basketball import League

load_dotenv()


def _get_owner(team) -> str:
    if hasattr(team, "owners") and team.owners:
        o = team.owners[0]
        if isinstance(o, dict):
            return f"{o.get('firstName', '')} {o.get('lastName', '')}".strip()
        return str(o)
    if hasattr(team, "owner"):
        return str(team.owner)
    return "Unknown"


def get_league() -> League:
    league_id = int(os.getenv("LEAGUE_ID", 0))
    year = int(os.getenv("SEASON_YEAR", 2025))
    espn_s2 = os.getenv("ESPN_S2")
    swid = os.getenv("ESPN_SWID")
    if not all([league_id, espn_s2, swid]):
        raise ValueError("Missing credentials.")
    return League(league_id=league_id, year=year, espn_s2=espn_s2, swid=swid)


def get_standings() -> list[dict]:
    league = get_league()
    box_scores = league.box_scores()
    week_scores = {}
    for matchup in box_scores:
        if matchup.home_team:
            week_scores[matchup.home_team.team_id] = round(matchup.home_score, 1)
        if matchup.away_team:
            week_scores[matchup.away_team.team_id] = round(matchup.away_score, 1)
    teams = sorted(league.teams, key=lambda t: week_scores.get(t.team_id, 0), reverse=True)
    standings = []
    for rank, team in enumerate(teams, start=1):
        standings.append({
            "rank": rank,
            "team_name": team.team_name,
            "owner": _get_owner(team),
            "wins": team.wins,
            "losses": team.losses,
            "week_points": week_scores.get(team.team_id, 0),
        })
    return standings


def get_injury_report() -> list[dict]:
    league = get_league()
    report = []
    for team in league.teams:
        injured_players = []
        for player in team.roster:
            status = getattr(player, "injuryStatus", None) or getattr(player, "injury_status", "ACTIVE")
            if status and status.upper() not in ("ACTIVE", "NORMAL", "NA", "NONE", ""):
                injured_players.append({
                    "name": player.name,
                    "position": player.position,
                    "status": status,
                    "pro_team": getattr(player, "proTeam", "N/A"),
                })
        if injured_players:
            report.append({
                "team_name": team.team_name,
                "owner": _get_owner(team),
                "injured_players": injured_players,
            })
    return report


def get_free_agent_suggestions(position: str = None, top_n: int = 15) -> list[dict]:
    league = get_league()
    size = top_n * 3 if position else top_n * 2
    try:
        fa_list = league.free_agents(size=size)
    except Exception as e:
        raise RuntimeError(f"Could not fetch free agents: {e}")
    suggestions = []
    for player in fa_list:
        player_pos = getattr(player, "position", "")
        if position and position.upper() not in player_pos.upper():
            continue
        status = (getattr(player, "injuryStatus", None) or "ACTIVE").upper()
        if status in ("OUT", "INJURED_RESERVE"):
            continue
        avg_points = getattr(player, "avg_points", 0) or 0
        total_points = getattr(player, "total_points", 0) or 0
        suggestions.append({
            "name": player.name,
            "position": player_pos,
            "pro_team": getattr(player, "proTeam", "N/A"),
            "avg_points": round(avg_points, 1),
            "total_points": round(total_points, 1),
            "injury_status": status,
        })
        if len(suggestions) >= top_n:
            break
    suggestions.sort(key=lambda p: p["avg_points"], reverse=True)
    return suggestions


def get_current_matchups() -> list[dict]:
    league = get_league()
    box_scores = league.box_scores()
    matchups = []
    seen_pairs = set()
    for matchup in box_scores:
        try:
            home = matchup.home_team
            away = matchup.away_team
            if not home or not away:
                continue
            pair = tuple(sorted([home.team_name, away.team_name]))
            if pair in seen_pairs:
                continue
            seen_pairs.add(pair)
            matchups.append({
                "home_team": home.team_name,
                "home_score": round(matchup.home_score or 0, 1),
                "away_team": away.team_name,
                "away_score": round(matchup.away_score or 0, 1),
            })
        except Exception:
            continue
    return matchups