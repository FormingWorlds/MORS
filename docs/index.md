![Coverage](https://gist.githubusercontent.com/lsoucasse/a25c37a328839edd00bb32d8527aec30/raw/covbadge.svg)

# MODEL FOR ROTATION OF STARS (MORS)

**This code is distributed as a python package for the purpose of the [PROTEUS framework](https://proteus-framework.org/PROTEUS/), a coupled simulation tool for the long-term evolution of atmospheres and interiors of rocky planets.
The MORS package solves specifically the stellar rotation and evolution. It is based on the [original code](https://www.aanda.org/articles/aa/pdf/2021/05/aa38407-20.pdf) and model developed by Colin P. Johnstone.**

**Original Author:** Colin P. Johnstone

This code solves the stellar rotation and XUV evolution model presented in Johnstone et al. (2021). The package can be used to calculate evolutionary tracks for stellar rotaton and X-ray, EUV, and Ly-alpha emission for stars with masses between 0.1 and 1.25 Msun and has additional functionality such as allowing the user to get basic stellar parameters such as stellar radius and luminosity as functions of mass and age using the stellar evolution models of Spada et al. (2013). When publishing results that were calculated using this code, both the Johnstone et al. (2020) paper and Spada et al. (2013) should be cited.

**NOTE:** This version contains the fix for the error in the equation converting EUV1 to EUV2.

### Contributors

| Name                    | Email address                            |
| -                       | -                                        |
| Colin P. Johnstone      | colinjohnstone@gmail.com                 |
| Laurent Soucasse        | l.soucasse@esciencecenter.nl             |
| Harrison Nicholls       | harrison.nicholls@physics.ox.ac.uk       |
| Stef Smeets             | s.smeets@esciencecenter.nl               |
| Tim Lichtenberg         | tim.lichtenberg@rug.nl                   |
| Karen Stuitje           | e.k.e.stuitje@student.rug.nl             |