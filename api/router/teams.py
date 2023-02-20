from fastapi import APIRouter

router = APIRouter(
    prefix="/teams",
    tags=["teams"]
)

@router.get("/{year}")
async def home(year: int):
    return {"message": f"You will get teams data for {year}"}