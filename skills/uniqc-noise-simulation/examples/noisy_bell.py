"""End-to-end noisy simulation: hand-built model + chip-backed dummy comparison."""

from __future__ import annotations

from uniqc import Circuit, submit_task, wait_for_result
from uniqc.simulator import Simulator, NoisySimulator
from uniqc.simulator.error_model import (
    Depolarizing,
    TwoQubitDepolarizing,
    AmplitudeDamping,
    ErrorLoader_GateTypeError,
)


def build_bell() -> Circuit:
    c = Circuit(2)
    c.h(0)
    c.cnot(0, 1)
    c.measure(0)
    c.measure(1)
    return c


def main() -> None:
    c = build_bell()

    # 1. Ideal reference (no noise)
    ideal = Simulator(backend_type="statevector").simulate_pmeasure(c)
    print("ideal probs:        ", [round(p, 4) for p in ideal])

    # 2. Hand-built noise model
    loader = ErrorLoader_GateTypeError(
        generic_error=[Depolarizing(0.001)],
        gatetype_error={
            "H":    [AmplitudeDamping(0.0008)],
            "CNOT": [TwoQubitDepolarizing(0.006)],
        },
    )
    noisy = NoisySimulator(
        backend_type="density_matrix",
        error_loader=loader,
        readout_error={0: [0.012, 0.018], 1: [0.014, 0.020]},
    )
    counts_handcrafted = noisy.simulate_shots(c, shots=2000)
    print("hand-built counts:  ", counts_handcrafted)

    # 3. Chip-backed dummy (uses the cached chip characterization)
    uid = submit_task(c, backend="dummy:originq:WK_C180", shots=2000)
    chip_result = wait_for_result(uid, timeout=60)
    print("chip-backed counts: ", chip_result.counts if chip_result else "(failed)")

    # 4. Suggested action: if (2) and (3) disagree by more than shot noise,
    #    the hand-built model is likely missing a channel (commonly a missing
    #    AmplitudeDamping / PhaseFlip layer that the chip-backed path includes
    #    for free from the cached T1/T2 numbers). Refine and re-run.


if __name__ == "__main__":
    main()
