"""Tests for src/mors/data.py: stellar evolution track download plumbing.

Covers the DownloadEvolutionTracks orchestrator (both grids are fetched through
fwl-io, and an unknown name is rejected before any fetch), the versioned
directory resolvers for the Baraffe and Spada grids, and the shipped fwl-io
manifest and registries. All network and filesystem download side effects are
mocked so nothing leaves the test process.

data.py is a utility source, so the physics-invariant requirement does not
apply; the anti-happy-path rules (edge case, error contract, discriminating
assertions) do.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import mors.data as data

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]


class _RecordingFetcher:
    """Fetcher double that records which dataset keys were fetched."""

    def __init__(self, log, key):
        self._log = log
        self._key = key

    def fetch_all(self):
        self._log.append(self._key)


def _record_fetches(monkeypatch):
    """Route data._fetcher to a network-free double and return the fetch log."""
    log = []
    monkeypatch.setattr(data, '_fetcher', lambda key: _RecordingFetcher(log, key))
    return log


def test_get_fwl_data_returns_absolute(monkeypatch, tmp_path):
    """GetFWLData resolves the configured data directory to an absolute path."""
    # Case 1: an already-absolute FWL_DATA_DIR is returned unchanged in value.
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    result = data.GetFWLData()
    # The returned path is absolute regardless of how FWL_DATA_DIR was given.
    assert result.is_absolute()
    # It points at the configured directory, not some default location.
    assert result == tmp_path.absolute()

    # Case 2: a relative FWL_DATA_DIR exercises the .absolute() promotion.
    monkeypatch.setattr(data, 'FWL_DATA_DIR', Path('rel_data_dir'), raising=False)
    rel_result = data.GetFWLData()
    # The relative directory is promoted to an absolute path, not left relative.
    assert rel_result.is_absolute()
    # .absolute() anchors the relative name at the current working directory.
    assert rel_result == Path('rel_data_dir').absolute()
    # The final path component is preserved through the conversion.
    assert rel_result.name == 'rel_data_dir'


def test_download_tracks_unknown_name_raises(monkeypatch, tmp_path):
    """DownloadEvolutionTracks rejects an unrecognised folder name with ValueError."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    log = _record_fetches(monkeypatch)

    with pytest.raises(ValueError, match='Unrecognised folder name'):
        data.DownloadEvolutionTracks('Kroupa')

    # The error fires before any fetch is attempted (no side effect ran).
    assert log == []
    # Nothing was created below the data root either.
    assert list(tmp_path.iterdir()) == []


@pytest.mark.parametrize(
    ('name', 'keys'),
    [
        ('Baraffe', ['star.tracks.baraffe_2015']),
        ('Spada', ['star.tracks.spada_2013']),
        ('', ['star.tracks.baraffe_2015', 'star.tracks.spada_2013']),
    ],
)
def test_download_tracks_fetches_the_requested_grids(monkeypatch, tmp_path, name, keys):
    """Each grid name fetches exactly its own manifest dataset, and no name fetches both."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    log = _record_fetches(monkeypatch)

    data.DownloadEvolutionTracks(name)

    # The requested datasets were fetched once each, in a fixed order.
    assert log == keys
    # Discrimination: a named grid never pulls in the other one.
    assert len(log) == len(keys)


def test_fetcher_forwards_the_archive_setting(monkeypatch, tmp_path):
    """The fetcher is built with the manifest's extract setting and the data root."""
    import fwl_io

    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    seen = {}

    def fake_create_fetcher(**kwargs):
        seen.update(kwargs)
        return object()

    monkeypatch.setattr(fwl_io, 'create_fetcher', fake_create_fetcher)

    data._fetcher(data._SPADA_KEY)

    # The Spada archive is unpacked by fwl-io, so the setting must reach it.
    assert seen['extract'] == 'tar'
    assert seen['zenodo'] == '10.5281/zenodo.15729101'
    assert seen['data_root'] == tmp_path.absolute()
    # Discrimination: a plain-file dataset passes no extraction.
    seen.clear()
    data._fetcher(data._BARAFFE_KEY)
    assert seen['extract'] is None
    assert seen['zenodo'] == '10.5281/zenodo.15729114'


def test_baraffe_data_dir_is_versioned(monkeypatch, tmp_path):
    """baraffe_data_dir resolves to the versioned fwl-io layout, not the legacy path."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)

    resolved = data.baraffe_data_dir()

    # The path is the pinned version directory below the new domain-first subdir.
    assert resolved == tmp_path / 'star' / 'tracks' / 'baraffe_2015' / 'r15729114'
    # Discrimination: the version segment must be present. A fetcher resolving the
    # bare location would sit one level up, which is what baraffe_data_dir guards.
    assert resolved != tmp_path / 'star' / 'tracks' / 'baraffe_2015'
    assert resolved.name == 'r15729114'


def test_baraffe_data_dir_rejects_unversioned_fwl_io(monkeypatch, tmp_path):
    """A fetcher resolving a directory without the version segment is rejected loudly."""

    class _StaleFetcher:
        # A fetcher with no version_dir resolves the bare location, one level
        # above the tracks, which would silently mislocate every read.
        version_dir = None
        target_dir = tmp_path / 'star' / 'tracks' / 'baraffe_2015'

    monkeypatch.setattr(data, '_fetcher', lambda key: _StaleFetcher)
    with pytest.raises(RuntimeError) as excinfo:
        data.baraffe_data_dir()
    msg = str(excinfo.value)
    # The error is actionable: it names the offending path and the layout expected.
    assert 'unversioned' in msg
    assert str(_StaleFetcher.target_dir) in msg
    assert 'r<record-id>' in msg
    # Discrimination: it is the layout guard talking, not the manifest-schema
    # guard, which reports an unreadable manifest instead.
    assert 'could not read the manifest' not in msg


def test_stale_fwl_io_is_named_as_the_stale_side(monkeypatch):
    """An fwl-io too old to read the shipped manifest is named as the thing to upgrade."""

    def _rejects_the_current_schema(path):
        # An fwl-io predating key-derived locations refuses the manifest for the
        # field it no longer needs, which reads as an error in MORS's own file.
        raise ValueError(
            'dataset \'star.tracks.baraffe_2015\': missing required field "subdir"'
        )

    monkeypatch.setattr('fwl_io.load_manifest', _rejects_the_current_schema)
    monkeypatch.setattr(data, '_fwl_io_derives_the_location', lambda: False)
    with pytest.raises(RuntimeError) as excinfo:
        data._dataset(data._BARAFFE_KEY)
    msg = str(excinfo.value)
    # The reader is sent to the installed package, not to the shipped manifest.
    assert 'upgrade to fwl-io>=26.7.22' in msg
    assert 'predates the manifest schema' in msg
    # The underlying complaint is kept, so the failure stays diagnosable.
    assert 'missing required field' in msg
    assert isinstance(excinfo.value.__cause__, ValueError)


def test_manifest_error_under_a_current_fwl_io_propagates(monkeypatch):
    """A real defect in the shipped manifest is not blamed on the installed fwl-io."""

    def _rejects_a_genuine_defect(path):
        # An fwl-io that does derive locations rejecting the manifest means the
        # manifest is at fault, and no upgrade would change that.
        raise ValueError("dataset 'star.tracks.baraffe_2015': zenodo value 'x' is not a DOI")

    monkeypatch.setattr('fwl_io.load_manifest', _rejects_a_genuine_defect)
    monkeypatch.setattr(data, '_fwl_io_derives_the_location', lambda: True)
    with pytest.raises(ValueError) as excinfo:
        data._dataset(data._BARAFFE_KEY)
    # The manifest error reaches the caller as itself, not recast as a version
    # problem, so the reader is sent to the file that is actually wrong.
    assert 'is not a DOI' in str(excinfo.value)
    assert 'upgrade to fwl-io' not in str(excinfo.value)
    # It is the original exception, not a new one carrying the same text.
    assert excinfo.value.__cause__ is None


def test_capability_check_distinguishes_the_two_manifest_schemas(monkeypatch):
    """The check separates an fwl-io that derives the location from one that declares it."""
    import dataclasses

    import fwl_io.manifest as fwl_manifest

    # The installed fwl-io satisfies the declared floor, so it derives the
    # location and the shipped manifest loads.
    assert data._fwl_io_derives_the_location() is True
    assert data._dataset(data._BARAFFE_KEY).key == 'star.tracks.baraffe_2015'

    @dataclasses.dataclass
    class _DeclaredLocationDataset:
        # An fwl-io before the schema move carries the location as a manifest
        # field, which is the fact the check reads.
        key: str = 'g.d'
        subdir: str = 'g/d'

    monkeypatch.setattr(fwl_manifest, 'Dataset', _DeclaredLocationDataset)
    # Discrimination: against that class the check reports the older schema, so
    # the version guard is driven by the installed package, not hard-coded true.
    assert data._fwl_io_derives_the_location() is False

    @dataclasses.dataclass
    class _DerivedLocationDataset:
        # A later fwl-io may implement the derivation any way it likes; what
        # matters is that the location is no longer a field of the dataset.
        key: str = 'g.d'

        @property
        def subdir(self) -> str:
            return self.key.replace('.', '/')

    monkeypatch.setattr(fwl_manifest, 'Dataset', _DerivedLocationDataset)
    assert data._fwl_io_derives_the_location() is True

    class _UnrecognisableDataset:
        pass

    monkeypatch.setattr(fwl_manifest, 'Dataset', _UnrecognisableDataset)
    # An fwl-io the check cannot read is reported as current, so a manifest
    # error is never blamed on a version mismatch that was not demonstrated.
    assert data._fwl_io_derives_the_location() is True


def test_declared_floor_matches_the_error_message_floor():
    """The version the errors name is the version the package actually requires."""
    import tomllib

    from packaging.requirements import Requirement
    from packaging.utils import canonicalize_name

    pyproject = Path(__file__).parents[1] / 'pyproject.toml'
    dependencies = tomllib.loads(pyproject.read_text(encoding='utf-8'))['project'][
        'dependencies'
    ]
    # Match on the canonical project name, so an extras suffix or an underscore
    # spelling still resolves to the same requirement instead of silently
    # leaving the pin unchecked.
    declared = [
        req for req in map(Requirement, dependencies) if canonicalize_name(req.name) == 'fwl-io'
    ]
    # Exactly one fwl-io requirement, so there is one floor to agree with.
    assert len(declared) == 1
    lower_bounds = [spec.version for spec in declared[0].specifier if spec.operator == '>=']
    # The constant the guards interpolate is the floor the requirement states.
    # Raising the pin without raising the constant would send users to a version
    # that no longer satisfies the install. Only the lower bound is read, so
    # adding an upper bound or an environment marker does not fail this test for
    # a floor that is still correct.
    assert lower_bounds == [data._FWL_IO_FLOOR]


def test_nightly_cache_key_tracks_the_files_that_pin_the_tracks():
    """The nightly cache key hashes exactly the manifest and registry MORS ships."""
    import re

    repo_root = Path(__file__).parents[1]
    workflow = (repo_root / '.github' / 'workflows' / 'nightly.yml').read_text(encoding='utf-8')
    call = re.search(r'hashFiles\(([^)]*)\)', workflow)
    # A cache key that stops tracking the data does not fail: the nightly stays
    # green and quietly refetches every run, so the coupling is pinned here.
    assert call is not None, 'the nightly no longer derives its cache key from hashFiles'
    patterns = re.findall(r"'([^']+)'", call.group(1))
    assert patterns, 'the hashFiles call declares no patterns'

    from fwl_io import load_manifest

    hashed = {path.resolve() for pattern in patterns for path in repo_root.glob(pattern)}
    manifest = data.manifest_path().resolve()
    # Every declared dataset, not just Baraffe, so a dataset added to the
    # manifest later is covered by this test rather than tripping it.
    registries = {ds.registry_path.resolve() for ds in load_manifest(manifest)}
    assert registries, 'the manifest declares no dataset to track'
    # The Zenodo pin lives in the manifest, so a re-pin has to move the key.
    assert manifest in hashed
    # The per-file checksums live in the registries, so a re-sync has to move it too.
    assert registries <= hashed
    # Nothing else: an over-broad pattern would bust the cache on edits that
    # leave the data untouched, which costs a full refetch from a single mirror.
    assert hashed == {manifest} | registries


def test_manifest_path_loads_both_track_datasets():
    """The shipped MORS manifest declares Baraffe and Spada under the versioned layout."""
    from fwl_io import load_manifest

    datasets = {ds.key: ds for ds in load_manifest(data.manifest_path())}
    # Exactly the two track grids MORS reads.
    assert set(datasets) == {'star.tracks.baraffe_2015', 'star.tracks.spada_2013'}
    baraffe = datasets['star.tracks.baraffe_2015']
    # The location is the key spelled as a path.
    assert baraffe.subdir == 'star/tracks/baraffe_2015'
    assert baraffe.zenodo == '10.5281/zenodo.15729114'
    # MORS is the declared consumer, so fwl-io routes the fetch to it.
    assert 'mors' in baraffe.required_by
    spada = datasets['star.tracks.spada_2013']
    assert spada.subdir == 'star/tracks/spada_2013'
    assert spada.zenodo == '10.5281/zenodo.15729101'
    assert 'mors' in spada.required_by
    # Spada is one tarball, Baraffe is a set of plain files.
    assert spada.extract == 'tar'
    assert baraffe.extract is None


def test_baraffe_registry_pins_committed_checksums():
    """The committed Baraffe registry parses and pins its file checksums."""
    from fwl_io import load_manifest

    ds = {d.key: d for d in load_manifest(data.manifest_path())}['star.tracks.baraffe_2015']
    registry = ds.registry()  # reads the committed registry next to the manifest
    # The record ships 30 mass tracks plus the combined structure file.
    assert len(registry) == 31
    # A known file pins a specific published md5, so a corrupted or truncated
    # registry (or the wrong Zenodo record) is caught rather than silently fetched.
    assert registry['BHAC15-M0p010.txt'] == 'md5:7b2927f8cb983680692280344eee1d9a'
    # The solar-mass track the reader interpolates over is present, not just any file.
    assert 'BHAC15-M1p000.txt' in registry


def test_spada_registry_pins_the_archive_checksum():
    """The committed Spada registry pins the single archive and its md5."""
    from fwl_io import load_manifest

    ds = {d.key: d for d in load_manifest(data.manifest_path())}['star.tracks.spada_2013']
    registry = ds.registry()
    # An archive dataset lists exactly one file: the tarball fwl-io verifies.
    assert list(registry) == ['fs255_grid.tar.gz']
    # The pinned md5 catches a corrupted download or the wrong Zenodo record.
    assert registry['fs255_grid.tar.gz'] == 'md5:f76987cf3d1da50435547f44a484a97f'


def test_spada_data_dir_is_versioned_and_inside_the_grid(monkeypatch, tmp_path):
    """spada_data_dir resolves to the fs255_grid directory of the versioned location."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)

    resolved = data.spada_data_dir()

    version_dir = tmp_path / 'star' / 'tracks' / 'spada_2013' / 'r15729101'
    # The grid directory sits inside the version directory the archive unpacks into.
    assert resolved == version_dir / 'fs255_grid'
    # Discrimination: neither the bare location nor the version directory alone.
    assert resolved != version_dir
    assert resolved.parent.name == 'r15729101'


def test_spada_data_dir_rejects_unversioned_fwl_io(monkeypatch, tmp_path):
    """An unversioned Spada location is rejected loudly and names the Spada grid."""

    class _StaleFetcher:
        version_dir = None
        target_dir = tmp_path / 'star' / 'tracks' / 'spada_2013'

    monkeypatch.setattr(data, '_fetcher', lambda key: _StaleFetcher)
    with pytest.raises(RuntimeError) as excinfo:
        data.spada_data_dir()
    msg = str(excinfo.value)
    assert 'unversioned Spada directory' in msg
    assert str(_StaleFetcher.target_dir) in msg


def test_star_evo_default_directory_resolves_lazily(monkeypatch, tmp_path):
    """starEvoDirDefault is resolved on access, so importing stellarevo fetches nothing."""
    import mors.stellarevo as se

    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)

    resolved = se.starEvoDirDefault

    # The attribute is the string form of the Spada grid directory under the data root.
    assert resolved == str(
        tmp_path / 'star' / 'tracks' / 'spada_2013' / 'r15729101' / 'fs255_grid'
    )
    # Discrimination: it follows FWL_DATA at access time, not at import time.
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path / 'other', raising=False)
    assert se.starEvoDirDefault.startswith(str(tmp_path / 'other'))
    # An unknown module attribute still raises, so the hook does not swallow typos.
    with pytest.raises(AttributeError):
        se.starEvoDirDefaultTypo


def test_mors_manifest_is_discovered_via_entry_point():
    """fwl-io discovers the MORS manifest through the fwl_io.manifests entry point."""
    from fwl_io import discover_manifests

    found = discover_manifests()
    # A typo in the entry-point name or target would drop MORS from discovery.
    assert 'mors' in found, 'MORS manifest is not registered under fwl_io.manifests'
    keys = {ds.key for ds in found['mors']}
    assert keys == {'star.tracks.baraffe_2015', 'star.tracks.spada_2013'}
