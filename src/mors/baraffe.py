"""Module for loading and interpolating Baraffe tracks data.
Original tracks data can be found on the website 
http://perso.ens-lyon.fr/isabelle.baraffe/BHAC15dir/BHAC15_tracks+structure"""
import numpy as np
import os
from scipy.interpolate import PchipInterpolator

import mors.constants as const

#Short cut to Baraffe tracks mass and temporal range
MassGrid = [0.010, 0.015, 0.020, 0.030, 0.040, 0.050,
            0.060, 0.070, 0.072, 0.075, 0.080, 0.090,
            0.100, 0.110, 0.130, 0.150, 0.170, 0.200,
            0.300, 0.400, 0.500, 0.600, 0.700, 0.800,
            0.900, 1.000, 1.100, 1.200, 1.300, 1.400 ]
tminGrid = [ 5.695210, 5.693523, 5.689884, 5.695099, 5.694350, 5.694123,
             5.694808, 5.692913, 5.694756, 5.694352, 5.694252, 5.689450,
             5.703957, 5.709729, 5.702708, 5.701659, 5.693846, 5.693823,
             5.690044, 5.689995, 5.694573, 5.690793, 5.691618, 5.693354,
             5.692710, 5.693063, 5.694315, 5.693263, 5.694626, 5.692977 ]
tmaxGrid = [ 7.612341, 8.050550, 8.089757, 8.514580, 8.851534, 9.178493,
             9.499851,10.000078, 9.999692,10.000130,10.000343, 9.999745,
             9.999914, 9.999209, 9.999428,10.000104, 9.999246, 9.999735,
            10.000004, 9.999193, 9.999099, 9.999787, 9.999811, 9.998991,
            10.000065, 9.920501, 9.789029, 9.651666, 9.538982, 9.425490 ]

fwl_data_dir = os.getenv('FWL_DATA')

class BaraffeTrack:
    """Class to hold interpolated baraffe tracks data for a given star mass

    Attributes
    ----------
    mstar : float
        Star mass
    track : dict
        Dictionary containing track data
    """

    def __init__(self, Mstar):

        self.mstar = Mstar

        #If Mstar is out of the mass range, code breaks
        if(Mstar < MassGrid[0]):
            raise Exception("Stellar mass is too low for the Baraffe tracks")
        elif(Mstar > MassGrid[29]):
            raise Exception("Stellar mass is too high for the Baraffe tracks")

        #If Mstar matches with values in the mass grid
        elif(Mstar in MassGrid):
            track = BaraffeLoadTrack(Mstar)

        #If Mstar is between two points in the mass grid, need mass interpolation
        else:
            for i in range(29):
                if not Mstar > MassGrid[i+1]:
                    #search for common temporal range
                    tmin = max(tminGrid[i],tminGrid[i+1])
                    tmax = min(tmaxGrid[i],tmaxGrid[i+1])
                    
                    #load neighbouring tracks with time interpolation on the same time grid
                    track  = BaraffeLoadTrack(MassGrid[i  ], tmin=tmin, tmax=tmax)
                    trackp = BaraffeLoadTrack(MassGrid[i+1], tmin=tmin, tmax=tmax)
                   
                    #perform linear mass interpolation for each array
                    mass_ratio=(Mstar-MassGrid[i])/(MassGrid[i+1]-MassGrid[i])
                    track['Teff' ]=(trackp['Teff' ]-track['Teff' ])*mass_ratio + track['Teff' ]
                    track['Lstar']=(trackp['Lstar']-track['Lstar'])*mass_ratio + track['Lstar']
                    track['Rstar']=(trackp['Rstar']-track['Rstar'])*mass_ratio + track['Rstar']

                    break

        self.track = track
        self.tmin = track['t'][0]
        self.tmax = track['t'][-1]

        return

    def BaraffeLuminosity(self, tstar):
        """Calculates the star luminosity at a given time.

        Parameters
        ----------
            tstar : float
                Star's age

        Returns
        ----------
            Lstar : float
                Luminosity Flux in units of solar luminosity
        """

        # Get time and check that it is in range
        if (tstar < self.tmin):
            print("Star age too low! Clipping to %.1g Myr" % int(self.tmin*1.e-6))
            tstar = self.tmin
        if (tstar > self.tmax):
            print("Star age too high! Clipping to %.1g Myr" % int(self.tmax*1.e-6))
            tstar = self.tmax

        # Find closest row in track
        iclose = (np.abs(self.track['t'] - tstar)).argmin()

        # Get data from track
        Lstar = self.track['Lstar'][iclose]

        return Lstar

    def BaraffeSolarConstant(self, tstar, mean_distance):
        """Calculates the bolometric flux of the star at a given time.
        Flux is scaled to the star-planet distance.

        Parameters
        ----------
            tstar : float
                Star's age
            mean_distance : float
                Star-planet distance

        Returns
        ----------
            inst : float
                Flux at planet's orbital separation (solar constant) in W/m^2
        """

        Lstar = self.BaraffeLuminosity(tstar)
        Lstar *= const.LbolSun_SI
        mean_distance *= const.AU_SI

        inst = Lstar / ( 4. * np.pi * mean_distance * mean_distance )

        return inst

    def BaraffeStellarRadius(self, tstar):
        """Calculates the star's radius at a time t.

        Parameters
        ----------
            tstar : float
                Star's age

        Returns
        ----------
            Rstar : float
                Radius of star in units of solar radius
        """

        # Get time and check that it is in range
        if (tstar < self.tmin):
            print("Star age too low! Clipping to %.1g Myr" % int(self.tmin*1.e-6))
            tstar = self.tmin
        if (tstar > self.tmax):
            print("Star age too high! Clipping to %.1g Myr" % int(self.tmax*1.e-6))
            tstar = self.tmax

        # Find closest row in track
        iclose = (np.abs(self.track['t'] - tstar)).argmin()

        # Get data from track
        Rstar = self.track['Rstar'][iclose]

        return Rstar

def BaraffeLoadTrack(Mstar, pre_interp = True, tmin = None, tmax = None):
    """Load a baraffe track into memory and optionally interpolate it into a fine time-grid

    Parameters
    ----------
        Mstar : float
            Star mass (in unit of solar mass)
            It assumes the value has been checked and matches with the mass grid.
        pre_interp : bool
            Pre-interpolate the tracks onto a higher resolution time-grid
        tmin : float
            Minimum value of the temporal grid
        tmax : float
            Maximum value of the temporal grid

    Returns
    ----------
        track : dict
            Dictionary containing track data
    """

    # Load data
    formatted_mass = f"{Mstar:.3f}"
    file = (fwl_data_dir +
           "/stellar_evolution_tracks/Baraffe/BHAC15-M" +
           str(formatted_mass).replace('.', 'p') +
           ".txt")
    if not os.path.isfile(file):
        raise Exception(
            "Cannot find Baraffe track file %s. "
            "Did you set the FWL_DATA environment variable? "
            "Did you run the DownloadEvolutionTracks function to get access to the Baraffe track data?"
            % file
        )

    data = np.loadtxt(file,skiprows=1).T

    # Parse data
    t =     data[1]
    Teff =  data[2]
    Lstar = data[3]
    Rstar = data[5]

    # Pre-interpolate in time if required
    if pre_interp:
        # Params for interpolation
        grid_count = 5e4
        if tmin==None: tmin = t[0]
        if tmax==None: tmax = t[-1]

        # Do interpolation
        #log.info("Interpolating stellar track onto a grid of size %d" % grid_count)
        interp_Teff =   PchipInterpolator(t,Teff)
        interp_Lstar =  PchipInterpolator(t,Lstar)
        interp_Rstar =  PchipInterpolator(t,Rstar)

        new_t = np.logspace(tmin, tmax, int(grid_count))
        new_t = np.log10(new_t)
        new_Teff =  interp_Teff(new_t)
        new_Lstar = interp_Lstar(new_t)
        new_Rstar = interp_Rstar(new_t)

        track = {
            't':        10.0**new_t,      # yr
            'Teff':     new_Teff,         # K
            'Lstar':    10.0**new_Lstar,  # L_sun
            'Rstar':    new_Rstar         # R_sun
        }
    else:
        track = {
            't':        10.0**t,      # yr
            'Teff':     Teff,         # K
            'Lstar':    10.0**Lstar,  # L_sun
            'Rstar':    Rstar         # R_sun
        }
        
    return track
