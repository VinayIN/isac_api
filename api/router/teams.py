from typing import Union, Optional
from fastapi import APIRouter
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel
from datetime import datetime, timezone
from api.utils import text_db

router = APIRouter(
    prefix="/teams",
    tags=["teams"],
)


class TeamMember(BaseModel):
    department: str
    email: Optional[str] = None
    first_name: str
    last_name: str
    native_state: Optional[str] = None
    team: str
    year: int

@router.get("/")
async def home():
    teams_db = text_db.Base("member-info-db")
    data = teams_db.fetch()
    return {"data": data.items}

@router.get("/{year}")
async def query_year(year: int):
    teams_db = text_db.Base("member-info-db")
    data = teams_db.fetch({"year": year})
    return {"data": data.items}

@router.post("/create")
async def create_team_member(member: TeamMember):
    teams_db = text_db.Base("member-info-db")
    encoded = jsonable_encoder(member)
    encoded.update(jsonable_encoder({"modified_time": datetime.now(timezone.utc).isoformat()}))
    res = teams_db.insert(encoded)
    if res:
        news_db = text_db.Base("news-db")
        data = {
            "modified_time": f'{res.get("modified_time")}', # type: ignore  
           "description": f'{res.get("first_name")} {res.get("last_name")} added to ISAC team for the year {res.get("year")}', # type: ignore
            "url": None
        }
        # expire_in 24 hr
        news_db.insert(data, expire_in=24*3600)
    return res

@router.get("/request-data/{last_name}")
async def request_data(last_name):
    teams_db = text_db.Base("member-info-db")
    data = teams_db.fetch({"last_name": last_name})
    return {"data": data.items}

@router.put("/update/{key}")
async def update_team_member(member: TeamMember, key: str):
    teams_db = text_db.Base("member-info-db")
    encoded = jsonable_encoder(member)
    encoded.update(jsonable_encoder({"modified_time": datetime.now(timezone.utc).isoformat()}))
    res = teams_db.put(encoded, key=key)
    return res
