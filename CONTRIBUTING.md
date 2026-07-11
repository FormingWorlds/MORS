# Contributing guidelines

### Building the documentation

The documentation is written in [markdown](https://www.markdownguide.org/basic-syntax/), and uses [Zensical](https://www.zensical.org/) to generate the pages.

To build the documentation for yourself:

```console
pip install -e .[docs]
zensical serve
```

You can find the documentation source in the [docs](https://github.com/FormingWorlds/MORS/tree/main/docs) directory.
If you are adding new pages, make sure to update the listing in the [`mkdocs.yml`](https://github.com/FormingWorlds/MORS/blob/main/mkdocs.yml) under the `nav` entry.

The documentation is hosted on [PROTEUS Framework](https://proteus-framework.org/MORS/).
### Running tests

MORS uses [pytest](https://docs.pytest.org/en/latest/) to run the tests. You can run the tests for yourself using:

```console
pytest
```

To check coverage:

```console
coverage run -m pytest
coverage report  # to output to terminal
coverage html    # to generate html report
```


### Making a release

MORS uses [CalVer](https://calver.org/) and derives its version straight from git tags with [setuptools-scm](https://setuptools-scm.readthedocs.io/), so there is no version string to edit by hand. To cut a release, tag the current `main` with today's date and publish a GitHub release:

```console
git checkout main && git pull
git tag 26.07.11          # today's date as YY.MM.DD, with no leading "v"
git push origin 26.07.11
gh release create 26.07.11 --title "26.07.11" --generate-notes
```

Publishing the GitHub release triggers the [publish workflow](https://github.com/FormingWorlds/MORS/actions/workflows/publish.yaml), which builds the package and uploads it to [PyPI](https://pypi.org/project/fwl-mors) via trusted publishing. The full procedure, the version-scheme rationale, and troubleshooting are on the [release how-to](https://proteus-framework.org/MORS/How-to/releasing.html) page.
