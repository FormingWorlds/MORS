from __future__ import annotations

import dataclasses
import logging
import os
from pathlib import Path

import platformdirs

log = logging.getLogger('fwl.' + __name__)

FWL_DATA_DIR = Path(os.environ.get('FWL_DATA', platformdirs.user_data_dir('fwl_data')))

# The stellar evolution tracks are fetched through fwl-io into the versioned
# data layout (star/tracks/<dataset>/r<record-id>), declared in
# mors_manifest.toml so the location and Zenodo pin have a single source of
# truth: fwl-io derives the location from the table key, so it cannot drift.
_BARAFFE_KEY = 'star.tracks.baraffe_2015'
_SPADA_KEY = 'star.tracks.spada_2013'

# Top-level directory inside the Spada archive.
_SPADA_GRID = 'fs255_grid'

# The manifest schema the shipped manifest is written against. An fwl-io older
# than this reads the manifest as malformed rather than as a version mismatch,
# so the load names which side is out of date. Keep in step with the fwl-io
# requirement in pyproject.toml; test_data.py pins the two together.
_FWL_IO_FLOOR = '26.7.22'


def _fwl_io_derives_the_location() -> bool:
    """Report whether the installed fwl-io derives a dataset location from its key.

    The question is whether ``subdir`` is still a manifest field, so the answer
    is read off the dataset fields rather than off how the attribute happens to
    be implemented. Only positive evidence of the older schema counts: an fwl-io
    that cannot be introspected is reported as current, so the caller never
    blames a version mismatch it cannot demonstrate.
    """
    try:
        from fwl_io.manifest import Dataset

        return 'subdir' not in {field.name for field in dataclasses.fields(Dataset)}
    except Exception:
        return True


def manifest_path() -> Path:
    """Entry-point target: the MORS dataset manifest read by fwl-io."""
    return Path(__file__).parent / 'data' / 'mors_manifest.toml'


def _dataset(key: str):
    """Return the dataset declared under ``key`` in the shipped manifest.

    An fwl-io older than the manifest schema rejects the shipped manifest as
    malformed, which points the reader at a file they should not edit, so that
    case is reported as the version mismatch it is. A manifest error under a
    current fwl-io is a real error in the shipped file and propagates unchanged.
    """
    from fwl_io import load_manifest

    try:
        datasets = {ds.key: ds for ds in load_manifest(manifest_path())}
    except ValueError as exc:
        if _fwl_io_derives_the_location():
            raise
        raise RuntimeError(
            f'fwl-io could not read the manifest MORS ships ({exc}); the installed '
            f'fwl-io predates the manifest schema: upgrade to fwl-io>={_FWL_IO_FLOOR}.'
        ) from exc
    return datasets[key]


def _fetcher(key: str):
    """Build an fwl-io fetcher for the dataset ``key`` from its manifest pin."""
    from fwl_io import create_fetcher

    ds = _dataset(key)
    return create_fetcher(
        subdir=ds.subdir,
        zenodo=ds.zenodo,
        registry=ds.registry(),
        data_root=GetFWLData(),
        extract=ds.extract,
    )


def _versioned_dir(key: str, label: str) -> Path:
    """Return the version directory that holds the files of dataset ``key``.

    A fetcher without a version_dir resolves the bare location, which would put
    the files one directory above where every reader looks for them.
    """
    fetcher = _fetcher(key)
    if getattr(fetcher, 'version_dir', None) is None:
        raise RuntimeError(
            f'fwl-io resolved an unversioned {label} directory {fetcher.target_dir}; '
            'the tracks are expected under an r<record-id> version directory.'
        )
    return fetcher.target_dir


def baraffe_data_dir() -> Path:
    """Return the versioned directory that holds the Baraffe track files.

    The ``r<record-id>`` version segment is resolved by fwl-io from the pinned
    manifest, so the layout stays a single source of truth. Resolving the path
    creates the ``FWL_DATA`` root if absent (an fwl-io side effect) but does not
    download the tracks; call ``DownloadEvolutionTracks("Baraffe")`` (or
    ``mors download baraffe``) to populate it.
    """
    return _versioned_dir(_BARAFFE_KEY, 'Baraffe')


def spada_data_dir() -> Path:
    """Return the directory that holds the Spada model grid.

    This is the ``fs255_grid`` directory inside the versioned fwl-io location of
    the Spada archive. Resolving the path does not download the tracks; call
    ``DownloadEvolutionTracks("Spada")`` (or ``mors download spada``) to populate it.
    """
    return _versioned_dir(_SPADA_KEY, 'Spada') / _SPADA_GRID


def GetFWLData() -> Path:
    """
    Get path to FWL data directory on the disk
    """
    return Path(FWL_DATA_DIR).absolute()


def DownloadEvolutionTracks(fname=''):
    """
    Download evolution track data

    Inputs :
        - fname (optional) :    folder name, "Spada" or "Baraffe"
                                if not provided download both

    Both grids are fetched through fwl-io into the versioned data layout. The
    Spada grid is a single archive, which fwl-io unpacks into its directory.
    """

    # If no folder name specified download both Spada and Baraffe
    if not fname:
        folder_list = ('Spada', 'Baraffe')
    elif fname in ('Spada', 'Baraffe'):
        folder_list = [fname]
    else:
        raise ValueError(f'Unrecognised folder name: {fname}')

    if 'Baraffe' in folder_list:
        _fetch_baraffe()
    if 'Spada' in folder_list:
        _fetch_spada()

    return


def _fetch_baraffe():
    """Fetch the Baraffe tracks through fwl-io (idempotent, hash-verified)."""
    _fetcher(_BARAFFE_KEY).fetch_all()


def _fetch_spada():
    """Fetch and unpack the Spada grid through fwl-io (idempotent, hash-verified)."""
    _fetcher(_SPADA_KEY).fetch_all()
