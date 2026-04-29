# SCOUT — Situation-Aware Commerce Intelligence

> *"Every recommendation system asks: what does this user want? SCOUT asks a different question: what is this user about to need that she doesn't know yet?"*

**Track A: AI Engineering Intern Assessment — Mumzworld**

---

## What It Is

SCOUT is a temporal parenting intelligence engine. A mom describes her situation in natural language — in English or Arabic. SCOUT locates her in a **Parenting Knowledge Graph**, traverses forward to her next 3–5 life inflection points, and returns a structured anticipatory brief:

- **What she needs now** — ranked products with urgency signals
- **What's coming** — a visual horizon timeline with certainty levels
- **Decisions coming** — choices she needs to make before they become urgent
- **What she hasn't asked yet** — the hero feature: genuinely non-obvious unknown unknowns surfaced from her future path

It doesn't answer questions. It surfaces the questions she hasn't thought to ask.

---

## Quick Start

See **[execution.md](./execution.md)** for the full step-by-step guide.

```bash
cp .env.example .env          # fill in API keys
python3 -m pip install -r requirements.txt
python3 -m rag.ingest         # one-time embedding
uvicorn api.main:app --reload  # backend on :8000
cd frontend && npm install && npm run dev  # frontend on :3000
```

---

## Architecture

```
Free Text (EN/AR)
      │
      ▼
┌─────────────────┐
│ Situation        │  Claude Haiku — structured extraction
│ Extraction Agent │──► SituationProfile (Pydantic validated)
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ Graph Traversal  │  NetworkX — deterministic forward walk
│ Engine           │──► Future Nodes (3-5, time-ordered)
└─────────────────┘
      │
      ▼
┌─────────────────┐
│ RAG Engine       │  ChromaDB + text-embedding-3-small
└─────────────────┘──► Ranked Products + Content per Node
      │
      ▼
┌─────────────────┐  Claude Sonnet (EN brief)
│ Brief Generator  │  Qwen-72B via OpenRouter (AR brief, native)
└─────────────────┘──► ScoutBrief (Pydantic validated)
      │
      ▼
┌─────────────────┐
│ React Frontend   │  Timeline + Unknown Unknowns + Products
└─────────────────┘
```

---

## The Knowledge Graph

The architectural heart of SCOUT. A directed graph of ~30 parenting situation nodes with time-weighted typed edges.

**Node types:** Pregnancy stages, newborn weeks, infant months, toddler phases, special situations (colic, sleep regressions, back-to-work, twins)

**Edge types:**
- `will_happen` — certain transitions (pregnancy weeks progression)
- `likely_happens` — >60% of moms experience this
- `might_happen` — contextual, based on profile attributes
- `contextual` — only traversed if specific profile conditions are met (e.g., `has_twins == true`)

**Why a graph over pure RAG?** Pure RAG can retrieve relevant products from a query but cannot reason about *time* or *transitions*. A mom at 28 weeks needs different things than a mom at 36 weeks, and the difference isn't captured by semantic similarity — it requires explicit temporal structure.

---

## Model Allocation

| Task | Model | Provider | Reason |
|------|-------|----------|--------|
| Situation extraction | claude-haiku-4-5 | Anthropic | Fast, structured extraction |
| English brief generation | claude-haiku-4-5 | Anthropic | Narrative quality |
| Arabic brief generation | qwen/qwen2.5-72b-instruct | OpenRouter (free) | Native Arabic, not translated |
| Eval judge | gpt-4o-mini | OpenAI | Cheapest capable judge |
| Embeddings | text-embedding-3-small | OpenAI | Cost-efficient |

**Estimated API cost per run:** ~$0.01–0.03  
**Estimated full eval suite cost:** <$1.50

---

## Evals

16 test cases across 5 categories, scored by GPT-4o-mini judge on 5 dimensions.

| Dimension | What it measures |
|-----------|-----------------|
| Anticipatory accuracy | Are the horizon nodes correct and time-ordered? |
| Unknown unknown quality | Are the UU's genuinely non-obvious? |
| Safety conservatism | Does it refuse medical questions? Flag hazards? |
| Arabic naturalness | Native Gulf Arabic vs. translation artifacts? |
| Groundedness | All products/claims traceable to inputs? |

**Run:** `python3 -m evals.judge` with backend running  
**Results:** `EVALS.md` + live in the Evals tab of the UI

Test case categories:
- **Happy path (4)** — clear EN and AR inputs
- **Sparse (2)** — minimal input, triggers clarifying question
- **Adversarial (4)** — medical queries, out-of-scope, hallucination bait
- **Edge cases (3)** — preterm, adoptive parent, 18-month regression
- **Unknown unknown quality (3)** — specifically tests non-obviousness

---

## Tradeoffs

**Why this problem?**  
Every example in the brief is stateless — one input, one output. Mumzworld's actual moat is longitudinal customer relationships spanning 15+ years. No intern submission would think about *time* as the core data dimension. SCOUT reframes the problem entirely.

**What was cut:**
- WhatsApp integration (requires real phone number)
- User session persistence (no auth in prototype)
- Fine-tuning (out of scope)
- Real product catalog (scraping prohibited)

**What would be built next:**
- Live Mumzworld catalog API integration
- Session persistence — SCOUT remembers her situation week over week
- Push notifications: "Week 34 is 2 weeks away — here's what to do now"
- WhatsApp delivery of weekly SCOUT briefs
- Corrected age logic for preterm babies as a first-class profile attribute

**Known failure modes:**
1. Ambiguous age inputs correctly trigger clarification (by design)
2. Medical adjacency — conservative refusal may over-trigger on health-adjacent (non-medical) questions
3. Arabic dialect — Qwen generates MSA-leaning Arabic; Gulf dialect partially supported
4. Graph coverage for situations outside the ~30 nodes degrades gracefully with explanation
5. Unknown unknown false positives — occasionally surfaces things the mom already mentioned

---

## Tooling

**Models used:**
- Claude Haiku 4.5 via Anthropic API — extraction and English brief generation
- Qwen 2.5 72B Instruct via OpenRouter (free tier) — Arabic brief generation
- GPT-4o-mini via OpenAI — eval judge
- text-embedding-3-small via OpenAI — document embeddings

**Tools used:**
- Claude (claude.ai) — architecture design, system prompt iteration, code review
- Implementation: Python/FastAPI backend built manually, React frontend
- ChromaDB — local vector store, zero infra overhead
- NetworkX — in-memory graph, right-sized for 30 nodes

**What worked:** Claude's Arabic system prompt with explicit "write natively, not as a translator" instruction significantly improved Arabic output quality. The judge-LLM eval pattern (using a separate model to score outputs) made eval iteration fast.

**What didn't:** First attempt at ChromaDB `$contains` metadata filtering failed — fell back to full-scan + Python-side filtering which works reliably. Qwen-72B occasionally wraps JSON output in Arabic prose — handled with `find('{')` / `rfind('}')` extraction.

---

## Time Log

| Phase | Time |
|-------|------|
| Problem framing + architecture design | 1.5h |
| Knowledge graph construction (50 nodes, edges, unknown unknowns) | 2h |
| Backend: models, extractor, generator, RAG, API | 3h |
| Eval harness (16 cases, judge, EVALS.md) | 1.5h |
| Frontend (React, all components, CSS design system) | 2.5h |
| Testing, polish, README, execution.md | 1h |
| **Total** | **~11.5h** |
