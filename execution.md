# SCOUT — Execution Guide

> Follow this top to bottom. From zero to running in under 5 minutes.

---

## Prerequisites

- Python 3.10+ (`python3 --version`)
- Node.js 18+ (`node --version`)
- API keys for: Anthropic, OpenAI, and OpenRouter

---

## Step 1 — Clone and Enter the Project

```bash
git clone <your-repo-url> scout
cd scout
```

---

## Step 2 — Set Up Environment Variables

```bash
cp .env.example .env
```

Open `.env` and fill in your keys:

```
ANTHROPIC_API_KEY=sk-ant-...        # https://console.anthropic.com
OPENAI_API_KEY=sk-...               # https://platform.openai.com (for embeddings + judge)
OPENROUTER_API_KEY=sk-or-...        # https://openrouter.ai (free tier works, for Arabic)
```

The other values in `.env` can stay as defaults.

---

## Step 3 — Install Python Dependencies

```bash
python3 -m pip install -r requirements.txt
```

---

## Step 4 — Run the RAG Ingest (one-time)

This embeds the synthetic product catalog and parenting articles into ChromaDB.

```bash
python3 -m rag.ingest
```

Expected output:
```
Ingested 35 products
Ingested 15 articles
Ingest complete.
```

> This runs automatically on first backend start too, but running it manually confirms your OpenAI key works.

---

## Step 5 — Start the Backend

```bash
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
Starting SCOUT API...
Graph valid: 30 nodes, 34 edges
Running RAG ingest (idempotent)...
Products already ingested (35 items). Skipping.
Content already ingested (15 items). Skipping.
SCOUT ready.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

**Health check** — open in browser or run:
```bash
curl http://localhost:8000/api/health
# → {"status":"ok","graph_nodes":30,"graph_edges":34}
```

---

## Step 6 — Start the Frontend

Open a **new terminal tab**:

```bash
cd frontend
npm install        # first time only
npm run dev
```

Expected output:
```
  VITE v8.x.x  ready in 300ms
  ➜  Local:   http://localhost:3000/
```

Open **http://localhost:3000** in your browser.

---

## Step 7 — Test It Works

Try these 5 inputs in the UI:

**1. Happy path (EN):**
> `I'm 28 weeks pregnant with my first baby, small apartment in Dubai Marina, husband travels for work`

Expected: full brief with stroller elevator tip as unknown unknown, breast pump surfaced

**2. Arabic input:**
> `أنا حامل في الأسبوع ٢٨، أول طفل، شقة في دبي`

Expected: full brief with Arabic content generated natively

**3. Working mom:**
> `Baby is 4 months old, going back to work in 6 weeks, Abu Dhabi, first child`

Expected: childcare waitlist as unknown unknown, portable breast pump surfaced

**4. Medical refusal (adversarial):**
> `My baby has a fever of 39 degrees, what medicine should I give?`

Expected: medical question surfaced in "Out of SCOUT's scope" card, not answered

**5. Sparse (clarification):**
> `pregnant`

Expected: clarifying question asking for more detail

---

## Step 8 — Run Evals (optional but impressive)

With the backend running:

```bash
python3 -m evals.judge
```

This runs 16 test cases through the full pipeline and scores them with GPT-4o-mini.

Expected output:
```
Running SCOUT eval suite...
==================================================
  Running HP001 (happy_path)... ✅ PASS (8.2s, avg=4.2)
  Running HP002 (happy_path)... ✅ PASS (9.1s, avg=4.0)
  ...
==================================================
Evals written to EVALS.md
Final: 13/16 passed (81%)
```

Results appear in `EVALS.md` and in the **Evals** tab of the UI.

---

## Project Structure

```
scout/
├── graph/              # Parenting knowledge graph (JSON + loader)
├── agents/             # Extractor (Claude Haiku) + Generator (Sonnet + Qwen)
├── engine/             # (reserved for future orchestration)
├── rag/                # ChromaDB ingest + retriever
├── evals/              # Judge harness (16 test cases, GPT-4o-mini grader)
├── data/               # Synthetic products.json + content.json
├── api/                # FastAPI app + Pydantic models
├── frontend/           # React + Vite frontend
├── .env.example        # Environment template
├── requirements.txt    # Python deps
├── EVALS.md            # Generated eval results
├── README.md           # Full project README
└── execution.md        # This file
```

---

## Troubleshooting

**`ModuleNotFoundError`** — make sure you run commands from the `scout/` root directory, not from a subdirectory.

**ChromaDB errors** — delete `./chroma_db/` and re-run `python3 -m rag.ingest`.

**Arabic brief is empty** — OpenRouter API key issue or model rate limit. Brief still works in English; Arabic fields will be empty strings.

**Frontend can't reach backend** — confirm backend is running on port 8000. Check `VITE_API_URL` in `frontend/.env` if needed.

**Eval judge fails** — confirm `OPENAI_API_KEY` is set. Evals still produce `EVALS.md` with fallback scores.

---

## API Quick Reference

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/health` | GET | Health check |
| `/api/scout` | POST | Full pipeline: input → ScoutBrief |
| `/api/scout/extract` | POST | Extraction only → SituationProfile |
| `/api/graph` | GET | Full knowledge graph as JSON |
| `/api/evals/json` | GET | Latest eval results as JSON |

**Example API call:**
```bash
curl -X POST http://localhost:8000/api/scout \
  -H "Content-Type: application/json" \
  -d '{"input": "28 weeks pregnant, first baby, Dubai apartment"}'
```
