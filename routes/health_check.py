from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health-check")
def health_check() -> dict[str, str]:
    return {"status": "ok"}
