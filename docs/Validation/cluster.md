# Validation: `src/mors/cluster.py`

## What this page checks

This page checks how MORS calculates statistical percentiles of stellar rotation in open clusters.
`Cluster` in `mors.cluster` holds a population of synthetic stars, and reports summary statistics of their rotation rates.
Validation means that a test runs the code on an analytical limit with a known exact solution, and checks the output within a tight tolerance.
If this part of the code is wrong, synthetic stars start at the wrong rotation rates.
The rotation history, magnetic activity, and high-energy radiation budget are then wrong in coupled simulations.

## Percentile of a uniform ramp

**Why this check exists.** An off-by-one error in percentile indexing, or a midpoint collapse, alters the rotation percentile without an error message. A user would then receive a wrong rotation rate for the requested percentile.

**What it tests.** `Cluster.Percentile` calculates the `q`-th percentile of an evenly spaced rotation-rate distribution running from `A` to `B`. Under linear interpolation, the exact percentile is `A + (B - A) * q / 100`, independent of the number of samples. The test builds an evenly spaced ramp, queries percentiles at `q` = 5, 50, and 95, and asserts agreement with the closed form. A companion `physics_invariant` test checks that the percentile mapping is monotone in `q`, and bounded within the distribution range.

**How we know the right answer.** The percentile of a uniform ramp is an analytical limit from the closed form `percentile(q) = A + (B - A) * q / 100`. A bug that returns the midpoint of the distribution differs from the analytical values by far more than the `rtol=1e-12` tolerance.

**Why it matters.** `src/mors/star.py` sets initial rotation rates from cluster percentiles. PROTEUS uses these percentiles when configuring initial stellar rotation tracks.

??? info "Test details"
    - Reference: closed form `A + (B - A) * q / 100`
    - Tolerance: `rtol=1e-12` at q = 5, 50 and 95
    - Test id: `tests/test_cluster.py::test_percentile_of_uniform_ramp_matches_closed_form`
    - Command: `pytest tests/test_cluster.py::test_percentile_of_uniform_ramp_matches_closed_form`

## Related code

- `src/mors/cluster.py`: `Cluster`, `Cluster.Percentile`, and the percentile inversion helper.
- `src/mors/star.py`: sets initial rotation rates from cluster percentiles.
- `tests/test_cluster.py`: `test_percentile_of_uniform_ramp_matches_closed_form` and companion monotonicity checks.
