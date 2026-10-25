import assert from "node:assert/strict";
import test from "node:test";
import { attachSourceChunkEvidence, buildCrossPaperBridges, mergeNamespacedPaperGraphs } from "./crossPaperGraph.ts";
import type { GraphNode } from "./types.ts";

const node = (
  id: string,
  paper_id: string,
  name: string,
  source_chunk_ids: string[] = ["chunk-1"]
): GraphNode => ({ id, paper_id, name, type: "Concept", source_chunk_ids });

test("cross-paper links require exact names and evidence chunks on both nodes", () => {
  const nodes = [
    node("a1", "paper-a", "Transformer", ["paper-a:chunk-1"]),
    node("b1", "paper-b", "Transformer", ["paper-b:chunk-1"]),
    node("b2", "paper-b", "Transformer architecture"),
    node("c1", "paper-c", "Transformer", []),
  ];

  const links = buildCrossPaperBridges(nodes);

  assert.equal(links.length, 2);
  assert.deepEqual(
    links.map(({ source, target, type }) => ({ source, target, type })),
    [
      { source: "a1", target: "b1", type: "ENTITY_IDENTITY_MATCH" },
      { source: "b1", target: "a1", type: "ENTITY_IDENTITY_MATCH" },
    ]
  );
  assert.ok(links.every((edge) => edge.validation_status === "identity_match_only"));
  assert.ok(links.every((edge) => edge.source_chunk_ids?.length === 2));
  assert.ok(links.every((edge) => !edge.is_bridge));
});

test("generic names and unsupported nodes do not create cross-paper edges", () => {
  const links = buildCrossPaperBridges([
    node("a1", "paper-a", "Model"),
    node("b1", "paper-b", "Model"),
    node("a2", "paper-a", "GraphSAGE", []),
    node("b2", "paper-b", "GraphSAGE", []),
  ]);

  assert.deepEqual(links, []);
});

test("multi-paper merge grounds extracted entities in PDF chunks before linking them", () => {
  const first = attachSourceChunkEvidence("paper-a", {
    nodes: [node("a1", "paper-a", "Diabetic Retinopathy", [])], edges: [],
  }, ["We evaluate a model for diabetic retinopathy screening."]);
  const second = attachSourceChunkEvidence("paper-b", {
    nodes: [node("b1", "paper-b", "Diabetic Retinopathy", [])], edges: [],
  }, ["Diabetic retinopathy is classified from retinal fundus images."]);

  const merged = mergeNamespacedPaperGraphs([
    { paperId: "paper-a", graph: first },
    { paperId: "paper-b", graph: second },
  ]);
  const links = merged.original_graph.edges.filter((edge) => edge.type === "ENTITY_IDENTITY_MATCH");

  assert.equal(links.length, 2);
  assert.ok(links.every((edge) => edge.source_evidence?.length === 2));
  assert.ok(first.nodes[0].source_chunk_ids?.[0].includes("visual_chunk_0001"));
});
