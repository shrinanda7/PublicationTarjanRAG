"""Validate human-authored gold question annotations before evaluation."""
import argparse
import sys

from backend.evaluation.gold_dataset import load_dataset


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("dataset", help="Path to the frozen gold dataset JSON")
    parser.add_argument("--chunk-manifest", help="Optional paper_id -> list of ingested chunk IDs JSON")
    args = parser.parse_args()
    try:
        dataset = load_dataset(args.dataset, args.chunk_manifest)
    except (OSError, ValueError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"Valid gold dataset: {len(dataset['questions'])} questions; corpus={dataset['corpus_version']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
