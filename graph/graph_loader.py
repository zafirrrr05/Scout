import json
import os
import networkx as nx
from api.models import HorizonItem, SituationProfile


def load_graph(path: str) -> nx.DiGraph:
    with open(path) as f:
        data = json.load(f)
    G = nx.DiGraph()
    for node in data["nodes"]:
        G.add_node(node["id"], **node)
    for edge in data["edges"]:
        G.add_edge(edge["from"], edge["to"], **edge)
    return G


def validate_graph(G: nx.DiGraph) -> bool:
    for u, v in G.edges():
        if u not in G.nodes() or v not in G.nodes():
            raise ValueError(f"Edge references missing node: {u} -> {v}")
    print(f"Graph valid: {len(G.nodes())} nodes, {len(G.edges())} edges")
    return True


def _evaluate_condition(condition: str, profile: SituationProfile) -> bool:
    if not condition:
        return True
    try:
        parts = condition.split(" ")
        if len(parts) != 3:
            return True
        field, op, value = parts
        profile_val = getattr(profile, field, None)
        if op == "==":
            return str(profile_val).lower() == value.lower()
        return True
    except Exception:
        return True


def traverse_forward(
    profile: SituationProfile,
    G: nx.DiGraph,
    max_nodes: int = 5,
    max_weeks: int = 12,
) -> list[HorizonItem]:
    if profile.current_node_id not in G.nodes():
        return []

    horizon: list[HorizonItem] = []
    visited: set[str] = {profile.current_node_id}
    frontier: list[tuple[str, int]] = [(profile.current_node_id, 0)]

    while frontier and len(horizon) < max_nodes:
        current_id, cumulative_weeks = frontier.pop(0)

        for _, neighbor, edge_data in G.out_edges(current_id, data=True):
            if neighbor in visited:
                continue

            weeks_until = cumulative_weeks + edge_data.get("weeks_until", 0)
            if weeks_until > max_weeks:
                continue

            edge_type = edge_data.get("type", "might_happen")
            if edge_type == "contextual":
                condition = edge_data.get("condition", "")
                if not _evaluate_condition(condition, profile):
                    continue

            node_data = G.nodes[neighbor]
            certainty = edge_type if edge_type in ["will_happen", "likely_happens", "might_happen"] else "might_happen"

            horizon.append(
                HorizonItem(
                    node_id=neighbor,
                    situation=node_data.get("label", neighbor),
                    situation_ar=node_data.get("label_ar", ""),
                    weeks_until=weeks_until,
                    certainty=certainty,
                    preview=node_data.get("preview", ""),
                    preview_ar=node_data.get("preview_ar", ""),
                )
            )
            visited.add(neighbor)
            frontier.append((neighbor, weeks_until))

    return sorted(horizon, key=lambda x: x.weeks_until)


def get_unknown_unknowns(
    profile: SituationProfile,
    horizon: list[HorizonItem],
    G: nx.DiGraph,
) -> list[str]:
    all_unknowns: list[str] = []

    current_data = G.nodes.get(profile.current_node_id, {})
    all_unknowns.extend(current_data.get("unknown_unknowns", []))

    for item in horizon:
        node_data = G.nodes.get(item.node_id, {})
        all_unknowns.extend(node_data.get("unknown_unknowns", []))

    return list(dict.fromkeys(all_unknowns))


def get_node_ids(G: nx.DiGraph) -> list[str]:
    return [n for n in G.nodes() if n != "unknown"]


_graph_instance: nx.DiGraph | None = None


def get_graph() -> nx.DiGraph:
    global _graph_instance
    if _graph_instance is None:
        graph_path = os.getenv("GRAPH_PATH", "./graph/parenting_graph.json")
        _graph_instance = load_graph(graph_path)
        validate_graph(_graph_instance)
    return _graph_instance
