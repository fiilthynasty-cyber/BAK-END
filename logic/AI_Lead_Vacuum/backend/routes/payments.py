from fastapi import APIRouter

router = APIRouter()


@router.post("/subscribe")
def subscribe() -> dict[str, str]:
    return {"message": "Subscription endpoint placeholder"}
