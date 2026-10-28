# Copyright 2026 Katteli Inc.
# TestFlows.com Open-Source Software Testing Framework (http://testflows.com)
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
import os
import sys
import subprocess

import testflows.settings as settings
from testflows._core.interactive_notebook import marimo_theme


def colorfgbg_theme():
    """Return theme from COLORFGBG environment variable (e.g. "15;0") or None."""
    try:
        bg = int(os.environ["COLORFGBG"].split(";")[-1])
    except (KeyError, ValueError):
        return None
    return "dark" if bg < 7 or bg == 8 else "light"


def gsettings_theme():
    """Return theme from GNOME color-scheme setting or None."""
    try:
        out = subprocess.run(
            ["gsettings", "get", "org.gnome.desktop.interface", "color-scheme"],
            capture_output=True,
            text=True,
            timeout=1,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    if "prefer-dark" in out:
        return "dark"
    if "prefer-light" in out or "default" in out:
        return "light"
    return None


_theme = None
_detected = False


def settings_theme():
    """Return theme from settings.theme or None if it is not set or not valid."""
    theme = str(settings.theme or "").strip().lower()
    return theme if theme in ("light", "dark") else None


def detect_terminal_theme():
    """Detect and remember the output theme, "light" or "dark" or None if unknown.

    Checked in order: settings.theme, Marimo display theme, COLORFGBG, GNOME color-scheme.

    Must be called from the thread that runs the test (for example, in init())
    as Marimo context is thread local and is not available in other threads.
    """
    global _theme, _detected
    theme = settings_theme() or marimo_theme() or colorfgbg_theme()
    if theme is None and sys.platform.startswith("linux") and sys.stdout.isatty():
        theme = gsettings_theme()
    _theme, _detected = theme, True
    return _theme


def terminal_theme():
    """Return the output theme detected by detect_terminal_theme()."""
    if not _detected:
        detect_terminal_theme()
    return _theme
