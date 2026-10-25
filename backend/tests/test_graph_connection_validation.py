from backend.search.multi_paper_search import _verified_traversed_relations


def test_quotient_edge_displays_only_reviewed_original_relation_with_available_evidence():
    valid = {
        "source": "p1::A", "target": "p1::B", "type": "USES", "paper_id": "p1",
        "provenance": "llm_extracted", "validation_status": "validated",
        "source_chunk_ids": ["c1"], "source_evidence": [{"paper_id": "p1", "chunk_id": "c1"}],
    }
    unreviewed = {**valid, "source": "p1::B", "target": "p1::A", "validation_status": "unreviewed"}
    identity_only = {**valid, "type": "SAME_ENTITY_NAME", "provenance": "normalized_exact_name_match", "validation_status": "identity_match_only"}
    absent_chunk = {**valid, "source": "p1::B", "target": "p1::A", "source_evidence": [{"paper_id": "p1", "chunk_id": "missing"}]}
    nodes = [
        {"id": "p1::A", "name": "Method A", "paper_id": "p1", "source_chunk_ids": ["c1"]},
        {"id": "p1::B", "name": "Method B", "paper_id": "p1", "source_chunk_ids": ["c1"]},
    ]
    originals = [valid, unreviewed, identity_only, absent_chunk]
    selected = [{"source": "scc-a", "target": "scc-b", "original_relations": [valid, unreviewed, identity_only, absent_chunk]}]

    result = _verified_traversed_relations(selected, nodes, originals)
    assert result == [{"edge": valid, "source_evidence": [{"paper_id": "p1", "chunk_id": "c1"}]}]


def test_relation_not_in_source_graph_or_without_source_evidence_is_rejected():
    relation = {
        "source": "A", "target": "B", "type": "USES", "paper_id": "p1",
        "provenance": "paper_extraction", "validation_status": "validated",
        "source_chunk_ids": ["c1"], "source_evidence": [{"paper_id": "p1", "chunk_id": "c1"}],
    }
    nodes = [
        {"id": "A", "paper_id": "p1", "source_chunk_ids": ["c1"]},
        {"id": "B", "paper_id": "p1", "source_chunk_ids": ["c1"]},
    ]
    quotient = [{"source": "A", "target": "B", "original_relations": [relation]}]
    assert _verified_traversed_relations(quotient, nodes, []) == []
    no_evidence = {**relation, "source_evidence": []}
    assert _verified_traversed_relations(
        [{"source": "A", "target": "B", "original_relations": [no_evidence]}],
        nodes,
        [no_evidence],
    ) == []
