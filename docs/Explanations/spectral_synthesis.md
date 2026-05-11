# Spectral synthesis

The `spectrum.py` module provides the `Spectrum` class for handling continuous stellar spectra (wavelength in nm, flux in erg s$^{-1}$ cm$^{-2}$ nm$^{-1}$ at 1 AU). Spectra can be loaded from TSV files or arrays, extended to shorter wavelengths using a constant extrapolation and to longer wavelengths using the Planck function (`Spectrum.ExtendPlanck`), and integrated over the five defined wavelength bands (X-ray, EUV1, EUV2, UV, Planckian) with `Spectrum.CalcBandFluxes`.

## Historical spectra 

The `synthesis.py` module builds historical spectra by scaling a modern reference spectrum band-by-band. The workflow consists of three steps:

1. `GetProperties(Mstar, pctle, age)` computes band-integrated fluxes and stellar radius and temperature for a given star at a given age.
2. `CalcBandScales(modern_dict, historical_dict)` computes the flux scale factor $Q$ for each band as the ratio of historical to modern flux.
3. `CalcScaledSpectrumFromProps(modern_spec, modern_dict, historical_dict)` applies those scale factors to the modern spectrum to produce the historical one.

An inverse fitting function `FitModernProperties` uses **Nelder-Mead optimisation** to estimate the rotation percentile (and optionally the age) of a star from its observed spectrum.