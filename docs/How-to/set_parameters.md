## Setting custom simulation parameters (How-to)

### Goal
Create simulation parameters for a `Star` (or `Cluster`) run, and optionally restrict the ages saved in output tracks using `AgesOut`.  This overrides MORS default simulation parameters. 

### Prerequisites
Make sure MORS and stellar evolution data are installed:

```bash
pip install fwl-mors
mors download all
```

---

### Step 1: Start from the default parameter set

Create a parameter dictionary identical to the internal defaults (`paramsDefault` in `parameters.py`):

```python
import mors
params = mors.NewParams()
```

This gives you a normal Python dictionary you can edit.

---

### Step 2: Change one or more parameters

**Option A: edit the dictionary after creation**
```python
import mors
params = mors.NewParams()

params["param1"] = 1.5
params["param2"] = 2.5
```

**Option B: set values when calling `NewParams` (recommended)**
```python
import mors
params = mors.NewParams(param1=1.5, param2=2.5)
```

---

### Step 3: Pass the parameter dictionary into `Star` (or `Cluster`)

```python
import mors
star = mors.Star(Mstar=1.0, Omega=10.0, params=params)
```

(Use the same `params=` keyword when creating a `mors.Cluster`.)

---

### Step 4: Discover available parameters

To print a complete list of parameters (and their meanings/values as exposed by MORS):

```python
import mors
mors.PrintParams()
```

You can also inspect the source file `parameters.py` in your MORS installation.

---

### Step 5: Restrict output ages with `AgesOut` (optional)

By default, MORS computes tracks on its internal age grid. If you only need values at specific ages, set `AgesOut` so the saved tracks contain only those ages **plus the starting age (1 Myr)**.

**Single age**
```python
import mors
star = mors.Star(Mstar=1.0, Omega=10.0, AgesOut=100.0)  # Myr
```

**Multiple ages**
```python
import numpy as np
import mors

ages = np.array([100.0, 200.0, 300.0, 400.0])  # Myr (ascending)
star = mors.Star(Mstar=1.0, Omega=10.0, AgesOut=ages)
```

Notes:
- The simulation ends at the **largest** age in `AgesOut`.
- Provide `AgesOut` in **ascending** order.
- If you later call interpolating helpers like `star.Lx(Age)` at arbitrary ages, results can be inaccurate if `AgesOut` is too sparse.
- Very large `AgesOut` grids can slow down calculations significantly.

---

### Common pitfalls
- `AgesOut` is in **Myr**.
- If you intend to query many arbitrary ages later, prefer the default age grid (don’t over-thin `AgesOut`).
