import json
import os

import chromadb
from openai import OpenAI


_chroma_client: chromadb.ClientAPI | None = None
_openai_client: OpenAI | None = None


def _get_chroma() -> chromadb.ClientAPI:
    global _chroma_client
    if _chroma_client is None:
        persist = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
        _chroma_client = chromadb.PersistentClient(path=persist)
    return _chroma_client


def _get_openai() -> OpenAI:
    global _openai_client
    if _openai_client is None:
        _openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
    return _openai_client


def _embed(text: str) -> list[float]:
    response = _get_openai().embeddings.create(
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        input=[text]
    )
    return response.data[0].embedding


def retrieve_for_nodes(node_ids: list[str], node_labels: list[str], top_k: int = 3) -> dict:
    query_text = f"products and advice for parenting stages: {', '.join(node_labels)}"
    query_embedding = _embed(query_text)

    chroma = _get_chroma()

    products_collection = chroma.get_or_create_collection("products")
    all_products = products_collection.get(include=["metadatas", "documents"])

    matched_products = []
    if all_products and all_products["ids"]:
        for i, pid in enumerate(all_products["ids"]):
            meta = all_products["metadatas"][i]
            tagged_nodes = json.loads(meta.get("nodes_tagged", "[]"))
            for node_id in node_ids:
                if node_id in tagged_nodes:
                    urgency_map = json.loads(meta.get("urgency_at_nodes", "{}"))
                    matched_products.append({
                        "id": pid,
                        "name": meta.get("name", ""),
                        "name_ar": meta.get("name_ar", ""),
                        "price_aed": meta.get("price_aed", ""),
                        "description": meta.get("description", ""),
                        "description_ar": meta.get("description_ar", ""),
                        "category": meta.get("category", ""),
                        "urgency": urgency_map.get(node_id, "upcoming"),
                        "node_source": node_id,
                        "compatibility_notes": meta.get("compatibility_notes", "")
                    })
                    break

    seen_ids: set[str] = set()
    unique_products = []
    for p in matched_products:
        if p["id"] not in seen_ids:
            seen_ids.add(p["id"])
            unique_products.append(p)

    unique_products.sort(key=lambda x: ["immediate", "soon", "upcoming"].index(x["urgency"]))
    products_result = unique_products[:top_k * len(node_ids)]

    content_collection = chroma.get_or_create_collection("content")
    content_results = content_collection.query(
        query_embeddings=[query_embedding],
        n_results=min(3, content_collection.count())
    )

    content_items = []
    if content_results and content_results["ids"] and content_results["ids"][0]:
        for i, cid in enumerate(content_results["ids"][0]):
            meta = content_results["metadatas"][0][i]
            content_items.append({
                "id": cid,
                "title": meta.get("title", ""),
                "title_ar": meta.get("title_ar", ""),
                "key_points": json.loads(meta.get("key_points", "[]"))
            })

    return {
        "products": products_result,
        "content": content_items
    }
