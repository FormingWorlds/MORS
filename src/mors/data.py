import os
import subprocess
from osfclient.api import OSF

#project ID of the stellar evolution tracks folder in the OSF
project_id = '9u3fb'

def download_folder(storage, folder_name, local_path):
    ''''
    Download a specific folder in the OSF repository

    Inputs :
        - storage     : OSF storage name
        - folder_name : folder name to be downloaded
        - local_path  : local repository where data are saved
    '''
    for file in storage.files:
        if file.path.startswith(folder_name):
            local_file_path = local_path + file.path
            #Create local directory if needed
            os.makedirs(os.path.dirname(local_file_path), exist_ok=True)
            #Download the file
            with open(local_file_path, 'wb') as local_file:
                file.write_to(local_file)
    return

def DownloadEvolutionTracks(fname=""):
    '''
    Download evolution track data

    Inputs :
        - fname (optional) :    folder name, "Spada" or "Baraffe"
                                if not provided download both
    '''

    #Check if data environment variable is set up
    fwl_data_dir = os.getenv('FWL_DATA')
    if os.environ.get("FWL_DATA") == None:
        raise Exception("The FWL_DATA environment variable where input data will be downloaded needs to be set up!")

    #Create stellar evolution tracks data repository if not existing
    data_dir = fwl_data_dir + "/stellar_evolution_tracks/"
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)

    #Link with OSF project repository
    osf = OSF()
    project = osf.project(project_id)
    storage = project.storage('osfstorage')

    #If no folder name specified download both Spada and Baraffe
    #If local directory exists, assumes the data are already there
    unzip_spada = False
    if not fname:
        if not os.path.exists(data_dir+"/Spada"):
            download_folder(storage,"/Spada",data_dir)
            unzip_spada = True
        if not os.path.exists(data_dir+"/Baraffe"):
            download_folder(storage,"/Baraffe",data_dir)
    elif fname == "Spada":
        if not os.path.exists(data_dir+"/Spada"):
            download_folder(storage,"/Spada",data_dir)
            unzip_spada = True
    elif fname == "Baraffe":
        if not os.path.exists(data_dir+"/Baraffe"):
            download_folder(storage,"/Baraffe",data_dir)
    else:
        print("Unrecognised folder name in DownloadEvolutionTracks")

    if unzip_spada:
        #Unzip Spada evolution tracks
        wrk_dir = os.getcwd()
        os.chdir(data_dir + '/Spada')
        subprocess.call( ['tar','xvfz', 'fs255_grid.tar.gz'] )
        subprocess.call( ['rm','-f', 'fs255_grid.tar.gz'] )
        os.chdir(wrk_dir)

    return
