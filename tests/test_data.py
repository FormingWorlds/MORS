"""Tests for src/mors/data.py: stellar evolution track download plumbing.

Covers the Spada Zenodo record lookup, the Zenodo and OSF folder downloaders,
and the DownloadEvolutionTracks orchestrator: the Baraffe fwl-io fetch, the
Spada legacy path (untar, already-present short-circuit, retry / fallback
ladder), and the unknown-name error contract. The Baraffe track directory
resolver and the shipped fwl-io manifest are covered too. All network and
filesystem download side effects are mocked so nothing leaves the test process.

data.py is a utility source, so the physics-invariant requirement does not
apply; the anti-happy-path rules (edge case, error contract, discriminating
assertions) do.
"""

from __future__ import annotations

from pathlib import Path

import pytest

import mors.data as data

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]


class _FakeStorage:
    """Minimal OSF storage double exposing a .files iterable."""

    def __init__(self, files):
        self.files = files


class _FakeProject:
    def __init__(self, storage):
        self._storage = storage

    def storage(self, name):
        assert name == 'osfstorage'
        return self._storage


class _FakeOSF:
    """Stand-in for osfclient.api.OSF that never touches the network."""

    storage_obj = _FakeStorage([])

    def project(self, project_id):
        assert project_id == data.project_id
        return _FakeProject(self.storage_obj)


class _FakeOSFFile:
    """OSF file double whose write_to persists a marker byte string."""

    def __init__(self, path, payload=b'trackdata'):
        self.path = path
        self.payload = payload

    def write_to(self, handle):
        handle.write(self.payload)


def _patch_osf(monkeypatch):
    """Route data.OSF() through the network-free fake."""
    monkeypatch.setattr(data, 'OSF', _FakeOSF)


def test_get_zenodo_record_spada_only():
    """The legacy Zenodo map resolves Spada; Baraffe has moved to fwl-io."""
    # Spada resolves to its pinned published record id (a string, not None).
    assert data.get_zenodo_record('Spada') == '15729101'
    # Baraffe is fetched through fwl-io now, so it is absent from the legacy map
    # and yields the sentinel None rather than its old record id.
    assert data.get_zenodo_record('Baraffe') is None
    assert data.get_zenodo_record('Baraffe') != '15729114'
    # Edge case: an unrecognised folder yields the sentinel None, not a KeyError.
    assert data.get_zenodo_record('Nonexistent') is None
    assert data.get_zenodo_record('') is None


def test_download_zenodo_folder_builds_command_and_logs(monkeypatch, tmp_path):
    """download_zenodo_folder creates the target folder and shells out to zenodo_get."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)

    captured = {}

    def fake_run(cmd, check, stdout, stderr):
        captured['cmd'] = cmd
        captured['check'] = check
        # Emulate the tool writing to its log handle.
        stdout.write('ok')

    monkeypatch.setattr(data.subprocess, 'run', fake_run)

    data.download_zenodo_folder('Spada', tmp_path)

    folder_dir = tmp_path / 'Spada'
    # The per-folder directory is created before the download starts.
    assert folder_dir.is_dir()
    # The command targets the Spada record id and writes into the folder dir.
    assert captured['cmd'][0] == 'zenodo_get'
    assert captured['cmd'][1] == '15729101'
    assert Path(captured['cmd'][-1]) == folder_dir
    # check=True so a non-zero exit from zenodo_get propagates as an exception.
    assert captured['check'] is True
    # The log lands next to FWL_DATA_DIR, not inside the folder being populated.
    assert (tmp_path / 'zenodo.log').exists()


def test_download_OSF_folder_writes_matching_skips_others(tmp_path):
    """download_OSF_folder writes only files under the requested folders, once each."""
    files = [
        _FakeOSFFile('/Spada/fs255_grid.tar.gz', payload=b'spada'),
        _FakeOSFFile('/Baraffe/BHAC15.dat', payload=b'baraffe'),
        _FakeOSFFile('/Other/ignore.txt', payload=b'nope'),
    ]
    storage = _FakeStorage(files)

    data.download_OSF_folder(storage=storage, folders=['Spada'], data_dir=tmp_path)

    written = tmp_path / 'Spada' / 'fs255_grid.tar.gz'
    # The matching file is written with its byte payload into the mirrored tree.
    assert written.read_bytes() == b'spada'
    # A non-requested folder is left untouched (no directory, no file).
    assert not (tmp_path / 'Baraffe').exists()
    # The unrelated top-level folder is also skipped.
    assert not (tmp_path / 'Other').exists()


def test_download_OSF_folder_multiple_folders(tmp_path):
    """A folder list matches each of its members and mirrors the OSF path layout."""
    files = [
        _FakeOSFFile('/Spada/a.txt', payload=b'A'),
        _FakeOSFFile('/Baraffe/b.txt', payload=b'B'),
    ]
    storage = _FakeStorage(files)

    data.download_OSF_folder(storage=storage, folders=['Spada', 'Baraffe'], data_dir=tmp_path)

    # Both requested folders are mirrored with their nested files.
    assert (tmp_path / 'Spada' / 'a.txt').read_bytes() == b'A'
    assert (tmp_path / 'Baraffe' / 'b.txt').read_bytes() == b'B'


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
    _patch_osf(monkeypatch)

    called = {'zenodo': 0}

    def fake_zenodo(**kwargs):
        called['zenodo'] += 1

    monkeypatch.setattr(data, 'download_zenodo_folder', fake_zenodo)

    with pytest.raises(ValueError, match='Unrecognised folder name'):
        data.DownloadEvolutionTracks('Kroupa')

    # The error fires before any download is attempted (no side effect ran).
    assert called['zenodo'] == 0


def test_download_tracks_spada_short_circuits_baraffe_delegates(monkeypatch, tmp_path):
    """A present Spada folder skips its download; Baraffe always delegates to fwl-io."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    _patch_osf(monkeypatch)

    # Pre-create the Spada track folder so its existence guard short-circuits.
    (tmp_path / 'stellar_evolution_tracks' / 'Spada').mkdir(parents=True)

    calls = {'zenodo': 0, 'osf': 0, 'baraffe': 0}
    monkeypatch.setattr(
        data,
        'download_zenodo_folder',
        lambda **k: calls.__setitem__('zenodo', calls['zenodo'] + 1),
    )
    monkeypatch.setattr(
        data,
        'download_OSF_folder',
        lambda **k: calls.__setitem__('osf', calls['osf'] + 1),
    )
    monkeypatch.setattr(
        data,
        '_fetch_baraffe',
        lambda: calls.__setitem__('baraffe', calls['baraffe'] + 1),
    )

    # Empty fname takes the both-tracks branch.
    data.DownloadEvolutionTracks('')

    # Spada is already on disk, so neither Spada downloader runs.
    assert calls['zenodo'] == 0
    assert calls['osf'] == 0
    # Baraffe is delegated to fwl-io unconditionally (fwl-io does its own
    # checksum-based idempotency), so the fetch is invoked exactly once.
    assert calls['baraffe'] == 1


def test_download_tracks_spada_untar(monkeypatch, tmp_path):
    """The Spada path downloads then untars and removes the grid archive."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    _patch_osf(monkeypatch)

    base = tmp_path / 'stellar_evolution_tracks'

    def fake_zenodo(*, folder, data_dir):
        # A real download creates the folder; mirror that so os.chdir succeeds.
        (data_dir / folder).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(data, 'download_zenodo_folder', fake_zenodo)

    subcalls = []
    monkeypatch.setattr(data.subprocess, 'call', lambda cmd: subcalls.append(cmd))

    data.DownloadEvolutionTracks('Spada')

    # The Spada folder exists after the download step.
    assert (base / 'Spada').is_dir()
    # Exactly the untar and cleanup commands run, in order.
    assert subcalls[0][0] == 'tar'
    assert 'fs255_grid.tar.gz' in subcalls[0]
    assert subcalls[1][0] == 'rm'
    assert len(subcalls) == 2


def test_download_tracks_baraffe_uses_fwl_io(monkeypatch, tmp_path):
    """Baraffe is fetched through fwl-io, not the legacy Zenodo/OSF/untar path."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)

    fetched = {'n': 0}

    class _FakeFetcher:
        def fetch_all(self):
            fetched['n'] += 1

    monkeypatch.setattr(data, '_baraffe_fetcher', lambda: _FakeFetcher())

    # The legacy downloaders and the untar step must not be touched for Baraffe.
    legacy = {'zenodo': 0, 'osf': 0}
    monkeypatch.setattr(
        data,
        'download_zenodo_folder',
        lambda **k: legacy.__setitem__('zenodo', legacy['zenodo'] + 1),
    )
    monkeypatch.setattr(
        data,
        'download_OSF_folder',
        lambda **k: legacy.__setitem__('osf', legacy['osf'] + 1),
    )
    subcalls = []
    monkeypatch.setattr(data.subprocess, 'call', lambda cmd: subcalls.append(cmd))

    data.DownloadEvolutionTracks('Baraffe')

    # The fwl-io fetcher ran exactly once.
    assert fetched['n'] == 1
    # No legacy Zenodo/OSF download and no Spada-style untar for Baraffe.
    assert legacy == {'zenodo': 0, 'osf': 0}
    assert subcalls == []


def test_download_tracks_spada_zenodo_fails_osf_fallback(monkeypatch, tmp_path):
    """When Spada's Zenodo download fails, the OSF fallback runs and succeeds."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    _patch_osf(monkeypatch)

    def failing_zenodo(*, folder, data_dir):
        # Real code creates the folder before failing; the handler cleans it up.
        (data_dir / folder).mkdir(parents=True, exist_ok=True)
        # zenodo_get exits non-zero, which subprocess.run(check=True) surfaces as
        # CalledProcessError; the mock raises the real type so the fallback is
        # exercised through the exception the production code actually sees.
        raise data.subprocess.CalledProcessError(1, ['zenodo_get'])

    monkeypatch.setattr(data, 'download_zenodo_folder', failing_zenodo)

    osf_calls = {'n': 0, 'kwargs': None}

    def fake_osf(*, storage, folders, data_dir):
        # Capture the exact keyword arguments so a signature drift is caught,
        # not silently absorbed by a no-op stand-in.
        osf_calls['n'] += 1
        osf_calls['kwargs'] = {
            'storage': storage,
            'folders': folders,
            'data_dir': data_dir,
        }

    monkeypatch.setattr(data, 'download_OSF_folder', fake_osf)
    # Guard against any accidental real sleep in the retry ladder.
    monkeypatch.setattr(data, 'sleep', lambda s: None)

    data.DownloadEvolutionTracks('Spada')

    # The OSF fallback ran exactly once after the single Zenodo failure.
    assert osf_calls['n'] == 1
    kw = osf_calls['kwargs']
    tracks_dir = tmp_path / 'stellar_evolution_tracks'
    # The fallback receives the OSF storage handle opened from the project, so a
    # rename of the storage keyword would surface here.
    assert kw['storage'] is _FakeOSF.storage_obj
    # The download target is the shared tracks directory, not a per-folder subdir.
    assert kw['data_dir'] == tracks_dir
    # Present behaviour: _download_spada passes the folder name as a bare string,
    # while download_OSF_folder annotates folders as list[str] and iterates it (a
    # string is then iterated character by character). This pins the current call
    # shape; the string-vs-list mismatch is a source bug.
    assert kw['folders'] == 'Spada'
    # The stale folder created by the failed Zenodo attempt was cleared by rmtree.
    assert not (tracks_dir / 'Spada').exists()


def test_download_tracks_spada_clears_partial_download(monkeypatch, tmp_path):
    """A non-empty partial folder from a failed Zenodo attempt is cleared, not crashed on."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    _patch_osf(monkeypatch)

    def failing_zenodo(*, folder, data_dir):
        # zenodo_get can exit non-zero after writing partial files, so the folder
        # is NOT empty when the failure handler cleans it up. rmdir would raise
        # OSError on a non-empty directory; shutil.rmtree clears it.
        d = data_dir / folder
        d.mkdir(parents=True, exist_ok=True)
        (d / 'partial.tmp').write_text('half a track')
        raise data.subprocess.CalledProcessError(1, ['zenodo_get'])

    def failing_osf(*, storage, folders, data_dir):
        raise RuntimeError('osf down')

    monkeypatch.setattr(data, 'download_zenodo_folder', failing_zenodo)
    monkeypatch.setattr(data, 'download_OSF_folder', failing_osf)
    monkeypatch.setattr(data, 'sleep', lambda s: None)

    # Must not raise: on the buggy rmdir this propagates OSError('Directory not
    # empty') out of _download_spada, so the call itself discriminates the fix.
    result = data.DownloadEvolutionTracks('Spada')
    assert result is None
    # The partial folder was removed, so a retry can recreate it cleanly.
    assert not (tmp_path / 'stellar_evolution_tracks' / 'Spada').exists()


def test_download_tracks_spada_both_fail_retries_then_gives_up(monkeypatch, tmp_path):
    """Both Spada downloaders failing triggers one retry with a back-off, then gives up."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    _patch_osf(monkeypatch)

    zenodo_attempts = {'n': 0}
    osf_calls = {'n': 0, 'folders': None}

    def failing_zenodo(*, folder, data_dir):
        zenodo_attempts['n'] += 1
        (data_dir / folder).mkdir(parents=True, exist_ok=True)
        # The real failure type (non-zero zenodo_get exit), not RuntimeError.
        raise data.subprocess.CalledProcessError(1, ['zenodo_get'])

    def failing_osf(*, storage, folders, data_dir):
        # Record the call shape before failing so a signature drift in the
        # fallback path is caught even when the download itself errors out.
        osf_calls['n'] += 1
        osf_calls['folders'] = folders
        raise RuntimeError('osf down')

    monkeypatch.setattr(data, 'download_zenodo_folder', failing_zenodo)
    monkeypatch.setattr(data, 'download_OSF_folder', failing_osf)

    sleeps = []
    monkeypatch.setattr(data, 'sleep', lambda s: sleeps.append(s))

    # No exception is raised; the function logs the failure and returns.
    result = data.DownloadEvolutionTracks('Spada')

    assert result is None
    # Two attempts are made (max_tries == 2); the first failure triggers a back-off.
    assert zenodo_attempts['n'] == 2
    # The OSF fallback is tried on each of the two attempts.
    assert osf_calls['n'] == 2
    # Present behaviour: the folder name reaches the fallback as a bare string
    # (see test_download_tracks_spada_zenodo_fails_osf_fallback); this pins that shape.
    assert osf_calls['folders'] == 'Spada'
    # Exactly one back-off sleep occurs between the two attempts, and it is positive.
    assert len(sleeps) == 1
    assert sleeps[0] > 0


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

    monkeypatch.setattr(data, '_baraffe_fetcher', lambda: _StaleFetcher)
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
        data._baraffe_dataset()
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
        data._baraffe_dataset()
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
    assert data._baraffe_dataset().key == 'star.tracks.baraffe_2015'

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

    hashed = {path.resolve() for pattern in patterns for path in repo_root.glob(pattern)}
    dataset = data._baraffe_dataset()
    manifest = data.manifest_path().resolve()
    registry = dataset.registry_path.resolve()
    # The Zenodo pin lives in the manifest, so a re-pin has to move the key.
    assert manifest in hashed
    # The per-file checksums live in the registry, so a re-sync has to move it too.
    assert registry in hashed
    # Nothing else: an over-broad pattern would bust the cache on edits that
    # leave the data untouched, which costs a full refetch from a single mirror.
    assert hashed == {manifest, registry}


def test_manifest_path_loads_baraffe_dataset():
    """The shipped MORS manifest declares Baraffe under the new versioned layout."""
    from fwl_io import load_manifest

    datasets = {ds.key: ds for ds in load_manifest(data.manifest_path())}
    # The manifest declares exactly the Baraffe dataset (Spada is not fwl-io yet).
    assert set(datasets) == {'star.tracks.baraffe_2015'}
    baraffe = datasets['star.tracks.baraffe_2015']
    # The location is the key spelled as a path, and it is the directory the
    # tracks already live in, so this migration moves no user data.
    assert baraffe.subdir == 'star/tracks/baraffe_2015'
    assert baraffe.zenodo == '10.5281/zenodo.15729114'
    # MORS is the declared consumer, so fwl-io routes the fetch to it.
    assert 'mors' in baraffe.required_by


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


def test_mors_manifest_is_discovered_via_entry_point():
    """fwl-io discovers the MORS manifest through the fwl_io.manifests entry point."""
    from fwl_io import discover_manifests

    found = discover_manifests()
    # A typo in the entry-point name or target would drop MORS from discovery.
    assert 'mors' in found, 'MORS manifest is not registered under fwl_io.manifests'
    keys = {ds.key for ds in found['mors']}
    assert keys == {'star.tracks.baraffe_2015'}
