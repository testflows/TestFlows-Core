# -*- coding: utf-8 -*-
"""
    pygments.lexers.compiled
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Just export lexer classes previously contained in this module.

    :copyright: Copyright 2006-2019 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from testflows._core.contrib.pygments.lexers.jvm import JavaLexer, ScalaLexer
from testflows._core.contrib.pygments.lexers.c_cpp import CLexer, CppLexer
from testflows._core.contrib.pygments.lexers.d import DLexer
from testflows._core.contrib.pygments.lexers.objective import ObjectiveCLexer, \
    ObjectiveCppLexer, LogosLexer
from testflows._core.contrib.pygments.lexers.go import GoLexer
from testflows._core.contrib.pygments.lexers.rust import RustLexer
from testflows._core.contrib.pygments.lexers.c_like import ECLexer, ValaLexer, CudaLexer
from testflows._core.contrib.pygments.lexers.pascal import DelphiLexer, Modula2Lexer, AdaLexer
from testflows._core.contrib.pygments.lexers.business import CobolLexer, CobolFreeformatLexer
from testflows._core.contrib.pygments.lexers.fortran import FortranLexer
from testflows._core.contrib.pygments.lexers.prolog import PrologLexer
from testflows._core.contrib.pygments.lexers.python import CythonLexer
from testflows._core.contrib.pygments.lexers.graphics import GLShaderLexer
from testflows._core.contrib.pygments.lexers.ml import OcamlLexer
from testflows._core.contrib.pygments.lexers.basic import BlitzBasicLexer, BlitzMaxLexer, MonkeyLexer
from testflows._core.contrib.pygments.lexers.dylan import DylanLexer, DylanLidLexer, DylanConsoleLexer
from testflows._core.contrib.pygments.lexers.ooc import OocLexer
from testflows._core.contrib.pygments.lexers.felix import FelixLexer
from testflows._core.contrib.pygments.lexers.nimrod import NimrodLexer
from testflows._core.contrib.pygments.lexers.crystal import CrystalLexer

__all__ = []
