# logic/pipeline.py
#
# Master orchestrator — ties together every logic module.
#
# Usage:
#   from logic.pipeline import run_pipeline, PipelineOptions
#   from logic.query_builder import CompanyProfile
#
#   company = CompanyProfile(
#       url="https://myapp.com",
#       name="My App",
#       niche="project management",
#       keywords=("project management", "kanban", "team tasks"),
#       locations=("Austin",),
#   )
#   positioning = {
#       "name": "My App",
#       "url": "https://myapp.com",
#       "niche": "project management",
#       "keywords": ["kanban", "tasks"],
#   }
#   result = run_pipeline(supabase, user_id, company, positioning)
#   for lead in result.leads:
#       print(lead.score, lead.intent, lead.title)

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from logic.billing import can_use, consume
from logic.cache import filter_queries, mark_query_run
from logic.notify import maybe_alert_hot_lead
from logic.query_builder import CompanyProfile, build_queries
from logic.scoring import score_lead
from logic.sources import fetch_reddit, fetch_hn, fetch_indiehackers_rss

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

@dataclass
class PipelineOptions:
    """Tune pipeline behaviour without touching source code."""

    # how many SERP queries to build and run
    max_queries: int = 20

    # max leads fetched per source per query
    leads_per_query: int = 10

    # discard leads below this score
    min_score: int = 30

    # which upstream sources to poll
    sources: List[str] = field(default_factory=lambda: ["reddit", "hn", "indiehackers"])

    # optional AI enrichment (requires OPENAI_API_KEY + billing quota)
    run_ai_analysis: bool = False
    run_reply_draft: bool = False


# ---------------------------------------------------------------------------
# Output types
# ---------------------------------------------------------------------------

@dataclass
class ScoredLead:
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

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "url": self.url,
            "deep_link": self.deep_link,
            "snippet": self.snippet,
            "source": self.source,
            "created_at_iso": self.created_at_iso,
            "score": self.score,
            "intent": self.intent,
            "reasons": self.reasons,
            "meta": self.meta,
            "ai_analysis": self.ai_analysis,
            "reply_draft": self.reply_draft,
        }


@dataclass
class PipelineResult:
    leads: List[ScoredLead]
    queries_run: int
    queries_skipped: int
    raw_fetched: int
    below_threshold: int
    errors: List[str]

    @property
    def hot_leads(self) -> List[ScoredLead]:
        return [l for l in self.leads if l.score >= 70]

    @property
    def high_intent_leads(self) -> List[ScoredLead]:
        return [l for l in self.leads if l.intent == "high"]

    def summary(self) -> Dict[str, Any]:
        return {
            "total_leads": len(self.leads),
            "hot_leads": len(self.hot_leads),
            "high_intent": len(self.high_intent_leads),
            "queries_run": self.queries_run,
            "queries_skipped": self.queries_skipped,
            "raw_fetched": self.raw_fetched,
            "below_threshold": self.below_threshold,
            "errors": self.errors,
        }


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _dedupe_by_url(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    seen: set[str] = set()
    out: List[Dict[str, Any]] = []
    for item in leads:
        url = (item.get("url") or "").strip().lower()
        if url and url not in seen:
            seen.add(url)
            out.append(item)
    return out


def _fetch_from_source(
    source: str,
    query: str,
    limit: int,
    keywords: Optional[List[str]] = None,
) -> List[Dict[str, Any]]:
    if source == "reddit":
        return fetch_reddit(query, limit=limit)
    if source == "hn":
        return fetch_hn(query, limit=limit)
    if source == "indiehackers":
        return fetch_indiehackers_rss(keywords or [query], limit=limit)
    return []


def _run_ai_analysis(
    supabase,
    user_id: str,
    lead: ScoredLead,
    positioning: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    try:
        from logic.lead_ai import analyze_lead  # lazy import; OPENAI_API_KEY required
        if not can_use(supabase, user_id, "ai_classifications", amount=1):
            return None
        result = analyze_lead(
            lead={"title": lead.title, "content": lead.snippet, "source": lead.source},
            positioning=positioning,
        )
        consume(supabase, user_id, "ai_classifications", amount=1)
        return result
    except Exception as exc:
        logger.warning("AI analysis failed for %s: %s", lead.url, exc)
        return None


def _run_reply_draft(
    supabase,
    user_id: str,
    lead: ScoredLead,
    positioning: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    try:
        from logic.reply import draft_reply  # lazy import; OPENAI_API_KEY required
        if not can_use(supabase, user_id, "ai_classifications", amount=1):
            return None
        result = draft_reply(
            lead={
                "title": lead.title,
                "content": lead.snippet,
                "source": lead.source,
                "intent": lead.intent,
                "score": lead.score,
                "reasons": lead.reasons,
                "url": lead.url,
            },
            project=positioning,
        )
        consume(supabase, user_id, "ai_classifications", amount=1)
        return result
    except Exception as exc:
        logger.warning("Reply draft failed for %s: %s", lead.url, exc)
        return None


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------

def run_pipeline(
    supabase,
    user_id: str,
    company: CompanyProfile,
    positioning: Optional[Dict[str, Any]] = None,
    opts: Optional[PipelineOptions] = None,
) -> PipelineResult:
    """
    Full lead-discovery pipeline for one company profile.

    Steps
    -----
    1. Build SERP queries from company profile.
    2. Filter out queries still on cache cooldown.
    3. Check billing quota before fetching.
    4. Fetch raw leads from each configured source.
    5. Deduplicate by URL.
    6. Score every lead; drop those below min_score.
    7. Fire hot-lead notifications.
    8. Optionally enrich with AI analysis and/or reply draft.
    9. Consume billing quotas.
    10. Return sorted PipelineResult.
    """
    opts = opts or PipelineOptions()
    errors: List[str] = []

    # ── 1. Build queries ────────────────────────────────────────────────────
    all_queries = build_queries(company, max_queries=opts.max_queries)
    if not all_queries:
        return PipelineResult([], 0, 0, 0, 0, ["No queries generated from company profile"])

    # ── 2. Cache filter ─────────────────────────────────────────────────────
    queries_skipped = 0
    try:
        fresh_queries = filter_queries(supabase, all_queries)
        queries_skipped = len(all_queries) - len(fresh_queries)
    except Exception as exc:
        logger.warning("Cache filter unavailable: %s", exc)
        fresh_queries = all_queries

    if not fresh_queries:
        return PipelineResult([], 0, queries_skipped, 0, 0, ["All queries on cooldown"])

    n_queries = len(fresh_queries)

    # ── 3. Billing gate ─────────────────────────────────────────────────────
    try:
        if not can_use(supabase, user_id, "serp_queries", amount=n_queries):
            return PipelineResult([], 0, queries_skipped, 0, 0, ["serp_queries quota exceeded"])
    except Exception as exc:
        logger.warning("Billing check unavailable (proceeding): %s", exc)

    # ── 4. Fetch leads ───────────────────────────────────────────────────────
    raw: List[Dict[str, Any]] = []
    kw_list = list(company.keywords) + ([company.niche] if company.niche else [])

    for query in fresh_queries:
        for source in opts.sources:
            try:
                batch = _fetch_from_source(source, query, opts.leads_per_query, keywords=kw_list)
                raw.extend(batch)
            except Exception as exc:
                errors.append(f"{source} error [{query[:60]}]: {exc}")

        try:
            mark_query_run(supabase, query)
        except Exception:
            pass

    # ── 5. Deduplicate ───────────────────────────────────────────────────────
    raw = _dedupe_by_url(raw)
    raw_count = len(raw)

    # ── 6. Score + filter ────────────────────────────────────────────────────
    scored: List[ScoredLead] = []
    below_threshold = 0

    for item in raw:
        try:
            s, intent, reasons = score_lead(
                title=item.get("title", ""),
                content=item.get("snippet", ""),
                url=item.get("url", ""),
                source=item.get("source", ""),
                created_at_iso=item.get("created_at_iso"),
                meta=item.get("meta"),
            )
        except Exception as exc:
            errors.append(f"Scoring error: {exc}")
            continue

        if s < opts.min_score:
            below_threshold += 1
            continue

        lead = ScoredLead(
            title=item.get("title", ""),
            url=item.get("url", ""),
            deep_link=item.get("deep_link") or item.get("url", ""),
            snippet=item.get("snippet", ""),
            source=item.get("source", ""),
            created_at_iso=item.get("created_at_iso", ""),
            score=s,
            intent=intent,
            reasons=reasons,
            meta=item.get("meta") or {},
        )

        # ── 7. Notify hot leads ──────────────────────────────────────────────
        try:
            maybe_alert_hot_lead({
                "url": lead.url,
                "score": lead.score,
                "keywords": list(company.keywords),
            })
        except Exception as exc:
            errors.append(f"Notify error: {exc}")

        # ── 8a. AI analysis ──────────────────────────────────────────────────
        if opts.run_ai_analysis and positioning:
            lead.ai_analysis = _run_ai_analysis(supabase, user_id, lead, positioning)

        # ── 8b. Reply draft ──────────────────────────────────────────────────
        if opts.run_reply_draft and positioning:
            lead.reply_draft = _run_reply_draft(supabase, user_id, lead, positioning)

        scored.append(lead)

    # ── 9. Consume quotas ────────────────────────────────────────────────────
    try:
        consume(supabase, user_id, "serp_queries", amount=n_queries)
        consume(supabase, user_id, "scans", amount=raw_count)
    except Exception as exc:
        errors.append(f"Quota consume error: {exc}")

    # ── 10. Sort and return ──────────────────────────────────────────────────
    scored.sort(key=lambda l: l.score, reverse=True)

    return PipelineResult(
        leads=scored,
        queries_run=n_queries,
        queries_skipped=queries_skipped,
        raw_fetched=raw_count,
        below_threshold=below_threshold,
        errors=errors,
    )
