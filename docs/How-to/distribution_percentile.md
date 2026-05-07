# Using model percentiles for initial rotation

Pick an initial rotation rate from the built-in model rotation distribution [^johnstone2021], inspect a star's inferred percentile, and convert between rotation rate and percentile for a given stellar mass.

## Prerequisites

Install MORS and download stellar evolution data:

```bash
pip install fwl-mors
mors download all
```

!!! info "Units"
    `Age` is in **Myr**, `Prot` is in **days**, and `Omega` is in units of the **current solar rotation rate** ($\Omega_\odot = 2.67 \times 10^{-6}$ rad s$^{-1}$).
---

## Step 1: Get the built-in model cluster distribution

This returns arrays of stellar masses and their 1 Myr rotation rates, derived by evolving observed cluster rotation distributions back to 1 Myr:

```python
import mors

Mstar_dist, Omega_dist = mors.ModelCluster()
print(Mstar_dist.shape, Omega_dist.shape)
```

!!! note "Citation"
    If you use this distribution directly in published research, cite the rotation measurement sources listed in Table 1 of Johnstone et al. (2021) [^johnstone2021] in addition to the MORS paper.

---

## Step 2: Create a star by percentile

Set initial rotation using a numeric percentile (0–100) or the string shortcuts `'slow'`, `'medium'`, `'fast'`, which map to the 5th, 50th, and 95th percentiles respectively:

```python
import mors

star_slow   = mors.Star(Mstar=1.0, percentile='slow')    # 5th percentile
star_medium = mors.Star(Mstar=1.0, percentile='medium')  # 50th percentile
star_fast   = mors.Star(Mstar=1.0, percentile='fast')    # 95th percentile

# or with a numeric value
star = mors.Star(Mstar=1.0, percentile=10.0)
```

---

## Step 3: Read back the star's inferred percentile

Regardless of how the star is created (`Omega`, `Prot`, or `percentile`), MORS stores the inferred percentile in the 1 Myr distribution after computing the tracks:

```python
print(star_slow.percentile)
```

---

## Step 4: Convert a rotation rate to a percentile

```python
import mors

# from Omega (Ω☉)
p = mors.Percentile(Mstar=1.0, Omega=10.0)
print(p)

# from Prot (days)
p = mors.Percentile(Mstar=1.0, Prot=1.0)
print(p)
```

---

## Step 5: Convert a percentile to a rotation rate

```python
import mors

Omega = mors.Percentile(Mstar=1.0, percentile=10.0)  # returns Ω in Ω☉
print(Omega)
```

---

## Step 6: Control the mass window used for percentiles

Percentiles are computed from stars within a mass window around `Mstar`. The half-width is controlled by `dMstarPer` (default: $0.1\,M_\odot$). To change it, create a custom parameter dictionary:

```python
import mors

my_params = mors.NewParams(dMstarPer=0.05)
star = mors.Star(Mstar=1.0, percentile='medium', params=my_params)
```

---

## Step 7: Use a custom rotation distribution (optional)

Pass your own mass and rotation arrays into `Percentile` instead of using the built-in 1 Myr distribution:

```python
import numpy as np
import mors

MstarDist = np.array([1.0, 1.0, 1.0, 0.9, 1.1])
OmegaDist = np.array([2.0, 5.0, 10.0, 3.0, 7.0])

p = mors.Percentile(Mstar=1.0, Omega=6.0, MstarDist=MstarDist, OmegaDist=OmegaDist)
print(p)
```

You can also supply a period distribution instead:

```python
MstarDist = np.array([1.0, 1.0, 0.9, 1.1])
ProtDist  = np.array([12.0, 6.0, 9.0, 7.0])  # days

p = mors.Percentile(Mstar=1.0, Prot=8.0, MstarDist=MstarDist, ProtDist=ProtDist)
print(p)
```

---

## Common pitfalls

- Percentiles refer to the **initial (~1 Myr)** rotation distribution used by the model cluster.
- `Omega` is in **Ω☉**, not rad s$^{-1}$. `Prot` is in **days**.
- If the custom distribution is sparse or covers a narrow mass range, at least two stars must fall within the `dMstarPer` window, otherwise `Percentile` will raise an exception.

---

[^johnstone2021]: Johnstone, C. P., Bartel, M., & Güdel, M. (2021). The active lives of stars: a complete description of the rotation and XUV evolution of F, G, K, and M dwarfs. *Astronomy & Astrophysics, 649*, A96. https://doi.org/10.1051/0004-6361/202038407