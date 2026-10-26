# Validation: `src/mors/cluster.py`

## What this page checks

This page checks how the `Cluster` class of MORS reports percentiles of stellar rotation.
`Cluster` in `mors.cluster` holds a population of stars and reports statistics of their rotation rates.
Validation means that a test runs the code on a case with a known right answer and checks the result within a stated tolerance.
If this part of the code is wrong, a user of `Cluster` gets a wrong rotation rate for a requested percentile.
The case below says why the check exists, what it tests, how we know the right answer and why it matters; a box "Test details" ends the case.

## Percentile of a uniform ramp

**Why this check exists.** `Cluster.Percentile` collects the surface rotation rates of all member stars at an age, rescaled by their spin-down, and hands them to the percentile routine. A wrong collection or a wrong dispatch, for example one that returns the middle of the distribution for every request, gives a wrong rotation rate without an error message.

**What it tests.** The test builds a cluster of 8 stars whose initial rotation rates are evenly spaced from $A$ = 1 to $B$ = 40 times the solar rotation rate. At an age of 200 Myr every star is spun down by the same factor, so the distribution stays evenly spaced. For an evenly spaced distribution from $A$ to $B$, the `q`-th percentile under linear interpolation is exactly `A + (B - A) * q / 100`, whatever the number of stars. The test asks for `q` = 5, 50 and 95 and compares each with this value. It also checks that the 5th and 95th percentiles are more than 1 away from the middle of the distribution.

**How we know the right answer.** The percentile of an evenly spaced distribution is a closed-form result.

**Why it matters.** `Cluster.Percentile` is the percentile interface of a star population in MORS ([Using model percentiles for initial rotation](../How-to/distribution_percentile.md)).

**Known limit.** The test replaces the percentile routine `star.Percentile` with a stand-in that calls `np.percentile`, so it checks how `Cluster.Percentile` collects and passes the rates, not the percentile code of MORS. `Star` and PROTEUS take the initial rotation of a single star from `star.Percentile` directly, which this test does not cover. A companion test, `test_percentile_maps_percentile_to_rotation_monotonically`, checks that the percentile rises with `q` and stays within the range of the distribution.

??? info "Test details"
    - Reference: closed form `A + (B - A) * q / 100`
    - Tolerance: `rtol=1e-12` at q = 5, 50 and 95
    - Test id: `tests/test_cluster.py::test_percentile_of_uniform_ramp_matches_closed_form`
    - Command: `pytest tests/test_cluster.py::test_percentile_of_uniform_ramp_matches_closed_form`

## Related code

- `src/mors/cluster.py`: the `Cluster` class, `Cluster.Percentile`, and the per-quantity accessors that delegate to the member stars.
- `src/mors/star.py`: `Percentile`, the separate percentile path of a single star.
- [Using model percentiles for initial rotation](../How-to/distribution_percentile.md) describes the rotation distribution and the percentile interface.
