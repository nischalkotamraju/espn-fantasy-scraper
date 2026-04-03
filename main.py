"""
ESPN Fantasy Basketball - FastAPI REST layer.
"""
from fastapi import FastAPI, HTTPException, Query
from services.league import (
    get_standings,
    get_injury_report,
    get_free_agent_suggestions,
    get_current_matchups,
)

app = FastAPI(title="ESPN Fantasy Basketball API", version="1.0.0")

@app.get("/")
def root():
    return {"message": "ESPN Fantasy Basketball API is running. Visit /docs for all endpoints."}

@app.get("/standings")
def standings():
    try:
        return {"standings": get_standings()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/injuries")
def injuries():
    try:
        return {"injury_report": get_injury_report()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/free-agents")
def free_agents(position: str = Query(None), top_n: int = Query(15, ge=1, le=50)):
    try:
        return {"free_agents": get_free_agent_suggestions(position=position, top_n=top_n)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/matchups")
def matchups():
    try:
        return {"matchups": get_current_matchups()}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/advice")
def daily_advice(team: str = Query(None)):
    try:
        from services.advice import get_daily_advice
        return get_daily_advice(team_name=team)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))