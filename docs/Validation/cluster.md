# Validation: `src/mors/cluster.py`

This page tracks the `@pytest.mark.reference_pinned` tests that anchor the
behaviour of `mors.cluster` against an analytical limit.

| Test id | Reference | Scope |
|---|---|---|
| `tests/test_cluster.py::test_percentile_of_uniform_ramp_matches_closed_form` | Analytical limit: the percentile of an evenly spaced distribution | Pins the `Cluster.Percentile` output for an evenly spaced rotation-rate distribution to the closed form `A + (B - A) * q / 100`. |

## Re-derivation note

`Cluster` holds a population of stars and reports statistics of their rotation
distribution. For an evenly spaced distribution running from `A` to `B`, the
`q`-th percentile under linear interpolation is exactly

```
percentile(q) = A + (B - A) * q / 100
```

independent of the number of samples. The reference-pinned test builds a
cluster whose initial rotation rates form an evenly spaced ramp, queries the
percentile at a chosen `q`, and pins the result to that closed form. A
midpoint-collapse or an off-by-one in the percentile index moves the result
away from the analytic value.

## Anchor type

Analytical limit. The percentile of a uniform ramp is a closed-form identity.
A companion `physics_invariant` test checks that the percentile mapping is
monotone in `q` and bounded within the distribution range.

## Cross-references

- `src/mors/cluster.py`: the `Cluster` class, `Cluster.Percentile`, and the
  per-quantity accessors that delegate to the member stars.
- [Using model percentiles for initial rotation](../How-to/distribution_percentile.md)
  describes the rotation distribution and the percentile interface.
