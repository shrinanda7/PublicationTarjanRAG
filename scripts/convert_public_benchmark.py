"""Adapter to convert standard public multi-hop and scholarly QA datasets into Tarjan-RAG gold evaluation schema.

Supported formats:
  - HotpotQA (distractor / fullwiki json)
  - 2WikiMultiHopQA (train / dev json)
  - QASPER (academic papers QA json)
  - Custom JSON format

Usage:
  python3 scripts/convert_public_benchmark.py --dataset hotpotqa --input hotpot_dev_distractor_v1.json --output data/evaluation/hotpotqa_gold.json --limit 50
  python3 scripts/convert_public_benchmark.py --dataset 2wikimultihop --input dev.json --output data/evaluation/2wiki_gold.json --limit 50
  python3 scripts/convert_public_benchmark.py --dataset qasper --input qasper-dev-v0.3.json --output data/evaluation/qasper_gold.json --limit 50
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def clean_text(text: str) -> str:
    """Normalize whitespace and strip text."""
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def convert_hotpotqa(raw_items: List[Dict[str, Any]], limit: Optional[int] = None) -> Dict[str, Any]:
    """Convert HotpotQA dev items to gold schema format.
    
    HotpotQA items contain:
      - _id: question ID
      - question: text
      - answer: text string
      - type: 'bridge' or 'comparison'
      - supporting_facts: list of [title, sentence_index]
      - context: list of [title, [sentence1, sentence2, ...]]
    """
    questions: List[Dict[str, Any]] = []
    
    for item in raw_items:
        if limit and len(questions) >= limit:
            break
            
        qid = str(item.get("_id", f"hotpot_{len(questions)+1}"))
        q_text = clean_text(item.get("question", ""))
        ans_text = clean_text(item.get("answer", ""))
        q_type = item.get("type", "bridge")
        
        if not q_text or not ans_text:
            continue
            
        # Parse context lookup: title -> sentences
        context_dict: Dict[str, List[str]] = {}
        for entry in item.get("context", []):
            if isinstance(entry, list) and len(entry) >= 2:
                title = clean_text(entry[0])
                sentences = [clean_text(s) for s in entry[1] if clean_text(s)]
                context_dict[title] = sentences
                
        # Parse supporting facts into gold_evidence
        gold_evidence: List[Dict[str, str]] = []
        doc_titles = set()
        for fact in item.get("supporting_facts", []):
            if isinstance(fact, list) and len(fact) >= 2:
                title = clean_text(fact[0])
                s_idx = int(fact[1])
                doc_titles.add(title)
                
                # Fetch quote if available in context
                quote = ""
                if title in context_dict and s_idx < len(context_dict[title]):
                    quote = context_dict[title][s_idx]
                if not quote:
                    quote = f"Supporting sentence from {title} (sentence index {s_idx})"
                    
                chunk_id = f"sent_{s_idx}"
                gold_evidence.append({
                    "paper_id": title,
                    "chunk_id": chunk_id,
                    "quote": quote
                })
                
        paper_ids = sorted(list(doc_titles)) if doc_titles else ["hotpot_doc_1"]
        category = "multi_hop_cross_paper" if len(paper_ids) >= 2 else "multi_hop_single_paper"
        required_hops = max(1, len(gold_evidence) - 1) if len(gold_evidence) > 1 else 1
        
        # Build gold path between evidence documents
        path_nodes: List[str] = []
        path_edges: List[Dict[str, str]] = []
        for i, doc in enumerate(paper_ids):
            path_nodes.append(f"{doc}::concept")
        if len(path_nodes) >= 2:
            for i in range(len(path_nodes) - 1):
                path_edges.append({
                    "source": path_nodes[i],
                    "target": path_nodes[i+1],
                    "type": "bridge_reference"
                })
        else:
            # Single paper / entity multi-hop: create chunk hops
            for i, ev in enumerate(gold_evidence[:3]):
                path_nodes.append(f"{ev['paper_id']}::{ev['chunk_id']}")
            if len(path_nodes) >= 2:
                for i in range(len(path_nodes) - 1):
                    path_edges.append({
                        "source": path_nodes[i],
                        "target": path_nodes[i+1],
                        "type": "reasoning_step"
                    })
            else:
                path_nodes = [f"{paper_ids[0]}::start", f"{paper_ids[0]}::end"]
                path_edges = [{"source": path_nodes[0], "target": path_nodes[1], "type": "entails"}]
                
        gold_paths = [{
            "nodes": path_nodes,
            "edges": path_edges
        }]
        
        questions.append({
            "question_id": f"hotpot_{qid}",
            "paper_ids": paper_ids,
            "question": q_text,
            "category": category,
            "answerable": True,
            "gold_answers": [ans_text],
            "gold_evidence": gold_evidence if gold_evidence else [{
                "paper_id": paper_ids[0],
                "chunk_id": "chunk_0",
                "quote": ans_text
            }],
            "gold_paths": gold_paths,
            "required_hops": required_hops,
            "annotation": {
                "source_dataset": "HotpotQA",
                "original_id": qid,
                "question_type": q_type,
                "adjudicated": True
            }
        })
        
    return {
        "version": "1.0",
        "corpus_version": "hotpotqa_distractor_v1",
        "description": "Converted HotpotQA multi-hop benchmark for Tarjan-RAG evaluation",
        "questions": questions
    }


def convert_2wikimultihop(raw_items: List[Dict[str, Any]], limit: Optional[int] = None) -> Dict[str, Any]:
    """Convert 2WikiMultiHopQA items to gold schema format.
    
    Contains explicit reasoning paths with entity relationships and supporting facts.
    """
    questions: List[Dict[str, Any]] = []
    
    for item in raw_items:
        if limit and len(questions) >= limit:
            break
            
        qid = str(item.get("_id", f"2wiki_{len(questions)+1}"))
        q_text = clean_text(item.get("question", ""))
        ans_text = clean_text(item.get("answer", ""))
        q_type = item.get("type", "compositional")
        
        if not q_text or not ans_text:
            continue
            
        # Parse context
        context_dict: Dict[str, List[str]] = {}
        for entry in item.get("context", []):
            if isinstance(entry, list) and len(entry) >= 2:
                title = clean_text(entry[0])
                sentences = [clean_text(s) for s in entry[1] if clean_text(s)]
                context_dict[title] = sentences
                
        gold_evidence: List[Dict[str, str]] = []
        doc_titles = set()
        for fact in item.get("supporting_facts", []):
            if isinstance(fact, list) and len(fact) >= 2:
                title = clean_text(fact[0])
                s_idx = int(fact[1])
                doc_titles.add(title)
                
                quote = ""
                if title in context_dict and s_idx < len(context_dict[title]):
                    quote = context_dict[title][s_idx]
                if not quote:
                    quote = f"Sentence {s_idx} from {title}"
                    
                gold_evidence.append({
                    "paper_id": title,
                    "chunk_id": f"s_{s_idx}",
                    "quote": quote
                })
                
        paper_ids = sorted(list(doc_titles)) if doc_titles else ["wiki_doc_1"]
        category = "multi_hop_cross_paper" if len(paper_ids) >= 2 else "multi_hop_single_paper"
        
        # Parse reasoning path
        ev_triples = item.get("evidences", [])
        path_nodes: List[str] = []
        path_edges: List[Dict[str, str]] = []
        
        if ev_triples:
            for triple in ev_triples:
                if isinstance(triple, list) and len(triple) >= 3:
                    sub, rel, obj = clean_text(triple[0]), clean_text(triple[1]), clean_text(triple[2])
                    if not path_nodes:
                        path_nodes.append(sub)
                    if sub == path_nodes[-1]:
                        path_nodes.append(obj)
                        path_edges.append({"source": sub, "target": obj, "type": rel or "relates"})
                        
        if len(path_nodes) < 2 or len(path_edges) != len(path_nodes) - 1:
            # Fallback to document-level path
            path_nodes = [f"{doc}::entity" for doc in paper_ids]
            if len(path_nodes) == 1:
                path_nodes.append(f"{paper_ids[0]}::target")
            path_edges = [
                {"source": path_nodes[i], "target": path_nodes[i+1], "type": "relates_to"}
                for i in range(len(path_nodes) - 1)
            ]
            
        gold_paths = [{
            "nodes": path_nodes,
            "edges": path_edges
        }]
        
        questions.append({
            "question_id": f"2wiki_{qid}",
            "paper_ids": paper_ids,
            "question": q_text,
            "category": category,
            "answerable": True,
            "gold_answers": [ans_text],
            "gold_evidence": gold_evidence if gold_evidence else [{
                "paper_id": paper_ids[0],
                "chunk_id": "c0",
                "quote": ans_text
            }],
            "gold_paths": gold_paths,
            "required_hops": max(1, len(path_edges)),
            "annotation": {
                "source_dataset": "2WikiMultiHopQA",
                "original_id": qid,
                "question_type": q_type,
                "adjudicated": True
            }
        })
        
    return {
        "version": "1.0",
        "corpus_version": "2wikimultihop_v1",
        "description": "Converted 2WikiMultiHopQA multi-hop benchmark for Tarjan-RAG evaluation",
        "questions": questions
    }


def convert_qasper(raw_data: Dict[str, Any], limit: Optional[int] = None) -> Dict[str, Any]:
    """Convert QASPER (academic papers QA) to gold schema format.
    
    QASPER is paper-level: raw_data maps paper_id -> paper data with 'qas'.
    """
    questions: List[Dict[str, Any]] = []
    
    for paper_id, pdata in raw_data.items():
        if limit and len(questions) >= limit:
            break
        qas = pdata.get("qas", [])
        for qa in qas:
            if limit and len(questions) >= limit:
                break
            qid = str(qa.get("question_id", f"qasper_{len(questions)+1}"))
            q_text = clean_text(qa.get("question", ""))
            
            # Find acceptable answers & evidence
            answers: List[str] = []
            evidence_quotes: List[str] = []
            
            for ans_obj in qa.get("answers", []):
                ans = ans_obj.get("answer", {})
                if ans.get("unanswerable"):
                    continue
                free_text = clean_text(ans.get("free_form_answer", ""))
                ext_spans = ans.get("extractive_spans", [])
                yes_no = ans.get("yes_no")
                
                if free_text:
                    answers.append(free_text)
                elif ext_spans:
                    answers.extend([clean_text(s) for s in ext_spans if clean_text(s)])
                elif yes_no is not None:
                    answers.append("Yes" if yes_no else "No")
                    
                for ev in ans.get("evidence", []):
                    if clean_text(ev):
                        evidence_quotes.append(clean_text(ev))
                        
            if not answers:
                # Unanswerable / abstention test
                questions.append({
                    "question_id": f"qasper_{qid}",
                    "paper_ids": [paper_id],
                    "question": q_text,
                    "category": "single_paper",
                    "answerable": False,
                    "gold_answers": [],
                    "gold_evidence": [],
                    "gold_paths": [],
                    "required_hops": 0,
                    "annotation": {
                        "source_dataset": "QASPER",
                        "paper_title": clean_text(pdata.get("title", "")),
                        "unanswerable_control": True
                    }
                })
                continue
                
            gold_ev = [
                {"paper_id": paper_id, "chunk_id": f"ev_{i}", "quote": q}
                for i, q in enumerate(set(evidence_quotes))
            ] if evidence_quotes else [{
                "paper_id": paper_id, "chunk_id": "ev_0", "quote": answers[0]
            }]
            
            questions.append({
                "question_id": f"qasper_{qid}",
                "paper_ids": [paper_id],
                "question": q_text,
                "category": "single_paper",
                "answerable": True,
                "gold_answers": list(set(answers)),
                "gold_evidence": gold_ev,
                "gold_paths": [],
                "required_hops": 1,
                "annotation": {
                    "source_dataset": "QASPER",
                    "paper_title": clean_text(pdata.get("title", "")),
                    "adjudicated": True
                }
            })
            
    return {
        "version": "1.0",
        "corpus_version": "qasper_dev_v1",
        "description": "Converted QASPER scholarly paper QA benchmark for Tarjan-RAG evaluation",
        "questions": questions
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset", required=True, choices=["hotpotqa", "2wikimultihop", "qasper"])
    parser.add_argument("--input", required=True, help="Input raw JSON file downloaded from dataset source")
    parser.add_argument("--output", required=True, help="Output converted gold standard JSON")
    parser.add_argument("--limit", type=int, default=None, help="Limit number of questions converted")
    args = parser.parse_args()
    
    input_path = Path(args.input)
    if not input_path.exists():
        print(f"Error: input file {input_path} not found.", file=sys.stderr)
        return 1
        
    with open(input_path, "r", encoding="utf-8") as f:
        raw_data = json.load(f)
        
    if args.dataset == "hotpotqa":
        converted = convert_hotpotqa(raw_data if isinstance(raw_data, list) else raw_data.get("data", []), limit=args.limit)
    elif args.dataset == "2wikimultihop":
        converted = convert_2wikimultihop(raw_data if isinstance(raw_data, list) else raw_data.get("data", []), limit=args.limit)
    elif args.dataset == "qasper":
        converted = convert_qasper(raw_data, limit=args.limit)
    else:
        print(f"Unknown dataset type {args.dataset}", file=sys.stderr)
        return 1
        
    out_path = Path(args.output)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(converted, f, indent=2, ensure_ascii=False)
        
    print(f"Successfully converted {len(converted['questions'])} questions from {args.dataset} to {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
