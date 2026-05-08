# How to build tests

This page is about *writing* a new test, by hand or with an LLM. For running
the existing suite see [running tests](run_tests.md).

## Decision tree: which marker?

The marker is the load-bearing decision. CI currently runs the full test suite on every push and pull request via `coverage run -m pytest` with no marker filtering; slow tests will block CI. Pick the strictest marker the test fits.

!!! warning "Current suite"
    The current test suite does not yet follow these markers. Nevertheless, **new tests should**; current test scripts will be updated soon.

| Use ... | When ... |
|---|---|
| `@pytest.mark.unit` | < 100 ms, no `mors.Star` call. Stellar property helpers, parameter validators, Rossby number calculation, HZ boundary formulas, percentile bisection on synthetic input, unit conversions. |
| `@pytest.mark.smoke` | One full `mors.Star` call at 1 Msun that finishes in seconds. Verifies the whole ODE integration and track-building path runs end to end at relaxed tolerance. |
| `@pytest.mark.integration` | Full `mors.Star` call validated against published reference values. |
| `@pytest.mark.slow` | Cluster evolution, full percentile grids over many masses, anything that takes minutes per test. Tag these now so they can be excluded once marker filtering is added to CI. |

Tests covering more than one tier carry a single marker matching the dominant runtime.

## Choosing a file

Naming convention: `test_<module>_<aspect>.py`, lower-snake, one module per
file where possible.

| Situation | Where the test goes |
|---|---|
| New unit test for an existing module | `test_<module>.py` if it exists, else create it. |
| Branch-coverage test for a hard-to-reach path | `test_<module>_branches.py` |
| Failure-mode test (raises, validation errors) | `test_<module>_failures.py` |
| Smoke / integration track test | `test_<scenario>.py` (e.g. `test_solar_track.py`, `test_HZ_boundaries.py`) |
| Regression for a fixed bug | Add to the closest existing file; do not create one regression file per bug. |

## Float comparisons

Always `pytest.approx`, never `==`.

```python
assert result == pytest.approx(expected, rel=1e-3)
```

Choose the tolerance to match the physics, not the implementation. A
well-converged stellar track matches published Lx values to a few percent,
not 1e-9. State the chosen tolerance with a one-line comment naming the
source or the limiting factor.

## Reference values

Every reference value asserted by a test must come from a primary source
cited inline. Example:

```python
# Kopparapu et al. (2013), Table 1: runaway greenhouse inner edge for sun-like star = 0.97 AU.
assert HZ_inner_runaway_greenhouse == pytest.approx(0.97, rel=1e-2)
```

Do not infer a tolerance from a previous run. If no published reference is
available, the test belongs in the unit tier with a synthetic input whose
expected output you can derive analytically.

## Mocking stellar evolution tracks

Mocking is appropriate when:

- The test isolates a non-track component (the ODE solver, parameter
  validation, a HZ formula) and loading the Spada grid is a confounder.
- The point of the test is an analytic limit (constant Lx, fixed rotation).

Mocking is not appropriate when the test is meant to verify behaviour that
depends on the actual Spada interpolation (mass-dependent tauConv, Icore
evolution, track convergence). For those, use a direct `mors.Star` call.

## Comment hygiene

Inline comments and docstrings should explain *why* the test exists, never
*when it was added* or *what it used to do*. Acceptable:

```python
# Kopparapu et al. (2013), Eq. 2: the flux factor Seff depends on Teff via a fourth-order polynomial. 
# For a solar-type star the runaway greenhouse boundary sits interior to the moist greenhouse boundary, 
# so aOrbHZ['RunawayGreenhouse'] must always be less than aOrbHZ['MoistGreenhouse'].
```

Not acceptable:

```python
# Added to cover the EUV bug found in April.
# Previously rel=1e-6; loosened after the grid reload in commit abc1234.
```

History belongs in the commit message and the PR description, not in the
test source.

## Anti-patterns

- **Forgetting the marker.** CI currently runs all tests, but markers will
  be used for filtering once the suite grows. Add a marker now so slow tests
  can be excluded later without modifying the test itself. Run
  `pytest --collect-only -m unit | tail` to verify pickup.
- **Hardcoding paths.** Use `pathlib.Path(__file__).parent` for relative
  paths, never absolute paths.
- **Test ordering dependence.** Each test must pass in isolation. xdist
  reorders aggressively; relying on side-effects from a previous test is a
  bug, not a shortcut.
- **Asserting on log output.** Logs change for cosmetic reasons; assert on
  return values or state. Use `caplog` only when the log line is itself the
  contract.
- **Mutating the default parameter dictionary.** `params.paramsDefault` is a
  module-level singleton. Always use `params.NewParams()` in tests, never
  modify `paramsDefault` directly.

## Suggested LLM prompt

When asking an LLM (Claude, Cursor, Copilot) to add or modify tests, paste
the prompt below at the start of the request along with the relevant source
file.

````text
You are writing a pytest test for MORS (fwl-mors), a stellar rotation and
XUV evolution package. Follow these rules strictly.

MARKERS (mandatory for future CI filtering):
- @pytest.mark.unit: < 100 ms, no mors.Star call. Use for stellar property
  helpers, parameter validators, Rossby number and HZ formulas, percentile
  bisection on synthetic input, unit conversions.
- @pytest.mark.smoke: one full mors.Star call at 1 Msun that finishes in
  seconds. Use for end-to-end smoke checks of the ODE integration.
- @pytest.mark.integration: full mors.Star call validated against published
  reference values.
- @pytest.mark.slow: cluster evolution, percentile grids, anything that
  takes minutes per test. Tag these so they can be excluded from CI once
  marker filtering is introduced.
Pick the strictest marker the test fits. Do not double-mark.

FLOAT COMPARISONS:
- Always pytest.approx, never ==.
- Choose the tolerance to match the physics (stellar tracks match published
  values to a few percent, not 1e-9).
- State the source or limiting factor in a one-line comment.

REFERENCE VALUES:
- Cite the primary source inline (e.g. Johnstone et al. 2021, Spada et al. 2013,
  Kopparapu et al. 2013). If no source is available, use a synthetic input
  whose expected output you can derive analytically.
- Do not infer tolerances from a previous run.

MOCKING:
- Mock Spada tracks only when the test isolates a non-track component
  (ODE solver, parameter validation, HZ formula). For track-dependent
  physics use a direct mors.Star call.
- Never modify params.paramsDefault directly; always use params.NewParams().

NAMING:
- Files: test_<module>.py, test_<module>_branches.py for hard-to-reach
  paths, test_<module>_failures.py for failure-mode tests.
- Function names: snake_case, descriptive, no test_1 / test_2.

STYLE:
- Single quotes (ruff).
- `from __future__ import annotations` at the top of every file.
- One-line docstring stating the rationale for the test.
- Comments explain WHY, never WHEN added or what the code used to do.
- No project-tracking labels or commit SHAs.

ANTI-PATTERNS:
- No bare assertions on float equality.
- No hardcoded absolute paths.
- No reliance on test execution order.
- No assertions on log content unless the log line is itself the contract.
- Never mutate params.paramsDefault between tests.

OUTPUT:
- Produce only the test source. Do not modify the module under test.
- Place the new test in the appropriate existing file, or name a new file
  per the naming convention.
- After the test, list (a) which marker you chose and why, (b) the
  reference source for any literature value, (c) the tolerance and its
  justification.
````