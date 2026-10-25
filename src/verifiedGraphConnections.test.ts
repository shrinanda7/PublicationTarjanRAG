import assert from "node:assert/strict";
import test from "node:test";
import type { GraphEdge, GraphTopology } from "./types.ts";
import { buildQuotientGraph } from "./graphEngine.ts";
import { enforceVerifiedGraphConnections, verifiedTraversedRelations } from "./verifiedGraphConnections.ts";

const relation: GraphEdge = {
  source: "p1::A", target: "p1::B", type: "USES",
  provenance: "paper_extraction", validation_status: "validated",
  source_chunk_ids: ["c1"], source_evidence: [{ paper_id: "p1", chunk_id: "c1" }],
};
const source: GraphTopology = {
  nodes: [
    { id: "p1::A", paper_id: "p1", name: "Method A", type: "Method", source_chunk_ids: ["c1"] },
    { id: "p1::B", paper_id: "p1", name: "Dataset B", type: "Dataset", source_chunk_ids: ["c1"] },
  ],
  edges: [relation],
};
const quotientEdge: GraphEdge = {
  source: "scc-a", target: "scc-b", type: "USES", original_relations: [relation],
};

test("renders only validated, provenance-backed relations on traversed quotient edges", () => {
  const result = enforceVerifiedGraphConnections(
    "### Direct Answer\nA result.\n\n### Graph Connections\n\nA model-made claim.\n\n### Key Takeaway\nCheck the paper.",
    [quotientEdge],
    source,
  );
  assert.match(result, /Method A.*USES.*Dataset B/);
  assert.match(result, /p1::c1/);
  assert.doesNotMatch(result, /A model-made claim/);
  assert.match(result, /### Key Takeaway/);
});

test("excludes identity-only, unvalidated, unsupported, and untraversed edges", () => {
  const identityOnly = { ...relation, provenance: "normalized_exact_name_match" as const, validation_status: "identity_match_only" as const };
  const unvalidated = { ...relation, validation_status: "unreviewed" as const };
  const missingChunk = { ...relation, source_evidence: [{ paper_id: "p1", chunk_id: "absent" }] };
  const result = verifiedTraversedRelations([
    { ...quotientEdge, original_relations: [identityOnly, unvalidated, missingChunk] },
  ], source);
  assert.deepEqual(result, []);
  const noTraversal = enforceVerifiedGraphConnections("Answer.", [], source);
  assert.doesNotMatch(noTraversal, /No validated, provenance-backed graph relations were traversed/);
  assert.doesNotMatch(noTraversal, /Graph Connections/);
});

test("quotient edges retain every original relation and its evidence metadata", () => {
  const nodes = [
    { id: "A", name: "A", type: "Method", paper_id: "p1", source_chunk_ids: ["c1"] },
    { id: "B", name: "B", type: "Method", paper_id: "p1", source_chunk_ids: ["c2"] },
    { id: "C", name: "C", type: "Dataset", paper_id: "p1", source_chunk_ids: ["c3"] },
  ];
  const edges: GraphEdge[] = [
    { source: "A", target: "B", type: "USES", provenance: "paper_extraction", validation_status: "validated", source_chunk_ids: ["c1"], source_evidence: [{ paper_id: "p1", chunk_id: "c1" }] },
    { source: "B", target: "A", type: "USES", provenance: "paper_extraction", validation_status: "validated", source_chunk_ids: ["c2"], source_evidence: [{ paper_id: "p1", chunk_id: "c2" }] },
    { source: "A", target: "C", type: "EVALUATED_ON", provenance: "paper_extraction", validation_status: "validated", source_chunk_ids: ["c3"], source_evidence: [{ paper_id: "p1", chunk_id: "c3" }] },
    { source: "B", target: "C", type: "EVALUATED_ON", provenance: "paper_extraction", validation_status: "validated", source_chunk_ids: ["c3"], source_evidence: [{ paper_id: "p1", chunk_id: "c3" }] },
  ];
  const quotient = buildQuotientGraph(nodes, edges);
  const external = quotient.edges.find((edge) => edge.target === "C");
  assert.equal(external?.original_relations?.length, 2);
  assert.deepEqual(external?.original_relations?.map((edge) => edge.source_evidence?.[0].chunk_id), ["c3", "c3"]);
});
