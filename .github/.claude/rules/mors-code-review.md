# MORS Code Review Criteria

When reviewing MORS code (either your own or via code-reviewer agents), apply these domain-specific checks in addition to standard code quality review.

> **Discovery note.** MORS keeps its Claude-Code rule files under `.github/.claude/rules/` (not the conventional repo-root `.claude/`) so they can be tracked in git and shared across collaborators. Claude does NOT auto-discover them at this path; the repo-root `CLAUDE.md` (symlinked to `.github/copilot-instructions.md`) names this file and `mors-tests.md` explicitly. **Before opening any review pass, read both this file and `mors-tests.md`.**

## Physics plausibility

- Luminosity, radius, and effective temperature must be positive everywhere. Flag any code path where `L_bol`, `R_star`, or `T_eff` could reach zero or go negative.
- Bolometric and band fluxes must be non-negative. A synthesised spectrum floors its flux above zero (`>= 1e-20`); flag any path that could emit a zero or negative flux into the band integrals.
- Bolometric band closure: `F_bo` must equal the sum of the band fluxes (`F_xr + F_e1 + F_e2 + F_uv + F_pl`) within tolerance. The UV band is defined as the remainder `F_bo - F_xr - F_e1 - F_e2 - F_pl`; flag any change that lets the remainder go negative (it means a band was double-counted or the bolometric flux was underestimated).
- Rotation rate `Omega` must stay positive through the spin-down integration. Flag any torque term that could drive `Omega <= 0` without a guard.
- Distribution percentiles must lie in `[0, 100]`; the inverse (percentile -> Omega) must be monotone. Flag any `Cluster` method that could return a percentile outside the range or a non-monotone mapping.
- Track interpolation must not extrapolate silently past the grid edges. Flag any `Value` / `Percentile` path that accepts an off-grid mass or age and returns a number without clamping or raising.

## Unit convention boundaries

MORS has a mixed cgs / SI convention. This is the recurring trap; verify the unit is correct at every conversion site:

- **Stellar quantities**: luminosity in **erg/s** (cgs; a solar-type `Lbol` is `~8e33`), radius in **R_sun** or cm depending on the call, effective temperature in **K**.
- **Rotation**: `Omega` in units of the solar rotation rate (`Omega_sun`), age in **Myr**, stellar mass in **M_sun**.
- **Spectra**: wavelength in **nm**, flux at 1 AU in **W/m^2** (SI), surface flux scaled by `(R_star / AU)^2`.
- **Constants**: `AU`, `LbolSun`, `Pi` and friends live in `src/mors/constants.py`; check that a body uses the module constant rather than re-deriving a literal.

When reviewing code that crosses these boundaries (a new emission relation, a new band, a new PROTEUS-side caller), confirm the unit at each site. The `erg/s` vs `W` and `cm` vs `m` boundaries are where wrong-by-a-constant-factor bugs hide; a value that is "close enough" to pass a loose test but off by `1e7` (erg to W) is the signature.

## Track-data loading and determinism

`baraffe.py` and `stellarevo.py` load evolutionary tracks from `FWL_DATA` (downloaded from OSF on first use).

- Flag any code that assumes the track files are present without a download / existence check.
- Flag any interpolation that changes results depending on the track release without recording the release the numbers were pinned against.
- A change to the default track set (Baraffe vs Spada) or the default time-integration method (`ForwardEuler` vs `RungeKutta`) has fan-out across the pinned reference tests and the `docs/Validation/` pages: `git grep` the old default and update every reference value and validation page tied to it in the same PR.

## PROTEUS coupling patterns

MORS is called by PROTEUS during the stellar-evolution step to supply the stellar spectrum and the high-energy (XUV) flux history that drive atmospheric heating and escape.

- **Band definitions are the coupling contract.** The band keys (`xr`, `e1`, `e2`, `uv`, `pl`, `bo`) and their wavelength limits (`spectrum.bands_limits`) are consumed downstream. Flag any change to a band boundary or key name that is not mirrored in the PROTEUS-side caller and the pinned band-flux tests.
- **`Value` / `Percentile` are the API surface.** PROTEUS reads `star.Value(age, key)` for `Rstar`, `Lbol`, `Leuv` and uses `Percentile` for the initial-rotation distribution. Flag any change that alters the return units or the key set without a corresponding PROTEUS-side update.
- **Spectral scaling round-trip.** The surface <-> 1 AU scaling (`ScaleToSurf` / `ScaleTo1AU`) must be a clean inverse pair. Flag any change that breaks `ScaleTo1AU(ScaleToSurf(f, R)) == f` within tolerance; a broken round-trip silently rescales every flux PROTEUS receives.
- **Monotone flux history.** PROTEUS integrates the XUV flux over the star's life; a non-monotone or discontinuous `Leuv(age)` from a track-interpolation regression corrupts the escape budget. Flag interpolation changes that could introduce a discontinuity at a grid boundary.

## Config mutability

Objects that carry user input (the parameter dictionary from `parameters.py`, a `Star` instance's configured attributes) must not be mutated at runtime after initialisation. Flag any code that rewrites a configured value mid-evolution; use local variables instead.

## Cross-module constant duplication

Physical constants (`AU`, `LbolSun`, `Pi`, `Rsun`, `Msun`) are defined in `src/mors/constants.py`. When reviewing code that uses a physical constant, check the import is from `mors.constants` and not re-derived as a literal in a body. A new constant introduced as a bare literal (e.g. `1.496e11` for the AU) is a red flag.

## Test marker discipline

Every test file must begin with a module-level `pytestmark = [pytest.mark.<tier>, pytest.mark.timeout(<budget>)]` (unit/30 s, smoke/60 s, integration/300 s, slow/3600 s). Per-function markers are additive but do not replace the module-level marker; CI runs `pytest -m "(unit or smoke) and not skip"` and any file missing the tier marker ships untested. Real-track model runs belong in the `integration` tier (nightly), not the PR fast gate.

## Test quality (cross-reference)

Test-content rules (anti-happy-path, discriminating-value guards, physics-invariant tiering, `physics_invariant` / `reference_pinned` certification markers, adversarial-review trigger, mocking discipline, `importorskip` + module-constant-monkeypatch traps, cgs-vs-SI unit slips, track-data determinism) live in [`mors-tests.md`](mors-tests.md). When reviewing tests, apply both files: this one for marker discipline and review-pass gate, the deep-dive for the content contract.

## Sister rules (cross-link)

- [`.github/copilot-instructions.md`](../../copilot-instructions.md) "Testing Standards" -- high-level rules visible to all readers. Repo-root `CLAUDE.md` is a symlink to this file.
- [`mors-tests.md`](mors-tests.md) -- test quality deep-dive; the canonical source for anti-happy-path patterns and the validation certification markers.
