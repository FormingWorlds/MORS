"""Unit tests for the compiled-grid cache in src/mors/stellarevo.py.

Covers the cache key (location outside the track directory, sensitivity to
the tracks' own content, realpath normalisation of a symlinked directory),
concurrent compilation of the same grid, and recovery from a corrupt cache
file. All track reads are stubbed, so nothing here needs real Spada or
Baraffe data and every test stays fast enough for the unit tier.
"""

from __future__ import annotations

import logging
import multiprocessing
import os
import pickle
import time

import numpy as np
import pytest

import mors.stellarevo as se

pytestmark = [pytest.mark.unit, pytest.mark.timeout(60)]


def _make_track_dir(tmp_path, name='tracks', n_files=3):
    track_dir = tmp_path / name
    track_dir.mkdir()
    for i in range(n_files):
        (track_dir / f'file{i}.track1').write_text(f'line {i}\n')
    return track_dir


def _fake_track(starEvoDir, evoModels, Mstar, MstarFilenameMiddle, *, delay=0.0, n=64):
    if delay:
        time.sleep(delay)
    return {
        'Mstar': Mstar,
        'Age': np.arange(n, dtype=float),
        'Lbol': np.full(n, Mstar),
    }


def _fake_track_large(starEvoDir, evoModels, Mstar, MstarFilenameMiddle):
    n = 300000
    return {
        'Mstar': Mstar,
        'Age': np.arange(n, dtype=float),
        'Lbol': np.full(n, Mstar),
    }


def _concurrent_compile_worker(track_dir, cache_root, evoModels, log_path):
    """Runs in its own OS process: real parallel writers, not GIL-serialized threads.

    A thread-based version of this test cannot reproduce the shared-temp-file
    collision: CPython's GIL keeps the open/write/replace sequence for a small
    payload inside one scheduler quantum too reliably. Separate processes, as
    in the reported failure (an array job on a cold cache), do collide.
    """
    se.platformdirs.user_cache_dir = lambda *_a, **_k: cache_root
    se._ReadEvolutionTrack = _fake_track_large

    handler = logging.FileHandler(log_path)
    se.log.addHandler(handler)
    se.log.setLevel(logging.WARNING)
    try:
        se._CompileNewGrid(track_dir, evoModels)
    finally:
        se.log.removeHandler(handler)
        handler.close()


def test_grid_cache_file_lives_outside_track_dir(tmp_path, monkeypatch):
    """The compiled-grid cache path sits under the cache root, not the track directory."""
    cache_root = tmp_path / 'cache'
    monkeypatch.setattr(se.platformdirs, 'user_cache_dir', lambda *_a, **_k: str(cache_root))

    track_dir = _make_track_dir(tmp_path)
    cache_file = se._gridCacheFile(track_dir, 'evoA')

    assert str(cache_root) in cache_file
    assert str(track_dir) not in cache_file


def test_grid_cache_key_differs_for_different_track_trees(tmp_path, monkeypatch):
    """A change to the tracks' own content changes the cache key, not just the path."""
    cache_root = tmp_path / 'cache'
    monkeypatch.setattr(se.platformdirs, 'user_cache_dir', lambda *_a, **_k: str(cache_root))

    track_dir = _make_track_dir(tmp_path, name='tracks')
    key_before = se._gridCacheFile(track_dir, 'evoA')

    # Same path, different content: a track file changes size.
    (track_dir / 'file0.track1').write_text('a longer replacement line\n')
    key_after = se._gridCacheFile(track_dir, 'evoA')

    assert key_before != key_after
    assert key_before.startswith(str(cache_root))
    assert key_after.startswith(str(cache_root))


def test_grid_cache_key_same_through_symlink(tmp_path, monkeypatch):
    """A symlinked track directory shares one cache entry with its real target."""
    cache_root = tmp_path / 'cache'
    monkeypatch.setattr(se.platformdirs, 'user_cache_dir', lambda *_a, **_k: str(cache_root))

    real_dir = _make_track_dir(tmp_path, name='real_tracks')
    link_dir = tmp_path / 'linked_tracks'
    link_dir.symlink_to(real_dir)

    key_real = se._gridCacheFile(real_dir, 'evoA')
    key_link = se._gridCacheFile(link_dir, 'evoA')

    assert key_real == key_link
    assert key_real.startswith(str(cache_root))


def test_concurrent_compiles_of_same_grid_produce_one_loadable_grid(tmp_path, monkeypatch):
    """Several OS processes compiling the same grid at once leave one complete, loadable pickle."""
    cache_root = str(tmp_path / 'cache')
    track_dir = str(_make_track_dir(tmp_path))

    n_writers = 16
    log_paths = [str(tmp_path / f'writer{i}.log') for i in range(n_writers)]
    ctx = multiprocessing.get_context('spawn')
    procs = [
        ctx.Process(
            target=_concurrent_compile_worker, args=(track_dir, cache_root, 'evoA', log_path)
        )
        for log_path in log_paths
    ]
    for p in procs:
        p.start()
    for p in procs:
        p.join(timeout=45)

    assert all(p.exitcode == 0 for p in procs)

    warnings = []
    for log_path in log_paths:
        if os.path.exists(log_path):
            with open(log_path) as f:
                warnings.extend(line for line in f if line.strip())
    assert warnings == [], (
        f'a writer logged a warning while compiling the shared grid: {warnings}'
    )

    monkeypatch.setattr(se.platformdirs, 'user_cache_dir', lambda *_a, **_k: cache_root)
    monkeypatch.setattr(se, '_ReadEvolutionTrack', _fake_track_large)
    loaded = se._LoadSavedGrid(track_dir, 'evoA')
    assert len(loaded['MstarAll']) == 24
    for mstar in loaded['MstarAll']:
        assert mstar in loaded
        assert len(loaded[mstar]['Age']) == 300000


def test_corrupt_cache_file_is_replaced_by_a_fresh_compile(tmp_path, monkeypatch, caplog):
    """A truncated pickle triggers a warning and a full recompile, not a crash."""
    cache_root = tmp_path / 'cache'
    monkeypatch.setattr(se.platformdirs, 'user_cache_dir', lambda *_a, **_k: str(cache_root))
    monkeypatch.setattr(se, '_ReadEvolutionTrack', lambda *a: _fake_track(*a))

    track_dir = _make_track_dir(tmp_path)
    cache_file = se._gridCacheFile(track_dir, 'evoA')

    os.makedirs(os.path.dirname(cache_file), exist_ok=True)
    with open(cache_file, 'wb') as f:
        f.write(pickle.dumps({'MstarAll': np.array([0.1])})[:5])

    with caplog.at_level('WARNING'):
        loaded = se._LoadSavedGrid(track_dir, 'evoA')

    assert 'MstarAll' in loaded
    assert len(loaded['MstarAll']) == 24
    assert any('recompiling' in rec.message for rec in caplog.records)

    reloaded = pickle.load(open(cache_file, 'rb'))
    assert len(reloaded['MstarAll']) == 24
