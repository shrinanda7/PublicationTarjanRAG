# Tarjan-RAG evaluation annotation protocol

Status: **protocol draft; no annotations are certified by this document**. Freeze a version of this protocol before annotators label the pilot. Record any later change as a new version and re-review affected items.

## 1. Independence and blinding

- Use two annotators with relevant research-reading experience. They work independently on the same frozen corpus and do not see Tarjan-RAG answers, retrieved passages, graph outputs, or each other's labels.
- Give annotators the original paper PDFs and the frozen extraction/chunk manifest. The manifest must map stable `paper_id` and `chunk_id` values to exact source text and PDF page/section metadata.
- Authors may draft candidate questions, but annotators must independently establish answerability, acceptable answers, supporting passages, and reasoning paths from the papers. Do not use system-generated answers as gold answers.
- A third reviewer adjudicates disagreements without seeing system outputs. Preserve both original annotations and the adjudicated record in the audit trail; the current JSON schema stores reviewer IDs and adjudication state, so detailed disagreements should be retained in a companion CSV/JSONL file.

## 2. Question eligibility and labels

Each item must have a stable unique ID, exact question text, and the minimum paper IDs needed to answer it. Assign exactly one category:

- `single_paper`: answer requires one source paper and no evidence chain across distinct claims.
- `multi_hop_single_paper`: answer requires connecting at least two evidence-bearing steps within one paper.
- `multi_hop_cross_paper`: answer requires evidence from at least two distinct papers; removing any required paper should make the intended synthesis incomplete.

Do not classify a question as multi-hop merely because the response is long or cites multiple passages. Record `required_hops` as the number of directed relation transitions in the adjudicated path; state and freeze this convention with the dataset release. For unanswerable questions, ensure the frozen corpus genuinely lacks the requested evidence. Prefer realistic near-miss questions over nonsensical questions, and record why each is unanswerable.

## 3. Gold answer and evidence annotation

- Write a concise reference answer independently of the system output. Include a list of materially equivalent acceptable answer variants where exact matching is appropriate. Longer synthesis requires a separate predefined human rubric; exact match and token F1 are not sufficient.
- For each required claim, record one or more minimal supporting passages. Each passage must use the actual frozen `paper_id`, `chunk_id`, page/section metadata, and an exact quote copied from that chunk.
- Do not cite a whole paper or a paraphrase as an exact evidence quote. If evidence crosses a chunk boundary, list each source chunk separately.
- Record which evidence passages support which answer claims in the companion annotation file. The base dataset's passage-level citation precision/recall can only approximate claim-level support unless this mapping is supplied.
- For cross-paper items, identify which required claim each paper supports and why one paper alone is insufficient.

## 4. Gold path annotation

- Represent paths as ordered node IDs and directed edges. A path must contain at least one directed transition (two or more nodes), and every edge must match adjacent nodes and have a relation type; add source paper/chunk provenance in the companion annotation file. Questions with zero required hops must have an empty `gold_paths` array.
- Annotators should identify paths from source passages and the frozen graph extraction independently. If an edge is absent from the graph or has no evidence in the paper, do not silently treat it as a valid gold edge; log it as a graph-construction defect and adjudicate whether to repair the graph or exclude/rewrite the item.
- Record alternative valid paths when the literature supports more than one chain. Freeze the accepted path set before evaluating systems.
- For compression evaluation, compare each original directed transition after mapping original nodes to SCC members. A transition within one SCC counts as represented by the component; a transition between SCCs requires the corresponding directed quotient edge. Evidence recovery is a separate check: the original source chunk must still be recoverable.

## 5. Disagreement and quality control

- Adjudicate disagreements on category, answerability, gold answer, evidence span, path direction, hop count, and required-paper set.
- Report pre-adjudication agreement separately for each label type. Use Cohen's kappa for two annotators' categorical labels (category and answerability); report raw agreement and a clearly defined span-overlap/evidence-set agreement for passage labels. Do not collapse these into one reliability number.
- Keep the pilot's 10/10/10 category allocation as a design target. Audit the realized counts after annotation; do not rebalance silently. The main set target is approximately 180, but its category allocation must be preregistered before annotation based on the study question.
- Recheck a random sample of adjudicated items against PDF pages and exact chunk text. Record omissions, OCR errors, ambiguous claims, and exclusions.

## 6. Freeze and release checklist

Before the benchmark is used, publish or archive:

1. Protocol version, corpus manifest, paper citations/access notes, and PDF SHA-256 checksums.
2. Frozen chunk manifest with chunk IDs, source text, page and section mapping, and a hash of the manifest.
3. Question JSON passing `python scripts/validate_gold_dataset.py GOLD.json --chunk-manifest CHUNKS.json`.
4. Independent annotations, disagreement/adjudication log, agreement statistics, exclusions, and final question counts by category and answerability.
5. Versioned system predictions and run metadata (models, prompts, code revision, configuration, seeds, hardware/services, token/cost/latency fields).

The protocol defines the process; it does not establish that the current draft questions, PDFs, extracted chunks, or generated relations meet these conditions.
# Cross-paper graph bridges

The query-time graph may traverse semantic cross-paper relations only when
they appear in `cross_paper_bridges.json` with `validation_status` set to
`human_validated`. The example file `cross_paper_bridges.template.json` shows
the required fields. The active file is optional; when absent, no semantic
cross-paper bridge is added.

For each bridge, annotate the directed source and target graph node IDs, the
relation type, and at least one exact indexed chunk quote from each paper.
Quotes must be copied from the exact indexed chunk. Both endpoint nodes must
reference their corresponding evidence chunks. Record reviewer IDs and only
mark a bridge human validated after checking that the direction and relation
are supported by the quoted passages. Similarity, shared topics, or paper
relatedness alone is not sufficient evidence for a traversable relation.

The backend rejects a bridge if its papers or node IDs are not in the current
query, if its quote does not match an indexed chunk, if a quote is not linked
to the endpoint node, or if the record lacks human validation. Rejected bridge
IDs and malformed-file errors are recorded in the retrieval trace.

