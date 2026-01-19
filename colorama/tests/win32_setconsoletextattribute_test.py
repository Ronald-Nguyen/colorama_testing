import unittest
from unittest.mock import patch
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


if __name__ == "__main__":
    unittest.main()