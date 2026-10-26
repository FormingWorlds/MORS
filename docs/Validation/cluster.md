# Validation: `src/mors/cluster.py`

## What this page checks

This page checks how the `Cluster` class of MORS reports percentiles of stellar rotation.
`Cluster` in `mors.cluster` holds a population of stars and reports statistics of their rotation rates.
Validation means that a test runs the code on a case with a known right answer and checks the result within a stated tolerance.
If this part of the code is wrong, a user of `Cluster` gets a wrong rotation rate for a requested percentile.
The case below says why the check exists, what it tests, how we know the right answer and why it matters; a box "Test details" ends the case.

## Percentile of a uniform ramp

**Why this check exists.** An off-by-one error in percentile indexing, or a midpoint collapse, alters the rotation percentile without an error message. A user would then receive a wrong rotation rate for the requested percentile.

**What it tests.** `Cluster.Percentile` calculates the `q`-th percentile of an evenly spaced rotation-rate distribution running from `A` to `B`. Under linear interpolation, the exact percentile is `A + (B - A) * q / 100`, independent of the number of samples. The test builds an evenly spaced ramp, queries percentiles at `q` = 5, 50, and 95, and asserts agreement with the closed form. A companion test, `test_percentile_maps_percentile_to_rotation_monotonically`, checks that the percentile rises with `q` and stays within the range of the distribution.

**How we know the right answer.** The percentile of a uniform ramp is an analytical limit from the closed form `percentile(q) = A + (B - A) * q / 100`. A bug that returns the midpoint of the distribution differs from the analytical values by far more than the `rtol=1e-12` tolerance.

**Why it matters.** `Cluster.Percentile` is the percentile interface of a star population in MORS ([Using model percentiles for initial rotation](../How-to/distribution_percentile.md)).

**Known limit.** `Star` and PROTEUS do not use `Cluster.Percentile`: `star.Percentile` sets the initial rotation of a single star with `np.percentile` over `misc.ModelCluster`, which this test does not cover.

??? info "Test details"
    - Reference: closed form `A + (B - A) * q / 100`
    - Tolerance: `rtol=1e-12` at q = 5, 50 and 95
    - Test id: `tests/test_cluster.py::test_percentile_of_uniform_ramp_matches_closed_form`
    - Command: `pytest tests/test_cluster.py::test_percentile_of_uniform_ramp_matches_closed_form`

## Related code

- `src/mors/cluster.py`: the `Cluster` class, `Cluster.Percentile`, and the per-quantity accessors that delegate to the member stars.
- `src/mors/star.py`: `Percentile`, the separate percentile path of a single star.
- [Using model percentiles for initial rotation](../How-to/distribution_percentile.md) describes the rotation distribution and the percentile interface.
