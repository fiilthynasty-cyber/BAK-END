from fastapi import APIRouter

router = APIRouter()


@router.post("/login")
def login() -> dict[str, str]:
    return {"message": "Login endpoint placeholder"}


@router.post("/signup")
def signup() -> dict[str, str]:
    return {"message": "Signup endpoint placeholder"}
