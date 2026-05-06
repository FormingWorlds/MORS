# Habitable zone boundaries

Habitable zone boundaries are computed following Kopparapu et al. (2013) [^kopparapu] using stellar luminosities and effective temperatures from the Spada models [^spada] (`physicalmodel.aOrbHZ`). Six boundaries are returned:

| Boundary | Key |
|---|---|
| Recent Venus | `RecentVenus` |
| Runaway Greenhouse | `RunawayGreenhouse` |
| Moist Greenhouse | `MoistGreenhouse` |
| Maximum Greenhouse | `MaximumGreenhouse` |
| Early Mars | `EarlyMars` |
| Midpoint (Moist + maximum Greenhouse) | `HZ` |

All distances are in AU and computed by default at 5000 Myr (`params['AgeHZ']`).

The `HZ` boundary is defined as the midpoint between the moist and maximum greenhouse limits:

$$a_\mathrm{HZ} = \frac{1}{2}\left(a_\mathrm{MoistGreenhouse} + a_\mathrm{MaximumGreenhouse}\right)$$

Each boundary distance is computed from the stellar flux factor $S_\mathrm{eff}$ following Kopparapu et al. (2013), eq. 3 [^kopparapu]:

$$a = \left(\frac{L_\mathrm{bol}}{L_\odot \cdot S_\mathrm{eff}}\right)^{1/2} \quad (\mathrm{AU})$$

where $S_\mathrm{eff}$ depends on the stellar effective temperature $T_\mathrm{eff}$ via a fourth-order polynomial anchored to solar values.

## Fluxes in the habitable zone

$F_X$, $F_\mathrm{EUV,1}$, $F_\mathrm{EUV,2}$, $F_\mathrm{EUV}$, and $F_\mathrm{Ly\alpha}$ are all computed at the `HZ` orbital distance and stored as standard quantities on every evolutionary track:

| Track quantity | Description |
|---|---|
| `FxHZ` | X-ray flux at $a_\mathrm{HZ}$ |
| `Feuv1HZ` | EUV1 (10–36 nm) flux at $a_\mathrm{HZ}$ |
| `Feuv2HZ` | EUV2 (36–92 nm) flux at $a_\mathrm{HZ}$ |
| `FeuvHZ` | Total EUV (10–92 nm) flux at $a_\mathrm{HZ}$ |
| `FlyHZ` | Ly-$\alpha$ flux at $a_\mathrm{HZ}$ |

These are computed as $F = L / (4\pi a_\mathrm{HZ}^2)$ for each band.

!!! note
    The habitable zone boundaries are calculated once at instantiation using stellar properties at `params['AgeHZ']` (default 5 Gyr) and held fixed throughout the evolutionary track. This reflects the interest in planets that spend billions of years in the habitable zone, for which the main-sequence stellar properties are the appropriate reference.

---

[^kopparapu]: Kopparapu, R. K., Ramirez, R., Kasting, J. F., et al. (2013). Habitable zones around main-sequence stars: new estimates. *The Astrophysical Journal, 765*(2), 131. https://doi.org/10.1088/0004-637X/765/2/131

[^spada]: Spada, F., Demarque, P., Kim, Y.-C., & Sills, A. (2013). The radius discrepancy in low-mass stars: single versus binaries. *The Astrophysical Journal, 776*(2), 87. https://doi.org/10.1088/0004-637X/776/2/87