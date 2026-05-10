#!/usr/bin/env python3
"""Inspect a UnifiedResult and dump JSON + histogram PNG.

Usage:
    python analyze_result.py <uqt_id>
    python analyze_result.py <uqt_id> --out reports/
    python analyze_result.py <uqt_id> --no-plot           # text-only

The script:
    1. Re-attaches to the task via wait_for_result (works on a fresh shell as long as
       ~/.uniqc/cache/tasks.sqlite still has the entry).
    2. Prints a counts/probability table.
    3. Saves counts.json and (optionally) counts.png next to it.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def print_table(result, top: int = 16) -> None:
    items = sorted(result.counts.items(), key=lambda kv: kv[1], reverse=True)[:top]
    width = max(len(k) for k, _ in items)
    print(f"task={result.task_id} shots={result.shots} platform={result.platform} backend={result.backend_name}")
    print(f"{'bitstring':<{width}}  {'count':>6}  {'probability':>11}")
    for k, n in items:
        print(f"{k:<{width}}  {n:>6}  {n / result.shots:>11.4f}")


def main() -> None:
    parser = argparse.ArgumentParser(description="Analyze a UnifiedQuantum task result")
    parser.add_argument("task_id", help="uniqc task id, e.g. uqt_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx")
    parser.add_argument("--out", type=Path, default=Path("./reports"))
    parser.add_argument("--top", type=int, default=16)
    parser.add_argument("--no-plot", action="store_true")
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    from uniqc import wait_for_result, query_task

    info = query_task(args.task_id)
    print(f"status: {getattr(info, 'status', info)}")

    result = wait_for_result(args.task_id, timeout=args.timeout)
    if result is None:
        sys.exit("task failed — see `uniqc task show <uid>` for platform error.")
    if isinstance(result, list):
        print(f"batch result with {len(result)} circuits — using element [0] for plot.")
        outer_results = result
        result = result[0]
    else:
        outer_results = [result]

    print_table(result, top=args.top)

    args.out.mkdir(parents=True, exist_ok=True)
    json_path = args.out / f"{args.task_id}.json"
    json_path.write_text(json.dumps(
        {
            "task_id": args.task_id,
            "platform": result.platform,
            "backend_name": result.backend_name,
            "shots": result.shots,
            "counts": result.counts,
            "probabilities": result.probabilities,
            "circuits": [
                {
                    "shots": r.shots if r is not None else 0,
                    "counts": r.counts if r is not None else None,
                }
                for r in outer_results
            ] if len(outer_results) > 1 else None,
        },
        indent=2,
    ))
    print(f"\nwrote {json_path}")

    if args.no_plot:
        return

    try:
        import matplotlib.pyplot as plt
        from uniqc.visualization import plot_histogram
    except ImportError as exc:
        print(f"matplotlib not installed ({exc}); skipping plot.")
        return

    plot_histogram(result.counts, title=f"counts {result.task_id[:10]}…")
    png_path = args.out / f"{args.task_id}.png"
    plt.savefig(png_path, dpi=160, bbox_inches="tight")
    plt.close()
    print(f"wrote {png_path}")


if __name__ == "__main__":
    main()
