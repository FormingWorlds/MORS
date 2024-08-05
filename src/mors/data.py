import os
import subprocess
from osfclient.api import OSF
from pathlib import Path

#project ID of the stellar evolution tracks folder in the OSF
project_id = '9u3fb'

def download_folder(*, storage, folders: list[str], data_dir: Path):
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
            print(f'Downloading {file.path}...')
            with open(target, 'wb') as f:
                file.write_to(f)
            break


def GetFWLData() -> Path:
    """
    Get path to FWL data directory on the disk
    """
    fwl_data_dir = os.getenv('FWL_DATA')
    if not os.environ.get("FWL_DATA"):
        raise Exception("The FWL_DATA environment variable where spectral data will be downloaded needs to be set up!")
    return Path(fwl_data_dir).absolute()

def DownloadEvolutionTracks(fname=""):
    """
    Download evolution track data

    Inputs :
        - fname (optional) :    folder name, "/Spada" or "/Baraffe"
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
        print(f"Unrecognised folder name:  {fname}")

    folders = [folder for folder in folder_list if not (data_dir / folder).exists()]

    if folders:
        print("Downloading MORS evolution tracks")
        download_folder(storage=storage, folders=folders, data_dir=data_dir)

    if "Spada" in folders:
        #Unzip Spada evolution tracks
        wrk_dir = os.getcwd()
        os.chdir(data_dir / "Spada")
        subprocess.call( ['tar','xvfz', 'fs255_grid.tar.gz'] )
        subprocess.call( ['rm','-f', 'fs255_grid.tar.gz'] )
        os.chdir(wrk_dir)

    return
