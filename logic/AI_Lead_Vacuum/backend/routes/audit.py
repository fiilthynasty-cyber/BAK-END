from __future__ import annotations

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class AuditRequest(BaseModel):
    url: str = Field(min_length=7, max_length=500)


@router.post("/site")
def audit_site_endpoint(body: AuditRequest) -> dict:
    """
    Fetch and AI-audit a website for conversion/positioning issues.
    Requires OPENAI_API_KEY environment variable.
    """
    try:
        from logic.site_audit import audit_site
        return audit_site(body.url)
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(exc),
        )
