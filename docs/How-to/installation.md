# Installation 

### Prerequisites
- **Python:** >3.11 installed
- **pip:** available (`python -m pip --version`)
- **Git:** only needed for the developer install (`git --version`)
- **Internet access:** required once to download the stellar evolution tracks
- *(Optional)* **Conda/Anaconda/Miniconda:** only if you want to use a conda environment

### 0. Optional: Conda/virtual environment

Create and activate a Conda environment (requires `conda` installed):
```bash
conda create -n mors python=3.11 -y
conda activate mors
```

No `conda`? create and activate a virtual environment (venv):
```bash
python -m venv .venv
source .venv/bin/activate
```

### 1. Basic install

The Forming Worlds Mors package is available on PyPI. Run the following command to install

```sh
pip install fwl-mors
```
### 2. Developer install

You can alternatively download the source code from GitHub somewhere on your computer using

```
git clone git@github.com:FormingWorlds/MORS.git
```

Then run the following command inside the main directory to install the code (check the pyproject.toml file for dependencies)

```
pip install -e .
```


### 3. Stellar evolution tracks

The code requires also a set of stellar evolution data, stored in the [OSF repository](https://osf.io/9u3fb/).

You can use `mors download all` to download the data. This will download and extract package stellar evolution tracks data.

By default, MORS stores the data in based on the [XDG specification](https://specifications.freedesktop.org/basedir-spec/latest/).
You can check the location by typing `mors env` in your terminal.
You can override the path using the `FWL_DATA` environment variable, e.g.

```console
export FWL_DATA=...
```

Where ... should be replaced with the path to your main data directory. To make this permanent on Ubuntu, use

```console
gedit ~/.profile
```

and add the export command to the bottom of the file.

Alternatively, when creating a star object in your Python script, you can specify the path to a directory where evolution tracks are stored using the starEvoDir keyword

```python
import mors
myStar = mors.StarEvo(starEvoDir=...)
```

where ... can be given as the path relative to the current directory. When this is done, no environmental variable needs to be set.