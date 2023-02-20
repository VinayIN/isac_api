from fastapi import APIRouter

router = APIRouter(
    prefix="/events",
    tags=["events"]
)

@router.get("/{year}")
async def home(year: int, month: int):
    return {"message": f"you have entered {year}, and query {month}"}