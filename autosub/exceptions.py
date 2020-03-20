#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defines exceptions used by autosub.
"""

# Import built-in modules
import sys

# Import third-party modules


# Any changes to the path and your own modules


class AutosubException(Exception):
    """
    Raised when something need to print
    and works need to be stopped.
    """

    def __init__(self, msg):
        super(AutosubException, self).__init__(msg)
        try:
            self.msg = str(msg)
        except UnicodeEncodeError:
            self.msg = msg.encode(sys.stdout.encoding)

    def __str__(self):
        return self.msg


class ConversionException(AutosubException):
    """
    Raised when short-term audio fragments conversion failed.
    """


class SpeechToTextException(AutosubException):
    """
    Raised when speech-to-text failed.
    """
