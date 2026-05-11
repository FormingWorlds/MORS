# Calculate cluster evolution

Compute rotation and activity evolution tracks for a cluster of stars, then inspect per-star tracks, evaluate cluster distributions at a given age, and save the result to avoid recomputation.

## Prerequisites

Install MORS and download stellar evolution data:

```bash
pip install fwl-mors
mors download all
```

!!! info "Units"
    `Age` is in **Myr**, `Prot` is in **days**, and `Omega` is in units of the **current solar rotation rate** ($\Omega_\odot = 2.67 \times 10^{-6}$ rad s$^{-1}$).
---

## Step 1: Create a cluster from arrays

Create arrays of masses and rotation rates of the same length. If `Age` is omitted, `Omega` is interpreted as the initial (~1 Myr) rotation rate.

```python
import numpy as np
import mors

Mstar = np.array([1.0, 0.5, 0.75])
Omega = np.array([10.0, 10.0, 10.0])

cluster = mors.Cluster(Mstar=Mstar, Omega=Omega)
```

To print progress while tracks are computed, enable `verbose`:

```python
cluster = mors.Cluster(Mstar=Mstar, Omega=Omega, verbose=True)
```

---

## Step 2: Fit tracks through a specified age (optional)

If you provide `Age`, MORS fits each track so that the star passes through the given rotation rate at that age.

**One age applied to all stars:**

```python
cluster = mors.Cluster(Mstar=Mstar, Omega=Omega, Age=100.0)
```

**A different age for each star:**

```python
Age = np.array([80.0, 120.0, 100.0])  # same length as Mstar and Omega
cluster = mors.Cluster(Mstar=Mstar, Omega=Omega, Age=Age)
```

!!! warning
    Fitting with `Age` and `Omega` can fail if the requested rotation rate is outside the achievable range for a given mass and age. See [Troubleshooting](troubleshooting.md) for the specific error messages.

---

## Step 3: Access per-star tracks

Each star is a `mors.Star` instance stored in `cluster.stars`. Stars are also accessible as attributes `cluster.star0`, `cluster.star1`, etc.:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
for i in range(cluster.nStars):
    ax.plot(cluster.stars[i].AgeTrack, cluster.stars[i].LxTrack)

ax.set_xlabel("Age [Myr]")
ax.set_ylabel("Lx [erg/s]")
ax.set_xscale('log')
ax.set_yscale('log')
plt.show()
```

---

## Step 4: Get cluster values at a fixed age

Use `cluster.Values(Age=..., Quantity=...)` to retrieve an array across all stars:

```python
Lx = cluster.Values(Age=100.0, Quantity='Lx')
```

Or use the quantity accessor directly:

```python
Lx = cluster.Lx(100.0)
```

For example, to plot $L_X$ versus mass at a given age:

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.scatter(cluster.Mstar, cluster.Lx(100.0))
ax.set_xlabel(r"$M_\star$ [$M_\odot$]")
ax.set_ylabel(r"$L_X$ [erg s$^{-1}$]")
ax.set_yscale('log')
plt.show()
```

---

## Step 5: Save and reload

Cluster calculations can be expensive for large numbers of stars. Save and reload with:

```python
import mors

cluster.Save(filename="cluster.pickle")

# Always use mors.Load rather than pickle.load directly,
# as it re-attaches the quantity accessor functions
cluster2 = mors.Load("cluster.pickle")
```

---

## Step 6: Use the built-in model cluster (optional)

MORS includes a model cluster distribution derived from observed young cluster rotation measurements. Load and evolve it like any other cluster:

```python
import mors

Mstar, Omega = mors.ModelCluster()
cluster = mors.Cluster(Mstar=Mstar, Omega=Omega)
```

!!! note "Citation"
    If you use this model cluster distribution in published research, cite the rotation measurement sources listed in Table 1 of Johnstone et al. (2021) [^johnstone2021] in addition to the MORS paper.

---

## Common pitfalls

- `Mstar`, `Omega`, and `Age` (if provided) must all be the same length.
- `Age` is always in **Myr**; `Omega` is in **Ω☉**, not rad s$^{-1}$.
- Do not use `pickle.load` directly to reload a saved cluster — use `mors.Load` instead.
- Per-star attributes are named `cluster.star0`, `cluster.star1`, etc. (not `cluster.stars0`).

---

[^johnstone2021]: Johnstone, C. P., Bartel, M., & Güdel, M. (2021). The active lives of stars: a complete description of the rotation and XUV evolution of F, G, K, and M dwarfs. *Astronomy & Astrophysics, 649*, A96. https://doi.org/10.1051/0004-6361/202038407