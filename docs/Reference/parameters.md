# Model parameter reference

All model behaviour is controlled through a single dictionary (`parameters.paramsDefault`). A modified parameter dictionary can be created with `parameters.NewParams(**kwargs)`, which copies the defaults and overrides the specified keys:

```python
import mors
my_params = mors.NewParams(dAgeMax=10.0, CoreEnvelopeDecoupling=False)
star = mors.Star(Mstar=1.0, Omega=1.0, params=my_params)
```

## Numerical integration

| Parameter | Default | Description |
|---|---|---|
| `TimeIntegrationMethod` | `'RosenbrockFixed'` | ODE solver (options: `ForwardEuler`, `RungeKutta4`, `RungeKuttaFehlberg`, `Rosenbrock`, `RosenbrockFixed`) |
| `AgeMinDefault` | $1.0$ Myr | Default start age of evolutionary tracks |
| `AgeMaxDefault` | $5000.0$ Myr | Default end age of evolutionary tracks |
| `dAgeMin` | $10^{-5}$ Myr | Minimum allowed timestep |
| `dAgeMax` | $50.0$ Myr | Maximum allowed timestep |
| `nStepMax` | $10^6$ | Maximum number of timesteps before error |

## Physical processes

| Parameter | Default | Description |
|---|---|---|
| `CoreEnvelopeDecoupling` | `True` | Enable two-zone core–envelope model |
| `WindTorque` | `True` | Include wind spin-down torque |
| `CoreEnvelopeTorque` | `True` | Include core–envelope coupling torque |
| `DiskLocking` | `True` | Include disk-locking torque |
| `MomentInertiaChangeTorque` | `True` | Include moment of inertia change torque (do not disable) |
| `CoreGrowthTorque` | `True` | Include core-growth torque (do not disable) |
| `BreakupMdotIncrease` | `True` | Enhance $\dot{M}$ when approaching breakup rotation |
| `ExtendedTracks` | `False` | Return full set of output quantities (overridden to `True` by `Star` and `Cluster`) |

## Two-zone thresholds

| Parameter | Default | Description |
|---|---|---|
| `MstarThresholdCE` | $0.35\,M_\odot$ | Stars below this mass are treated as fully convective |
| `IcoreThresholdCE` | $0.01$ | Core–envelope decoupling disabled if $I_\mathrm{core}/I_\mathrm{total}$ is below this value |

## Disk locking

| Parameter | Default | Description |
|---|---|---|
| `aDiskLock` | $13.5$ | Coefficient $a$ in $t_\mathrm{disk} = a\,\Omega_0^b$ |
| `bDiskLock` | $-0.5$ | Exponent $b$ in $t_\mathrm{disk} = a\,\Omega_0^b$ |
| `ageDLmax` | $15.0$ Myr | Maximum disk-locking age |

## Wind and magnetic field

| Parameter | Default | Description |
|---|---|---|
| `Kwind` | $11.0$ | Wind torque normalisation constant $K_\tau$ |
| `BdipSun` | $1.35$ G | Solar dipole field strength $B_{\mathrm{dip},\odot}$ |
| `aBdip` | $-1.32$ | Power-law index of $B_\mathrm{dip}$–$Ro$ relation |
| `RoSatBdip` | $0.0605$ | Saturation Rossby number for $B_\mathrm{dip}$ |
| `MdotSun` | $1.4 \times 10^{-14}\,M_\odot\,\mathrm{yr}^{-1}$ | Solar mass loss rate |
| `aMdot` | $-1.7591$ | Power-law index on $Ro$ in $\dot{M}$ relation |
| `bMdot` | $0.6494$ | Power-law index on $M_\star$ in $\dot{M}$ relation |
| `RoSatMdot` | $0.0605$ | Saturation Rossby number for $\dot{M}$ |
| `fracBreakThreshold` | $0.1$ | Fraction of $\Omega_\mathrm{break}$ at which magnetocentrifugal enhancement begins |

## Core–envelope coupling

| Parameter | Default | Description |
|---|---|---|
| `aCoreEnvelope` | $25.6015$ | Coefficient $a_\mathrm{ce}$ in coupling timescale |
| `bCoreEnvelope` | $-3.4817 \times 10^{-2}$ | Exponent $b_\mathrm{ce}$ in coupling timescale |
| `cCoreEnvelope` | $-0.4476$ | Exponent $c_\mathrm{ce}$ in coupling timescale |
| `timeCEmin` | $0.0$ Myr | Minimum allowed core–envelope coupling timescale |

## X-ray emission

| Parameter | Default | Description |
|---|---|---|
| `RoSatXray` | $0.0605$ | Saturation Rossby number for X-ray emission |
| `RxSatXray` | $5.135 \times 10^{-4}$ | $R_X$ at the saturation threshold |
| `beta1Xray` | $-0.135$ | Power-law index $\beta_1$ in the saturated regime |
| `beta2Xray` | $-1.889$ | Power-law index $\beta_2$ in the unsaturated regime |
| `sigmaXray` | $0.359$ dex | Standard deviation of log-normal X-ray variability scatter |

## Rotation fitting

| Parameter | Default | Description |
|---|---|---|
| `Omega0FitMin` | $0.1\,\Omega_\odot$ | Minimum initial rotation rate considered when fitting |
| `Omega0FitMax` | $50.0\,\Omega_\odot$ | Maximum initial rotation rate considered when fitting |
| `nStepMaxFit` | $1000$ | Maximum bisection steps when fitting initial rotation |
| `toleranceFit` | $10^{-5}$ | Convergence tolerance for rotation fitting |

## Other

| Parameter | Default | Description |
|---|---|---|
| `dMstarPer` | $0.1\,M_\odot$ | Half-width of mass bin used when computing rotation percentiles |
| `AgeHZ` | $5000.0$ Myr | Age at which habitable zone boundaries are calculated |

A modified parameter dictionary can be created with `parameters.NewParams(**kwargs)`, which copies the defaults and overrides the specified keys.