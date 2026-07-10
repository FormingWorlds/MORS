# Validation: `src/mors/physicalmodel.py`

This page tracks the `@pytest.mark.reference_pinned` tests that anchor the
behaviour of `mors.physicalmodel` against published sources.

| Test id | Reference | Scope |
|---|---|---|
| `tests/test_physicalmodel.py::test_saturated_xray_ratio_matches_johnstone_value` | Johnstone et al. (2020) saturated X-ray ratio, calibrated on the Spada et al. (2013) [^cite-spada2013] models | Pins the saturated X-ray-to-bolometric ratio at the saturation Rossby number to `Rx_sat = 5.135e-4`, the value the rotation-activity model uses (see [High-energy emission and activity](../Explanations/activity.md)). |
| `tests/test_physicalmodel.py::test_solar_runaway_greenhouse_limit` | Kopparapu et al. (2013) [^cite-kopparapu2013], Table 3 | Pins the runaway-greenhouse boundary for a solar analogue to `(Lbol / Seff)**0.5` with `Seff = 1.0385`, giving about 0.98 AU at one solar luminosity. |

## Re-derivation note

`physicalmodel.py` holds the rotation, activity, and high-energy emission
relations of the stellar model. Two anchors pin it:

The X-ray activity relation is a broken power law in Rossby number with a
saturated branch `Rx = C1 * Ro**beta1` for `Ro <= Ro_sat`. At the saturation
Rossby number the two branches meet at `Rx_sat = 5.135e-4`. The reference-pinned
test evaluates the relation at the saturation point and pins that value, so a
regression in the saturation constant or the branch selection is caught. A
companion test walks a point on each side of the threshold to check the
branch dispatch.

The habitable-zone boundaries follow the Kopparapu et al. (2013) effective
stellar flux `Seff = Seff_sun + a*T + b*T**2 + c*T**3 + d*T**4` with
`T = Teff - 5780`, and the boundary distance is `aOrb = (Lbol / Seff)**0.5`.
For a solar analogue `T = 0`, so `Seff = Seff_sun`; the runaway-greenhouse
coefficient `Seff_sun = 1.0385` places the boundary at `(1 / 1.0385)**0.5`,
about 0.98 AU for one solar luminosity. The test pins that solar-limit
boundary, and a companion test asserts the full ordering of the five
boundaries from Recent Venus (innermost) to Early Mars (outermost).

## Anchor type

Published benchmark. The saturated X-ray ratio is the calibrated model value;
the habitable-zone boundary is the Kopparapu et al. (2013) solar limit.
Companion `physics_invariant` tests cover the positivity of the emission
quantities, the band conservation `Lxuv = Lx + Leuv`, the torque antisymmetry,
the saturation monotonicity, and the ordering of the habitable-zone boundaries.

## Cross-references

- `src/mors/physicalmodel.py`: `Lxuv`, `Lx`, `Leuv`, the Rossby and torque
  helpers, and `aOrbHZ`.
- [High-energy emission and activity](../Explanations/activity.md) and
  [Habitable zone boundaries](../Explanations/habitablezone.md) describe the
  full relations and carry the complete reference list.

## References

[^cite-kopparapu2013]: R. K. Kopparapu, R. Ramirez, J. F. Kasting, et al., *[Habitable zones around main-sequence stars: new estimates](https://doi.org/10.1088/0004-637X/765/2/131)*, The Astrophysical Journal, 765(2), 131, 2013.

[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The radius discrepancy in low-mass stars: single versus binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776(2), 87, 2013.
