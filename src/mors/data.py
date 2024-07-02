import os
import subprocess
from osfclient.api import OSF
from tqdm import tqdm

#project ID of the stellar evolution tracks folder in the OSF
project_id = '9u3fb'

def DownloadEvolutionTracks():

    #Check if data environment variable is set up
    fwl_data_dir = os.getenv('FWL_DATA')
    if os.environ.get("FWL_DATA") == None:
        raise Exception("The FWL_DATA environment variable where input data will be downloaded needs to be set up!")

    #Create stellar evolution tracks data repository if not existing
    data_dir = fwl_data_dir + "/stellar_evolution_tracks"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    #Link with OSF project repository
    osf = OSF()
    project = osf.project(project_id)
    storage = project.storage('osfstorage')

    with tqdm(unit='files') as pbar:
        for store in project.storages:

            #Loop over all the remote files in the OSF project
            for file_ in store.files:

                #Set up local path for remote file
                path = file_.path
                if path.startswith('/'):
                    path = path[1:]
                path = os.path.join(data_dir, path)

                #Create local directory if needed
                directory, _ = os.path.split(path)
                os.makedirs(directory, exist_ok=True)

                #Download and write remote file to local path
                with open(path, "wb") as f:
                    file_.write_to(f)

                pbar.update()

    #Unzip Spada evolution tracks
    wrk_dir = os.getcwd()
    os.chdir(data_dir + '/Spada')
    subprocess.call( ['tar','xvfz', 'fs255_grid.tar.gz'] )
    subprocess.call( ['rm','-f', 'fs255_grid.tar.gz'] )
    os.chdir(wrk_dir)

    return
