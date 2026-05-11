# High-energy emission

All high-energy emission is computed from the instantaneous rotation state in `physicalmodel.ExtendedQuantities`. Throughout this section, surface fluxes are evaluated at the stellar surface (in erg s$^{-1}$ cm$^{-2}$) and luminosities are in erg s$^{-1}$.

!!! note "Wavelength band definitions"
    Following Johnstone et al. (2021) [^johnstone2021]:

    - **XUV**: 0.1–92 nm
    - **X-ray**: 0.517–12.4 nm (2.4–0.1 keV)
    - **EUV** (total): 10–92 nm
    - **EUV1**: 10–36 nm
    - **EUV2**: 36–92 nm
    - **Ly-$\alpha$**: 121.6 nm

---

## 1. X-ray emission

The ratio $R_X = L_X / L_\mathrm{bol}$ is related to the Rossby number by a broken power law constrained using the sample of Wright et al. (2011) [^wright] with convective turnover times from Spada et al. (2013) [^spada]:

$$R_X = \begin{cases} C_1 \, Ro^{\beta_1} & Ro \leq Ro_\mathrm{sat} \quad \text{(saturated)} \\ C_2 \, Ro^{\beta_2} & Ro > Ro_\mathrm{sat} \quad \text{(unsaturated)} \end{cases} \tag{17}$$

The constants $C_1$ and $C_2$ are derived from the requirement that the two power laws are equal at the saturation point ($R_{X,\mathrm{sat}} = C_1 Ro_\mathrm{sat}^{\beta_1} = C_2 Ro_\mathrm{sat}^{\beta_2}$). The fitted parameters are:

| Parameter | Symbol | Value |
|---|---|---|
| Saturation Rossby number | $Ro_\mathrm{sat}$ | $0.0605$ |
| Saturation $R_X$ | $R_{X,\mathrm{sat}}$ | $5.135 \times 10^{-4}$ |
| Saturated power-law index | $\beta_1$ | $-0.135$ |
| Unsaturated power-law index | $\beta_2$ | $-1.889$ |

The $R_X$ relation is shallower in the unsaturated regime than many previous estimates, consistent with the Sun being less X-ray active than other stars with similar parameters [^reinhold]. The X-ray luminosity and surface flux then follow as:

$$L_X = R_X \cdot L_\mathrm{bol}, \qquad F_X = \frac{L_X}{4\pi R_\star^2}$$

Implementation: `physicalmodel._Xray`.

### X-ray variability

Real stellar X-ray emission varies around the average relation. The observed scatter in the $Ro$–$R_X$ distribution can be described as a log-normal centred on zero with standard deviation $\sigma = 0.359$ dex (`params['sigmaXray']`), meaning stars spend approximately 90% of their time within one standard deviation of the average [^johnstone2021]. This scatter can be sampled with `physicalmodel.XrayScatter` or `physicalmodel.XUVScatter`, which apply correlated random offsets consistently across all XUV bands.

---

## 2. Coronal temperature

Stars with higher X-ray surface fluxes have hotter coronae. The emission-measure-weighted average coronal temperature is estimated from $F_X$ following Johnstone & Güdel (2015) [^johnstone2015]:

$$\bar{T}_\mathrm{cor} = 0.11\, F_X^{0.26} \quad (\mathrm{MK}) \tag{18}$$

This relation is mass-independent when expressed in surface fluxes. Since coronae dominate emission at wavelengths below $\sim$40 nm, stars with higher $F_X$ emit a larger fraction of their XUV at shorter wavelengths. Implementation: `physicalmodel._Tcor`.

---

## 3. EUV emission

EUV emission is empirically related to $F_X$ rather than to $L_X$ or $R_X$, since $F_X$ best captures the physical state of the emitting plasma [^johnstone2015]. The relations are derived from EUVE observations of nearby F, G, K, and M stars [^craig] and solar spectra.

### EUV band 1 (10–36 nm)

Constrained from the EUVE stellar sample using the OLS Bisector method (Johnstone et al. 2021 [^johnstone2021] Eq. 19):

$$\log F_\mathrm{EUV,1} = 2.04 + 0.681\,\log F_X \tag{19}$$

which gives

$$\frac{F_\mathrm{EUV,1}}{F_X} = 110\,F_X^{-0.319} \tag{20}$$

Implementation: `physicalmodel._EUV1`.

### EUV band 2 (36–92 nm)

Constrained using solar spectra only, considering solar values with $L_X > 10^{27}$ erg s$^{-1}$ (Johnstone et al. 2021 [^johnstone2021] Eq. 21):

$$\log F_\mathrm{EUV,2} = -0.341 + 0.920\,\log F_\mathrm{EUV,1} \tag{21}$$

which gives

$$\frac{F_\mathrm{EUV,2}}{F_\mathrm{EUV,1}} = 0.924\,F_\mathrm{EUV,1}^{-0.0798} \tag{22}$$

This relation is less reliable than the $F_X$–$F_\mathrm{EUV,1}$ relation since it is derived from the Sun alone, which samples only a small fraction of the parameter space. Implementation: `physicalmodel._EUV2`.

### Total EUV

$$L_\mathrm{EUV} = L_\mathrm{EUV,1} + L_\mathrm{EUV,2}, \qquad F_\mathrm{EUV} = F_\mathrm{EUV,1} + F_\mathrm{EUV,2}$$

Implementation: `physicalmodel._EUV`.

---

## 4. Ly-$\alpha$ emission

The Ly-$\alpha$ line at 121.6 nm is formed in the transition region and upper chromosphere [^avrett] and is often more luminous than the entire X-ray and EUV combined. Although most of the line is absorbed by the ISM, reconstructions of the intrinsic line flux are available for a large number of stars [^wood2005].

The Ly-$\alpha$ surface flux is related to $F_X$ following Wood et al. (2005) [^wood2005] and Linsky et al. (2013) [^linsky]. When expressed in surface fluxes (rather than luminosities or 1 AU fluxes), the relation becomes mass-independent (Johnstone et al. 2021 [^johnstone2021] Eq. 23):

$$\log F_\mathrm{Ly\alpha} = 3.97 + 0.375\,\log F_X \tag{23}$$

which gives

$$\frac{F_\mathrm{Ly\alpha}}{F_X} = 1.96 \times 10^4\,F_X^{-0.681} \tag{24}$$

where both fluxes are in erg s$^{-1}$ cm$^{-2}$. Implementation: `physicalmodel._Lymanalpha`.

---

## 5. Habitable zone fluxes

$F_X$, $F_\mathrm{EUV,1}$, $F_\mathrm{EUV,2}$, $F_\mathrm{EUV}$, and $F_\mathrm{Ly\alpha}$ are all also computed at the habitable zone distance (`FxHZ`, `Feuv1HZ`, `Feuv2HZ`, `FeuvHZ`, `FlyHZ`) and stored on every evolutionary track. The habitable zone distance is defined as half-way between the moist and maximum greenhouse limits, calculated at 5 Gyr stellar properties. See [Habitable Zone](habitablezone.md) for details.

---

[^johnstone2021]: Johnstone, C. P., Bartel, M., & Güdel, M. (2021). The active lives of stars: a complete description of the rotation and XUV evolution of F, G, K, and M dwarfs. *Astronomy & Astrophysics, 649*, A96. https://doi.org/10.1051/0004-6361/202038407

[^wright]: Wright, N. J., Drake, J. J., Mamajek, E. E., & Henry, G. W. (2011). The stellar-activity–rotation relationship and the evolution of stellar dynamos. *The Astrophysical Journal, 743*(1), 48. https://doi.org/10.1088/0004-637X/743/1/48

[^spada]: Spada, F., Demarque, P., Kim, Y.-C., & Sills, A. (2013). The radius discrepancy in low-mass stars: single versus binaries. *The Astrophysical Journal, 776*(2), 87. https://doi.org/10.1088/0004-637X/776/2/87

[^reinhold]: Reinhold, T., Shapiro, A. I., Solanki, S. K., et al. (2020). The Sun is less active than other solar-like stars. *Science, 368*(6490), 518–521. https://doi.org/10.1126/science.aay3821

[^johnstone2015]: Johnstone, C. P., & Güdel, M. (2015). The coronal temperatures of solar-type stars. *Astronomy & Astrophysics, 578*, A129. https://doi.org/10.1051/0004-6361/201526164

[^craig]: Craig, N., Abbott, M., Finley, D., et al. (1997). The extreme ultraviolet explorer stellar spectral atlas. *The Astrophysical Journal Supplement Series, 113*(1), 131. https://doi.org/10.1086/313052

[^avrett]: Avrett, E. H., & Loeser, R. (2008). Models of the solar chromosphere and transition region from SUMER and HRTS observations. *The Astrophysical Journal Supplement Series, 175*(1), 229. https://doi.org/10.1086/523671

[^wood2005]: Wood, B. E., Redfield, S., Linsky, J. L., Müller, H.-R., & Zank, G. P. (2005). Stellar Ly-α emission lines in the Hubble Space Telescope archive. *The Astrophysical Journal Supplement Series, 159*(1), 118. https://doi.org/10.1086/430523

[^linsky]: Linsky, J. L., France, K., & Ayres, T. (2013). Computing intrinsic Ly-α fluxes of F5 V to M5 V stars. *The Astrophysical Journal, 766*(2), 69. https://doi.org/10.1088/0004-637X/766/2/69