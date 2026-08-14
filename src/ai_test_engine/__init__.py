"""AI-powered test automation engine."""

import sys

__version__ = "1.0.0"

# The agents log progress with emoji. On Windows, stdout falls back to the
# locale codec (cp1252) whenever it is not a console -- a pipe, a file, CI
# logs -- and those prints raise UnicodeEncodeError. Force UTF-8 so output
# survives redirection.
for _stream in (sys.stdout, sys.stderr):
    if hasattr(_stream, "reconfigure"):
        try:
            _stream.reconfigure(encoding="utf-8", errors="replace")
        except (ValueError, OSError):  # already detached or not reconfigurable
            pass
