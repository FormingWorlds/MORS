## Rotation and activity quantities (How-to)

### Goal
Compute high-energy emission quantities (X-ray, EUV, Ly-α) from stellar **mass**, **age**, and **rotation**, optionally add variability/scatter, and (if needed) retrieve a larger set of model diagnostics via `ExtendedQuantities`.

### Prerequisites
Install MORS and download the required stellar evolution data:

```bash
pip install fwl-mors
mors download all
```

> **Units:** `Mstar` in **M☉**, `Age` in **Myr**, `Prot` in **days**, `Omega` in **Ω☉**. Luminosities are in **erg s⁻¹** and surface fluxes in **erg s⁻¹ cm⁻²**.

---

### Step 1: Get the full XUV dictionary (`Lxuv`)

Use `Omega` (or `OmegaEnv`) **or** `Prot` to specify the surface rotation.

**Using Ω (Ω☉):**
```python
import mors
xuv = mors.Lxuv(Mstar=1.0, Age=5000.0, Omega=10.0)
```

**Using rotation period (days):**
```python
import mors
xuv = mors.Lxuv(Mstar=1.0, Age=5000.0, Prot=1.0)
```

The returned dictionary includes luminosities, surface fluxes, and bolometric-normalized values, e.g.:
- Luminosities: `Lxuv`, `Lx`, `Leuv1`, `Leuv2`, `Leuv`, `Lly`  (erg s⁻¹)
- Fluxes: `Fxuv`, `Fx`, `Feuv1`, ... (erg s⁻¹ cm⁻²)
- Normalized: `Rxuv`, `Rx`, `Reuv1`, ... (dimensionless)

To see what keys are present:
```python
print(sorted(xuv.keys()))
```

---

### Step 2: Retrieve a single quantity directly (`Lx`, `Leuv`, `Lly`)

```python
import mors

Lx  = mors.Lx(Mstar=1.0, Age=5000.0, Omega=10.0)
Leu = mors.Leuv(Mstar=1.0, Age=5000.0, Omega=10.0)
Lly = mors.Lly(Mstar=1.0, Age=5000.0, Omega=10.0)
```

#### Choose an EUV sub-band with `band`
`Leuv(..., band=...)` supports:
- `band=0` → 10–92 nm (total EUV)
- `band=1` → 10–36 nm (EUV1)
- `band=2` → 36–92 nm (EUV2)

```python
import mors
Leuv_total = mors.Leuv(Mstar=1.0, Age=5000.0, Omega=10.0, band=0)
Leuv1      = mors.Leuv(Mstar=1.0, Age=5000.0, Omega=10.0, band=1)
Leuv2      = mors.Leuv(Mstar=1.0, Age=5000.0, Omega=10.0, band=2)
```

---

### Step 3: Add variability/scatter (optional)

MORS provides random scatter terms intended to represent variability as a log-normal scatter.

#### X-ray scatter (`XrayScatter`)
You pass the mean value (e.g., `Lx`) and get a delta to add:
```python
import mors

Lx = mors.Lx(Mstar=1.0, Age=5000.0, Omega=10.0)
dLx = mors.XrayScatter(Lx)

Lx_scattered = Lx + dLx
```

You can also pass `Fx` or `Rx` and receive `dFx` / `dRx`.

#### Full XUV scatter (`XUVScatter`)
`XUVScatter` takes the dictionary from `Lxuv` and returns a dictionary of deltas with the same keys:
```python
import mors

xuv  = mors.Lxuv(Mstar=1.0, Age=5000.0, Omega=10.0)
dxuv = mors.XUVScatter(xuv)

# Example: apply deltas to get one scattered realization
xuv_scattered = {k: xuv[k] + dxuv[k] for k in xuv}
```

**Controlling the scatter width:** the X-ray scatter width is controlled by `sigmaXray` in the parameters file. You can override it by passing a custom `params` dictionary (see the parameter how-to):

```python
import mors

params = mors.NewParams(sigmaXray=0.3)  # example value
Lx = mors.Lx(Mstar=1.0, Age=5000.0, Omega=10.0, params=params)
dLx = mors.XrayScatter(Lx, params=params) if "params" in mors.XrayScatter.__code__.co_varnames else mors.XrayScatter(Lx)
```
*(If `XrayScatter` does not accept `params` directly, set `sigmaXray` via your model run parameters and use it consistently.)*

---

### Step 4: Get detailed diagnostics (`ExtendedQuantities`)

If you need additional model internals (stellar properties, wind quantities, magnetic fields, torques), call `ExtendedQuantities` with envelope and core rotation rates:

```python
import mors

q = mors.ExtendedQuantities(Mstar=1.0, Age=5000.0, OmegaEnv=10.0, OmegaCore=10.0)
print(list(q))
```

---

### Common pitfalls
- Don’t mix `Omega` (Ω☉) and `Prot` (days) in the same call; pick one rotation representation.
- Scatter functions are random; results differ each run unless you control the random seed in your workflow.
- `ExtendedQuantities` requires **both** `OmegaEnv` and `OmegaCore`.
