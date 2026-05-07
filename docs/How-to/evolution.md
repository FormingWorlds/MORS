# Calculate a star's evolution

Compute a star's rotation and activity evolution tracks, then plot a quantity, query values at specific ages, and save the result for reuse.

## Prerequisites

Make sure the package and stellar evolution data are installed:

```bash
pip install fwl-mors
mors download all
```

!!! info "Units"
    Throughout MORS, `Age` is in **Myr**, `Prot` is in **days**, and `Omega` is in units of the **current solar rotation rate** ($\Omega_\odot = 2.67 \times 10^{-6}$ rad s$^{-1}$).

---

## Step 1: Create a `Star`

Pick one of the following ways to specify the initial rotation:

**A) Set initial rotation rate $\Omega$ (at ~1 Myr)**

```python
import mors
star = mors.Star(Mstar=1.0, Omega=10.0)
```

**B) Set initial rotation period in days**

```python
import mors
star = mors.Star(Mstar=1.0, Prot=2.7)
```

**C) Set rotation percentile in the 1 Myr distribution**

```python
import mors
star = mors.Star(Mstar=1.0, percentile=50.0)  # median rotator
# string shortcuts are also accepted:
star = mors.Star(Mstar=1.0, percentile='slow')    # 5th percentile
star = mors.Star(Mstar=1.0, percentile='medium')  # 50th percentile
star = mors.Star(Mstar=1.0, percentile='fast')    # 95th percentile
```

**D) Fit a track through a known rotation at a known age**

```python
import mors
star = mors.Star(Mstar=1.0, Age=100.0, Omega=50.0)
```

!!! warning
    Option D will raise an exception if the requested rotation rate is outside the range achievable for that mass and age (below the slowest or above the fastest possible track). See [Troubleshooting](troubleshooting.md) for the specific error messages.

---

## Step 2: Inspect available quantities and units

```python
star.PrintAvailableTracks()  # requires logging to be configured
print(star.Units['Lx'])      # prints the units string for Lx
```

To configure logging first:

```python
from mors.logs import setup_logger
setup_logger("INFO")
star.PrintAvailableTracks()
```

---

## Step 3: Plot an evolutionary track

Tracks are stored in `star.Tracks` and also exposed as `star.<Quantity>Track` arrays:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(star.AgeTrack, star.LxTrack)
ax.set_xlabel(f"Age [{star.Units['Age']}]")
ax.set_ylabel(f"Lx [{star.Units['Lx']}]")
ax.set_xscale('log')
ax.set_yscale('log')
plt.show()
```

---

## Step 4: Query a value at a specific age

```python
# Using the generic Value method
lx = star.Value(Age=150.0, Quantity='Lx')

# Using the quantity accessor (preferred)
lx = star.Lx(Age=150.0)
```

Both return a linearly interpolated scalar at the requested age. The age must be within the range of the evolutionary track.

---

## Step 5: Save and reload

```python
import mors

star.Save(filename="star.pickle")

# Always use mors.Load rather than pickle.load directly,
# as it re-attaches the quantity accessor functions
star2 = mors.Load("star.pickle")
print(star2.Lx(Age=4500.0))
```

---

## Common pitfalls

- `Age` is always in **Myr**, not years or Gyr.
- `Omega` is in units of $\Omega_\odot$, not rad s$^{-1}$.
- Do not use `pickle.load` directly to reload a saved star — use `mors.Load` instead.
- `PrintAvailableTracks` uses the logging system and produces no output unless logging is configured.