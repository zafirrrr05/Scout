import os
import time
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

load_dotenv()

from agents.extractor import extract_situation
from agents.generator import generate_brief
from api.models import EvalReport, EvalResult, EvalScore, ScoutBrief, ScoutRequest, SituationProfile
from graph.graph_loader import get_graph, get_node_ids, traverse_forward, get_unknown_unknowns
from rag.ingest import run_ingest
from rag.retriever import retrieve_for_nodes


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting SCOUT API...")
    G = get_graph()
    print(f"Graph loaded: {len(G.nodes())} nodes")
    print("Running RAG ingest (idempotent)...")
    try:
        run_ingest()
    except Exception as e:
        print(f"Ingest warning: {e}")
    print("SCOUT ready.")
    yield


app = FastAPI(
    title="SCOUT API",
    version="1.0.0",
    description="Situation-Aware Commerce Intelligence for Mumzworld",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
async def health():
    G = get_graph()
    return {
        "status": "ok",
        "graph_nodes": len(G.nodes()),
        "graph_edges": len(G.edges())
    }


@app.post("/api/scout", response_model=ScoutBrief)
async def run_scout(request: ScoutRequest):
    start = time.time()
    G = get_graph()
    node_ids = get_node_ids(G)

    profile: SituationProfile = extract_situation(request.input, node_ids)

    if profile.node_confidence < 0.6 or profile.current_node_id == "unknown":
        raise HTTPException(
            status_code=400,
            detail={
                "message": "Need more context to generate your SCOUT brief",
                "clarifying_question": profile.clarifying_question or "Could you tell me how far along your pregnancy is, or how old your baby is?"
            }
        )

    horizon = traverse_forward(
        profile,
        G,
        max_nodes=5,
        max_weeks=request.max_horizon_weeks
    )

    horizon_node_ids = [h.node_id for h in horizon]
    horizon_labels = [h.situation for h in horizon]
    rag_results = retrieve_for_nodes(
        [profile.current_node_id] + horizon_node_ids,
        [profile.current_node_id] + horizon_labels
    )

    unknown_unknowns = get_unknown_unknowns(profile, horizon, G)

    brief = generate_brief(
        profile=profile,
        horizon=horizon,
        rag_results=rag_results,
        unknown_unknowns=unknown_unknowns,
        processing_start=start
    )

    return brief


@app.post("/api/scout/extract", response_model=SituationProfile)
async def extract_only(request: ScoutRequest):
    G = get_graph()
    node_ids = get_node_ids(G)
    return extract_situation(request.input, node_ids)


@app.get("/api/graph")
async def get_graph_data():
    G = get_graph()
    return {
        "nodes": [dict(G.nodes[n], id=n) for n in G.nodes()],
        "edges": [
            {"from": u, "to": v, **d}
            for u, v, d in G.edges(data=True)
        ]
    }


@app.get("/api/evals", response_model=EvalReport)
async def get_evals():
    evals_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "EVALS.md")
    if not os.path.exists(evals_path):
        raise HTTPException(status_code=404, detail="Evals not yet run. Run: python -m evals.judge")

    return EvalReport(
        run_at="see EVALS.md",
        total_cases=16,
        pass_rate=0.0,
        aggregate_scores={},
        cases=[]
    )


@app.get("/api/evals/json")
async def get_evals_json():
    import json
    evals_json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "evals",
        "results.json"
    )
    if not os.path.exists(evals_json_path):
        return {"message": "Evals not yet run", "cases": []}
    with open(evals_json_path) as f:
        return json.load(f)
