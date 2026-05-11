# Setting custom simulation parameters

Create a custom parameter dictionary for a `Star` or `Cluster` run, and optionally restrict the ages saved in output tracks using `AgesOut`.

## Prerequisites

Install MORS and download stellar evolution data:

```bash
pip install fwl-mors
mors download all
```

!!! info "Units"
    `Age` is in **Myr**, `Prot` is in **days**, and `Omega` is in units of the **current solar rotation rate** ($\Omega_\odot = 2.67 \times 10^{-6}$ rad s$^{-1}$).
---

## Step 1: Start from the default parameter set

Create a parameter dictionary identical to the internal defaults:

```python
import mors

my_params = mors.NewParams()
```

This returns a standard Python dictionary that you can inspect and modify freely.

---

## Step 2: Change one or more parameters

**Option A: pass values directly to `NewParams` (recommended)**

```python
import mors

my_params = mors.NewParams(Kwind=15.0, dAgeMax=10.0)
```

**Option B: edit the dictionary after creation**

```python
import mors

my_params = mors.NewParams()
my_params['Kwind'] = 15.0
my_params['dAgeMax'] = 10.0
```

See the [Parameters](../Reference/parameters.md) page for the full list of available parameters and their defaults.

---

## Step 3: Pass the parameter dictionary into `Star` or `Cluster`

```python
import mors

star = mors.Star(Mstar=1.0, Omega=10.0, params=my_params)
cluster = mors.Cluster(Mstar=Mstar, Omega=Omega, params=my_params)
```

---

## Step 4: Print the current parameter values

`PrintParams` uses the logging system, so configure logging first:

```python
import mors
from mors.logs import setup_logger

setup_logger("INFO")

# print all defaults
mors.PrintParams()

# or print a custom dictionary
mors.PrintParams(params=my_params)
```

---

## Step 5: Restrict output ages with `AgesOut` (optional)

By default, MORS saves tracks on its internal adaptive age grid. If you only need values at specific ages, pass `AgesOut` to restrict the saved output to those ages:

**Single age:**

```python
import mors

star = mors.Star(Mstar=1.0, Omega=10.0, AgesOut=100.0)  # Myr
```

**Multiple ages:**

```python
import numpy as np
import mors

ages = np.array([100.0, 200.0, 300.0, 400.0])  # Myr, must be ascending
star = mors.Star(Mstar=1.0, Omega=10.0, AgesOut=ages)
```

!!! info "How `AgesOut` affects the simulation"
    - The simulation runs from 1 Myr and ends at the **last age** in `AgesOut`.
    - Ages below 1 Myr are silently dropped.
    - `AgesOut` must be in **ascending** order.
    - Interpolating functions like `star.Lx(Age=...)` can return inaccurate results if the saved grid is too sparse for the ages you query.

---

## Common pitfalls

- `AgesOut` is in **Myr**.
- The simulation always starts at 1 Myr regardless of `AgesOut`.
- If you later need to query many arbitrary ages, prefer the default age grid rather than a sparse `AgesOut`.
- `PrintParams` produces no output unless logging is configured.