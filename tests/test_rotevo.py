"""Tests for src/mors/rotevo.py.

Exercises the rotational-evolution solver: the top-level fitter
(``FitRotation``), the main age-integration loop (``EvolveRotation``), the
single-step dispatcher (``EvolveRotationStep``) and its five time-integration
backends (forward Euler, classical Runge-Kutta, Runge-Kutta-Fehlberg, and the
adaptive and fixed-grid Rosenbrock variants), plus the timestep, output-cadence,
linear-solve, and data-validation helpers.

The stellar-structure model that supplies the torque terms lives in
``mors.physicalmodel``; here it is mocked at the narrow scope of
``physicalmodel.dOmegadt`` so the integrators are exercised in isolation with a
prescribed braking law. The mock returns physically plausible spin-down rates
(negative, and, where the invariant is under test, scaling with the rotation
rate) so that sign and monotonicity bugs in the integrators are caught. The
angular-momentum sign convention (a braking torque strictly reduces the
rotation rate) and the analytical forward-Euler update are the anchors.

Anchor: spin-down braking law (forward-Euler analytical limit).
"""

from __future__ import annotations

import copy

import numpy as np
import pytest
from numpy.testing import assert_allclose

from mors import miscellaneous as misc
from mors import parameters, rotevo

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]


def make_params():
    """Return a private deep copy of the default parameter dictionary."""
    return copy.deepcopy(parameters.paramsDefault)


class FakeStarEvo:
    """Stand-in for ``mors.stellarevo.StarEvo`` that records loaded masses.

    The real class reads Spada tracks off disk; the integrators only call
    ``LoadTrack`` in the code paths under test (the physics is mocked), so a
    no-op loader is a faithful and fast substitute.
    """

    def __init__(self):
        self.loaded = []

    def LoadTrack(self, Mstar):
        self.loaded.append(Mstar)


def const_rate(rate_env, rate_core):
    """Build a ``dOmegadt`` mock returning fixed (age/omega-independent) rates."""

    def _fake(Mstar=None, Age=None, OmegaEnv=None, OmegaCore=None, params=None, StarEvo=None):
        return (rate_env, rate_core)

    return _fake


def cubic_brake(k):
    """Build a ``dOmegadt`` mock with a wind-braking law scaling as ``-k*Omega**3``.

    A faster rotator brakes harder under this law, which is the physical
    behaviour of an unsaturated magnetised wind.
    """

    def _fake(Mstar=None, Age=None, OmegaEnv=None, OmegaCore=None, params=None, StarEvo=None):
        return (-k * OmegaEnv**3, -k * OmegaCore**3)

    return _fake


def linear_brake(k):
    """Build a ``dOmegadt`` mock with a braking law scaling as ``-k*Omega``."""

    def _fake(Mstar=None, Age=None, OmegaEnv=None, OmegaCore=None, params=None, StarEvo=None):
        return (-k * OmegaEnv, -k * OmegaCore)

    return _fake


# ---------------------------------------------------------------------------
# _dAgeCalc
# ---------------------------------------------------------------------------


def test_dagecalc_clamps_to_maximum_step():
    """An over-long requested step is clamped to the parameter ceiling, not to zero.

    With no output-age list, the room-to-end-of-run is AgeMax - Age; a proposed
    step far larger than the ``dAgeMax`` ceiling must come back at the ceiling.
    """
    p = make_params()
    dAge, dAgeMax = rotevo._dAgeCalc(5000.0, 1.0, 1000.0, None, p)
    # Ceiling wins over the huge request.
    assert_allclose(dAge, p['dAgeMax'], rtol=1e-12)
    # Room-to-end is the raw span, before the per-step ceiling is applied.
    assert_allclose(dAgeMax, 999.0, rtol=1e-12)
    # A missing clamp would have left dAge at 5000, off by orders of magnitude.
    assert dAge < 5000.0


def test_dagecalc_clamps_to_minimum_step():
    """A vanishingly small requested step is floored at the minimum, not left at zero.

    Edge case: a step orders of magnitude below ``dAgeMin`` must be raised to
    the floor so the integrator cannot stall.
    """
    p = make_params()
    dAge, _ = rotevo._dAgeCalc(1.0e-9, 1.0, 1000.0, None, p)
    assert_allclose(dAge, p['dAgeMin'], rtol=1e-12)
    # A dropped floor would leave the sub-nanoyear step in place.
    assert dAge > 1.0e-9


def test_dagecalc_uses_next_output_age():
    """With an output-age array, the step is capped so the next output age is hit exactly.

    The maximum step becomes the distance to the first output age strictly
    greater than the current age.
    """
    p = make_params()
    ages_out = np.array([5.0, 10.0, 20.0])
    dAge, dAgeMax = rotevo._dAgeCalc(0.5, 3.0, 100.0, ages_out, p)
    # Distance to the next output age (5.0) from Age = 3.0.
    assert_allclose(dAgeMax, 2.0, rtol=1e-12)
    # The 0.5 request is below that cap, so it survives.
    assert_allclose(dAge, 0.5, rtol=1e-12)


def test_dagecalc_scalar_output_age():
    """A scalar output age sets the room-to-output directly (no array indexing path)."""
    p = make_params()
    dAge, dAgeMax = rotevo._dAgeCalc(0.5, 2.0, 100.0, 6.0, p)
    assert_allclose(dAgeMax, 4.0, rtol=1e-12)
    assert_allclose(dAge, 0.5, rtol=1e-12)


# ---------------------------------------------------------------------------
# _shouldAppend
# ---------------------------------------------------------------------------


def test_shouldappend_no_output_list_always_true():
    """With no output-age filter, every step is flagged for output."""
    returned, flag = rotevo._shouldAppend(3.14, None)
    assert flag is True
    # The (absent) filter is passed straight back unchanged.
    assert returned is None


def test_shouldappend_scalar_pins_present_behaviour():
    """Pins the present scalar-branch behaviour of the output-cadence check.

    This does NOT assert a proximity contract. The scalar branch evaluates
    ``abs(Age / AgesOut) - 1.0 < 1e-6`` (operator precedence groups the
    subtraction before the comparison), so it flags any Age at or below the
    target rather than only ages within 1e-6 of it, and rejects an Age that
    overshoots the target by more than a factor of ~1e-6. The assertions below
    record that actual behaviour; see the flagged source bug for the intended
    proximity form.
    """
    # Age well below the target: the present branch flags it True even though it
    # is nowhere near the target, which is the non-proximity behaviour.
    _, flag_far_below = rotevo._shouldAppend(5.0, 10.0)
    # Age above the target by more than the ~1e-6 margin: rejected.
    _, flag_above = rotevo._shouldAppend(10.0, 5.0)
    assert flag_far_below is True
    assert flag_above is False
    # A genuine proximity check would reject an Age three orders of magnitude
    # below the target; the present branch flags it, confirming it is not one.
    _, flag_tiny = rotevo._shouldAppend(1.0, 1.0e3)
    assert flag_tiny is True


def test_shouldappend_array_hit_removes_element():
    """A near-exact match to the leading output age is flagged and consumed.

    The matched age is deleted so the next call compares against the following
    output age; the returned array must be one element shorter.
    """
    ages_out = np.array([5.0, 10.0])
    returned, flag = rotevo._shouldAppend(5.0000001, ages_out)
    assert flag is True
    # The consumed leading age is removed.
    assert len(returned) == 1
    assert_allclose(returned[0], 10.0, rtol=1e-12)


def test_shouldappend_array_miss_keeps_element():
    """An age far from the leading output age is not flagged and nothing is consumed."""
    ages_out = np.array([5.0, 10.0])
    returned, flag = rotevo._shouldAppend(3.0, ages_out)
    assert flag is False
    # No element is consumed on a miss.
    assert len(returned) == 2


def test_shouldappend_nonascending_raises():
    """A non-ascending output-age array trips the ordering guard.

    Error contract: when the nearest output age is not the leading element the
    function raises rather than silently skipping an output.
    """
    ages_out = np.array([100.0, 2.0])
    with pytest.raises(Exception, match="indexMin is not zero"):
        rotevo._shouldAppend(2.0, ages_out)


# ---------------------------------------------------------------------------
# _GaussianElimination
# ---------------------------------------------------------------------------


def test_gaussian_elimination_matches_reference_solve():
    """The linear solver reproduces the numpy reference on a well-conditioned system.

    Uses an asymmetric right-hand side so a transpose or an index swap in the
    back-substitution would change the answer.
    """
    A = np.array([[4.0, 1.0], [2.0, 3.0]])
    b = np.array([1.0, 2.0])
    x = rotevo._GaussianElimination(A, b)
    reference = np.linalg.solve(A, b)
    assert_allclose(x, reference, rtol=1e-12)
    # Residual closure: A x = b to machine tolerance.
    assert_allclose(A @ x, b, atol=1e-12)


def test_gaussian_elimination_zero_pivot_raises():
    """A zero leading pivot trips the singular-diagonal guard.

    Error contract: the solver refuses a matrix with a zero on the diagonal
    rather than dividing by zero and returning nonsense.
    """
    A = np.array([[0.0, 1.0], [1.0, 0.0]])
    b = np.array([1.0, 1.0])
    with pytest.raises(Exception, match="diagonal term"):
        rotevo._GaussianElimination(A, b)


# ---------------------------------------------------------------------------
# _CheckBadData
# ---------------------------------------------------------------------------


def test_checkbaddata_accepts_valid_state():
    """Physically valid final entries pass the validator without raising.

    Boundary: rotation rates just above zero are acceptable; only non-positive
    values are rejected.
    """
    tracks = {
        'Age': np.array([1.0, 2.0]),
        'OmegaEnv': np.array([10.0, 1.0e-3]),
        'OmegaCore': np.array([10.0, 1.0e-3]),
    }
    assert rotevo._CheckBadData(tracks) is None
    # The validator does not mutate the tracks it inspects.
    assert len(tracks['OmegaEnv']) == 2


def test_checkbaddata_rejects_negative_rotation():
    """A non-positive envelope rotation rate is rejected.

    Error contract: negative angular velocity is unphysical and must halt the run.
    """
    tracks = {
        'Age': np.array([1.0]),
        'OmegaEnv': np.array([-1.0]),
        'OmegaCore': np.array([1.0]),
    }
    with pytest.raises(Exception, match="bad data"):
        rotevo._CheckBadData(tracks)


def test_checkbaddata_rejects_negative_core():
    """A non-positive core rotation rate is rejected even when the envelope is valid."""
    tracks = {
        'Age': np.array([1.0]),
        'OmegaEnv': np.array([1.0]),
        'OmegaCore': np.array([0.0]),
    }
    with pytest.raises(Exception, match="bad data"):
        rotevo._CheckBadData(tracks)


def test_checkbaddata_rejects_nan_and_inf():
    """NaN and infinite entries in any track are rejected.

    Edge case: a NaN passes the ``<= 0`` positivity test (NaN comparisons are
    False) yet must still be caught by the explicit finiteness check.
    """
    tracks_nan = {
        'Age': np.array([1.0]),
        'OmegaEnv': np.array([np.nan]),
        'OmegaCore': np.array([1.0]),
    }
    with pytest.raises(Exception, match="bad data"):
        rotevo._CheckBadData(tracks_nan)
    tracks_inf = {
        'Age': np.array([np.inf]),
        'OmegaEnv': np.array([1.0]),
        'OmegaCore': np.array([1.0]),
    }
    with pytest.raises(Exception, match="bad data"):
        rotevo._CheckBadData(tracks_inf)


# ---------------------------------------------------------------------------
# EvolveRotationStep dispatch and backends
# ---------------------------------------------------------------------------


def test_evolverotationstep_missing_arguments_raise():
    """Each mandatory argument is validated before any stepping occurs.

    Error contract: missing mass, age, either rotation rate, or both timestep
    controls raises; no partial state is produced.
    """
    with pytest.raises(Exception, match="Mstar"):
        rotevo.EvolveRotationStep(Age=1.0, OmegaEnv=1.0, OmegaCore=1.0, dAge=0.5)
    with pytest.raises(Exception, match="Age"):
        rotevo.EvolveRotationStep(Mstar=1.0, OmegaEnv=1.0, OmegaCore=1.0, dAge=0.5)
    with pytest.raises(Exception, match="OmegaEnv"):
        rotevo.EvolveRotationStep(Mstar=1.0, Age=1.0, OmegaCore=1.0, dAge=0.5)
    with pytest.raises(Exception, match="OmegaCore"):
        rotevo.EvolveRotationStep(Mstar=1.0, Age=1.0, OmegaEnv=1.0, dAge=0.5)
    with pytest.raises(Exception, match="dAge"):
        rotevo.EvolveRotationStep(Mstar=1.0, Age=1.0, OmegaEnv=1.0, OmegaCore=1.0)


def test_evolverotationstep_invalid_method_raises(monkeypatch):
    """An unrecognised integration method name is rejected.

    Error contract: the dispatcher raises rather than silently doing nothing.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0, -1.0))
    p = make_params()
    p['TimeIntegrationMethod'] = 'NotAMethod'
    with pytest.raises(Exception, match="invalid value of TimeIntegrationMethod"):
        rotevo.EvolveRotationStep(
            Mstar=1.0, Age=100.0, OmegaEnv=10.0, OmegaCore=10.0,
            dAge=0.5, dAgeMax=1.0, params=p, StarEvo=FakeStarEvo(),
        )


@pytest.mark.reference_pinned
@pytest.mark.physics_invariant
def test_forward_euler_step_matches_analytic_update(monkeypatch):
    """The forward-Euler step reproduces the closed-form linear update exactly.

    Analytical limit: for a prescribed constant rate ``r``, one explicit Euler
    step gives ``Omega_new = Omega + dAge * r`` exactly. With r = -2 (envelope)
    and r = -1 (core), dAge = 0.5, Omega = 10, the updates are 9.0 and 9.5.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-2.0, -1.0))
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    dAge, dAgeNew, env, core = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=10.0, OmegaCore=10.0,
        dAge=0.5, params=p, StarEvo=FakeStarEvo(),
    )
    assert_allclose(env, 9.0, rtol=1e-12)
    assert_allclose(core, 9.5, rtol=1e-12)
    # Sign guard: a wrong-sign torque would spin the star up past 10, not down.
    assert env < 10.0
    # Wrong-sign envelope result (11.0) differs from the correct 9.0 by 2 >> tol.
    assert abs(env - 11.0) > 1.0
    # Forward Euler reports back the fixed step it was handed.
    assert_allclose(dAgeNew, 0.5, rtol=1e-12)


@pytest.mark.physics_invariant
def test_forward_euler_faster_rotator_brakes_harder(monkeypatch):
    """Under a cubic wind-braking law the faster rotator loses more angular velocity.

    A braking rate scaling as ``-k*Omega**3`` decrements a five-times-faster
    rotator by 125 times as much over one step, the signature of an unsaturated
    magnetised wind. Edge contrast between a slow and a fast rotator.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', cubic_brake(1.0e-4))
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    _, _, env_slow, _ = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=1.0, OmegaCore=1.0,
        dAge=0.5, params=p, StarEvo=FakeStarEvo(),
    )
    _, _, env_fast, _ = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=5.0, OmegaCore=5.0,
        dAge=0.5, params=p, StarEvo=FakeStarEvo(),
    )
    drop_slow = 1.0 - env_slow
    drop_fast = 5.0 - env_fast
    # Both brake (positive drop) and the fast rotator brakes strictly harder.
    assert drop_slow > 0.0
    assert drop_fast > drop_slow
    # Cubic scaling: the fast-rotator drop is ~125x the slow-rotator drop.
    assert_allclose(drop_fast / drop_slow, 125.0, rtol=1e-9)


@pytest.mark.physics_invariant
def test_runge_kutta4_constant_rate_linear_update(monkeypatch):
    """Classical RK4 collapses to the exact linear update for a constant rate.

    When the rate does not vary over the step, the four RK4 stages are equal and
    the weighted average returns ``Omega + dAge * r``.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-2.0, -2.0))
    p = make_params()
    p['TimeIntegrationMethod'] = 'RungeKutta4'
    _, _, env, core = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=10.0, OmegaCore=10.0,
        dAge=0.5, params=p, StarEvo=FakeStarEvo(),
    )
    assert_allclose(env, 9.0, rtol=1e-12)
    # Envelope and core share the rate here, so they track each other.
    assert_allclose(env, core, rtol=1e-12)
    # Braking, not spin-up.
    assert env < 10.0


@pytest.mark.physics_invariant
def test_runge_kutta_fehlberg_step_brakes_and_adapts(monkeypatch):
    """The adaptive RKF step decreases the rotation rate and returns a positive next step.

    With a constant rate the embedded error vanishes, so the controller proposes
    a longer next step while still applying the braking increment.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0, -1.0))
    p = make_params()
    p['TimeIntegrationMethod'] = 'RungeKuttaFehlberg'
    dAge, dAgeNew, env, core = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=10.0, OmegaCore=10.0,
        dAge=0.5, dAgeMax=5.0, params=p, StarEvo=FakeStarEvo(),
    )
    # One step of a -1 rate over 0.5 Myr removes 0.5 from each rate.
    assert_allclose(env, 9.5, rtol=1e-9)
    assert env < 10.0
    # The adaptive controller returns a strictly positive proposed next step.
    assert dAgeNew > 0.0


@pytest.mark.physics_invariant
def test_rosenbrock_adaptive_step_brakes(monkeypatch):
    """The adaptive Rosenbrock step applies the braking increment and stays positive.

    Exercises the Jacobian assembly, the k-coefficient linear solves, and the
    adaptive step controller with a constant torque.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0e-2, -1.0e-2))
    p = make_params()
    p['TimeIntegrationMethod'] = 'Rosenbrock'
    _, dAgeNew, env, core = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=10.0, OmegaCore=10.0,
        dAge=0.5, dAgeMax=5.0, params=p, StarEvo=FakeStarEvo(),
    )
    # Rotation rate decreases under the braking torque.
    assert env < 10.0
    assert core < 10.0
    # A valid next timestep is proposed.
    assert dAgeNew > 0.0


@pytest.mark.physics_invariant
def test_rosenbrock_fixed_step_uses_age_scaled_step(monkeypatch):
    """The fixed-grid Rosenbrock step sizes its timestep from the age and brakes.

    The step is ``0.1 * Age**0.75`` capped by the ceiling; at Age = 100 that is
    well below the cap, so the returned step equals the age-scaled value.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0e-2, -1.0e-2))
    p = make_params()
    p['TimeIntegrationMethod'] = 'RosenbrockFixed'
    dAge, _, env, _ = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=10.0, OmegaCore=10.0,
        dAge=0.5, dAgeMax=50.0, params=p, StarEvo=FakeStarEvo(),
    )
    expected_step = 0.1 * 100.0**0.75
    assert_allclose(dAge, expected_step, rtol=1e-9)
    # The braking torque still lowers the rotation rate.
    assert env < 10.0


# ---------------------------------------------------------------------------
# EvolveRotation main loop
# ---------------------------------------------------------------------------


def test_evolverotation_requires_mstar():
    """The main loop refuses to run without a stellar mass.

    Error contract: mass is mandatory and its absence raises before any track
    is created.
    """
    with pytest.raises(Exception, match="Mstar"):
        rotevo.EvolveRotation(Omega0=1.0)


def test_evolverotation_rejects_inconsistent_rotation_arguments():
    """The rotation-argument contract rejects both under- and over-specification.

    Error contract: omitting all three rotation inputs, or setting both the
    lumped ``Omega0`` and a split envelope rate, are each rejected.
    """
    with pytest.raises(Exception, match="OmegaEnv0 and OmegaCore0"):
        rotevo.EvolveRotation(Mstar=1.0)
    with pytest.raises(Exception, match="neither OmegaEnv0 nor OmegaCore0"):
        rotevo.EvolveRotation(Mstar=1.0, Omega0=1.0, OmegaEnv0=1.0)


@pytest.mark.physics_invariant
def test_evolverotation_spins_down_monotonically(monkeypatch):
    """A braking torque drives a strictly decreasing, strictly positive spin-down track.

    Skumanich-like braking (rate scaling with Omega) must lower the envelope
    rotation rate at every recorded step while keeping it positive, and the
    integration must reach the requested final age.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', linear_brake(1.0e-2))
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    tracks = rotevo.EvolveRotation(
        Mstar=1.0, Omega0=10.0, AgeMin=1.0, AgeMax=11.0,
        params=p, StarEvo=FakeStarEvo(),
    )
    omega = tracks['OmegaEnv']
    # More than the initial sample is recorded.
    assert tracks['nAge'] > 1
    # Strictly monotone spin-down: every successive rate is lower.
    assert np.all(np.diff(omega) < 0.0)
    # Positivity of the whole track.
    assert np.all(omega > 0.0)
    # The loop advances to (just short of) the requested final age.
    assert tracks['Age'][-1] > 0.99 * 11.0


@pytest.mark.physics_invariant
def test_evolverotation_faster_start_ends_faster(monkeypatch):
    """Two spin-down runs preserve their ordering: the faster start stays faster.

    Under the same braking law a star launched at a higher initial rate ends the
    integration above one launched slower, and both end below their starts.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', linear_brake(1.0e-2))
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    slow = rotevo.EvolveRotation(
        Mstar=1.0, Omega0=2.0, AgeMin=1.0, AgeMax=11.0, params=p, StarEvo=FakeStarEvo(),
    )
    fast = rotevo.EvolveRotation(
        Mstar=1.0, Omega0=20.0, AgeMin=1.0, AgeMax=11.0, params=p, StarEvo=FakeStarEvo(),
    )
    assert fast['OmegaEnv'][-1] > slow['OmegaEnv'][-1]
    # Both have braked from their starting rates.
    assert fast['OmegaEnv'][-1] < 20.0
    assert slow['OmegaEnv'][-1] < 2.0


def test_evolverotation_split_core_envelope_start(monkeypatch):
    """Supplying separate envelope and core rates seeds the two reservoirs independently.

    Edge case: the lumped ``Omega0`` is omitted and the split path is taken; the
    first recorded core rate must equal the supplied core seed, not the envelope.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0e-3, -1.0e-3))
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    tracks = rotevo.EvolveRotation(
        Mstar=1.0, OmegaEnv0=8.0, OmegaCore0=12.0, AgeMin=1.0, AgeMax=4.0,
        params=p, StarEvo=FakeStarEvo(),
    )
    assert_allclose(tracks['OmegaEnv'][0], 8.0, rtol=1e-12)
    assert_allclose(tracks['OmegaCore'][0], 12.0, rtol=1e-12)
    # The two reservoirs start apart, confirming the split seed was honoured.
    assert tracks['OmegaCore'][0] > tracks['OmegaEnv'][0]


def test_evolverotation_default_rosenbrock_fixed(monkeypatch):
    """The default fixed-grid Rosenbrock path integrates a short braking track.

    Runs with the shipped default integration method (no override), exercising
    the Jacobian, k-coefficient, and Gaussian-elimination helpers inside the
    main loop.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0e-3, -1.0e-3))
    p = make_params()
    tracks = rotevo.EvolveRotation(
        Mstar=1.0, Omega0=10.0, AgeMin=1.0, AgeMax=30.0,
        params=p, StarEvo=FakeStarEvo(),
    )
    assert tracks['nAge'] > 1
    # Braking lowers the final rate below the start.
    assert tracks['OmegaEnv'][-1] < 10.0
    assert np.all(tracks['OmegaEnv'] > 0.0)


def test_evolverotation_output_age_array_filters_below_agemin(monkeypatch):
    """An output-age list is honoured and entries below the start age are dropped.

    Edge case: a requested output age younger than ``AgeMin`` (here 0.5 Myr vs a
    1 Myr start) must be discarded, and the final output age fixes ``AgeMax``.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0e-3, -1.0e-3))
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    tracks = rotevo.EvolveRotation(
        Mstar=1.0, Omega0=10.0, AgeMin=1.0, AgesOut=np.array([0.5, 6.0, 10.0]),
        params=p, StarEvo=FakeStarEvo(),
    )
    # Integration ends at the last requested output age.
    assert_allclose(tracks['Age'][-1], 10.0, atol=0.5)
    # The sub-AgeMin request (0.5) never appears in the output ages.
    assert np.min(tracks['Age']) >= 1.0


def test_evolverotation_scalar_output_age(monkeypatch):
    """A single scalar output age drives the run to that age.

    Edge case: ``AgesOut`` given as a bare float is normalised to a one-element
    array before the integration loop, so the run ends at that age via the array
    output-cadence path. The scalar helper branches inside ``_dAgeCalc`` and
    ``_shouldAppend`` are not reached from this entry point; this verifies the
    scalar-input normalisation and the final age, not those scalar branches.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0e-3, -1.0e-3))
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    tracks = rotevo.EvolveRotation(
        Mstar=1.0, Omega0=10.0, AgeMin=1.0, AgesOut=8.0,
        params=p, StarEvo=FakeStarEvo(),
    )
    assert_allclose(tracks['Age'][-1], 8.0, atol=0.5)
    assert tracks['OmegaEnv'][-1] < 10.0


def test_evolverotation_step_ceiling_raises(monkeypatch):
    """Exceeding the maximum-step budget halts the run.

    Error contract: a tiny ``nStepMax`` forces the loop past its budget before
    reaching the final age, and the guard raises.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0e-3, -1.0e-3))
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    p['nStepMax'] = 2
    with pytest.raises(Exception, match="too many timesteps"):
        rotevo.EvolveRotation(
            Mstar=1.0, Omega0=10.0, AgeMin=1.0, AgeMax=1000.0,
            params=p, StarEvo=FakeStarEvo(),
        )


def test_evolverotation_extended_tracks(monkeypatch):
    """Extended-track mode appends the auxiliary stellar quantities each step.

    With ``ExtendedTracks`` on, the auxiliary-quantity provider is mocked to
    return a small plausible activity set; those keys must appear in the output
    dictionary with one entry per recorded age.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0e-3, -1.0e-3))

    def fake_extended(Mstar=None, Age=None, OmegaEnv=None, OmegaCore=None,
                      params=None, StarEvo=None):
        # Include a core rotation-rate key so the appender exercises its
        # skip-if-already-present branch as well as the new-quantity branch.
        return {'OmegaEnv': OmegaEnv, 'Rstar': 0.95, 'Lx': 1.0e27}

    monkeypatch.setattr(rotevo.phys, 'ExtendedQuantities', fake_extended)
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    p['ExtendedTracks'] = True
    tracks = rotevo.EvolveRotation(
        Mstar=1.0, Omega0=10.0, AgeMin=1.0, AgeMax=4.0,
        params=p, StarEvo=FakeStarEvo(),
    )
    # The auxiliary quantities are carried alongside the rotation tracks.
    assert 'Rstar' in tracks
    assert len(tracks['Rstar']) == tracks['nAge']
    assert_allclose(tracks['Rstar'][0], 0.95, rtol=1e-12)


# ---------------------------------------------------------------------------
# FitRotation
# ---------------------------------------------------------------------------


def test_fitrotation_requires_mstar_and_omega():
    """The fitter validates its two mandatory inputs.

    Error contract: neither stellar mass nor the target rotation rate may be
    omitted.
    """
    with pytest.raises(Exception, match="Mstar"):
        rotevo.FitRotation(Omega=1.0)
    with pytest.raises(Exception, match="Omega"):
        rotevo.FitRotation(Mstar=1.0)


def _patch_linear_fit(monkeypatch):
    """Replace EvolveRotation with a monotone map: final rate is half of Omega0."""

    def fake_evolve(Mstar=None, Omega0=None, AgeMin=None, AgeMax=None,
                    params=None, StarEvo=None):
        return {'OmegaEnv': np.array([Omega0, 0.5 * Omega0])}

    monkeypatch.setattr(rotevo, 'EvolveRotation', fake_evolve)


def test_fitrotation_recovers_initial_rate(monkeypatch):
    """Bisection recovers the initial rate that reproduces a target present-day rate.

    With a final-rate map of half the initial rate, a target of 5 must come from
    an initial rate of 10. The bisection converges to that value within the fit
    tolerance.
    """
    _patch_linear_fit(monkeypatch)
    p = make_params()
    # Pass an explicit start age so the caller-supplied-AgeMin branch is taken.
    omega0 = rotevo.FitRotation(
        Mstar=1.0, Age=1000.0, Omega=5.0, AgeMin=1.0, params=p, StarEvo=FakeStarEvo(),
    )
    assert_allclose(omega0, 10.0, rtol=1e-3)
    # The recovered initial rate is well above the target it maps down to, so a
    # bug that returned the target itself (5.0) would miss by ~5 >> tolerance.
    assert abs(omega0 - 5.0) > 1.0


def test_fitrotation_converges_on_bracket_collapse(monkeypatch):
    """An unreachable in-range target is resolved when the search bracket collapses.

    Edge case: the evolution map has a discontinuity, so a target that lands in
    the gap between the two branches is never matched by value; the bisection
    instead terminates when the min and max initial rates converge, returning the
    collapse point rather than a no-solution sentinel.
    """

    def fake_gap(Mstar=None, Omega0=None, AgeMin=None, AgeMax=None,
                 params=None, StarEvo=None):
        # Lower branch reaches finals up to ~5; upper branch starts at ~10,
        # leaving the interval (5, 10) unreachable.
        final = 0.5 * Omega0 if Omega0 < 10.0 else 0.5 * Omega0 + 5.0
        return {'OmegaEnv': np.array([Omega0, final])}

    monkeypatch.setattr(rotevo, 'EvolveRotation', fake_gap)
    p = make_params()
    result = rotevo.FitRotation(
        Mstar=1.0, Age=1000.0, Omega=7.0, params=p, StarEvo=FakeStarEvo(),
    )
    # A real (non-sentinel) initial rate is returned at the discontinuity near 10.
    assert result > 0.0
    assert_allclose(result, 10.0, atol=0.5)


def test_fitrotation_below_range_returns_minus_one(monkeypatch):
    """A target below the reachable minimum returns the -1 sentinel.

    Edge case: a target rate under the floor set by ``Omega0FitMin`` cannot be
    fit and the documented sentinel is returned.
    """
    _patch_linear_fit(monkeypatch)
    p = make_params()
    result = rotevo.FitRotation(
        Mstar=1.0, Age=1000.0, Omega=0.01, params=p, StarEvo=FakeStarEvo(),
    )
    assert result == -1
    assert result < 0


def test_fitrotation_above_range_returns_minus_two(monkeypatch):
    """A target above the reachable maximum returns the -2 sentinel.

    Edge case: a target above the ceiling set by ``Omega0FitMax`` cannot be fit.
    """
    _patch_linear_fit(monkeypatch)
    p = make_params()
    result = rotevo.FitRotation(
        Mstar=1.0, Age=1000.0, Omega=100.0, params=p, StarEvo=FakeStarEvo(),
    )
    assert result == -2
    # Distinct from the below-range sentinel, so the two failure modes are separable.
    assert result < -1


def test_fitrotation_no_convergence_returns_minus_three(monkeypatch):
    """Exhausting the iteration budget without convergence returns the -3 sentinel.

    Edge case: with zero allowed bisection steps the in-range target can never be
    matched, so the no-solution sentinel is returned.
    """
    _patch_linear_fit(monkeypatch)
    p = make_params()
    p['nStepMaxFit'] = 0
    result = rotevo.FitRotation(
        Mstar=1.0, Age=1000.0, Omega=5.0, params=p, StarEvo=FakeStarEvo(),
    )
    assert result == -3
    assert result < 0


# ---------------------------------------------------------------------------
# Default-StarEvo and adaptive-solver branch coverage
# ---------------------------------------------------------------------------


def test_evolverotationstep_builds_default_starevo(monkeypatch):
    """Omitting the StarEvo instance loads a default one rather than failing.

    Edge case: with ``StarEvo=None`` the step must construct its own model. The
    real constructor is replaced by a no-op stand-in so the branch runs without
    disk access, and the braking update still applies.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-2.0, -2.0))
    monkeypatch.setattr(rotevo.SE, 'StarEvo', FakeStarEvo)
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    _, _, env, core = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=10.0, OmegaCore=10.0, dAge=0.5, params=p,
    )
    assert_allclose(env, 9.0, rtol=1e-12)
    assert core < 10.0


def test_evolverotation_builds_default_starevo_and_agemin(monkeypatch):
    """The main loop supplies its own StarEvo and start age when both are omitted.

    Edge case: ``StarEvo=None`` and ``AgeMin=None`` take the default-construction
    and default-start-age branches; the run still produces a positive, braked
    track.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(-1.0e-3, -1.0e-3))
    monkeypatch.setattr(rotevo.SE, 'StarEvo', FakeStarEvo)
    p = make_params()
    p['TimeIntegrationMethod'] = 'ForwardEuler'
    tracks = rotevo.EvolveRotation(Mstar=1.0, Omega0=10.0, AgeMax=4.0, params=p)
    assert tracks['nAge'] > 1
    assert np.all(tracks['OmegaEnv'] > 0.0)
    assert tracks['OmegaEnv'][-1] < 10.0


def test_fitrotation_builds_default_starevo_and_agemin(monkeypatch):
    """The fitter constructs a default StarEvo and start age when both are omitted.

    Edge case: ``StarEvo=None`` and ``AgeMin=None`` take the default branches
    while the evolution map is mocked, and bisection still recovers the initial
    rate.
    """
    monkeypatch.setattr(rotevo.SE, 'StarEvo', FakeStarEvo)
    _patch_linear_fit(monkeypatch)
    p = make_params()
    omega0 = rotevo.FitRotation(Mstar=1.0, Age=1000.0, Omega=5.0, params=p)
    assert_allclose(omega0, 10.0, rtol=1e-3)
    # A returned target-value (5.0) would miss the true initial rate by ~5.
    assert abs(omega0 - 5.0) > 1.0


def test_runge_kutta_fehlberg_nonzero_error_controls_step(monkeypatch):
    """A rotation-dependent rate gives a non-zero embedded error and drives adaption.

    With a braking law that varies over the step, the fifth- and fourth-order
    RKF estimates differ, so the non-degenerate step-control branch is taken; the
    star still brakes and a positive next step is proposed.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', linear_brake(1.0e-3))
    p = make_params()
    p['TimeIntegrationMethod'] = 'RungeKuttaFehlberg'
    _, dAgeNew, env, core = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=10.0, OmegaCore=10.0,
        dAge=0.5, dAgeMax=5.0, params=p, StarEvo=FakeStarEvo(),
    )
    assert env < 10.0
    assert core < 10.0
    assert dAgeNew > 0.0


def test_rosenbrock_nonzero_error_controls_step(monkeypatch):
    """A rotation-dependent rate gives a non-zero Rosenbrock error estimate.

    The high- and low-order Rosenbrock updates differ under a varying torque, so
    the error-driven step-factor branch runs rather than the zero-error shortcut;
    the star brakes and a positive next step is proposed.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', linear_brake(1.0e-3))
    p = make_params()
    p['TimeIntegrationMethod'] = 'Rosenbrock'
    _, dAgeNew, env, core = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=10.0, OmegaCore=10.0,
        dAge=0.5, dAgeMax=5.0, params=p, StarEvo=FakeStarEvo(),
    )
    assert env < 10.0
    assert core < 10.0
    assert dAgeNew > 0.0


@pytest.mark.physics_invariant
def test_rosenbrock_zero_torque_conserves_rotation(monkeypatch):
    """With no torque the adaptive Rosenbrock step conserves the rotation rate.

    Conservation limit: a null braking law leaves both reservoirs unchanged, and
    the zero-error step-control shortcut is taken.
    """
    monkeypatch.setattr(rotevo.phys, 'dOmegadt', const_rate(0.0, 0.0))
    p = make_params()
    p['TimeIntegrationMethod'] = 'Rosenbrock'
    _, dAgeNew, env, core = rotevo.EvolveRotationStep(
        Mstar=1.0, Age=100.0, OmegaEnv=10.0, OmegaCore=7.0,
        dAge=0.5, dAgeMax=5.0, params=p, StarEvo=FakeStarEvo(),
    )
    # No torque, no change: angular velocity is conserved for both reservoirs.
    assert_allclose(env, 10.0, rtol=1e-10)
    assert_allclose(core, 7.0, rtol=1e-10)
    assert dAgeNew > 0.0


# ---------------------------------------------------------------------------
# _getIndexGT sanity (used by the timestep helper)
# ---------------------------------------------------------------------------


def test_getindexgt_returns_first_greater():
    """The ascending-array index helper returns the first strictly-greater entry.

    Confirms the contract the timestep helper depends on: the next output age is
    the first array element above the current age, and an at-or-below query does
    not select an earlier element.
    """
    arr = np.array([1.0, 5.0, 10.0])
    assert misc._getIndexGT(arr, 3.0) == 1
    assert misc._getIndexGT(arr, 0.0) == 0
