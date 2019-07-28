#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Defines autosub's lang codes functionality.
"""
# Import built-in modules
from __future__ import absolute_import, print_function, unicode_literals
import gettext

# Import third-party modules
import langcodes
import wcwidth

# Any changes to the path and your own modules
from autosub import constants

LANG_CODE_TEXT = gettext.translation(domain=__name__,
                                     localedir=constants.LOCALE_PATH,
                                     languages=[constants.CURRENT_LOCALE],
                                     fallback=True)

try:
    _ = LANG_CODE_TEXT.ugettext
except AttributeError:
    # Python 3 fallback
    _ = LANG_CODE_TEXT.gettext


def better_match(desired_language,
                 supported_languages,
                 min_score=90):
    """
    Modified from langcodes.best_match.

    You have software that supports any of the `supported_languages`. You want
    to use `desired_language`. This function lets you choose the right language,
    even if there isn't an exact match.

    Returns:

    - The better-matching language code, which will be a list of the
      `supported_languages` or 'und'
    - The match strength, from 0 to 100

    `min_score` sets the minimum score that will be allowed to match. If all
    the scores are less than `min_score`, the result will be 'und' with a
    strength of 0.

    When there is a tie for the best matching language, the first one in the
    tie will be used.

    Setting `min_score` lower will enable more things to match, at the cost of
    possibly mis-handling data or upsetting users. Read the documentation for
    :func:`tag_match_score` to understand what the numbers mean.

    """

    match_scores = []
    unsupported_languages = []
    for supported in supported_languages:
        try:
            score = langcodes.tag_match_score(desired_language, supported)
            match_scores.append((supported, score))
        except langcodes.tag_parser.LanguageTagError:
            unsupported_languages.append(supported)
            continue

    match_scores = [
        (supported, score) for (supported, score) in match_scores
        if score >= min_score
    ]

    if not match_scores:
        match_scores.append(('und', 0))
    else:
        match_scores.sort(key=lambda item: -item[1])

    return match_scores, unsupported_languages


def wjust(
        str_just,
        length,
        is_left=True
):
    """
    Use wcwidth to just string.
    """
    u_width = wcwidth.wcswidth(str_just)
    if length > u_width:
        just_space = " " * (length - u_width)
    else:
        just_space = ""

    if is_left:
        return str_just + just_space

    return just_space + str_just


def match_print(
        dsr_lang,
        match_list,
        min_score):
    """
    Match, print and return lang codes.
    """
    if not min_score:
        min_score = 90

    print(_("Now match lang codes."))

    if min_score < 0 or min_score > 100:
        print(_("The value of arg of \"-mns\"/\"--min-score\" isn't legal."))
        return None

    print("{column_1}{column_2}".format(
        column_1=wjust(str_just=_("Input:"), length=18),
        column_2=dsr_lang))

    print("{column_1}{column_2}".format(
        column_1=wjust(str_just=_("Score above:"), length=18),
        column_2=min_score))

    match_scores = better_match(
        desired_language=dsr_lang,
        supported_languages=match_list,
        min_score=min_score
    )[0]
    if match_scores[0][0] == 'und':
        print(_("No lang codes been matched."))
        return None

    print("{column_1}{column_2}".format(
        column_1=wjust(str_just=_("Match result"), length=18),
        column_2=_("Score (0-100)")))
    for match in match_scores:
        print("{column_1}{column_2}".format(
            column_1=wjust(str_just=match[0], length=18),
            column_2=match[1]))
    return match_scores[0]
