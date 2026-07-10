# Testing suite

[![tests](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/FormingWorlds/MORS/badges/tests-total.json)](https://proteus-framework.org/validation)
[![unit tests](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/FormingWorlds/MORS/badges/tests-unit.json)](https://proteus-framework.org/validation)
[![integration tests](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/FormingWorlds/MORS/badges/tests-integration.json)](https://proteus-framework.org/validation)
[![Tests](https://img.shields.io/github/actions/workflow/status/FormingWorlds/MORS/tests.yaml?branch=main&label=CI)](https://github.com/FormingWorlds/MORS/actions/workflows/tests.yaml)
[![coverage](https://codecov.io/gh/FormingWorlds/MORS/branch/main/graph/badge.svg)](https://app.codecov.io/gh/FormingWorlds/MORS)

The test-count badges show how many tests the suite carries, split into the
mocked unit tests that run on every pull request and the integration tests that
run the real evolutionary-track model nightly. They read small JSON files on the
repository's `badges` branch that the `Refresh test count badges` workflow
regenerates whenever the test suite or source changes on `main`, so the counts
stay current without hand editing. The same files back the module's row on the
central [PROTEUS validation page](https://proteus-framework.org/validation).

The suite is a regression net: a passing run confirms that recent changes have
not perturbed locked behaviour, not that the behaviour is itself physically
correct. Physical correctness is judged separately, against analytic limits,
benchmark codes, and published references; each physics source records its
anchor on a validation page (`docs/Validation/`).

## Test tiers and coverage

Every test declares a tier. The `unit` and `smoke` tiers run on every pull
request under a ten-minute cap; the `integration` and `slow` tiers run the real
Baraffe and Spada tracks nightly. Line coverage is measured on the full suite
nightly and uploaded to [Codecov](https://app.codecov.io/gh/FormingWorlds/MORS),
where the coverage badge above is served. The coverage gates ratchet upward
toward the 90% ecosystem target and are never lowered.

## Badge system

The badge JSON files sit at the root of the `badges` branch in the shields.io
endpoint schema. Publishing to a dedicated branch keeps the generated files off
`main`, where direct pushes need review. The `Refresh test count badges`
workflow regenerates the counts whenever the test suite or source changes on
`main` and publishes them there; shields.io fetches them live.

For how to run the suite, see [Testing](../How-to/run_tests.md).
