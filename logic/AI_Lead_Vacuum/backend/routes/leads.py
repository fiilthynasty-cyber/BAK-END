from __future__ import annotations

import os
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from openai import OpenAI
from sqlalchemy.orm import Session

from backend.models import LeadCreate, LeadORM, LeadOut, LeadUpdate, OutreachORM, OutreachOut
from backend.utils.db import get_db

router = APIRouter()
_openai = OpenAI()  # reads OPENAI_API_KEY from env
_AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")


def _get_or_404(db: Session, lead_id: int) -> LeadORM:
    row = db.get(LeadORM, lead_id)
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Lead not found")
    return row


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------

@router.get("/", response_model=list[LeadOut])
def list_leads(
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=50, ge=1, le=500),
    min_score: Optional[float] = Query(default=None, ge=0, le=100),
    intent: Optional[str] = Query(default=None, max_length=50),
    db: Session = Depends(get_db),
) -> list[LeadORM]:
    q = db.query(LeadORM).order_by(LeadORM.score.desc())
    if min_score is not None:
        q = q.filter(LeadORM.score >= min_score)
    if intent:
        q = q.filter(LeadORM.intent == intent)
    return q.offset(skip).limit(limit).all()


@router.post("/", response_model=LeadOut, status_code=status.HTTP_201_CREATED)
def create_lead(payload: LeadCreate, db: Session = Depends(get_db)) -> LeadORM:
    row = LeadORM(**payload.model_dump())
    db.add(row)
    db.commit()
    db.refresh(row)
    return row


@router.get("/{lead_id}", response_model=LeadOut)
def get_lead(lead_id: int, db: Session = Depends(get_db)) -> LeadORM:
    return _get_or_404(db, lead_id)


@router.put("/{lead_id}", response_model=LeadOut)
def update_lead(lead_id: int, payload: LeadUpdate, db: Session = Depends(get_db)) -> LeadORM:
    row = _get_or_404(db, lead_id)
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


@router.delete("/{lead_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_lead(lead_id: int, db: Session = Depends(get_db)) -> None:
    row = _get_or_404(db, lead_id)
    db.delete(row)
    db.commit()


# ---------------------------------------------------------------------------
# AI outreach send
# ---------------------------------------------------------------------------

@router.post("/{lead_id}/outreach", response_model=OutreachOut, status_code=status.HTTP_201_CREATED)
def send_outreach(lead_id: int, db: Session = Depends(get_db)) -> OutreachORM:
    """
    Generate an AI outreach message for the lead and persist it.
    Requires OPENAI_API_KEY environment variable.
    """
    lead = _get_or_404(db, lead_id)

    system_prompt = (
        "You are a concise, human outbound sales writer. "
        "Write one short, personalised outreach message (max 5 lines). "
        "No hype, no AI mentions, no invented claims. End with one CTA question."
    )
    user_prompt = (
        f"Business: {lead.business_name}\n"
        f"URL: {lead.url}\n"
        f"Intent: {lead.intent or 'unknown'}\n"
        f"Score: {lead.score}\n"
        f"Reason: {lead.ai_reason or 'N/A'}"
    )

    response = _openai.chat.completions.create(
        model=_AI_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.7,
        max_tokens=300,
    )
    message_text = (response.choices[0].message.content or "").strip()

    outreach = OutreachORM(lead_id=lead.id, message=message_text, status="sent")
    db.add(outreach)
    db.commit()
    db.refresh(outreach)
    return outreach


@router.get("/{lead_id}/outreach", response_model=list[OutreachOut])
def list_outreach_for_lead(lead_id: int, db: Session = Depends(get_db)) -> list[OutreachORM]:
    _get_or_404(db, lead_id)
    return (
        db.query(OutreachORM)
        .filter(OutreachORM.lead_id == lead_id)
        .order_by(OutreachORM.sent_at.desc())
        .all()
    )
