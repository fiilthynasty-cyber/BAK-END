from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class AnalyticsRequest(BaseModel):
    leads: List[Dict[str, Any]]


@router.post("/report")
def analytics_report(body: AnalyticsRequest) -> Dict[str, Any]:
    """Full analytics report over a batch of scored leads."""
    from logic.analytics import full_report
    return full_report(body.leads)


@router.post("/summary")
def analytics_summary(body: AnalyticsRequest) -> Dict[str, Any]:
    from logic.analytics import summarise_leads
    return summarise_leads(body.leads)
