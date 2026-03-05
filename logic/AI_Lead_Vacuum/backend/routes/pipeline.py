from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

router = APIRouter()


# ---------------------------------------------------------------------------
# Request / Response schemas
# ---------------------------------------------------------------------------

class CompanyProfileRequest(BaseModel):
    url: str = Field(min_length=4, max_length=500)
    name: Optional[str] = Field(default=None, max_length=120)
    niche: Optional[str] = Field(default=None, max_length=120)
    keywords: List[str] = Field(default_factory=list)
    locations: List[str] = Field(default_factory=list)


class PipelineRequest(BaseModel):
    user_id: str = Field(min_length=1, max_length=200)
    company: CompanyProfileRequest
    positioning: Optional[Dict[str, Any]] = None
    max_queries: int = Field(default=20, ge=1, le=100)
    min_score: int = Field(default=30, ge=0, le=100)
    sources: List[str] = Field(default=["reddit", "hn"])
    run_ai_analysis: bool = False
    run_reply_draft: bool = False


class ScoredLeadOut(BaseModel):
    title: str
    url: str
    deep_link: str
    snippet: str
    source: str
    created_at_iso: str
    score: int
    intent: str
    reasons: Dict[str, Any]
    meta: Dict[str, Any]
    ai_analysis: Optional[Dict[str, Any]] = None
    reply_draft: Optional[Dict[str, Any]] = None


class PipelineResponse(BaseModel):
    leads: List[ScoredLeadOut]
    summary: Dict[str, Any]


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("/run", response_model=PipelineResponse, status_code=status.HTTP_200_OK)
def run_pipeline_endpoint(body: PipelineRequest) -> PipelineResponse:
    """
    Trigger a full lead-discovery pipeline run for a company profile.
    Requires Supabase + billing to be configured server-side.
    """
    try:
        # Lazy import: pipeline uses supabase + logic modules
        from logic.pipeline import run_pipeline, PipelineOptions
        from logic.query_builder import CompanyProfile
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Logic layer not available: {exc}",
        )

    company = CompanyProfile(
        url=body.company.url,
        name=body.company.name,
        niche=body.company.niche,
        keywords=tuple(body.company.keywords),
        locations=tuple(body.company.locations),
    )

    opts = PipelineOptions(
        max_queries=body.max_queries,
        min_score=body.min_score,
        sources=body.sources,
        run_ai_analysis=body.run_ai_analysis,
        run_reply_draft=body.run_reply_draft,
    )

    # supabase is None in dev/test; pipeline handles gracefully
    result = run_pipeline(
        supabase=None,
        user_id=body.user_id,
        company=company,
        positioning=body.positioning,
        opts=opts,
    )

    leads_out = [ScoredLeadOut(**lead.to_dict()) for lead in result.leads]

    return PipelineResponse(leads=leads_out, summary=result.summary())
