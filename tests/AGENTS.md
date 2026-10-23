# MORS test instructions

<!-- fwl-tests-core:begin sha256=0d210e346c572a96 -->
## Test rules shared by the PROTEUS ecosystem

Each test file starts with a module-level tier marker and a timeout. CI selects tests by marker, so a file without one runs in no CI job; the timeout stops a hang, it is not a target.

```python
pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]
```

| tier | what it tests | timeout |
|---|---|---|
| `unit` | Python logic with the heavy physics mocked; aim for < 100 ms | 30 s |
| `smoke` | the real binaries or solvers, one step, low resolution | 60 s |
| `integration` | several modules coupled | 300 s |
| `slow` | full physics validation | 3600 s |

Each test carries exactly one tier marker, so that the tier filters select it in the one CI job meant for it; a function marker for a second tier breaks that. Split a file whose tests need different tiers. `skip` excludes a test from every CI job.

Every new test covers an edge case (a boundary value, an empty input, an extreme physical parameter), exercises the error contract (a documented exception with the check that no side effect ran, a guard, a clamp, or the limit input of the formula), and asserts values that do not follow trivially from the implementation. A pinned value of 1 that every exponent reproduces checks nothing.

`python tools/check_test_quality.py --check` fails when the count of any rule rises above `tools/test_quality_baseline.json`; the offenders it prints are the first few of that rule in the tree, not necessarily yours. The rules: a file without a tier marker, a test without a docstring, a test with one assertion or none, a weak assertion as the only one (`is None`, `is not None`, `> 0`, `len(...) > 0`, `isinstance`), `==` next to a non-zero float literal, and an optional dependency imported without `pytest.importorskip`. `bash tools/validate_test_structure.sh` runs the repository's own structure check; the repository part of this file says what it checks.

Physics tests carry markers so their coverage is tracked apart from line coverage:
- `@pytest.mark.physics_invariant` on each test function that asserts a conservation law, a bound (T > 0, fractions in [0, 1]), a monotonicity or symmetry, or a pinned value with a discrimination guard. The marker goes on the function, not the module: structural tests in the same file do not carry it.
- `@pytest.mark.reference_pinned` (together with `physics_invariant`) on a test that pins a published benchmark, an analytical limit or a cross-implementation result; cite the paper, table or figure in the docstring.
- A discrimination guard asserts that the most plausible wrong formula (a missing factor, a swapped exponent, the wrong unit) gives a result outside the tolerance of the pinned value.

Floats: compare with `pytest.approx` or `np.testing.assert_allclose` and a tolerance you can justify from the method, not the one that makes the test pass.

Mocks: mock at the narrowest scope (the one external call), and return physically plausible values, so the code under test runs its real branches. Set random seeds and write files only under `tmp_path`.

A module-level constant read from an environment variable at import time does not change with `monkeypatch.setenv`; patch the constant with `monkeypatch.setattr`.
<!-- fwl-tests-core:end -->

## MORS specifics

Structure: `src/mors/<file>.py` is tested in `tests/test_<file>.py`. A scenario that runs several sources (a coupled `Star` evolution uses `star.py`, `stellarevo.py`, `rotevo.py` and `physicalmodel.py`) is named after the primary source, and its file docstring names the others. `bash tools/validate_test_structure.sh` checks that every test carries at most one of `unit`, `smoke`, `integration` and `slow` (module, class or function), and `skip` when it carries none.

Tiers: tests of the band, flux and synthesis code with the track lookups mocked are `unit`; tests that read the real Baraffe or Spada tracks are `integration`, need `FWL_DATA`, and run nightly. Smoke tests aim for under 30 s each. The tests need the develop extra: proteus-mpl provides the `validation_plot` fixture. `pytest -m <tier>` runs one tier. CI: pull requests run `pytest -m "(unit or smoke) and not skip"` with the fast coverage gate, the structure check and `check_test_quality.py --check`, which blocks here; the nightly runs all tiers. The [testing page](../docs/How-to/run_tests.md) gives the commands per tier.

### Physics sources and invariants

The physics sources are listed in `AGENTS.md` and in `PHYSICS_SOURCES` of `tools/check_test_quality.py`. Each unit test of a physics source asserts at least one of these; utility sources are exempt from this rule but not from the rest:

- Conservation: `F_bo == F_xr + F_e1 + F_e2 + F_uv + F_pl`; `ScaleTo1AU(ScaleToSurf(f, R)) == f`; angular-momentum balance across a rotation step.
- Bounds: `Lbol`, `Rstar`, `Teff` and `Omega` positive; band fluxes non-negative and a spectrum floored at `1e-20`; percentiles in [0, 100].
- Monotonicity: Planck surface flux rises with `Teff`; main-sequence luminosity rises with mass at fixed age; `Omega` falls with age along a spin-down track; the wavelength grid is strictly ascending after sanitisation.
- A pinned value with a discrimination guard, when a published track value or a closed-form limit is the contract.

A property (monotonicity, conservation, bound) is preferred over a point pin where both are possible. Each physics source has at least one `physics_invariant` and one `reference_pinned` test and a page in `docs/Validation/`; the [Validation overview](../docs/Validation/index.md) lists the cases. `python tools/check_test_quality.py --reference-pinned-status` and `--physics-invariant-status` list the gaps (advisory). The markers are registered in `pyproject.toml` and do not block CI on their own.

### Edge cases and discriminating values

Useful edge cases here: `Omega = 0`, the youngest age of a track, the lowest and highest mass of the grid, a spectrum with a single band or an empty band.


The plausible bugs here are a wrong exponent or factor, a wrong sign, a cgs and SI slip (erg/s against W, cm against m, nm against micron), and a wrong track, band or integrator (Baraffe or Spada, X-ray or EUV, `ForwardEuler` or `RungeKutta4`). A test that pins a value with `pytest.approx` or `assert_allclose` adds a guard for each class: a wrong-value distance, an explicit sign (`val > 0`), a scale window with the unit in the comment (`1e32 < L < 1e34` for a solar-type `Lbol` in erg/s), and a value that separates the chosen track or band from its sibling. When the primary assertion is a conservation closure, the closure covers the exponent class; the sign and scale guards stay.

- Baraffe luminosity: two masses (0.1 and 1.0 Msun), not one, so a wrong track index moves `L` by orders of magnitude.
- Planck surface flux: two temperatures (3000 and 6000 K), so the `T**4` scaling is resolved.
- Track interpolation: an age between grid nodes; at a node every interpolant agrees.
- Band closure: a spectrum with non-trivial flux in each band, not one band at unit flux.

The linter flags a weak assertion only when it is the sole assertion, so the sign and scale guards beside a pin pass. A single assertion is accepted only for a hard-fail invariant (a band closure at `1e-12`) that no other test in the file checks. Delete a test that asserts a fixture's implicit default.

### Tolerances, mocks, constants

- State the reason for a tolerance in a comment when it is not obvious ("`rtol=1e-4` because `WriteTSV` writes `%1.4e`"). Closed-form band algebra holds to `rel=1e-12`; interpolated track output needs a looser tolerance.
- Unit tests mock the track download, file and HTTP access, `scipy.optimize.minimize`, and the real `Value` and `Percentile` lookups (`monkeypatch.setattr(synth, 'Value', fake_Value)`). When a test sets a physics term to zero to isolate another (the Planck flux, to test the XUV budget), its docstring says so and it asserts the degenerate invariant. Never mock the function under test. Smoke, integration and slow tests use the real tracks.
- `hypothesis` is the one optional dependency the linter knows (`OPTIONAL_DEPS`); a new optional dependency is added there. The runtime dependencies (`numpy`, `scipy`, `matplotlib`, `click`, `platformdirs`) need no guard.
- `FWL_DATA` is read into a module constant at import: patch the constant (`monkeypatch.setattr('mors.data.<CONST>', tmp_path, raising=False)`) as well as the environment variable.
- Test parameters use the units of the source, named in a comment (Msun, Myr, `Omega_sun`, erg/s, nm, erg s-1 cm-2 at 1 AU); parametrize ids name the physical scenario (low-mass star, young star, `ForwardEuler`). Write no large outputs.

### Docstrings and names

The file docstring starts with `Tests for src/mors/<file>.py` and lists the invariants and contract clauses it checks. Each test docstring states the physical scenario or contract clause. A comment explains why an input was chosen ("3000 and 6000 K so the `T**4` scaling is resolved"). Names describe behaviour in snake_case (`test_planck_surface_flux_scales_with_temperature`, not `test_planck`); a class groups tests that share setup. Log-capture assertions and the pages under `docs/` follow the public-text rule of `AGENTS.md`; the docs do not cite the agent instruction files.

### Coverage gates

The fast gate (`[tool.mors.coverage_fast]`, unit and smoke, every pull request) and the full gate (`[tool.coverage.report]`, all tiers, nightly) move one way toward 90 % (`ECOSYSTEM_CEILING` in `tools/update_coverage_threshold.py`, which raises them: `--target fast` or `--target full`); never lower one by hand. Most of MORS (rotation evolution, track interpolation, `Star`, `Cluster`) runs only in the integration tier, so the fast gate sits below the full gate. `python tools/check_test_quality.py --baseline` rewrites `tools/test_quality_baseline.json`; run it only after a change that reduced violations.

### Review of test changes

A pull request that adds or changes more than 50 lines under `tests/` (`git diff origin/main...HEAD -- tests/`, over all its commits) gets an independent review of its tests before merge. The reviewer checks the rules above, recomputes a pinned value with the most plausible wrong formula (wrong track, cgs and SI slip) and confirms the test fails with it, and names the invariant each physics test asserts. Fixes go in a follow-up commit whose subject states the outcome. Recurring faults: a loose tolerance that hides a cgs and SI slip, a pinned track value that does not name its track release, an interpolation test at a grid node, a Planck test at one temperature, an environment variable patched after import, an optional import without `importorskip`, a file renamed without its `pytestmark`, and a test that is true for an implicit `None`.
