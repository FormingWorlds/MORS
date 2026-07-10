from __future__ import annotations

import pytest
from click.testing import CliRunner

import mors.data
from mors.cli import cli

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]


def _record_download(monkeypatch):
    """Replace DownloadEvolutionTracks with a recorder returning a plausible path.

    Returns a list that captures the positional args each invocation received so
    tests can assert which track family was requested without touching the network.
    """
    calls = []

    def fake_download(*args, **kwargs):
        calls.append(args)
        return '/fake/fwl_data/stellar_evolution_tracks'

    monkeypatch.setattr(mors.data, 'DownloadEvolutionTracks', fake_download)
    return calls


def test_download_spada_requests_spada_family(monkeypatch):
    """`mors download spada` must trigger exactly one Spada-track download and succeed."""
    calls = _record_download(monkeypatch)
    result = CliRunner().invoke(cli, ['download', 'spada'])

    assert result.exit_code == 0
    assert calls == [('Spada',)]


def test_download_baraffe_requests_baraffe_family(monkeypatch):
    """`mors download baraffe` must trigger exactly one Baraffe-track download and succeed."""
    calls = _record_download(monkeypatch)
    result = CliRunner().invoke(cli, ['download', 'baraffe'])

    assert result.exit_code == 0
    assert calls == [('Baraffe',)]


def test_download_all_requests_every_family(monkeypatch):
    """`mors download all` calls the downloader with no family filter (both grids)."""
    calls = _record_download(monkeypatch)
    result = CliRunner().invoke(cli, ['download', 'all'])

    assert result.exit_code == 0
    # The bare call (no positional argument) is the contract for downloading every grid.
    assert calls == [()]


def test_env_reports_data_location(monkeypatch):
    """`mors env` echoes the configured FWL_DATA directory to stdout."""
    monkeypatch.setattr(mors.data, 'FWL_DATA_DIR', '/tmp/fwl_probe_dir', raising=False)
    result = CliRunner().invoke(cli, ['env'])

    assert result.exit_code == 0
    assert 'FWL_DATA location:' in result.output
    assert '/tmp/fwl_probe_dir' in result.output


def test_download_group_lists_subcommands():
    """Invoking the download group with no subcommand shows usage and exits cleanly."""
    result = CliRunner().invoke(cli, ['download', '--help'])

    assert result.exit_code == 0
    assert 'spada' in result.output
    assert 'baraffe' in result.output


def test_unknown_subcommand_is_usage_error():
    """An unregistered subcommand fails with a non-zero exit and a diagnostic message."""
    result = CliRunner().invoke(cli, ['download', 'no_such_track'])

    assert result.exit_code != 0
    assert 'no_such_track' in result.output or 'No such command' in result.output


def test_top_level_help_lists_groups():
    """The root group advertises both the download group and the env command."""
    result = CliRunner().invoke(cli, ['--help'])

    assert result.exit_code == 0
    assert 'download' in result.output
    assert 'env' in result.output
