# mors.constants

::: mors.constants
    options:
      members: false
      inherited_members: false
      show_source: true

All constants are defined in `constants.py` in CGS units unless otherwise noted.

## Time

| Name | Value | Units |
|---|---|---|
| `sec` | 1.0 | s |
| `minute` | 60.0 | s |
| `hour` | 3600.0 | s |
| `day` | 86400.0 | s |
| `year` | 3.1558 × 10⁷ | s |
| `Myr` | 3.1558 × 10¹³ | s |
| `Gyr` | 3.1558 × 10¹⁶ | s |

## Distance (CGS)

| Name | Value | Units |
|---|---|---|
| `A` | 1.0 × 10⁻⁸ | cm (Ångström) |
| `nm` | 1.0 × 10⁻⁷ | cm |
| `micron` | 1.0 × 10⁻⁴ | cm |
| `mm` | 0.1 | cm |
| `cm` | 1.0 | cm |
| `m` | 1.0 × 10³ | cm |
| `km` | 1.0 × 10⁵ | cm |
| `Rearth` | 6.371 × 10⁸ | cm |
| `Rjup` | 6.9911 × 10⁹ | cm |
| `Rsun` | 6.957 × 10¹⁰ | cm |
| `AU` | 1.496 × 10¹³ | cm |
| `AU_SI` | 1.495979 × 10¹¹ | m |

## Mass (CGS)

| Name | Value | Units |
|---|---|---|
| `g` | 1.0 | g |
| `kg` | 1.0 × 10³ | g |
| `Mearth` | 5.972 × 10²⁷ | g |
| `Mjup` | 1.89813 × 10³⁰ | g |
| `Msun` | 1.99 × 10³³ | g |
| `Mproton` | 1.6726219 × 10⁻²⁴ | g |
| `Melec` | 9.10938356 × 10⁻²⁸ | g |
| `Msunyr_` | $\dot{M}_\odot / \mathrm{yr}$ | g s⁻¹ |

## Solar quantities

| Name | Value | Units | Description |
|---|---|---|---|
| `LbolSun` | 3.828 × 10³³ | erg s⁻¹ | Solar bolometric luminosity |
| `LbolSun_SI` | 3.828 × 10²⁶ | W | Solar bolometric luminosity (SI) |
| `AgeSun` | 4567.0 | Myr | Solar age |
| `OmegaSun` | 2.67 × 10⁻⁶ | rad s⁻¹ | Solar rotation rate |
| `ProtSun` | $2\pi / \Omega_\odot$ | days | Solar rotation period |
| `tauConvSun` | 28.436 | days | Solar convective turnover time (Spada et al. 2013) |
| `RoSun` | $P_{\mathrm{rot},\odot} / \tau_\odot$ | — | Solar Rossby number |

## Physical constants

| Name | Value | Units | Description |
|---|---|---|---|
| `GravConstant` | 6.674 × 10⁻⁸ | cm³ g⁻¹ s⁻² | Gravitational constant |
| `kB` | 1.38064852 × 10⁻¹⁶ | erg K⁻¹ | Boltzmann constant |
| `Pi` | 3.14159265359 | — | π |
| `h_SI` | 6.626075540 × 10⁻³⁴ | J s | Planck constant |
| `c_SI` | 2.99792458 × 10⁸ | m s⁻¹ | Speed of light |
| `k_SI` | 1.38065812 × 10⁻²³ | J K⁻¹ | Boltzmann constant (SI) |