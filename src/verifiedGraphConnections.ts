import type { GraphEdge, GraphTopology } from "./types";

type SourceEvidence = { paper_id: string; chunk_id: string };

function evidenceKey(evidence: SourceEvidence): string {
  return `${evidence.paper_id}::${evidence.chunk_id}`;
}

/**
 * Render only human-validated paper-extraction relations that survived into
 * the traversed quotient edge and whose source chunks exist in the source graph.
 * Exact-name identity candidates are deliberately excluded.
 */
export function verifiedTraversedRelations(
  traversedEdges: GraphEdge[],
  originalGraph: GraphTopology
): Array<{ edge: GraphEdge; evidence: SourceEvidence[] }> {
  const sourceNodes = new Map((originalGraph.nodes || []).map((node) => [node.id, node]));
  const knownChunks = new Set<string>();
  for (const node of originalGraph.nodes || []) {
    const namespaceIndex = node.id.indexOf("::");
    const paperId = node.paper_id || (namespaceIndex > 0 ? node.id.slice(0, namespaceIndex) : "");
    if (!paperId) continue;
    for (const chunkId of node.source_chunk_ids || []) {
      knownChunks.add(`${paperId}::${chunkId}`);
    }
  }
  const originalEdges = new Set((originalGraph.edges || []).map((edge) =>
    `${edge.source}\u0000${edge.target}\u0000${edge.type}`
  ));
  const seen = new Set<string>();
  const verified: Array<{ edge: GraphEdge; evidence: SourceEvidence[] }> = [];

  for (const traversed of traversedEdges) {
    for (const relation of traversed.original_relations || []) {
      const key = `${relation.source}\u0000${relation.target}\u0000${relation.type}`;
      if (seen.has(key) || !originalEdges.has(key)) continue;
      if (!(["paper_extraction", "human_validated_bridge"].includes(relation.provenance || "")) || relation.validation_status !== "validated") continue;
      if (!sourceNodes.has(relation.source) || !sourceNodes.has(relation.target)) continue;
      const evidence = relation.source_evidence as SourceEvidence[] | undefined;
      if (!Array.isArray(evidence) || evidence.length === 0) continue;
      const sourceChunkIds = new Set(relation.source_chunk_ids || []);
      if (evidence.some((item) =>
        !item || typeof item.paper_id !== "string" || typeof item.chunk_id !== "string" ||
        !sourceChunkIds.has(item.chunk_id) || !knownChunks.has(evidenceKey(item))
      )) continue;
      seen.add(key);
      verified.push({ edge: relation, evidence });
    }
  }
  return verified;
}

/** Replace any model-written Graph Connections section with verified trace data. */
export function enforceVerifiedGraphConnections(
  answer: string,
  traversedEdges: GraphEdge[],
  originalGraph: GraphTopology
): string {
  const withoutModelSection = answer
    .replace(/(?:^|\n)#{1,4}\s*[^\n]*\bGraph Connections\b[^\n]*[\s\S]*?(?=\n#{1,4}\s|$)/i, "\n")
    .trim();
  const nodeNames = new Map((originalGraph.nodes || []).map((node) => [node.id, node.name || node.id]));
  const relations = verifiedTraversedRelations(traversedEdges, originalGraph);
  if (!relations.length) return withoutModelSection;
  const body = relations.map(({ edge, evidence }) =>
    `- **${nodeNames.get(edge.source) || edge.source}** —${edge.type}→ **${nodeNames.get(edge.target) || edge.target}** (${evidence.map(evidenceKey).join(", ")})`
  ).join("\n");
  return `${withoutModelSection}\n\n**Verified graph links**\n${body}`.trim();
}
