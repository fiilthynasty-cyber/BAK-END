# worker/scraper_worker.py
#
# Continuous polling worker: runs the lead-discovery pipeline on a schedule,
# then rescores every existing DB lead using BeautifulSoup + OpenAI.
#
# Environment variables:
#   POLL_INTERVAL_SECONDS  (default 3600 = 1 hour)
#   PIPELINE_USER_ID       required — Supabase user id to run under
#   SUPABASE_URL           required for Supabase-backed features
#   SUPABASE_SERVICE_KEY   required for Supabase-backed features
#   COMPANY_URL, COMPANY_NAME, COMPANY_NICHE, COMPANY_KEYWORDS, COMPANY_LOCATIONS
#   DATABASE_URL           PostgreSQL connection string
#   OPENAI_API_KEY         required for AI rescoring
#   OPENAI_MODEL           (default gpt-4.1-mini)
#
# Run:
#   python scraper_worker.py

import json
import logging
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup
from openai import OpenAI

# Ensure repo root is on sys.path when run directly
sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("scraper_worker")

POLL_INTERVAL = int(os.getenv("POLL_INTERVAL_SECONDS", "3600"))
USER_ID = os.getenv("PIPELINE_USER_ID", "dev-user")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4.1-mini")

_openai = OpenAI()


def _build_company():
    from logic.query_builder import CompanyProfile

    kw_raw = os.getenv("COMPANY_KEYWORDS", "")
    keywords = tuple(k.strip() for k in kw_raw.split(",") if k.strip())

    loc_raw = os.getenv("COMPANY_LOCATIONS", "")
    locations = tuple(l.strip() for l in loc_raw.split(",") if l.strip())

    return CompanyProfile(
        url=os.getenv("COMPANY_URL", "https://example.com"),
        name=os.getenv("COMPANY_NAME", "My Company"),
        niche=os.getenv("COMPANY_NICHE", "software"),
        keywords=keywords or ("software",),
        locations=locations,
    )


def _get_supabase():
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_SERVICE_KEY")
    if url and key:
        from supabase import create_client
        return create_client(url, key)
    return None


def _scrape_title(url: str) -> str:
    """Fetch a lead URL and return its <title> text (falls back to the URL)."""
    try:
        resp = requests.get(url, timeout=10, headers={"User-Agent": "Mozilla/5.0"})
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        return soup.title.string.strip() if soup.title and soup.title.string else url
    except Exception as exc:
        logger.debug("_scrape_title(%s) failed: %s", url, exc)
        return url


def _ai_rescore_lead(url: str, name: str) -> dict:
    """Ask the AI to return a JSON score/intent/reason for a lead."""
    prompt = (
        f"Analyze the business '{name}' at {url}.\n"
        "Return ONLY valid JSON with keys: score (int 0-100), intent (\"high\"|\"medium\"|\"low\"), reason (str)."
    )
    try:
        resp = _openai.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            response_format={"type": "json_object"},
        )
        return json.loads(resp.choices[0].message.content)
    except Exception as exc:
        logger.warning("_ai_rescore_lead(%s) failed: %s", url, exc)
        return {"score": 50, "intent": "medium", "reason": str(exc)}


def rescore_existing_leads() -> None:
    """Loop over every LeadORM row, scrape its URL, ask AI for a new score, and save."""
    from backend.utils.db import SessionLocal
    from backend.models import LeadORM

    db = SessionLocal()
    try:
        leads = db.query(LeadORM).all()
        logger.info("Rescoring %d existing leads...", len(leads))
        for lead in leads:
            try:
                name = _scrape_title(lead.url)
                data = _ai_rescore_lead(lead.url, name)
                lead.score = int(data.get("score", lead.score))
                lead.intent = str(data.get("intent", lead.intent))
                lead.ai_reason = str(data.get("reason", ""))
                lead.last_seen = datetime.now(timezone.utc)
                logger.debug("Rescored lead %d (%s): score=%s intent=%s", lead.id, lead.url, lead.score, lead.intent)
            except Exception as exc:
                logger.error("Failed to rescore lead %d: %s", lead.id, exc, exc_info=True)
        db.commit()
        logger.info("Rescore complete.")
    except Exception as exc:
        db.rollback()
        logger.error("rescore_existing_leads failed: %s", exc, exc_info=True)
    finally:
        db.close()


def run_once():
    from logic.pipeline import PipelineOptions, run_pipeline

    company = _build_company()
    supabase = _get_supabase()
    opts = PipelineOptions(max_queries=20, min_score=35)

    logger.info("Starting pipeline for '%s' (%s)", company.name, company.url)
    result = run_pipeline(supabase, USER_ID, company, opts=opts)
    summary = result.summary()

    logger.info(
        "Pipeline done: %d leads found (%d hot), %d queries run, %d skipped, %d errors",
        summary["total_leads"],
        summary["hot_leads"],
        summary["queries_run"],
        summary["queries_skipped"],
        len(summary["errors"]),
    )
    for err in summary["errors"]:
        logger.warning("Pipeline error: %s", err)

    rescore_existing_leads()

    return result


def run_worker():
    logger.info("Worker started. Poll interval: %ds", POLL_INTERVAL)
    while True:
        try:
            run_once()
        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
            break
        except Exception as exc:
            logger.error("Unhandled error in run_once: %s", exc, exc_info=True)

        logger.info("Sleeping %ds until next run...", POLL_INTERVAL)
        try:
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            logger.info("Worker stopped by user.")
            break


if __name__ == "__main__":
    run_worker()
