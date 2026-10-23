# MORS agent instructions

MORS evolves the rotation, luminosity, radius and high-energy (X-ray, EUV, UV) emission of a star from published evolutionary tracks (Baraffe et al. 2015, Spada et al. 2013), and synthesises the stellar spectrum. PROTEUS calls it in the stellar-evolution step for the spectrum and the XUV flux history that drive atmospheric heating and escape; it also runs standalone. Before a first edit:

- Tests for `src/mors/<file>.py` go in `tests/test_<file>.py`; the test rules are in `tests/AGENTS.md`.
- Physics sources: `baraffe.py`, `cluster.py`, `physicalmodel.py`, `rotevo.py`, `spectrum.py`, `star.py`, `stellarevo.py`, `synthesis.py`. Utility sources: `__init__.py`, `constants.py`, `data.py`, `cli.py`, `logs.py`, `parameters.py`, `miscellaneous.py`. The [API reference](docs/Reference/api/index.md) describes each module.
- These commands decide whether a change is ready (CI runs the tests, the structure check, the test-quality lint and the agent-file check):

```bash
pytest -m "(unit or smoke) and not skip"
ruff check --fix src/ tests/ && ruff format src/ tests/
bash tools/validate_test_structure.sh
python tools/check_test_quality.py --check
python tools/agents/check_agents_md.py
```

Coverage as the nightly measures it, and one test with its locals on failure:

```bash
coverage run -m pytest -m "(unit or smoke or integration or slow) and not skip" && coverage report && coverage html
pytest -x -v --showlocals tests/test_<file>.py::test_function
```

<!-- fwl-core:begin sha256=1adfa510a4f117ec -->
## PROTEUS ecosystem rules

PROTEUS couples separate module repositories into one model of the evolution of rocky planets and their atmospheres. Its config selects one module per process; the config values are the lowercase names:

- `interior_energetics.module`: `aragog`, `spider` (or the built-in `boundary`); `interior_struct.module`: `zalmoxis`, `spider`
- `atmos_clim.module`: `agni`, `janus`, both with SOCRATES spectral radiative transfer
- `outgas.module`: `calliope`, `atmodeller`; `atmos_chem.module`: `vulcan`
- `star.module`: `mors`; `escape.module`: `zephyrus`, `boreas`; `orbit.module` (tides): `obliqua`, `lovepy`
- fwl-io downloads the reference data the modules use

A module change to anything PROTEUS calls or reads (a function signature, a config key, an output column, a unit) can break the coupled model while the module's own tests pass. Search `src/proteus/` in PROTEUS for the name before you change it, and name the affected PROTEUS call sites in the pull request.

### Physics and numerics

- Units differ between and within modules: MORS and VULCAN use cgs; CALLIOPE and atmodeller work with pressures in bar; AGNI takes surface pressure in bar at setup and holds Pa inside; PROTEUS states the unit of every `hf_row` key in `GetHelpfileKeys` (`src/proteus/utils/coupler.py`: atmospheric pressures in bar, interior pressures in Pa, model time in years, orbital periods in s), and its config reference pages state each key's unit (for example stellar mass in M_sun, initial partial surface pressures in bar, stellar age in Gyr). State the unit of every physical quantity in its docstring and convert explicitly at the boundary: a unit mismatch between two modules passes the tests of both and shows only in the coupled run.
- A physics test must fail for the most plausible wrong formula: check a conservation law, a bound, a monotonicity, or a published or analytical value, and assert that the wrong result falls outside the tolerance.
- Take each physical constant from one source per repository (in Python `scipy.constants` or the module's constants file). Two retyped values of one constant differ at round-off and hide real differences between code paths.
- Do not loosen a solver tolerance, a conservation check or a clamp to make a run or a test pass. Find the cause; a loosened check also hides the next defect.

### Validation

A new or changed physics routine gets the validation cases named in its confirmed plan: an analytical law, a published figure or table, or a cross-code check. Each case is a `reference_pinned` test that runs the real code on real data, with no mocks, asserts the tolerance, and writes its light and dark plot through the `validation_plot` fixture of proteus-mpl. `pytest -m reference_pinned --validation-plots` makes all plots again. Line plots are SVG, maps are AVIF; each file is at most 60 kB, under `docs/assets/validation/`. Each case has a subsection on its page in the Validation tab, with the reference, the tolerance, the test id and the command. Data read from a published figure comes from 2 independent figlab reads that agree within the stated error, as a CSV with its provenance under `tests/validation/data/`.

### Code

- Keep an inline comment block to 2 lines or fewer, and never more than 4, because a long block drifts from the code it describes. An explanation that needs more goes in the docstring, the commit message or the pull-request description.

### Branches and pull requests

- Work on a feature branch `<initials>/<short-description>`; `main` changes only through a reviewed pull request.
- Fill every section of the repository's pull-request template, where it has one.
- Before you push, run the checks listed at the top of this `AGENTS.md` and in `tests/AGENTS.md`.

### Where knowledge goes

Rules for every contributor go in the `AGENTS.md` files, the reason for a change in its commit message and pull-request description, and the scientific validation of a module in its `docs/Validation/` pages, where the repository has them. Do not add memory, notes or decision-log files to the repository: nobody maintains them, and they go stale.
<!-- fwl-core:end -->

<!-- fwl-voice:begin sha256=b4fe24baeef8b734 -->
### Commit messages and public text

Commit messages, pull-request text, code comments, docstrings, test names, test skip reasons, parametrize ids, log strings that ship with the code, and CI job and step names describe the change and the current state of the code. They name no tool used to write the change, carry no tool-attribution trailer, use no internal plan, phase or work-group labels, and use no em or en dashes (a page range in a citation is the exception).
<!-- fwl-voice:end -->

## Environment

Python 3.11, 3.12 or 3.13 and git. `pip install -e ".[develop]"` and `pre-commit install -f`; there is nothing to compile. Next to PROTEUS, install MORS editable from the PROTEUS tree (`pip install -e MORS/.`) so a change takes effect without a reinstall. `FWL_DATA` must point at a data directory: MORS fetches the Baraffe and Spada tracks there through fwl-io on first use, and `mors download all` fetches them at once. The pre-commit hook runs `ruff check --fix` on the files a commit touches; older modules carry lint debt that is cleaned when a file is edited, not in one sweep. Serve the docs with `zensical serve` after `pip install -e '.[docs]'`.

Style: lines shorter than 96 characters; the existing code mixes casing (`Value`, `Percentile`), so match the file rather than rename; constants in `UPPER_CASE`; standard type hints; a docstring states the physical scenario.

## CI

- `tests.yaml` (every pull request): `pytest -m "(unit or smoke) and not skip"` with coverage against the fast gate, `validate_test_structure.sh`, `check_test_quality.py --check` (blocking), the agent-file check, and a guard that rejects a pull request that lowers `[tool.coverage.report].fail_under` or `[tool.mors.coverage_fast].fail_under` below `min(base, 90)` or raises one above 90.
- `code-style.yaml` runs pre-commit on the changed files; `docs.yaml` builds the docs.
- `nightly.yml`: all tiers, coverage to Codecov, the full gate enforced.
- `publish-test-badges.yml` refreshes the test-count badges on the `badges` branch; `publish.yaml` releases to PyPI on a tag.

## Physics and coupling contract

- Units mix cgs and SI, and this is where errors enter: luminosity in erg/s from `Star.Value` (about 4.1e33 for 1 Msun at 4.57 Gyr) and in Lsun from `stellarevo.Value`, radius in Rsun or cm depending on the call, `Teff` in K, `Omega` in units of the solar rotation rate, age in Myr, stellar mass in Msun, wavelength in nm, flux at 1 AU in W/m^2, surface flux scaled by `(R_star / AU)**2`. Confirm the unit at every conversion site; a value off by 1e7 (erg against W) or 1e2 (cm against m) that passes a loose test is the signature.
- Constants (`AU`, `LbolSun`, `Pi`, `Rsun`, `Msun`) come from `mors.constants`; a bare literal such as `1.496e11` in a function body is a defect.
- The band keys (`xr`, `e1`, `e2`, `uv`, `pl`, `bo`) and their limits (`spectrum.bands_limits`) are the coupling contract. A change to a key or a limit is mirrored in the PROTEUS caller and in the pinned band-flux tests.
- PROTEUS (`src/proteus/star/wrapper.py`) builds `mors.Star(Mstar=..., Age=..., percentile=..., Prot=...)` and `mors.BaraffeTrack(Mstar)`, and reads `Star.Value(age, key)` for `Rstar`, `Teff`, `Lbol`, `Lx`, `Leuv1` and `Leuv2`; a change of a signature, a return unit or a key comes with the PROTEUS change.
- `ScaleTo1AU(ScaleToSurf(f, R)) == f` within tolerance; a broken round trip rescales every flux PROTEUS receives.
- PROTEUS integrates the XUV flux over the life of the star, so `Lx` and `Leuv1`, `Leuv2` must stay continuous in age at the grid boundaries of the track interpolation.
- `baraffe.py` and `stellarevo.py` read the tracks from `FWL_DATA`; code checks that the files exist (or fetches them) before it reads them. A pinned value names the track set it was pinned against. A change of the default track set (Baraffe or Spada) or of the default time integration (`TimeIntegrationMethod`, now `RosenbrockFixed`) changes the pinned reference values and the `docs/Validation/` pages: `git grep` the old default and update each in the same pull request.
- The parameter dictionary from `parameters.py` and the configured attributes of a `Star` are not changed after initialisation; use local variables.

## Adding a physics source

1. Create `src/mors/<file>.py` and `tests/test_<file>.py` with the module-level `pytestmark`.
2. Add at least one `physics_invariant` test and one `reference_pinned` test.
3. Add `docs/Validation/<file>.md` with a subsection per case (reference, tolerance, test id, command), and list the case in `docs/Validation/index.md` and in the Validation nav of `mkdocs.yml`.

## Review

Check each change against these points and the physics and coupling contract above. `.github/copilot-instructions.md` repeats this checklist for tools that read only that file; change it together with this section.

- `Lbol`, `Rstar`, `Teff` stay positive; band and bolometric fluxes stay non-negative, and a synthesised spectrum keeps its flux floor (`>= 1e-20`).
- `F_bo` equals `F_xr + F_e1 + F_e2 + F_uv + F_pl`; the UV band is the remainder and must not go negative.
- `Omega` stays positive through the spin-down integration; percentiles stay in [0, 100] and the percentile to `Omega` mapping stays monotone.
- Track interpolation does not extrapolate past the grid edges without a clamp or an error.
- Units at each cgs and SI boundary; constants from `mors.constants`; the band keys, `Star`, `BaraffeTrack` and the `Value` keys as PROTEUS reads them.
- Tests follow `tests/AGENTS.md`.
