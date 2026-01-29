import re
import sys
import os

from .ansi import AnsiFore, AnsiBack, AnsiStyle, Style, BEL
from .winterm import enable_vt_processing, WinTerm, WinColor, WinStyle
from .win32 import windll, winapi_test

winterm = None
if windll is not None:
    winterm = WinTerm()

class StreamWrapper:

    def __init__(self, wrapped, converter):
        self.__wrapped = wrapped
        self.__convertor = converter

    def __getattr__(self, name):
        return getattr(self.__wrapped, name)

    def __enter__(self, *args, **kwargs):
        return self.__wrapped.__enter__(*args, **kwargs)

    def __exit__(self, *args, **kwargs):
        return self.__wrapped.__exit__(*args, **kwargs)

    def __setstate__(self, state):
        self.__dict__ = state

    def __getstate__(self):
        return self.__dict__

    def write(self, text):
        self.__convertor.write(text)

    def isatty(self):
        stream = self.__wrapped
        if 'PYCHARM_HOSTED' in os.environ:
            if stream is not None and (stream is sys.__stdout__ or stream is sys.__stderr__):
                return True
        try:
            stream_isatty = stream.isatty
        except AttributeError:
            return False
        else:
            return stream_isatty()

    @property
    def closed(self):
        stream = self.__wrapped
        try:
            return stream.closed
        except (AttributeError, ValueError):
            return True

def _strategy_reset_all(params, on_stderr=False):
    winterm.reset_all(on_stderr=on_stderr)

def _strategy_style_bright(params, on_stderr=False):
    winterm.style(WinStyle.BRIGHT, on_stderr=on_stderr)

def _strategy_style_dim(params, on_stderr=False):
    winterm.style(WinStyle.NORMAL, on_stderr=on_stderr)

def _strategy_style_normal(params, on_stderr=False):
    winterm.style(WinStyle.NORMAL, on_stderr=on_stderr)

def _strategy_fore_black(params, on_stderr=False):
    winterm.fore(WinColor.BLACK, on_stderr=on_stderr)

def _strategy_fore_red(params, on_stderr=False):
    winterm.fore(WinColor.RED, on_stderr=on_stderr)

def _strategy_fore_green(params, on_stderr=False):
    winterm.fore(WinColor.GREEN, on_stderr=on_stderr)

def _strategy_fore_yellow(params, on_stderr=False):
    winterm.fore(WinColor.YELLOW, on_stderr=on_stderr)

def _strategy_fore_blue(params, on_stderr=False):
    winterm.fore(WinColor.BLUE, on_stderr=on_stderr)

def _strategy_fore_magenta(params, on_stderr=False):
    winterm.fore(WinColor.MAGENTA, on_stderr=on_stderr)

def _strategy_fore_cyan(params, on_stderr=False):
    winterm.fore(WinColor.CYAN, on_stderr=on_stderr)

def _strategy_fore_white(params, on_stderr=False):
    winterm.fore(WinColor.GREY, on_stderr=on_stderr)

def _strategy_fore_reset(params, on_stderr=False):
    winterm.fore(on_stderr=on_stderr)

def _strategy_fore_lightblack_ex(params, on_stderr=False):
    winterm.fore(WinColor.BLACK, light=True, on_stderr=on_stderr)

def _strategy_fore_lightred_ex(params, on_stderr=False):
    winterm.fore(WinColor.RED, light=True, on_stderr=on_stderr)

def _strategy_fore_lightgreen_ex(params, on_stderr=False):
    winterm.fore(WinColor.GREEN, light=True, on_stderr=on_stderr)

def _strategy_fore_lightyellow_ex(params, on_stderr=False):
    winterm.fore(WinColor.YELLOW, light=True, on_stderr=on_stderr)

def _strategy_fore_lightblue_ex(params, on_stderr=False):
    winterm.fore(WinColor.BLUE, light=True, on_stderr=on_stderr)

def _strategy_fore_lightmagenta_ex(params, on_stderr=False):
    winterm.fore(WinColor.MAGENTA, light=True, on_stderr=on_stderr)

def _strategy_fore_lightcyan_ex(params, on_stderr=False):
    winterm.fore(WinColor.CYAN, light=True, on_stderr=on_stderr)

def _strategy_fore_lightwhite_ex(params, on_stderr=False):
    winterm.fore(WinColor.GREY, light=True, on_stderr=on_stderr)

def _strategy_back_black(params, on_stderr=False):
    winterm.back(WinColor.BLACK, on_stderr=on_stderr)

def _strategy_back_red(params, on_stderr=False):
    winterm.back(WinColor.RED, on_stderr=on_stderr)

def _strategy_back_green(params, on_stderr=False):
    winterm.back(WinColor.GREEN, on_stderr=on_stderr)

def _strategy_back_yellow(params, on_stderr=False):
    winterm.back(WinColor.YELLOW, on_stderr=on_stderr)

def _strategy_back_blue(params, on_stderr=False):
    winterm.back(WinColor.BLUE, on_stderr=on_stderr)

def _strategy_back_magenta(params, on_stderr=False):
    winterm.back(WinColor.MAGENTA, on_stderr=on_stderr)

def _strategy_back_cyan(params, on_stderr=False):
    winterm.back(WinColor.CYAN, on_stderr=on_stderr)

def _strategy_back_white(params, on_stderr=False):
    winterm.back(WinColor.GREY, on_stderr=on_stderr)

def _strategy_back_reset(params, on_stderr=False):
    winterm.back(on_stderr=on_stderr)

def _strategy_back_lightblack_ex(params, on_stderr=False):
    winterm.back(WinColor.BLACK, light=True, on_stderr=on_stderr)

def _strategy_back_lightred_ex(params, on_stderr=False):
    winterm.back(WinColor.RED, light=True, on_stderr=on_stderr)

def _strategy_back_lightgreen_ex(params, on_stderr=False):
    winterm.back(WinColor.GREEN, light=True, on_stderr=on_stderr)

def _strategy_back_lightyellow_ex(params, on_stderr=False):
    winterm.back(WinColor.YELLOW, light=True, on_stderr=on_stderr)

def _strategy_back_lightblue_ex(params, on_stderr=False):
    winterm.back(WinColor.BLUE, light=True, on_stderr=on_stderr)

def _strategy_back_lightmagenta_ex(params, on_stderr=False):
    winterm.back(WinColor.MAGENTA, light=True, on_stderr=on_stderr)

def _strategy_back_lightcyan_ex(params, on_stderr=False):
    winterm.back(WinColor.CYAN, light=True, on_stderr=on_stderr)

def _strategy_back_lightwhite_ex(params, on_stderr=False):
    winterm.back(WinColor.GREY, light=True, on_stderr=on_stderr)

STRATEGIES = {
    AnsiStyle.RESET_ALL: _strategy_reset_all,
    AnsiStyle.BRIGHT: _strategy_style_bright,
    AnsiStyle.DIM: _strategy_style_dim,
    AnsiStyle.NORMAL: _strategy_style_normal,
    AnsiFore.BLACK: _strategy_fore_black,
    AnsiFore.RED: _strategy_fore_red,
    AnsiFore.GREEN: _strategy_fore_green,
    AnsiFore.YELLOW: _strategy_fore_yellow,
    AnsiFore.BLUE: _strategy_fore_blue,
    AnsiFore.MAGENTA: _strategy_fore_magenta,
    AnsiFore.CYAN: _strategy_fore_cyan,
    AnsiFore.WHITE: _strategy_fore_white,
    AnsiFore.RESET: _strategy_fore_reset,
    AnsiFore.LIGHTBLACK_EX: _strategy_fore_lightblack_ex,
    AnsiFore.LIGHTRED_EX: _strategy_fore_lightred_ex,
    AnsiFore.LIGHTGREEN_EX: _strategy_fore_lightgreen_ex,
    AnsiFore.LIGHTYELLOW_EX: _strategy_fore_lightyellow_ex,
    AnsiFore.LIGHTBLUE_EX: _strategy_fore_lightblue_ex,
    AnsiFore.LIGHTMAGENTA_EX: _strategy_fore_lightmagenta_ex,
    AnsiFore.LIGHTCYAN_EX: _strategy_fore_lightcyan_ex,
    AnsiFore.LIGHTWHITE_EX: _strategy_fore_lightwhite_ex,
    AnsiBack.BLACK: _strategy_back_black,
    AnsiBack.RED: _strategy_back_red,
    AnsiBack.GREEN: _strategy_back_green,
    AnsiBack.YELLOW: _strategy_back_yellow,
    AnsiBack.BLUE: _strategy_back_blue,
    AnsiBack.MAGENTA: _strategy_back_magenta,
    AnsiBack.CYAN: _strategy_back_cyan,
    AnsiBack.WHITE: _strategy_back_white,
    AnsiBack.RESET: _strategy_back_reset,
    AnsiBack.LIGHTBLACK_EX: _strategy_back_lightblack_ex,
    AnsiBack.LIGHTRED_EX: _strategy_back_lightred_ex,
    AnsiBack.LIGHTGREEN_EX: _strategy_back_lightgreen_ex,
    AnsiBack.LIGHTYELLOW_EX: _strategy_back_lightyellow_ex,
    AnsiBack.LIGHTBLUE_EX: _strategy_back_lightblue_ex,
    AnsiBack.LIGHTMAGENTA_EX: _strategy_back_lightmagenta_ex,
    AnsiBack.LIGHTCYAN_EX: _strategy_back_lightcyan_ex,
    AnsiBack.LIGHTWHITE_EX: _strategy_back_lightwhite_ex,
}

class AnsiToWin32:

    ANSI_CSI_RE = re.compile('\001?\033\\[((?:\\d|;)*)([a-zA-Z])\002?')
    ANSI_OSC_RE = re.compile('\001?\033\\]([^\a]*)(\a)\002?')

    def __init__(self, wrapped, convert=None, strip=None, autoreset=False):
        self.wrapped = wrapped

        self.autoreset = autoreset

        self.stream = StreamWrapper(wrapped, self)

        on_windows = os.name == 'nt'
        conversion_supported = on_windows and winapi_test()
        try:
            fd = wrapped.fileno()
        except Exception:
            fd = -1
        system_has_native_ansi = not on_windows or enable_vt_processing(fd)
        have_tty = not self.stream.closed and self.stream.isatty()
        need_conversion = conversion_supported and not system_has_native_ansi

        if strip is None:
            strip = need_conversion or not have_tty
        self.strip = strip

        if convert is None:
            convert = need_conversion and have_tty
        self.convert = convert

        self.on_stderr = self.wrapped is sys.stderr

    def should_wrap(self):
        return self.convert or self.strip or self.autoreset

    def write(self, text):
        if self.strip or self.convert:
            self.write_and_convert(text)
        else:
            self.wrapped.write(text)
            self.wrapped.flush()
        if self.autoreset:
            self.reset_all()

    def reset_all(self):
        if self.convert:
            self.call_win32('m', (0,))
        elif not self.strip and not self.stream.closed:
            self.wrapped.write(Style.RESET_ALL)

    def write_and_convert(self, text):
        cursor = 0
        text = self.convert_osc(text)
        for match in self.ANSI_CSI_RE.finditer(text):
            start, end = match.span()
            self.write_plain_text(text, cursor, start)
            self.convert_ansi(*match.groups())
            cursor = end
        self.write_plain_text(text, cursor, len(text))

    def write_plain_text(self, text, start, end):
        if start < end:
            self.wrapped.write(text[start:end])
            self.wrapped.flush()

    def convert_ansi(self, paramstring, command):
        if self.convert:
            params = self.extract_params(command, paramstring)
            self.call_win32(command, params)

    def extract_params(self, command, paramstring):
        if command in 'Hf':
            params = tuple(int(p) if len(p) != 0 else 1 for p in paramstring.split(';'))
            while len(params) < 2:
                params = params + (1,)
        else:
            params = tuple(int(p) for p in paramstring.split(';') if len(p) != 0)
            if len(params) == 0:
                if command in 'JKm':
                    params = (0,)
                elif command in 'ABCD':
                    params = (1,)

        return params

    def call_win32(self, command, params):
        if command == 'm':
            for param in params:
                if param in STRATEGIES:
                    STRATEGIES[param](params, on_stderr=self.on_stderr)
        elif command in 'J':
            winterm.erase_screen(params[0], on_stderr=self.on_stderr)
        elif command in 'K':
            winterm.erase_line(params[0], on_stderr=self.on_stderr)
        elif command in 'Hf':
            winterm.set_cursor_position(params, on_stderr=self.on_stderr)
        elif command in 'ABCD':
            n = params[0]
            x, y = {'A': (0, -n), 'B': (0, n), 'C': (n, 0), 'D': (-n, 0)}[command]
            winterm.cursor_adjust(x, y, on_stderr=self.on_stderr)

    def convert_osc(self, text):
        for match in self.ANSI_OSC_RE.finditer(text):
            start, end = match.span()
            text = text[:start] + text[end:]
            paramstring, command = match.groups()
            if command == BEL:
                if paramstring.count(";") == 1:
                    params = paramstring.split(";")
                    if params[0] in '02':
                        winterm.set_title(params[1])
        return text

    def flush(self):
        self.wrapped.flush()