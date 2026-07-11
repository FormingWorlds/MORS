# Coupling to PROTEUS

[PROTEUS](https://proteus-framework.org/PROTEUS) is a coupled planetary evolution framework that simulates the long-term evolution of rocky planets, including their interior, atmosphere, and the stellar environment they orbit in. A schematic of PROTEUS components and corresponding modules is shown below; click any module in the diagram to open its documentation. Please find a description of the PROTEUS architecture [here](https://proteus-framework.org/PROTEUS/Explanations/model.html). <br>
<br>

<object type="image/svg+xml" data="https://cdn.jsdelivr.net/gh/FormingWorlds/PROTEUS@main/docs/assets/proteus_modules_schematic.svg" class="mod-diagram mod-diagram--light" aria-label="PROTEUS module schematic (light mode)">PROTEUS module schematic (light mode)</object>
<object type="image/svg+xml" data="https://cdn.jsdelivr.net/gh/FormingWorlds/PROTEUS@main/docs/assets/proteus_modules_schematic_darkmode.svg" class="mod-diagram mod-diagram--dark" aria-label="PROTEUS module schematic (dark mode)">PROTEUS module schematic (dark mode)</object>

<p style="text-align: center;"><strong>Schematic of PROTEUS components and corresponding modules.</strong></p>

## MORS in PROTEUS

The host star is not static in PROTEUS simulations; its luminosity, radius, temperature, and high-energy emission all change significantly over geological timescales, and these changes directly affect the planet's atmospheric escape, photochemistry, and surface conditions. MORS is the stellar evolution module within PROTEUS responsible for tracking how the star changes over time. At each iteration of the PROTEUS simulation loop, MORS provides:

- The **stellar radius and effective temperature** at the current age, used to compute the planetary energy budget
- The **bolometric instellation** at the planet's orbital distance, which drives the atmospheric energy balance
- The **XUV flux** (X-ray + EUV) as a function of stellar age and rotation, which drives atmospheric escape
- A **historical stellar spectrum** at the current age, constructed by scaling a modern reference spectrum using the MORS activity tracks

MORS is selected by setting `star.module = 'mors'` in the PROTEUS configuration file.

This page explains how MORS behaves inside a coupled run: the track options, the rotation and spectrum inputs, and the quantities it updates each iteration. For the practical configuration recipe, with the exact `[star]` and `[star.mors]` TOML blocks, see [Coupling to PROTEUS (how-to)](../How-to/proteus_coupling.md).

## Track options

PROTEUS supports two sets of stellar evolution tracks through MORS, selected via `star.mors.tracks`:

| Setting | Tracks | Mass range | Time unit | XUV |
|---|---|---|---|---|
| `'spada'` | Spada et al. (2013) | 0.10 to 1.25 Msun | Myr | Yes |
| `'baraffe'` | Baraffe et al. (2015) | 0.01 to 1.40 Msun | yr | No |

!!! warning "Mass clipped outside valid range"
    If the configured stellar mass falls outside the valid range for the chosen tracks, PROTEUS clips it to the nearest limit and logs a warning. Note the difference from standalone MORS: called on its own, `mors.Star` raises for an out-of-range mass. The clipping happens in the PROTEUS star wrapper, before MORS is called.

## Rotation

Rotation drives the high-energy evolution on Spada tracks and is set with one of two options in the configuration:

- `star.mors.rot_pcntle`: rotation percentile in the 1 Myr distribution. When set, the reference age is fixed at 1 Myr, consistent with the assumptions in `mors.Percentile()`.
- `star.mors.rot_period`: rotation period in days at the current stellar age (`star.mors.age_now`).

Exactly one of the two carries a value; `rot_pcntle` defaults to the 50th (median) percentile, so a configuration that sets neither is accepted and uses the median rotation. Setting both is rejected for any track set. Baraffe tracks have no rotation model, so the value is validated but does not affect the evolution.

## Stellar spectrum

PROTEUS requires a modern reference spectrum to initialise the spectral synthesis. This can be a custom stellar spectrum scaled to 1 AU, or an automatically downloaded stellar spectrum. There are three automatic options, configured via `star.mors.spectrum_source`:

| Setting | Behaviour |
|---|---|
| `'solar'` | Use modern or historical solar reference spectrum |
| `'muscles'` | Use [MUSCLES](https://archive.stsci.edu/hlsp/muscles) observed spectrum |
| `'phoenix'` | Generate a [PHOENIX](https://phoenix.astro.physik.uni-goettingen.de/) synthetic spectrum from stellar parameters |

PROTEUS rescales the spectrum to the planet's orbital separation. More information on stellar spectra in PROTEUS can be found [here](https://proteus-framework.org/PROTEUS/Reference/data.html#stellar-spectra).

## Quantities updated during the simulation loop

At each PROTEUS iteration, `update_stellar_quantities` updates the following:

| Quantity | Spada | Baraffe |
|---|---|---|
| Stellar radius | `star.Value(age, 'Rstar')` | `BaraffeStellarRadius(age)` |
| Effective temperature | `star.Value(age, 'Teff')` | `BaraffeStellarTeff(age)` |
| Bolometric instellation | From `Lbol` track | `BaraffeSolarConstant(age, sep)` |
| XUV instellation | From `Lx + Leuv` tracks | Not available (set to 0) |

Ages are passed in years to Baraffe methods and in Myr to Spada methods.

## Spectral synthesis during the simulation

For Spada tracks, historical spectra are computed by scaling the modern reference spectrum band-by-band using `mors.synthesis.CalcScaledSpectrumFromProps`. For Baraffe tracks, spectral synthesis uses `BaraffeTrack.BaraffeSpectrumCalc`, which scales the modern spectrum by the ratio of historical to modern bolometric luminosity. No band-resolved scaling is available.

## See also

- [Coupling to PROTEUS (how-to)](../How-to/proteus_coupling.md): the practical TOML recipe for configuring MORS inside a PROTEUS run.
- [PROTEUS documentation](https://proteus-framework.org/PROTEUS): the coupled framework that MORS plugs into.
