# Habitable zone boundaries

Habitable zone boundaries are computed following Kopparapu et al. (2013a)[^cite-kopparapu2013a] using stellar luminosities and effective temperatures from the Spada et al. (2013)[^cite-spada2013] models (`physicalmodel.aOrbHZ`). Six boundaries are returned:

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

Each boundary distance is computed from the stellar flux factor $S_\mathrm{eff}$ following Kopparapu et al. (2013a)[^cite-kopparapu2013a], eq. 3:

$$a = \left(\frac{L_\mathrm{bol}}{L_\odot \cdot S_\mathrm{eff}}\right)^{1/2} \quad (\mathrm{AU})$$

where $S_\mathrm{eff}$ depends on the stellar effective temperature $T_\mathrm{eff}$ via a fourth-order polynomial anchored to solar values, with the coefficients of Table 3 in the erratum of Kopparapu et al. (2013b)[^cite-kopparapu2013b].

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

[^cite-kopparapu2013a]: R. K. Kopparapu, R. Ramirez, J. F. Kasting, V. Eymet, T. D. Robinson, S. Mahadevan, R. C. Terrien, S. Domagal-Goldman, V. Meadows, R. Deshpande, *[Habitable Zones around Main-sequence Stars: New Estimates](https://doi.org/10.1088/0004-637X/765/2/131)*, The Astrophysical Journal, 765, 131, 2013. [SciX](https://scixplorer.org/abs/2013ApJ...765..131K/abstract).

[^cite-kopparapu2013b]: R. K. Kopparapu, R. Ramirez, J. F. Kasting, V. Eymet, T. D. Robinson, S. Mahadevan, R. C. Terrien, S. Domagal-Goldman, V. Meadows, R. Deshpande, *[Erratum: "Habitable Zones around Main-sequence Stars: New Estimates" (2013, ApJ, 765, 131)](https://doi.org/10.1088/0004-637X/770/1/82)*, The Astrophysical Journal, 770, 82, 2013. [SciX](https://scixplorer.org/abs/2013ApJ...770...82K/abstract).

[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The Radius Discrepancy in Low-mass Stars: Single versus Binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776, 87, 2013. [SciX](https://scixplorer.org/abs/2013ApJ...776...87S/abstract).
