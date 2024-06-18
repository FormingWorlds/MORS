"""Module for historical spectral synthesis"""

# Import system libraries 
import numpy as np
from copy import deepcopy

# Import MORS files 
import mors.spectrum as spec
import mors.constants as const
from mors.star import  Percentile
from mors.stellarevo import Value, Lbol
from mors.physicalmodel import Lxuv


def GetProperties(Mstar:float, pctle:float, age:float):
    """Calculate properties of star at a given age
    
    Parameters 
    ----------
        Mstar : float 
            Mass of star [M_sun]
        pctle : float 
            Rotation percentile 
        age : float 
            Stellar age  [Myr] 

    Returns 
    ----------
        out : dict
            Dictionary of radius [m], Teff [K], and band fluxes at 1 AU [erg s-1 cm-2]
    """

    # Get star radius [m]
    Rstar = Value(Mstar, age, 'Rstar') * const.Rsun * 1.0e-2

    # Get star temperature [K]
    Tstar = Value(Mstar, age, 'Teff')

    # Get rotation rate [Omega_sun]
    Omega = Percentile(Mstar=Mstar, percentile=pctle)

    # Get luminosities and fluxes 
    Ldict = Lxuv(Mstar=Mstar, Age=age, Omega=Omega)

    # Output 
    out = {
        "mass"   : Mstar,      # units of M_sun 
        "pctle"  : pctle,
        "age"    : age,        # units of Myr
        "radius" : Rstar,
        "Teff"   : Tstar,
    }

    # Fluxes scaled to 1 AU (erg s-1 cm-2)
    area = (4.0 * const.Pi * const.AU * const.AU)

    out["F_bo"] = Lbol(Mstar,age) * const.LbolSun / area  
    out["F_xr"] = Ldict["Lx"] / area 
    out["F_e1"] = Ldict["Leuv1"] / area 
    out["F_e2"] = Ldict["Leuv2"] / area 

    # Get flux from Planckian band 
    wl_pl = np.logspace(np.log10(spec.bands_limits["pl"][0]), np.log10(spec.bands_limits["pl"][1]), 1000)
    fl_pl = spec.PlanckFunction_surf(wl_pl, Tstar)
    fl_pl = spec.ScaleTo1AU(fl_pl, Rstar)
    out["F_pl"] = np.trapz(fl_pl, wl_pl)

    # Get flux of UV band from remainder 
    out["F_uv"] = out["F_bo"] - out["F_xr"] - out["F_e1"] - out["F_e2"] - out["F_pl"]

    print(out)

    return out 


def CalcBandScales(modern_dict:dict, historical_age:float):
    """Get band scale factors for historical spectrum

    Parameters 
    ----------
        modern_dict : dict 
            Dictionary output of `GetProperties` call for modern spectrum
        historical_age : float 
            Stellar age at which to get corresponding scale factors

    Returns 
    ----------
        Q_dict : dict
            Dictionary of band scale factors
    """

    # Get properties 
    historical = GetProperties(modern_dict["mass"], modern_dict["pctle"], historical_age)

    # Get scale factors 
    Q_dict = {}
    for key in spec.bands_limits.keys():
        Q_dict["Q_"+key] = historical["F_"+key]/modern_dict["F_"+key]

    return Q_dict

def GetScaledSpectrum(modern_spec:spec.Spectrum, Q_dict:dict):
    """Scale a stellar spectrum according to band scale factors.

    Returns a new Spectrum object containing the historical fluxes.

    Parameters 
    ----------
        modern_spec : Spectrum object
            Spectrum object containing data for a modern fluxes
        Q_dict : float 
            Dictionary of band scale factors

    Returns 
    ----------
        historical_spec : Spectrum object 
            Spectrum object containing data for historical fluxes
    """

    # Get modern wl, fl
    spec_fl = deepcopy(modern_spec.fl)
    spec_wl = deepcopy(modern_spec.wl)

    # Get band indicies 
    for i in range(len(spec_wl)):
        b = spec.WhichBand(spec_wl[i])
        if b == None:
            continue 
        spec_fl[i] *= Q_dict["Q_"+b]

    # Make new spectrum object
    historical_spec = spec.Spectrum()
    historical_spec.LoadDirectly(spec_wl, spec_fl)

    return historical_spec

    


