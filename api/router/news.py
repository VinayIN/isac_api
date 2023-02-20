from fastapi import APIRouter

router = APIRouter(
    prefix="/news",
    tags=["news"]
)

@router.get("/")
async def home():
    return {"message": f"you are in news sections"}