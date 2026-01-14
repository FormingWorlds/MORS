## Evolutionary calculations (How-to)

### Goal
Compute a star’s rotation and activity evolution tracks, then (a) plot a quantity, (b) query values at specific ages, and (c) save the result for reuse.

### Prerequisites
Make sure the package and stellar evolution data are installed:

```bash
pip install fwl-mors
mors download all
```

> **Units:** `Age` is in **Myr**, `Prot` is in **days**, and `Omega` is in units of the **current solar rotation rate (Ω☉)**.

---

### Step 1: Create a `Star`

Pick **one** of these common ways:

**A) Set initial rotation using Ω (at ~1 Myr)**

```python
import mors
star = mors.Star(Mstar=1.0, Omega=10.0)
```

**B) Set initial rotation using rotation period (days)**

```python
import mors
star = mors.Star(Mstar=1.0, Prot=2.7)
```

**C) Fit a track through a point (Age, Ω)**

```python
import mors
star = mors.Star(Mstar=1.0, Age=100.0, Omega=50.0)
```

Use (C) only at ages where rotation tracks have not strongly converged for that mass; otherwise the fit may be ill-posed or fail if the requested rotation rate is unrealistic.

---

### Step 2: Inspect available tracks and units

```python
star.PrintAvailableTracks()
print(star.Units['Lx'])
```

---

### Step 3: Plot an evolutionary track

Tracks are stored in `star.Tracks` and also exposed as `<Quantity>Track` arrays.

```python
import matplotlib.pyplot as plt

plt.plot(star.Tracks['Age'], star.Tracks['Lx'])
# or: plt.plot(star.AgeTrack, star.LxTrack)
plt.xlabel(f"Age [{star.Units['Age']}]")
plt.ylabel(f"Lx [{star.Units['Lx']}]")
plt.show()
```

---

### Step 4: Find a value at a given age

```python
print(star.Value(150.0, 'Lx'))
# or:
print(star.Value(Age=150.0, Quantity='Lx'))
# or (preferred when available):
print(star.Lx(150.0))
```

---

### Step 5: Save and reload

```python
star.Save(filename="star.pickle")
star2 = mors.Load("star.pickle")
```

---

### Common pitfalls
- `Age` is in **Myr** (not years).
- `Omega` is in **Ω☉** (not rad/s).
- Fitting with `Age=...` + `Omega=...` may fail at late ages or for extreme rotation rates.
