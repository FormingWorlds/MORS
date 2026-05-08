# Tutorial: First run

By the end of this tutorial you will have installed MORS, computed your first stellar evolutionary track, plotted a quantity, queried values at specific ages, and saved the result for reuse.

!!! info "Units"
    `Age` is in **Myr**, `Prot` is in **days**, and `Omega` is in units of the **current solar rotation rate** ($\Omega_\odot = 2.67 \times 10^{-6}$ rad s$^{-1}$).

## Prerequisites

You need a Python 3 environment with `pip` and a working internet connection for the one-time data download.

Optionally, create and activate an isolated environment first. With Conda:

```bash
conda create -n mors python=3.11 -y
conda activate mors
```

Or with a standard virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

---

## Step 1: Install MORS

```bash
pip install fwl-mors
```

Verify the installation:

```bash
python -c "import mors; print('ok')"
```

---

## Step 2: Download stellar evolution data

MORS requires stellar evolution tracks, downloaded once:

```bash
mors download all
```

To check where the data are stored:

```bash
mors env
```

If you want to store data somewhere specific, set the `FWL_DATA` environment variable before downloading:

```bash
export FWL_DATA=/path/to/your/data
mors download all
```

---

## Step 3: Create your first star

Create a 1 Msun star with an initial rotation period of 2.7 days at ~1 Myr:

```python
import mors

star = mors.Star(Mstar=1.0, Prot=2.7)
```

You can also specify the initial rotation rate as a multiple of the solar rotation rate:

```python
star = mors.Star(Mstar=1.0, Omega=10.0)
```

---

## Step 4: Inspect available tracks

Print all available track names and their units:

```python
star.PrintAvailableTracks()
print(star.Units['Lx'])
```

!!! note
    `PrintAvailableTracks` uses the logging system. If you see no output, configure logging first:
    ```python
    from mors.logs import setup_logger
    setup_logger("INFO")
    star.PrintAvailableTracks()
    ```

Track arrays are accessible via the `Tracks` dictionary or as `<Quantity>Track` attributes directly on the star:

```python
age = star.Tracks['Age']   # or: star.AgeTrack
lx  = star.Tracks['Lx']   # or: star.LxTrack
```

---

## Step 5: Plot a track

```python
import matplotlib.pyplot as plt

fig, ax = plt.subplots()
ax.plot(star.AgeTrack, star.LxTrack)
ax.set_xlabel(f"Age [{star.Units['Age']}]")
ax.set_ylabel(f"Lx [{star.Units['Lx']}]")
ax.set_xscale('log')
ax.set_yscale('log')
plt.show()
```

If you see a plot with no errors, your installation and data download are working correctly.

---

## Step 6: Query values at specific ages

Use the generic `Value` method:

```python
lx = star.Value(Age=150.0, Quantity='Lx')
print(lx)
```

Or the quantity accessor directly:

```python
lx = star.Lx(150.0)
print(lx)
```

Both return a linearly interpolated scalar at the requested age.

---

## Step 7: Compare slow, medium, and fast rotators (optional)

MORS includes a built-in 1 Myr rotation distribution. You can create stars at the 5th, 50th, and 95th percentiles using string shortcuts:

```python
slow   = mors.Star(Mstar=1.0, percentile='slow')    # 5th percentile
medium = mors.Star(Mstar=1.0, percentile='medium')  # 50th percentile
fast   = mors.Star(Mstar=1.0, percentile='fast')    # 95th percentile

print(slow.percentile, medium.percentile, fast.percentile)
```

---

## Step 8: Save and reload

Saving avoids recomputing the tracks next time:

```python
star.Save(filename='star.pickle')
```

Reload with `mors.Load` rather than `pickle.load` directly, as it re-attaches the quantity accessor functions:

```python
star2 = mors.Load('star.pickle')
print(star2.Lx(150.0))
```