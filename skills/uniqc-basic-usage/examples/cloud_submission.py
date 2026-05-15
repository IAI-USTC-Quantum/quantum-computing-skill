#!/usr/bin/env python3
"""Programmatic cloud-task examples for UnifiedQuantum.

By default this script runs a dummy submission so it is safe for local
testing. Real backend examples are included as callable functions but are
not executed automatically.

Notes for readers:

* uniqc itself does NOT auto-read ``ORIGINQ_API_KEY`` / ``QUAFU_API_TOKEN`` /
  ``QUARK_API_KEY`` / ``IBM_TOKEN`` environment variables. Tokens live in
  ``~/.uniqc/config.yaml`` (set them via ``uniqc config set <platform>.<key>``).
  The :func:`_sync_env_to_config` helper below is a per-script convenience
  that copies env vars INTO that config so CI-style workflows work; it is not
  built into uniqc.
* ``wait_for_result(...)`` returns a :class:`UnifiedResult` dataclass. Access
  measurement data via ``result.counts`` / ``result.probabilities`` (and
  ``result.metadata``); ``result.raw()`` returns the platform-specific raw
  payload. ``UnifiedResult`` also implements a dict-like ``__getitem__``
  proxy onto ``counts`` so ``result["00"]`` works, but ``result["counts"]``
  does **not** (it would try to look up a bitstring named ``"counts"``).
* For real ``originq`` (and chip-backed ``dummy:originq:<chip>``) submissions
  you need ``unified-quantum[originq]``. The chip-backed dummy compile pass
  uses qiskit, which is now a **core dependency** in uniqc 0.0.13 — no
  ``[qiskit]`` extra required.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
from pprint import pprint

import yaml

from uniqc import (
    Circuit,
    compile,
    find_backend,
    query_task,
    submit_task,
    wait_for_result,
)


def build_bell_circuit() -> Circuit:
    circuit = Circuit(2)
    circuit.h(0)
    circuit.cnot(0, 1)
    circuit.measure(0)
    circuit.measure(1)
    return circuit


def print_result(result) -> None:
    """``wait_for_result`` returns a :class:`UnifiedResult`; print its counts."""

    if not result:
        print("No result returned.")
        return

    print("Counts (dict[bitstring|int, int]):")
    pprint(getattr(result, "counts", result))


def run_dummy_demo(shots: int) -> None:
    try:
        from uniqc.backend_adapter.task.optional_deps import check_simulation
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
      1. ``pip install "unified-quantum[originq]"``
      2. ``uniqc config set originq.token <TOKEN>`` (uniqc does NOT read
         ``ORIGINQ_API_KEY`` automatically; set the token in
         ``~/.uniqc/config.yaml``).

    The circuit is compiled to the chip's native gate set BEFORE submission.
    Since uniqc 0.0.11.dev30, ``submit_task`` itself runs qiskit transpile
    (``local_compile=1`` default), so explicit pre-compile is not strictly
    required for simple circuits — but doing it explicitly is still the
    clearest pattern for examples.
    """

    _sync_env_to_config()
    circuit = build_bell_circuit()
    backend_info = find_backend("originq:WK_C180")
    compiled = compile(circuit, backend_info, level=2)
    return submit_task(
        compiled,
        backend="originq:WK_C180",  # uniqc ≥ 0.0.13: provider:chip required
        shots=shots,
        metadata={"example": "real-originq"},
    )


def real_quafu_example(shots: int) -> str:
    """Skeleton for a real Quafu submission.

    Quafu is **deprecated and archived** as of uniqc 0.0.13. The
    ``[quafu]`` extra has been removed; install ``pyquafu`` directly
    if you still need it (and accept the ``numpy<2`` constraint that
    pyquafu pulls in). Importing the Quafu adapter emits a
    ``DeprecationWarning``. New code should target OriginQ / Quark / IBM.

    Requires:
      1. ``pip install pyquafu`` (and pin ``numpy<2`` if needed)
      2. ``uniqc config set quafu.token <TOKEN>`` (uniqc does NOT read
         ``QUAFU_API_TOKEN`` automatically).
    """

    _sync_env_to_config()
    circuit = build_bell_circuit()
    return submit_task(
        circuit,
        backend="quafu:ScQ-Sim10",  # uniqc ≥ 0.0.13: provider:chip required
        shots=shots,
        metadata={"example": "real-quafu"},
    )


def real_ibm_example(shots: int) -> str:
    """Skeleton for a real IBM submission.

    Requires:
      1. ``pip install unified-quantum`` — qiskit, qiskit-aer, and
         qiskit-ibm-runtime ship with the core install in uniqc 0.0.13
         (the ``[qiskit]`` extra has been removed).
      2. ``uniqc config set ibm.token <TOKEN>`` (and, if needed,
         ``uniqc config set ibm.proxy.https <URL>``). uniqc does NOT read
         ``IBM_TOKEN`` automatically.
    """

    _sync_env_to_config()
    circuit = build_bell_circuit()
    return submit_task(
        circuit,
        backend="ibm:ibm_fez",  # uniqc ≥ 0.0.13: provider:chip required
        shots=shots,
        metadata={"example": "real-ibm"},
    )


def real_quark_example(shots: int) -> str:
    """Skeleton for a real Quark submission.

    Requires:
      1. ``pip install "unified-quantum[quark]"``  (Python >= 3.12)
      2. ``uniqc config set quark.QUARK_API_KEY <TOKEN>`` (uniqc does NOT
         read ``QUARK_API_KEY`` automatically).
    """

    _sync_env_to_config()
    circuit = build_bell_circuit()
    return submit_task(
        circuit,
        backend="quark",
        shots=shots,
        chip_id="Baihua",
        metadata={"example": "real-quark"},
    )


def _sync_env_to_config() -> None:
    """Per-script convenience: copy ``~/.uniqc/config.yaml`` tokens into env vars.

    This is NOT how uniqc itself looks up tokens -- uniqc reads tokens straight
    out of ``~/.uniqc/config.yaml``. This helper is here only so that downstream
    code which does read env vars (e.g. some legacy adapter SDKs, CI tooling)
    sees the same values without the user having to duplicate them.
    """

    config_path = Path.home() / ".uniqc" / "config.yaml"
    if not config_path.exists():
        return

    data = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
    profile_name = data.get("active_profile", "default")
    profile = data.get(profile_name, {})

    mappings = {
        ("originq", "token"): "ORIGINQ_API_KEY",
        ("quafu", "token"): "QUAFU_API_TOKEN",
        ("quark", "QUARK_API_KEY"): "QUARK_API_KEY",
        ("ibm", "token"): "IBM_TOKEN",
    }
    for (platform, key), env_name in mappings.items():
        token = profile.get(platform, {}).get(key)
        if token and not os.getenv(env_name):
            os.environ[env_name] = token


# Backwards-compatible alias for the previous public name.
load_adapter_env_from_uniqc_config = _sync_env_to_config


def main() -> None:
    parser = argparse.ArgumentParser(description="UnifiedQuantum cloud submission demo")
    parser.add_argument("--shots", type=int, default=1000)
    args = parser.parse_args()

    run_dummy_demo(args.shots)

    print("\nReal backend entry points are available as helper functions:")
    print("  - real_originq_example(shots)")
    print("  - real_quafu_example(shots)")
    print("  - real_quark_example(shots)")
    print("  - real_ibm_example(shots)")


if __name__ == "__main__":
    main()
