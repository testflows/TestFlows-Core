# -*- coding: utf-8 -*-
"""
    pygments.lexers.text
    ~~~~~~~~~~~~~~~~~~~~

    Lexers for non-source code file types.

    :copyright: Copyright 2006-2019 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from testflows._core.contrib.pygments.lexers.configs import ApacheConfLexer, NginxConfLexer, \
    SquidConfLexer, LighttpdConfLexer, IniLexer, RegeditLexer, PropertiesLexer
from testflows._core.contrib.pygments.lexers.console import PyPyLogLexer
from testflows._core.contrib.pygments.lexers.textedit import VimLexer
from testflows._core.contrib.pygments.lexers.markup import BBCodeLexer, MoinWikiLexer, RstLexer, \
    TexLexer, GroffLexer
from testflows._core.contrib.pygments.lexers.installers import DebianControlLexer, SourcesListLexer
from testflows._core.contrib.pygments.lexers.make import MakefileLexer, BaseMakefileLexer, CMakeLexer
from testflows._core.contrib.pygments.lexers.haxe import HxmlLexer
from testflows._core.contrib.pygments.lexers.sgf import SmartGameFormatLexer
from testflows._core.contrib.pygments.lexers.diff import DiffLexer, DarcsPatchLexer
from testflows._core.contrib.pygments.lexers.data import YamlLexer
from testflows._core.contrib.pygments.lexers.textfmts import IrcLogsLexer, GettextLexer, HttpLexer

__all__ = []
