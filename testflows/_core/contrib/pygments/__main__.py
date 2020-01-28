# -*- coding: utf-8 -*-
"""
    pygments.__main__
    ~~~~~~~~~~~~~~~~~

    Main entry point for ``python -m pygments``.

    :copyright: Copyright 2006-2019 by the Pygments team, see AUTHORS.
    :license: BSD, see LICENSE for details.
"""

import sys
import testflows._core.contrib.pygments.cmdline as pygments_cmdline

try:
    sys.exit(pygments_cmdline.main(sys.argv))
except KeyboardInterrupt:
    sys.exit(1)
