# Copyright 2023-2026 Katteli Inc.
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
import sys


def is_marimo_notebook():
    """Return True if running inside a Marimo notebook."""
    marimo = sys.modules.get("marimo")
    if marimo is None:
        return False
    try:
        return bool(marimo.running_in_notebook())
    except Exception:
        return False


def marimo_theme():
    """Return Marimo display theme ("light" or "dark") or None if not in Marimo.

    Note that Marimo reports "light" when its theme is set to "system".
    """
    if not is_marimo_notebook():
        return None
    try:
        return sys.modules["marimo"].app_meta().theme
    except Exception:
        return None


def is_jupyter_notebook():
    """Return True if running inside a Jupyter notebook."""
    try:
        shell = get_ipython().__class__.__name__
        if shell == "TerminalInteractiveShell":
            return False
        return True
    except NameError:
        return False


def is_interactive_notebook():
    """Return True if running inside any interactive notebook (Jupyter or Marimo)."""
    return is_marimo_notebook() or is_jupyter_notebook()
