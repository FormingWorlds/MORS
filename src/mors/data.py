from __future__ import annotations

import logging
import os
import shutil
import subprocess
from pathlib import Path
from time import sleep

import platformdirs
from osfclient.api import OSF

log = logging.getLogger('fwl.' + __name__)

FWL_DATA_DIR = Path(os.environ.get('FWL_DATA', platformdirs.user_data_dir('fwl_data')))

# project ID of the stellar evolution tracks folder in the OSF
project_id = '9u3fb'

# The Baraffe tracks are fetched through fwl-io into the versioned data layout
# (star/tracks/baraffe_2015/r<record-id>), declared in mors_manifest.toml so the
# location and Zenodo pin have a single source of truth: fwl-io derives the
# location from the table key, so it cannot drift. The Spada grid is a single
# tarball and still comes down the legacy Zenodo/OSF path below.
_BARAFFE_KEY = 'star.tracks.baraffe_2015'

# The manifest schema the shipped manifest is written against. An fwl-io older
# than this reads the manifest as malformed rather than as a version mismatch,
# so the load names which side is out of date. Keep in step with the fwl-io
# requirement in pyproject.toml; test_data.py pins the two together.
_FWL_IO_FLOOR = '26.7.22'


def _fwl_io_derives_the_location() -> bool:
    """Report whether the installed fwl-io derives a dataset location from its key.

    The field became a derived property in the release that removed ``subdir``
    from the manifest schema, so its kind on the class distinguishes an fwl-io
    that reads the shipped manifest from one that rejects it.
    """
    from fwl_io.manifest import Dataset

    return isinstance(getattr(Dataset, 'subdir', None), property)


def manifest_path() -> Path:
    """Entry-point target: the MORS dataset manifest read by fwl-io."""
    return Path(__file__).parent / 'data' / 'mors_manifest.toml'


def _baraffe_dataset():
    """Return the Baraffe dataset declared in the shipped manifest.

    An fwl-io older than the manifest schema rejects the shipped manifest as
    malformed, which points the reader at a file they should not edit, so that
    case is re-raised naming the version that reads it. A manifest error under a
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
    return datasets[_BARAFFE_KEY]


def _baraffe_fetcher():
    """Build an fwl-io fetcher for the Baraffe tracks from the manifest pin."""
    from fwl_io import create_fetcher

    ds = _baraffe_dataset()
    return create_fetcher(
        subdir=ds.subdir,
        zenodo=ds.zenodo,
        registry=ds.registry(),
        data_root=GetFWLData(),
    )


def baraffe_data_dir() -> Path:
    """Return the versioned directory that holds the Baraffe track files.

    The ``r<record-id>`` version segment is resolved by fwl-io from the pinned
    manifest, so the layout stays a single source of truth. Resolving the path
    creates the ``FWL_DATA`` root if absent (an fwl-io side effect) but does not
    download the tracks; call ``DownloadEvolutionTracks("Baraffe")`` (or
    ``mors download baraffe``) to populate it.
    """
    fetcher = _baraffe_fetcher()
    # A pre-versioning fwl-io (before the r<record-id> layout) resolves the bare
    # subdir and has no version_dir, which would silently mislocate the tracks.
    if getattr(fetcher, 'version_dir', None) is None:
        raise RuntimeError(
            f'fwl-io resolved an unversioned Baraffe directory {fetcher.target_dir}; '
            f'upgrade to fwl-io>={_FWL_IO_FLOOR} to resolve the versioned data layout.'
        )
    return fetcher.target_dir


def get_zenodo_record(folder: str) -> str | None:
    """
    Get Zenodo record ID for a given folder.

    Inputs :
        - folder : str
            Folder name to get the Zenodo record ID for

    Returns :
        - str | None : Zenodo record ID or None if not found
    """
    # Baraffe is fetched through fwl-io and is intentionally absent here.
    zenodo_map = {
        'Spada': '15729101',
    }
    return zenodo_map.get(folder, None)


def download_zenodo_folder(folder: str, data_dir: Path):
    """
    Download a specific Zenodo record into specified folder

    Inputs :
        - folder : str
            Folder name to download
        - folder_dir : Path
            local repository where data are saved
    """

    folder_dir = data_dir / folder
    folder_dir.mkdir(parents=True)
    zenodo_id = get_zenodo_record(folder)
    cmd = ['zenodo_get', zenodo_id, '-o', folder_dir]
    out = os.path.join(GetFWLData(), 'zenodo.log')
    log.debug('    logging to %s' % out)
    with open(out, 'w') as hdl:
        subprocess.run(cmd, check=True, stdout=hdl, stderr=hdl)


def download_OSF_folder(*, storage, folders: list[str], data_dir: Path):
    """
    Download a specific folder in the OSF repository

    Inputs :
        - storage : OSF storage name
        - folders : folder names to download
        - data_dir : local repository where data are saved
    """
    for file in storage.files:
        for folder in folders:
            if not file.path[1:].startswith(folder):
                continue
            parts = file.path.split('/')[1:]
            target = Path(data_dir, *parts)
            target.parent.mkdir(parents=True, exist_ok=True)
            log.info(f'Downloading {file.path}...')
            with open(target, 'wb') as f:
                file.write_to(f)
            break


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

    Baraffe is fetched through fwl-io into the versioned data layout; Spada is a
    single tarball and comes down the legacy Zenodo/OSF path, untarred in place.
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
        _download_spada()

    return


def _fetch_baraffe():
    """Fetch the Baraffe tracks through fwl-io (idempotent, hash-verified)."""
    _baraffe_fetcher().fetch_all()


def _download_spada():
    """Download and unpack the Spada grid via Zenodo, falling back to OSF."""
    # Create stellar evolution tracks data repository if not existing
    data_dir = GetFWLData() / 'stellar_evolution_tracks'
    data_dir.mkdir(parents=True, exist_ok=True)

    folder = 'Spada'
    folder_dir = data_dir / folder
    if folder_dir.exists():
        return

    # Link with OSF project repository (fallback mirror)
    osf = OSF()
    project = osf.project(project_id)
    storage = project.storage('osfstorage')

    max_tries = 2  # Maximum download attempts, could be a function argument
    log.info(f'Downloading stellar evolution tracks to {data_dir}')
    for i in range(max_tries):
        log.info(f'Attempt {i + 1} of {max_tries}')
        success = False

        try:
            download_zenodo_folder(folder=folder, data_dir=data_dir)
            success = True
        except (subprocess.CalledProcessError, OSError) as e:
            # zenodo_get exits non-zero on failure (CalledProcessError via
            # check=True) or is missing (FileNotFoundError); neither is a
            # RuntimeError, so both must be caught for the fallback to run.
            log.error(f'Zenodo download failed: {e}')
            # A non-zero exit can leave partial files, so clear the whole tree;
            # rmdir would raise on a non-empty directory and mask the failure.
            shutil.rmtree(folder_dir, ignore_errors=True)

        if not success:
            try:
                download_OSF_folder(storage=storage, folders=folder, data_dir=data_dir)
                success = True
            except (RuntimeError, OSError) as e:
                log.error(f'OSF download failed: {e}')

        if success:
            break

        if i < max_tries - 1:
            log.info('Retrying download...')
            sleep(5)  # Wait 5 seconds before retrying
        else:
            log.error('Max retries reached. Download failed.')

    # Unzip Spada evolution tracks (only when the download populated the folder)
    if folder_dir.exists():
        wrk_dir = os.getcwd()
        os.chdir(os.path.join(data_dir, 'Spada'))
        subprocess.call(['tar', 'xvfz', 'fs255_grid.tar.gz'])
        subprocess.call(['rm', '-f', 'fs255_grid.tar.gz'])
        os.chdir(wrk_dir)

    return
