"""Tests for src/mors/physicalmodel.py.

Exercises the rotation-activity and high-energy emission model: the
core-envelope rotation-rate derivatives, the saturated / unsaturated X-ray
scaling, the EUV and Lyman-alpha band relations, the wind and core-envelope
torque terms, the Rossby number, the breakup rotation rate, and the
Kopparapu et al. (2013) habitable-zone boundaries.

The invariants asserted here are: positivity of luminosities, fluxes, radii,
and Rossby numbers; band conservation (Lxuv = Lx + Leuv, Leuv = Leuv1 + Leuv2);
monotonicity of the saturation relation (a fast rotator emits more X-rays than
a slow one at fixed bolometric luminosity); the habitable-zone ordering
(inner boundary inside outer boundary); and a reference-pinned check against the
saturated X-ray-to-bolometric ratio of Johnstone et al. (2020) and the runaway
greenhouse limit of Kopparapu et al. (2013).

The real Spada track model is replaced by a stand-in returning plausible
solar-type structural values so every test runs in the unit tier without the
FWL_DATA tracks. Units follow the source: mass in Msun, age in Myr, rotation in
OmegaSun (2.67e-6 rad/s), luminosity in erg/s, radius in Rsun.
"""

from __future__ import annotations

import copy

import numpy as np
import pytest
from numpy.testing import assert_allclose

import mors.constants as const
import mors.parameters as parameters
import mors.physicalmodel as pm

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]


class FakeStarEvo:
    """Stand-in for the Spada track model returning plausible solar-type values.

    Every method ignores its arguments and returns a fixed physically plausible
    value in the unit the source expects, so the pure-math emission and torque
    code can be exercised without the real evolutionary tracks.
    """

    def Rstar(self, Mstar, Age):
        return 1.0  # Rsun

    def tauConv(self, Mstar, Age):
        return 30.0  # days

    def Itotal(self, Mstar, Age):
        return 6.0e53  # g cm^2

    def Ienv(self, Mstar, Age):
        return 5.0e53  # g cm^2

    def Icore(self, Mstar, Age):
        return 1.0e53  # g cm^2

    def dItotaldt(self, Mstar, Age):
        return 1.0e40  # g cm^2 per Myr

    def dIenvdt(self, Mstar, Age):
        return -5.0e39  # g cm^2 per Myr

    def dIcoredt(self, Mstar, Age):
        return 5.0e39  # g cm^2 per Myr

    def Rcore(self, Mstar, Age):
        return 0.2  # Rsun

    def dMcoredt(self, Mstar, Age):
        return 1.0e-9  # Msun per Myr

    def Lbol(self, Mstar, Age):
        return 1.0  # Lsun

    def Teff(self, Mstar, Age):
        return 5700.0  # K


def _default_params():
    """Return a deep copy of the default parameter dictionary for local edits."""
    return copy.deepcopy(parameters.paramsDefault)


def _plausible_starstate():
    """Build a StarState dict with the fields the emission helpers read.

    Fx is set to an active-Sun value (~1e5 erg/s/cm^2), Rstar to 1 Rsun, and
    Lbol to a solar bolometric luminosity in erg/s, so the EUV and Lyman-alpha
    power laws land in a physically sensible range.
    """
    return {
        'Ro': 0.5,
        'Rstar': 1.0,  # Rsun
        'Lbol': const.LbolSun,  # erg/s
        'Fx': 1.0e5,  # erg/s/cm^2
    }


class TestRossbyAndConversions:
    """Rossby number and period / angular-velocity conversions."""

    def test_rossby_number_is_positive_ratio_of_period_to_turnover(self):
        """Rossby number is the rotation period divided by the convective turnover time."""
        state = {'Prot': 12.0, 'tauConv': 30.0}  # days over days
        ro = pm._Ro(state)
        assert ro > 0.0
        assert_allclose(ro, 12.0 / 30.0, rtol=1e-12)
        # A swapped ratio (turnover over period) would give 2.5, far from 0.4.
        assert abs(ro - 30.0 / 12.0) > 1.0

    def test_period_and_omega_are_inverse_transforms(self):
        """Converting Omega to a period and back recovers the original rotation rate."""
        omega = 3.0  # OmegaSun
        prot = pm._Prot(omega)
        omega_back = pm._Omega(prot)
        assert prot > 0.0
        assert_allclose(omega_back, omega, rtol=1e-12)
        # A missing 2*pi factor would move the period by more than an order of magnitude.
        assert abs(prot - 1.0 / (omega * const.OmegaSun) / const.day) > 1.0

    def test_omega_from_period_matches_closed_form(self):
        """A one-day rotation period maps to a large multiple of the solar rotation rate."""
        prot = 1.0  # day
        omega = pm._Omega(prot)
        expected = 2.0 * const.Pi / (prot * const.day) / const.OmegaSun
        assert omega > 0.0
        assert_allclose(omega, expected, rtol=1e-12)
        # The Sun rotates once per ~25 days, so a 1-day period is many OmegaSun.
        assert omega > 10.0


class TestXrayRegimes:
    """Saturated and unsaturated X-ray scaling with Rossby number."""

    @pytest.mark.physics_invariant
    def test_fast_rotator_emits_more_xrays_than_slow_rotator(self):
        """The saturated fast rotator has a higher X-ray-to-bolometric ratio than a slow one.

        A fast rotator (small Rossby number, below the saturation threshold) sits
        on the flat saturated branch, while a slow rotator (large Rossby number)
        falls on the steep unsaturated branch, so its Rx is far smaller.
        """
        params = _default_params()
        fast = _plausible_starstate()
        fast['Ro'] = 0.5 * params['RoSatXray']  # saturated branch
        slow = _plausible_starstate()
        slow['Ro'] = 10.0 * params['RoSatXray']  # unsaturated branch
        Lx_fast, Fx_fast, Rx_fast = pm._Xray(fast, params=params)
        Lx_slow, Fx_slow, Rx_slow = pm._Xray(slow, params=params)
        # Positivity of every returned quantity.
        assert Rx_fast > 0.0 and Rx_slow > 0.0
        assert Lx_fast > 0.0 and Fx_fast > 0.0
        # The saturated rotator outshines the slow rotator by a wide margin.
        assert Rx_fast > 5.0 * Rx_slow
        # Luminosity is the bolometric luminosity times the activity ratio.
        assert_allclose(Lx_fast, fast['Lbol'] * Rx_fast, rtol=1e-12)

    @pytest.mark.reference_pinned
    @pytest.mark.physics_invariant
    def test_saturated_xray_ratio_matches_johnstone_value(self):
        """At the saturation threshold the X-ray-to-bolometric ratio equals the pinned value.

        Reference: Johnstone et al. (2020), saturated Rx = 5.135e-4 at the
        saturation Rossby number, calibrated on the Spada et al. (2013) models.
        At Ro = RoSatXray the piecewise relation is continuous and returns
        exactly this ratio.
        """
        params = _default_params()
        state = _plausible_starstate()
        state['Ro'] = params['RoSatXray']  # exactly at the saturation threshold
        Lx, Fx, Rx = pm._Xray(state, params=params)
        # Pinned saturated activity ratio.
        assert_allclose(Rx, 5.135e-4, rtol=1e-6)
        # Sign guard: an activity ratio is strictly positive.
        assert Rx > 0.0
        # Scale guard: a cgs-vs-SI or exponent slip would leave this window.
        assert 1.0e-4 < Rx < 1.0e-3
        # Flux is the luminosity spread over the stellar surface.
        expected_Fx = Lx / (4.0 * const.Pi * (state['Rstar'] * const.Rsun) ** 2.0)
        assert_allclose(Fx, expected_Fx, rtol=1e-12)

    @pytest.mark.physics_invariant
    def test_coronal_temperature_rises_with_xray_flux(self):
        """Coronal temperature follows the Johnstone and Guedel (2015) power law of Fx."""
        cool = {'Fx': 1.0e3}
        hot = {'Fx': 1.0e7}
        Tcor_cool = pm._Tcor(cool)
        Tcor_hot = pm._Tcor(hot)
        assert Tcor_cool > 0.0
        # A four-decade rise in Fx raises Tcor through the 0.26 power law.
        assert Tcor_hot > Tcor_cool
        assert_allclose(Tcor_hot, 0.11 * hot['Fx'] ** 0.26, rtol=1e-12)


class TestBandRelations:
    """EUV and Lyman-alpha band luminosities derived from the X-ray flux."""

    @pytest.mark.physics_invariant
    def test_euv_bands_are_positive_and_sum_to_total(self):
        """The two EUV sub-bands are positive and add to the combined EUV band.

        The 10-36 nm and 36-92 nm sub-bands are computed from the X-ray flux, and
        the combined 10-92 nm band must equal their sum exactly.
        """
        state = _plausible_starstate()
        state['Leuv1'], state['Feuv1'], state['Reuv1'] = pm._EUV1(state)
        state['Leuv2'], state['Feuv2'], state['Reuv2'] = pm._EUV2(state)
        Leuv, Feuv, Reuv = pm._EUV(state)
        assert state['Leuv1'] > 0.0 and state['Leuv2'] > 0.0
        # Band conservation: the total is the sum of the two sub-bands.
        assert_allclose(Leuv, state['Leuv1'] + state['Leuv2'], rtol=1e-12)
        assert_allclose(Feuv, state['Feuv1'] + state['Feuv2'], rtol=1e-12)
        assert_allclose(Reuv, state['Reuv1'] + state['Reuv2'], rtol=1e-12)

    @pytest.mark.physics_invariant
    def test_euv1_luminosity_is_flux_times_surface_area(self):
        """The 10-36 nm luminosity is its surface flux integrated over the stellar surface."""
        state = _plausible_starstate()
        Leuv1, Feuv1, Reuv1 = pm._EUV1(state)
        assert Feuv1 > 0.0
        area = 4.0 * const.Pi * (state['Rstar'] * const.Rsun) ** 2.0
        assert_allclose(Leuv1, Feuv1 * area, rtol=1e-12)
        # The activity ratio is the band luminosity over the bolometric one.
        assert_allclose(Reuv1, Leuv1 / state['Lbol'], rtol=1e-12)

    @pytest.mark.physics_invariant
    def test_lyman_alpha_scales_with_xray_flux(self):
        """Lyman-alpha luminosity grows with X-ray flux through the Johnstone (2020) law.

        Two X-ray flux levels four decades apart give strictly increasing
        Lyman-alpha luminosity, and each is positive.
        """
        low = _plausible_starstate()
        low['Fx'] = 1.0e3
        high = _plausible_starstate()
        high['Fx'] = 1.0e7
        Lly_low, Fly_low, Rly_low = pm._Lymanalpha(low)
        Lly_high, Fly_high, Rly_high = pm._Lymanalpha(high)
        assert Lly_low > 0.0 and Fly_low > 0.0
        # Monotonic rise with X-ray flux.
        assert Lly_high > Lly_low
        assert_allclose(Fly_low, 10.0 ** (3.97 + 0.375 * np.log10(low['Fx'])), rtol=1e-12)


class TestLxuvAssembly:
    """The public Lxuv / Lx / Leuv / Lly wrappers and their argument contract."""

    @pytest.mark.physics_invariant
    def test_lxuv_conserves_band_budget(self):
        """The assembled XUV dictionary satisfies Lxuv = Lx + Leuv and Reuv = Reuv1 + Reuv2."""
        star_evo = FakeStarEvo()
        out = pm.Lxuv(Mstar=1.0, Age=100.0, Omega=1.0, StarEvo=star_evo)
        assert out['Lx'] > 0.0 and out['Leuv'] > 0.0
        # Band conservation across the XUV budget.
        assert_allclose(out['Lxuv'], out['Lx'] + out['Leuv'], rtol=1e-12)
        assert_allclose(out['Reuv'], out['Reuv1'] + out['Reuv2'], rtol=1e-12)
        assert_allclose(out['Fxuv'], out['Fx'] + out['Feuv'], rtol=1e-12)

    def test_lxuv_accepts_period_or_omegaenv_equivalently(self):
        """Specifying rotation as a period matches specifying the equivalent Omega."""
        star_evo = FakeStarEvo()
        omega = 2.0  # OmegaSun
        prot = pm._Prot(omega)  # equivalent period in days
        via_omega = pm.Lxuv(Mstar=1.0, Age=100.0, Omega=omega, StarEvo=star_evo)
        via_prot = pm.Lxuv(Mstar=1.0, Age=100.0, Prot=prot, StarEvo=star_evo)
        via_env = pm.Lxuv(Mstar=1.0, Age=100.0, OmegaEnv=omega, StarEvo=star_evo)
        assert via_omega['Lx'] > 0.0
        assert_allclose(via_prot['Lx'], via_omega['Lx'], rtol=1e-10)
        assert_allclose(via_env['Lx'], via_omega['Lx'], rtol=1e-10)

    def test_lxuv_loads_default_starevo_when_absent(self, monkeypatch):
        """With no StarEvo argument the wrapper constructs the default track model."""
        monkeypatch.setattr('mors.stellarevo.StarEvo', FakeStarEvo)
        out = pm.Lxuv(Mstar=1.0, Age=100.0, Omega=1.0)
        assert out['Lx'] > 0.0
        # The composite XUV luminosity exceeds the X-ray part alone.
        assert out['Lxuv'] > out['Lx']

    def test_lxuv_rejects_missing_mass_age_and_rotation(self):
        """The wrapper raises when mass, age, or the rotation specifier is missing."""
        star_evo = FakeStarEvo()
        with pytest.raises(Exception, match='Mstar'):
            pm.Lxuv(Mstar=None, Age=100.0, Omega=1.0, StarEvo=star_evo)
        with pytest.raises(Exception, match='Age'):
            pm.Lxuv(Mstar=1.0, Age=None, Omega=1.0, StarEvo=star_evo)
        with pytest.raises(Exception, match='Omega, OmegaEnv, or Prot'):
            pm.Lxuv(Mstar=1.0, Age=100.0, StarEvo=star_evo)

    def test_lxuv_rejects_more_than_one_rotation_specifier(self):
        """Setting two rotation specifiers at once is rejected, before any computation."""
        star_evo = FakeStarEvo()
        with pytest.raises(Exception, match='only set one'):
            pm.Lxuv(Mstar=1.0, Age=100.0, Omega=1.0, Prot=10.0, StarEvo=star_evo)
        # A single specifier still succeeds, confirming the guard is specific.
        ok = pm.Lxuv(Mstar=1.0, Age=100.0, Omega=1.0, StarEvo=star_evo)
        assert ok['Lx'] > 0.0

    def test_lx_wrapper_returns_xray_component(self):
        """The Lx convenience wrapper returns the X-ray entry of the XUV dictionary."""
        star_evo = FakeStarEvo()
        full = pm.Lxuv(Mstar=1.0, Age=100.0, Omega=1.0, StarEvo=star_evo)
        lx = pm.Lx(Mstar=1.0, Age=100.0, Omega=1.0, StarEvo=star_evo)
        assert lx > 0.0
        assert_allclose(lx, full['Lx'], rtol=1e-12)

    def test_leuv_wrapper_selects_band_and_rejects_unknown(self):
        """The Leuv wrapper returns the requested band and rejects an out-of-range band index."""
        star_evo = FakeStarEvo()
        full = pm.Lxuv(Mstar=1.0, Age=100.0, Omega=1.0, StarEvo=star_evo)
        total = pm.Leuv(Mstar=1.0, Age=100.0, Omega=1.0, band=0, StarEvo=star_evo)
        band1 = pm.Leuv(Mstar=1.0, Age=100.0, Omega=1.0, band=1, StarEvo=star_evo)
        band2 = pm.Leuv(Mstar=1.0, Age=100.0, Omega=1.0, band=2, StarEvo=star_evo)
        assert_allclose(total, full['Leuv'], rtol=1e-12)
        # The combined band equals the sum of its two sub-bands.
        assert_allclose(total, band1 + band2, rtol=1e-12)
        with pytest.raises(Exception, match='invalid band'):
            pm.Leuv(Mstar=1.0, Age=100.0, Omega=1.0, band=7, StarEvo=star_evo)

    def test_lly_wrapper_returns_lyman_component(self):
        """The Lly convenience wrapper returns the Lyman-alpha entry of the XUV dictionary."""
        star_evo = FakeStarEvo()
        full = pm.Lxuv(Mstar=1.0, Age=100.0, Omega=1.0, StarEvo=star_evo)
        lly = pm.Lly(Mstar=1.0, Age=100.0, Omega=1.0, StarEvo=star_evo)
        assert lly > 0.0
        assert_allclose(lly, full['Lly'], rtol=1e-12)


class TestScatter:
    """Log-normal scatter of the average activity relations."""

    @pytest.mark.physics_invariant
    def test_xray_scatter_stays_positive_for_scalar_and_array(self):
        """The scattered X-ray value is positive for both a single star and an array.

        The scatter is drawn as a log-normal perturbation, so the average plus the
        returned delta (the scattered value) is always positive. The scalar input
        path returns a length-one array; the array input path returns one entry
        per star.
        """
        np.random.seed(42)
        params = _default_params()
        avg_scalar = 1.0e29  # erg/s
        delta_scalar = pm.XrayScatter(avg_scalar, params=params)
        avg_array = np.array([1.0e28, 1.0e29, 1.0e30])
        delta_array = pm.XrayScatter(avg_array, params=params)
        # Scattered value is the average plus the delta, always positive.
        assert np.all(avg_scalar + delta_scalar > 0.0)
        assert len(delta_array) == 3
        assert np.all(avg_array + delta_array > 0.0)

    def test_xray_scatter_vanishes_without_spread(self):
        """A zero scatter width leaves the average X-ray value unchanged."""
        np.random.seed(42)
        params = _default_params()
        params['sigmaXray'] = 0.0  # no spread
        delta = pm.XrayScatter(5.0e29, params=params)
        assert len(delta) == 1
        # With no spread the scattered value equals the average; only log10 round-trip
        # roundoff remains, negligible against the 5e29 erg/s signal.
        assert abs(delta[0]) < 1.0e18

    @pytest.mark.physics_invariant
    def test_xuv_scatter_preserves_band_budget(self):
        """The correlated XUV scatter keeps the assembled bands consistent.

        The scattered composite luminosities are reconstructed from average plus
        delta, and Lxuv = Lx + Leuv must still hold after the correlated draw.
        """
        np.random.seed(42)
        params = _default_params()
        avg = {
            'Lxuv': 3.0e29, 'Lx': 1.0e29, 'Leuv': 2.0e29, 'Leuv1': 1.2e29,
            'Leuv2': 0.8e29, 'Lly': 5.0e28,
            'Fxuv': 3.0e5, 'Fx': 1.0e5, 'Feuv': 2.0e5, 'Feuv1': 1.2e5,
            'Feuv2': 0.8e5, 'Fly': 5.0e4,
            'Rxuv': 3.0e-4, 'Rx': 1.0e-4, 'Reuv': 2.0e-4, 'Reuv1': 1.2e-4,
            'Reuv2': 0.8e-4, 'Rly': 5.0e-5,
        }
        delta = pm.XUVScatter(avg, params=params)
        # Reconstruct the scattered composite and its parts.
        lxuv_s = delta['Lxuv'] + avg['Lxuv']
        lx_s = delta['Lx'] + avg['Lx']
        leuv_s = delta['Leuv'] + avg['Leuv']
        assert set(delta.keys()) >= {'Lxuv', 'Lx', 'Leuv', 'Reuv', 'Fly'}
        # Band conservation survives the correlated scatter draw.
        assert_allclose(lxuv_s, lx_s + leuv_s, rtol=1e-10)


class TestTorques:
    """Individual torque terms feeding the rotation-rate derivatives."""

    @pytest.mark.physics_invariant
    def test_wind_torque_is_a_spin_down_torque(self):
        """The magnetised-wind torque removes angular momentum from the envelope.

        With a positive dipole field, mass-loss rate, and rotation rate, the Matt
        et al. (2012) wind torque is negative (spin-down), and its magnitude
        scales with the multiplicative Kwind constant.
        """
        state = {
            'Bdip': 2.0, 'Mdot': 1.0e12, 'Rstar': 1.0, 'OmegaEnv': 5.0, 'vEsc': 6.0e7,
        }
        params = _default_params()
        torque = pm._torqueWind(state, params=params)
        # A spin-down torque is negative.
        assert torque < 0.0
        # Doubling Kwind doubles the magnitude of the torque.
        params2 = _default_params()
        params2['Kwind'] = 2.0 * params['Kwind']
        torque2 = pm._torqueWind(state, params=params2)
        assert_allclose(torque2, 2.0 * torque, rtol=1e-12)

    @pytest.mark.physics_invariant
    def test_core_envelope_torque_is_antisymmetric(self):
        """The core-envelope coupling exchanges equal and opposite angular momentum.

        The torque on the envelope and the torque on the core are equal in
        magnitude and opposite in sign, and when the core spins faster than the
        envelope the envelope is spun up (positive envelope torque).
        """
        state = {
            'Icore': 1.0e53, 'Ienv': 5.0e53, 'OmegaCore': 3.0, 'OmegaEnv': 1.0,
            'Mstar': 1.0,
        }
        params = _default_params()
        t_env, t_core = pm._torqueCoreEnvelope(state, params=params)
        # Faster core spins up the envelope.
        assert t_env > 0.0
        # Angular-momentum exchange is antisymmetric.
        assert_allclose(t_core, -t_env, rtol=1e-12)

    def test_core_envelope_torque_respects_minimum_timescale(self):
        """A positive minimum coupling timescale caps the torque magnitude.

        Raising the timeCEmin floor lengthens the coupling timescale and so
        reduces the magnitude of the transferred torque.
        """
        state = {
            'Icore': 1.0e53, 'Ienv': 5.0e53, 'OmegaCore': 3.0, 'OmegaEnv': 1.0,
            'Mstar': 1.0,
        }
        params_small = _default_params()
        params_large = _default_params()
        params_large['timeCEmin'] = 1.0e4  # Myr, a long floor
        t_small, _ = pm._torqueCoreEnvelope(state, params=params_small)
        t_large, _ = pm._torqueCoreEnvelope(state, params=params_large)
        assert t_small > 0.0
        # A longer coupling timescale gives a weaker torque.
        assert abs(t_large) < abs(t_small)

    @pytest.mark.physics_invariant
    def test_moment_torque_switches_with_decoupling(self):
        """The moment-of-inertia torque uses envelope or total inertia change by regime.

        When core and envelope are decoupled the envelope torque follows the
        envelope inertia change and the core torque is nonzero; when coupled, the
        envelope torque follows the total inertia change and the core torque is
        zero.
        """
        state = {
            'dIenvdt': -5.0e39, 'dIcoredt': 5.0e39, 'dItotaldt': 1.0e40,
            'OmegaEnv': 1.0, 'OmegaCore': 2.0,
        }
        env_dec, core_dec = pm._torqueMoment(state, True)
        env_cpl, core_cpl = pm._torqueMoment(state, False)
        # Coupled regime places no separate torque on the core.
        assert_allclose(core_cpl, 0.0, atol=1e-30)
        assert abs(core_dec) > 0.0
        # The decoupled and coupled envelope torques use different inertia terms.
        assert abs(env_dec - env_cpl) > 0.0

    @pytest.mark.physics_invariant
    def test_core_growth_torque_is_antisymmetric(self):
        """Core growth transfers equal and opposite angular momentum between reservoirs."""
        state = {'Rcore': 1.0e10, 'OmegaEnv': 1.0, 'dMcoredt': 1.0e15}
        t_env, t_core = pm._torqueCoreGrowth(state)
        # The two torques cancel exactly.
        assert_allclose(t_core, -t_env, rtol=1e-12)
        # Growing the core at a positive rate spins the envelope down.
        assert t_env < 0.0

    def test_disk_locking_returns_zero_after_locking_age(self):
        """Beyond the disk-locking age the disk-locking torque vanishes."""
        params = _default_params()
        state = {
            'OmegaEnv': 1.0, 'Age': 1000.0,  # Myr, well past the locking age
            'torqueEnvWind': -1.0e30, 'torqueEnvCE': 0.0, 'torqueEnvCG': 0.0,
            'torqueEnvMom': 0.0,
        }
        torque = pm._torqueDiskLocking(state, True, params=params)
        assert_allclose(torque, 0.0, atol=1e-30)
        # While still locked, the disk cancels the other envelope torques.
        state_young = dict(state)
        state_young['Age'] = 1.0  # Myr, still within the locking age
        torque_young = pm._torqueDiskLocking(state_young, True, params=params)
        assert_allclose(torque_young, 1.0e30, rtol=1e-12)

    def test_disk_locking_uses_reduced_torque_set_when_coupled(self):
        """When core and envelope are coupled the disk balances fewer torque terms."""
        params = _default_params()
        state = {
            'OmegaEnv': 1.0, 'Age': 1.0,  # Myr, within the locking age
            'torqueEnvWind': -1.0e30, 'torqueEnvCE': -2.0e30, 'torqueEnvCG': -3.0e30,
            'torqueEnvMom': -4.0e29,
        }
        decoupled = pm._torqueDiskLocking(state, True, params=params)
        coupled = pm._torqueDiskLocking(state, False, params=params)
        # The decoupled balance includes the core-envelope and core-growth terms.
        assert_allclose(decoupled,
                        -(state['torqueEnvWind'] + state['torqueEnvCE']
                          + state['torqueEnvCG'] + state['torqueEnvMom']), rtol=1e-12)
        # The coupled balance omits them, giving a different value.
        assert abs(coupled - decoupled) > 0.0


class TestWindHelpers:
    """Dipole field, mass loss, escape velocity, and breakup rotation."""

    @pytest.mark.physics_invariant
    def test_dipole_field_saturates_below_threshold(self):
        """The dipole field strength flattens once the Rossby number drops below saturation.

        In the unsaturated regime the field grows as the Rossby number shrinks;
        in the saturated regime it is pinned at the threshold value, so two fast
        rotators below the threshold share the same field.
        """
        params = _default_params()
        slow = {'Ro': 2.0 * params['RoSatBdip']}  # unsaturated
        fast = {'Ro': 0.1 * params['RoSatBdip']}  # saturated
        faster = {'Ro': 0.01 * params['RoSatBdip']}  # deeper into saturation
        B_slow = pm._Bdip(slow, params=params)
        B_fast = pm._Bdip(fast, params=params)
        B_faster = pm._Bdip(faster, params=params)
        assert B_slow > 0.0
        # Slower rotator has a weaker field than the saturated fast rotator.
        assert B_fast > B_slow
        # Both saturated rotators share the pinned saturation field.
        assert_allclose(B_faster, B_fast, rtol=1e-12)

    @pytest.mark.physics_invariant
    def test_mass_loss_rate_saturates_and_is_positive(self):
        """The wind mass-loss rate is positive and saturates below the threshold Rossby number."""
        params = _default_params()
        params['BreakupMdotIncrease'] = False  # isolate the Rossby scaling
        slow = {'Ro': 3.0 * params['RoSatMdot'], 'Rstar': 1.0, 'Mstar': 1.0, 'OmegaEnv': 1.0}
        fast = {'Ro': 0.1 * params['RoSatMdot'], 'Rstar': 1.0, 'Mstar': 1.0, 'OmegaEnv': 1.0}
        faster = {'Ro': 0.01 * params['RoSatMdot'], 'Rstar': 1.0, 'Mstar': 1.0, 'OmegaEnv': 1.0}
        Mdot_slow = pm._Mdot(slow, params=params)
        Mdot_fast = pm._Mdot(fast, params=params)
        Mdot_faster = pm._Mdot(faster, params=params)
        assert Mdot_slow > 0.0
        # Fast rotator loses mass faster than a slow one.
        assert Mdot_fast > Mdot_slow
        # Both saturated rotators share the pinned saturation mass-loss rate.
        assert_allclose(Mdot_faster, Mdot_fast, rtol=1e-12)

    def test_mass_loss_breakup_factor_applied_when_enabled(self):
        """Enabling the breakup increase raises the mass-loss rate of a rapid rotator."""
        params_on = _default_params()
        params_off = _default_params()
        params_off['BreakupMdotIncrease'] = False
        # Choose a rotation rate well above the breakup threshold fraction.
        omega_break = pm.OmegaBreak(1.0, 1.0)
        state = {
            'Ro': 0.1 * params_on['RoSatMdot'], 'Rstar': 1.0, 'Mstar': 1.0,
            'OmegaEnv': 0.5 * omega_break,
        }
        Mdot_on = pm._Mdot(dict(state), params=params_on)
        Mdot_off = pm._Mdot(dict(state), params=params_off)
        assert Mdot_off > 0.0
        # The breakup factor is greater than unity for a rapid rotator.
        assert Mdot_on > Mdot_off

    @pytest.mark.physics_invariant
    def test_breakup_factor_regimes(self):
        """The mass-loss breakup factor is unity when slow and grows near breakup.

        Below the threshold fraction of breakup the factor is exactly one; between
        the threshold and 1.009 it uses the primary fit; at or above 1.009 it
        switches to the polynomial fit. Each regime gives a factor above one when
        close to breakup.
        """
        params = _default_params()
        omega_break = pm.OmegaBreak(1.0, 1.0)
        # Slow rotator, well below threshold: factor is unity.
        factor_slow = pm.MdotFactor(1.0, 1.0, 0.01 * omega_break, params=params)
        assert_allclose(factor_slow, 1.0, rtol=1e-12)
        # Moderate approach to breakup, primary fit: factor above one.
        factor_mid = pm.MdotFactor(1.0, 1.0, 0.5 * omega_break, params=params)
        assert factor_mid > 1.0
        # Beyond breakup, polynomial fit branch.
        factor_over = pm.MdotFactor(1.0, 1.0, 1.02 * omega_break, params=params)
        assert factor_over > 1.0

    @pytest.mark.physics_invariant
    def test_escape_velocity_scales_with_mass_and_radius(self):
        """Surface escape velocity rises with mass and falls with radius.

        The escape velocity follows sqrt(2 G M / R): a more massive star has a
        higher escape velocity, an inflated star a lower one, and the value is
        strictly positive.
        """
        v_sun = pm._vEsc(1.0, 1.0)
        v_massive = pm._vEsc(4.0, 1.0)
        v_inflated = pm._vEsc(1.0, 4.0)
        assert v_sun > 0.0
        # Quadrupling the mass doubles the escape velocity.
        assert_allclose(v_massive, 2.0 * v_sun, rtol=1e-12)
        # Quadrupling the radius halves it.
        assert_allclose(v_inflated, 0.5 * v_sun, rtol=1e-12)

    @pytest.mark.physics_invariant
    def test_breakup_rotation_scales_with_mass_and_radius(self):
        """Breakup rotation rate rises with mass and falls with radius.

        The breakup angular velocity follows sqrt(G M) / R^1.5: a heavier star
        spins up to breakup faster, an inflated one at a lower rate. The value is
        positive and, for the Sun, of order a hundred solar rotation rates.
        """
        omega_sun = pm.OmegaBreak(1.0, 1.0)
        omega_massive = pm.OmegaBreak(4.0, 1.0)
        omega_inflated = pm.OmegaBreak(1.0, 4.0)
        assert omega_sun > 0.0
        # Quadrupling the mass doubles the breakup rate.
        assert_allclose(omega_massive, 2.0 * omega_sun, rtol=1e-12)
        # Quadrupling the radius reduces it by a factor of eight.
        assert_allclose(omega_inflated, omega_sun / 8.0, rtol=1e-12)


class TestDecoupling:
    """Core-envelope decoupling decision logic."""

    def test_decoupling_disabled_by_parameter(self):
        """Disabling the decoupling parameter forces the coupled regime regardless of inertia."""
        params = _default_params()
        params['CoreEnvelopeDecoupling'] = False
        state = {'Icore': 1.0e53, 'Itotal': 2.0e53, 'Mstar': 1.0}
        assert pm._shouldCoreEnvelopeDecoupling(state, params=params) is False
        # With the switch on and the same generous inertia and mass, decoupling is allowed.
        params_on = _default_params()
        assert pm._shouldCoreEnvelopeDecoupling(state, params=params_on) is True

    def test_decoupling_requires_core_inertia_and_mass_thresholds(self):
        """A small core inertia fraction or a low stellar mass forbids decoupling."""
        params = _default_params()
        small_core = {'Icore': 1.0e50, 'Itotal': 1.0e53, 'Mstar': 1.0}
        low_mass = {'Icore': 1.0e53, 'Itotal': 2.0e53, 'Mstar': 0.1}
        # Core inertia fraction below the threshold forbids decoupling.
        assert pm._shouldCoreEnvelopeDecoupling(small_core, params=params) is False
        # Mass below the threshold also forbids it.
        assert pm._shouldCoreEnvelopeDecoupling(low_mass, params=params) is False


class TestRotationQuantities:
    """The assembled rotation-quantity dictionary and its derivatives."""

    @pytest.mark.physics_invariant
    def test_rotation_quantities_positive_and_consistent_decoupled(self):
        """A solar-type star with a developed core yields positive structural quantities.

        With a generous core inertia the star is in the decoupled regime, so the
        core derivative comes from the core torque over the core inertia. Radius,
        Rossby number, and moments of inertia are all positive.
        """
        state = pm.RotationQuantities(Mstar=1.0, Age=100.0, OmegaEnv=1.0,
                                      OmegaCore=1.0, StarEvo=FakeStarEvo())
        assert state['Rstar'] > 0.0 and state['Ro'] > 0.0
        assert state['Ienv'] > 0.0
        # The envelope derivative is the total envelope torque over the envelope inertia.
        expected = state['torqueEnv'] / state['Ienv'] * const.Myr / const.OmegaSun
        assert_allclose(state['dOmegaEnvdt'], expected, rtol=1e-12)

    def test_rotation_quantities_couples_core_when_not_decoupled(self):
        """In the coupled regime the core rotation derivative tracks the envelope's.

        Disabling the decoupling switch forces the coupled branch, in which the
        core carries no separate torque and its derivative equals the envelope's.
        """
        params = _default_params()
        params['CoreEnvelopeDecoupling'] = False
        state = pm.RotationQuantities(Mstar=1.0, Age=5.0, OmegaEnv=1.0, OmegaCore=1.0,
                                      params=params, StarEvo=FakeStarEvo())
        assert_allclose(state['torqueCore'], 0.0, atol=1e-30)
        # Core and envelope rotation rates change together when coupled.
        assert_allclose(state['dOmegaCoredt'], state['dOmegaEnvdt'], rtol=1e-12)

    def test_rotation_quantities_honours_disabled_torque_switches(self):
        """Disabling individual torque contributions zeroes the corresponding entries."""
        params = _default_params()
        params['MomentInertiaChangeTorque'] = False
        params['WindTorque'] = False
        params['DiskLocking'] = False
        state = pm.RotationQuantities(Mstar=1.0, Age=100.0, OmegaEnv=1.0, OmegaCore=1.0,
                                      params=params, StarEvo=FakeStarEvo())
        # The disabled contributions are exactly zero.
        assert_allclose(state['torqueEnvMom'], 0.0, atol=1e-30)
        assert_allclose(state['torqueEnvWind'], 0.0, atol=1e-30)
        assert_allclose(state['torqueEnvDL'], 0.0, atol=1e-30)

    def test_rotation_quantities_rejects_missing_arguments(self):
        """Every required rotation argument is validated before any computation."""
        with pytest.raises(Exception, match='Mstar'):
            pm.RotationQuantities(Mstar=None, Age=1.0, OmegaEnv=1.0, OmegaCore=1.0,
                                  StarEvo=FakeStarEvo())
        with pytest.raises(Exception, match='Age'):
            pm.RotationQuantities(Mstar=1.0, Age=None, OmegaEnv=1.0, OmegaCore=1.0,
                                  StarEvo=FakeStarEvo())
        with pytest.raises(Exception, match='OmegaEnv'):
            pm.RotationQuantities(Mstar=1.0, Age=1.0, OmegaEnv=None, OmegaCore=1.0,
                                  StarEvo=FakeStarEvo())
        with pytest.raises(Exception, match='OmegaCore'):
            pm.RotationQuantities(Mstar=1.0, Age=1.0, OmegaEnv=1.0, OmegaCore=None,
                                  StarEvo=FakeStarEvo())

    def test_rotation_quantities_loads_default_starevo_when_absent(self, monkeypatch):
        """Omitting the track model constructs the default one before the computation."""
        monkeypatch.setattr('mors.stellarevo.StarEvo', FakeStarEvo)
        state = pm.RotationQuantities(Mstar=1.0, Age=100.0, OmegaEnv=1.0, OmegaCore=1.0)
        assert state['Rstar'] > 0.0
        # The default-model run reproduces the explicit-model run.
        explicit = pm.RotationQuantities(Mstar=1.0, Age=100.0, OmegaEnv=1.0, OmegaCore=1.0,
                                         StarEvo=FakeStarEvo())
        assert_allclose(state['dOmegaEnvdt'], explicit['dOmegaEnvdt'], rtol=1e-12)

    def test_domegadt_returns_envelope_and_core_rates(self, monkeypatch):
        """The top-level derivative wrapper returns the envelope and core rotation rates.

        With no StarEvo supplied the wrapper builds the default track model, which
        is replaced here by the plausible-value stand-in.
        """
        monkeypatch.setattr('mors.stellarevo.StarEvo', FakeStarEvo)
        d_env, d_core = pm.dOmegadt(Mstar=1.0, Age=100.0, OmegaEnv=1.0, OmegaCore=1.0)
        # A supplied track model gives the same derivatives as the default one.
        d_env2, d_core2 = pm.dOmegadt(Mstar=1.0, Age=100.0, OmegaEnv=1.0, OmegaCore=1.0,
                                      StarEvo=FakeStarEvo())
        full = pm.RotationQuantities(Mstar=1.0, Age=100.0, OmegaEnv=1.0, OmegaCore=1.0,
                                     StarEvo=FakeStarEvo())
        assert np.isfinite(d_env) and np.isfinite(d_core)
        assert_allclose(d_env, full['dOmegaEnvdt'], rtol=1e-12)
        assert_allclose(d_env2, d_env, rtol=1e-12)

    def test_domegadt_rejects_missing_arguments(self):
        """The derivative wrapper validates each rotation argument."""
        with pytest.raises(Exception, match='Mstar'):
            pm.dOmegadt(Mstar=None, Age=1.0, OmegaEnv=1.0, OmegaCore=1.0,
                        StarEvo=FakeStarEvo())
        with pytest.raises(Exception, match='Age'):
            pm.dOmegadt(Mstar=1.0, Age=None, OmegaEnv=1.0, OmegaCore=1.0,
                        StarEvo=FakeStarEvo())
        with pytest.raises(Exception, match='OmegaEnv'):
            pm.dOmegadt(Mstar=1.0, Age=1.0, OmegaEnv=None, OmegaCore=1.0,
                        StarEvo=FakeStarEvo())
        with pytest.raises(Exception, match='OmegaCore'):
            pm.dOmegadt(Mstar=1.0, Age=1.0, OmegaEnv=1.0, OmegaCore=None,
                        StarEvo=FakeStarEvo())


class TestExtendedQuantitiesAndUnits:
    """Extended emission quantities and the units dictionary."""

    @pytest.mark.physics_invariant
    def test_extended_quantities_adds_positive_emission(self, monkeypatch):
        """Extended quantities append positive high-energy luminosities to a rotation state.

        The bolometric, X-ray, EUV, and Lyman-alpha luminosities are all positive,
        and the habitable-zone X-ray flux is the X-ray luminosity spread over the
        habitable-zone sphere.
        """
        monkeypatch.setattr('mors.stellarevo.StarEvo', FakeStarEvo)
        monkeypatch.setattr('mors.stellarevo.Lbol', lambda M, A: 1.0)
        monkeypatch.setattr('mors.stellarevo.Teff', lambda M, A: 5700.0)
        state = pm.ExtendedQuantities(Mstar=1.0, Age=100.0, OmegaEnv=1.0, OmegaCore=1.0)
        assert state['Lbol'] > 0.0 and state['Lx'] > 0.0
        assert state['Leuv'] > 0.0 and state['Lly'] > 0.0
        # The habitable-zone flux is the X-ray luminosity over the HZ sphere.
        hz = pm.aOrbHZ(Mstar=1.0, Age=100.0)
        expected = state['Lx'] / (4.0 * const.Pi * (hz['HZ'] * const.AU) ** 2.0)
        assert_allclose(state['FxHZ'], expected, rtol=1e-10)

    def test_extended_quantities_requires_arguments_without_state(self, monkeypatch):
        """Without a prior state the extended-quantity call validates its inputs."""
        monkeypatch.setattr('mors.stellarevo.StarEvo', FakeStarEvo)
        monkeypatch.setattr('mors.stellarevo.Lbol', lambda M, A: 1.0)
        monkeypatch.setattr('mors.stellarevo.Teff', lambda M, A: 5700.0)
        with pytest.raises(Exception, match='Mstar'):
            pm.ExtendedQuantities(Mstar=None, Age=1.0, OmegaEnv=1.0, OmegaCore=1.0)
        with pytest.raises(Exception, match='Age'):
            pm.ExtendedQuantities(Mstar=1.0, Age=None, OmegaEnv=1.0, OmegaCore=1.0)
        with pytest.raises(Exception, match='OmegaEnv'):
            pm.ExtendedQuantities(Mstar=1.0, Age=1.0, OmegaEnv=None, OmegaCore=1.0)
        with pytest.raises(Exception, match='OmegaCore'):
            pm.ExtendedQuantities(Mstar=1.0, Age=1.0, OmegaEnv=1.0, OmegaCore=None)

    @pytest.mark.physics_invariant
    def test_extended_quantities_reuses_supplied_state_and_starevo(self, monkeypatch):
        """A precomputed rotation state and an explicit track model are reused directly.

        When the caller supplies both StarState and StarEvo the function skips the
        rotation-quantity recomputation and appends the emission quantities to the
        existing dictionary, keeping the rotation entries untouched.
        """
        monkeypatch.setattr('mors.stellarevo.Lbol', lambda M, A: 1.0)
        monkeypatch.setattr('mors.stellarevo.Teff', lambda M, A: 5700.0)
        star_evo = FakeStarEvo()
        base = pm.RotationQuantities(Mstar=1.0, Age=100.0, OmegaEnv=1.0, OmegaCore=1.0,
                                     StarEvo=star_evo)
        rossby_before = base['Ro']
        extended = pm.ExtendedQuantities(StarState=base, Mstar=1.0, Age=100.0,
                                         StarEvo=star_evo)
        # Emission quantities were appended, rotation entries preserved.
        assert extended['Lx'] > 0.0 and extended['Leuv'] > 0.0
        assert_allclose(extended['Ro'], rossby_before, rtol=1e-12)

    def test_quantities_units_full_and_filtered(self):
        """The units dictionary is complete on its own and filters to a supplied state."""
        full = pm.QuantitiesUnits()
        assert full['Lx'] == 'erg s^-1'
        assert full['Ro'] == ''
        # A filtered call returns only the keys present in the state.
        subset = pm.QuantitiesUnits(StarState={'Mstar': 1.0, 'Lx': 1.0e29})
        assert set(subset.keys()) == {'Mstar', 'Lx'}

    def test_quantities_units_rejects_unknown_quantity(self):
        """A state carrying an unlisted quantity is rejected by the units lookup."""
        with pytest.raises(Exception, match='not included in units list'):
            pm.QuantitiesUnits(StarState={'Mstar': 1.0, 'NotAQuantity': 3.0})
        # A state with only listed quantities passes without error.
        ok = pm.QuantitiesUnits(StarState={'Teff': 5700.0})
        assert ok['Teff'] == 'K'


class TestSaturationThresholds:
    """Saturation rotation period and angular velocity."""

    def test_prot_sat_selects_band_and_rejects_unknown(self):
        """The saturation period uses the band-specific Rossby number and rejects an unknown band."""
        params = _default_params()
        star_evo = FakeStarEvo()
        prot_xuv = pm.ProtSat(Mstar=1.0, Age=100.0, param='XUV', params=params, StarEvo=star_evo)
        prot_bdip = pm.ProtSat(Mstar=1.0, Age=100.0, param='Bdip', params=params, StarEvo=star_evo)
        prot_mdot = pm.ProtSat(Mstar=1.0, Age=100.0, param='Mdot', params=params, StarEvo=star_evo)
        # The saturation period is the saturation Rossby number times the turnover time.
        assert_allclose(prot_xuv, params['RoSatXray'] * star_evo.tauConv(1.0, 100.0), rtol=1e-12)
        assert prot_bdip > 0.0 and prot_mdot > 0.0
        with pytest.raises(Exception, match='invalid value of param'):
            pm.ProtSat(Mstar=1.0, Age=100.0, param='nonsense', params=params, StarEvo=star_evo)

    @pytest.mark.physics_invariant
    def test_omega_sat_is_positive_and_inverse_of_period(self, monkeypatch):
        """The saturation angular velocity is the positive inverse transform of its period."""
        monkeypatch.setattr('mors.stellarevo.StarEvo', FakeStarEvo)
        params = _default_params()
        omega = pm.OmegaSat(Mstar=1.0, Age=100.0, param='XUV', params=params)
        prot = pm.ProtSat(Mstar=1.0, Age=100.0, param='XUV', params=params,
                          StarEvo=FakeStarEvo())
        assert omega > 0.0
        # OmegaSat is the angular velocity corresponding to the saturation period.
        assert_allclose(omega, pm._Omega(prot), rtol=1e-12)

    def test_saturation_helpers_accept_explicit_or_default_starevo(self, monkeypatch):
        """Supplying a track model matches constructing the default one for both helpers."""
        monkeypatch.setattr('mors.stellarevo.StarEvo', FakeStarEvo)
        params = _default_params()
        star_evo = FakeStarEvo()
        omega_explicit = pm.OmegaSat(Mstar=1.0, Age=100.0, params=params, StarEvo=star_evo)
        omega_default = pm.OmegaSat(Mstar=1.0, Age=100.0, params=params)
        prot_default = pm.ProtSat(Mstar=1.0, Age=100.0, params=params)
        assert omega_explicit > 0.0 and prot_default > 0.0
        # The explicit-model and default-model saturation rates agree.
        assert_allclose(omega_explicit, omega_default, rtol=1e-12)


class TestHabitableZone:
    """Kopparapu et al. (2013) habitable-zone boundaries."""

    @pytest.mark.reference_pinned
    @pytest.mark.physics_invariant
    def test_solar_runaway_greenhouse_limit(self, monkeypatch):
        """For a solar analogue the runaway greenhouse limit matches Kopparapu et al. (2013).

        Reference: Kopparapu et al. (2013), Table 3, runaway greenhouse effective
        stellar flux Seff = 1.0385 at solar effective temperature. With a solar
        bolometric luminosity of 1 Lsun the boundary is (1 / 1.0385)^0.5 ~ 0.981
        AU, the classic inner edge of the conservative habitable zone.
        """
        monkeypatch.setattr('mors.stellarevo.Lbol', lambda M, A: 1.0)
        monkeypatch.setattr('mors.stellarevo.Teff', lambda M, A: 5780.0)
        hz = pm.aOrbHZ(Mstar=1.0, Age=4570.0)
        expected = (1.0 / 1.0385) ** 0.5
        assert_allclose(hz['RunawayGreenhouse'], expected, rtol=1e-6)
        # Sign / scale guard: a solar inner HZ edge is near 1 AU, not 0.1 or 10 AU.
        assert 0.5 < hz['RunawayGreenhouse'] < 1.5

    @pytest.mark.reference_pinned
    @pytest.mark.physics_invariant
    def test_runaway_greenhouse_limit_for_a_cool_star(self, monkeypatch):
        """For a cool star the runaway greenhouse limit follows the Kopparapu polynomial.

        Reference: Kopparapu et al. (2013), Table 3. At Teff = 4000 K the shifted
        temperature Tstar = Teff - 5780 = -1780 K drives the full
        a*Tstar + b*Tstar**2 + c*Tstar**3 + d*Tstar**4 correction, unlike the
        solar case where every temperature term vanishes. The boundary distance
        is (Lbol / Seff)**0.5 with Seff from the published coefficients.
        """
        monkeypatch.setattr('mors.stellarevo.Lbol', lambda M, A: 0.1)
        monkeypatch.setattr('mors.stellarevo.Teff', lambda M, A: 4000.0)
        hz = pm.aOrbHZ(Mstar=0.5, Age=1000.0)
        # Kopparapu runaway-greenhouse coefficients at Tstar = -1780 K.
        tstar = 4000.0 - 5780.0
        seff = (1.0385 + 1.2456e-4 * tstar + 1.4612e-8 * tstar**2
                - 7.6345e-12 * tstar**3 - 1.7511e-15 * tstar**4)
        expected = (0.1 / seff) ** 0.5
        assert_allclose(hz['RunawayGreenhouse'], expected, rtol=1e-9)
        # Discrimination guard: a linear cubic term (c*Tstar instead of
        # c*Tstar**3) shifts the boundary by more than two percent at this
        # temperature, so an exponent slip fails here even though it is invisible
        # at the solar anchor where Tstar is zero.
        seff_linear = (1.0385 + 1.2456e-4 * tstar + 1.4612e-8 * tstar**2
                       - 7.6345e-12 * tstar * 3.0 - 1.7511e-15 * tstar**4)
        wrong = (0.1 / seff_linear) ** 0.5
        assert abs(hz['RunawayGreenhouse'] - wrong) > 0.02 * expected
        # Positivity and scale guard for a cool, faint star.
        assert 0.2 < hz['RunawayGreenhouse'] < 0.5

    @pytest.mark.physics_invariant
    def test_habitable_zone_boundaries_are_ordered(self, monkeypatch):
        """The habitable-zone boundaries increase from the hottest to the coolest limit.

        The Recent Venus inner edge lies inside the Runaway Greenhouse, Moist
        Greenhouse, Maximum Greenhouse, and Early Mars limits in turn, and the
        adopted central HZ distance lies between the moist and maximum boundaries.
        """
        # Teff of exactly 5780 K sets Tstar = Teff - 5780 = 0, so the polynomial
        # correction terms vanish and each boundary reduces to (Lbol / SeffSun)**0.5.
        # These are the solar-limit boundary distances; the ordering below tests the
        # ranking of the SeffSun coefficients at the solar anchor.
        monkeypatch.setattr('mors.stellarevo.Lbol', lambda M, A: 1.0)
        monkeypatch.setattr('mors.stellarevo.Teff', lambda M, A: 5780.0)
        hz = pm.aOrbHZ(Mstar=1.0)
        assert hz['RecentVenus'] > 0.0
        # Full ordering from the hottest inner edge to the coolest outer edge.
        assert (hz['RecentVenus'] < hz['RunawayGreenhouse'] < hz['MoistGreenhouse']
                < hz['MaximumGreenhouse'] < hz['EarlyMars'])
        # The adopted HZ distance is the mean of the moist and maximum greenhouse edges.
        assert_allclose(hz['HZ'], 0.5 * (hz['MoistGreenhouse'] + hz['MaximumGreenhouse']),
                        rtol=1e-12)

    def test_habitable_zone_defaults_age_and_requires_mass(self, monkeypatch):
        """The boundary call falls back to the default age and rejects a missing mass."""
        monkeypatch.setattr('mors.stellarevo.Lbol', lambda M, A: 1.0)
        monkeypatch.setattr('mors.stellarevo.Teff', lambda M, A: 5780.0)
        params = _default_params()
        with_default_age = pm.aOrbHZ(Mstar=1.0, params=params)
        explicit_age = pm.aOrbHZ(Mstar=1.0, Age=params['AgeHZ'], params=params)
        # Omitting the age uses the AgeHZ parameter, matching an explicit AgeHZ call.
        assert_allclose(with_default_age['HZ'], explicit_age['HZ'], rtol=1e-12)
        with pytest.raises(Exception, match='Mstar'):
            pm.aOrbHZ(Mstar=None)
