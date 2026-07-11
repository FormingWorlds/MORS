# ruff: noqa: F401, F403
"""Public API for MORS.

This module re-exports the classes and functions that make up the MORS public
interface, so they can be imported directly from ``mors`` (for example
``mors.Star``, ``mors.Value``, or ``mors.aOrbHZ``).
"""
from __future__ import annotations

try:
    from ._version import __version__, __version_tuple__
except ImportError:
    # Fallback for when the package is not installed (e.g. running from source
    # without setuptools-scm having generated _version.py).
    __version__ = '0.0.0.dev0'
    __version_tuple__ = (0, 0, 0, 'dev0')

from .baraffe import *
from .cluster import Cluster
from .data import DownloadEvolutionTracks
from .miscellaneous import ActivityLifetime, IntegrateEmission, Load, ModelCluster
from .parameters import NewParams, PrintParams
from .physicalmodel import (
    ExtendedQuantities,
    Leuv,
    Lly,
    Lx,
    Lxuv,
    MdotFactor,
    OmegaBreak,
    OmegaSat,
    ProtSat,
    RotationQuantities,
    XrayScatter,
    XUVScatter,
    aOrbHZ,
    dOmegadt,
)
from .rotevo import EvolveRotation, EvolveRotationStep
from .spectrum import *
from .star import Percentile, Star
from .stellarevo import (
    Icore,
    Ienv,
    Itotal,
    Lbol,
    LoadTrack,
    Mcore,
    Menv,
    Rcore,
    Rstar,
    StarEvo,
    Teff,
    Value,
    dIcoredt,
    dIenvdt,
    dItotaldt,
    dMcoredt,
    dRcoredt,
    tauConv,
)
from .synthesis import *
