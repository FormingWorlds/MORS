# Installation

!!! note "PROTEUS users"
    The standard way of installing this version of MORS is within the PROTEUS Framework, as described in the [PROTEUS installation guide](https://proteus-framework.org/PROTEUS/installation.html#9-install-submodules-as-editable). When installed as part of PROTEUS, MORS is set up automatically alongside all other modules. The standalone instructions below are only needed if you want to use MORS independently of PROTEUS.

!!! info "Prerequisites"
    - **Python** ≥ 3.11
    - **pip** (`python -m pip --version`)
    - **Git**: only needed for the developer install (`git --version`)
    - **Internet access**: required once to download the stellar evolution tracks
    - *(Optional)* **Conda** or **venv** : recommended to isolate the installation

---

## Standard install

MORS is available on [PyPI](https://pypi.org/project/fwl-mors/). Install it with:

```sh
pip install fwl-mors
```

Then download the required stellar evolution data:

```sh
mors download all
```

That's it. Jump to [first run](../Tutorials/first_run.md) to run your first model.

---

## Developer install

Use this route if you want to modify the source code or contribute to MORS.

### 1. Create an isolated environment (recommended)

=== "Conda"

    ```sh
    conda create -n mors python=3.11 -y
    conda activate mors
    ```

=== "venv"

    ```sh
    python -m venv .venv
    source .venv/bin/activate   # Windows: .venv\Scripts\activate
    ```

### 2. Clone the repository

```sh
git clone git@github.com:FormingWorlds/MORS.git
cd MORS
```

### 3. Install in editable mode

```sh
pip install -e .
```

This installs MORS and all its dependencies (see [`pyproject.toml`](https://github.com/FormingWorlds/MORS/blob/main/pyproject.toml)) while keeping the source directory live: any edits you make are immediately reflected without reinstalling.

---

## Stellar evolution data

MORS requires a set of pre-computed stellar evolution tracks. After installation, download them with:

```sh
mors download all
```

This fetches both the [Spada](https://zenodo.org/records/15729101) and [Baraffe](https://zenodo.org/records/15729114) track sets from two Zenodo records, with an automatic fallback to [OSF]((https://osf.io/9u3fb/)) if Zenodo is unavailable. If you only need one set, you can download them individually:

```sh
mors download spada
mors download baraffe
```

### Data location

By default, MORS stores data according to the [XDG Base Directory specification](https://specifications.freedesktop.org/basedir-spec/latest/). To check where data will be stored on your system:

```sh
mors env
```

### Changing the data directory

Set the `FWL_DATA` environment variable to redirect MORS to a different location:

```sh
export FWL_DATA=/path/to/your/data
```

To make this permanent, add that line to your shell configuration file (`~/.bashrc`, `~/.zshrc`, etc.) and reload it:

```sh
echo 'export FWL_DATA=/path/to/your/data' >> ~/.bashrc
source ~/.bashrc
```

Alternatively, you can pass the data path directly when loading stellar evolution tracks in Python, without setting any environment variable:

```python
import mors
StarEvo = mors.stellarevo.StarEvo(starEvoDir="/path/to/tracks")
```

Or when creating a `Star` object:

```python
star = mors.Star(Mstar=1.0, Omega=1.0, starEvoDir="/path/to/tracks")
```

---

## Verifying the installation

After installing and downloading the data, run the following to confirm everything works:

```python
import mors
star = mors.Star(Mstar=1.0, Omega=1.0)
print(f"Lx at 4.5 Gyr: {star.Lx(Age=4500.0):.3e} erg/s")
```

You should see an X-ray luminosity value printed without errors. If you run into any issues, check the [troubleshooting](../How-to/troubleshooting.md) page or open an issue on [GitHub](https://github.com/FormingWorlds/MORS/issues).