# High-energy emission

All high-energy emission is computed from the instantaneous rotation state in `physicalmodel.ExtendedQuantities`. Throughout this section, surface fluxes are evaluated at the stellar surface (in erg s$^{-1}$ cm$^{-2}$) and luminosities are in erg s$^{-1}$.

!!! note "Wavelength band definitions"
    Following Johnstone et al. (2021)[^cite-johnstone2021]:

    - **XUV**: 0.1–92 nm
    - **X-ray**: 0.517–12.4 nm (2.4–0.1 keV)
    - **EUV** (total): 10–92 nm
    - **EUV1**: 10–36 nm
    - **EUV2**: 36–92 nm
    - **Ly-$\alpha$**: 121.6 nm

---

## 1. X-ray emission

The ratio $R_X = L_X / L_\mathrm{bol}$ is related to the Rossby number by a broken power law constrained using the sample of Wright et al. (2011)[^cite-wright2011] with convective turnover times from Spada et al. (2013)[^cite-spada2013]:

$$R_X = \begin{cases} C_1 \, Ro^{\beta_1} & Ro \leq Ro_\mathrm{sat} \quad \text{(saturated)} \\ C_2 \, Ro^{\beta_2} & Ro > Ro_\mathrm{sat} \quad \text{(unsaturated)} \end{cases} \tag{17}$$

The constants $C_1$ and $C_2$ are derived from the requirement that the two power laws are equal at the saturation point ($R_{X,\mathrm{sat}} = C_1 Ro_\mathrm{sat}^{\beta_1} = C_2 Ro_\mathrm{sat}^{\beta_2}$). The fitted parameters are:

| Parameter | Symbol | Value |
|---|---|---|
| Saturation Rossby number | $Ro_\mathrm{sat}$ | $0.0605$ |
| Saturation $R_X$ | $R_{X,\mathrm{sat}}$ | $5.135 \times 10^{-4}$ |
| Saturated power-law index | $\beta_1$ | $-0.135$ |
| Unsaturated power-law index | $\beta_2$ | $-1.889$ |

The $R_X$ relation is shallower in the unsaturated regime than many previous estimates, consistent with the Sun being less X-ray active than other stars with similar parameters (Reinhold et al. 2020[^cite-reinhold2020]). The X-ray luminosity and surface flux then follow as:

$$L_X = R_X \cdot L_\mathrm{bol}, \qquad F_X = \frac{L_X}{4\pi R_\star^2}$$

Implementation: `physicalmodel._Xray`.

### X-ray variability

Real stellar X-ray emission varies around the average relation. The observed scatter in the distribution of $R_X$ against $Ro$ can be described as a log-normal centred on zero with standard deviation $\sigma = 0.359$ dex (`params['sigmaXray']`), meaning stars spend approximately 90% of their time within one standard deviation of the average (Johnstone et al. 2021[^cite-johnstone2021]). This scatter can be sampled with `physicalmodel.XrayScatter` or `physicalmodel.XUVScatter`, which apply correlated random offsets consistently across all XUV bands.

---

## 2. Coronal temperature

Stars with higher X-ray surface fluxes have hotter coronae. The emission-measure-weighted average coronal temperature is estimated from $F_X$ following Johnstone & Güdel (2015)[^cite-johnstone2015]:

$$\bar{T}_\mathrm{cor} = 0.11\, F_X^{0.26} \quad (\mathrm{MK}) \tag{18}$$

This relation is mass-independent when expressed in surface fluxes. Since coronae dominate emission at wavelengths below $\sim$40 nm, stars with higher $F_X$ emit a larger fraction of their XUV at shorter wavelengths. Implementation: `physicalmodel._Tcor`.

---

## 3. EUV emission

EUV emission is empirically related to $F_X$ rather than to $L_X$ or $R_X$, since $F_X$ best captures the physical state of the emitting plasma (Johnstone & Güdel 2015[^cite-johnstone2015]). The relations are derived from EUVE observations of nearby F, G, K, and M stars (Craig et al. 1997[^cite-craig1997]) and solar spectra.

### EUV band 1 (10–36 nm)

Constrained from the EUVE stellar sample using the OLS Bisector method (Johnstone et al. 2021[^cite-johnstone2021], Eq. 19):

$$\log F_\mathrm{EUV,1} = 2.04 + 0.681\,\log F_X \tag{19}$$

which gives

$$\frac{F_\mathrm{EUV,1}}{F_X} = 110\,F_X^{-0.319} \tag{20}$$

Implementation: `physicalmodel._EUV1`.

### EUV band 2 (36–92 nm)

Constrained using solar spectra only, considering solar values with $L_X > 10^{27}$ erg s$^{-1}$ (Johnstone et al. 2021[^cite-johnstone2021], Eq. 21):

$$\log F_\mathrm{EUV,2} = -0.0341 + 0.920\,\log F_\mathrm{EUV,1} \tag{21}$$

which Johnstone et al. (2021) print as

$$\frac{F_\mathrm{EUV,2}}{F_\mathrm{EUV,1}} = 0.924\,F_\mathrm{EUV,1}^{-0.0798} \tag{22}$$

This relation is less reliable than the relation between $F_X$ and $F_\mathrm{EUV,1}$, because it is derived from the Sun alone. The Sun samples only a small fraction of the parameter space. Johnstone et al. (2021) print the constant of their Eq. 21 as $-0.341$. Their Eq. 22 has the factor $0.924 = 10^{-0.0341}$, so Eq. 21 above shows $-0.0341$, the constant that the code uses. The slope $0.920$ of Eq. 21 gives the exponent $0.920 - 1 = -0.080$, which is the exponent that the code uses. Implementation: `physicalmodel._EUV2`.

### Total EUV

$$L_\mathrm{EUV} = L_\mathrm{EUV,1} + L_\mathrm{EUV,2}, \qquad F_\mathrm{EUV} = F_\mathrm{EUV,1} + F_\mathrm{EUV,2}$$

Implementation: `physicalmodel._EUV`.

---

## 4. Ly-$\alpha$ emission

The Ly-$\alpha$ line at 121.6 nm is formed in the transition region and upper chromosphere (Avrett & Loeser 2008[^cite-avrett2008]) and is often more luminous than the entire X-ray and EUV combined. Although most of the line is absorbed by the ISM, reconstructions of the intrinsic line flux are available for a large number of stars (Wood et al. 2005[^cite-wood2005]).

The Ly-$\alpha$ surface flux is related to $F_X$ following Wood et al. (2005)[^cite-wood2005] and Linsky et al. (2013)[^cite-linsky2013]. When expressed in surface fluxes (rather than luminosities or 1 AU fluxes), the relation becomes mass-independent (Johnstone et al. 2021[^cite-johnstone2021], Eq. 23):

$$\log F_\mathrm{Ly\alpha} = 3.97 + 0.375\,\log F_X \tag{23}$$

which gives

$$\frac{F_\mathrm{Ly\alpha}}{F_X} = 9.33 \times 10^3\,F_X^{-0.625} \tag{24}$$

where both fluxes are in erg s$^{-1}$ cm$^{-2}$. In linear form, Eq. 23 reads $F_\mathrm{Ly\alpha} = 10^{3.97}\,F_X^{0.375}$; dividing by $F_X$ gives Eq. 24, with the factor $10^{3.97} = 9.33 \times 10^3$ and the exponent $0.375 - 1 = -0.625$. Johnstone et al. (2021) print their Eq. 24 as $1.96 \times 10^4\,F_X^{-0.681}$, which does not follow from their Eq. 23; the code uses Eq. 23. Implementation: `physicalmodel._Lymanalpha`.

---

## 5. Habitable zone fluxes

$F_X$, $F_\mathrm{EUV,1}$, $F_\mathrm{EUV,2}$, $F_\mathrm{EUV}$, and $F_\mathrm{Ly\alpha}$ are all also computed at the habitable zone distance (`FxHZ`, `Feuv1HZ`, `Feuv2HZ`, `FeuvHZ`, `FlyHZ`) and stored on every evolutionary track. The habitable zone distance is defined as half-way between the moist and maximum greenhouse limits, calculated at 5 Gyr stellar properties. See [Habitable Zone](habitablezone.md) for details.

---

[^cite-johnstone2021]: C. P. Johnstone, M. Bartel, M. Güdel, *[The active lives of stars: A complete description of the rotation and XUV evolution of F, G, K, and M dwarfs](https://doi.org/10.1051/0004-6361/202038407)*, Astronomy & Astrophysics, 649, A96, 2021. [SciX](https://scixplorer.org/abs/2021A%26A...649A..96J/abstract).

[^cite-wright2011]: N. J. Wright, J. J. Drake, E. E. Mamajek, G. W. Henry, *[The Stellar-activity-Rotation Relationship and the Evolution of Stellar Dynamos](https://doi.org/10.1088/0004-637X/743/1/48)*, The Astrophysical Journal, 743, 48, 2011. [SciX](https://scixplorer.org/abs/2011ApJ...743...48W/abstract).

[^cite-spada2013]: F. Spada, P. Demarque, Y.-C. Kim, A. Sills, *[The Radius Discrepancy in Low-mass Stars: Single versus Binaries](https://doi.org/10.1088/0004-637X/776/2/87)*, The Astrophysical Journal, 776, 87, 2013. [SciX](https://scixplorer.org/abs/2013ApJ...776...87S/abstract).

[^cite-reinhold2020]: T. Reinhold, A. I. Shapiro, S. K. Solanki, B. T. Montet, N. A. Krivova, R. H. Cameron, E. M. Amazo-Gómez, *[The Sun is less active than other solar-like stars](https://doi.org/10.1126/science.aay3821)*, Science, 368, 518-521, 2020. [SciX](https://scixplorer.org/abs/2020Sci...368..518R/abstract).

[^cite-johnstone2015]: C. P. Johnstone, M. Güdel, *[The coronal temperatures of low-mass main-sequence stars](https://doi.org/10.1051/0004-6361/201425283)*, Astronomy & Astrophysics, 578, A129, 2015. [SciX](https://scixplorer.org/abs/2015A%26A...578A.129J/abstract).

[^cite-craig1997]: N. Craig, M. Abbott, D. Finley, H. Jessop, S. B. Howell, M. Mathioudakis, J. Sommers, J. V. Vallerga, R. F. Malina, *[The Extreme Ultraviolet Explorer Stellar Spectral Atlas](https://doi.org/10.1086/313052)*, The Astrophysical Journal Supplement Series, 113, 131-193, 1997. [SciX](https://scixplorer.org/abs/1997ApJS..113..131C/abstract).

[^cite-avrett2008]: E. H. Avrett, R. Loeser, *[Models of the Solar Chromosphere and Transition Region from SUMER and HRTS Observations: Formation of the Extreme-Ultraviolet Spectrum of Hydrogen, Carbon, and Oxygen](https://doi.org/10.1086/523671)*, The Astrophysical Journal Supplement Series, 175, 229-276, 2008. [SciX](https://scixplorer.org/abs/2008ApJS..175..229A/abstract).

[^cite-wood2005]: B. E. Wood, S. Redfield, J. L. Linsky, H.-R. Müller, G. P. Zank, *[Stellar Lyα Emission Lines in the Hubble Space Telescope Archive: Intrinsic Line Fluxes and Absorption from the Heliosphere and Astrospheres](https://doi.org/10.1086/430523)*, The Astrophysical Journal Supplement Series, 159, 118-140, 2005. [SciX](https://scixplorer.org/abs/2005ApJS..159..118W/abstract).

[^cite-linsky2013]: J. L. Linsky, K. France, T. Ayres, *[Computing Intrinsic Lyα Fluxes of F5 V to M5 V Stars](https://doi.org/10.1088/0004-637X/766/2/69)*, The Astrophysical Journal, 766, 69, 2013. [SciX](https://scixplorer.org/abs/2013ApJ...766...69L/abstract).
