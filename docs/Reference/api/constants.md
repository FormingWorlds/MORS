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
| `sec` | $1.0$ | s |
| `minute` | $60.0$ | s |
| `hour` | $3600.0$ | s |
| `day` | $86400.0$ | s |
| `year` | $3.1558 \times 10^{7}$ | s |
| `Myr` | $3.1558 \times 10^{13}$ | s |
| `Gyr` | $3.1558 \times 10^{16}$ | s |

## Distance (CGS)

| Name | Value | Units |
|---|---|---|
| `A` | $1.0 \times 10^{-8}$ | cm (Ångström) |
| `nm` | $1.0 \times 10^{-7}$ | cm |
| `micron` | $1.0 \times 10^{-4}$ | cm |
| `mm` | $0.1$ | cm |
| `cm` | $1.0$ | cm |
| `m` | $1.0 \times 10^{3}$ | cm |
| `km` | $1.0 \times 10^{5}$ | cm |
| `Rearth` | $6.371 \times 10^{8}$ | cm |
| `Rjup` | $6.9911 \times 10^{9}$ | cm |
| `Rsun` | $6.957 \times 10^{10}$ | cm |
| `AU` | $1.496 \times 10^{13}$ | cm |
| `AU_SI` | $1.495979 \times 10^{11}$ | m |

## Mass (CGS)

| Name | Value | Units |
|---|---|---|
| `g` | $1.0$ | g |
| `kg` | $1.0 \times 10^{3}$ | g |
| `Mearth` | $5.972 \times 10^{27}$ | g |
| `Mjup` | $1.89813 \times 10^{30}$ | g |
| `Msun` | $1.99 \times 10^{33}$ | g |
| `Mproton` | $1.6726219 \times 10^{-24}$ | g |
| `Melec` | $9.10938356 \times 10^{-28}$ | g |
| `Msunyr_` | $\dot{M}_\odot\,\mathrm{yr}^{-1}$ | $\mathrm{g\,s}^{-1}$ |

## Solar quantities

| Name | Value | Units | Description |
|---|---|---|---|
| `LbolSun` | $3.828 \times 10^{33}$ | $\mathrm{erg\,s}^{-1}$ | Solar bolometric luminosity |
| `LbolSun_SI` | $3.828 \times 10^{26}$ | W | Solar bolometric luminosity (SI) |
| `AgeSun` | $4567.0$ | Myr | Solar age |
| `OmegaSun` | $2.67 \times 10^{-6}$ | $\mathrm{rad\,s}^{-1}$ | Solar rotation rate |
| `ProtSun` | $2\pi / \Omega_\odot$ | days | Solar rotation period |
| `tauConvSun` | $28.436$ | days | Solar convective turnover time (Spada et al. 2013) |
| `RoSun` | $P_{\mathrm{rot},\odot} / \tau_\odot$ | — | Solar Rossby number |

## Physical constants

| Name | Value | Units | Description |
|---|---|---|---|
| `GravConstant` | $6.674 \times 10^{-8}$ | $\mathrm{cm}^{3}\,\mathrm{g}^{-1}\,\mathrm{s}^{-2}$ | Gravitational constant |
| `kB` | $1.38064852 \times 10^{-16}$ | $\mathrm{erg\,K}^{-1}$ | Boltzmann constant |
| `Pi` | $3.14159265359$ | — | $\pi$ |
| `h_SI` | $6.626075540 \times 10^{-34}$ | $\mathrm{J\,s}$ | Planck constant |
| `c_SI` | $2.99792458 \times 10^{8}$ | $\mathrm{m\,s}^{-1}$ | Speed of light |
| `k_SI` | $1.38065812 \times 10^{-23}$ | $\mathrm{J\,K}^{-1}$ | Boltzmann constant (SI) |