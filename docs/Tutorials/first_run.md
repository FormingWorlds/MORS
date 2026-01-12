# Tutorial: First run 

## What you’ll do
By the end of this tutorial you will:
1. Install MORS and download the required data
2. Create a `Star` and compute evolutionary tracks
3. Inspect available tracks + units
4. Plot one track
5. Find stellar values at specific ages
6. Save and reload the result

> **Time/units cheat sheet:** `Mstar` in **M☉**, `Age` in **Myr**, `Prot` in **days**, `Omega` in **Ω☉**.

---

## 0) Prerequisites
You need:
- Python 3 environment with `pip`
- A working internet connection (for downloading data once)

**Optional**: Create and activate a Conda environment (requires `conda` installed):
```bash
conda create -n mors python=3.11 -y
conda activate mors
```

No `conda`? create and activate a virtual environment (venv):
```bash
python -m venv .venv
source .venv/bin/activate
```

---

## 1) Install MORS
```bash
pip install fwl-mors
```

Quick sanity check:
```bash
python -c "import mors; print('mors imported:', mors.__version__ if hasattr(mors,'__version__') else 'ok')"
```

---

## 2) Download stellar evolution data
MORS requires stellar evolution tracks (downloaded once):
```bash
mors download all
```

See where data are stored:
```bash
mors env
```

If you want to place data somewhere else, set `FWL_DATA` (optional):
```bash
export FWL_DATA=/path/to/your/data
```

---

## 3) Create your first star
Create a 1 M☉ star with an initial rotation period of 2.7 days (at ~1 Myr):
```python
import mors
star = mors.Star(Mstar=1.0, Prot=2.7)
```

Alternative: specify initial rotation as Ω/Ω☉:
```python
star = mors.Star(Mstar=1.0, Omega=10.0)
```

---

## 4) Inspect what tracks exist
Print track names and units:
```python
star.PrintAvailableTracks()
print("Lx units:", star.Units.get("Lx"))
```

You can access arrays either via the `Tracks` dict:
```python
age = star.Tracks["Age"]
lx  = star.Tracks["Lx"]
```
or via convenience attributes:
```python
age = star.AgeTrack
lx  = star.LxTrack
```

---

## 5) Plot a track
```python
import matplotlib.pyplot as plt

plt.plot(star.AgeTrack, star.LxTrack)
plt.xlabel(f"Age [{star.Units['Age']}]")
plt.ylabel(f"Lx [{star.Units['Lx']}]")
plt.show()
```

If you see a plot and no errors, your installation + data are working.

---

## 6) Find stellar values at specific ages
Use the generic accessor:
```python
print(star.Value(Age=150.0, Quantity="Lx"))
```

Or a convenience method (when available):
```python
print(star.Lx(150.0))
```

---

## 7) (Optional) Try percentiles: slow/medium/fast rotators
This uses the built-in model distribution:
```python
slow   = mors.Star(Mstar=1.0, percentile="slow")    # 5th percentile
medium = mors.Star(Mstar=1.0, percentile="medium")  # 50th percentile
fast   = mors.Star(Mstar=1.0, percentile="fast")    # 95th percentile

print("slow percentile:", slow.percentile)
print("fast percentile:", fast.percentile)
```

---

## 8) Save and reload (recommended)
Save:
```python
star.Save(filename="star.pickle")
```

Reload later:
```python
import mors
star2 = mors.Load("star.pickle")
print(star2.Lx(150.0))
```
