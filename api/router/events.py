from fastapi import APIRouter
from api.utils import do_nothing

router = APIRouter(
    prefix="/events",
    tags=["events"]
)

@router.get("/{year}")
async def home(year: int, month: int):
    return {"message": f"you have entered {year}, and query {month}"}