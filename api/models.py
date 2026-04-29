from pydantic import BaseModel, Field
from typing import Optional, Literal
from datetime import datetime


class SituationProfile(BaseModel):
    pregnancy_weeks: Optional[int] = None
    child_age_months: Optional[int] = None
    parity: Literal["first_time", "experienced", "unknown"] = "unknown"
    location_country: Optional[str] = None
    location_type: Optional[str] = None
    support_level: Literal["high", "medium", "low", "unknown"] = "unknown"
    current_node_id: str = "unknown"
    node_confidence: float = 0.0
    input_language: Literal["en", "ar", "mixed"] = "en"
    has_twins: bool = False
    is_working_mom: Optional[bool] = None
    special_conditions: list[str] = Field(default_factory=list)
    unresolvable_fields: list[str] = Field(default_factory=list)
    extraction_notes: str = ""
    clarifying_question: Optional[str] = None


class Product(BaseModel):
    id: str
    name: str
    name_ar: str
    reason: str
    reason_ar: str
    urgency: Literal["immediate", "soon", "upcoming"]
    price_range_aed: str
    node_source: str
    safety_cleared: bool = True


class HorizonItem(BaseModel):
    node_id: str
    situation: str
    situation_ar: str
    weeks_until: int
    certainty: Literal["will_happen", "likely_happens", "might_happen"]
    preview: str
    preview_ar: str


class Decision(BaseModel):
    title: str
    title_ar: str
    description: str
    description_ar: str
    deadline_weeks: int
    stakes: str
    stakes_ar: str


class UnknownUnknown(BaseModel):
    insight: str
    insight_ar: str
    why_it_matters: str
    why_it_matters_ar: str
    related_product_ids: list[str] = Field(default_factory=list)
    surprise_score: float = 0.8


class SafetyFlag(BaseModel):
    product_id: str
    product_name: str
    flag: str
    severity: Literal["warning", "critical"]


class ScoutBrief(BaseModel):
    current_situation_summary: str
    current_situation_summary_ar: str
    horizon: list[HorizonItem]
    immediate_needs: list[Product]
    decisions_coming: list[Decision]
    unknown_unknowns: list[UnknownUnknown]
    safety_flags: list[SafetyFlag]
    confidence: float
    input_language: str
    generated_at: str
    processing_time_ms: int = 0
    out_of_scope_queries: list[str] = Field(default_factory=list)
    refusal_message: Optional[str] = None
    grounded: bool = True
    hallucination_flags: list[str] = Field(default_factory=list)


class ScoutRequest(BaseModel):
    input: str
    language_preference: str = "auto"
    max_horizon_weeks: int = 12


class EvalScore(BaseModel):
    anticipatory_accuracy: int
    unknown_unknown_quality: int
    safety_conservatism: int
    arabic_naturalness: int
    groundedness: int


class EvalResult(BaseModel):
    case_id: str
    input: str
    scores: Optional[EvalScore] = None
    aggregate: float = 0.0
    passed: bool = False
    failures: list[str] = Field(default_factory=list)
    notes: str = ""
    error: Optional[str] = None


class EvalReport(BaseModel):
    run_at: str
    total_cases: int
    pass_rate: float
    aggregate_scores: dict
    cases: list[EvalResult]
