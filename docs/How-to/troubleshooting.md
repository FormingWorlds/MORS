# Troubleshooting

This page collects the most common errors and how to fix them.  If you encounter errors that you cannot solve via the standard step-by-step guide or the advice below, [contact the developers](../Community/contact.md).

## Error index
 
| Error | Section |
|---|---|
| `FileNotFoundError` on `.track1` / `.track2` file | [Data and installation issues](#data-and-installation-issues) |
| Download fails or is incomplete | [Data and installation issues](#data-and-installation-issues) |
| `ValueError: Unrecognised folder name` | [Data and installation issues](#data-and-installation-issues) |
| `stellar mass cannot be less than lower limit of 0.1 Msun` | [Stellar mass and age errors](#stellar-mass-and-age-errors) |
| `stellar mass cannot be greater than upper limit of 1.25 Msun` | [Stellar mass and age errors](#stellar-mass-and-age-errors) |
| `input age X is not within limits of Y to Z` | [Stellar mass and age errors](#stellar-mass-and-age-errors) |
| `input stellar mass X is not within limits of Y to Z` | [Stellar mass and age errors](#stellar-mass-and-age-errors) |
| `must set either Omega or both OmegaEnv and OmegaCore as argument of Star` | [Rotation input errors](#rotation-input-errors) |
| `cannot set OmegaEnv and OmegaCore when Omega is set as argument of Star` | [Rotation input errors](#rotation-input-errors) |
| `cannot set both Omega and Prot as arguments of Star` | [Rotation input errors](#rotation-input-errors) |
| `cannot set both Age and OmegaCore as arguments of Star` | [Rotation input errors](#rotation-input-errors) |
| `cannot set both percentile and Omega` (or `OmegaEnv`, `OmegaCore`, `Prot`) | [Rotation input errors](#rotation-input-errors) |
| `if Age is set then must set either Omega or OmegaEnv as argument of Star` | [Rotation input errors](#rotation-input-errors) |
| `input rotation rate too low for given mass and age` | [Rotation fitting errors](#rotation-fitting-errors) |
| `input rotation rate too high for given mass and age` | [Rotation fitting errors](#rotation-fitting-errors) |
| `input rotation rate in valid range for mass and age but solver was unable to fit track` | [Rotation fitting errors](#rotation-fitting-errors) |
| `ending simulation due to bad data found` | [Numerical integration errors](#numerical-integration-errors) |
| `too many timesteps taken` | [Numerical integration errors](#numerical-integration-errors) |
| `invalid quantity` in `ActivityLifetime` | [Method and query errors](#method-and-query-errors) |
| `invalid Band` in `IntegrateEmission` | [Method and query errors](#method-and-query-errors) |
| `invalid aOrb` in `IntegrateEmission` | [Method and query errors](#method-and-query-errors) |
| `AgeMin not in range of evolutionary track` | [Method and query errors](#method-and-query-errors) |
| `Mstar and Omega have different lengths` | [Cluster-specific errors](#cluster-specific-errors) |
| Saved object has no callable quantity methods after loading | [Loading saved objects](#loading-saved-objects) |
 

If your issue is not listed here, please open an issue on [GitHub](https://github.com/FormingWorlds/MORS/issues) and include the full traceback and the inputs you used. You can also try to get more diagnostic information, as described [here](#getting-more-diagnostic-information).


---



## Data and installation issues

### `FileNotFoundError` on first run

**Symptom:** Python raises a `FileNotFoundError` when creating a `Star` or `Cluster` object, pointing to a `.track1` or `.track2` file inside the `stellar_evolution_tracks` directory.

**Cause:** The stellar evolution data has not been downloaded yet, or was downloaded to a different location than where MORS is looking.

**Fix:** Download the data:

```sh
mors download all
```

Then check where MORS expects the data to be:

```sh
mors env
```

If you have already downloaded the data to a custom location, point MORS to it with the `FWL_DATA` environment variable:

```sh
export FWL_DATA=/path/to/your/data
```

Or pass the path directly when creating an object:

```python
star = mors.Star(Mstar=1.0, Omega=1.0, starEvoDir="/path/to/tracks")
```

---

### Download fails or is incomplete

**Symptom:** `mors download` exits with an error, or the data directory exists but is empty or missing files.

**Cause:** MORS tries Zenodo first and then falls back to OSF, with a maximum of 2 attempts per source. A transient network issue or rate-limit can cause both to fail.

**Fix:** Wait a few minutes and retry:

```sh
mors download spada
mors download baraffe
```

You can also download each track set independently if one source succeeded and the other did not. If the Spada directory was partially created before the failure, remove it before retrying, otherwise MORS will assume it is complete and skip the download:

```sh
rm -rf $FWL_DATA/stellar_evolution_tracks/Spada
mors download spada
```

!!! note "Incomplete directory"
    After a successful Spada download, MORS automatically extracts the archive (`fs255_grid.tar.gz`) and removes it. If extraction failed mid-way, the directory may exist but be incomplete. Removing it and re-downloading is the safest fix.

---

### `ValueError: Unrecognised folder name`

**Symptom:**
```
ValueError: Unrecognised folder name: <name>
```

**Cause:** `DownloadEvolutionTracks` was called with an invalid folder name. Only `"Spada"` and `"Baraffe"` are accepted (case-sensitive). Passing an empty string downloads both.

**Fix:**
```python
from mors.data import DownloadEvolutionTracks
DownloadEvolutionTracks("Spada")   # or "Baraffe", or "" for both
```

---

## Stellar mass and age errors

### Mass outside of supported range
- `stellar mass cannot be less than lower limit of 0.1 Msun`
- `stellar mass cannot be greater than upper limit of 1.25 Msun`

**Cause:** MORS only supports stellar masses in the range **0.1 – 1.25 Msun**, set by `MstarMin = 0.1` and `MstarMax = 1.25` in `star.py`. Passing a value outside this range raises an exception immediately.

**Fix:** Ensure your stellar mass is within the supported range before creating a `Star`:

```python
# Valid
star = mors.Star(Mstar=1.0, Omega=1.0)

# Invalid — will raise an exception
star = mors.Star(Mstar=1.5, Omega=1.0)
```

---

### `input age X is not within limits of Y to Z`

**Cause:** The requested age falls outside the age range covered by the stellar evolution track for this mass. The track starts at 1 Myr and ends at the end of the main sequence (varies with mass).

**Fix:** Check the age range of the loaded track before querying it:

```python
print(star.AgeTrack[0], star.AgeTrack[-1])  # start and end ages in Myr
```

Only query ages within this range when calling `star.Value()` or any of the quantity accessor functions.

---

### `input stellar mass X is not within limits of Y to Z`

**Cause:** Raised during 2D interpolation in `stellarevo.py` when the requested mass falls outside the range of masses currently loaded in `ModelData`. This can happen if `ClearData=True` was used when calling `StarEvo.LoadTrack` and a different mass is subsequently requested.

---

## Rotation input errors

### `must set either Omega or both OmegaEnv and OmegaCore as argument of Star`

**Cause:** No rotation rate was provided. `Star` requires either `Omega` (sets both envelope and core to the same value), or both `OmegaEnv` and `OmegaCore` explicitly.

**Fix:**
```python
# Option 1: single rotation rate (envelope = core)
star = mors.Star(Mstar=1.0, Omega=1.0)

# Option 2: separate envelope and core rates
star = mors.Star(Mstar=1.0, OmegaEnv=2.0, OmegaCore=1.5)
```

---

### `cannot set OmegaEnv and OmegaCore when Omega is set as argument of Star`

**Cause:** `Omega` was set alongside `OmegaEnv` or `OmegaCore`. These are mutually exclusive: `Omega` is a shorthand that sets both envelope and core to the same value.

---

### `cannot set both Omega and Prot as arguments of Star`

**Cause:** Both `Omega` (rotation rate in units of Ωsun) and `Prot` (rotation period in days) were provided. Only one may be specified.

---

### `cannot set both Age and OmegaCore as arguments of Star`

**Cause:** When `Age` is provided, MORS fits the evolutionary track to pass through the given surface rotation at that age. In this mode, the core rotation at the initial time is determined by the fit and cannot be set independently.

---

### `cannot set both percentile and Omega` (or `OmegaEnv`, `OmegaCore`, `Prot`)

**Cause:** `percentile` specifies the rotation rate via the empirical 1 Myr rotation distribution and is mutually exclusive with all direct rotation rate inputs.

**Fix:** Use one or the other:

```python
# Specify rotation directly
star = mors.Star(Mstar=1.0, Omega=5.0)

# Or use a percentile of the rotation distribution
star = mors.Star(Mstar=1.0, percentile=50.0)

# String shortcuts are also accepted
star = mors.Star(Mstar=1.0, percentile='slow')   # 5th percentile
star = mors.Star(Mstar=1.0, percentile='medium') # 50th percentile
star = mors.Star(Mstar=1.0, percentile='fast')   # 95th percentile
```

---

### `if Age is set then must set either Omega or OmegaEnv as argument of Star`

**Cause:** `Age` was provided (to fit the track to a known rotation at a known age) but no surface rotation rate was given. When `Age` is set, either `Omega` or `OmegaEnv` must also be set; `OmegaCore` cannot be used in this mode.

---

## Rotation fitting errors

These errors are raised by `rotevo.FitRotation` when MORS tries to find the initial rotation rate that produces a given rotation at a given age.

### `input rotation rate too low for given mass and age`

**Cause:** The requested rotation rate at the given age is lower than what the slowest possible initial rotator (Ω₀ = 0.1 Ωsun) would produce. The star would need to have started rotating slower than any physically supported initial rate.

---

### `input rotation rate too high for given mass and age`

**Cause:** The requested rotation rate at the given age is higher than what the fastest possible initial rotator (Ω₀ = 50 Ωsun) would produce.

---

### `input rotation rate in valid range for mass and age but solver was unable to fit track`

**Cause:** The requested rotation is within the fittable range but the bisection solver failed to converge within `params['nStepMaxFit']` = 1000 steps to within the tolerance `params['toleranceFit']` = 1 × 10⁻⁵. This is rare in normal use.

**Fix:** If you hit this, try relaxing the tolerance or increasing the step limit via a custom parameter dictionary:

```python
import mors
import mors.parameters as params

my_params = params.NewParams(toleranceFit=1e-4, nStepMaxFit=5000)
star = mors.Star(Mstar=1.0, Age=100.0, Omega=10.0, params=my_params)
```

---

## Numerical integration errors

### `ending simulation due to bad data found`

**Cause:** The ODE solver produced a NaN, Inf, or non-positive rotation rate (OmegaEnv ≤ 0 or OmegaCore ≤ 0). This indicates the simulation has become numerically unstable. Possible causes include an extreme initial rotation rate or unusual parameter combinations.

**Fix:** Check your inputs. If using custom parameters, try reducing `dAgeMax` (the maximum allowed timestep) to improve stability:

```python
my_params = params.NewParams(dAgeMax=10.0)  # default is 50 Myr
```

---

### `too many timesteps taken`

**Cause:** The solver exceeded `params['nStepMax']` = 1,000,000 timesteps without reaching the end age. This should not occur with the default `RosenbrockFixed` solver under normal conditions.

---

## Method and query errors

### `invalid quantity` in `ActivityLifetime`

**Cause:** The `Quantity` argument is not in the list of supported quantities. The full list of valid values is:

`'Lx'`, `'Fx'`, `'Rx'`, `'FxHZ'`, `'Leuv1'`, `'Feuv1'`, `'Reuv1'`, `'Feuv1HZ'`, `'Leuv2'`, `'Feuv2'`, `'Reuv2'`, `'Feuv2HZ'`, `'Leuv'`, `'Feuv'`, `'Reuv'`, `'FeuvHZ'`, `'Lly'`, `'Fly'`, `'Rly'`, `'FlyHZ'`

Note that `Threshold='sat'` is a valid special value, which normalises the track to the saturation rotation rate and sets the threshold to 1.

---

### `invalid Band` in `IntegrateEmission`

**Cause:** The `Band` argument is not one of the supported wavelength bands. Valid values are:

`'XUV'`, `'Xray'`, `'EUV1'`, `'EUV2'`, `'EUV'`, `'Lyman'`, `'bol'`

---

### `invalid aOrb` in `IntegrateEmission`

**Cause:** A string was passed for `aOrb` that is not one of the recognised habitable zone boundaries. Valid string values are:

`'RecentVenus'`, `'RunawayGreenhouse'`, `'MoistGreenhouse'`, `'MaximumGreenhouse'`, `'EarlyMars'`, `'HZ'`

You can also pass a numerical value in AU directly.

---

### `AgeMin not in range of evolutionary track` / `AgeMax not in range of evolutionary track`

**Cause:** Raised by `IntegrateEmission` when either `AgeMin` or `AgeMax` falls outside the age range of the star's evolutionary track. Both must satisfy `Age[0] <= AgeMin <= Age[-1]` and `Age[0] <= AgeMax <= Age[-1]`.

---

## Cluster-specific errors

### `Mstar and Omega have different lengths`

**Cause:** When creating a `Cluster`, the `Mstar` and `Omega` (or `OmegaEnv` / `OmegaCore`) arrays must all have the same length. MORS checks each pair independently and raises a specific message for whichever mismatches.

**Fix:**
```python
import numpy as np
import mors

Mstar = np.array([0.5, 0.8, 1.0])
Omega = np.array([1.0, 2.0, 5.0])  # must be same length as Mstar

cluster = mors.Cluster(Mstar=Mstar, Omega=Omega)
```

---

## Loading saved objects

### Saved `Star` or `Cluster` has no callable quantity methods after loading

**Cause:** `pickle` does not restore the dynamically attached methods (e.g. `star.Lx(Age=...)`) that `Star` and `Cluster` set up at creation time. If you load a saved object with `pickle.load()` directly, these methods will be missing.

**Fix:** Always use `mors.miscellaneous.Load` instead of `pickle.load`:

```python
import mors.miscellaneous as misc

star = misc.Load("star.pickle")       # correct: re-attaches quantity functions
cluster = misc.Load("cluster.pickle") # correct
```

---

## Getting more diagnostic information

MORS uses Python's standard `logging` module under the logger name `fwl.*`. To enable debug output, configure the logger before running your script:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

Or use the convenience function provided in `mors.logs`:

```python
from mors.logs import setup_logger
log = setup_logger("DEBUG")
```

This will print detailed per-step information from the ODE solver and data loading routines, which can help identify where a problem originates.
