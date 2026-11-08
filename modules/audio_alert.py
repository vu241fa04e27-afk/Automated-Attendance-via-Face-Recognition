"""
Acoustic Alert Module for SafeSite PPE Violation Warning.
Synthesizes audible warning tones upon safety violations with rate limiting / debounce.
"""

import time
import threading
import sys
import config

_last_alert_time = 0.0
_lock = threading.Lock()

def trigger_violation_alarm(frequency: int = 1200, duration_ms: int = 250):
    """
    Triggers an acoustic alert in a background thread if debounce interval has elapsed.
    """
    global _last_alert_time
    if not config.AUDIO_ALERT_ENABLED:
        return

    now = time.time()
    with _lock:
        if now - _last_alert_time < config.AUDIO_ALERT_DEBOUNCE_SECONDS:
            return
        _last_alert_time = now

    def _play():
        try:
            if sys.platform == "win32":
                import winsound
                winsound.Beep(frequency, duration_ms)
            else:
                # Terminal bell for Linux / macOS / Docker
                sys.stdout.write("\a")
                sys.stdout.flush()
        except Exception:
            pass

    threading.Thread(target=_play, daemon=True).start()

