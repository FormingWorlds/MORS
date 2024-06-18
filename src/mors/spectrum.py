"""Module for deriving stellar spectra from band-integrated fluxes"""

# Import system libraries 
import numpy as np
import os 

# Import MORS files 
import mors.constants as const
import mors.miscellaneous as misc

# Spectral bands for stellar fluxes, in nm
bands_limits = {
    "xr" : [0.517 , 12.5],      # X-ray,      defined by Mors
    "e1" : [10.0  , 32.0],      # EUV1,       defined by Mors
    "e2" : [32.0  , 92.0],      # EUV2,       defined by Mors
    "uv" : [92.0  , 400.0],     # UV,         defined by Harrison
    "pl" : [400.0 , 1.0e9],     # planckian,  defined by Harrison
    'bo' : [1.e-3 , 1.0e9]      # bolometric, all wavelengths
}

bands_ascending = ["xr","e1","e2","uv","pl"]

def WhichBand(wl:float):
    """Determine which band(s) this wavelength is inside of
    
    Parameters
    ----------
        wl : float
            Wavelength to query [nm]
    
    Returns 
    ----------
        bands : list | None
            List of band names (strings) which this band is inside of. Bands 
            can overlap, so this list may have a length greater than one.     
            If `wl` is outside all bandpasses, then this value is None.   
    
    """

    # Find band, returning when found 
    bands = []
    for b in bands_ascending:
        if bands_limits[b][0] <= wl < bands_limits[b][1]:
            bands.append(b)
    
    # Not found...
    if len(bands) == 0:
        return None 
    
    # Else...
    return bands

class Spectrum():

    def __init__(self):

        # Flags
        self.loaded = False 

        # Arrays (scaled to 1 AU)
        self.nbins = 0      # Number of bins 
        self.wl = []        # Wavelength bins [nm]
        self.fl = []        # Flux bins [erg s-1 cm-2 nm-1]
        self.binwidth = []  # Width of wavelength bins [nm]

        # Extensions
        self.ext_long   = -1 # Index where Planck function extension starts
        self.ext_short  = -1 # Index where shortwave extension starts

        # Integrated fluxes for each band [erg s-1 cm-2]
        self.fl_integ = {}
        for b in bands_limits.keys():
            self.fl_integ[b] = 0.0


    def CalcBandFluxes(self):
        """Calculate integrated fluxes for each band.

        Integrated fluxes will have units of [erg s-1 cm-2] scaled to 1 AU.
        """

        # For each spectral band 
        idxs = []
        i_lo = 0
        for b in bands_ascending:

            # Get band indicies 
            for i in range(i_lo, self.nbins, 1):
                wb = WhichBand(self.wl[i])

                # Out of range
                if wb == None:
                    continue 

                if b in wb:
                    # In current band 
                    idxs.append(i)
                else:
                    # End of band 
                    i_lo = i
                    break 
            
            # With idxs defined, integrate over band 
            band_wl = self.wl[idxs]
            band_fl = self.fl[idxs]
            self.fl_integ[b] = np.trapz(band_fl,band_wl)

            # Reset idxs 
            # print("%s band between in interval [%.2f, %.2f] nm"%(b,self.wl[idxs[0]],self.wl[idxs[-1]]))
            idxs = []

        # For bolometric "band"
        self.fl_integ["bo"] = np.trapz(self.fl,self.wl)

        return self.fl_integ

    def LoadDirectly(self, spec_wl:np.ndarray, spec_fl:np.ndarray):
        """Store spectral data in object.

        Scaled to 1 AU. 

        Parameters
        ----------
            spec_wl : np.ndarray
                Array of wavelengths [nm] 
            spec_fl : np.ndarray
                Array of fluxes [erg s-1 cm-2 nm-1]
        """


        # Check length 
        if len(spec_wl) != len(spec_fl):
            misc._PrintErrorKill("Stellar spectrum size mismatch (%d and %d)"%(len(spec_wl), len(spec_fl)))
        if len(spec_wl) < 10:
            misc._PrintErrorKill("Stellar spectrum size too small (%d bins)"%len(spec_wl))

        # Check reversal (should be wl ascending)
        if spec_wl[4] < spec_wl[0]:
            spec_wl = spec_wl[::-1]
            spec_fl = spec_fl[::-1]

        # Replace NaN and zero values 
        for i in range(len(spec_fl)):
            if not np.isfinite(spec_fl[i]):
                spec_fl[i] = 0.0
            spec_fl[i] = max(spec_fl[i], 1e-20)

        # Calculate bin width
        binwidth_wl = spec_wl[1:] - spec_wl[0:-1]

        # Store 
        self.nbins = len(spec_wl)
        self.wl = spec_wl
        self.fl = spec_fl 
        self.binwidth = np.array(binwidth_wl, dtype=float)

        self.loaded = True

        return self 


    def LoadTSV(self, fp:str):
        """Load stellar spectrum from TSV file into memory.

        Scaled to 1 AU. File should be whitespace delimited with 
        units of [nm] and [erg s-1 cm-2 nm-1].

        Parameters
        ----------
            fp : str
                Path to file 
        """

        # Check path
        fp = os.path.abspath(fp)
        if not os.path.isfile(fp):
            misc._PrintErrorKill("Cannot find TSV file at '%s'"%fp)

        # Load file
        spec_data = np.loadtxt(fp).T
        spec_wl = spec_data[0]
        spec_fl = spec_data[1]

        # Process data 
        spec_wl = np.array(spec_wl, dtype=float)
        spec_fl = np.array(spec_fl, dtype=float)

        # Store 
        self.LoadDirectly(spec_wl, spec_fl)

        self.loaded = True 

        return self 


    def ExtendShortwave(self, wl_min:float):
        """Extend spectrum to shorter wavelengths using constant value.

        Parameters
        ----------
            wl_min : float 
                New minimum wavelength [nm]
        """

        # Already extended
        if wl_min > self.wl[0]:
            return 
        
        # Calc wavelength extension
        wl_ext = np.logspace(np.log10(wl_min), np.log10(self.wl[0]), 200)[:-1]

        # Evalulate planck function
        fl_ext = np.ones(np.shape(wl_ext)) * self.fl[0]

        # Update Spectrum object data 
        self.ext_short = len(wl_ext)
        spec_wl = np.concatenate((wl_ext,self.wl))
        spec_fl = np.concatenate((fl_ext,self.fl))

        # Store 
        self.LoadDirectly(spec_wl, spec_fl)


    def ExtendPlanck(self, Teff:float, R_star:float, wl_max:float):
        """Extend spectrum to longer wavelengths using planck function.

        Parameters
        ----------
            Teff : float 
                Effective temperature of star 
            R_star : float 
                Radius of star [m]
            wl_max : float 
                New maximum wavelength [nm]
        """


        # Already extended
        if wl_max < self.wl[-1]:
            return 
        
        # Calc wavelength extension
        wl_ext = np.logspace(np.log10(self.wl[-1]), np.log10(wl_max), 300)[1:]

        # Evalulate planck function
        fl_ext = PlanckFunction_surf(wl_ext, Teff)

        # Scale to 1 AU
        fl_ext = ScaleTo1AU(fl_ext, R_star)

        # Update Spectrum object data 
        self.ext_long = len(self.wl)
        spec_wl = np.concatenate((self.wl, wl_ext))
        spec_fl = np.concatenate((self.fl, fl_ext))

        # Store 
        self.LoadDirectly(spec_wl, spec_fl)

    
    def WriteTSV(self, fp:str):
        """Write spectrum to file(s) on disk.

        Parameters
        ----------
            fp : str
                Path to file 
        """

        fp = os.path.abspath(fp)
        X = np.array([self.wl,self.fl]).T
        header = "WL(nm)\t Flux(ergs/cm**2/s/nm)    Stellar flux (1 AU)"

        np.savetxt(fp, X, header=header,fmt='%1.4e',delimiter='\t')

        return fp


def PlanckFunction_surf(wl:np.ndarray, Teff:float):
    """Returns the planck fluxes evaluated at the wavelength array
    
    Parameters
    ----------
        wl : np.ndarray
            Wavelength array [nm]
        Teff : float
            Effective temperature of the object

    Returns
    ----------
        yp : float
            Flux at stellar surface [erg s-1 cm-2 nm-1]
    """

    yp = np.zeros(np.shape(wl))
    for i,x in enumerate(wl):
        lam = x * 1.0e-9  # nm -> m

        # Calculate planck function value [W m-2 sr-1 m-1]
        # http://spiff.rit.edu/classes/phys317/lectures/planck.html
        yp[i] = 2.0 * const.h_SI * const.c_SI**2.0 / lam**5.0   *   1.0 / ( np.exp(const.h_SI * const.c_SI / (lam * const.k_SI * Teff)) - 1.0)

        # Integrate solid angle (hemisphere), convert units
        yp[i] = yp[i] * np.pi * 1.0e-9 # [W m-2 nm-1]
        yp[i] = yp[i] * 1000.0 # [erg s-1 cm-2 nm-1]

    return yp


def ScaleToSurf(fl:np.ndarray, R_star:float):
    """Scale spectrum from 1 AU to stellar surface
    
    Parameters
    ----------
        fl : np.ndarray
            Spectrum at 1 AU
        R_star : float
            Star radius in [m]

    Returns
    ----------
        fl_surf : np.ndarray
            Flux at stellar surface (same units as `fl`)
    """

    return fl * (const.AU_SI/R_star)**2


def ScaleTo1AU(fl:np.ndarray, R_star:float):
    """Scale spectrum from stellar surface to 1AU
    
    Parameters
    ----------
        fl : np.ndarray
            Spectrum at surface
        R_star : float
            Star radius in [m]

    Returns
    ----------
        fl_1AU : np.ndarray
            Flux at 1 AU (same units as `fl`)
    """

    return fl * (R_star/const.AU_SI)**2

