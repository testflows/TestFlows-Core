# -*- coding: utf-8 -*-
"""
    pygments.lexers.web
    ~~~~~~~~~~~~~~~~~~~

    Just export previously exported lexers.

    :copyright: Copyright 2006-2019 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

from testflows._core.contrib.pygments.lexers.html import HtmlLexer, DtdLexer, XmlLexer, XsltLexer, \
    HamlLexer, ScamlLexer, JadeLexer
from testflows._core.contrib.pygments.lexers.css import CssLexer, SassLexer, ScssLexer
from testflows._core.contrib.pygments.lexers.javascript import JavascriptLexer, LiveScriptLexer, \
    DartLexer, TypeScriptLexer, LassoLexer, ObjectiveJLexer, CoffeeScriptLexer
from testflows._core.contrib.pygments.lexers.actionscript import ActionScriptLexer, \
    ActionScript3Lexer, MxmlLexer
from testflows._core.contrib.pygments.lexers.php import PhpLexer
from testflows._core.contrib.pygments.lexers.webmisc import DuelLexer, XQueryLexer, SlimLexer, QmlLexer
from testflows._core.contrib.pygments.lexers.data import JsonLexer
JSONLexer = JsonLexer  # for backwards compatibility with Pygments 1.5

__all__ = []
