from typing import Optional
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from datetime import datetime, timezone
from api.utils import text_db

router = APIRouter(
    prefix="/news",
    tags=["news"]
)

class News(BaseModel):
    description: str
    url: str

@router.get("/")
async def home():
    news_db = text_db.Base("news-db")
    data = news_db.fetch()
    return {"data": data.items}

@router.post("/create")
async def create_news(news: News, expire_in_hr: int=24):
    news_db = text_db.Base("news-db")
    encoded = jsonable_encoder(news)
    encoded.update(jsonable_encoder({"modified_time": datetime.now(timezone.utc).isoformat()}))
    res = news_db.insert(encoded, expire_in=expire_in_hr*3600)
    return res