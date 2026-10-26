# Validation: `src/mors/rotevo.py`

## What this page checks

This page checks the forward-Euler time step of `mors.rotevo`. Forward Euler advances a quantity by its rate of change times the time step.
The module integrates the coupled rotation of the stellar core and envelope forward in time under wind-braking torques.
Validation means that a test runs the code on a case with a known right answer and checks the result within a stated tolerance.
If this part of the code is wrong, the rotation history of the star is wrong, and so are the activity and the high-energy emission that MORS derives from it.
The case below says why the check exists, what it tests, how we know the right answer and why it matters; a box "Test details" ends the case.

## Forward-Euler step

**Why this check exists.** The integrator arithmetic can drop the time-step factor, reverse the sign of a step, or swap the core and envelope updates without an error message. The star would then spin up instead of braking, or evolve at the wrong rate.

**What it tests.** `Omega` is the angular rotation rate and `dAge` the time step. For a prescribed constant rate of change `r`, one explicit forward-Euler step gives `Omega_new = Omega + dAge * r`. The test replaces the rate function with fixed rates (`r = -2` for the envelope, `r = -1` for the core) and takes one step with `dAge = 0.5` from `Omega = 10`. The rotation rate of the envelope must become 9.0 and that of the core 9.5. Fixing the rates separates the integrator arithmetic from the physics of the rate law.

**How we know the right answer.** The single-step Euler update is a closed-form identity. A swapped update, a wrong sign or a missing time step misses it by far more than the `rtol=1e-12` tolerance. Other tests of the module check that a braking track spins down monotonically (a faster rotator brakes harder and stays positive), that a forward-Euler track reaches the requested final age, and that 2 tracks started at different rates keep their order.

**Why it matters.** `mors.star.Star` calls `rotevo.EvolveRotation` to compute the rotation history of the star. That rotation history sets stellar magnetic activity and high-energy emission.

**Known limit.** The test covers the forward-Euler step only. The default method is `RosenbrockFixed`, which PROTEUS uses through `mors.Star`, so this test does not protect the PROTEUS path. The other step methods are checked by tests that are not reference-pinned, such as `test_runge_kutta4_constant_rate_linear_update`.

??? info "Test details"
    - Reference: closed form `Omega_new = Omega + dAge * r`
    - Tolerance: `rtol=1e-12` on the envelope (9.0) and core (9.5) rates
    - Test id: `tests/test_rotevo.py::test_forward_euler_step_matches_analytic_update`
    - Command: `pytest tests/test_rotevo.py::test_forward_euler_step_matches_analytic_update`

## Related code

- `src/mors/rotevo.py`: `EvolveRotation` and the per-method step functions (forward Euler, Runge-Kutta, Runge-Kutta-Fehlberg, Rosenbrock).
- [Rotational evolution model](../Explanations/rotation.md) describes the torques and the integration scheme.
