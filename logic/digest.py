# logic/digest.py
#
# Builds plaintext + HTML email digests from a batch of scored leads.
#
# Usage:
#   from logic.digest import build_digest
#   digest = build_digest(leads, project_name="My App", period="daily")
#   print(digest.text)
#   send_html_email(to=user_email, subject=digest.subject, html=digest.html)

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

_INTENT_EMOJI = {"high": "🔥", "medium": "⚡", "low": "·"}


@dataclass
class Digest:
    subject: str
    text: str
    html: str
    lead_count: int
    hot_count: int
    period: str


def _intent_label(intent: str) -> str:
    return _INTENT_EMOJI.get(intent, "·") + " " + intent.upper()


def _score_bar(score: int, width: int = 10) -> str:
    filled = round(score / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _truncate(s: str, n: int) -> str:
    s = (s or "").strip()
    return s[:n] + ("…" if len(s) > n else "")


# ---------------------------------------------------------------------------
# Plain text
# ---------------------------------------------------------------------------

def _build_text(
    leads: List[Dict[str, Any]],
    project_name: str,
    period: str,
    generated_at: str,
) -> str:
    hot = [l for l in leads if int(l.get("score") or 0) >= 70]
    other = [l for l in leads if int(l.get("score") or 0) < 70]

    lines: List[str] = [
        f"{'='*60}",
        f"AI Lead Vacuum — {period.title()} Digest",
        f"Project: {project_name}",
        f"Generated: {generated_at} UTC",
        f"{'='*60}",
        f"Total leads: {len(leads)}   Hot leads: {len(hot)}",
        "",
    ]

    if hot:
        lines += [f"{'─'*40}", "🔥 HOT LEADS", f"{'─'*40}"]
        for i, lead in enumerate(hot[:10], 1):
            score = int(lead.get("score") or 0)
            lines += [
                f"{i}. [{score}] {_truncate(lead.get('title',''), 80)}",
                f"   Intent : {lead.get('intent','').upper()}",
                f"   Source : {lead.get('source', '')}",
                f"   URL    : {lead.get('deep_link') or lead.get('url','')}",
                f"   Score  : {_score_bar(score)} {score}/100",
                "",
            ]

    if other:
        lines += [f"{'─'*40}", "OTHER LEADS", f"{'─'*40}"]
        for i, lead in enumerate(other[:20], 1):
            score = int(lead.get("score") or 0)
            lines += [
                f"{i}. [{score}] {_truncate(lead.get('title',''), 80)}",
                f"   {lead.get('source','')} | {lead.get('intent','').upper()} | {lead.get('deep_link') or lead.get('url','')}",
                "",
            ]

    lines += [f"{'='*60}", "Powered by AI Lead Vacuum", f"{'='*60}"]
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# HTML
# ---------------------------------------------------------------------------

_HTML_STYLE = """
  body{font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;
       background:#f4f6f8;margin:0;padding:20px}
  .card{background:#fff;border-radius:10px;padding:24px;max-width:640px;
        margin:0 auto;box-shadow:0 2px 8px rgba(0,0,0,.08)}
  h1{font-size:1.3rem;margin:0 0 4px}
  .meta{color:#666;font-size:.8rem;margin-bottom:20px}
  .section{margin-top:24px}
  .section-title{font-size:.75rem;font-weight:700;text-transform:uppercase;
                 letter-spacing:.06em;color:#555;border-bottom:1px solid #e5e7eb;
                 padding-bottom:6px;margin-bottom:12px}
  .lead{margin-bottom:14px;padding:12px 14px;border-radius:8px;border:1px solid #e5e7eb}
  .lead.hot{border-left:4px solid #ef4444}
  .lead.medium{border-left:4px solid #f59e0b}
  .lead.low{border-left:4px solid #94a3b8}
  .lead-title a{font-weight:600;font-size:.9rem;color:#1a1a1a;text-decoration:none}
  .lead-title a:hover{text-decoration:underline}
  .pill{display:inline-block;font-size:.65rem;font-weight:700;padding:2px 7px;
        border-radius:999px;margin-right:4px;text-transform:uppercase}
  .pill-source{background:#eff6ff;color:#2563eb}
  .pill-high{background:#fef2f2;color:#ef4444}
  .pill-medium{background:#fffbeb;color:#b45309}
  .pill-low{background:#f1f5f9;color:#64748b}
  .score{font-size:.75rem;color:#555;margin-top:4px}
  .footer{text-align:center;font-size:.7rem;color:#9ca3af;margin-top:24px}
"""


def _intent_pill(intent: str) -> str:
    cls = f"pill-{intent}" if intent in ("high", "medium", "low") else "pill-low"
    label = _INTENT_EMOJI.get(intent, "") + intent.upper()
    return f'<span class="pill {cls}">{label}</span>'


def _source_pill(source: str) -> str:
    return f'<span class="pill pill-source">{source}</span>'


def _lead_html(lead: Dict[str, Any]) -> str:
    score = int(lead.get("score") or 0)
    intent = lead.get("intent") or "low"
    url = lead.get("deep_link") or lead.get("url") or "#"
    title = _truncate(lead.get("title") or "Untitled", 100)
    source = lead.get("source") or "unknown"
    css_cls = "hot" if score >= 70 else intent

    return f"""
  <div class="lead {css_cls}">
    <div class="lead-title"><a href="{url}" target="_blank" rel="noopener noreferrer">{title}</a></div>
    <div style="margin-top:5px">{_source_pill(source)}{_intent_pill(intent)}</div>
    <div class="score">Score: <strong>{score}</strong>/100</div>
  </div>"""


def _build_html(
    leads: List[Dict[str, Any]],
    project_name: str,
    period: str,
    generated_at: str,
) -> str:
    hot = [l for l in leads if int(l.get("score") or 0) >= 70]
    other = [l for l in leads if int(l.get("score") or 0) < 70]

    hot_html = "\n".join(_lead_html(l) for l in hot[:10]) or "<p style='color:#888'>None this period.</p>"
    other_html = "\n".join(_lead_html(l) for l in other[:20]) or ""

    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{period.title()} Lead Digest — {project_name}</title>
<style>{_HTML_STYLE}</style></head>
<body>
<div class="card">
  <h1>AI Lead Vacuum — {period.title()} Digest</h1>
  <div class="meta">Project: <strong>{project_name}</strong> &nbsp;·&nbsp; {generated_at} UTC &nbsp;·&nbsp; {len(leads)} leads found, {len(hot)} hot</div>

  <div class="section">
    <div class="section-title">🔥 Hot Leads (score ≥ 70)</div>
    {hot_html}
  </div>

  {"<div class='section'><div class='section-title'>Other Leads</div>" + other_html + "</div>" if other_html else ""}

  <div class="footer">Powered by AI Lead Vacuum</div>
</div>
</body></html>"""


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_digest(
    leads: List[Dict[str, Any]],
    project_name: str = "Your Project",
    period: str = "daily",
) -> Digest:
    """
    Build a Digest from a list of scored lead dicts.
    `period` is a label only: "daily" | "weekly" | "hourly".
    """
    leads_sorted = sorted(leads, key=lambda l: int(l.get("score") or 0), reverse=True)
    hot = [l for l in leads_sorted if int(l.get("score") or 0) >= 70]
    now_str = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")
    subject = (
        f"🔥 {len(hot)} hot leads · {project_name} {period} digest ({now_str})"
        if hot else
        f"📬 {len(leads_sorted)} leads · {project_name} {period} digest ({now_str})"
    )

    text = _build_text(leads_sorted, project_name, period, now_str)
    html = _build_html(leads_sorted, project_name, period, now_str)

    return Digest(
        subject=subject,
        text=text,
        html=html,
        lead_count=len(leads_sorted),
        hot_count=len(hot),
        period=period,
    )
