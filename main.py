from typing import Union
from fastapi import FastAPI, Form
from api.router import events, teams, news
from deta import Deta

app = FastAPI(title="ISAC (website API), BTU Cottbus-Senftenberg", openapi_url="/openapi.json")

app.include_router(events.router)
app.include_router(teams.router)
app.include_router(news.router)


@app.get("/")
def root():
    return {"mesage": "You are at homepage"}
