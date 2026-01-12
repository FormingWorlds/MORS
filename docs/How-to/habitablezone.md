## 8. Find habitable zone boundaries (How-to)

### Goal
Compute habitable zone (HZ) boundary orbital distances (AU) as a function of stellar **mass** and **age** using `mors.aOrbHZ`.

### Prerequisites
Install MORS and download stellar evolution data:

```bash
pip install fwl-mors
mors download all
```

> **Units:** `Mstar` in **M☉**, `Age` in **Myr**, returned distances in **AU**.

**Citation note:** If you use these HZ boundaries in research, cite **Kopparapu et al. (2013)** (HZ prescription) and **Spada et al. (2013)** (stellar parameters used).

---

### Step 1: Compute HZ boundaries for a single star mass

By default, `aOrbHZ` uses stellar parameters at **5000 Myr** if you don’t specify `Age`.

```python
import mors

hz = mors.aOrbHZ(Mstar=1.0)
```

The returned dictionary contains these keys:
- `RecentVenus`
- `RunawayGreenhouse`
- `MoistGreenhouse`
- `MaximumGreenhouse`
- `EarlyMars`
- `HZ`

Print them:

```python
for k in ["RecentVenus", "RunawayGreenhouse", "MoistGreenhouse",
          "MaximumGreenhouse", "EarlyMars", "HZ"]:
    print(k, hz[k])
```

`HZ` is defined (Johnstone et al. 2020) as the average of the `RunawayGreenhouse` and `MoistGreenhouse` orbital distances.

---

### Step 2: Specify a stellar age

```python
import mors
hz_1gyr = mors.aOrbHZ(Mstar=1.0, Age=1000.0)  # Myr
print(hz_1gyr["HZ"])
```

---

### Step 3: Compute HZ boundaries for multiple masses

If you pass an array of masses, you get arrays back in the dictionary:

```python
import numpy as np
import mors

masses = np.array([0.3, 0.5, 0.8, 1.0])
hz = mors.aOrbHZ(Mstar=masses, Age=5000.0)

print(hz["HZ"])              # array of AU
print(hz["RunawayGreenhouse"])
```

---

### Common pitfalls
- `Age` is in **Myr** (not years).
- When passing arrays for `Mstar`, each returned dict entry becomes an array of the same length.
