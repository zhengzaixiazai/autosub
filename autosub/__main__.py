#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's entry point.
"""

from __future__ import absolute_import, print_function, unicode_literals

# Import built-in modules
# pylint: disable=no-member, protected-access
import multiprocessing
import sys

if __package__ is None and not hasattr(sys, "frozen"):
    # direct call of __main__.py
    # Reference: https://github.com/rg3/youtube-dl/blob/master/youtube_dl/__main__.py
    import os.path
    PATH = os.path.realpath(os.path.abspath(__file__))
    sys.path.insert(0, os.path.dirname(os.path.dirname(PATH)))

# Any changes to the path and your own modules

if __name__ == "__main__":
    # On Windows calling this function is necessary.
    if sys.platform.startswith('win'):
        multiprocessing.freeze_support()
    import autosub
    autosub.main()
