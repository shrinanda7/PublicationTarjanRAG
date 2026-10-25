# Evaluation artifacts

`historical_unvalidated_benchmark.json` is retained only for provenance. It contains pre-fix scores and graph-preservation values that were not reliably measured; **do not cite or use it as evidence** in a paper.

A fresh run of the benchmark endpoint writes `latest_benchmark.json`. Before reporting results, verify that each configuration has successful samples, valid judge scores, and independently computed graph metrics. Failed query attempts and missing judge scores are now represented explicitly rather than silently omitted or assigned fabricated values.

## Frozen gold evaluation

Follow [`ANNOTATION_PROTOCOL.md`](ANNOTATION_PROTOCOL.md) and freeze its version before labeling. `gold_dataset.template.json` is only a starter; it intentionally fails validation. A usable dataset must pass `python scripts/validate_gold_dataset.py PATH_TO_GOLD.json`. Include a frozen paper manifest with SHA-256 values, independently reviewed answerability/answers/evidence/paths, at least two reviewer IDs, and adjudication. For stronger chunk integrity checks, also provide `--chunk-manifest` as a JSON object mapping each paper ID to a mapping of chunk IDs to exact indexed chunk text.

Saved predictions can be scored without an LLM judge:

```powershell
python -m backend.evaluation.score_run PATH_TO_GOLD.json PATH_TO_PREDICTIONS.json --top-k 5 --output scores.json
```

Prediction documents use `{ "run": { ...reproducibility metadata... }, "predictions": [...] }`. Each prediction must contain a unique `question_id`. Optional fields are `answer`, `retrieved_evidence`, `citations`, `retrieved_paths`, `quotient_graph`, and `abstained`. Evidence and citation IDs are `paper_id::chunk_id`; paths are ordered original node-ID arrays. Every gold question must have exactly one prediction. Cross-paper evidence coverage uses the distinct papers represented in the adjudicated gold evidence as its denominator, not every candidate paper. The scorer records a canonical SHA-256 fingerprint of the validated dataset, per-question scores, aggregate scores, category aggregates, and available latency/call/token telemetry. Automated answer metrics do not replace human rubric judgments or claim-level faithfulness annotation.

## Cross-paper graph bridges

Disconnected paper graphs can be connected for traversal only through
human-reviewed, evidence-backed relations. Annotate them using
[`cross_paper_bridges.template.json`](cross_paper_bridges.template.json) and
save the completed file as `cross_paper_bridges.json`. Each directed bridge
must name existing endpoint nodes, include exact quotes from indexed chunks on
both papers, include reviewer IDs, and use `validation_status:
"human_validated"`. The backend checks the quotes and endpoint chunk links
before using the edge. Similarity-only and unreviewed links are not traversed
or presented as verified Graph Connections.

## Retrieval baselines

`backend/evaluation/baseline_retrieval.py` exposes chunk-level `rank_bm25`, `rank_dense`, and `rank_hybrid` functions. BM25 uses `k1=1.2` and `b=0.75`; dense retrieval uses cosine similarity from the configured Ollama embedding model; hybrid retrieval uses equal-weight reciprocal-rank fusion with `rrf_k=60`. Dense and hybrid runs fail explicitly when real embeddings are unavailable and return embedding call/token/latency telemetry.

`backend/evaluation/experiment_runner.py` runs one method per output file for Tarjan-RAG, six one-flag Tarjan ablations, local graph, static/dynamic community, BM25, dense, or hybrid retrieval. All methods use the same final evidence prompt, synthesis model, temperature, and context-budget policy. Local graph performs lexical entity seeding and graph-neighborhood retrieval, then uses shared synthesis. Dense and hybrid require a live, non-mock Ollama embedding service. Example:

```powershell
python -m backend.evaluation.experiment_runner PATH_TO_GOLD.json predictions_tarjan.json --method tarjan
python -m backend.evaluation.experiment_runner PATH_TO_GOLD.json predictions_local.json --method local
python -m backend.evaluation.experiment_runner PATH_TO_GOLD.json predictions_static_community.json --method static_community
python -m backend.evaluation.experiment_runner PATH_TO_GOLD.json predictions_dynamic_community.json --method dynamic_community
python -m backend.evaluation.experiment_runner PATH_TO_GOLD.json predictions_bm25.json --method bm25
python -m backend.evaluation.experiment_runner PATH_TO_GOLD.json predictions_dense.json --method dense
python -m backend.evaluation.experiment_runner PATH_TO_GOLD.json predictions_hybrid.json --method hybrid
python -m backend.evaluation.score_run PATH_TO_GOLD.json predictions_tarjan.json --output scores_tarjan.json
```

The runner records per-question errors/statuses and model, prompt, context, dataset, revision, working-tree state, platform, and retrieval telemetry. For graph methods it saves original and quotient node/edge counts; compression ratios are quotient count divided by original count, while reduction fractions are one minus that ratio. PSR/RCFR uses the complete quotient graph before query-time selection; Gold Path Recall uses bounded original-node paths represented by the selected quotient subgraph. The scorer reports estimated context tokens/utilization and prompt/completion tokens when the backend returns them. The scorer returns diagnostic metrics but marks `valid_for_analysis=false` if any sample has an operational/LLM failure, required metadata is absent, the corpus version differs, or the run came from a dirty working tree. Review every row before interpreting scores. Static community selects all level-1 quotient communities and retrieves linked source chunks. Dynamic community uses the LLM relevance-rating traversal to select communities, with rating summaries formed from member entity names/descriptions rather than generated reports, then retrieves linked source chunks. Both skip legacy map/reduce and use shared synthesis; treat them as explicit matched variants, not exact reproductions of the older answer pipeline. Community selection is applied independently to each paper in a multi-paper item. Token limits use a character-based estimate, so publication runs should replace it with the selected model tokenizer and record exact model/service versions. These tools enable experiments; they do not themselves provide valid results or replace human review.

The `tarjan` reference run pins all six retrieval flags on regardless of local `.env` overrides. Ablations can be run with `--method no_scc`, `no_connector`, `no_budget`, `no_cross_paper_links`, `no_evidence_recovery`, or `no_query_conditioned`; each starts from that pinned reference configuration, disables exactly one flag, records the effective flags and override, then restores the process settings. The no-budget ablation disables traversal pruning only; the shared synthesis hard context limit remains in force to prevent invalid model requests.

## Repeated-run comparisons

After saving and scoring at least two valid repeated runs for each method on the same validated dataset, compare them with paired question-level resampling:

```powershell
python -m backend.evaluation.compare_runs bm25=scores_bm25_seed1.json bm25=scores_bm25_seed2.json tarjan=scores_tarjan_seed1.json tarjan=scores_tarjan_seed2.json --bootstrap-samples 10000 --seed 2026 --output comparison.json
```

The utility checks analysis validity, dataset fingerprints, identical question coverage within each method, matching shared model/prompt/temperature/retrieval/budget/hardware settings, and a common embedding model for dense and hybrid runs. It averages repeated-run values within each question, bootstraps paired question differences within gold categories (preserving category counts), computes an exact sign-flip test for up to 20 questions (Monte Carlo above that), and applies Holm-Bonferroni adjustment across all reported method-pair/metric tests. This is a reproducible analysis aid; choose and preregister the statistical plan and interpret inference with the study design in mind.
