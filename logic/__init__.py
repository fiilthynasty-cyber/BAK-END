# logic/__init__.py
# Public API surface for the logic package.

from logic.analytics import full_report, summarise_leads, top_sources, intent_breakdown
from logic.billing import can_use, consume, remaining, get_user_plan, get_limits
from logic.cache import filter_queries, mark_query_run, is_url_cached, mark_url_cached, cleanup_old_cache
from logic.digest import build_digest, Digest
from logic.notify import maybe_alert_hot_lead, is_hot_lead
from logic.outreach import (
    save_outreach, list_outreach, get_outreach,
    mark_contacted, mark_replied, mark_converted, dismiss_outreach,
    update_draft, outreach_stats,
)
from logic.pipeline import run_pipeline, PipelineOptions, PipelineResult, ScoredLead
from logic.query_builder import build_queries, CompanyProfile
from logic.scoring import score_lead, ScoreWeights
from logic.sources import fetch_reddit, fetch_hn, fetch_indiehackers_rss
from logic.referrals import ensure_referral_code, attribute_referral

__all__ = [
    # analytics
    "full_report", "summarise_leads", "top_sources", "intent_breakdown",
    # billing
    "can_use", "consume", "remaining", "get_user_plan", "get_limits",
    # cache
    "filter_queries", "mark_query_run", "is_url_cached", "mark_url_cached", "cleanup_old_cache",
    # digest
    "build_digest", "Digest",
    # notify
    "maybe_alert_hot_lead", "is_hot_lead",
    # outreach
    "save_outreach", "list_outreach", "get_outreach",
    "mark_contacted", "mark_replied", "mark_converted", "dismiss_outreach",
    "update_draft", "outreach_stats",
    # pipeline
    "run_pipeline", "PipelineOptions", "PipelineResult", "ScoredLead",
    # query builder
    "build_queries", "CompanyProfile",
    # scoring
    "score_lead", "ScoreWeights",
    # sources
    "fetch_reddit", "fetch_hn", "fetch_indiehackers_rss",
    # referrals
    "ensure_referral_code", "attribute_referral",
]
