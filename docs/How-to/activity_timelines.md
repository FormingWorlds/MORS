# Find stellar activity lifetimes

Compute how long a star (or cluster of stars) stays above an activity threshold, such as an X-ray luminosity limit, or how long it remains in the saturated regime.

## Prerequisites

Make sure the package and stellar evolution data are installed: 

```bash
pip install fwl-mors
mors download all
```

!!! info "Units"
    Thresholds must match the units of the chosen quantity (e.g., `Lx` in **erg s⁻¹**). Ages returned are in **Myr**.

---

## Option 1: Standalone helper on an explicit track

`mors.ActivityLifetime` takes an age array and a track array directly and returns the age when the track finally drops below the threshold:

```python
import mors

star = mors.Star(Mstar=1.0, Omega=1.0)

age_active = mors.ActivityLifetime(
    Age=star.AgeTrack,
    Track=star.LxTrack,
    Threshold=1.0e28
)
print(age_active)  # Myr
```

Behaviour:

- If the track crosses the threshold multiple times, the **final** crossing age is returned.
- If the track never drops below the threshold, the **final age** in the track is returned.
- If the track is always below the threshold, `0.0` is returned.

To limit the search to ages below a maximum:

```python
age_active = mors.ActivityLifetime(
    Age=star.AgeTrack,
    Track=star.LxTrack,
    Threshold=1.0e28,
    AgeMax=2000.0
)
```

---

## Option 2: `Star.ActivityLifetime` method (recommended)

This selects the track internally — you only provide the quantity name and threshold:

```python
age_active = star.ActivityLifetime(Quantity='Lx', Threshold=1.0e28)
print(age_active)  # Myr
```

To limit the search to ages below a maximum:

```python
age_active = star.ActivityLifetime(Quantity='Lx', Threshold=1.0e28, AgeMax=1000.0)
```

The `Quantity` argument must be one of the following supported activity quantities:

| Band | Valid quantities |
|---|---|
| X-ray | `Lx`, `Fx`, `Rx`, `FxHZ` |
| EUV1 (10–36 nm) | `Leuv1`, `Feuv1`, `Reuv1`, `Feuv1HZ` |
| EUV2 (36–92 nm) | `Leuv2`, `Feuv2`, `Reuv2`, `Feuv2HZ` |
| EUV (10–92 nm) | `Leuv`, `Feuv`, `Reuv`, `FeuvHZ` |
| Ly-$\alpha$ | `Lly`, `Fly`, `Rly`, `FlyHZ` |

---

## Cluster activity lifetimes

For a `mors.Cluster`, the same method returns one value per star as a NumPy array:

```python
import numpy as np
import mors

Mstar = np.array([0.5, 0.8, 1.0, 1.2])
Omega = np.array([1.0, 1.0, 1.0, 1.0])
cluster = mors.Cluster(Mstar=Mstar, Omega=Omega)

ages_active = cluster.ActivityLifetime(Quantity='Lx', Threshold=1.0e28)
print(ages_active)  # array of Myr, one per star
```

---

## Saturation lifetime

To find how long a star remains in the saturated X-ray regime, pass `Threshold='sat'`. This normalises the track to $\Omega_\mathrm{env}/\Omega_\mathrm{sat}$ and finds when it drops below 1, so the result is independent of which valid quantity you choose:

```python
age_saturated = star.ActivityLifetime(Quantity='Lx', Threshold='sat')
print(age_saturated)  # Myr
```

---

## Common pitfalls

- The threshold must be in the same units as the chosen quantity (`Lx` in erg s⁻¹, `Fx` in erg s⁻¹ cm⁻², `Rx` dimensionless, etc.).
- The function always returns the **final** crossing age when there are multiple crossings.
- `Threshold='sat'` is available on `Star.ActivityLifetime` and `Cluster.ActivityLifetime`, but not on the standalone `mors.ActivityLifetime`.