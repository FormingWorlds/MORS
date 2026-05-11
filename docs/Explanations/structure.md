# MORS model overview

MORS computes the rotational spin-down and high-energy (X-ray, EUV, Ly-$\alpha$) emission history of low-mass stars with masses between $0.1$ and $1.25\,M_\odot$, from 1 Myr through the end of the main sequence. The model is described in full in Johnstone, Bartel & Güdel (2021) [^johnstone2021] and consists of a rotational evolution model and a high-energy emission model, found in the sidebar. It also calculates habitable zone fluxes and builds historical spectra from modern reference spectra.

A model parameter reference can be found [here](../Reference/parameters.md).

## Stellar structure

All time-dependent internal stellar properties (radius, luminosity, effective temperature, core and envelope moments of inertia and their rates of change, convective turnover time, core radius and mass) are taken from the pre-computed grids of Spada et al. (2013) [^spada]. The grid spans 24 mass bins from $0.1$ to $1.25\,M_\odot$ and is loaded once at startup by `stellarevo.StarEvo`. When a stellar mass falls between two grid points, a bilinear interpolation in mass and log-age is performed transparently by `stellarevo._ValueSingle`.

The relevant solar calibration values hard-coded in `constants.py` are:

| Quantity | Symbol | Value |
|---|---|---|
| Solar rotation rate | $\Omega_\odot$ | $2.67 \times 10^{-6}$ rad s$^{-1}$ |
| Solar bolometric luminosity | $L_\odot$ | $3.828 \times 10^{33}$ erg s$^{-1}$ |
| Solar convective turnover time | $\tau_\odot$ | $28.436$ days |
| Solar Rossby number | $Ro_\odot$ | $P_{\mathrm{rot},\odot} / \tau_\odot$ |

The Rossby number is defined throughout the code as

$$Ro = \frac{P_\mathrm{rot}}{\tau_\mathrm{conv}}$$

where $P_\mathrm{rot}$ is the surface rotation period in days and $\tau_\mathrm{conv}$ is the convective turnover time from the Spada models, both evaluated at the same mass and age.

[^johnstone2021]: Johnstone, C. P., Bartel, M., & Güdel, M. (2021). The active lives of stars: a complete description of the rotation and XUV evolution of F, G, K, and M dwarfs. *Astronomy & Astrophysics, 649*, A96. https://doi.org/10.1051/0004-6361/202038407

[^spada]: Spada, F., Demarque, P., Kim, Y.-C., & Sills, A. (2013). The radius discrepancy in low-mass stars: single versus binaries. *The Astrophysical Journal, 776*(2), 87. https://doi.org/10.1088/0004-637X/776/2/87