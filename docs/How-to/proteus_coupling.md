# Coupling to PROTEUS

This page is the practical recipe for using MORS inside a [PROTEUS](https://proteus-framework.org/PROTEUS) coupled run: which configuration blocks matter, what each setting does, and which combinations are valid. For how MORS behaves once it is coupled, the track model, the per-iteration quantities, and the spectral synthesis, see [Coupling to PROTEUS (explanation)](../Explanations/proteus.md).

The MORS wrapper lives in the PROTEUS repository (`src/proteus/star/wrapper.py`), not in MORS itself. This page documents the MORS side of the contract: the `[star]` and `[star.mors]` configuration that the wrapper reads.

## Minimal `[star]` block

MORS is enabled by selecting it as the star module and giving the host-star mass:

```toml
[star]
module = "mors"        # use MORS for stellar evolution
mass   = 1.0           # stellar mass [M_sun]

[star.mors]
tracks          = "spada"     # "spada" or "baraffe"
age_now         = 4.567       # current stellar age [Gyr]
rot_pcntle      = 50.0        # rotation percentile (0-100)
spectrum_source = "solar"     # "solar", "muscles", or "phoenix"
star_name       = "sun"       # required for "solar" and "muscles"
```

## Choosing the tracks

`star.mors.tracks` selects the stellar-evolution grid:

| Setting | Tracks | Mass range | Rotation model | XUV |
|---|---|---|---|---|
| `"spada"` | Spada et al. (2013) | 0.10 to 1.25 M_sun | Yes | Yes |
| `"baraffe"` | Baraffe et al. (2015) | 0.01 to 1.40 M_sun | No | No |

Use `"spada"` for a rotation-driven XUV history (the usual choice for escape studies). Use `"baraffe"` when you only need bolometric evolution over a wider mass range and do not need XUV or rotation.

!!! warning "Mass is clipped to the track range"
    If `star.mass` falls outside the range for the chosen tracks, PROTEUS clips it to the nearest limit and logs a warning rather than failing. Keep the mass inside the track range to avoid a silent change in the star you simulate.

## Setting the initial rotation

Rotation drives the XUV history on Spada tracks. Set it with exactly one of two options:

- `star.mors.rot_pcntle`: a rotation percentile in the 1 Myr distribution (`0` to `100`). The reference age is fixed at 1 Myr, matching `mors.Percentile()`. A percentile of 5 is a slow rotator, 50 the median, 95 a fast rotator.
- `star.mors.rot_period`: a rotation period in days at the current stellar age `star.mors.age_now`.

Exactly one of `rot_pcntle` and `rot_period` must carry a value. `rot_pcntle` defaults to 50 (the median rotator), so leaving both keys out is valid and selects the median rotation without raising an error. Setting both to a value raises a configuration error, and so does nulling `rot_pcntle` (setting `rot_pcntle = "none"`) while leaving `rot_period` unset. This check runs for every MORS configuration regardless of the chosen tracks. Baraffe tracks have no rotation model, so the value does not affect the evolution, but the setting is still validated.

## Choosing the reference spectrum

`star.mors.spectrum_source` selects the modern reference spectrum that the historical spectra are scaled from:

| Setting | Behaviour |
|---|---|
| `"solar"` | Modern or historical solar reference spectrum (set `star.mors.star_name`) |
| `"muscles"` | [MUSCLES](https://archive.stsci.edu/hlsp/muscles) observed spectrum (set `star.mors.star_name`) |
| `"phoenix"` | [PHOENIX](https://phoenix.astro.physik.uni-goettingen.de/) synthetic spectrum from stellar parameters |

For `"solar"` and `"muscles"`, set `star.mors.star_name` to the target star (for the solar reference, `star_name = "sun"`). `"phoenix"` instead builds the spectrum from stellar parameters and does not need `star_name`. PROTEUS rescales the chosen spectrum to the planet's orbital separation. Fuller detail on stellar spectra is in the [PROTEUS data reference](https://proteus-framework.org/PROTEUS/Reference/data.html#stellar-spectra).

## Common pitfalls

- **Both `rot_pcntle` and `rot_period` set.** Setting both to a value is rejected for any tracks (including Baraffe). Because `rot_pcntle` defaults to 50, leaving both keys out is accepted and gives the median rotator; the "neither set" error appears only if you null `rot_pcntle` without setting `rot_period`.
- **`age_now` missing or non-positive.** The current stellar age must be greater than zero; it is given in Gyr.
- **Expecting XUV from Baraffe tracks.** Baraffe tracks provide no XUV; the XUV instellation is set to zero. Use Spada tracks for escape-driving XUV.
- **Mass outside the track range.** The mass is clipped with a warning, so the simulated star may differ from the configured one. Check the log if the star mass is near a track limit.

## Next step

See [Coupling to PROTEUS (explanation)](../Explanations/proteus.md) for the track model, the quantities MORS updates each iteration, and how the historical spectrum is synthesised.
