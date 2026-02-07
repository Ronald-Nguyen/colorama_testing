import builtins
import contextlib
import ctypes
import importlib
import sys
from io import StringIO
from unittest.mock import Mock, patch

import pytest

from colorama import ansi
from colorama import ansitowin32
from colorama import initialise
import colorama.win32 as win32
import colorama.winterm as winterm


class FakeKernel32:
    def __init__(self):
        def stub(*_args, **_kwargs):
            return 1

        self.GetStdHandle = stub
        self.GetConsoleScreenBufferInfo = stub
        self.SetConsoleTextAttribute = stub
        self.SetConsoleCursorPosition = stub
        self.FillConsoleOutputCharacterA = stub
        self.FillConsoleOutputAttribute = stub
        self.SetConsoleTitleW = stub
        self.GetConsoleMode = stub
        self.SetConsoleMode = stub


@contextlib.contextmanager
def fake_windows_modules():
    original_windll = getattr(ctypes, "WinDLL", None)
    original_winerror = getattr(ctypes, "WinError", None)
    kernel32 = FakeKernel32()

    def fake_windll(_):
        return kernel32

    def fake_winerror(*_args, **_kwargs):
        return OSError("winerror")

    setattr(ctypes, "WinDLL", fake_windll)
    setattr(ctypes, "WinError", fake_winerror)
    try:
        win32_reloaded = importlib.reload(win32)
        winterm_reloaded = importlib.reload(winterm)
        yield win32_reloaded, winterm_reloaded
    finally:
        if original_windll is None:
            if hasattr(ctypes, "WinDLL"):
                delattr(ctypes, "WinDLL")
        else:
            setattr(ctypes, "WinDLL", original_windll)
        if original_winerror is None:
            if hasattr(ctypes, "WinError"):
                delattr(ctypes, "WinError")
        else:
            setattr(ctypes, "WinError", original_winerror)
        importlib.reload(win32)
        importlib.reload(winterm)


@contextlib.contextmanager
def reload_winterm_without_msvcrt():
    original_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "msvcrt":
            raise ImportError("msvcrt unavailable")
        return original_import(name, *args, **kwargs)

    builtins.__import__ = fake_import
    try:
        reloaded = importlib.reload(winterm)
        yield reloaded
    finally:
        builtins.__import__ = original_import
        importlib.reload(winterm)


def assert_equal(actual, expected, message=""):
    if actual != expected:
        raise AssertionError(message or f"{actual!r} != {expected!r}")


def assert_in(member, container, message=""):
    if member not in container:
        raise AssertionError(message or f"{member!r} not found in container")


def assert_is(actual, expected, message=""):
    if actual is not expected:
        raise AssertionError(message or f"{actual!r} is not {expected!r}")


def assert_true(condition, message=""):
    if not condition:
        raise AssertionError(message or "Expected condition to be true")


def test_ansi_helpers_and_cursor():
    assert_equal(ansi.code_to_chars(5), "\033[5m")
    assert_equal(ansi.set_title("title"), "\033]2;title\a")
    assert_equal(ansi.clear_screen(1), "\033[1J")
    assert_equal(ansi.clear_line(1), "\033[1K")
    cursor = ansi.AnsiCursor()
    assert_equal(cursor.UP(2), "\033[2A")
    assert_equal(cursor.DOWN(3), "\033[3B")
    assert_equal(cursor.FORWARD(4), "\033[4C")
    assert_equal(cursor.BACK(5), "\033[5D")
    assert_equal(cursor.POS(2, 3), "\033[3;2H")


def test_ansitowin32_state_and_calls():
    wrapper = ansitowin32.StreamWrapper(Mock(), Mock())
    wrapper.__setstate__({"value": 1})
    assert_equal(wrapper.__getstate__()["value"], 1)

    wrapped = Mock()
    wrapped.closed = False
    wrapped.isatty.return_value = True
    stream = ansitowin32.AnsiToWin32(wrapped)
    stream.strip = False
    stream.convert = False
    stream.reset_all()

    stream.call_win32 = Mock()
    stream.convert = True
    stream.reset_all()
    stream.call_win32.assert_called_with("m", (0,))

    assert_equal(stream.extract_params("H", "2"), (2, 1))
    assert_equal(stream.extract_params("A", ""), (1,))

    call_wrapped = Mock()
    call_wrapped.closed = False
    call_wrapped.isatty.return_value = True
    call_stream = ansitowin32.AnsiToWin32(call_wrapped)
    fake_term = Mock()
    with patch.object(ansitowin32, "winterm", fake_term):
        call_stream.win32_calls = {}
        call_stream.call_win32("J", (2,))
        call_stream.call_win32("K", (1,))
        call_stream.call_win32("H", (3, 4))
        call_stream.call_win32("A", (2,))

    with patch.object(ansitowin32, "winterm", Mock()):
        stream.convert = True
        calls = stream.get_win32_calls()
        assert_in(ansitowin32.AnsiStyle.RESET_ALL, calls)

    stream.wrapped = Mock()
    stream.flush()


def test_ansitowin32_initializes_winterm_with_windll():
    class DummyWinTerm:
        pass

    with patch.object(win32, "windll", object()), patch.object(winterm, "WinTerm", DummyWinTerm):
        reloaded = importlib.reload(ansitowin32)
        assert_true(isinstance(reloaded.winterm, DummyWinTerm))
    importlib.reload(ansitowin32)


def test_initialise_paths():
    initialise._wipe_internal_state_for_tests()
    reset_call = Mock()

    class DummyAnsiToWin32:
        def __init__(self, _stream):
            pass

        def reset_all(self):
            reset_call()

    initialise.orig_stdout = object()
    with patch("colorama.initialise.AnsiToWin32", DummyAnsiToWin32):
        initialise.reset_all()
    reset_call.assert_called_once()

    with pytest.raises(ValueError):
        initialise.init(autoreset=True, wrap=False)

    saved_stdout = sys.stdout
    saved_stderr = sys.stderr
    try:
        sys.stdout = None
        sys.stderr = None
        with patch("colorama.initialise.atexit.register") as register:
            initialise.init()
            register.assert_called_once()
    finally:
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr
        initialise._wipe_internal_state_for_tests()

    dummy_stdout = StringIO()
    dummy_stderr = StringIO()
    with patch("colorama.initialise.atexit.register") as register, patch(
        "colorama.initialise.wrap_stream", side_effect=lambda stream, *_args, **_kwargs: stream
    ):
        sys.stdout = dummy_stdout
        sys.stderr = dummy_stderr
        initialise.init()
        register.assert_called_once()
        initialise.deinit()
    sys.stdout = saved_stdout
    sys.stderr = saved_stderr

    initialise.wrapped_stdout = dummy_stdout
    initialise.wrapped_stderr = dummy_stderr
    sys.stdout = saved_stdout
    sys.stderr = saved_stderr
    initialise.reinit()
    assert_is(sys.stdout, dummy_stdout)
    assert_is(sys.stderr, dummy_stderr)
    sys.stdout = saved_stdout
    sys.stderr = saved_stderr

    with patch("colorama.initialise.init") as init_mock, patch(
        "colorama.initialise.deinit"
    ) as deinit_mock:
        with initialise.colorama_text():
            pass
    init_mock.assert_called_once()
    deinit_mock.assert_called_once()

    class DummyWrapper:
        def __init__(self, _stream, **_kwargs):
            self.stream = "wrapped"

        def should_wrap(self):
            return True

    with patch("colorama.initialise.AnsiToWin32", DummyWrapper):
        assert_equal(initialise.wrap_stream("stream", None, None, False, True), "wrapped")


def test_just_fix_windows_console_paths():
    saved_stdout = sys.stdout
    saved_stderr = sys.stderr
    try:
        with patch("colorama.initialise.sys.platform", "win32"):
            initialise._wipe_internal_state_for_tests()
            initialise.fixed_windows_console = True
            initialise.just_fix_windows_console()

            initialise._wipe_internal_state_for_tests()
            initialise.wrapped_stdout = object()
            initialise.just_fix_windows_console()

            initialise._wipe_internal_state_for_tests()
            stdout = Mock()
            stdout.closed = False
            stdout.isatty.return_value = True
            stdout.fileno.return_value = 1
            stderr = Mock()
            stderr.closed = False
            stderr.isatty.return_value = True
            stderr.fileno.return_value = 2
            sys.stdout = stdout
            sys.stderr = stderr
            new_stdout = Mock(convert=True)
            new_stderr = Mock(convert=True)
            with patch("colorama.initialise.AnsiToWin32", side_effect=[new_stdout, new_stderr]):
                initialise.just_fix_windows_console()
            assert_is(sys.stdout, new_stdout)
            assert_is(sys.stderr, new_stderr)
            assert_true(initialise.fixed_windows_console)
    finally:
        sys.stdout = saved_stdout
        sys.stderr = saved_stderr
        initialise._wipe_internal_state_for_tests()


def test_win32_api_wrappers_and_console_info():
    with fake_windows_modules() as (fake_win32, _fake_winterm):
        info = fake_win32.CONSOLE_SCREEN_BUFFER_INFO()
        info.dwSize.X = 10
        info.dwSize.Y = 20
        info.dwCursorPosition.X = 3
        info.dwCursorPosition.Y = 4
        info.wAttributes = 7
        info.srWindow.Top = 1
        info.srWindow.Left = 2
        info.srWindow.Bottom = 3
        info.srWindow.Right = 4
        info.dwMaximumWindowSize.X = 30
        info.dwMaximumWindowSize.Y = 40
        assert_true(str(info))

        fake_win32._GetStdHandle = Mock(side_effect=lambda handle: handle)

        def fake_get_csbi(_handle, csbi_ptr):
            csbi = csbi_ptr._obj
            csbi.dwSize.X = 10
            csbi.dwSize.Y = 5
            csbi.dwCursorPosition.X = 2
            csbi.dwCursorPosition.Y = 3
            csbi.wAttributes = 7
            csbi.srWindow.Top = 1
            csbi.srWindow.Left = 1
            csbi.srWindow.Bottom = 4
            csbi.srWindow.Right = 5
            csbi.dwMaximumWindowSize.X = 8
            csbi.dwMaximumWindowSize.Y = 9
            return 1

        fake_win32._GetConsoleScreenBufferInfo = fake_get_csbi
        fake_win32._SetConsoleTextAttribute = Mock(return_value=True)
        fake_win32._SetConsoleCursorPosition = Mock(return_value=True)

        def fake_fill_character(_handle, _char, length, _start, num_written):
            num_written._obj.value = length.value
            return 1

        def fake_fill_attribute(_handle, _attr, length, _start, num_written):
            num_written._obj.value = length.value
            return 1

        fake_win32._FillConsoleOutputCharacterA = fake_fill_character
        fake_win32._FillConsoleOutputAttribute = fake_fill_attribute
        fake_win32._SetConsoleTitleW = Mock(return_value=True)

        def fake_get_mode(_handle, mode_ptr):
            mode_ptr._obj.value = 1
            return 1

        fake_win32._GetConsoleMode = fake_get_mode
        fake_win32._SetConsoleMode = Mock(return_value=True)

        assert_true(fake_win32._winapi_test(123))
        assert_true(fake_win32.winapi_test())
        csbi = fake_win32.GetConsoleScreenBufferInfo(fake_win32.STDOUT)
        assert_equal(csbi.dwSize.X, 10)
        assert_true(fake_win32.SetConsoleTextAttribute(fake_win32.STDOUT, 7))
        fake_win32.SetConsoleCursorPosition(fake_win32.STDOUT, (2, 3))
        assert_is(fake_win32.SetConsoleCursorPosition(fake_win32.STDOUT, (0, 0)), None)
        assert_equal(
            fake_win32.FillConsoleOutputCharacter(
                fake_win32.STDOUT, "X", 5, fake_win32.COORD(0, 0)
            ),
            5,
        )
        assert_equal(
            fake_win32.FillConsoleOutputAttribute(
                fake_win32.STDOUT, 7, 5, fake_win32.COORD(0, 0)
            ),
            1,
        )
        fake_win32.SetConsoleTitle("title")
        assert_equal(fake_win32.GetConsoleMode(123), 1)
        fake_win32.SetConsoleMode(123, 1)

        fake_win32._GetConsoleMode = lambda _handle, _mode_ptr: 0
        with pytest.raises(OSError):
            fake_win32.GetConsoleMode(123)

        fake_win32._SetConsoleMode = lambda _handle, _mode: 0
        with pytest.raises(OSError):
            fake_win32.SetConsoleMode(123, 1)


def test_winterm_behavior_and_vt_processing():
    if winterm.get_osfhandle.__module__ == "msvcrt":
        assert_true(winterm.get_osfhandle(1) is not None)
    else:
        with pytest.raises(OSError):
            winterm.get_osfhandle(1)
    assert_is(winterm.enable_vt_processing(1), False)

    with reload_winterm_without_msvcrt() as reloaded:
        with pytest.raises(OSError):
            reloaded.get_osfhandle(1)

    with fake_windows_modules() as (fake_win32, fake_winterm):
        csbi = fake_win32.CONSOLE_SCREEN_BUFFER_INFO()
        csbi.dwSize.X = 10
        csbi.dwSize.Y = 5
        csbi.dwCursorPosition.X = 2
        csbi.dwCursorPosition.Y = 3
        csbi.wAttributes = 7
        csbi.srWindow.Top = 1
        csbi.srWindow.Left = 1
        csbi.srWindow.Bottom = 4
        csbi.srWindow.Right = 5
        fake_win32.GetConsoleScreenBufferInfo = Mock(return_value=csbi)
        fake_win32.SetConsoleTextAttribute = Mock()
        fake_win32.SetConsoleCursorPosition = Mock()
        fake_win32.FillConsoleOutputCharacter = Mock()
        fake_win32.FillConsoleOutputAttribute = Mock()
        fake_win32.SetConsoleTitle = Mock()

        term = fake_winterm.WinTerm()
        term.fore(light=False)
        term.fore(light=True)
        term.back(light=False)
        term.back(light=True)
        term.style()
        term.get_position(fake_win32.STDOUT)
        term.set_cursor_position()
        term.set_cursor_position((1, 1), on_stderr=True)
        term.cursor_adjust(1, 2, on_stderr=True)
        term.erase_screen(0)
        term.erase_screen(0, on_stderr=True)
        term.erase_screen(1)
        term.erase_screen(2)
        term.erase_screen(3)
        term.erase_line(0)
        term.erase_line(0, on_stderr=True)
        term.erase_line(1)
        term.erase_line(2)
        term.erase_line(3)
        term.set_title("title")

        fake_win32.winapi_test = Mock(return_value=True)
        fake_winterm.get_osfhandle = Mock(return_value=123)
        modes = [0, fake_win32.ENABLE_VIRTUAL_TERMINAL_PROCESSING]

        def fake_get_console_mode(_handle):
            return modes.pop(0)

        fake_win32.GetConsoleMode = Mock(side_effect=fake_get_console_mode)
        fake_win32.SetConsoleMode = Mock()
        assert_is(fake_winterm.enable_vt_processing(1), True)

        fake_winterm.get_osfhandle = Mock(side_effect=OSError("bad handle"))
        assert_is(fake_winterm.enable_vt_processing(1), False)
