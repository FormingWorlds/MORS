# Releasing

MORS derives its version straight from git tags using [setuptools-scm](https://setuptools-scm.readthedocs.io/), so there is no version string to edit by hand. A release is just a dated tag and a GitHub release; publishing that release uploads the package to [PyPI](https://pypi.org/project/fwl-mors) automatically.

## Version scheme

MORS uses [CalVer](https://calver.org/): tags are bare `YY.MM.DD` dates with no leading `v` (for example `26.07.11`). setuptools-scm reads the latest tag on `main` and writes it into `src/mors/_version.py` at build and install time; that file is gitignored and never edited by hand.

Between releases the version is a post-tag development string. With `version_scheme = "no-guess-dev"` a commit made after the `26.07.11` tag reports as `26.7.11.post1.devN+g<hash>`, which is honest about being a development build after that tag rather than a pre-release of a future date. The default `guess-next-dev` scheme would instead invent a next calendar date that could collide with the following day's release tag, which is why `no-guess-dev` is set.

## How to make a release

### 1. Make sure `main` is ready

CI on `main` should be green. Locally:

```console
pytest -m "(unit or smoke) and not skip"
ruff check src/ tests/
```

### 2. Tag the release

```console
git checkout main && git pull
git tag 26.07.11          # today's date as YY.MM.DD
git push origin 26.07.11
```

!!! warning "Tags are bare dates"
    Use a bare `YY.MM.DD` tag with no leading `v`, matching MORS's existing release tags. A mixed tag history (some `v`-prefixed, some not) makes the version sequence harder to follow.

### 3. Create a GitHub release

```console
gh release create 26.07.11 --title "26.07.11" --generate-notes
```

Or use the GitHub web interface: choose the tag, set the title to the same date, generate the release notes, and publish.

### 4. PyPI publication (automatic)

Publishing the GitHub release triggers the [publish workflow](https://github.com/FormingWorlds/MORS/actions/workflows/publish.yaml). It checks out the full tag history, builds the package with `python -m build`, and uploads it to PyPI through trusted publishing, so no API tokens are stored in the repository. The package appears at [pypi.org/project/fwl-mors](https://pypi.org/project/fwl-mors) within a few minutes.

### 5. Verify

```console
pip install --upgrade fwl-mors
python -c "import mors; print(mors.__version__)"
```

## How versioning works

| State of the checkout | Reported version |
|---|---|
| On the `26.07.11` tag | `26.7.11` |
| A few commits after the tag | `26.7.11.post1.devN+g<hash>` |
| Source checkout with no generated `_version.py` | `0.0.0.dev0` fallback |

The reported version drops the leading zeros in the month and day, because setuptools-scm emits PEP 440-canonical versions (see the normalisation note below).

The `0.0.0.dev0` fallback lives in `src/mors/__init__.py` and is used when no `_version.py` has been generated, which happens in a source checkout that was never built or installed. setuptools-scm writes `_version.py` at build and install time, and for that it needs the tag history, so a shallow clone with no tags also leaves the fallback in place. Fetch the tags with `git fetch --tags`. In CI the publish workflow checks out with `fetch-depth: 0` for this reason.

## Multiple releases on the same day

Append a patch number to the date:

```console
git tag 26.07.11.1
```

This produces version `26.7.11.1`.

## Note on version normalisation

setuptools-scm emits PEP 440-canonical versions, so a `26.07.11` tag becomes `26.7.11` (leading zeros in the month and day are dropped) in the built package, the wheel filename, and `mors.__version__`. This normalisation happens locally at build time; PyPI applies the same PEP 440 rule, so the published name matches. This is expected and consistent with earlier MORS releases.
