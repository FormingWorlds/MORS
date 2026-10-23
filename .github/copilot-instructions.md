# MORS short instructions

The full instructions are in `AGENTS.md` (repository rules and review points) and `tests/AGENTS.md` (test rules). This file repeats what a review or a chat needs when it cannot read them.

## Commands

```bash
pip install -e ".[develop]"
pytest -m "(unit or smoke) and not skip"
ruff check --fix <changed files> && ruff format <changed files>
bash tools/validate_test_structure.sh
python tools/check_test_quality.py --check
python tools/agents/check_agents_md.py
```

## Review checklist

- `Lbol`, `Rstar`, `Teff` stay positive; band and bolometric fluxes stay non-negative, and a synthesised spectrum keeps its flux floor (`>= 1e-20`).
- `F_bo` equals `F_xr + F_e1 + F_e2 + F_uv + F_pl`; the UV band is the remainder and must not go negative.
- `Omega` stays positive through the spin-down integration; percentiles stay in [0, 100] and the percentile to `Omega` mapping stays monotone.
- Track interpolation does not extrapolate past the grid edges without a clamp or an error.
- Units: luminosity in erg/s from `Star.Value` and in Lsun from `stellarevo.Value`, age in Myr, mass in Msun, wavelength in nm, spectra and band fluxes at 1 AU in erg s-1 cm-2, `R_star` in m for `ScaleToSurf` and `ScaleTo1AU` (with `AU_SI`); constants from `mors.constants`, never a retyped literal.
- PROTEUS builds `mors.Star(Mstar, Age, percentile, Prot)` and `mors.BaraffeTrack`, and reads `Star.Value` for `Rstar`, `Teff`, `Lbol`, `Lx`, `Leuv`, `Leuv1`, `Leuv2` (`src/proteus/star/wrapper.py`); with the band keys (`xr`, `e1`, `e2`, `uv`, `pl`, `bo`) and `spectrum.bands_limits` this is the coupling contract, and a change to it comes with the PROTEUS change.
- Tests: `src/mors/<file>.py` is tested in `tests/test_<file>.py`; each file has `pytestmark = [pytest.mark.<tier>, pytest.mark.timeout(<s>)]`; each test has a docstring, at least 2 assertions, an edge case and the error path; floats are compared with a tolerance; a test that asserts a physical invariant carries `physics_invariant`, a test against a published or analytical value also carries `reference_pinned`, and pinned values have sign, scale and wrong-formula guards.
- Commit messages, pull-request text, comments, test names and CI job names describe the change: no tool attribution, no internal plan labels, no em or en dashes; an inline comment block has at most 4 lines.

This checklist is a subset of the review points of `AGENTS.md` (its Review section and its physics and coupling contract) and `tests/AGENTS.md`; change them together.
