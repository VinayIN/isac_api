from typing import Union, Optional
from fastapi import FastAPI, Depends, Request
from fastapi.encoders import jsonable_encoder
from api import utils
from api.router import events, teams, news
import warnings
from datetime import datetime, timezone, timedelta


app = FastAPI(title="ISAC (website API), BTU Cottbus-Senftenberg", openapi_url="/openapi.yml")

app.include_router(events.router, dependencies=[Depends(utils.generic_user)])
app.include_router(teams.router, dependencies=[Depends(utils.generic_user)])
app.include_router(news.router, dependencies=[Depends(utils.generic_user)])
app.include_router(utils.router)

class Registration(utils.User):
    password: str = "x"

@app.get("/")
def root():
    return {"mesage": f"You are at homepage"}

@app.post("/request")
async def request_access(data: Registration):
    user_info = utils.text_db.Base("user-access")
    hashed_password = utils.pwd_context.hash(data.password)
    data.active_inactive = "inactive" # always keep this inactive, so that no one can signup unless made active in db
    encoded = jsonable_encoder(data)

    # do not store the password
    del encoded["password"]
    encoded.update(jsonable_encoder({
        "hashed_password": hashed_password,
        "modified_time": datetime.now(timezone.utc).isoformat()}))
    duplicate_entry = user_info.fetch({"email": data.email}).items
    for entry in duplicate_entry:
        warnings.warn("This email id already exits. Creating new credentials and removing old ones")
        user_info.delete(entry["key"])
    user_info.insert(encoded)
    return encoded

@app.put("/authorize", dependencies=[Depends(utils.oauth2_schema), Depends(utils.admin_user)], include_in_schema=True)
async def authorize(email):
    user_info = utils.text_db.Base("user-access")
    user_data = user_info.fetch({"email": email}).items
    if user_data:
        for user in user_data:
            user_info.update({"active_inactive": "active"}, key=user["key"])
        return {"mesage": "Success"}
    return {"message": f"The following email:{email} doesn't exists. First request authentication, then authorise."}
