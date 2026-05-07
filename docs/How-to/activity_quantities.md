# Find stellar rotation and activity quantities

Compute high-energy emission quantities (X-ray, EUV, Ly-$\alpha$) from stellar mass, age, and rotation rate, optionally add variability scatter, and retrieve detailed model diagnostics via `ExtendedQuantities`.

## Prerequisites

Make sure the package and stellar evolution data are installed:

```bash
pip install fwl-mors
mors download all
```

!!! info "Units"
    `Age` is in **Myr**, `Prot` is in **days**, and `Omega` is in units of the **current solar rotation rate** ($\Omega_\odot = 2.67 \times 10^{-6}$ rad s$^{-1}$).

---

## Step 1: Get the full XUV dictionary

Use `mors.Lxuv` with either `Omega` (Ω☉) or `Prot` (days) to specify the surface rotation:

```python
import mors

# using rotation rate
xuv = mors.Lxuv(Mstar=1.0, Age=5000.0, Omega=1.0)

# using rotation period
xuv = mors.Lxuv(Mstar=1.0, Age=5000.0, Prot=25.4)
```

The returned dictionary contains:

| Key | Description | Units |
|---|---|---|
| `Lxuv`, `Lx`, `Leuv`, `Leuv1`, `Leuv2`, `Lly` | Luminosities | erg s⁻¹ |
| `Fxuv`, `Fx`, `Feuv`, `Feuv1`, `Feuv2`, `Fly` | Surface fluxes | erg s⁻¹ cm⁻² |
| `Rxuv`, `Rx`, `Reuv`, `Reuv1`, `Reuv2`, `Rly` | Bolometric ratios | dimensionless |

```python
print(sorted(xuv.keys()))
print(f"Lx = {xuv['Lx']:.3e} erg/s")
```

---

## Step 2: Retrieve a single quantity directly

Convenience functions exist for X-ray, EUV, and Ly-$\alpha$ luminosities:

```python
import mors

Lx  = mors.Lx(Mstar=1.0, Age=5000.0, Omega=1.0)
Lly = mors.Lly(Mstar=1.0, Age=5000.0, Omega=1.0)
```

`mors.Leuv` supports a `band` argument to select the wavelength range:

```python
Leuv_total = mors.Leuv(Mstar=1.0, Age=5000.0, Omega=1.0, band=0)  # 10–92 nm
Leuv1      = mors.Leuv(Mstar=1.0, Age=5000.0, Omega=1.0, band=1)  # 10–36 nm
Leuv2      = mors.Leuv(Mstar=1.0, Age=5000.0, Omega=1.0, band=2)  # 36–92 nm
```

---

## Step 3: Add variability scatter (optional)

MORS provides scatter functions that sample a log-normal distribution to represent stellar variability around the mean emission.

### X-ray scatter

Pass the mean value (any of `Lx`, `Fx`, or `Rx`) and receive a delta to add:

```python
import mors

Lx  = mors.Lx(Mstar=1.0, Age=5000.0, Omega=1.0)
dLx = mors.XrayScatter(Lx)
Lx_scattered = Lx + dLx
```

### Full XUV scatter

`XUVScatter` takes the dictionary from `Lxuv` and returns a dictionary of deltas with the same keys, with correlated offsets across all bands:

```python
import mors

xuv  = mors.Lxuv(Mstar=1.0, Age=5000.0, Omega=1.0)
dxuv = mors.XUVScatter(xuv)

xuv_scattered = {k: xuv[k] + dxuv[k] for k in xuv}
```

### Controlling the scatter width

The scatter width is set by `sigmaXray` (default 0.359 dex). Pass a custom parameter dictionary to both the emission and scatter functions to change it:

```python
import mors

my_params = mors.NewParams(sigmaXray=0.3)

Lx  = mors.Lx(Mstar=1.0, Age=5000.0, Omega=1.0, params=my_params)
dLx = mors.XrayScatter(Lx, params=my_params)
Lx_scattered = Lx + dLx
```

---

## Step 4: Get detailed model diagnostics (`ExtendedQuantities`)

`ExtendedQuantities` returns a large dictionary of model internals including stellar structure properties, wind quantities, magnetic field strengths, and torques. It requires both the envelope and core rotation rates:

```python
import mors

q = mors.ExtendedQuantities(Mstar=1.0, Age=5000.0, OmegaEnv=1.0, OmegaCore=1.0)
print(list(q.keys()))
```

For a coupled core–envelope system at early ages, `OmegaEnv` and `OmegaCore` will generally differ. For a fully spun-down star, they can be set equal.

---

## Common pitfalls

- Do not set both `Omega` and `Prot` in the same call — only one rotation representation can be used at a time.
- Scatter functions are stochastic — results differ each call unless you set a NumPy random seed.
- `ExtendedQuantities` requires both `OmegaEnv` and `OmegaCore`; unlike `Lxuv`, it does not accept `Omega` as a shorthand.