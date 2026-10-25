# Validation: `src/mors/rotevo.py`

## What this page checks

This page checks the time-stepping integrators in `mors.rotevo`.
The module integrates the coupled rotation of the stellar core and envelope forward in time under wind-braking torques.
Validation means that a test runs the code on an analytical limit with a known exact solution, and checks the output to a tight tolerance.
If this part of the code is wrong, stellar rotation rates and spin-down timescales are incorrect.
The resulting magnetic activity and high-energy emission histories in coupled planetary evolution models are then wrong.

## Forward-Euler step

**Why this check exists.** Integrator arithmetic can drop a timestep factor, reverse a torque sign, or swap core and envelope updates without raising an error. The star would then spin up instead of braking, or evolve at the wrong rate.

**What it tests.** For a prescribed constant rate `r`, one explicit forward-Euler step gives `Omega_new = Omega + dAge * r`. The test mocks constant braking rates (`r = -2` for envelope, `r = -1` for core) and takes one step with `dAge = 0.5` from `Omega = 10`. It asserts that the envelope rate updates to 9.0 and the core rate updates to 9.5. Companion `physics_invariant` tests verify monotone spin-down, adaptive-step convergence, and track ordering for different initial rotation rates.

**How we know the right answer.** The single-step Euler update is an analytical closed-form identity. A swapped update or sign error fails against the exact linear solution by far more than the `rtol=1e-12` tolerance.

**Why it matters.** `mors.star.Star` calls `rotevo.EvolveRotation` to compute the rotation history of the star. That rotation history sets stellar magnetic activity and high-energy emission.

??? info "Test details"
    - Reference: closed form `Omega_new = Omega + dAge * r`
    - Tolerance: `rtol=1e-12` on the envelope (9.0) and core (9.5) rates
    - Test id: `tests/test_rotevo.py::test_forward_euler_step_matches_analytic_update`
    - Command: `pytest tests/test_rotevo.py::test_forward_euler_step_matches_analytic_update`

## Related code

- `src/mors/rotevo.py`: `EvolveRotation` and the per-method step functions (forward Euler, Runge-Kutta, Runge-Kutta-Fehlberg, Rosenbrock).
- [Rotational evolution model](../Explanations/rotation.md) describes the torques and the integration scheme.
