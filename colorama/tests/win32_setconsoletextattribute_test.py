import unittest
from unittest.mock import patch
import inspect
import dis

import colorama.win32 as win32


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


if __name__ == "__main__":
    unittest.main()