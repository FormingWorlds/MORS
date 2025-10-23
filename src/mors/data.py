import logging
import os
import subprocess
from pathlib import Path
from time import sleep

import platformdirs
from osfclient.api import OSF

import logging
log = logging.getLogger("fwl."+__name__)

FWL_DATA_DIR = Path(os.environ.get('FWL_DATA', platformdirs.user_data_dir('fwl_data')))

#project ID of the stellar evolution tracks folder in the OSF
project_id = '9u3fb'

def get_zenodo_record(folder: str) -> str | None:
    """
    Get Zenodo record ID for a given folder.

    Inputs :
        - folder : str
            Folder name to get the Zenodo record ID for

    Returns :
        - str | None : Zenodo record ID or None if not found
    """
    zenodo_map = {
        'Baraffe': '15729114',
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
    cmd = [
            "zenodo_get", zenodo_id,
            "-o", folder_dir
        ]
    out = os.path.join(GetFWLData(), "zenodo.log")
    log.debug("    logging to %s"%out)
    with open(out,'w') as hdl:
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

def DownloadEvolutionTracks(fname=""):
    """
    Download evolution track data

    Inputs :
        - fname (optional) :    folder name, "Spada" or "Baraffe"
                                if not provided download both
    """

    #Create stellar evolution tracks data repository if not existing
    data_dir = GetFWLData() / "stellar_evolution_tracks"
    data_dir.mkdir(parents=True, exist_ok=True)

    #Link with OSF project repository
    osf = OSF()
    project = osf.project(project_id)
    storage = project.storage('osfstorage')

    #If no folder name specified download both Spada and Baraffe
    if not fname:
        folder_list = ("Spada", "Baraffe")
    elif fname in ("Spada", "Baraffe"):
        folder_list = [fname]
    else:
        raise ValueError(f"Unrecognised folder name: {fname}")

    for folder in folder_list:
        folder_dir = data_dir / folder
        max_tries = 2 # Maximum download attempts, could be a function argument

        if not folder_dir.exists():
            log.info(f"Downloading stellar evolution tracks to {data_dir}")
            for i in range(max_tries):
                log.info(f"Attempt {i + 1} of {max_tries}")
                success = False

                try:
                    download_zenodo_folder(folder = folder, data_dir=data_dir)
                    success = True
                except RuntimeError as e:
                    log.error(f"Zenodo download failed: {e}")
                    folder_dir.rmdir()

                if not success:
                    try:
                        download_OSF_folder(storage=storage, folders=folder, data_dir=data_dir)
                        success = True
                    except RuntimeError as e:
                        log.error(f"OSF download failed: {e}")

                if success:
                    break

                if i < max_tries - 1:
                    log.info("Retrying download...")
                    sleep(5) # Wait 5 seconds before retrying
                else:
                    log.error("Max retries reached. Download failed.")

            if folder=="Spada":
                #Unzip Spada evolution tracks
                wrk_dir = os.getcwd()
                os.chdir(os.path.join(data_dir , "Spada"))
                subprocess.call( ['tar','xvfz', 'fs255_grid.tar.gz'] )
                subprocess.call( ['rm','-f', 'fs255_grid.tar.gz'] )
                os.chdir(wrk_dir)

    return
