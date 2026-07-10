# Validation: `src/mors/rotevo.py`

This page tracks the `@pytest.mark.reference_pinned` tests that anchor the
behaviour of `mors.rotevo` against an analytical limit.

| Test id | Reference | Scope |
|---|---|---|
| `tests/test_rotevo.py::test_forward_euler_step_matches_analytic_update` | Analytical limit: one explicit Euler step of a prescribed constant rate | Pins a single forward-Euler rotation step against the closed form `Omega_new = Omega + dAge * rate`, for a prescribed constant envelope and core rate. |

## Re-derivation note

`rotevo.py` integrates the coupled core and envelope rotation rates forward in
time under the spin-down torques. For a prescribed constant rate `r`, one
explicit forward-Euler step is exactly

```
Omega_new = Omega + dAge * r
```

The reference-pinned test mocks the rate function to return fixed rates
(`r = -2` for the envelope, `r = -1` for the core), takes one step with
`dAge = 0.5` from `Omega = 10`, and pins the result to `9.0` and `9.5`. This
isolates the integrator arithmetic from the physics of the rate law, so a wrong
step sign, a dropped timestep factor, or a swapped core and envelope update
fails against the closed form.

## Anchor type

Analytical limit. The single-step Euler update is a closed-form identity.
Companion `physics_invariant` tests cover the monotone spin-down of a braking
track (a faster rotator brakes harder and stays positive), the adaptive-step
integrators reaching the requested final age, and the ordering of two tracks
started at different rates.

## Cross-references

- `src/mors/rotevo.py`: `EvolveRotation` and the per-method step functions
  (forward Euler, Runge-Kutta, Runge-Kutta-Fehlberg, Rosenbrock).
- [Rotational evolution model](../Explanations/rotation.md) describes the
  torques and the integration scheme.
