import unittest
from unittest.mock import patch
import inspect
import dis

import colorama.win32 as win32
from colorama.ansitowin32 import AnsiToWin32


class Win32SetConsoleTextAttributeTest(unittest.TestCase):
    def setUp(self):
        # Skip if the Windows API-backed functions are not available on this platform
        if not hasattr(win32, "_GetStdHandle") or not hasattr(win32, "_SetConsoleTextAttribute"):
            self.skipTest("Windows WinAPI functions are not available; skipping test.")

    def test_calls_getstdhandle_and_setconsoletextattribute_and_returns_value(self):
        stream_id = 42
        attrs = 7
        fake_handle = object()
        expected_return = True

        with patch.object(win32, "_GetStdHandle", return_value=fake_handle) as mock_get, \
             patch.object(win32, "_SetConsoleTextAttribute", return_value=expected_return) as mock_set:

            result = win32.SetConsoleTextAttribute(stream_id, attrs)

            # Verify the return value is passed through
            self.assertEqual(result, expected_return)

            # Verify the correct calls and arguments
            mock_get.assert_called_once_with(stream_id)
            mock_set.assert_called_once_with(fake_handle, attrs)

    @unittest.skip("only using when inline variable refactoring")
    def test_inline_variable_handle_is_applied(self):
        """
        Verifies the inline-variable refactoring was applied by asserting:
        - No local variable named 'handle' exists in the function.
        - No STORE_* to a local named 'handle' appears in the bytecode.
        - The function is a Python function (not a stub/builtin).
        """
        func = win32.SetConsoleTextAttribute

        # Robust function check (avoid types.FunctionType conflicts)
        self.assertTrue(
            inspect.isfunction(func),
            "Expected a Python function implementation, not a stub or builtin."
        )

        # 1) There must be no local variable named 'handle'
        self.assertNotIn(
            "handle",
            func.__code__.co_varnames,
            "Local variable 'handle' still present; inline-variable refactoring not applied.",
        )

        # 2) There must be no STORE_* instruction targeting 'handle'
        for ins in dis.get_instructions(func):
            self.assertFalse(
                ins.opname.startswith("STORE") and ins.argval == "handle",
                "Found a STORE to local 'handle'; inline-variable refactoring not applied.",
            )

class TestAnsiToWin32ConvertGetterSetter(unittest.TestCase):
    def setUp(self):
        # Create a safe instance that avoids OS-dependent behavior by passing explicit flags
        self.stream = AnsiToWin32(wrapped=object(), convert=False, strip=False, autoreset=False)

    @unittest.skip("only when getter setter refactoring is applied")
    def test_convert_is_property(self):
        # Class must expose 'convert' as a property
        self.assertTrue(
            isinstance(AnsiToWin32.convert, property),
            "AnsiToWin32.convert should be a @property",
        )
        # Getter and setter should be regular Python functions
        self.assertTrue(inspect.isfunction(AnsiToWin32.convert.fget))
        self.assertTrue(
            hasattr(AnsiToWin32.convert, "fset") and inspect.isfunction(AnsiToWin32.convert.fset),
            "convert should have a setter",
        )
        
    @unittest.skip("only when getter setter refactoring is applied")
    def test_convert_backing_attribute_used(self):
        # Instance should not store 'convert' directly in __dict__
        self.assertNotIn(
            "convert",
            self.stream.__dict__,
            "Direct storage of 'convert' found; expected backing attribute via property.",
        )
        # Expect a backing attribute, commonly named '_convert' (or similar)
        self.assertTrue(
            any(name in self.stream.__dict__ for name in ("_convert", "__convert", "convert_")),
            "Expected a backing attribute for 'convert' (e.g., _convert) in __dict__",
        )

    def test_convert_getter_setter_roundtrip(self):
        # Roundtrip assignment and read using the property
        self.stream.convert = True
        self.assertTrue(self.stream.convert, "convert setter should set to True")
        self.stream.convert = False
        self.assertFalse(self.stream.convert, "convert setter should set to False")

    @unittest.skip("only when getter setter refactoring is applied")
    def test_convert_property_does_not_break_behavioral_contract(self):
        # Basic behavioral check: should_wrap reflects convert when strip=False
        # (This does not rely on OS-specific setup.)
        self.stream.strip = False
        self.stream.convert = False
        self.assertFalse(self.stream.should_wrap(), "should_wrap should be False when convert=False and strip=False")

        self.stream.convert = True
        self.assertTrue(self.stream.should_wrap(), "should_wrap should be True when convert=True and strip=False")


if __name__ == "__main__":
    unittest.main()