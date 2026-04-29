import json
import os

import anthropic
from dotenv import load_dotenv

from api.models import SituationProfile

load_dotenv()

_client: anthropic.Anthropic | None = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    return _client


SYSTEM_PROMPT = """You are SCOUT's situation extraction engine for Mumzworld, the Middle East's largest parenting e-commerce platform.

Your job: extract a structured SituationProfile from a mom's free-text input. She may write in English, Arabic, or a mix.

Rules:
- Extract only what is stated or strongly implied. Never infer what is not there.
- Return null for any field you cannot resolve with confidence.
- If you cannot determine the current parenting situation at all, set node_confidence below 0.6 and generate a clarifying_question.
- Do NOT infer medical conditions from casual language.
- Do NOT assume the mom is asking a medical question — if she describes symptoms, set them in special_conditions only.
- Map current_node_id to the closest matching node from the provided list.
- If input is in Arabic, process natively — do not translate to English first.
- Return ONLY valid JSON. No markdown fences, no explanation, just the JSON object.

Node mapping guidance:
- pregnancy weeks 4-12 → early_pregnancy
- pregnancy weeks 13-26 → second_trimester  
- pregnancy weeks 26-30 → 28_weeks_pregnant
- pregnancy weeks 30-34 → 32_weeks_pregnant
- pregnancy weeks 34-38 → 36_weeks_pregnant
- twins pregnancy → twins_pregnancy
- baby age 0-1 week → newborn_first_week
- baby age 1-4 weeks → newborn_1_month
- baby age 6-10 weeks → infant_2_months
- baby age 14-18 weeks → infant_4_months
- baby age 22-26 weeks → infant_6_months
- baby age 30-34 weeks → infant_8_months
- baby age 38-44 weeks → infant_10_months
- baby age 11-14 months → first_birthday
- baby age 17-20 months → toddler_18_months
- baby age 22-26 months → toddler_2_years
- unclear → unknown (confidence < 0.6, add clarifying_question)"""


def extract_situation(user_input: str, node_ids: list[str]) -> SituationProfile:
    schema = {
        "pregnancy_weeks": "int or null",
        "child_age_months": "int or null",
        "parity": "first_time | experienced | unknown",
        "location_country": "string or null (UAE, KSA, Qatar, Kuwait, Bahrain, Oman, or null)",
        "location_type": "string or null (apartment, villa, house, or null)",
        "support_level": "high | medium | low | unknown",
        "current_node_id": f"one of: {', '.join(node_ids)}",
        "node_confidence": "float 0.0-1.0",
        "input_language": "en | ar | mixed",
        "has_twins": "boolean",
        "is_working_mom": "boolean or null",
        "special_conditions": "array of strings",
        "unresolvable_fields": "array of field names that could not be determined",
        "extraction_notes": "string",
        "clarifying_question": "string or null — only if node_confidence < 0.6"
    }

    prompt = f"""Extract a SituationProfile from this input.

Input: "{user_input}"

Return JSON matching this schema exactly:
{json.dumps(schema, indent=2)}"""

    try:
        response = _get_client().messages.create(
            model=os.getenv("EXTRACTION_MODEL", "claude-haiku-4-5-20251001"),
            max_tokens=800,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": prompt}]
        )

        raw = response.content[0].text.strip()
        raw = raw.replace("```json", "").replace("```", "").strip()

        data = json.loads(raw)
        return SituationProfile(**data)

    except (json.JSONDecodeError, Exception):
        return SituationProfile(
            parity="unknown",
            support_level="unknown",
            current_node_id="unknown",
            node_confidence=0.3,
            input_language="en",
            clarifying_question="Could you tell me how far along your pregnancy is, or how old your baby is? That will help me give you the most relevant information."
        )
