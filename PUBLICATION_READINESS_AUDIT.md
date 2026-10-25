# Tarjan-RAG publication readiness audit

Audit date: 2026-10-19  
Scope: repository state and the accompanying master completion checklist. `DONE` means the capability is present in code and its stated scope is supported by evidence; it does not imply a journal-ready experiment. `PARTIAL` means code exists but validation, completeness, or evidence is missing. `MISSING` means no implementation/artifact was found. `PLANNED` means it is an intended experiment or deliverable, not a completed result.

## Overall assessment

**Not ready for a research journal submission.** The repository is a prototype with useful graph algorithms, a retrieval pipeline, a UI, and regression tests. It lacks a frozen, independently annotated dataset and fresh comparative experimental results. The latest benchmark artifact contains null judge scores, zero reported tokens/calls, and missing graph-preservation metrics; the historical artifact is explicitly marked unvalidated in `data/evaluation/README.md`.

The most defensible near-term publication path is a systems/method paper after the graph method is specified precisely and evaluated. Tarjan SCC computation itself is established prior work; novelty must be demonstrated in the evidence-preserving compression and query-specific retrieval method, not asserted from using Tarjan.

## 1. Research method and graph integrity

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| SCC computation | PARTIAL | `backend/core/tarjan.py` implements iterative SCC and undirected bridge/articulation algorithms. `backend/tests/test_stage3_tarjan.py` compares algorithm outputs with NetworkX, but the proof scope is graph correctness, not retrieval benefit or publication validation. |
| Quotient graph and member mapping | PARTIAL | `backend/core/compression.py` builds SCC quotient nodes and preserves member IDs/chunk references. Need broader property-based coverage and independent path-survival evaluation on annotated paths. |
| Edge provenance | PARTIAL | Python and TypeScript extraction distinguish extraction provenance from human validation; Python and TypeScript quotient edges now retain original relations. `src/verifiedGraphConnections.ts` and `backend/search/multi_paper_search.py` require a validated original edge plus source chunks present in the graph. No relations are currently human-validated in a released benchmark. |
| Cross-paper relation generation | PARTIAL | Both backends generate only normalized exact-name identity candidates, marked `identity_match_only`; these are not semantic links and are excluded from verified connections. Homonym error rate still needs measurement on annotated papers. |
| Graph Connections output | PARTIAL | The Express route buffers generation and replaces any model-written Graph Connections heading with deterministic output from validated original relations on selected/traversed quotient edges; it excludes identity-only, unreviewed, unsupported, or absent-chunk edges. The Python multi-paper route applies the same policy. Tests cover these rejection cases and quotient provenance retention. No positive human-validated graph edge/path has yet been tested against a real corpus. |
| Connector preservation | PARTIAL | Bridge-aware quotient selection exists in `backend/search/quotient_traversal.py`. It preserves adjacent connector components in a defined case; empirical connector precision/recall and path survival have not been measured. |
| Context-budget-aware retrieval | PARTIAL | Quotient selection bounds node/path counts. Python single-paper synthesis token-checks the assembled prompt; multi-paper retrieval now budgets formatted evidence blocks against both a character cap and `MAX_TOKEN_BUDGET`, with explicit estimates/utilization in trace and a no-call overflow state. The estimator is character-based, not the model tokenizer; quality-at-budget experiments remain absent. |
| Query-specific traversal trace | PARTIAL | Python trace records seeds, selected quotient nodes/edges, evidence chunks, fallback mode, and budgets; edge steps now carry relation validation states and are labeled selected rather than traversed. Express trace follows outgoing edges from matched nodes; unvalidated edge narration is excluded from the answer prompt. End-to-end trace completeness still needs corpus-backed audit. |
| Evidence recovery | PARTIAL | Python search maps quotient members to original chunk IDs and returns paper/page/section metadata. The Python graph-inspection endpoint now returns an explicit empty `no_indexed_graph` response instead of inventing and persisting a starter topology; a regression test asserts it performs no graph write. Need tests for every compression shape and a manual citation audit against PDF pages. |
| Giant-SCC mitigation | MISSING | `backend/core/compression.py` now labels giant-SCC detection as warning-only; no automatic edge pruning is implemented. A mitigation policy must be specified, implemented, and evaluated before claiming mitigation. |
| Novelty / related work | MISSING | No manuscript or related-work analysis was found. A literature comparison and precise contribution statement are required. |

## 2. Dataset and annotation

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| Fixed corpus of about 20 papers | MISSING | No frozen corpus manifest with version/checksums and licensing/availability notes was found. Current local PDFs and application catalog are not a documented evaluation corpus. |
| 30-question pilot with 10/10/10 allocation | MISSING | `backend/evaluation/question_generator.py` contains a draft set of 50 questions, but no validated 30-item pilot manifest or allocation audit. |
| About 180 main questions | PLANNED | The attached checklist sets this target. No main-set annotation artifact was found. |
| Gold answers, evidence chunks, paths, answerability | MISSING | Existing questions contain short `ground_truth_hint` strings; there are no independently established answer texts, gold chunk IDs, gold paths, or unanswerable labels. |
| Annotation review and disagreement resolution | PARTIAL | `data/evaluation/ANNOTATION_PROTOCOL.md` now specifies blinded independent annotation, evidence/path rules, adjudication, and agreement reporting. No annotators, labels, agreement statistics, or adjudication records exist yet. |
| PDF ingestion and metadata validation | PARTIAL | PDF ingestion code exists, but no frozen-corpus ingestion report or end-to-end audit is available. |

Do not derive gold answers from Tarjan-RAG outputs. Confirm candidate paper rights and corpus availability before freezing a shareable dataset.

## 3. Metrics and evaluation protocol

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| Fresh per-question experiment records | MISSING | `data/evaluation/latest_benchmark.json` is not a usable run: judge scores and graph-preservation values are null, with zero tokens/calls. |
| Answer correctness / rubric | PARTIAL | `backend/evaluation/benchmark_runner.py` has an LLM judge prompt, but no validated rubric, human scores, inter-rater results, or usable run. |
| Evidence Recall/Precision@K, MRR, Hit@K | PARTIAL | `backend/evaluation/metrics.py` implements these, and `backend/evaluation/score_run.py` applies them to aligned saved runs; no gold dataset exists to produce research results. |
| Gold Path Recall, PSR, RCFR | PARTIAL | Saved-run scorer computes exact path recall and quotient path survival (PSR/RCFR). The experiment runner exports bounded original-node paths represented in the selected quotient subgraph and preserves the full quotient edge set separately, so PSR/RCFR measures compression before query-time selection. The gold validator/schema reject zero-transition paths and require empty path sets at zero hops. No validated gold paths or measured results exist. |
| Compression and context efficiency | PARTIAL | `experiment_runner.py` exports original/quotient node and edge counts plus ratio/reduction fractions; `score_run.py` aggregates these and estimated context utilization. The convention is documented in `data/evaluation/README.md`. There are no verified aggregate results, exact tokenizer counts, or quality-versus-budget study. |
| Latency and cost | PARTIAL | `experiment_runner.py` captures per-question end-to-end, retrieval, and synthesis latency plus available answer, retrieval, and embedding call/token counts, including prompt/completion counts where returned; `score_run.py` aggregates them. There are no live measurements, and provider dollar cost or exact remote service/model versions are not recorded. |
| Citation precision/recall and abstention | PARTIAL | Citation-set and abstention metrics are implemented; no claim-level annotations or unanswerable gold set exists. |
| Failure accounting | PARTIAL | Experiment export preserves per-question operational errors/statuses. The deterministic scorer now emits `valid_for_analysis` and lists operational failures or missing/mismatched reproducibility metadata, including dirty working trees. Needs validation on a complete live run and explicit model/service-version capture. |
| Repeated runs, uncertainty, significance | PARTIAL | `backend/evaluation/compare_runs.py` requires multiple valid runs per method with distinct seeds/run IDs, matching dataset fingerprints and shared model/prompt/temperature/retrieval/budget/hardware settings; it also requires the dense and hybrid baselines to use the same embedding model. It bootstraps paired differences within gold categories, reports paired sign-flip p-values, and applies Holm-Bonferroni adjustment. No repeated experiment outputs exist; preregistration and study-specific analysis decisions remain. |

## 4. Baselines and ablations

The application query router now constructs hierarchical community reports only for the explicit static/dynamic baseline modes. Tarjan-RAG and local graph retrieval skip that report-generation path and operate directly on the compressed or source graph, consistent with the master checklist's architecture distinction.

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| Dense vector RAG baseline | PARTIAL | `backend/evaluation/baseline_retrieval.py::rank_dense` performs chunk-level cosine ranking with the configured Ollama embedding model and records embedding calls/tokens/latency. `experiment_runner.py` applies matched synthesis; live embeddings and measured runs are still required. |
| BM25 / sparse RAG baseline | PARTIAL | `rank_bm25` implements documented BM25 (k1=1.2, b=0.75) with deterministic ranking; `experiment_runner.py` applies matched synthesis. No corpus-backed run exists. |
| Hybrid RAG baseline | PARTIAL | `rank_hybrid` fuses BM25 and dense rankings using equal-weight reciprocal-rank fusion (k=60); `experiment_runner.py` applies matched synthesis. Live embeddings and measured runs are still required. |
| Local graph search baseline | PARTIAL | `backend/search/local_search.py` has deterministic lexical entity seeding, k-hop neighborhood expansion, original chunk recovery, explicit unreviewed relation labels, and a retrieval-only path. The matched runner sends its retrieved chunks through shared synthesis and budgeting; focused source-recovery/retrieval-only tests pass. No corpus-backed comparative run exists. |
| Static/dynamic community baselines | PARTIAL | Matched runner adapters select source chunks from all Level-1 quotient communities (static) or LLM-rated relevant communities (dynamic), then use shared synthesis and context budgeting. Dynamic ratings use joined entity names/descriptions rather than generated community reports and record rating calls/tokens/statuses; tests cover chunk recovery and export. These adapters intentionally omit legacy report map/reduce, so they are explicit matched variants rather than exact reproductions of the legacy answer pipeline. No corpus-backed run or effectiveness result exists. |
| No-SCC ablation | PARTIAL | `experiment_runner.py --method no_scc` starts from all six reference retrieval flags enabled, disables only `ENABLE_TARJAN_COMPRESSION`, records effective flags, then restores process settings; parameterized runner tests verify each transition/restoration. No frozen-data run exists. |
| No-connector ablation | PARTIAL | `--method no_connector` disables only bridge-aware pruning from the pinned reference configuration; regression covers flag isolation/restoration. No frozen-data run exists. |
| No-budget ablation | PARTIAL | `--method no_budget` disables quotient traversal budget pruning from the pinned reference configuration while retaining the shared hard synthesis context cap; regression covers flag isolation/restoration. No frozen-data run exists. |
| No-cross-paper-links ablation | PARTIAL | `--method no_cross_paper_links` disables exact-name identity links; regression covers flag isolation/restoration. No frozen-data run exists. |
| No-evidence-recovery ablation | PARTIAL | `--method no_evidence_recovery` disables graph-linked chunk recovery; regression covers flag isolation/restoration. No frozen-data run exists. |
| No-query-conditioned traversal ablation | PARTIAL | `--method no_query_conditioned` uses stable graph-order seeding; regression covers flag isolation/restoration. No frozen-data run exists. |
| Shared matched evaluation harness | PARTIAL | `backend/evaluation/experiment_runner.py` exports validated-gold runs for Tarjan-RAG, six one-flag ablations, local graph, static/dynamic community, BM25, dense, or hybrid using shared synthesis/context policy; `score_run.py` enforces exact question alignment and reports validity plus metrics. No actual experiment outputs exist. |

## 5. Application features (separate from research evidence)

| Feature | Status | Evidence / remaining work |
|---|---|---|
| Create new chat | PARTIAL | `ChatPanel.tsx` exposes a new-chat action and local session list; state is browser-local. |
| Persistent conversation history | PARTIAL | Question/answer turns are saved in `localStorage`, which survives reloads in the same browser profile, but has no server/account backup and silently tolerates quota/write failures. |
| Rename and delete sessions | DONE (local scope) | Session list supports both actions and persists them in `localStorage`; no cross-device sync. |
| Session isolation | PARTIAL | Each saved turn records its paper IDs and retrieval mode; session state is local and no server-side session boundary exists. |
| Resume a previous session | PARTIAL | Selecting a session restores transcript, latest answer/metrics/citations/trace, retrieval mode, and paper selection. It does not restore a complete graph snapshot. |
| Conversation context control | PARTIAL | `ChatPanel.tsx` has an opt-in control that sends at most four prior turns capped at 2,000 characters. Backend synthesis prompts cap this context at 4,000 characters, label it as reference rather than evidence, preserve the current question as the retrieval query, and include it in prompt-budget estimates. It remains a single-browser feature, and multi-provider context tokenization is approximate. |
| Clear session versus clear research data | PARTIAL | New chat clears the active view and deleting a session only removes chat history; paper deletion is a separate action, but the UI does not explain this distinction or provide a clear-data confirmation flow. |
| Document library | PARTIAL | Paper catalog, upload, and delete controls exist in `server.ts` and `PaperSidebar.tsx`; the React and Python ingestion stores remain separate. |
| Duplicate detection | PARTIAL | Express upload checks duplicate content hashes and names; parity with Python ingestion and race-safe concurrent upload handling are not verified. |
| Re-ingestion and deletion consistency | MISSING | No verified atomic rebuild/cleanup across chunks, embeddings, graph records, and indexes; app-side catalog and Python research index can diverge. |
| Per-session document selection | PARTIAL | Each turn stores selected paper IDs and resuming restores the latest scope; isolation is client-local and stale IDs are filtered. |
| Ingestion status and progress | PARTIAL | `ingestion_manager.py` reports extraction/chunking/entity/persistence stages and failures; consistent progress display across the frontend upload paths is not verified. |
| Evidence citations | PARTIAL | Python research endpoint returns source IDs, pages, and sections; local legacy routes have weaker metadata. Manual source audit is outstanding. |
| Graph Connections panel | PARTIAL | Backend output is deterministic and provenance-gated for supported paths; UI presents it inside answer text rather than a separately validated interactive panel. |
| Retrieval trace | PARTIAL | Backend emits selection, traversal, evidence, and fallback trace data; UI renders parts of the trace, but complete parity across all modes is unverified. |
| Fallback transparency | PARTIAL | Backend marks fallback modes; UI does not clearly distinguish all graph, lexical, dense, and evidence-insufficient outcomes. |
| Answerability handling | PARTIAL | Backend can report no evidence and avoids generation in several missing-data cases; calibrated abstention behavior has not been tested on unanswerable questions. |
| Loading, empty, and error states | PARTIAL | Basic query loading/errors and empty states exist; behavior across ingestion, network, and index failures is not covered end-to-end. |
| Retry and cancellation | PARTIAL | Request timeouts/disconnect handling exist in routes, but the UI has no verified safe retry/cancel lifecycle across query and ingestion tasks. |
| Configuration visibility | PARTIAL | Some retrieval settings and traces are exposed, but active model/service versions and effective budget/configuration are not consistently visible in the application. |
| Session/document consistency | MISSING | Deleting or re-ingesting documents has not been verified to invalidate all stale session, graph, cache, embedding, and retrieval references. |
| Basic security | PARTIAL | Upload validation and some route restrictions exist; the app has no user authentication or multi-user data isolation and should remain trusted/local. |

## 6. Engineering and reproducibility

| Requirement | Status | Evidence / remaining work |
|---|---|---|
| Python regression tests | PARTIAL | Latest consolidated deterministic graph/evaluation group passed (56), covering opt-in bounded conversation context, query-router core-mode dispatch, verified graph connections, SCC/quotient behavior, runner/scorer/comparison, baselines, multi-paper retrieval, and ablations. `python -m compileall -q backend` and `git diff --check` also pass. The full `backend/tests` run is not green: `test_pdf_extraction_and_chunking` fails because `data/papers/1609.02907_GCN.pdf` is absent, and `test_hierarchical_clustering_and_reports` stalled while invoking the external report-generation service; a subsequent broad run also stalled in live search/API tests. The all-chunk ingestion regression passes after fixing silent four-chunk truncation; focused search/ingestion checks previously passed 15 with the unavailable PDF fixture excluded. |
| TypeScript lint/build | PARTIAL | `npm run lint`, `npm run build`, `git diff --check`, and five node tests for exact identity links, validation filtering, and quotient provenance pass. Vite reports the existing `__dirname` native-config warning and a 950.91 kB client bundle warning; neither fails the build. |
| Live Neo4j/LLM/browser integration | MISSING | No evidence of current live integration validation. |
| Clean reproducible setup | PARTIAL | Requirements and lockfile exist. Pin Python dependencies and record Neo4j/LLM/model versions, prompts, hardware, seeds, and dataset hashes for experiments. |
| Publication artifact / manuscript | MISSING | No manuscript, tables with valid results, or supplementary materials found. |

## Changes made during this audit

- Removed hard-coded and fuzzy semantic cross-paper edges from `src/crossPaperGraph.ts`. Frontend identity links now require exact normalized names and source chunk IDs in both papers, and carry explicit provenance/validation fields.
- Removed heuristic entity-co-occurrence relations and fabricated feedback cycles from the TypeScript fallback extractor; Python extraction now stores LLM-produced relations as unreviewed with paper-scoped chunk evidence, and exact-name cross-paper links are identified as identity matches only.
- Changed the Express `/api/query/multi-paper` route to call the Python evidence-backed research endpoint. The frontend now surfaces backend/indexing errors instead of falling back to a local demo graph, and the obsolete local multi-paper answer path was removed.
- Removed metadata-as-evidence fallback text and restricted frontend “Graph Connections” to validated, evidence-backed traversed edges. Generated local traces now follow edges that exist in the selected quotient graph.
- Preserved original relation objects and evidence through TypeScript quotient compression. Both multi-paper APIs now emit Graph Connections deterministically from reviewed original edges whose chunk provenance exists in the source graph; exact-name identity candidates are labeled identity-only and never presented as semantic relations. Model-written Graph Connections sections are removed before the Express final answer is streamed and before Python appends its deterministic section.
- Added an estimated token budget to Python multi-paper retrieval alongside the character ceiling. Chunk labels, metadata, prompt instructions, and an allowance for system/message framing are counted before each evidence block is accepted; an oversized evidence prompt never calls the model and reports the budget failure in the trace.
- Removed the Python graph-inspection endpoint's fabricated starter graph for unindexed papers. It now reports `no_indexed_graph` with empty topology and does not persist synthetic entities, avoiding demo structure being mistaken for extracted evidence.
- Added deterministic chunk-level BM25, dense-cosine, and equal-weight RRF retrieval rankers with embedding telemetry. Corrected Local Search: it is now explicitly a lexical graph-neighborhood baseline, reads source chunks through the store API, ranks evidence rather than taking the first five chunks, and avoids making an unused embedding call.
- Updated the README to describe a prototype and document that evidence-backed queries require the research backend; clarified that community retrieval is a baseline/legacy mode, not the core Tarjan-RAG method.

These changes improve integrity; they do not constitute experimental validation or make the project publication-ready by themselves.

Additional evaluation groundwork: `backend/evaluation/metrics.py` implements normalized exact match, token F1, evidence precision/recall/MRR/hit, directed path survival (PSR/RCFR), exact path recall, citation precision/recall, abstention accuracy, and run latency/call/token aggregates. `backend/evaluation/gold_dataset.py`, `data/evaluation/gold_dataset.schema.json`, and `scripts/validate_gold_dataset.py` define a strict validated-annotation contract with corpus checksums, reviewer/adjudication fields, unique paper scopes, consistent hop/path lengths, and optional frozen-chunk/quote verification. `data/evaluation/ANNOTATION_PROTOCOL.md` specifies the blinded double-annotation and adjudication procedure. A blank template is provided; it is deliberately not a usable benchmark. Backend config exposes cross-paper-link, evidence-recovery, and query-conditioned-traversal ablations, with deterministic traversal tests. No scores are reported because there is no valid gold dataset.

Added deterministic saved-run scoring at `backend/evaluation/score_run.py`; it rejects missing, duplicate, or unexpected question IDs, fingerprints the validated dataset, emits per-question/aggregate/category and operational telemetry, and reports whether execution and metadata satisfy the current analysis-validity gate. `backend/evaluation/compare_runs.py` provides category-stratified paired bootstrap intervals and paired sign-flip tests with Holm adjustment. Added `backend/search/evidence_synthesis.py` so Tarjan-RAG, local graph, matched static/dynamic community variants, and BM25/dense/hybrid use the same evidence prompt, model, temperature, and budget estimator. `backend/evaluation/experiment_runner.py` exports per-method predictions for those methods and the six one-flag ablations, with retrieval traces and explicit operational failures, including missing indexed chunks/graphs. The runner remains unvalidated against a frozen gold corpus and live services. Workflow and input shape are documented in `data/evaluation/README.md`. Also fixed the ingestion pipeline's four-chunk deep-extraction cap: all chunks now pass through the same extraction path, with the 30-chunk regression passing. This improves graph coverage but increases extraction calls, so real studies must report provider cost and exact model/service versions in addition to recorded token/latency counts.

Chat sessions now append multiple turns, display older question/answer pairs when resumed, restore the most recent paper selection and saved query output/trace, and support renaming as well as deleting sessions. `npm run lint` passes after these changes. This remains a single-browser local-storage feature; server persistence, cross-device synchronization, and durable large histories are not implemented.

## Required gates before submission

1. Freeze and checksum the paper corpus and final question set; complete independent gold annotations and adjudication.
2. Verify every relation and citation against original passages; specify exactly what “validated” means and distinguish extraction provenance from human validation.
3. Implement or remove the non-operative giant-SCC mitigation claim.
4. Run the shared exporter and scorer for Tarjan-RAG, local graph, static/dynamic community variants, BM25, dense, hybrid, and all six ablations on the frozen dataset; inspect validity gates and error records.
5. Run the pilot, fix measurement/retrieval failures, then run the main experiment with matched baselines, repeated runs, and uncertainty estimates.
6. Run all repository checks and live integration against the recorded Neo4j and LLM versions.
7. Write the paper with related work, method, dataset/annotation protocol, results, limitations, and reproducibility materials. Make no quality or “hallucination-free” claims without direct evidence.
