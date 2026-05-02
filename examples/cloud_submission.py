#!/usr/bin/env python3
"""Programmatic cloud-task examples for UnifiedQuantum.

By default this script runs a dummy submission so it is safe for local
testing. Real backend examples are included as callable functions but are
not executed automatically.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from pprint import pprint

import yaml

from uniqc import Circuit, query_task, submit_task, wait_for_result


def build_bell_circuit() -> Circuit:
    circuit = Circuit(2)
    circuit.h(0)
    circuit.cnot(0, 1)
    circuit.measure(0, 1)
    return circuit


def print_result(result: dict | None) -> None:
    if not result:
        print("No result returned.")
        return

    print("Normalized result payload:")
    pprint(result)

    if all(isinstance(value, int) for value in result.values()):
        print("\nCounts:")
        pprint(result)
        return

    if "counts" in result:
        print("\nCounts:")
        pprint(result["counts"])

    if "probabilities" in result:
        print("\nProbabilities:")
        pprint(result["probabilities"])


def run_dummy_demo(shots: int) -> None:
    try:
        from uniqc.task.optional_deps import check_simulation
    except ImportError:
        check_simulation = lambda: False

    if not check_simulation():
        raise RuntimeError(
            "Dummy mode uses the local simulator. Install unified-quantum[simulation] first."
        )

    circuit = build_bell_circuit()
    task_id = submit_task(
        circuit,
        backend="dummy",
        shots=shots,
        metadata={"example": "cloud_submission.py"},
    )

    print(f"Dummy task submitted: {task_id}")

    task_info = query_task(task_id)
    print(f"Cached task status: {task_info.status}")
    print(f"Cached backend tag: {task_info.backend}")

    result = wait_for_result(task_id, timeout=60)
    print_result(result)


def real_originq_example(shots: int) -> str:
    """Skeleton for a real OriginQ submission.

    Requires:
      1. pip install "unified-quantum[originq]"
      2. configure ~/.uniqc/uniqc.yml or export ORIGINQ_API_KEY=...
    """

    load_adapter_env_from_uniqc_config()
    circuit = build_bell_circuit()
    return submit_task(
        circuit,
        backend="originq",
        shots=shots,
        backend_name="WK_C180",
        metadata={"example": "real-originq"},
    )


def real_quafu_example(shots: int) -> str:
    """Skeleton for a real Quafu submission.

    Requires:
      1. pip install "unified-quantum[quafu]"
      2. configure ~/.uniqc/uniqc.yml or export QUAFU_API_TOKEN=...
    """

    load_adapter_env_from_uniqc_config()
    circuit = build_bell_circuit()
    return submit_task(
        circuit,
        backend="quafu",
        shots=shots,
        chip_id="ScQ-Sim10",
        metadata={"example": "real-quafu"},
    )


def real_ibm_example(shots: int) -> str:
    """Skeleton for a real IBM submission.

    Requires:
      1. pip install "unified-quantum[qiskit]"
      2. configure ~/.uniqc/uniqc.yml or export IBM_TOKEN=...
    """

    load_adapter_env_from_uniqc_config()
    circuit = build_bell_circuit()
    return submit_task(
        circuit,
        backend="ibm",
        shots=shots,
        metadata={"example": "real-ibm"},
    )


def load_adapter_env_from_uniqc_config() -> None:
    """Map ~/.uniqc/uniqc.yml tokens into env vars for script portability."""

    config_path = Path.home() / ".uniqc" / "uniqc.yml"
    if not config_path.exists():
        return

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    profile_name = data.get("active_profile", "default")
    profile = data.get(profile_name, {})

    mappings = {
        ("originq", "token"): "ORIGINQ_API_KEY",
        ("quafu", "token"): "QUAFU_API_TOKEN",
        ("ibm", "token"): "IBM_TOKEN",
    }
    for (platform, key), env_name in mappings.items():
        token = profile.get(platform, {}).get(key)
        if token and not os.getenv(env_name):
            os.environ[env_name] = token


def main() -> None:
    parser = argparse.ArgumentParser(description="UnifiedQuantum cloud submission demo")
    parser.add_argument("--shots", type=int, default=1000)
    args = parser.parse_args()

    run_dummy_demo(args.shots)

    print("\nReal backend entry points are available as helper functions:")
    print("  - real_originq_example(shots)")
    print("  - real_quafu_example(shots)")
    print("  - real_ibm_example(shots)")


if __name__ == "__main__":
    main()
