# Rotational Evolution Model

## 1. Two-zone structure

For stars with $M_\star \geq 0.35\,M_\odot$, the star is divided into a **radiative core** and a **convective envelope**, each treated as a solid-body rotator with its own angular velocity ($\Omega_\mathrm{core}$, $\Omega_\mathrm{env}$). Their evolution is governed by two coupled ODEs (`physicalmodel.py: RotationQuantities`):

$$\frac{d\Omega_\mathrm{core}}{dt} = \frac{1}{I_\mathrm{core}} \left( -\tau_\mathrm{ce} - \tau_\mathrm{cg} - \Omega_\mathrm{core} \frac{dI_\mathrm{core}}{dt} \right) \tag{1}$$

$$\frac{d\Omega_\mathrm{env}}{dt} = \frac{1}{I_\mathrm{env}} \left( \tau_w + \tau_\mathrm{ce} + \tau_\mathrm{cg} + \tau_\mathrm{dl} - \Omega_\mathrm{env} \frac{dI_\mathrm{env}}{dt} \right) \tag{2}$$

where $\Omega_\mathrm{core}$ and $\Omega_\mathrm{env}$ are the core and envelope angular velocities, $I_\mathrm{core}$ and $I_\mathrm{env}$ are their respective moments of inertia, $\tau_w$ is the stellar wind spin-down torque, $\tau_\mathrm{ce}$ is the core–envelope coupling torque, $\tau_\mathrm{cg}$ is the core-growth torque, and $\tau_\mathrm{dl}$ is the disk-locking torque.

For fully convective stars ($M_\star \lesssim 0.35\,M_\odot$), the distinction between core and envelope is not considered and the star rotates entirely as a solid body:

$$\frac{d\Omega_\star}{dt} = \frac{1}{I_\star}\left(\tau_w + \tau_\mathrm{dl} - \Omega_\star \frac{dI_\star}{dt}\right) \tag{3}$$

where $\Omega_\star$ and $I_\star$ are the star's rotation rate and moment of inertia. The threshold is controlled by the parameters `MstarThresholdCE` ($0.35\,M_\odot$) and `IcoreThresholdCE` ($I_\mathrm{core}/I_\mathrm{total} < 0.01$).

---

## 2. Torques

### Wind spin-down torque $\tau_w$

The wind torque follows [Matt et al. (2012)](https://doi.org/10.1088/2041-8205/754/2/L26). We calculate $\tau_w = -K_\tau \tau'$, where $K_\tau = 11$ (`params['Kwind']`) is a parameter used to reproduce the Skumanich spin-down of the modern Sun, and $\tau'$ is given by:

$$\tau' = K_1^2 B_\mathrm{dip}^{4m} \dot{M}_\star^{1-2m} R_\star^{4m+2} \frac{\Omega_\mathrm{env}}{(K_2^2 v_\mathrm{esc}^2 + \Omega_\mathrm{env}^2 R_\star^2)^m} \tag{4,5}$$

with $K_1 = 1.3$, $K_2 = 0.0506$, $m = 0.2177$. Here $B_\mathrm{dip}$ is the dipole field strength, $\dot{M}_\star$ is the wind mass loss rate, $R_\star$ and $M_\star$ are the stellar radius and mass, and $v_\mathrm{esc} = \sqrt{2GM_\star/R_\star}$ is the surface escape velocity (`physicalmodel._vEsc`).

#### Dipole field strength $B_\mathrm{dip}$

The large-scale dipole field scales with Rossby number following [Vidotto et al. (2014)](https://doi.org/10.1093/mnras/stu728):

$$B_\mathrm{dip} = \begin{cases} B_{\mathrm{dip},\odot} \left(\dfrac{Ro_\mathrm{sat}}{Ro_\odot}\right)^{-1.32} & \text{if } Ro \leq Ro_\mathrm{sat} \\[8pt] B_{\mathrm{dip},\odot} \left(\dfrac{Ro}{Ro_\odot}\right)^{-1.32} & \text{otherwise} \end{cases} \tag{6}$$

where $Ro_\odot$ and $B_{\mathrm{dip},\odot}$ are the Rossby number and dipole field strength of the modern Sun. The solar dipole field strength is $B_{\mathrm{dip},\odot} = 1.35\,\mathrm{G}$ (`params['BdipSun']`) and the saturation Rossby number is $Ro_\mathrm{sat} = 0.0605$ (`params['RoSatBdip']`).

#### Wind mass loss rate $\dot{M}_\star$

The mass loss rate scales with Rossby number, stellar radius, and stellar mass (`physicalmodel._Mdot`):

$$\dot{M}_\star = \begin{cases} f\,\dot{M}_\odot \left(\dfrac{R_\star}{R_\odot}\right)^2 \left(\dfrac{Ro_\mathrm{sat}}{Ro_\odot}\right)^{a_w} \left(\dfrac{M_\star}{M_\odot}\right)^{b_w} & \text{if } Ro \leq Ro_\mathrm{sat} \\[8pt] f\,\dot{M}_\odot \left(\dfrac{R_\star}{R_\odot}\right)^2 \left(\dfrac{Ro}{Ro_\odot}\right)^{a_w} \left(\dfrac{M_\star}{M_\odot}\right)^{b_w} & \text{otherwise} \end{cases} \tag{7}$$

where $\dot{M}_\odot = 1.4 \times 10^{-14}\,M_\odot\,\mathrm{yr}^{-1}$ is the current solar mass loss rate, $a_w = -1.7591$ and $b_w = 0.6494$ are fit parameters (`params['aMdot']`, `params['bMdot']`), and $f$ is the magnetocentrifugal factor described below.

#### Magnetocentrifugal enhancement $f$

For very rapidly rotating stars approaching breakup, wind mass loss is enhanced by magnetocentrifugal effects (`physicalmodel.MdotFactor`):

$$f(\Omega_\mathrm{env}) = \begin{cases} 1 & x \leq 0.1 \\ 0.93\,(1.01 - x)^{-0.43}\,e^{0.31 x^{7.5}} & \text{otherwise} \end{cases} \tag{8}$$

where $x = \Omega_\mathrm{env}/\Omega_\mathrm{break}$. Stars reach breakup when the Keplerian co-rotation radius equals the stellar equatorial radius. Taking the polar radius $R_p = R_\star$, this gives:

$$\Omega_\mathrm{break} = \left(\frac{2}{3}\right)^{3/2} \left(\frac{G M_\star}{R_\star^3}\right)^{1/2} \tag{9}$$

implemented in `physicalmodel.OmegaBreak`. The evolution of $\Omega_\mathrm{break}$ depends on mass and age through $R_\star$ and $M_\star$ from the stellar evolution models.

---

### Core–envelope coupling torque $\tau_\mathrm{ce}$

Angular momentum is exchanged between core and envelope on a coupling timescale $t_\mathrm{ce}$ (`physicalmodel._torqueCoreEnvelope`). We define this torque such that positive values imply angular momentum transfer from the core to the envelope:

$$\tau_\mathrm{ce} = \frac{\Delta J}{t_\mathrm{ce}} \tag{10}$$

where $\Delta J$ is the angular momentum that must be transferred to bring both components to the same rotation rate:

$$\Delta J = \frac{I_\mathrm{env}\,I_\mathrm{core}}{I_\mathrm{env} + I_\mathrm{core}}\,(\Omega_\mathrm{core} - \Omega_\mathrm{env}) \tag{11}$$

which implies $\Delta J = 0$ when $\Omega_\mathrm{core} = \Omega_\mathrm{env}$. The coupling timescale has a power-law dependence on differential rotation and stellar mass:

$$t_\mathrm{ce} = a_\mathrm{ce}\,|\Omega_\mathrm{env} - \Omega_\mathrm{core}|^{b_\mathrm{ce}} \left(\frac{M_\star}{M_\odot}\right)^{c_\mathrm{ce}} \tag{12}$$

with $a_\mathrm{ce} = 25.6015$, $b_\mathrm{ce} = -3.4817 \times 10^{-2}$, $c_\mathrm{ce} = -0.4476$ (in Myr, with angular velocities in units of $\Omega_\odot$).

---

### Core-growth torque $\tau_\mathrm{cg}$

As the radiative core grows during the pre-main sequence, material from the envelope becomes part of the core and carries its angular momentum with it (`physicalmodel._torqueCoreGrowth`). Assuming a positive value corresponds to angular momentum transport from the envelope to the core:

$$\tau_\mathrm{cg} = -\frac{2}{3} R_\mathrm{core}^2\,\Omega_\mathrm{env}\,\frac{dM_\mathrm{core}}{dt} \tag{13}$$

where $M_\mathrm{core}$ and $R_\mathrm{core}$ are the core mass and radius. This torque is valid when $dM_\mathrm{core}/dt > 0$; when $dM_\mathrm{core}/dt < 0$, $\Omega_\mathrm{env}$ is replaced by $\Omega_\mathrm{core}$.

---

### Disk-locking torque $\tau_\mathrm{dl}$

During the early pre-main-sequence phase, stars still possess circumstellar gas disks and do not spin up despite contracting. A disk-locking torque acting on the envelope cancels all other terms in Eq. (2) to keep the surface rotation constant (`physicalmodel._torqueDiskLocking`):

$$\tau_\mathrm{dl} = \begin{cases} -\tau_w - \tau_\mathrm{ce} - \tau_\mathrm{cg} + \Omega_\mathrm{env}\,\dfrac{dI_\mathrm{env}}{dt} & \text{if } t \leq t_\mathrm{disk} \\ 0 & \text{otherwise} \end{cases} \tag{14}$$

The disk-locking timescale follows:

$$t_\mathrm{disk} = 13.5 \left(\frac{\Omega_0}{\Omega_\odot}\right)^{-0.5}\,\mathrm{Myr} \tag{15}$$

where $\Omega_0$ is the initial (1 Myr) rotation rate. The inverse dependence means fast rotators lose their disks earlier, consistent with observed rotation distributions in young clusters. The timescale is capped at a maximum of 15 Myr (`params['ageDLmax']`) to avoid unreasonably large values for slow rotators.

---

### Moment-of-inertia change torque $\tau_\mathrm{mom}$

Changes in the moments of inertia due to stellar contraction and core growth contribute an effective torque (`physicalmodel._torqueMoment`). This is not a physical torque in the traditional sense but encapsulates angular momentum conservation as the stellar structure evolves:

$$\tau_{\mathrm{env,mom}} = -\frac{dI_\mathrm{env}}{dt}\,\Omega_\mathrm{env}, \qquad \tau_{\mathrm{core,mom}} = -\frac{dI_\mathrm{core}}{dt}\,\Omega_\mathrm{core}$$

When core–envelope decoupling is inactive, the total moment of inertia is used instead: $\tau_{\mathrm{env,mom}} = -(dI_\mathrm{total}/dt)\,\Omega_\mathrm{env}$.

---

## 3. Numerical Integration

Rotational evolution is performed by `rotevo.EvolveRotation`, which integrates the two-component ODE system from `AgeMin` (default 1 Myr) to `AgeMax` (end of main sequence for the given mass). Five solvers are available, selected by `params['TimeIntegrationMethod']`:

| Method | Description |
|---|---|
| `ForwardEuler` | First-order explicit (for testing only) |
| `RungeKutta4` | Classical 4th-order Runge–Kutta |
| `RungeKuttaFehlberg` | Adaptive-step RKF45 |
| `Rosenbrock` | Adaptive-step stiff solver (RODAS3) |
| `RosenbrockFixed` | Fixed-step Rosenbrock (default) |

The default **RosenbrockFixed** solver uses a timestep that grows with age:

$$\Delta t = 0.1 \times \mathrm{Age}^{0.75} \quad \text{(capped at } \Delta t_\mathrm{max} = 50\,\mathrm{Myr)}$$

This resolves the rapid early evolution without the overhead of adaptive step-size control. The Jacobian $d(\dot{\Omega})/d\Omega$ is computed by finite differences (`rotevo._JacobianRB`) and a 4-stage RODAS3 Rosenbrock scheme is applied (`rotevo._kCoeffRB`).

### Fitting an initial rotation rate

When the user specifies a known surface rotation rate at a known age (rather than an initial rotation rate), `rotevo.FitRotation` performs a bisection search over initial rotation rates $\Omega_0 \in [0.1,\,50]\,\Omega_\odot$ to find the evolutionary track that passes through the observed value, to within a tolerance of $10^{-5}$ and a maximum of 1000 bisection steps.