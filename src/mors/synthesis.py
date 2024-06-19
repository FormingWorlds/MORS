"""Module for historical spectral synthesis"""

# Import system libraries 
import numpy as np
from copy import deepcopy
from scipy.optimize import minimize

# Import MORS files 
import mors.spectrum as spec
import mors.constants as const
import mors.miscellaneous as misc
from mors.star import  Percentile
from mors.stellarevo import Value, Lbol
from mors.physicalmodel import Lxuv


def GetProperties(Mstar:float, pctle:float, age:float):
    """Calculate properties of star for a given rotation percentile and  age
    
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

    # Luminosities (erg s-1)
    out["L_bo"] = Lbol(Mstar,age) * const.LbolSun   
    out["L_xr"] = Ldict["Lx"] 
    out["L_e1"] = Ldict["Leuv1"] 
    out["L_e2"] = Ldict["Leuv2"] 

    # Fluxes at 1 AU
    area = (4.0 * const.Pi * const.AU * const.AU)
    for k in ["bo","xr","e1","e2"]:
        out["F_"+k] = out["L_"+k]/area

    # Get flux from Planckian band 
    wl_pl = np.logspace(np.log10(spec.bands_limits["pl"][0]), np.log10(spec.bands_limits["pl"][1]), 1000)
    fl_pl = spec.PlanckFunction_surf(wl_pl, Tstar)
    fl_pl = spec.ScaleTo1AU(fl_pl, Rstar)
    out["F_pl"] = np.trapz(fl_pl, wl_pl)
    out["L_pl"] = out["F_pl"] * area

    # Get flux of UV band from remainder 
    out["F_uv"] = out["F_bo"] - out["F_xr"] - out["F_e1"] - out["F_e2"] - out["F_pl"]
    out["L_uv"] = out["F_uv"] * area

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

def CalcScaledSpectrumFromProps(modern_spec:spec.Spectrum, modern_dict:dict, historical_age:float):
    """Scale a stellar spectrum according to stellar properties.

    Returns a new Spectrum object containing the historical fluxes.

    Parameters 
    ----------
        modern_spec : Spectrum object
            Spectrum object containing data for a modern fluxes
        modern_dict : dict 
            Dictionary output of `GetProperties` call for modern spectrum
        historical_age : float 
            Stellar age at which to get corresponding scale factors

    Returns 
    ----------
        historical_spec : Spectrum object 
            Spectrum object containing data for historical fluxes
    """

    # Get scale factors relative to modern spectrum
    Q_dict = CalcBandScales(modern_dict, historical_age)

    # Get modern wl, fl
    spec_fl = deepcopy(modern_spec.fl)
    spec_wl = deepcopy(modern_spec.wl)

    # Get band indicies 
    for i in range(len(spec_wl)):
        b = spec.WhichBand(spec_wl[i])
        if b == None:
            continue 
        spec_fl[i] *= Q_dict["Q_"+b[0]]

    # Make new spectrum object
    historical_spec = spec.Spectrum()
    historical_spec.LoadDirectly(spec_wl, spec_fl)

    return historical_spec

    
def FitModernProperties(modern_spec:spec.Spectrum, Mstar:float, age:float=-1):
    """Estimate rotation percentile and (optionally) age from modern spectrum.

    Parameters 
    ----------
        modern_spec : Spectrum object
            Spectrum object containing data for a modern fluxes
        Mstar : float 
            Stellar mass [M_sun]
        age : float 
            Optional guess for current age. Will be estimated if not provided.

    Returns 
    ----------
        best_pctle : float 
            Best estimate of rotation percentile 
        best_age : float 
            Best estimate of star's age (equal to `age` if `age` is provided)
    """

    # Integrated fluxes
    modern_spec.CalcBandFluxes()

    fit_age = bool(age>0)

    # Objective function
    def _fev(x_arr:tuple):

        this_pctle = x_arr[0]
        if fit_age:
            this_age = x_arr[1]
        else:
            this_age = age

        this_age = max(min(this_age, 11000), 0.4)

        props = GetProperties(Mstar, this_pctle, this_age)

        resid = 0.0
        for k in ["xr","e1","e2","uv"]:
            lim = spec.bands_limits[k]
            wid = lim[1]-lim[0]
            resid += (props["F_"+k]/wid - modern_spec.fl_integ[k]/wid)**2
        
        return np.sqrt(resid)
    
    # Initial guess 
    if fit_age:
        x0 = [1.0, 1000.0]
    else:
        x0 = [1.0]

    # Find best params
    result = minimize(_fev, x0, method='Nelder-Mead')

    # Check 
    if not result.success:
        misc._PrintError("Could not fit stellar properties to modern spectrum")

    # Result 
    best_pctle = result.x[0]
    if fit_age:
        best_age = result.x[1]
    else:
        best_age = age

    # Return
    return best_pctle, best_age
    

