import json
import os
from datetime import datetime

import anthropic
import httpx
from dotenv import load_dotenv

from api.models import (
    Decision,
    HorizonItem,
    Product,
    SafetyFlag,
    ScoutBrief,
    SituationProfile,
    UnknownUnknown,
)

load_dotenv()

_claude_client: anthropic.Anthropic | None = None


def _get_claude() -> anthropic.Anthropic:
    global _claude_client
    if _claude_client is None:
        _claude_client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _claude_client


ENGLISH_SYSTEM = """You are SCOUT, a situation-aware parenting intelligence engine for Mumzworld, the Middle East's largest parenting platform.

You receive structured context about a mom's situation: her current parenting stage, upcoming horizon situations, retrieved products and content, and unknown unknowns candidates.

Your job: generate a ScoutBrief JSON object in English.

Rules:
- Every product must come from the retrieved_products list. Do not invent products.
- Every claim must be grounded in input context or retrieved content.
- CRITICAL: If you detect a medical question (symptoms, dosage, diagnosis), add it to out_of_scope_queries and do NOT answer it. Instead say "Please consult your pediatrician or OB."
- Unknown unknowns must be genuinely non-obvious — not things a first-time mom would obviously think of.
- Tone: warm, specific, knowledgeable. Like a friend who happens to know everything about parenting in the GCC.
- If uncertain about any claim, omit it rather than guess.
- Set grounded: false and populate hallucination_flags if you generate content not traceable to inputs.
- Return ONLY valid JSON. No markdown, no explanation.

JSON schema to return:
{
  "current_situation_summary": "string — warm, specific 2-sentence summary of her current stage",
  "horizon": [{"node_id": "str", "situation": "str", "situation_ar": "", "weeks_until": int, "certainty": "will_happen|likely_happens|might_happen", "preview": "str", "preview_ar": ""}],
  "immediate_needs": [{"id": "str from products", "name": "str", "name_ar": "", "reason": "str — why she needs this NOW specifically", "reason_ar": "", "urgency": "immediate|soon|upcoming", "price_range_aed": "str", "node_source": "str", "safety_cleared": true}],
  "decisions_coming": [{"title": "str", "title_ar": "", "description": "str", "description_ar": "", "deadline_weeks": int, "stakes": "str — why this decision matters", "stakes_ar": ""}],
  "unknown_unknowns": [{"insight": "str — the thing she doesn't know", "insight_ar": "", "why_it_matters": "str", "why_it_matters_ar": "", "related_product_ids": ["str"], "surprise_score": float 0.0-1.0}],
  "safety_flags": [{"product_id": "str", "product_name": "str", "flag": "str", "severity": "warning|critical"}],
  "confidence": float,
  "input_language": "str",
  "generated_at": "ISO timestamp",
  "out_of_scope_queries": ["str — medical questions detected"],
  "refusal_message": null or "str",
  "grounded": true,
  "hallucination_flags": []
}"""


ARABIC_SYSTEM = """أنت SCOUT، محرك ذكاء التسوق الاستباقي لمنصة Mumzworld.

مهمتك: إكمال الحقول العربية في ScoutBrief الذي أُعطيت مسودته بالإنجليزية.

قواعد صارمة:
- اكتب كمتحدث عربي أصيل، وليس كمترجم. لا تنقل بنية الجمل الإنجليزية إلى العربية.
- استخدم أسلوباً مناسباً لجمهور الخليج العربي (الإمارات، السعودية، قطر، الكويت، البحرين، عُمان).
- الأسلوب: دافئ، محدد، موثوق. كصديقة تعرف كل شيء عن تربية الأطفال في الخليج.
- لا تترجم حرفياً من الإنجليزية — أنشئ المحتوى العربي بأسلوبك الخاص.
- أعد JSON يحتوي فقط على الحقول العربية المطلوبة.
- أعد JSON صالحاً فقط. لا ماركداون، لا شرح.

الحقول المطلوبة:
{
  "current_situation_summary_ar": "ملخص الوضع الحالي بالعربية — جملتان دافئتان ومحددتان",
  "horizon_ar": [{"node_id": "str", "situation_ar": "str", "preview_ar": "str"}],
  "immediate_needs_ar": [{"id": "str", "name_ar": "str", "reason_ar": "str"}],
  "decisions_ar": [{"title_ar": "str", "description_ar": "str", "stakes_ar": "str"}],
  "unknown_unknowns_ar": [{"insight_ar": "str", "why_it_matters_ar": "str"}]
}"""


def _call_openrouter(prompt: str, context_json: str) -> dict:
    api_key = os.getenv("OPENROUTER_API_KEY", "")
    model = os.getenv("GENERATION_MODEL_AR", "qwen/qwen2.5-72b-instruct")

    try:
        response = httpx.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://scout.mumzworld.ai",
            },
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": ARABIC_SYSTEM},
                    {"role": "user", "content": f"Context (English brief):\n{context_json}\n\nGenerate the Arabic fields JSON now."}
                ],
                "max_tokens": 2000,
                "temperature": 0.3
            },
            timeout=60.0
        )
        data = response.json()
        if "choices" not in data:
            return {}
        raw = data["choices"][0]["message"]["content"]
        raw = raw.strip()
        start = raw.find("{")
        end = raw.rfind("}") + 1
        if start >= 0 and end > start:
            return json.loads(raw[start:end])
        return {}
    except Exception:
        return {}


def _merge_arabic(brief_dict: dict, ar_dict: dict) -> dict:
    if not ar_dict:
        return brief_dict

    brief_dict["current_situation_summary_ar"] = ar_dict.get(
        "current_situation_summary_ar",
        brief_dict.get("current_situation_summary_ar", "")
    )

    horizon_ar = {h["node_id"]: h for h in ar_dict.get("horizon_ar", [])}
    for item in brief_dict.get("horizon", []):
        node_id = item.get("node_id", "")
        if node_id in horizon_ar:
            item["situation_ar"] = horizon_ar[node_id].get("situation_ar", item.get("situation_ar", ""))
            item["preview_ar"] = horizon_ar[node_id].get("preview_ar", item.get("preview_ar", ""))

    needs_ar = {n["id"]: n for n in ar_dict.get("immediate_needs_ar", [])}
    for product in brief_dict.get("immediate_needs", []):
        pid = product.get("id", "")
        if pid in needs_ar:
            product["name_ar"] = needs_ar[pid].get("name_ar", product.get("name_ar", ""))
            product["reason_ar"] = needs_ar[pid].get("reason_ar", product.get("reason_ar", ""))

    decisions_ar = ar_dict.get("decisions_ar", [])
    for i, decision in enumerate(brief_dict.get("decisions_coming", [])):
        if i < len(decisions_ar):
            decision["title_ar"] = decisions_ar[i].get("title_ar", decision.get("title_ar", ""))
            decision["description_ar"] = decisions_ar[i].get("description_ar", decision.get("description_ar", ""))
            decision["stakes_ar"] = decisions_ar[i].get("stakes_ar", decision.get("stakes_ar", ""))

    unknowns_ar = ar_dict.get("unknown_unknowns_ar", [])
    for i, unk in enumerate(brief_dict.get("unknown_unknowns", [])):
        if i < len(unknowns_ar):
            unk["insight_ar"] = unknowns_ar[i].get("insight_ar", unk.get("insight_ar", ""))
            unk["why_it_matters_ar"] = unknowns_ar[i].get("why_it_matters_ar", unk.get("why_it_matters_ar", ""))

    return brief_dict


def generate_brief(
    profile: SituationProfile,
    horizon: list[HorizonItem],
    rag_results: dict,
    unknown_unknowns: list[str],
    processing_start: float
) -> ScoutBrief:
    import time

    context = {
        "profile": profile.model_dump(),
        "horizon": [h.model_dump() for h in horizon],
        "retrieved_products": rag_results.get("products", []),
        "retrieved_content_key_points": [
            point
            for item in rag_results.get("content", [])
            for point in item.get("key_points", [])
        ],
        "unknown_unknowns_candidates": unknown_unknowns[:8],
        "instruction": "Generate ScoutBrief JSON for this mom's situation."
    }

    context_json = json.dumps(context, ensure_ascii=False, indent=2)

    response = _get_claude().messages.create(
        model=os.getenv("GENERATION_MODEL_EN", "claude-haiku-4-5-20251001"),
        max_tokens=3000,
        system=ENGLISH_SYSTEM,
        messages=[{"role": "user", "content": context_json}]
    )

    raw = response.content[0].text.strip()
    start_idx = raw.find("{")
    end_idx = raw.rfind("}") + 1
    if start_idx >= 0 and end_idx > start_idx:
        raw = raw[start_idx:end_idx]

    en_dict = json.loads(raw)
    en_dict["generated_at"] = datetime.utcnow().isoformat()
    en_dict["input_language"] = profile.input_language

    if not en_dict.get("current_situation_summary_ar"):
        en_dict["current_situation_summary_ar"] = ""

    ar_context = json.dumps({
        "current_situation_summary": en_dict.get("current_situation_summary", ""),
        "horizon": en_dict.get("horizon", []),
        "immediate_needs": en_dict.get("immediate_needs", []),
        "decisions_coming": en_dict.get("decisions_coming", []),
        "unknown_unknowns": en_dict.get("unknown_unknowns", [])
    }, ensure_ascii=False)

    ar_dict = _call_openrouter("", ar_context)
    merged = _merge_arabic(en_dict, ar_dict)
    merged["processing_time_ms"] = int((time.time() - processing_start) * 1000)

    horizon_items = []
    for h in merged.get("horizon", []):
        certainty = h.get("certainty", "might_happen")
        if certainty not in ["will_happen", "likely_happens", "might_happen"]:
            certainty = "might_happen"
        horizon_items.append(HorizonItem(
            node_id=h.get("node_id", ""),
            situation=h.get("situation", ""),
            situation_ar=h.get("situation_ar", ""),
            weeks_until=h.get("weeks_until", 0),
            certainty=certainty,
            preview=h.get("preview", ""),
            preview_ar=h.get("preview_ar", "")
        ))

    products = []
    for p in merged.get("immediate_needs", []):
        urgency = p.get("urgency", "upcoming")
        if urgency not in ["immediate", "soon", "upcoming"]:
            urgency = "upcoming"
        products.append(Product(
            id=p.get("id", "unknown"),
            name=p.get("name", ""),
            name_ar=p.get("name_ar", ""),
            reason=p.get("reason", ""),
            reason_ar=p.get("reason_ar", ""),
            urgency=urgency,
            price_range_aed=str(p.get("price_range_aed", "")),
            node_source=p.get("node_source", ""),
            safety_cleared=p.get("safety_cleared", True)
        ))

    decisions = []
    for d in merged.get("decisions_coming", []):
        decisions.append(Decision(
            title=d.get("title", ""),
            title_ar=d.get("title_ar", ""),
            description=d.get("description", ""),
            description_ar=d.get("description_ar", ""),
            deadline_weeks=d.get("deadline_weeks", 4),
            stakes=d.get("stakes", ""),
            stakes_ar=d.get("stakes_ar", "")
        ))

    unknowns = []
    for u in merged.get("unknown_unknowns", []):
        unknowns.append(UnknownUnknown(
            insight=u.get("insight", ""),
            insight_ar=u.get("insight_ar", ""),
            why_it_matters=u.get("why_it_matters", ""),
            why_it_matters_ar=u.get("why_it_matters_ar", ""),
            related_product_ids=u.get("related_product_ids", []),
            surprise_score=float(u.get("surprise_score", 0.8))
        ))

    safety_flags = []
    for sf in merged.get("safety_flags", []):
        severity = sf.get("severity", "warning")
        if severity not in ["warning", "critical"]:
            severity = "warning"
        safety_flags.append(SafetyFlag(
            product_id=sf.get("product_id", ""),
            product_name=sf.get("product_name", ""),
            flag=sf.get("flag", ""),
            severity=severity
        ))

    return ScoutBrief(
        current_situation_summary=merged.get("current_situation_summary", ""),
        current_situation_summary_ar=merged.get("current_situation_summary_ar", ""),
        horizon=horizon_items,
        immediate_needs=products,
        decisions_coming=decisions,
        unknown_unknowns=unknowns,
        safety_flags=safety_flags,
        confidence=float(merged.get("confidence", 0.8)),
        input_language=profile.input_language,
        generated_at=merged.get("generated_at", datetime.utcnow().isoformat()),
        processing_time_ms=merged.get("processing_time_ms", 0),
        out_of_scope_queries=merged.get("out_of_scope_queries", []),
        refusal_message=merged.get("refusal_message"),
        grounded=merged.get("grounded", True),
        hallucination_flags=merged.get("hallucination_flags", [])
    )
