"""Tests for src/mors/logs.py.

Exercises the terminal-logger setup: the ``fwl`` logger name, the level
parsing and validation contract, the single stdout stream handler, the
idempotent handler reset on repeated setup, and the uncaught-exception hook
that routes ``KeyboardInterrupt`` to the default hook and every other
exception to a critical log record.

logs.py is a utility source (logger plumbing, no physical quantity), so the
physics-invariant requirement does not apply; the anti-happy-path rules do.
"""

from __future__ import annotations

import logging
import sys

import pytest

from mors import logs

pytestmark = [pytest.mark.unit, pytest.mark.timeout(30)]


@pytest.fixture
def restore_excepthook():
    """Save and restore ``sys.excepthook`` so setup_logger cannot leak state.

    setup_logger rebinds the interpreter-global ``sys.excepthook``; without
    this guard a test would replace the runner's hook for the whole session.
    """
    saved = sys.excepthook
    yield
    sys.excepthook = saved


@pytest.fixture(autouse=True)
def clear_fwl_handlers():
    """Reset the module-global ``fwl`` logger before and after each test.

    logging.getLogger returns a process-wide singleton, so handlers and the
    effective level persist across tests unless cleared; this keeps handler
    counts and level assertions independent of test ordering.
    """
    lg = logging.getLogger('fwl')
    lg.handlers.clear()
    lg.setLevel(logging.WARNING)
    yield
    lg.handlers.clear()
    lg.setLevel(logging.WARNING)


def test_setup_logger_returns_named_fwl_logger(restore_excepthook):
    """A configured logger is the shared 'fwl' instance, not a fresh object."""
    lg = logs.setup_logger('INFO')
    # The returned logger is the process-wide 'fwl' singleton.
    assert lg.name == 'fwl'
    assert lg is logging.getLogger('fwl')
    # A sibling logger under a different name is a distinct object, so the
    # name lookup is not returning an unrelated global.
    assert lg is not logging.getLogger('other')


def test_setup_logger_installs_single_stdout_stream_handler(restore_excepthook):
    """Setup attaches exactly one stdout StreamHandler at the chosen level."""
    lg = logs.setup_logger('DEBUG')
    assert len(lg.handlers) == 1
    handler = lg.handlers[0]
    assert isinstance(handler, logging.StreamHandler)
    # The handler writes to stdout, not stderr, and both the logger and its
    # handler sit at DEBUG.
    assert handler.stream is sys.stdout
    assert handler.level == logging.DEBUG
    assert lg.level == logging.DEBUG


def test_setup_logger_is_idempotent_on_handler_count(restore_excepthook):
    """Repeated setup clears prior handlers instead of stacking duplicates."""
    lg = logs.setup_logger('INFO')
    lg = logs.setup_logger('INFO')
    lg = logs.setup_logger('INFO')
    # Three setups, still one handler: each call clears before adding.
    assert len(lg.handlers) == 1
    assert isinstance(lg.handlers[0], logging.StreamHandler)


def test_setup_logger_reinit_switches_level(restore_excepthook):
    """A second setup at a different level re-points the logger and handler."""
    lg = logs.setup_logger('INFO')
    assert lg.level == logging.INFO
    lg = logs.setup_logger('ERROR')
    # Re-init moves both the logger and its single handler to the new level.
    assert lg.level == logging.ERROR
    assert lg.handlers[0].level == logging.ERROR
    assert len(lg.handlers) == 1


@pytest.mark.parametrize(
    'given,expected',
    [
        ('info', logging.INFO),
        ('  Debug  ', logging.DEBUG),
        ('WARNING', logging.WARNING),
        ('error', logging.ERROR),
    ],
)
def test_setup_logger_parses_case_and_whitespace(given, expected, restore_excepthook):
    """Level strings are upper-cased and stripped before lookup."""
    lg = logs.setup_logger(given)
    # Mixed case and surrounding whitespace resolve to the canonical code.
    assert lg.level == expected
    assert lg.handlers[0].level == expected


def test_setup_logger_default_level_is_info(restore_excepthook, caplog):
    """Calling with no argument selects INFO: INFO records pass, DEBUG records drop."""
    lg = logs.setup_logger()
    assert lg.level == logging.INFO
    # At the INFO level the logger emits an INFO record but drops a DEBUG one,
    # which distinguishes INFO from the more permissive DEBUG default. The
    # records reach caplog by propagation without altering the logger level.
    lg.debug('debug-line-should-be-filtered')
    lg.info('info-line-should-pass')
    messages = [rec.getMessage() for rec in caplog.records if rec.name == 'fwl']
    assert 'info-line-should-pass' in messages
    assert 'debug-line-should-be-filtered' not in messages


def test_setup_logger_rejects_unknown_level(restore_excepthook):
    """An unrecognised level raises ValueError and adds no handler."""
    lg = logging.getLogger('fwl')
    with pytest.raises(ValueError, match='Invalid log level'):
        logs.setup_logger('TRACE')
    # The guard fires before addHandler, so no handler leaks from the failed
    # call and the level is untouched from the fixture baseline.
    assert len(lg.handlers) == 0
    assert lg.level == logging.WARNING


def test_setup_logger_rejects_non_level_string(restore_excepthook):
    """A numeric-looking string that is not a named level is refused."""
    with pytest.raises(ValueError, match='Invalid log level'):
        logs.setup_logger('10')
    # 'CRITICAL' exists in the logging module but is outside the accepted set,
    # so the whitelist is stricter than getattr(logging, level) alone.
    with pytest.raises(ValueError, match='Invalid log level'):
        logs.setup_logger('CRITICAL')


def test_setup_logger_emits_at_and_above_level(restore_excepthook, capsys):
    """Records at or above the set level reach stdout; lower ones are dropped."""
    lg = logs.setup_logger('WARNING')
    lg.info('below-threshold-message')
    lg.warning('at-threshold-message')
    lg.error('above-threshold-message')
    out = capsys.readouterr().out
    # INFO is below WARNING and must be filtered; WARNING and ERROR pass.
    assert 'below-threshold-message' not in out
    assert 'at-threshold-message' in out
    assert 'above-threshold-message' in out


def test_excepthook_routes_regular_exception_to_critical(restore_excepthook, caplog):
    """A non-KeyboardInterrupt exception is logged at CRITICAL with traceback."""
    logs.setup_logger('DEBUG')
    try:
        raise ValueError('synthetic-failure')
    except ValueError:
        exc_type, exc_value, exc_tb = sys.exc_info()
    with caplog.at_level(logging.DEBUG, logger='fwl'):
        sys.excepthook(exc_type, exc_value, exc_tb)
    records = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    # Exactly one CRITICAL record carrying the 'Uncaught exception' message and
    # attached exception info for the traceback.
    assert len(records) == 1
    assert 'Uncaught exception' in records[0].getMessage()
    assert records[0].exc_info is not None
    assert records[0].exc_info[0] is ValueError


def test_excepthook_handles_keyboard_interrupt_separately(restore_excepthook, caplog):
    """KeyboardInterrupt logs an error and defers to the default hook."""
    logs.setup_logger('DEBUG')
    called = {}

    def fake_default_hook(exc_type, exc_value, exc_tb):
        called['type'] = exc_type

    original_default = sys.__excepthook__
    sys.__excepthook__ = fake_default_hook
    try:
        exc = KeyboardInterrupt()
        with caplog.at_level(logging.DEBUG, logger='fwl'):
            sys.excepthook(KeyboardInterrupt, exc, None)
    finally:
        sys.__excepthook__ = original_default

    # The interrupt branch logs 'KeyboardInterrupt' at ERROR, delegates to the
    # standard hook, and never emits the CRITICAL 'Uncaught exception' record.
    messages = [r.getMessage() for r in caplog.records]
    assert 'KeyboardInterrupt' in messages
    assert called.get('type') is KeyboardInterrupt
    assert not any(m == 'Uncaught exception' for m in messages)


def test_excepthook_keyboard_interrupt_subclass_uses_interrupt_branch(
    restore_excepthook, caplog
):
    """A KeyboardInterrupt subclass still takes the interrupt branch (issubclass)."""
    logs.setup_logger('DEBUG')

    class NestedInterrupt(KeyboardInterrupt):
        pass

    calls = {'count': 0}

    def fake_default_hook(exc_type, exc_value, exc_tb):
        calls['count'] += 1

    original_default = sys.__excepthook__
    sys.__excepthook__ = fake_default_hook
    try:
        with caplog.at_level(logging.DEBUG, logger='fwl'):
            sys.excepthook(NestedInterrupt, NestedInterrupt(), None)
    finally:
        sys.__excepthook__ = original_default

    # issubclass, not identity, selects the branch: the subclass is treated as
    # an interrupt (ERROR + delegate), not as a generic uncaught exception.
    critical = [r for r in caplog.records if r.levelno == logging.CRITICAL]
    assert calls['count'] == 1
    assert len(critical) == 0
