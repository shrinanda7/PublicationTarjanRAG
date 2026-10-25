"""Paired bootstrap and sign-flip comparisons over repeated scored runs."""
from __future__ import annotations

import argparse
import itertools
import json
import math
import random
import statistics
import sys
from pathlib import Path
from typing import Any, Dict, List, Sequence


def _number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(float(value))


def _load_runs(inputs: Sequence[str]) -> tuple[Dict[str, List[Dict[str, Any]]], str]:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    seen_run_ids: Dict[str, set[str]] = {}
    seen_seeds: Dict[str, set[int]] = {}
    fingerprint = None
    shared_settings: Dict[str, Any] | None = None
    embedding_models: set[str] = set()
    comparable_fields = (
        "model", "prompt_version", "temperature", "top_k", "max_evidence_chunks",
        "max_context_chars", "max_context_tokens_estimated", "token_estimator",
        "hardware_platform",
    )
    for spec in inputs:
        if "=" not in spec:
            raise ValueError(f"Input must use METHOD=PATH form: {spec!r}")
        method, filename = spec.split("=", 1)
        if not method.strip() or not filename.strip():
            raise ValueError(f"Input must use non-empty METHOD=PATH form: {spec!r}")
        result = json.loads(Path(filename).read_text(encoding="utf-8"))
        if result.get("valid_for_analysis") is not True:
            raise ValueError(f"Scored run is not valid for analysis: {filename}")
        current = result.get("dataset_sha256")
        if not current:
            raise ValueError(f"Scored run has no dataset fingerprint: {filename}")
        run = result.get("run")
        if not isinstance(run, dict) or run.get("methods") != [method.strip()]:
            raise ValueError(f"Scored run method metadata does not match alias {method.strip()!r}: {filename}")
        run_id = run.get("run_id")
        seed = run.get("seed")
        if not isinstance(run_id, str) or not run_id.strip():
            raise ValueError(f"Scored run has no unique run_id: {filename}")
        if isinstance(seed, bool) or not isinstance(seed, int):
            raise ValueError(f"Scored run has no integer seed: {filename}")
        current_settings = {field: run.get(field) for field in comparable_fields}
        if shared_settings is None:
            shared_settings = current_settings
        else:
            mismatches = {
                field: {"expected": shared_settings[field], "actual": current_settings[field]}
                for field in comparable_fields
                if current_settings[field] != shared_settings[field]
            }
            if mismatches:
                raise ValueError(f"Runs do not share matched experiment settings: {mismatches}")
        if method.strip() in {"dense", "hybrid"}:
            embedding_model = run.get("embedding_model")
            if not isinstance(embedding_model, str) or not embedding_model.strip():
                raise ValueError(f"Embedding baseline has no embedding_model metadata: {filename}")
            embedding_models.add(embedding_model)
        if run_id in seen_run_ids.setdefault(method.strip(), set()):
            raise ValueError(f"Duplicate run_id for method {method.strip()!r}: {run_id}")
        if seed in seen_seeds.setdefault(method.strip(), set()):
            raise ValueError(f"Repeated seed for method {method.strip()!r}: {seed}; use distinct seeds for repeated runs")
        seen_run_ids[method.strip()].add(run_id)
        seen_seeds[method.strip()].add(seed)
        if fingerprint is None:
            fingerprint = current
        elif current != fingerprint:
            raise ValueError("All score files must have the same validated dataset fingerprint")
        grouped.setdefault(method.strip(), []).append(result)
    if len(grouped) < 2:
        raise ValueError("At least two named methods are required")
    for method, runs in grouped.items():
        if len(runs) < 2:
            raise ValueError(f"Method {method!r} needs at least two valid repeated runs")
    if len(embedding_models) > 1:
        raise ValueError(f"Dense and hybrid baselines use different embedding models: {sorted(embedding_models)}")
    return grouped, str(fingerprint)


def _percentile(sorted_values: Sequence[float], probability: float) -> float:
    if len(sorted_values) == 1:
        return sorted_values[0]
    position = (len(sorted_values) - 1) * probability
    lower = math.floor(position)
    upper = math.ceil(position)
    if lower == upper:
        return sorted_values[lower]
    fraction = position - lower
    return sorted_values[lower] * (1 - fraction) + sorted_values[upper] * fraction


def _sign_flip_p_value(differences: Sequence[float], samples: int, rng: random.Random) -> float:
    observed = abs(statistics.mean(differences))
    n = len(differences)
    tolerance = 1e-15
    if n <= 20:
        total = 1 << n
        extreme = 0
        for signs in itertools.product((-1.0, 1.0), repeat=n):
            permuted = abs(sum(value * sign for value, sign in zip(differences, signs)) / n)
            extreme += permuted + tolerance >= observed
        return extreme / total
    extreme = 0
    for _ in range(samples):
        permuted = abs(sum(value * (-1.0 if rng.getrandbits(1) else 1.0) for value in differences) / n)
        extreme += permuted + tolerance >= observed
    return (extreme + 1) / (samples + 1)


def compare_runs(
    grouped: Dict[str, List[Dict[str, Any]]],
    dataset_sha256: str,
    *,
    bootstrap_samples: int = 10000,
    seed: int = 2026,
) -> Dict[str, Any]:
    if bootstrap_samples < 1000:
        raise ValueError("Use at least 1000 bootstrap samples")
    per_method: Dict[str, Dict[str, Dict[str, List[float]]]] = {}
    categories_by_method: Dict[str, Dict[str, str]] = {}
    metric_names = set()
    for method, runs in grouped.items():
        qids = None
        metric_data: Dict[str, Dict[str, List[float]]] = {}
        categories: Dict[str, str] = {}
        for run in runs:
            rows = run.get("per_question")
            if not isinstance(rows, list):
                raise ValueError(f"Method {method!r} has a score file without per_question rows")
            current_qids = {str(row.get("question_id")) for row in rows if row.get("question_id")}
            if qids is None:
                qids = current_qids
            elif current_qids != qids:
                raise ValueError(f"Repeated runs for method {method!r} do not cover identical question IDs")
            for row in rows:
                qid = str(row["question_id"])
                category = str(row.get("category", "unstratified"))
                if qid in categories and categories[qid] != category:
                    raise ValueError(f"Question {qid!r} has inconsistent categories across repeated runs for {method!r}")
                categories[qid] = category
                for metric, value in row.items():
                    if _number(value):
                        metric_names.add(metric)
                        metric_data.setdefault(metric, {}).setdefault(qid, []).append(float(value))
        per_method[method] = metric_data
        categories_by_method[method] = categories

    # Retain only metric names with comparable values for every method.
    common_metrics = set.intersection(*(set(per_method[m]) for m in per_method)) if per_method else set()
    comparisons = []
    methods = sorted(per_method)
    rng = random.Random(seed)
    for left_index, left in enumerate(methods):
        for right in methods[left_index + 1:]:
            for metric in sorted(common_metrics):
                left_q = per_method[left][metric]
                right_q = per_method[right][metric]
                qids = sorted(set(left_q) & set(right_q))
                paired = []
                for qid in qids:
                    if categories_by_method[left].get(qid) != categories_by_method[right].get(qid):
                        raise ValueError(f"Question {qid!r} has different categories between methods {left!r} and {right!r}")
                    left_mean = statistics.mean(left_q[qid])
                    right_mean = statistics.mean(right_q[qid])
                    paired.append((qid, right_mean - left_mean, categories_by_method[left].get(qid, "unstratified")))
                if not paired:
                    continue
                diffs = [value for _, value, _ in paired]
                by_category: Dict[str, List[float]] = {}
                for _, value, category in paired:
                    by_category.setdefault(category, []).append(value)
                boot_means = []
                for _ in range(bootstrap_samples):
                    resampled = [
                        values[rng.randrange(len(values))]
                        for values in by_category.values()
                        for _ in values
                    ]
                    boot_means.append(statistics.mean(resampled))
                boot_means.sort()
                comparisons.append({
                    "metric": metric,
                    "reference_method": left,
                    "comparison_method": right,
                    "difference_direction": f"{right} minus {left}",
                    "paired_question_count": len(paired),
                    "bootstrap_strata": {category: len(values) for category, values in sorted(by_category.items())},
                    "mean_paired_difference": statistics.mean(diffs),
                    "bootstrap_ci_95": [_percentile(boot_means, 0.025), _percentile(boot_means, 0.975)],
                    "paired_sign_flip_p_value": _sign_flip_p_value(diffs, bootstrap_samples, rng),
                    "question_level_differences": [{"question_id": qid, "category": category, "difference": value} for qid, value, category in paired],
                })
    order = sorted(range(len(comparisons)), key=lambda index: comparisons[index]["paired_sign_flip_p_value"])
    previous_adjusted = 0.0
    total_hypotheses = len(order)
    for rank, index in enumerate(order):
        raw_p = comparisons[index]["paired_sign_flip_p_value"]
        adjusted = min(1.0, raw_p * (total_hypotheses - rank))
        previous_adjusted = max(previous_adjusted, adjusted)
        comparisons[index]["p_value_holm_adjusted"] = previous_adjusted
    return {
        "analysis_version": "1.0",
        "dataset_sha256": dataset_sha256,
        "methods": {method: {"run_count": len(runs)} for method, runs in grouped.items()},
        "bootstrap_samples": bootstrap_samples,
        "random_seed": seed,
        "uncertainty_unit": "question; repeated runs are averaged within question, then paired bootstrap resamples within gold categories",
        "p_value_adjustment": "Holm-Bonferroni over all reported method-pair by metric tests",
        "comparisons": comparisons,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("inputs", nargs="+", help="Repeated METHOD=score.json inputs; provide at least two runs for each of two methods")
    parser.add_argument("--bootstrap-samples", type=int, default=10000)
    parser.add_argument("--seed", type=int, default=2026)
    parser.add_argument("--output")
    args = parser.parse_args()
    try:
        grouped, fingerprint = _load_runs(args.inputs)
        result = compare_runs(grouped, fingerprint, bootstrap_samples=args.bootstrap_samples, seed=args.seed)
        rendered = json.dumps(result, indent=2, ensure_ascii=False) + "\n"
        if args.output:
            Path(args.output).write_text(rendered, encoding="utf-8")
        else:
            print(rendered, end="")
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
