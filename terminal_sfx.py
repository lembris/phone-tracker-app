"""
Retro terminal sound effects for GHOSTTRACE (educational demo).
Uses Windows Beep API on win32; system bell elsewhere. Non-blocking.
"""

import sys
import threading

_sfx_enabled = True


def set_enabled(enabled: bool) -> None:
    global _sfx_enabled
    _sfx_enabled = enabled


def is_enabled() -> bool:
    return _sfx_enabled


def _play_tone(freq: int, duration_ms: int) -> None:
    if not _sfx_enabled:
        return
    try:
        if sys.platform == "win32":
            import winsound
            winsound.Beep(int(freq), int(duration_ms))
        else:
            sys.stdout.write("\a")
            sys.stdout.flush()
    except Exception:
        pass


def _async_tone(freq: int, duration_ms: int) -> None:
    threading.Thread(target=_play_tone, args=(freq, duration_ms), daemon=True).start()


def _async_sequence(tones: list) -> None:
    """tones: list of (freq, duration_ms)"""

    def run():
        for freq, dur in tones:
            _play_tone(freq, dur)

    threading.Thread(target=run, daemon=True).start()


def boot_line() -> None:
    _async_tone(520, 35)


def boot_ready() -> None:
    _async_sequence([(660, 60), (880, 60), (1100, 90)])


def scan_tick() -> None:
    _async_tone(720, 28)


def scan_step() -> None:
    _async_tone(740, 45)


def scan_warning() -> None:
    _async_tone(380, 120)


def scan_success() -> None:
    _async_sequence([(880, 70), (1100, 70), (1320, 110)])


def scan_error() -> None:
    _async_sequence([(320, 150), (240, 200)])


def key_tick() -> None:
    _async_tone(900, 18)


def toggle_click() -> None:
    _async_tone(600, 25)
