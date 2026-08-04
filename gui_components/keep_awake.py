"""
Keep Awake (sleep inhibitor)
============================
Stops the computer from sleeping and the display from blanking while the
application is open — for the times the event timeline is left up on a screen,
or a long batch is running unattended.

Windows only. The inhibitor is implemented with ``SetThreadExecutionState``;
on other platforms this degrades to a no-op and reports ``is_supported() is
False``, so the GUI can disable the setting rather than promise something the
OS will not honour.
"""

import ctypes
import logging
import sys

logger = logging.getLogger("setup_report_processor")

# SetThreadExecutionState flags (winbase.h)
ES_CONTINUOUS = 0x80000000        # state stays in effect until it is reset
ES_SYSTEM_REQUIRED = 0x00000001   # keep the system from sleeping
ES_DISPLAY_REQUIRED = 0x00000002  # keep the display from turning off


class KeepAwake:
    """
    An OS-level sleep inhibitor that can be toggled on and off.

    The Windows execution state is tracked *per thread*, so the thread that
    turns the inhibitor on has to stay alive for the request to hold. Always
    drive this from the GUI thread — never from a worker.

    The request is advisory: it defers idle sleep and display timeout, but it
    does not override the user closing the lid or choosing Sleep from the Start
    menu.

    Example:
        keep_awake = KeepAwake()
        keep_awake.set_enabled(True)   # computer and display stay on
        keep_awake.release()           # normal power behavior returns
    """

    def __init__(self):
        self._enabled = False

    @staticmethod
    def is_supported() -> bool:
        """
        Whether this platform has a sleep inhibitor this class knows how to use.

        Returns:
            True on Windows, False everywhere else.
        """
        return sys.platform == "win32"

    @property
    def enabled(self) -> bool:
        """Whether the inhibitor is currently in effect."""
        return self._enabled

    def set_enabled(self, enabled: bool) -> bool:
        """
        Turn the sleep inhibitor on or off.

        Args:
            enabled: True to keep the computer and display awake, False to
                restore the machine's normal power behavior.

        Returns:
            The state actually in effect afterwards. This is False when the
            request could not be applied — an unsupported platform, or an API
            call the OS refused — so callers can re-sync their UI to reality.
        """
        if enabled == self._enabled:
            return self._enabled

        if enabled and not self.is_supported():
            logger.warning(
                f"Keep awake is not supported on this platform ({sys.platform}); "
                "the computer will follow its normal power settings."
            )
            return False

        state = ES_CONTINUOUS
        if enabled:
            state |= ES_SYSTEM_REQUIRED | ES_DISPLAY_REQUIRED

        if not self._apply(state):
            return self._enabled

        self._enabled = enabled
        logger.info(
            "Keep awake on — the computer and display will stay on while this "
            "window is open"
            if enabled
            else "Keep awake off — normal power settings apply again"
        )
        return self._enabled

    def release(self):
        """
        Restore normal power behavior.

        Safe to call when the inhibitor is already off, so it can be wired
        straight to window close.
        """
        self.set_enabled(False)

    @staticmethod
    def _apply(state: int) -> bool:
        """
        Push an execution state to the OS.

        Args:
            state: A bitmask of the ES_* flags.

        Returns:
            True if the OS accepted the request.
        """
        if sys.platform != "win32":
            return False
        try:
            set_state = ctypes.windll.kernel32.SetThreadExecutionState
            set_state.argtypes = [ctypes.c_uint]
            set_state.restype = ctypes.c_uint
            # Returns the previous state, or 0 on failure.
            if set_state(ctypes.c_uint(state)) == 0:
                logger.error(
                    "Windows refused the keep-awake request "
                    "(SetThreadExecutionState returned 0)."
                )
                return False
            return True
        except (AttributeError, OSError) as exc:
            logger.error(f"Could not change the computer's sleep setting: {exc}")
            return False
