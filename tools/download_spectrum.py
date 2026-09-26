#!/usr/bin/env python3

# Python script to download and convert stellar spectra from online databases
from __future__ import annotations

import sys

stars_online = {
    'muscles': [
        'gj1132',
        'gj1214',
        'gj15a',
        'gj163',
        'gj176',
        'gj436',
        'gj551',
        'gj581',
        'gj649',
        'gj667c',
        'gj674',
        'gj676a',
        'gj699',
        'gj729',
        'gj832',
        'gj832_synth',
        'gj849',
        'gj876',
        'hd40307',
        'hd85512',
        'hd97658',
        'l-980-5',
        'lhs-2686',
        'trappist-1',
        'v-eps-eri',
    ],
    'vpl': ['hd128167', 'hd114710', 'hd206860', 'hd22049'],
    'nrel': ['sun'],
}


def DownloadModernSpectrum(name, distance):
    """Get a contemporary stellar spectrum

    Scaled to 1 AU from the star. Append "#lowres" to star name to use
    lower resolution spectrum, if that's what you want.

    Parameters
    ----------
        name : str
            Name of star (with '#lowres' if required)
        distance : float
            Distance to star [ly]
    Returns
    ----------
        filename : str
            Location where modern spectrum has been saved as a plain-text file
    """

    print('Attempting to obtain spectrum')

    # Import required libraries
    import os

    import certifi
    import requests
    # from astropy.io import fits

    # Convert stellar parameters
    distance = float(distance) * 9.46073047e17  # Convert ly -> cm
    name = str(name).strip().lower()

    # Check if lowres
    name_split = name.split('#')
    if len(name_split) == 1:
        lowres = False
    elif (len(name_split) == 2) and (name_split[1] == 'lowres'):
        lowres = True
    else:
        raise Exception(f"Invalid unable to parse star name '{name}'!")
    name = name_split[0]

    print(f'\tParameters: [star = {name}, distance = {distance:1.2e} ly, lowres = {lowres}]')

    r_scale = 1.496e13  # 1 AU in cm

    # Get database and name of star
    name = name.strip()
    database = ''
    star = ''
    for k in stars_online.keys():
        if name in stars_online[k]:
            star = name
            database = k
            break
    if database == '':
        raise Exception(f"Could not find star '{name}' in stellar databases!")
    else:
        print(f"\tFound star in '{database}' database")

    # Convert data from database source format to plain text file
    plaintext_spectrum = f'spec_{star}.txt'
    database_spectrum = f'spec_{star}.{database}'
    print(f"\tDownloading spectrum and writing file '{plaintext_spectrum}'")

    if os.path.isfile(plaintext_spectrum):
        print('\t(Overwriting existing file)')

    new_str = f'# Spectrum of {star} ({database}) at 1 AU\n# WL(nm)\tFlux(ergs/cm**2/s/nm)\n'
    match database:
        case 'muscles':
            cert = certifi.where()
            if lowres:
                source = f'https://archive.stsci.edu/missions/hlsp/muscles/{star}/hlsp_muscles_multi_multi_{star}_broadband_v23_adapt-const-res-sed.fits'
            else:
                source = f'https://archive.stsci.edu/missions/hlsp/muscles/{star}/hlsp_muscles_multi_multi_{star}_broadband_v23_adapt-var-res-sed.fits'
            resp = requests.get(source, verify=cert)  # Download file

            if resp.status_code == 404:  # Try other possible option (v22 instead of v23)
                if lowres:
                    source = f'https://archive.stsci.edu/missions/hlsp/muscles/{star}/hlsp_muscles_multi_multi_{star}_broadband_v22_adapt-const-res-sed.fits'
                else:
                    source = f'https://archive.stsci.edu/missions/hlsp/muscles/{star}/hlsp_muscles_multi_multi_{star}_broadband_v22_adapt-var-res-sed.fits'
            resp = requests.get(source, verify=cert)  # Download file

            if resp.status_code != 200:
                print(
                    f"\t WARNING: Request returned with status code '{int(resp.status_code)}' (should be 200/OK)"
                )

            with open(database_spectrum, 'wb') as f:
                f.write(resp.content)

            from astropy.io import fits
            # from astropy.table import Table

            # Epsilon Eridani is 10.475 light years away and with 0.735 solar radius
            # GJ876 is 15.2 light years away and has 0.3761 solar radius
            # GJ551 (proxima cen) is 4.246 light years away and has 0.1542 solar radius
            # GJ436 is 31.8 light years away and has 0.42 solar radius
            # GJ1214 is 47.5 light years away and has 0.2064 solar radius
            # TRAPPIST-1 is 40.66209 ly away and has 0.1192 solar radius
            hdulist = fits.open(database_spectrum)
            spec = fits.getdata(database_spectrum, 1)

            # WAVELENGTH : midpoint of the wavelength bin in Angstroms
            # WAVELENGTH0: left (blue) edge of the wavelength bin in Angstroms
            # WAVELENGTH1: right (red) edge of the wavelength bin in Angstroms
            # FLUX : average flux density in the wavelength bin in erg s-1 cm-2 Angstroms-1

            negaflux = False

            for n, w in enumerate(spec['WAVELENGTH']):
                wl = w * 0.1  # Convert å to nm
                fl = (
                    float(spec['FLUX'][n]) * 10.0 * (distance / r_scale) ** 2
                )  # Convert units and scale flux

                negaflux = negaflux or (fl <= 0)

                fl_abs = max(0.0, fl)

                new_str += f'{wl:1.7e}\t{fl_abs:1.7e} \n'

            with open(plaintext_spectrum, 'w') as f:
                f.write(new_str)

            if negaflux:
                print(
                    '\t WARNING: The stellar spectrum contained flux value(s) <= 0.0 ! These were set to zero.'
                    % wl
                )

        case 'vpl':
            cert = False  # This is not good, but it will stay for now.
            source = f'https://vpl.astro.washington.edu/spectra/stellar/{star}um.txt'
            resp = requests.get(source, verify=cert)  # Download file

            if resp.status_code != 200:
                print(
                    f"\t WARNING: Request returned with status code '{int(resp.status_code)}' (should be 200/OK)"
                )

            with open(database_spectrum, 'wb') as f:
                f.write(resp.content)

            with open(database_spectrum) as f:
                for line in f.readlines():
                    if not line.startswith('#') and line.split():
                        li = line.split()

                        wl = float(li[0]) * 1.0e3  # Convert um to nm
                        fl = (
                            float(li[1]) * 1.0e4 * (distance / r_scale) ** 2
                        )  # Convert units and scale flux

                        new_str += f'{wl:1.7e}\t{fl:1.7e} \n'

            with open(plaintext_spectrum, 'w') as f:
                f.write(new_str)

        case 'nrel':
            cert = certifi.where()
            source = 'https://www.nrel.gov/grid/solar-resource/assets/data/newguey2003.txt'  # Set to Sun only.
            resp = requests.get(source, verify=cert)  # Download file

            if resp.status_code != 200:
                print(
                    f"\t WARNING: Request returned with status code '{int(resp.status_code)}' (should be 200/OK)"
                )

            with open(database_spectrum, 'wb') as f:
                f.write(resp.content)

            i = -1
            with open(database_spectrum) as f:
                for line in f.readlines():
                    i += 1
                    if i < 9:
                        continue  # Skip header

                    li = line.split()

                    wl = float(li[0])  # Already in nm
                    fl = (
                        float(li[1]) * 1.0e3
                    )  # Convert [W m-2 nm-1] -> [erg s-1 cm-2 nm-1], already at 1 AU

                    new_str += f'{wl:1.7e}\t{fl:1.7e} \n'

            with open(plaintext_spectrum, 'w') as f:
                f.write(new_str)

    os.remove(database_spectrum)

    print('\tDone!')

    return plaintext_spectrum


def PrintHelp():
    print("""
This script downloads and parses stellar spectra from online databases.

Run pattern: GetStellarSpectrum.py [command] [param1] [param2] 

Commands:
    'help'
        Shows this menu.
        No parameters.
    'list'
        Lists available stars.
        No parameters.
    'get'
        Downloads and converts spectrum for given star.
        'param1' : star name (append '#lowres' to star name to avoid large files)
        'param2' : distance from Earth in units of Ly
            """)


# Run script
if __name__ == '__main__':
    if len(sys.argv) == 1:
        print('Not enough arguments provided.')
        PrintHelp()
        exit(1)

    match sys.argv[1]:
        case 'list':
            print('Available stars:')
            for k in stars_online.keys():
                for s in stars_online[k]:
                    print(f'{s:>12}    ({k:>7})')

        case 'get':
            star = str(sys.argv[2])
            sdst = float(sys.argv[3])
            DownloadModernSpectrum(star, sdst)

        case 'help':
            PrintHelp()

        case _:
            print('Invalid command provided.')
            PrintHelp()

# End of file
