from backend.search.cross_paper_bridges import build_validated_bridge_edges


def test_bridge_requires_human_review_linked_endpoint_chunks_and_exact_quotes():
    nodes = {
        "paper_a::a1": {"source_chunk_ids": ["a_chunk"]},
        "paper_b::b1": {"source_chunk_ids": ["b_chunk"]},
    }
    records = [{
        "bridge_id": "valid",
        "source_paper_id": "paper_a",
        "source_node_id": "a1",
        "target_paper_id": "paper_b",
        "target_node_id": "b1",
        "relation_type": "EXTENDS",
        "evidence": [
            {"paper_id": "paper_a", "chunk_id": "a_chunk", "quote": "Paper A proposes a retrieval graph."},
            {"paper_id": "paper_b", "chunk_id": "b_chunk", "quote": "Paper B extends the retrieval graph."},
        ],
        "reviewer_ids": ["r1", "r2"],
        "validation_status": "human_validated",
    }, {
        "bridge_id": "unreviewed",
        "source_paper_id": "paper_a",
        "source_node_id": "a1",
        "target_paper_id": "paper_b",
        "target_node_id": "b1",
        "relation_type": "RELATED_TO",
        "evidence": [
            {"paper_id": "paper_a", "chunk_id": "a_chunk", "quote": "Paper A proposes a retrieval graph."},
            {"paper_id": "paper_b", "chunk_id": "b_chunk", "quote": "Made up sentence."},
        ],
        "reviewer_ids": [],
        "validation_status": "candidate",
    }]

    edges, rejected = build_validated_bridge_edges(
        records,
        paper_ids=["paper_a", "paper_b"],
        node_ids_by_paper={"paper_a": {"a1": "paper_a::a1"}, "paper_b": {"b1": "paper_b::b1"}},
        nodes_by_namespaced_id=nodes,
        chunks_by_paper={
            "paper_a": [{"chunk_id": "a_chunk", "content": "Paper A proposes a retrieval graph."}],
            "paper_b": [{"chunk_id": "b_chunk", "content": "Paper B extends the retrieval graph."}],
        },
    )

    assert len(edges) == 1
    assert edges[0]["source"] == "paper_a::a1"
    assert edges[0]["target"] == "paper_b::b1"
    assert edges[0]["provenance"] == "human_validated_bridge"
    assert edges[0]["validation_status"] == "validated"
    assert rejected == ["unreviewed"]
