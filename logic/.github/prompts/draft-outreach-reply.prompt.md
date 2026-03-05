---
description: "Use when drafting a short, human outbound reply from a lead plus project context; returns strict JSON with message, tone, and rationale"
name: "Draft Outreach Reply"
argument-hint: "Paste JSON with lead + project context"
agent: "agent"
---
Draft one short outbound reply using the JSON I provide in the prompt arguments.

Requirements:
- Use ONLY facts from the provided input JSON.
- No hype, no AI mentions, no invented claims.
- Keep output concise:
1. one opener line
2. two to four short body lines
3. one CTA question
- Reference the lead's pain point or buying signal when present.
- Do not claim first-hand product use.
- Match tone to context: `calm`, `direct`, or `friendly`.

Expected input format:
```json
{
  "project": {
    "name": "",
    "url": "",
    "niche": "",
    "keywords": [],
    "locations": []
  },
  "lead": {
    "source": "",
    "title": "",
    "content": "",
    "deep_link": "",
    "intent": "high|medium|low",
    "score": 0,
    "pain_points": [],
    "buying_signals": []
  }
}
```

Return valid JSON only:
```json
{
  "message": "",
  "tone": "calm|direct|friendly",
  "why_this_works": ["", ""]
}
```

Quality bar:
- Make the message feel human and specific to the lead text.
- Avoid generic templates and repetitive phrasing.
- If input is missing critical context, still return JSON but keep claims minimal and conservative.
