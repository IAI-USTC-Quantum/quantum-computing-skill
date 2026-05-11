# The QV protocol

Quantum Volume is defined in Cross et al. 2019 (arXiv:1811.12926).
It is the largest power of two `2^n` such that the hardware can
faithfully execute a "square" random circuit at width `n` and depth `n`.
The figure of merit is the **heavy-output probability**.

## Step-by-step

For each width `n`:

1. Sample `K ≥ 100` random "model circuits" `U_k` of width `n` and
   depth `n`. Each layer is:
   - a uniformly random permutation of the `n` qubits,
   - `floor(n/2)` random `SU(4)` gates applied to disjoint pairs along
     the permutation.
2. For each `U_k`:
   - Compute the *ideal* output probability vector `p_k(x)` for
     `x ∈ {0, 1}^n` (statevector or stabilizer-aware sim).
   - Define the **heavy set** `H_k = { x : p_k(x) > median(p_k) }`.
3. Run `U_k` on the target backend with `S ≥ 1000` shots and obtain
   counts `c_k(x)`.
4. Compute the heavy-output frequency
   `h_k = Σ_{x ∈ H_k} c_k(x) / S`.
5. Score: mean `h̄ = (1/K) Σ h_k`, sample variance
   `σ² = (1/(K-1)) Σ (h_k - h̄)²`, and the one-sided 2σ lower
   confidence bound on the mean:
   `LCB = h̄ − 2 · σ / √K`.
6. **Pass** if `LCB > 2/3`. Otherwise the width fails.

The largest passing `n` defines `QV = 2^n_max`.

## Why the heavy-output rule?

For a Haar-random `n`-qubit unitary, the expected fraction of
amplitude carried by the upper half of the Porter-Thomas distribution
is `(1 + ln 2) / 2 ≈ 0.847` as `n → ∞`. Fully depolarised noise gives
`0.5`. The 2/3 threshold sits comfortably between the two and rejects
hardware whose effective channel is close to depolarising.

> ⚠️ **The 0.847 ceiling, not 1.0, is the point of the test.**
> A *perfect* simulator on QV circuits reproduces the ideal output
> distribution exactly, which means its measured heavy-output
> frequency equals the *ideal* heavy-output probability — and the
> ideal value is bounded above by Porter-Thomas. So `dummy:local:simulator`
> scoring around 0.79 (n=2) or 0.85 (n=3+) is **not** a bug or
> noise: it is the theoretical maximum.
>
> Empirically (uniqc 0.0.13.dev0, 30 circuits per width):
>
> | n | ideal mean heavy-output | perfect-sim measured |
> |---|------------------------:|---------------------:|
> | 2 |                  0.7852 |               0.7852 |
> | 3 |                  0.8512 |               0.8512 |
> | 4 |                  0.8262 |               0.8261 |
> | 5 |                  0.8445 |               0.8445 |
> | 6 |                  0.8492 |               0.8492 |
>
> Note that n=2 sits below the asymptote because the Porter-Thomas
> approximation is loose at d=4. From n≈4 the measured value tracks
> 0.85 ± shot noise. Real hardware will report something in (0.5, 0.85);
> if the LCB(2σ) of that mean exceeds 2/3, the width passes.

The single most useful diagnostic when staring at a QV result is the
ratio `measured / ideal`. A perfect simulator gives ≈ 1.000; depolarised
hardware gives ≈ `0.5 / 0.847 ≈ 0.59`; passing real hardware is
typically 0.85 – 0.95 of ideal at small widths.

## Why the 2σ confidence bound?

Without the LCB, you could "pass" QV by getting lucky once. The 2σ
test is a one-sided binomial-style certificate: with probability
~0.977 the true mean is at least `LCB`, so passing the test gives
real confidence that this hardware really does deserve QV `≥ 2^n`.

## What QV does *not* measure

- Specific-application accuracy (a chip can have QV-256 and still
  fail a particular VQE).
- Gate-by-gate fidelity (use XEB for that).
- Wall-clock throughput or queue latency.
- The largest circuit width the chip can address (different from the
  largest width that *passes*).

For a richer picture, complement QV with XEB
(see the `uniqc-xeb-qem` skill) and per-application benchmarks.

## Practical decisions when running QV

- **Width sweep**: 2, 3, 4, … incrementing by 1 until one width fails.
  Stop there; do not "skip" widths.
- **Same seed list** across backends. Reproducibility matters.
- **Compile per backend** — the depth is "logical depth", but the
  *executed* depth on a chip with different basis / topology can be
  much larger. Use `uniqc.compile(c, find_backend(...), level=2)`.
- **Apply readout mitigation** to counts before computing `h_k` for
  noisy backends — readout error alone can drag a passing chip below
  `2/3`.
- **Use the function form** `qiskit.circuit.library.quantum_volume(n,
  depth, seed=...)`. The class form `QuantumVolume(n, depth)` is
  deprecated in qiskit 2.2 and slated for removal in 3.0.

## When you cannot afford ideal simulation

For `n ≥ ~28` the ideal simulation step (`simulate_pmeasure`) becomes
impractical on a single workstation. Two mitigations:

- Use stabiliser-rank or MPS simulation when the circuit allows it
  (uniqc's `Simulator(backend_type="mps")` only handles linear
  topology; QV circuits are dense, so this rarely helps).
- For very wide hardware where ideal sim is genuinely infeasible,
  switch to **mirror-circuit benchmarking** (Proctor et al. 2021) or
  certified randomness extraction. Out of scope for this skill.
