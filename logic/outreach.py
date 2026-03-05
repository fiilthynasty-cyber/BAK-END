# logic/outreach.py
#
# CRM-style outreach state machine.
# Persists to Supabase table `outreach` with schema:
#
#   id            uuid PK default gen_random_uuid()
#   user_id       uuid FK users.id
#   lead_url      text not null
#   lead_title    text
#   source        text
#   score         int
#   intent        text
#   status        text  -- "new" | "contacted" | "replied" | "converted" | "dismissed"
#   message_draft text
#   notes         text
#   created_at    timestamptz default now()
#   updated_at    timestamptz default now()
#   contacted_at  timestamptz
#   replied_at    timestamptz
#   converted_at  timestamptz
#
# Usage:
#   outreach_id = save_outreach(sb, user_id, lead, draft)
#   mark_contacted(sb, outreach_id)
#   mark_replied(sb, outreach_id, notes="they said yes")
#   mark_converted(sb, outreach_id)
#   list_outreach(sb, user_id, status="contacted")

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

VALID_STATUSES = {"new", "contacted", "replied", "converted", "dismissed"}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


# ---------------------------------------------------------------------------
# Create / Read
# ---------------------------------------------------------------------------

def save_outreach(
    supabase,
    user_id: str,
    lead: Dict[str, Any],
    message_draft: Optional[str] = None,
) -> Optional[str]:
    """
    Save a lead to the outreach table with status "new".
    Returns the inserted row id, or None on failure.
    """
    payload: Dict[str, Any] = {
        "user_id": user_id,
        "lead_url": (lead.get("url") or lead.get("deep_link") or "").strip(),
        "lead_title": (lead.get("title") or "")[:500],
        "source": (lead.get("source") or "")[:80],
        "score": int(lead.get("score") or 0),
        "intent": (lead.get("intent") or "low")[:20],
        "status": "new",
        "message_draft": message_draft or "",
        "notes": "",
        "created_at": _now(),
        "updated_at": _now(),
    }

    try:
        resp = supabase.table("outreach").insert(payload).execute()
        rows = resp.data or []
        return rows[0]["id"] if rows else None
    except Exception as exc:
        print(f"save_outreach error: {exc}")
        return None


def list_outreach(
    supabase,
    user_id: str,
    status: Optional[str] = None,
    limit: int = 100,
) -> List[Dict[str, Any]]:
    """
    Return outreach rows for a user, optionally filtered by status.
    """
    query = (
        supabase.table("outreach")
        .select("*")
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .limit(limit)
    )
    if status and status in VALID_STATUSES:
        query = query.eq("status", status)

    resp = query.execute()
    return resp.data or []


def get_outreach(supabase, outreach_id: str) -> Optional[Dict[str, Any]]:
    resp = (
        supabase.table("outreach")
        .select("*")
        .eq("id", outreach_id)
        .limit(1)
        .execute()
    )
    rows = resp.data or []
    return rows[0] if rows else None


# ---------------------------------------------------------------------------
# Status transitions
# ---------------------------------------------------------------------------

def _update_status(
    supabase,
    outreach_id: str,
    new_status: str,
    extra: Optional[Dict[str, Any]] = None,
):
    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status: {new_status!r}")

    payload: Dict[str, Any] = {
        "status": new_status,
        "updated_at": _now(),
        **(extra or {}),
    }
    supabase.table("outreach").update(payload).eq("id", outreach_id).execute()


def mark_contacted(supabase, outreach_id: str, notes: str = ""):
    _update_status(supabase, outreach_id, "contacted", {
        "contacted_at": _now(),
        "notes": notes,
    })


def mark_replied(supabase, outreach_id: str, notes: str = ""):
    _update_status(supabase, outreach_id, "replied", {
        "replied_at": _now(),
        "notes": notes,
    })


def mark_converted(supabase, outreach_id: str, notes: str = ""):
    _update_status(supabase, outreach_id, "converted", {
        "converted_at": _now(),
        "notes": notes,
    })


def dismiss_outreach(supabase, outreach_id: str, notes: str = ""):
    _update_status(supabase, outreach_id, "dismissed", {"notes": notes})


def update_draft(supabase, outreach_id: str, draft: str):
    supabase.table("outreach").update({
        "message_draft": draft[:8000],
        "updated_at": _now(),
    }).eq("id", outreach_id).execute()


# ---------------------------------------------------------------------------
# Stats helpers (for analytics)
# ---------------------------------------------------------------------------

def outreach_stats(supabase, user_id: str) -> Dict[str, int]:
    """
    Returns per-status counts for a user's outreach pipeline.
    """
    all_rows = list_outreach(supabase, user_id, limit=5000)
    counts: Dict[str, int] = {s: 0 for s in VALID_STATUSES}
    for row in all_rows:
        s = row.get("status") or "new"
        counts[s] = counts.get(s, 0) + 1
    return counts
