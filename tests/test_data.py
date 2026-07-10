"""Tests for src/mors/data.py: stellar evolution track download plumbing.

Covers the Zenodo record lookup, the Zenodo and OSF folder downloaders, and
the DownloadEvolutionTracks orchestrator (Spada untar path, Baraffe path, the
already-present short-circuit, the unknown-name error contract, and the
retry / fallback ladder). All network and filesystem download side effects are
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


def test_get_zenodo_record_known_and_unknown():
    """The Zenodo map returns the pinned record id for known folders, None otherwise."""
    # Known folders resolve to their published Zenodo record ids (strings).
    assert data.get_zenodo_record('Baraffe') == '15729114'
    assert data.get_zenodo_record('Spada') == '15729101'
    # The two records must be distinct, else a wrong-folder bug would go unnoticed.
    assert data.get_zenodo_record('Baraffe') != data.get_zenodo_record('Spada')
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

    data.download_OSF_folder(
        storage=storage, folders=['Spada', 'Baraffe'], data_dir=tmp_path
    )

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


def test_download_tracks_short_circuit_when_present(monkeypatch, tmp_path):
    """Existing track folders are not re-downloaded; both defaults short-circuit."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    _patch_osf(monkeypatch)

    # Pre-create both track folders so the existence guard skips downloading.
    base = tmp_path / 'stellar_evolution_tracks'
    (base / 'Spada').mkdir(parents=True)
    (base / 'Baraffe').mkdir(parents=True)

    calls = {'zenodo': 0, 'osf': 0}
    monkeypatch.setattr(
        data, 'download_zenodo_folder',
        lambda **k: calls.__setitem__('zenodo', calls['zenodo'] + 1),
    )
    monkeypatch.setattr(
        data, 'download_OSF_folder',
        lambda **k: calls.__setitem__('osf', calls['osf'] + 1),
    )

    # Empty fname takes the both-folders branch; both already exist.
    data.DownloadEvolutionTracks('')

    # Neither downloader is invoked because both folders are already on disk.
    assert calls['zenodo'] == 0
    assert calls['osf'] == 0


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


def test_download_tracks_baraffe_no_untar(monkeypatch, tmp_path):
    """The Baraffe path downloads without triggering the Spada-only untar step."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    _patch_osf(monkeypatch)

    base = tmp_path / 'stellar_evolution_tracks'

    def fake_zenodo(*, folder, data_dir):
        (data_dir / folder).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(data, 'download_zenodo_folder', fake_zenodo)

    subcalls = []
    monkeypatch.setattr(data.subprocess, 'call', lambda cmd: subcalls.append(cmd))

    data.DownloadEvolutionTracks('Baraffe')

    # The Baraffe folder is populated.
    assert (base / 'Baraffe').is_dir()
    # No tar / rm commands run for Baraffe (untar is Spada-specific).
    assert subcalls == []


def test_download_tracks_zenodo_fails_osf_fallback(monkeypatch, tmp_path):
    """When Zenodo fails, the OSF fallback runs and the attempt is marked successful."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    _patch_osf(monkeypatch)

    def failing_zenodo(*, folder, data_dir):
        # Real code creates the folder before failing; rmdir on cleanup needs it.
        (data_dir / folder).mkdir(parents=True, exist_ok=True)
        raise RuntimeError('zenodo unreachable')

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

    data.DownloadEvolutionTracks('Baraffe')

    # The OSF fallback ran exactly once after the single Zenodo failure.
    assert osf_calls['n'] == 1
    kw = osf_calls['kwargs']
    tracks_dir = tmp_path / 'stellar_evolution_tracks'
    # The fallback receives the OSF storage handle opened from the project, so a
    # rename of the storage keyword would surface here.
    assert kw['storage'] is _FakeOSF.storage_obj
    # The download target is the shared tracks directory, not a per-folder subdir.
    assert kw['data_dir'] == tracks_dir
    # Present behaviour: DownloadEvolutionTracks passes the folder name as a bare
    # string, while download_OSF_folder annotates folders as list[str] and
    # iterates it (a string is then iterated character by character). This pins
    # the current call shape; the string-vs-list mismatch is a source bug.
    assert kw['folders'] == 'Baraffe'
    # The stale folder created by the failed Zenodo attempt was removed by rmdir.
    assert not (tracks_dir / 'Baraffe').exists()


def test_download_tracks_both_fail_retries_then_gives_up(monkeypatch, tmp_path):
    """Both downloaders failing triggers one retry with a back-off, then gives up."""
    monkeypatch.setattr(data, 'FWL_DATA_DIR', tmp_path, raising=False)
    _patch_osf(monkeypatch)

    zenodo_attempts = {'n': 0}
    osf_calls = {'n': 0, 'folders': None}

    def failing_zenodo(*, folder, data_dir):
        zenodo_attempts['n'] += 1
        (data_dir / folder).mkdir(parents=True, exist_ok=True)
        raise RuntimeError('zenodo down')

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
    result = data.DownloadEvolutionTracks('Baraffe')

    assert result is None
    # Two attempts are made (max_tries == 2); the first failure triggers a back-off.
    assert zenodo_attempts['n'] == 2
    # The OSF fallback is tried on each of the two attempts.
    assert osf_calls['n'] == 2
    # Present behaviour: the folder name reaches the fallback as a bare string
    # (see test_download_tracks_zenodo_fails_osf_fallback); this pins that shape.
    assert osf_calls['folders'] == 'Baraffe'
    # Exactly one back-off sleep occurs between the two attempts, and it is positive.
    assert len(sleeps) == 1
    assert sleeps[0] > 0
