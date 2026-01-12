## Activity timelines (How-to)

### Goal
Compute how long a star (or a cluster of stars) stays above an activity threshold (e.g., X-ray luminosity) or how long it remains in the saturated regime.

### Prerequisites
Install MORS and download stellar evolution data:

```bash
pip install fwl-mors
mors download all
```

> **Units:** thresholds must match the quantity you use (e.g., `Lx` in **erg s⁻¹**). Ages returned are in **Myr**.

---

### Compute activity threshold

#### Option 1: Use the standalone helper on an explicit track (basic)

`mors.ActivityLifetime` takes an age array and a track array and returns the age when the track finally drops below the threshold.

```python
import mors

AgeThreshold = mors.ActivityLifetime(
    Age=star.AgeTrack,
    Track=star.LxTrack,
    Threshold=1.0e28
)
print(AgeThreshold)
```

**Behavior:**
- If the track crosses the threshold multiple times → returns the **final** crossing time.
- If it never goes below the threshold → returns the **final age** in the track.
- If it is never above the threshold → returns `0.0`.

Optional: limit the search to ages below `AgeMax`.

---

#### Option 2: Prefer the `Star.ActivityLifetime` method (recommended)

This version selects the track internally; you only provide the quantity name and threshold.

```python
AgeThreshold = star.ActivityLifetime(Quantity="Lx", Threshold=1.0e28)
print(AgeThreshold)
```

You can also set a maximum age to consider:

```python
AgeThreshold = star.ActivityLifetime(Quantity="Lx", Threshold=1.0e28, AgeMax=1000.0)
```

**Note**: The `Quantity` string must match one of the supported activity tracks:

- `Lx`, `Fx`, `Rx`, `FxHZ`
- `Leuv1`, `Feuv1`, `Reuv1`, `Feuv1HZ`
- `Leuv2`, `Feuv2`, `Reuv2`, `Feuv2HZ`
- `Leuv`, `Feuv`, `Reuv`, `FeuvHZ`
- `Lly`, `Fly`, `Rly`, `FlyHZ`

---

### Compute cluster lifetimes (same interface, returns arrays)

For a `mors.Cluster`, the call is the same but returns one value per star:

```python
AgeThreshold = cluster.ActivityLifetime(Quantity="Lx", Threshold=1.0e28)
print(AgeThreshold)  # numpy array
```
---

### Compute saturation lifetime 

To get the time the star remains in the saturated regime, pass `Threshold="sat"`:

```python
AgeSaturated = star.ActivityLifetime(Quantity="Lx", Threshold="sat")
print(AgeSaturated)
```

Note: the choice of `Quantity` should not change the saturation lifetime (XUV quantities saturate together), but it must be a valid option.

---

### Common pitfalls
- Make sure your `Threshold` uses the same units as the chosen `Quantity` (e.g., `Lx` is erg s⁻¹).
- The function returns the **final** threshold crossing time if there are multiple crossings.
