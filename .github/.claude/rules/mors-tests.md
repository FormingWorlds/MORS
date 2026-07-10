# MORS Test Quality Rules

This file is the canonical deep-dive on test quality. The high-level summary lives in [`.github/copilot-instructions.md`](../../copilot-instructions.md) under "Testing Standards". The two files MUST stay in sync. If you change one, mirror the change in the other.

> **Discovery note.** MORS keeps its Claude-Code rule files under `.github/.claude/rules/` (not the conventional repo-root `.claude/`) so they can be tracked in git and shared across collaborators. Claude does NOT auto-discover them at this path; the repo-root `CLAUDE.md` (symlinked to `.github/copilot-instructions.md`) names this file and `mors-code-review.md` explicitly so AI tooling and human readers know to load them. **When opening or editing any file under `tests/**` or `src/mors/**`, read this file first.**

Sister rule files:

- [`.github/copilot-instructions.md`](../../copilot-instructions.md): high-level rules, applied repo-wide.
- [`.github/.claude/rules/mors-code-review.md`](mors-code-review.md): review-pass gate, domain-aware code review (stellar positivity bounds, cgs-vs-SI unit boundaries, track interpolation, PROTEUS-coupling patterns). Test-marker discipline lives there too.

MORS is scientific simulation code and the test suite is held to physics-grade rigor. Tests exist to catch real bugs. A test that asserts the wrong thing, or that passes for the wrong reason, is worse than no test because it generates false confidence. The rules below codify what "real test" means here.

---

## 1. Anti-happy-path rules (every new test)

Every new test function MUST include:

1. **At least one edge case**: a boundary value (`Omega = 0`, age at the youngest track node, a single-species spectrum, an empty band), an empty input, or an extreme physical parameter (lowest / highest stellar mass on the grid).
2. **At least one path that exercises the error contract**:
   - If the function under test has documented validation (refuses an off-grid mass, raises on an unknown track name), test that the error fires AND that no side effect ran.
   - If the function has no validation (closed-form mathematics: the Planck function, band integrals, flux scaling), exercise the **limit-input behavior** (constant flux over a band integrates to the band width; scaling to the surface and back is the identity) and assert the corresponding mathematical invariant.
   - "No validation in source therefore no error test" is not an exemption; the limit-input substitute is.
3. **Assertion values NOT trivially derivable from the implementation**: discriminating numeric pins (see Section 2) or property-based assertions (monotonicity, conservation, symmetry, boundedness).

### Forbidden patterns

These are flagged by `tools/check_test_quality.py` and rejected at PR time.

- **Single-assert test functions**. Two or more assertions per test; the second usually pins the invariant the first hand-waves over. Exception: a single assertion of a hard-fail invariant (band closure within `1e-12`) is acceptable if it is the only test of that invariant in the file.
- **Weak assertions when they stand alone as the sole meaningful check in the test.** The shapes are:
  - `assert result is not None`
  - `assert result > 0`
  - `assert len(result) > 0`
  - `assert isinstance(result, dict)`
  - `assert result is None` where the function returns `None` implicitly

  Required carve-out: the three-class discrimination guard (Section 2) uses `assert val > 0` as the sign-error guard and `assert lo < val < hi` as the scale-error guard alongside a primary `pytest.approx(...)` pin. Those secondary lines look like weak assertions in isolation; they are NOT flagged when paired with a stronger primary assertion in the same test. The linter applies the carve-out automatically: weak shapes are flagged only when the test has exactly one `assert` statement and that assertion is itself the weak shape.
- **Tests with no function-level docstring**. The docstring states which physical scenario or contract clause is being verified.
- **`==` adjacent to a float literal**. Use `pytest.approx(val, rel=...)` or `np.testing.assert_allclose(actual, expected, rtol=..., atol=...)`. Comparing two floats with `==` is a known flake source even for "exact" identities like 0.0.
- **Tests asserting on a fixture's implicit default**: e.g. `assert fixture_returning_none() is None`. This is trivially true. Delete the test.

---

## 2. Discriminating test values

The test contract is: a regression that introduces a plausible bug must fail the test. "Plausible bug" means off-by-one exponent, wrong sign, swapped factor of 2, missing factor of pi, dimensionally-wrong unit (cgs vs SI), **wrong-track / wrong-band selection**. Pick input values where the wrong-formula result is far from the correct one.

### Bad / good examples

| Pattern | Bad (any-formula-passes) | Good (discriminates) |
|---|---|---|
| Baraffe luminosity `L(M, age)` | Test one solar-mass star only | Test `M = 0.1` AND `M = 1.0` Msun so a wrong track index changes `L` by orders of magnitude |
| Planck surface flux `B(lambda, T)` | Test at one `T` only | Test at `T = 3000` AND `T = 6000` K so the `T**4` scaling is resolved far above tolerance |
| Spada `Value(age, 'Lbol')` | Test at a grid node (interpolation is identity there) | Test at an off-grid age where linear vs nearest-neighbour differ |
| Band-flux closure | One band at unit flux (closure is trivial) | Multi-band spectrum with non-trivial per-band integrals so each band matters |

### Discrimination guard (REQUIRED for pinned-value tests)

When a test pins a numeric value, include explicit assertions that the wrong-formula result would differ from the correct one for **each plausible bug class**. At minimum:

1. **Exponent or factor error** (off-by-one exponent, missing factor of 2 / pi). `abs(val - wrong_value)` discriminates.
2. **Sign error** (`-x` vs `+x`). `abs()` hides this; assert the sign explicitly (`val > 0`).
3. **Unit-conversion error** (cgs vs SI: erg/s vs W, cm vs m; K vs C; nm vs micron). Pin the absolute scale with the unit named in the comment.
4. **Wrong-track / wrong-band selection** (Baraffe vs Spada, ForwardEuler vs RungeKutta integration, X-ray vs EUV band). When the function dispatches by name, the guard MUST include a value that distinguishes the chosen path from a sibling path.

**Carve-out for conservation-style invariants.** When the primary assertion IS a conservation closure (bolometric band closure, scaling round-trip), the equality `sum(parts) == pytest.approx(total)` already discriminates exponent / factor errors by construction. The exponent guard is satisfied by the conservation equality itself; sign and scale guards remain mandatory.

Canonical pattern:

```python
def test_planck_surface_flux_scales_with_temperature():
    """Planck surface flux at 500 nm rises steeply with Teff (Stefan-Boltzmann limit)."""
    f_cool = spectrum.PlanckFunction_surf(np.array([500.0]), Teff=3000.0)
    f_hot = spectrum.PlanckFunction_surf(np.array([500.0]), Teff=6000.0)
    # Wien side at 500 nm: doubling Teff raises the surface flux by well over 10x.
    assert np.all(f_hot > 10.0 * f_cool)
    # Sign / positivity guard: a black-body surface flux is strictly positive.
    assert np.all(f_cool > 0.0)
    # Monotonicity guard: the flux increases with temperature everywhere.
    assert np.all(f_hot > f_cool)
```

The guard lines are mandatory whenever the test's primary assertion is a `pytest.approx` against a hand-calculated or published value. Property-based assertions (monotonicity, conservation, symmetry) do not need a separate guard because they are already discriminating across the input space.

---

## 3. Physics-invariant assertions (tiered)

### When required

Every unit test on a **physics source** must assert at least one of the four invariants below. Physics sources are:

```
src/mors/baraffe.py
src/mors/cluster.py
src/mors/physicalmodel.py
src/mors/rotevo.py
src/mors/spectrum.py
src/mors/star.py
src/mors/stellarevo.py
src/mors/synthesis.py
```

Per-source-file granularity: each physics file should carry at least one `@pytest.mark.physics_invariant` test and at least one `@pytest.mark.reference_pinned` test in its companion test file. Granularity is per source file, not per directory.

Utility sources are exempt from the physics-invariant requirement but still subject to all anti-happy-path rules:

```
src/mors/__init__.py     (re-exports)
src/mors/constants.py    (pure physical constants, no derivation)
src/mors/data.py         (OSF track download)
src/mors/cli.py          (command-line entry point)
src/mors/logs.py         (logger setup)
src/mors/parameters.py   (default parameter dictionary)
src/mors/miscellaneous.py (shared array / index helpers)
```

### The four invariant families

1. **Conservation**
   - Bolometric band closure: `F_bo ≈ F_xr + F_e1 + F_e2 + F_uv + F_pl` within solver tolerance.
   - Spectral scaling round-trip: `ScaleTo1AU(ScaleToSurf(f, R)) ≈ f`.
   - Angular-momentum balance across a rotation-evolution step.
2. **Positivity / boundedness**
   - `L_bol > 0`, `R_star > 0`, `T_eff > 0` everywhere.
   - Band and bolometric fluxes non-negative; a spectrum's flux floored above zero (`>= 1e-20`).
   - Rotation rate `Omega > 0`; distribution percentiles in `[0, 100]`.
3. **Monotonicity or symmetry**
   - Planck surface flux increasing with `T_eff` (Wien / Rayleigh-Jeans behaviour).
   - Main-sequence luminosity increasing with stellar mass at fixed age.
   - Rotation rate decreasing with age along a spin-down track (Skumanich-like braking).
   - Wavelength grid strictly ascending after sanitisation.
4. **Pinned numeric value with a discrimination guard**: see Section 2. Acceptable as the sole invariant when a published track value or closed-form limit is the contract.

Property-based assertions (monotonicity, conservation, symmetry, boundedness) are preferred over point-value pins when both are possible. They hold for any valid input and so catch bugs across the entire input space.

### Validation certification markers

Two markers track validation quality independently of line coverage:

- **`@pytest.mark.physics_invariant`** -- this test asserts at least one of the four invariants. Tag every qualifying test in a physics-source test file.
- **`@pytest.mark.reference_pinned`** -- this test pins behavior against a **published benchmark** (cite the paper, figure, table in the test docstring), an **analytical limit** (the Planck / Stefan-Boltzmann black-body limit, a constant-flux band integral, a spin-down power law), or a **cross-implementation cross-check**.
  - **Per-source-file**: each physics source should have at least one `reference_pinned` test in its companion test file. The specific anchor is chosen by the test author and recorded in `docs/Validation/<file>.md`.
  - **Tracking**: each physics source gets a page at `docs/Validation/<file>.md`, created when the first reference_pinned test for that source lands. The page records the source under test, the reference cited, the test ids carrying the marker, and the date of last comparison.
  - **Status report**: `python tools/check_test_quality.py --reference-pinned-status` reports the physics sources missing a `reference_pinned` test. This is the punch list for follow-up validation work; it is advisory, not blocking.

Both markers are registered in `pyproject.toml` under `[tool.pytest.ini_options] markers`. They do not gate CI on their own.

Current per-source anchor inventory (see `docs/Validation/`):

| Source | Anchor type | Reference |
|---|---|---|
| `baraffe.py` | published benchmark | Baraffe et al. (2015), A&A 577, A42 |
| `stellarevo.py` | published benchmark | Spada et al. (2013), ApJ 776, 87 |
| `star.py` | published benchmark | Spada et al. (2013) via the coupled rotation model |
| `spectrum.py` | analytical limit | Planck black-body surface flux; band-integration closure |
| `synthesis.py` | self-consistency | band-flux budget: `F_bo = sum(bands)`, UV as remainder |
| `physicalmodel.py` | published benchmark | rotation-activity relations *(deferred)* |
| `rotevo.py` | analytical limit | spin-down braking law *(deferred)* |
| `cluster.py` | published benchmark | rotation-rate distribution percentiles *(deferred)* |

Deferred anchors have no `reference_pinned` test yet and appear on the `--reference-pinned-status` punch list.

---

## 4. Mocking discipline

- Default to `unittest.mock` / `monkeypatch` for ALL external calls in unit tests: track-data download, file I/O, HTTP, `scipy.optimize.minimize`, the real evolutionary-track `Value` / `Percentile` lookups.
- Mock at the **narrowest scope**: patch the specific function (`monkeypatch.setattr(synth, 'Value', fake_Value)`), not the whole module.
- A mocked physics function MUST return **physically plausible** values. A mock that returns `0.0` or `1.0` for everything will mask sign / scaling / fallback bugs. When the true physics is nulled for isolation (e.g. Planck flux set to zero to isolate the XUV budget), state that in the test docstring and assert the corresponding degenerate invariant.
- NEVER mock the function under test. If you're tempted to, the test is asking the wrong question.
- Smoke tests use the real track model on a single star / age; integration and slow tests run the full evolution. The rules in this file still apply to those tiers, but the mocking discipline is relaxed because the real call is the contract.

---

## 5. Optional-dependency imports

Any test that imports an optional dependency MUST call `pytest.importorskip` at module top so `pip install --no-deps` CI runs do not fail collection:

```python
import pytest

hypothesis = pytest.importorskip('hypothesis')
```

Optional deps recognized by the linter (`OPTIONAL_DEPS` constant in `tools/check_test_quality.py`): `hypothesis`. MORS's runtime dependencies (`numpy`, `scipy`, `matplotlib`, `click`, `osfclient`, `platformdirs`, `zenodo_get`) are always installed and do not need a guard. Any test that adds a new optional dependency must extend `OPTIONAL_DEPS`.

---

## 6. Module-level constants and `monkeypatch`

When the source under test reads an env var into a **module-level constant** at import time, `monkeypatch.setenv` alone is not sufficient; the constant is frozen at the original import. MORS resolves the `FWL_DATA` data directory this way. Patch the constant directly:

```python
# Test (wrong):
monkeypatch.setenv('FWL_DATA', str(tmp_path))          # too late for an already-frozen constant

# Test (right, when the source froze the path at import):
monkeypatch.setattr('mors.data.<CONST>', tmp_path, raising=False)
```

When in doubt, do both the env-var monkeypatch and the constant monkeypatch. The lint script does NOT flag this pattern; it is a discipline rule enforced via the >50 LOC review trigger and the recurring-trap table in Section 16.

---

## 7. Marker discipline and timeouts

### Module-level marker is mandatory

Every test file MUST begin with:

```python
import pytest

pytestmark = [pytest.mark.<tier>, pytest.mark.timeout(<budget>)]
```

with budgets:

- `unit` -> `timeout(30)` (target wall-time per test is `< 100 ms`; the 30 s cap is a defensive net).
- `smoke` -> `timeout(60)` (target `< 30 s`).
- `integration` -> `timeout(300)`.
- `slow` -> `timeout(3600)`.

PR CI runs `pytest -m "(unit or smoke) and not skip"`. Tests without the tier marker are invisible to CI and shipped untested. The lint script blocks any file missing the module-level `pytestmark`.

The MORS tier split: tests that only touch pure-Python band / flux / synthesis math with mocked track lookups are `unit`; tests that download and run the real Baraffe / Spada tracks are `integration` (they need `FWL_DATA` and network, and run in nightly, not on every PR).

### Per-function markers

Per-function `@pytest.mark.<tier>` markers are **additive**, not a replacement for the module-level marker. They are useful when a file's tests span multiple tiers (rare; prefer separate files).

### Timeout is a safety net, not a target

The `timeout` ceiling exists so a future regression that introduces a hang (a track download retry loop, an integration that fails to converge) surfaces as a specific-test failure rather than a generic job timeout.

---

## 8. Float and numerical comparison

- NEVER use `==` for floats. Use `pytest.approx(val, rel=1e-5)` or `np.testing.assert_allclose(actual, expected, rtol=..., atol=...)`.
- State the tolerance rationale in a comment when the choice is non-obvious. E.g. "`rtol=1e-4` because `WriteTSV` uses `fmt='%1.4e'`".
- For pinned numeric values, include a **discrimination guard** (Section 2).
- For property-based assertions, use `pytest.approx` against the exact symbolic relation, with the tightest tolerance the implementation can hit (typically `rel=1e-12` for closed-form band algebra; looser for interpolated track outputs).

---

## 9. Voice rule for test artifacts

The repo-wide voice rule (zero AI-process disclosure in any public artifact) applies to test code with the same strictness as to source. The voice rule is **scoped** to public artifacts other contributors and external readers see; it does NOT apply to the rule documents themselves (this file, `mors-code-review.md`, `copilot-instructions.md`), which legitimately name the procedures they define.

In scope (the voice rule is BANNED here):

- Test-skip reasons (`@pytest.mark.skip(reason='...')`).
- Test-file and test-function docstrings.
- Test-function and test-class names.
- Parametrize ids.
- Log-capture assertions.
- Commit messages on test-touching commits (subject AND body).
- **Pull-request titles and bodies on test-touching PRs**.
- GitHub Actions job names and step names.
- Inline source comments and docstrings on `src/mors/**`.
- Log strings that ship with the repo.
- **All public-facing documentation** (anything under `docs/`, the repo README, CONTRIBUTING.md, tutorials). Public docs apply the rule silently; they do NOT enumerate the banned phrases, name the voice rule, advertise the existence of `.github/.claude/` rule infrastructure, or cross-reference `.github/.claude/rules/*.md` files.

Out of scope (these may NAME the procedures they define): this file, `mors-code-review.md`, `copilot-instructions.md`.

Banned phrases inside the in-scope artifacts: "audit", "review pass", "adversarial review", "Phase X" (AI-organized roadmap labels), "T1.x", "Group A/B/C/D" (AI-organized work groups), `claude-config/...` paths, "Generated with Claude", AI-tool names, em-dashes, en-dashes (except in bibliographic page ranges within citations), process meta-commentary ("after careful analysis").

Write the OUTCOME (what the test verifies; what the PR achieves) never the PROCESS. First-person Tim voice. Going-forward only, no history rewrite.

---

## 10. Fixture and parameter conventions

- Use the source's expected units in test parameters and NAME the unit in a comment (MORS mixes cgs and SI; see `mors-code-review.md`). Stellar mass in Msun, age in Myr, Omega in Omega_sun, luminosity in erg/s, wavelength in nm, flux at 1 AU in W/m^2.
- Use `@pytest.mark.parametrize` when the same logic spans multiple physical regimes (low-mass vs solar-mass star, young vs old age, ForwardEuler vs RungeKutta integration). Each parametrize id must read like a physical scenario, not a tuple of numbers.
- Set seeds for any randomness: `np.random.seed(42)`, `random.seed(42)`.
- Use `tmp_path` (pytest fixture) for temporary files. Do not produce large outputs in the test path.

---

## 11. Documentation per test

- **File-level docstring**: name the source file under test (`Tests for src/mors/<file>.py`), list the invariants and contract clauses the file exercises. Required.
- **Function-level docstring**: state the physical scenario or contract clause in plain language. Required (lint-enforced).
- **Inline comments**: explain **why** a specific input range was chosen ("`T = 3000` K and `T = 6000` K so the `T**4` surface-flux scaling is resolved well above tolerance").

---

## 12. Naming

- Test names describe behavior, not the called function: `test_planck_surface_flux_scales_with_temperature`, NOT `test_planck`.
- Test names use snake_case and read as full sentences.
- Group related tests in classes (`class TestBandFluxes:`) when they share setup.
- Test file names mirror source where practical: `src/mors/<file>.py` -> `tests/test_<file>.py`. When a single scenario exercises several sources (a coupled `Star` evolution touches `star.py`, `stellarevo.py`, `rotevo.py`, `physicalmodel.py`), name the file after the primary source under test and cross-reference the others in the file docstring.

---

## 13. Adversarial review trigger

A pull request that adds or substantially modifies **> 50 lines of test code across all its commits** triggers an independent review pass before merge. This is a discipline rule, not CI-automated: the author runs the review pass before pushing the final test-touching commit. The denominator is PR-level, not per-commit: `git diff origin/main...HEAD -- 'tests/**'` is the source of truth. Splitting one large change into 49 + 49 line commits does NOT dodge the trigger.

The reviewer's mandate:

- Cite the anti-happy-path rule (Section 1) and the discrimination-guard requirement (Section 2).
- Flag single-assert tests, weak `is not None` patterns, missing module-level marker, missing `physics_invariant` tag on a physics-source test, missing `reference_pinned` tag on a per-source benchmark test, dead tests (passes for the wrong reason), tests that mock the function under test.
- Verify discriminating values: re-derive the expected value from a plausible wrong formula (wrong track, cgs-vs-SI slip) and confirm the test fails with that wrong formula.
- Verify physics-source coverage of the four invariants: which of the four does this test exercise?

The reviewer's findings are addressed in a follow-up commit (not amended into the test commit). The follow-up subject describes the OUTCOME ("sharpen the Baraffe luminosity assertions to distinguish the 0.1 and 1.0 Msun tracks"), never the process.

---

## 14. Tooling

The repo provides:

- `bash tools/validate_test_structure.sh` -- structural check (module-level tier marker on every test).
- `python tools/check_test_quality.py --check` -- CI mode: AST scan for the forbidden patterns in Section 1 and the marker requirement in Section 7. Fails the PR if violations exceed the baseline.
- `python tools/check_test_quality.py --baseline` -- after a deliberate sweep, regenerates `tools/test_quality_baseline.json`. Only run when you have intentionally reduced violations.
- `python tools/check_test_quality.py --reference-pinned-status` -- prints physics sources missing a `reference_pinned` test.
- `python tools/check_test_quality.py --physics-invariant-status` -- prints physics-source tests asserting no invariant and not tagged.
- `python tools/update_coverage_threshold.py` -- ratchet the coverage gates upward when measured coverage exceeds the current `fail_under`. Capped at the 90% ecosystem ceiling.
- `ruff check src/ tests/` and `ruff format src/ tests/` -- run before commit.

The lint script is wired into PR CI (`tests.yaml`). The step runs in **blocking** mode: any regression above the baseline fails the PR.

---

## 15. Coverage strategy (operator's view)

MORS uses two coverage gates. The fast gate is for PR cycle time; the full nightly gate is the long-running KPI.

| Gate | Tests | Target | When |
|---|---|---|---|
| Fast gate (`tool.mors.coverage_fast`) | unit + smoke | ratcheting toward **90%** | Every PR |
| Full gate (`tool.coverage.report`) | unit + smoke + integration + slow | ratcheting toward **90%** | Nightly |

The ratchet is one-way (`tools/update_coverage_threshold.py`), capped at 90%. Never manually decrease the threshold. The CI guard in `.github/workflows/tests.yaml` rejects any PR that lowers `[tool.coverage.report].fail_under` below `min(base_ref, 90.0)`.

MORS's structural reality: most of the physics (rotation evolution, track interpolation, the `Star` and `Cluster` classes) runs only under the real-track `integration` tier, which lives in nightly. The PR fast gate therefore covers the mocked unit surface (band math, synthesis, spectrum) and starts well below 90; it climbs as mocked unit tests are added. The nightly full gate climbs as the real-track tier deepens. The two gates are different numbers on purpose.

---

## 16. Failure modes to recognize on review

| Pattern | Example | Why it slipped | Fix |
|---|---|---|---|
| **cgs-vs-SI unit slip** | A luminosity assertion expects `~1e33` (erg/s, cgs) but the source returns W (SI), or a radius in cm vs m | The test tolerance is loose enough to pass, or the expected value was copied from the wrong-unit branch | Name the unit in the assertion comment; add a scale guard (`1e32 < L < 1e34` for a solar-type Lbol in erg/s) |
| **Track-data determinism** | An `integration` test downloads a track on first run; a later refresh changes the cached file and the pinned value drifts | The pinned value is tied to a specific track release but the test does not name it | Cite the track paper AND release in the docstring; pin with a tolerance that reflects the interpolation, not the download |
| **Grid-node degeneracy** | Interpolation test evaluated only at a grid node, where linear and nearest-neighbour agree | The node is a fixed point of every interpolant | Evaluate off-grid where interpolants diverge (Section 2) |
| **Planck degeneracy** | Planck test at a single temperature | `T**4` scaling is untested with one point | Two temperatures far apart so the scaling is resolved |
| **Module-level constant patched only via env var** | `monkeypatch.setenv('FWL_DATA', ...)` on a source that read it at import time | Constants are frozen at import; setenv is too late | `monkeypatch.setattr('mors.<mod>.CONST', ...)` in addition to setenv |
| **Optional dep imported unconditionally** | `import hypothesis` at module top | `pip install --no-deps` build skips the optional install | `pytest.importorskip('hypothesis')` at module top |
| **Stale marker after refactor** | File renamed without re-applying the module-level `pytestmark` | CI marker filter passed via per-function markers; coverage tier became invisible | Restore module-level `pytestmark = [pytest.mark.<tier>, pytest.mark.timeout(<budget>)]` |
| **Trivially-true on implicit None** | `def test_x(fixture): assert fixture is None` where the fixture returns None implicitly | Test passes for the wrong reason | Delete the test |

When you spot a new variant of these, add it here.

---

## 17. Sister rules (cross-link)

- `.github/copilot-instructions.md` "Testing Standards" -- the high-level summary readers without `tests/**` context see first.
- `.github/.claude/rules/mors-code-review.md` "Test marker discipline" -- the review-pass gate that backs up the rules in this file. Also contains domain-aware physics checks (stellar positivity bounds, cgs-vs-SI unit boundaries, track interpolation, PROTEUS-coupling patterns) that apply when reviewing the **source** code that tests cover.

Any change to the rule set: update both files in the same commit and call out the cross-reference in the commit body.
