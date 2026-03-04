import os
import re
from datetime import datetime, timezone
from flask import Flask, request, jsonify
from flask_cors import CORS

# ---------------------------------------
# IntentFlow Backend (Revenue Playbook API)
# ---------------------------------------
# Endpoints:
#   GET  /health
#   POST /api/analyzeLead   { "lead": "..." }
#
# Notes:
# - Deterministic scoring so it works immediately (no LLM required).
# - Stable response contract for the frontend dashboard.
# - Easy to extend later with OpenAI / LLM scoring while keeping the same output shape.
# - CORS configured for local dev + your Vercel domain.
# ---------------------------------------

app = Flask(__name__)

# CORS: add your domains here if needed
CORS(
    app,
    resources={r"/*": {"origins": [
        "https://front-end-aiyf.vercel.app",
        "http://localhost:5173",
        "http://127.0.0.1:5173"
    ]}},
)

# -----------------------
# Utilities
# -----------------------
def utc_now_iso():
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

def json_error(message, status=400, **extra):
    payload = {"ok": False, "message": message}
    payload.update(extra)
    return jsonify(payload), status

def _count_hits(text, keywords):
    t = text.lower()
    return [k for k in keywords if k in t]

def _extract_name_company(text):
    """
    Light extraction for UX quality:
    - Name: first capitalized word on first line
    - Company: "at X" or "from X"
    """
    name = None
    company = None

    m = re.search(r"^\s*([A-Z][a-z]+)\b", text.strip())
    if m:
        name = m.group(1)

    m2 = re.search(r"\bat\s+([A-Z][A-Za-z0-9&\-\.\s]{2,40})", text)
    if m2:
        company = m2.group(1).strip()
    else:
        m3 = re.search(r"\bfrom\s+([A-Z][A-Za-z0-9&\-\.\s]{2,40})", text)
        if m3:
            company = m3.group(1).strip()

    return name, company

# -----------------------
# Scoring model (deterministic)
# -----------------------
URGENT = ["asap", "urgent", "today", "this week", "immediately", "now", "this month", "deadline"]
BUDGET = ["budget", "pricing", "price", "cost", "quote", "proposal", "invoice", "purchase", "buy"]
EVALUATION = ["comparing", "evaluate", "evaluating", "options", "alternatives", "shortlist", "vendor", "demo"]
PAIN = ["problem", "pain", "struggling", "wasting", "manual", "slow", "bottleneck", "inefficient", "can't", "cannot"]
TIMING = ["q1", "q2", "q3", "q4", "quarter", "next week", "next month", "this quarter", "end of month"]
AUTHORITY = ["founder", "ceo", "owner", "vp", "director", "head of", "manager", "lead", "president"]
POSITIVE = ["interested", "love to", "sounds good", "let's", "next steps", "send", "book", "schedule"]
NEGATIVE = ["not interested", "no budget", "later", "maybe", "we already", "not now", "too expensive"]

def _score_lead(text):
    """
    Produces:
      score (0-100)
      signals (dict)
      confidence ("low" | "medium" | "high")
    """
    urg = _count_hits(text, URGENT)
    bud = _count_hits(text, BUDGET)
    eva = _count_hits(text, EVALUATION)
    pain = _count_hits(text, PAIN)
    tim = _count_hits(text, TIMING)
    auth = _count_hits(text, AUTHORITY)
    pos = _count_hits(text, POSITIVE)
    neg = _count_hits(text, NEGATIVE)

    # Weighted score: designed to rank "ready to buy" signals higher.
    score = 20
    score += min(20, 5 * len(pain))      # pain present
    score += min(20, 7 * len(eva))       # evaluating tools
    score += min(20, 8 * len(bud))       # budget/pricing language
    score += min(15, 6 * len(urg))       # urgency words
    score += min(10, 5 * len(tim))       # timeline words
    score += min(10, 4 * len(auth))      # authority signals
    score += min(10, 3 * len(pos))       # positive intent language
    score -= min(25, 8 * len(neg))       # negative signals

    score = max(0, min(100, score))

    signals = {
        "urgency": urg,
        "budget": bud,
        "evaluation": eva,
        "pain": pain,
        "timing": tim,
        "authority": auth,
        "positive": pos,
        "negative": neg,
    }

    active_categories = sum(1 for _, v in signals.items() if len(v) > 0)
    confidence = "high" if active_categories >= 4 else "medium" if active_categories >= 2 else "low"

    return score, signals, confidence

def _tier(score):
    if score >= 85:
        return "HOT"
    if score >= 60:
        return "WARM"
    return "COLD"

def _build_playbook(lead_text, score, signals, confidence):
    """
    Output contract used by the frontend dashboard:
      score, tier, confidence, summary, next_step, message, reasons, followups, signals
    """
    name, company = _extract_name_company(lead_text)
    tier = _tier(score)

    bits = []
    if signals["pain"]: bits.append("pain signals")
    if signals["budget"]: bits.append("budget language")
    if signals["evaluation"]: bits.append("active evaluation")
    if signals["urgency"] or signals["timing"]: bits.append("time/urgency")
    if signals["authority"]: bits.append("decision authority")
    if not bits: bits.append("limited signals; needs qualification")

    summary = f"{tier} lead based on " + ", ".join(bits) + f". Confidence: {confidence}."

    if tier == "HOT":
        next_step = "Send a short, specific message today and ask for a 10â€“15 minute call."
    elif tier == "WARM":
        next_step = "Send value-first message + 1 qualifying question (timeline/budget)."
    else:
        next_step = "Qualify with 2 questions. If weak, move to nurture and donâ€™t waste time."

    who = name or "there"
    where = f" at {company}" if company else ""

    # Message: short, revenue-forward, with two qualifying questions.
    message = "\n".join([
        f"Hey {who},",
        "",
        f"Quick note â€” saw youâ€™re looking at improving your process{where}.",
        "If youâ€™re trying to cut manual work and move faster, I can show a simple workflow that gets a win quickly.",
        "",
        "Two fast questions: whatâ€™s your timeline, and what does â€˜successâ€™ look like in 30 days?",
        "If itâ€™s helpful, I can share a 2-step plan and examples. Worth a quick 10 minutes?"
    ])

    reasons = []
    if signals["budget"]:
        reasons.append("Pricing/budget language = commercial intent.")
    if signals["evaluation"]:
        reasons.append("Evaluation/comparison language = near-term decision cycle.")
    if signals["urgency"] or signals["timing"]:
        reasons.append("Timing/urgency language = higher close probability.")
    if signals["authority"]:
        reasons.append("Authority keywords suggest decision power.")
    if signals["pain"]:
        reasons.append("Pain language suggests active problem + motivation.")
    if not reasons:
        reasons.append("Not enough buying signals yet â€” qualify before investing time.")

    followups = [
        "Follow-up (24h): one-line nudge + ask about timeline.",
        "Follow-up (72h): add a tiny proof point + ask for 10 minutes.",
        "Follow-up (7d): close-the-loop: â€˜should I close this out or revisit next month?â€™",
    ]

    return {
        "score": score,
        "tier": tier,
        "confidence": confidence,
        "summary": summary,
        "next_step": next_step,
        "message": message,
        "reasons": reasons,
        "followups": followups,
        "signals": signals,
    }

# -----------------------
# Routes
# -----------------------
@app.get("/health")
def health():
    return jsonify({"ok": True, "status": "healthy"}), 200

@app.post("/api/analyzeLead")
def analyze_lead():
    payload = request.get_json(silent=True) or {}
    lead_text = (payload.get("lead") or payload.get("text") or "").strip()

    if not lead_text:
        return json_error("Missing 'lead' in request body", 400)

    score, signals, confidence = _score_lead(lead_text)
    playbook = _build_playbook(lead_text, score, signals, confidence)

    return jsonify({
        "ok": True,
        "generated_at": utc_now_iso(),
        **playbook
    }), 200

# -----------------------
# Run local dev server
# (Render uses gunicorn typically; keep this for local testing.)
# -----------------------
if __name__ == "__main__":
    port = int(os.environ.get("PORT", "5000"))
    app.run(host="0.0.0.0", port=port)
