"""
Neo4j adapter — syncs an extracted knowledge graph to a Neo4j instance.

Enabled via ENABLE_NEO4J=true in .env.
The adapter pattern here makes it straightforward to add other graph databases
(e.g. Amazon Neptune, ArangoDB) by implementing the same sync_graph() interface.
"""

import os
from typing import Any


def _get_driver():
    from neo4j import GraphDatabase  # type: ignore

    uri = os.environ.get("NEO4J_URI", "bolt://localhost:7687")
    user = os.environ.get("NEO4J_USER", "neo4j")
    password = os.environ.get("NEO4J_PASSWORD", "password")
    # 10-second connection timeout so we never block the HTTP response
    return GraphDatabase.driver(
        uri,
        auth=(user, password),
        connection_timeout=10,
        max_transaction_retry_time=5,
    )


def _upsert_node(tx, node: dict[str, Any]) -> None:
    query = """
    MERGE (n {id: $id})
    SET n.label       = $label,
        n.type        = $type,
        n.description = $description,
        n.source_text = $source_text,
        n:`{type}`
    """.replace(
        "{type}", node["type"]
    )
    tx.run(
        query,
        id=node["id"],
        label=node["label"],
        type=node["type"],
        description=node.get("description", ""),
        source_text=node.get("source_text", ""),
    )


def _upsert_edge(tx, edge: dict[str, Any]) -> None:
    rel_type = edge["label"].upper().replace(" ", "_").replace("-", "_")
    query = f"""
    MATCH (a {{id: $source}}), (b {{id: $target}})
    MERGE (a)-[r:{rel_type} {{id: $id}}]->(b)
    SET r.description = $description,
        r.source_text = $source_text
    """
    tx.run(
        query,
        id=edge["id"],
        source=edge["source"],
        target=edge["target"],
        description=edge.get("description", ""),
        source_text=edge.get("source_text", ""),
    )


def sync_graph(graph: dict) -> dict:
    """Sync nodes and edges to Neo4j. Returns a summary dict."""
    driver = _get_driver()
    nodes_written = 0
    edges_written = 0

    with driver.session() as session:
        for node in graph.get("nodes", []):
            session.execute_write(_upsert_node, node)
            nodes_written += 1
        for edge in graph.get("edges", []):
            try:
                session.execute_write(_upsert_edge, edge)
                edges_written += 1
            except Exception:
                # Skip edges whose endpoints weren't created
                pass

    driver.close()
    return {"nodes_written": nodes_written, "edges_written": edges_written}
