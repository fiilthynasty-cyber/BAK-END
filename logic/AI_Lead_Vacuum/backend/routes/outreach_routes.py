from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


class SaveOutreachRequest(BaseModel):
    user_id: str
    lead: Dict[str, Any]
    message_draft: Optional[str] = None


class StatusUpdateRequest(BaseModel):
    notes: str = ""


class DraftUpdateRequest(BaseModel):
    draft: str = Field(max_length=8000)


class OutreachListResponse(BaseModel):
    rows: List[Dict[str, Any]]


@router.post("/", status_code=status.HTTP_201_CREATED)
def create_outreach(body: SaveOutreachRequest) -> Dict[str, Any]:
    from logic.outreach import save_outreach
    row_id = save_outreach(None, body.user_id, body.lead, body.message_draft)
    if row_id is None:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Supabase not configured — cannot persist outreach.",
        )
    return {"id": row_id}


@router.get("/{user_id}", response_model=OutreachListResponse)
def get_outreach_list(user_id: str, status_filter: Optional[str] = None) -> OutreachListResponse:
    from logic.outreach import list_outreach
    rows = list_outreach(None, user_id, status=status_filter)
    return OutreachListResponse(rows=rows)


@router.get("/{user_id}/stats")
def get_outreach_stats(user_id: str) -> Dict[str, int]:
    from logic.outreach import outreach_stats
    return outreach_stats(None, user_id)


@router.patch("/{outreach_id}/contacted")
def contacted(outreach_id: str, body: StatusUpdateRequest) -> Dict[str, str]:
    from logic.outreach import mark_contacted
    mark_contacted(None, outreach_id, body.notes)
    return {"status": "contacted"}


@router.patch("/{outreach_id}/replied")
def replied(outreach_id: str, body: StatusUpdateRequest) -> Dict[str, str]:
    from logic.outreach import mark_replied
    mark_replied(None, outreach_id, body.notes)
    return {"status": "replied"}


@router.patch("/{outreach_id}/converted")
def converted(outreach_id: str, body: StatusUpdateRequest) -> Dict[str, str]:
    from logic.outreach import mark_converted
    mark_converted(None, outreach_id, body.notes)
    return {"status": "converted"}


@router.patch("/{outreach_id}/dismiss")
def dismiss(outreach_id: str, body: StatusUpdateRequest) -> Dict[str, str]:
    from logic.outreach import dismiss_outreach
    dismiss_outreach(None, outreach_id, body.notes)
    return {"status": "dismissed"}


@router.patch("/{outreach_id}/draft")
def update_draft_endpoint(outreach_id: str, body: DraftUpdateRequest) -> Dict[str, str]:
    from logic.outreach import update_draft
    update_draft(None, outreach_id, body.draft)
    return {"status": "updated"}
