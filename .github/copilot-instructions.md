# MORS AI Agent Guidelines

**Trust these instructions.** Only search if information is incomplete or found to be in error.

**Identity & Mission**: You are an expert Scientific Software Engineer working on the MORS module of the PROTEUS ecosystem.

## High-Level Instructions

> ### Rule files you MUST read on every session
>
> MORS keeps its Claude-Code rule files under `.github/.claude/rules/` (NOT the conventional repo-root `.claude/`, which is gitignored and so cannot be shared with collaborators). Claude Code does NOT auto-discover the rules at this unusual path. Read them explicitly at the start of every session and any time you open a related file:
>
> - [`.github/.claude/rules/mors-tests.md`](.claude/rules/mors-tests.md) -- test quality deep-dive: anti-happy-path patterns, discriminating-value guards, physics-invariant tiering, validation certification markers, adversarial-review trigger, track-data determinism, band-flux closure assertions. **Required reading before editing any file under `tests/**` or `src/mors/**`.**
> - [`.github/.claude/rules/mors-code-review.md`](.claude/rules/mors-code-review.md) -- review-pass gate, domain-aware physics review (stellar positivity bounds, cgs-vs-SI unit boundaries, track interpolation, PROTEUS-coupling patterns). **Required reading before any code review pass.**
>
> These two files plus this one are the canonical sources of truth for testing rigor and review criteria. Together they enforce MORS's extreme-rigor stance on physics validity, anti-happy-path testing, and validation certification.

1. **Always** read the two rule files above plus the Testing Standards section below before any code change.
2. **Always** inform the user that you are reading in this file by printing a message at the start of your response: "(Read in copilot-instructions.md...)"
3. When creating a PR, **always** follow the PR template (`.github/pull_request_template.md`) and ensure all sections are filled out with relevant information.
4. **Claude-specific**: `CLAUDE.md` is a symlink to this file. Session learnings, plans, and memories live in `~/.claude/projects/<repo>/memory/`; they do NOT live in this repository.

## Ecosystem Context

MORS is the stellar rotation and activity evolution module of the PROTEUS ecosystem. It evolves a star's rotation, luminosity, radius, and high-energy (X-ray, EUV, UV) emission over time from published evolutionary tracks, and synthesises the stellar spectrum that PROTEUS uses to drive atmospheric heating and escape. It is called by the main [PROTEUS](https://github.com/FormingWorlds/PROTEUS) coupled atmosphere-interior framework during the stellar-evolution step and is also usable standalone.

Sister modules in the ecosystem: AGNI (atmospheric radiative transfer), SOCRATES (spectral radiative transfer), JANUS (1D convective atmosphere), CALLIOPE (volatile in-/outgassing), ARAGOG / SPIDER (interior thermal evolution), VULCAN (atmospheric chemistry), ZEPHYRUS / BOREAS (atmospheric escape), Obliqua (tidal evolution).

**Project Type**: Scientific simulation module (Python).

**Languages**: Python 3.11+.

**Size**: 15 source files in `src/mors/`.

**Target Runtime**: Python 3.11+ on Linux / macOS.

## Build & Validation

### Environment Setup

**Prerequisites**:

1. Python 3.11, 3.12 or 3.13 (via conda / miniforge or system).
2. Git.
3. `FWL_DATA` environment variable pointing at a data directory; MORS downloads its evolutionary tracks (Baraffe 2015, Spada 2013) there on first use.

**Developer Install**:

```bash
git clone git@github.com:FormingWorlds/MORS.git
cd MORS
pip install -e ".[develop]"
pre-commit install -f
```

MORS has no compiled dependencies: a plain `pip install` is sufficient. When working alongside PROTEUS, the recommended pattern is editable-install via `pip install -e MORS/.` from the PROTEUS tree so changes propagate without re-install.

### Test Commands

**Run all tests**:

```bash
pytest
```

**Run by category** (matches CI):

```bash
pytest -m "(unit or smoke) and not skip"     # What PR checks run
pytest -m unit                                # Fast unit tests (<100ms each, mocked track lookups)
pytest -m smoke                               # Real track lookup, single star/age (reserved)
pytest -m integration                         # Real evolution-track model runs (nightly)
pytest -m slow                                # Full physics validation (nightly)
```

The `integration` tier downloads and runs the real Baraffe / Spada tracks and needs `FWL_DATA` set; it runs nightly, not on every PR.

**With coverage** (matches nightly CI):

```bash
coverage run -m pytest -m "(unit or smoke or integration or slow) and not skip"
coverage report
coverage html
```

**Coverage thresholds** (in `pyproject.toml`; one-way, never manually decreased, raised toward 90 by `tools/update_coverage_threshold.py` as coverage improves):

- Fast gate (`[tool.mors.coverage_fast]`, unit + smoke, every PR): ratcheting toward **90%** (the PROTEUS-ecosystem ceiling). Because most of MORS is exercised only by the real-track `integration` tier, the fast gate starts well below 90 and ratchets up as mocked unit coverage grows.
- Full gate (`[tool.coverage.report]`, unit + smoke + integration + slow, nightly): ratcheting toward **90%**.

**Validate test structure**:

```bash
bash tools/validate_test_structure.sh
```

**Test quality lint** (blocking on PRs):

```bash
python tools/check_test_quality.py --check
```

### Lint Commands

**Always run before committing**:

```bash
ruff check src/ tests/        # Check for issues
ruff check --fix src/ tests/  # Auto-fix issues
ruff format src/ tests/       # Format code
```

**Pre-commit hook** (runs automatically on commit):

```bash
pre-commit install -f
```

Pre-commit runs on the files a commit touches. Legacy modules carry lint debt that is cleaned incrementally as files are edited, not in a single sweep.

### Validation Pipeline

**CI runs on PRs** (`.github/workflows/tests.yaml`):

1. **Unit + smoke tests**: `pytest -m "(unit or smoke) and not skip" --cov=mors`.
2. **Fast coverage gate**: `[tool.mors.coverage_fast].fail_under` checked against the unit + smoke coverage.
3. **Test structure**: `bash tools/validate_test_structure.sh`.
4. **Test quality**: `python tools/check_test_quality.py --check` (blocking).
5. **Coverage ratchet guard**: rejects any PR that lowers either `[tool.coverage.report].fail_under` (full gate) or `[tool.mors.coverage_fast].fail_under` (fast gate) below `min(base_ref, 90.0)`.

`.github/workflows/code-style.yaml` runs pre-commit (ruff) on the files a PR changes.

**All must pass** before merge. Coverage thresholds move one way: the guard blocks lowering, and they are raised as coverage improves (never decrease).

**Nightly CI** (`.github/workflows/nightly.yml`):

- Full suite: `pytest -m "(unit or smoke or integration or slow) and not skip"`.
- Coverage uploaded to Codecov.
- The full-gate `fail_under` from `[tool.coverage.report]` is enforced.

## Project Layout

### Key Directories

- `src/mors/` - Main Python source code (flat layout, 15 files)
  - `__init__.py` - Re-exports (utility)
  - `constants.py` - Physical constants (utility)
  - `data.py` - OSF track-data download (utility)
  - `cli.py` - Command-line entry point (utility)
  - `logs.py` - Logger setup (utility)
  - `parameters.py` - Default parameter dictionary (utility)
  - `miscellaneous.py` - Shared helpers: array loading, index lookups, emission integrals (utility)
  - `baraffe.py` - Baraffe 2015 evolutionary-track interpolation: luminosity, radius, solar constant (physics)
  - `stellarevo.py` - Spada 2013 stellar-evolution-track loading and interpolation (physics)
  - `rotevo.py` - Rotation-evolution integration: spin-down torques (physics)
  - `star.py` - `Star` class: coupled rotation + activity evolution, `Value` / `Percentile` lookups (physics)
  - `physicalmodel.py` - Rotation-activity relations, high-energy emission model (physics)
  - `cluster.py` - `Cluster` class: rotation-rate distribution percentiles (physics)
  - `spectrum.py` - Stellar spectra from band-integrated fluxes; Planck function; band definitions (physics)
  - `synthesis.py` - Historical spectral synthesis: band scaling of XUV emission (physics)

- `tests/` - Test suite. Each physics source has a companion test file at `tests/test_<file>.py` as coverage grows. `tools/validate_test_structure.sh` enforces that every test carries a tier marker.

- `tools/` - Build / utility scripts
  - `check_test_quality.py` - AST linter (blocking on PRs)
  - `update_coverage_threshold.py` - One-way coverage ratchet (capped at 90)
  - `check_file_sizes.sh` - Line-cap hook on this file
  - `validate_test_structure.sh` - Module-level marker validator
  - `generate_test_badges.py` - Shields.io endpoint-badge JSON generator (total / unit / integration counts)

- `docs/` - Documentation (Zensical; Diátaxis structure)
  - `Explanations/` - Concept pages (rotation, activity, spectral synthesis, habitable zone, testing)
  - `How-to/` - Task guides (installation, usage, run_tests, ...)
  - `Tutorials/` - Worked examples
  - `Reference/` - API + publications
  - `Validation/<file>.md` - Per-source-file inventory of `@pytest.mark.reference_pinned` tests (created when the first such test lands)

### Configuration Files

- `pyproject.toml` - Package metadata, pytest config, coverage thresholds (fast + full gates), ruff rules.
- `mkdocs.yml` - Documentation configuration (used by Zensical).
- `.github/workflows/` - CI / CD pipelines
  - `tests.yaml` - PR validation (unit + smoke + test-quality + ratchet guard)
  - `nightly.yml` - Full suite with coverage upload to Codecov
  - `code-style.yaml` - Pre-commit (ruff) on changed files
  - `docs.yaml` - Documentation build
  - `publish-test-badges.yml` - Refreshes the test-count badge JSON on the `badges` branch
  - `publish.yaml` - PyPI release on tag

### Entry Points

- **Python API**: `import mors; star = mors.Star(Mstar=1.0, Omega=1.0); star.Value(age_myr, 'Lbol')`.
- **CLI**: `mors` (defined in `src/mors/cli.py`).

## Testing Standards

MORS is scientific simulation code, so the test suite is held to physics-grade rigor. The rules below are the contract; the deep-dive (anti-happy-path patterns, discriminating-value guards, certification markers, adversarial-review trigger, track-data determinism, band-flux closure assertions) lives in [`.github/.claude/rules/mors-tests.md`](.claude/rules/mors-tests.md). Read that file before editing any test file or any source file under `src/mors/**`. The two files must be kept in sync; if you change one, mirror the change in the other.

### Structure

- Tests live in `tests/`; each physics source gets a companion `tests/test_<file>.py` as coverage grows.
- Framework: `pytest` exclusively in the `tests/` directory.

### Markers and the module-level marker rule

Tier markers, with their CI surface and per-test wall-time budgets:

| Marker | What it tests | Speed budget | When CI runs it |
|---|---|---|---|
| `@pytest.mark.unit` | Python logic, track lookups mocked | < 100 ms per test | Every PR (`unit and not skip`) |
| `@pytest.mark.smoke` | Real track lookup, single star / age | < 30 s per test | Every PR (`smoke and not skip`) |
| `@pytest.mark.integration` | Real evolution-track model runs | Minutes per test | Nightly only |
| `@pytest.mark.slow` | Full physics validation | Up to hours per test | Nightly only |
| `@pytest.mark.skip` | Placeholder, deliberately disabled | n/a | Never |

**Mandatory module-level marker** (no exceptions): every test file begins with

```python
pytestmark = [pytest.mark.<tier>, pytest.mark.timeout(<budget>)]
```

with timeouts: 30 s for unit, 60 s for smoke, 300 s for integration, 3600 s for slow. Per-function markers are additive but do not replace the module-level marker. CI runs `pytest -m "(unit or smoke) and not skip"`; tests without a tier marker are invisible to CI. The `pytest-timeout` ceiling is a defensive net against future regressions that introduce a hang.

### Physics validity

Every unit test on a **physics source** (`baraffe.py`, `cluster.py`, `physicalmodel.py`, `rotevo.py`, `spectrum.py`, `star.py`, `stellarevo.py`, `synthesis.py`) must assert at least one of:

- **Conservation**: bolometric band closure (`F_bo == sum of band fluxes` within tolerance); spectral scaling round-trip (`ScaleTo1AU(ScaleToSurf(f)) == f`); angular-momentum balance in the spin-down integration.
- **Positivity / boundedness**: `L_bol > 0`, `R_star > 0`, `T_eff > 0`, band and bolometric fluxes non-negative, rotation rate `Omega > 0`, percentiles in `[0, 100]`.
- **Monotonicity or symmetry**: Planck surface flux increasing with `T_eff`; main-sequence luminosity increasing with stellar mass at fixed age; rotation rate decreasing with age along a spin-down track.
- **Pinned numeric value with a discrimination guard**: a published track value or closed-form limit pinned via `pytest.approx` / `assert_allclose`, accompanied by explicit assertions that a wrong-formula / wrong-track / wrong-unit result would differ from the correct one by more than the tolerance.

Utility sources (`__init__.py`, `constants.py`, `data.py`, `cli.py`, `logs.py`, `parameters.py`, `miscellaneous.py`) are **exempt** from the physics-invariant requirement but still subject to the anti-happy-path rules.

Tag every test that asserts a physical invariant with `@pytest.mark.physics_invariant`. Per-source-file granularity: each physics file should carry at least one such test in its companion test file.

### Reference-pinned validation

Tag tests that pin against a published benchmark, an analytical limit, or a cross-implementation cross-check with `@pytest.mark.reference_pinned`. Each physics file should have at least one such test. The specific anchor is chosen by the test author and recorded in `docs/Validation/<file>.md` (created when the first reference_pinned test for that source lands). The `--reference-pinned-status` mode of the linter reports the punch list of physics sources still missing a reference_pinned test.

### Anti-happy-path rules (every new test)

Every new test function MUST include:

1. **At least one edge case** (boundary value, empty input, extreme physical parameter).
2. **At least one path that exercises the error contract** (documented exception, guard return, graceful clamp). If the function under test has no validation, exercise the limit-input behavior and assert the mathematical invariant.
3. **Assertion values that are NOT trivially derivable from the implementation**: discriminating numeric pins or property-based assertions (monotonicity, conservation) preferred over point checks.

**Forbidden patterns** (flagged by `tools/check_test_quality.py`):

- Single-assert test functions.
- Standalone weak assertions (`assert result is not None`, `assert result > 0`, `assert len(result) > 0`, `assert isinstance(result, dict)`) as the only meaningful check.
- Tests with no function-level docstring.
- Tests using `==` adjacent to float literals.
- Tests asserting on a fixture's implicit default.

### Float and numerical comparison

NEVER use `==` for floats. Use `pytest.approx(val, rel=1e-5)` or `np.testing.assert_allclose(actual, expected, rtol=..., atol=...)`. For pinned numeric values, include a **discrimination guard**: a follow-up `assert` showing the wrong-formula / wrong-track / wrong-unit value would differ from the correct one by more than the tolerance. See `mors-tests.md` Section 2 for the canonical pattern.

### Mocking discipline

- Default to `unittest.mock` / `monkeypatch` for ALL external calls in unit tests: track-data download, file I/O, `scipy.optimize`, the real evolutionary-track lookups.
- Mock at the narrowest scope: a specific function, not a whole module.
- A mocked physics function must return **physically plausible** values; a mock that returns `0.0` or `1.0` for everything can mask real bugs.
- NEVER mock the function under test.
- Smoke / integration / slow tiers use the real track model.

### Optional-dependency imports

Any test that imports an optional dependency MUST call `pytest.importorskip('<dep>')` at module top. The `pip install --no-deps` CI image will otherwise fail to collect.

### Voice rule for test artifacts

The repo-wide voice rule (zero AI-process disclosure in any public artifact) applies to test code with the same strictness as to source. Scope: test-skip reasons, test-file / function docstrings, test-function / class names, parametrize ids, log-capture assertions, **commit messages on test-touching commits, pull-request titles and bodies on test-touching PRs**, GitHub Actions job / step names, inline `src/mors/**` comments, and shipped log strings. Out of scope: the rule documents themselves (this file, `mors-tests.md`, `mors-code-review.md`) may legitimately name the procedures they define. Public documentation under `docs/` applies the rule silently: it does not enumerate banned phrases, name the voice rule, or cross-reference `.github/.claude/rules/*.md`.

Write the OUTCOME, never the PROCESS.

### Speed and determinism

- Unit tests: < 100 ms wall-time each.
- Aggressively mock heavy track lookups and downloads in unit tests.
- Set seeds for any randomness: `np.random.seed(42)`, `random.seed(42)`.
- Use `tmp_path` (pytest fixture) for temporary files.

### Documentation per test

- File-level docstring: name the source under test, list the invariants and contract clauses the file exercises.
- Function-level docstring: state the physical scenario or contract clause being verified. Required (lint-enforced).
- Inline comments: explain **why** a specific input range was chosen.

### Independent review trigger

A pull request that adds or substantially modifies > 50 lines of test code across all its commits triggers an independent review pass before merge. The denominator is PR-level (`git diff origin/main...HEAD -- 'tests/**'`); splitting into many sub-50-line commits does not dodge the trigger. The reviewer cites the anti-happy-path rule, the discrimination-guard requirement, and the physics-invariant tier.

### Tooling

- Validate test structure: `bash tools/validate_test_structure.sh`
- Test-quality lint: `python tools/check_test_quality.py --check`
- Baseline regeneration (after a deliberate sweep): `python tools/check_test_quality.py --baseline`
- Reference-pinned status: `python tools/check_test_quality.py --reference-pinned-status`
- Coverage ratchet (one-way, capped at 90): `python tools/update_coverage_threshold.py`
- Format: `ruff format src/ tests/`
- Lint: `ruff check src/ tests/`

### Coverage architecture

MORS uses two gates with explicit sub-targets:

| Gate | Tests included | Target | Enforced |
|---|---|---|---|
| Fast gate (`tool.mors.coverage_fast.fail_under`) | unit + smoke | Ratcheting toward **90%** | Every PR |
| Full gate (`tool.coverage.report.fail_under`) | unit + smoke + integration + slow | Ratcheting toward **90%** | Nightly |

Both gates ratchet toward 90, capped at 90 (`tools/update_coverage_threshold.py` enforces `ECOSYSTEM_CEILING = 90.0`); neither may be manually decreased. The CI guard in `tests.yaml` rejects any PR that lowers `[tool.coverage.report].fail_under` below `min(base_ref, 90.0)`. Most of MORS's line coverage comes from the real-track `integration` tier in nightly; the PR fast gate covers the mocked unit surface only, so the two gates sit at different values while both climb toward 90.

## Safety & Determinism

- **Randomness**: explicitly set seeds in tests.
- **Files**: do not generate tests that produce large output files; use `tempfile` or mocks.

## Code Quality

**Style** (enforced by ruff):

- Line length < 96 chars.
- Variables / functions: the existing code uses mixed casing (`Value`, `Percentile`); match the surrounding file rather than renaming.
- Constants: `UPPER_CASE`.
- Type hints: standard Python.
- Docstrings: brief descriptions of physical scenarios.

**Pre-commit**: runs `ruff check --fix` automatically on changed files. Fix issues before committing.

## Common Workflows

### Making a Code Change

1. **Create branch**: `git checkout -b <initials>/<short-description>`.
2. **Make changes** in `src/mors/`.
3. **Write / update tests** in `tests/test_<file>.py`.
4. **Run tests locally**: `pytest -m "(unit or smoke) and not skip"`.
5. **Check coverage**: `pytest --cov=mors --cov-report=html`.
6. **Lint**: `ruff check --fix src/ tests/ && ruff format src/ tests/`.
7. **Validate structure**: `bash tools/validate_test_structure.sh`.
8. **Test quality**: `python tools/check_test_quality.py --check`.
9. **Commit**: plain-language subject, first-person voice, no AI-process disclosure.
10. **Push**: CI runs automatically on PR.

### Adding a New Physics Source

1. Create `src/mors/<file>.py`.
2. Create `tests/test_<file>.py` with module-level `pytestmark`.
3. Add at least one `@pytest.mark.physics_invariant` test asserting one of the four invariant families.
4. Plan a `@pytest.mark.reference_pinned` test (anchor: paper, analytical limit, or cross-check); create `docs/Validation/<file>.md` when it lands.
5. Run the full PR checks locally.

### Debugging Test Failures

```bash
pytest -v --showlocals                          # Verbose with local variables
pytest -x                                       # Stop at first failure
pytest tests/test_<file>.py::test_function      # Run specific test
pytest --pdb                                    # Drop into debugger on failure
```

## Documentation References

- **Testing rules**: `.github/.claude/rules/mors-tests.md`, `.github/.claude/rules/mors-code-review.md`
- **Test how-to**: `docs/How-to/run_tests.md`
- **Testing overview**: `docs/Explanations/testing.md`
- **Installation**: `docs/How-to/installation.md`
- **Concepts**: `docs/Explanations/rotation.md`, `docs/Explanations/activity.md`, `docs/Explanations/spectral_synthesis.md`
- **PROTEUS coupling**: `docs/Explanations/proteus.md`

## Project memory and session learnings

Session-specific knowledge (debugging logs, design rationale, sprint focus, ADR drafts) lives outside this repository, in the Claude memory tree under `~/.claude/projects/<project>/memory/`. The memory tree is per-user, sync-ready across machines, and not exposed in public commit history.

What still lives in this repository:

- Architectural decisions that affect every contributor: this file (`.github/copilot-instructions.md`).
- Test and review rules: `.github/.claude/rules/mors-tests.md` and `.github/.claude/rules/mors-code-review.md`.
- Per-PR rationale: PR descriptions.
- Per-commit rationale: commit messages.
- Module-level scientific validation: `docs/Validation/<file>.md` (created when the first `@pytest.mark.reference_pinned` test for that source lands).

Do not introduce a new in-repo "memory" or "decisions log" file. The four channels above are the contract.

---

## Quick Reference

```bash
# Setup
pip install -e ".[develop]"
pre-commit install -f

# Test
pytest -m "(unit or smoke) and not skip"
pytest --cov=mors --cov-report=html

# Lint
ruff check --fix src/ tests/
ruff format src/ tests/

# Validate
bash tools/validate_test_structure.sh
python tools/check_test_quality.py --check

# Serve docs locally
pip install -e '.[docs]'
zensical serve
```

**Remember**: Trust these instructions. Only search if information is incomplete or found to be in error.

---

> **⚠️ FILE SIZE LIMIT: This file must stay below 500 lines.** Enforced by pre-commit hook (`tools/check_file_sizes.sh`). File located at `.github/copilot-instructions.md`.
