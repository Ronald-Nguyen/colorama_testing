from io import StringIO
import sys
from unittest import TestCase, main
from unittest.mock import Mock, patch

from ..ansi import (
    BEL,
    CSI,
    OSC,
    AnsiBack,
    AnsiFore,
    AnsiStyle,
    Cursor,
    clear_line,
    clear_screen,
    code_to_chars,
    set_title,
)
from ..ansitowin32 import AnsiToWin32, StreamWrapper
from ..initialise import colorama_text, wrap_stream
from .utils import StreamNonTTY, StreamTTY, pycharm


EXCLUDED_CODES = {
    1,
    2,
    22,
    30,
    31,
    32,
    33,
    34,
    35,
    36,
    37,
    39,
    40,
    41,
    42,
    43,
    44,
    45,
    46,
    47,
    49,
    90,
    91,
    92,
    93,
    94,
    95,
    96,
    97,
    100,
    101,
    102,
    103,
    104,
    105,
    106,
    107,
}
CODE_TO_CHARS_CODES = [
    code for code in range(0, 150) if code not in EXCLUDED_CODES
][:106]
CLEAR_SCREEN_MODES = [0, 1, 2, 3, 4, 5, 6, 7]
CLEAR_LINE_MODES = [0, 1, 2, 3, 4, 5, 6, 7]
TITLE_CASES = [
    "",
    "Title",
    "Colorama",
    "Test 1",
    "Test-2",
    "title_with_underscores",
    "123",
    "MiXeD",
    "Symbols!@#",
    "Trailing ",
    " Leading",
    "Multi Word",
]
CURSOR_STEPS = [1, 2, 3, 4, 5, 6, 7, 8, 9]
CURSOR_POSITIONS = [1, 2, 3, 4, 5]

FORE_VALUES = [
    ("BLACK", 30),
    ("RED", 31),
    ("GREEN", 32),
    ("YELLOW", 33),
    ("BLUE", 34),
    ("MAGENTA", 35),
    ("CYAN", 36),
    ("WHITE", 37),
    ("RESET", 39),
    ("LIGHTBLACK_EX", 90),
    ("LIGHTRED_EX", 91),
    ("LIGHTGREEN_EX", 92),
    ("LIGHTYELLOW_EX", 93),
    ("LIGHTBLUE_EX", 94),
    ("LIGHTMAGENTA_EX", 95),
    ("LIGHTCYAN_EX", 96),
    ("LIGHTWHITE_EX", 97),
]
BACK_VALUES = [
    ("BLACK", 40),
    ("RED", 41),
    ("GREEN", 42),
    ("YELLOW", 43),
    ("BLUE", 44),
    ("MAGENTA", 45),
    ("CYAN", 46),
    ("WHITE", 47),
    ("RESET", 49),
    ("LIGHTBLACK_EX", 100),
    ("LIGHTRED_EX", 101),
    ("LIGHTGREEN_EX", 102),
    ("LIGHTYELLOW_EX", 103),
    ("LIGHTBLUE_EX", 104),
    ("LIGHTMAGENTA_EX", 105),
    ("LIGHTCYAN_EX", 106),
    ("LIGHTWHITE_EX", 107),
]
STYLE_VALUES = [
    ("BRIGHT", 1),
    ("DIM", 2),
    ("NORMAL", 22),
    ("RESET_ALL", 0),
]

M_PARAMS = [
    "",
    "0",
    "1",
    "2",
    "3",
    "4;5",
    "10;20;30",
    ";;",
    ";;1;;2;;",
    "007",
    "0;1;2;3",
    "5;0",
    "9;;",
    ";8",
    ";;9",
    "11;22;33;44",
    "100",
    "1;2;3;4;5",
    "200;300",
    "12;34;56;78;90",
]
M_EXPECTED = [
    (0,),
    (0,),
    (1,),
    (2,),
    (3,),
    (4, 5),
    (10, 20, 30),
    (0,),
    (1, 2),
    (7,),
    (0, 1, 2, 3),
    (5, 0),
    (9,),
    (8,),
    (9,),
    (11, 22, 33, 44),
    (100,),
    (1, 2, 3, 4, 5),
    (200, 300),
    (12, 34, 56, 78, 90),
]
J_PARAMS = ["", "0", "1", "2", "3", "4;5", ";;", "9;;10", ";8", "11;22;33"]
J_EXPECTED = [(0,), (0,), (1,), (2,), (3,), (4, 5), (0,), (9, 10), (8,), (11, 22, 33)]
K_PARAMS = ["", "0", "2", "5", "6;7", ";", ";;", "8;9;10", "12", ";13"]
K_EXPECTED = [(0,), (0,), (2,), (5,), (6, 7), (0,), (0,), (8, 9, 10), (12,), (13,)]
ABCD_PARAMS = ["", "1", "2", "5", "10", "0", "3;4", "7;8;9"]
ABCD_EXPECTED = [(1,), (1,), (2,), (5,), (10,), (0,), (3, 4), (7, 8, 9)]
HF_PARAMS = ["", "1", "2", "3;4", "5;", ";6", "7;8;9", "0;0", "10;20"]
HF_EXPECTED = [(1, 1), (1, 1), (2, 1), (3, 4), (5, 1), (1, 6), (7, 8, 9), (0, 0), (10, 20)]

OSC_CASES = [
    ("\033]0;Title\a", "", ["Title"]),
    ("before\033]0;Title\aafter", "beforeafter", ["Title"]),
    ("before\033]2;Next\aafter", "beforeafter", ["Next"]),
    ("before\033]1;Skip\aafter", "beforeafter", []),
    ("text\033]0;multi;semi\a", "text", []),
    ("text\033]0;Title", "text\033]0;Title", []),
    ("\033]2;Title\a suffix", " suffix", ["Title"]),
    ("prefix\033]0;Title\a", "prefix", ["Title"]),
    ("\033]2;\a", "", [""]),
    ("\033]3;Title\a", "", []),
    ("a\033]0;Title\a b\033]2;Other\a", "a b\033]2;Other\a", ["Title", "Other"]),
    ("a\033]0;Title\a\033]2;Other\a", "a\033]2;Other\a", ["Title", "Other"]),
    ("\033]0;Title\a\033]3;Skip\a", "\033]3;Skip\a", ["Title"]),
    ("X\033]0;Title\aY\033]1;Skip\aZ", "XY\033]1;Skip\aZ", ["Title"]),
    ("X\033]2;One\aY\033]2;Two\aZ", "XY\033]2;Two\a", ["One", "Two"]),
    ("X\033]2;One\aY\033]2;Two\a", "XY\033]2;Two\a", ["One", "Two"]),
    ("\033]0;Title\aX\033]0;Again\a", "X\033]0;Again\a", ["Title", "Again"]),
    ("No osc here", "No osc here", []),
    ("edge\033]0;Title\a\033]0;Again\aend", "edge\033]0;Again\a", ["Title", "Again"]),
    ("edge\033]1;Skip\a\033]2;Ok\aend", "edge\033]2;Ok\aen", ["Ok"]),
]


class CodeToCharsTest(TestCase):
    pass


def _make_code_to_chars_test(code):
    def test(self):
        self.assertEqual(code_to_chars(code), f"{CSI}{code}m")

    return test


for code in CODE_TO_CHARS_CODES:
    setattr(CodeToCharsTest, f"test_code_to_chars_{code}", _make_code_to_chars_test(code))


class ClearScreenTest(TestCase):
    pass


def _make_clear_screen_test(mode):
    def test(self):
        self.assertEqual(clear_screen(mode), f"{CSI}{mode}J")

    return test


for mode in CLEAR_SCREEN_MODES:
    setattr(ClearScreenTest, f"test_clear_screen_mode_{mode}", _make_clear_screen_test(mode))


class ClearLineTest(TestCase):
    pass


def _make_clear_line_test(mode):
    def test(self):
        self.assertEqual(clear_line(mode), f"{CSI}{mode}K")

    return test


for mode in CLEAR_LINE_MODES:
    setattr(ClearLineTest, f"test_clear_line_mode_{mode}", _make_clear_line_test(mode))


class SetTitleTest(TestCase):
    pass


def _make_set_title_test(title, index):
    def test(self):
        self.assertEqual(set_title(title), f"{OSC}2;{title}{BEL}")

    return test


for index, title in enumerate(TITLE_CASES):
    setattr(SetTitleTest, f"test_set_title_{index}", _make_set_title_test(title, index))


class CursorMovementTest(TestCase):
    pass


CURSOR_DIRECTIONS = {
    "up": ("UP", "A"),
    "down": ("DOWN", "B"),
    "forward": ("FORWARD", "C"),
    "back": ("BACK", "D"),
}


def _make_cursor_move_test(method_name, suffix, step):
    def test(self):
        method = getattr(Cursor, method_name)
        self.assertEqual(method(step), f"{CSI}{step}{suffix}")

    return test


for key, (method_name, suffix) in CURSOR_DIRECTIONS.items():
    for step in CURSOR_STEPS:
        setattr(
            CursorMovementTest,
            f"test_cursor_{key}_{step}",
            _make_cursor_move_test(method_name, suffix, step),
        )


class CursorPositionTest(TestCase):
    pass


def _make_cursor_pos_test(x, y):
    def test(self):
        self.assertEqual(Cursor.POS(x, y), f"{CSI}{y};{x}H")

    return test


for x in CURSOR_POSITIONS:
    for y in CURSOR_POSITIONS:
        setattr(CursorPositionTest, f"test_cursor_pos_{x}_{y}", _make_cursor_pos_test(x, y))


class AnsiForeValueTest(TestCase):
    pass


def _make_constant_test(cls, name, expected):
    def test(self):
        self.assertEqual(getattr(cls, name), expected)

    return test


for name, expected in FORE_VALUES:
    setattr(AnsiForeValueTest, f"test_fore_value_{name.lower()}", _make_constant_test(AnsiFore, name, expected))


class AnsiBackValueTest(TestCase):
    pass


for name, expected in BACK_VALUES:
    setattr(AnsiBackValueTest, f"test_back_value_{name.lower()}", _make_constant_test(AnsiBack, name, expected))


class AnsiStyleValueTest(TestCase):
    pass


for name, expected in STYLE_VALUES:
    setattr(AnsiStyleValueTest, f"test_style_value_{name.lower()}", _make_constant_test(AnsiStyle, name, expected))


class ExtractParamsTest(TestCase):
    pass


def _make_extract_params_test(command, paramstring, expected, index):
    def test(self):
        stream = AnsiToWin32(Mock())
        self.assertEqual(stream.extract_params(command, paramstring), expected)

    return test


extract_cases = []
extract_cases.extend([("m", param, expected) for param, expected in zip(M_PARAMS, M_EXPECTED)])
extract_cases.extend([("J", param, expected) for param, expected in zip(J_PARAMS, J_EXPECTED)])
extract_cases.extend([("K", param, expected) for param, expected in zip(K_PARAMS, K_EXPECTED)])
for command in "ABCD":
    extract_cases.extend([(command, param, expected) for param, expected in zip(ABCD_PARAMS, ABCD_EXPECTED)])
for command in ("H", "f"):
    extract_cases.extend([(command, param, expected) for param, expected in zip(HF_PARAMS, HF_EXPECTED)])


for index, (command, paramstring, expected) in enumerate(extract_cases):
    setattr(
        ExtractParamsTest,
        f"test_extract_params_{command.lower()}_{index}",
        _make_extract_params_test(command, paramstring, expected, index),
    )


class ConvertOscTest(TestCase):
    pass


def _make_convert_osc_test(text, expected_text, expected_titles, index):
    def test(self):
        stream = AnsiToWin32(Mock())
        with patch("colorama.ansitowin32.winterm") as winterm:
            result = stream.convert_osc(text)
            self.assertEqual(result, expected_text)
            self.assertEqual(
                [call.args[0] for call in winterm.set_title.call_args_list],
                expected_titles,
            )

    return test


for index, (text, expected_text, expected_titles) in enumerate(OSC_CASES):
    setattr(
        ConvertOscTest,
        f"test_convert_osc_{index}",
        _make_convert_osc_test(text, expected_text, expected_titles, index),
    )


class StreamWrapperBehaviorTest(TestCase):
    def test_isatty_true_for_tty(self):
        wrapper = StreamWrapper(StreamTTY(), Mock())
        self.assertTrue(wrapper.isatty())

    def test_isatty_false_for_non_tty(self):
        wrapper = StreamWrapper(StreamNonTTY(), Mock())
        self.assertFalse(wrapper.isatty())

    def test_isatty_false_without_isatty(self):
        wrapper = StreamWrapper(object(), Mock())
        self.assertFalse(wrapper.isatty())

    def test_isatty_false_for_none_stream(self):
        wrapper = StreamWrapper(None, Mock())
        self.assertFalse(wrapper.isatty())

    def test_isatty_true_for_pycharm_stdout(self):
        with pycharm():
            wrapper = StreamWrapper(sys.__stdout__, Mock())
            self.assertTrue(wrapper.isatty())

    def test_isatty_true_for_pycharm_stderr(self):
        with pycharm():
            wrapper = StreamWrapper(sys.__stderr__, Mock())
            self.assertTrue(wrapper.isatty())

    def test_closed_true_without_closed_attr(self):
        wrapper = StreamWrapper(object(), Mock())
        self.assertTrue(wrapper.closed)

    def test_closed_true_when_closed_raises_value_error(self):
        class BrokenClosed:
            @property
            def closed(self):
                raise ValueError("detached")

        wrapper = StreamWrapper(BrokenClosed(), Mock())
        self.assertTrue(wrapper.closed)

    def test_closed_true_when_closed(self):
        stream = StringIO()
        stream.close()
        wrapper = StreamWrapper(stream, Mock())
        self.assertTrue(wrapper.closed)

    def test_closed_false_when_open(self):
        stream = StringIO()
        wrapper = StreamWrapper(stream, Mock())
        self.assertFalse(wrapper.closed)


class WrapStreamTest(TestCase):
    pass


WRAP_STREAM_CASES = [
    ("wrap_false", False, None, None, False, False),
    ("wrap_true_wraps", True, None, None, False, True),
    ("wrap_true_should_wrap_false", True, None, None, False, False),
    ("wrap_true_convert_true", True, True, None, False, True),
    ("wrap_true_strip_true", True, None, True, False, True),
    ("wrap_true_autoreset_true", True, None, None, True, True),
    ("wrap_true_all_false", True, False, False, False, False),
    ("wrap_true_convert_false_strip_true", True, False, True, False, True),
    ("wrap_true_strip_false", True, None, False, False, False),
    ("wrap_true_convert_none_strip_none", True, None, None, False, True),
]


def _make_wrap_stream_test(name, wrap, convert, strip, autoreset, should_wrap):
    def test(self):
        stream = Mock()
        wrapper = Mock()
        wrapper.stream = object()
        wrapper.should_wrap.return_value = should_wrap
        with patch("colorama.initialise.AnsiToWin32", return_value=wrapper) as factory:
            result = wrap_stream(stream, convert, strip, autoreset, wrap)
        if wrap:
            factory.assert_called_once_with(
                stream,
                convert=convert,
                strip=strip,
                autoreset=autoreset,
            )
            expected = wrapper.stream if should_wrap else stream
            self.assertIs(result, expected)
        else:
            factory.assert_not_called()
            self.assertIs(result, stream)

    return test


for name, wrap, convert, strip, autoreset, should_wrap in WRAP_STREAM_CASES:
    setattr(
        WrapStreamTest,
        f"test_wrap_stream_{name}",
        _make_wrap_stream_test(name, wrap, convert, strip, autoreset, should_wrap),
    )


class ColoramaTextTest(TestCase):
    def test_colorama_text_calls_init_and_deinit(self):
        with patch("colorama.initialise.init") as init, patch("colorama.initialise.deinit") as deinit:
            with colorama_text():
                pass
        init.assert_called_once_with()
        deinit.assert_called_once_with()

    def test_colorama_text_passes_args(self):
        with patch("colorama.initialise.init") as init, patch("colorama.initialise.deinit") as deinit:
            with colorama_text(autoreset=True, wrap=False):
                pass
        init.assert_called_once_with(autoreset=True, wrap=False)
        deinit.assert_called_once_with()

    def test_colorama_text_calls_deinit_on_exception(self):
        with patch("colorama.initialise.init") as init, patch("colorama.initialise.deinit") as deinit:
            with self.assertRaises(RuntimeError):
                with colorama_text():
                    init.assert_called_once_with()
                    raise RuntimeError("boom")
        deinit.assert_called_once_with()

    def test_colorama_text_nested_calls(self):
        with patch("colorama.initialise.init") as init, patch("colorama.initialise.deinit") as deinit:
            with colorama_text():
                with colorama_text():
                    pass
        self.assertEqual(init.call_count, 2)
        self.assertEqual(deinit.call_count, 2)

    def test_colorama_text_order(self):
        events = []

        def record_init(*args, **kwargs):
            events.append("init")

        def record_deinit():
            events.append("deinit")

        with patch("colorama.initialise.init", side_effect=record_init), patch(
            "colorama.initialise.deinit",
            side_effect=record_deinit,
        ):
            with colorama_text():
                events.append("body")

        self.assertEqual(events, ["init", "body", "deinit"])


if __name__ == "__main__":
    main()
