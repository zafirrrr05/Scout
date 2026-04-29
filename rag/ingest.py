import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import chromadb
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()


def embed_texts(client: OpenAI, texts: list[str]) -> list[list[float]]:
    response = client.embeddings.create(
        model=os.getenv("EMBEDDING_MODEL", "text-embedding-3-small"),
        input=texts
    )
    return [r.embedding for r in response.data]


def ingest_products(chroma_client: chromadb.ClientAPI, openai_client: OpenAI, data_dir: str) -> None:
    collection = chroma_client.get_or_create_collection("products")
    existing = collection.count()
    if existing > 0:
        print(f"Products already ingested ({existing} items). Skipping.")
        return

    with open(os.path.join(data_dir, "products.json")) as f:
        products = json.load(f)

    texts = [
        f"{p['name']} - {p['description']} - Category: {p['category']} - "
        f"Nodes: {', '.join(p['nodes_tagged'])}"
        for p in products
    ]

    batch_size = 50
    all_embeddings = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i + batch_size]
        all_embeddings.extend(embed_texts(openai_client, batch))

    collection.add(
        ids=[p["id"] for p in products],
        embeddings=all_embeddings,
        documents=texts,
        metadatas=[{
            "name": p["name"],
            "name_ar": p["name_ar"],
            "price_aed": str(p["price_aed"]),
            "nodes_tagged": json.dumps(p["nodes_tagged"]),
            "urgency_at_nodes": json.dumps(p.get("urgency_at_nodes", {})),
            "category": p["category"],
            "description": p["description"],
            "description_ar": p["description_ar"],
            "safety_certifications": json.dumps(p.get("safety_certifications", [])),
            "compatibility_notes": p.get("compatibility_notes", "")
        } for p in products]
    )
    print(f"Ingested {len(products)} products")


def ingest_content(chroma_client: chromadb.ClientAPI, openai_client: OpenAI, data_dir: str) -> None:
    collection = chroma_client.get_or_create_collection("content")
    existing = collection.count()
    if existing > 0:
        print(f"Content already ingested ({existing} items). Skipping.")
        return

    with open(os.path.join(data_dir, "content.json")) as f:
        articles = json.load(f)

    texts = [f"{a['title']} - {a['body']}" for a in articles]
    all_embeddings = embed_texts(openai_client, texts)

    collection.add(
        ids=[a["id"] for a in articles],
        embeddings=all_embeddings,
        documents=texts,
        metadatas=[{
            "title": a["title"],
            "title_ar": a["title_ar"],
            "nodes_tagged": json.dumps(a["nodes_tagged"]),
            "stage": a["stage"],
            "key_points": json.dumps(a["key_points"])
        } for a in articles]
    )
    print(f"Ingested {len(articles)} articles")


def run_ingest() -> None:
    chroma_persist = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
    data_dir = os.getenv("DATA_DIR", "./data")

    chroma_client = chromadb.PersistentClient(path=chroma_persist)
    openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

    print("Ingesting products...")
    ingest_products(chroma_client, openai_client, data_dir)

    print("Ingesting content...")
    ingest_content(chroma_client, openai_client, data_dir)

    print("Ingest complete.")


if __name__ == "__main__":
    run_ingest()
