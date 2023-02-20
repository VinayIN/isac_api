from typing import Union
from fastapi import FastAPI
from api.router import events, social_media, teams, news

app = FastAPI()

app.include_router(events.router)
app.include_router(social_media.router)
app.include_router(teams.router)
app.include_router(news.router)

@app.get("/")
async def root():
    return {"mesage": "You are at homepage"}