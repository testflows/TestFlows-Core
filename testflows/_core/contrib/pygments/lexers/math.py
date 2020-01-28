# -*- coding: utf-8 -*-
"""
    pygments.lexers.math
    ~~~~~~~~~~~~~~~~~~~~

    Just export lexers that were contained in this module.

    :copyright: Copyright 2006-2019 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from testflows._core.contrib.pygments.lexers.python import NumPyLexer
from testflows._core.contrib.pygments.lexers.matlab import MatlabLexer, MatlabSessionLexer, \
    OctaveLexer, ScilabLexer
from testflows._core.contrib.pygments.lexers.julia import JuliaLexer, JuliaConsoleLexer
from testflows._core.contrib.pygments.lexers.r import RConsoleLexer, SLexer, RdLexer
from testflows._core.contrib.pygments.lexers.modeling import BugsLexer, JagsLexer, StanLexer
from testflows._core.contrib.pygments.lexers.idl import IDLLexer
from testflows._core.contrib.pygments.lexers.algebra import MuPADLexer

__all__ = []
