#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Defines utils used by auditok.
"""

# Import built-in modules

# Import third-party modules
import auditok
import pysubs2

# Any changes to the path and your own modules
from autosub import constants


def auditok_gen_speech_regions(  # pylint: disable=too-many-arguments
        audio_wav,
        energy_threshold=constants.DEFAULT_ENERGY_THRESHOLD,
        min_region_size=constants.DEFAULT_MIN_REGION_SIZE,
        max_region_size=constants.DEFAULT_MAX_REGION_SIZE,
        max_continuous_silence=constants.DEFAULT_CONTINUOUS_SILENCE,
        mode=auditok.StreamTokenizer.STRICT_MIN_LENGTH,
        is_ssa_event=False):
    """
    Give an input audio/video file, generate proper speech regions.
    """
    asource = auditok.ADSFactory.ads(
        filename=audio_wav, record=True)
    validator = auditok.AudioEnergyValidator(
        sample_width=asource.get_sample_width(),
        energy_threshold=energy_threshold)
    asource.open()
    tokenizer = auditok.StreamTokenizer(
        validator=validator,
        min_length=int(min_region_size * 100),
        max_length=int(max_region_size * 100),
        max_continuous_silence=int(max_continuous_silence * 100),
        mode=mode)

    # auditok.StreamTokenizer.DROP_TRAILING_SILENCE
    tokens = tokenizer.tokenize(asource)
    regions = []
    if not is_ssa_event:
        for token in tokens:
            # get start and end times
            regions.append((token[1] * 10, token[2] * 10))
    else:
        for token in tokens:
            # get start and end times
            regions.append(pysubs2.SSAEvent(
                start=token[1] * 10,
                end=token[2] * 10))
    asource.close()
    # reference
    # auditok.readthedocs.io/en/latest/apitutorial.html#examples-using-real-audio-data
    return regions


class AuditokSTATS:  # pylint: disable=too-many-instance-attributes, too-many-arguments, too-few-public-methods
    """
    Class for storing auditok stats.
    """
    def __init__(self,
                 energy_t,
                 mxcs,
                 mnrs,
                 mxrs,
                 nsml,
                 dts,
                 audio_wav):
        self.energy_t = energy_t
        self.mxcs = mxcs
        self.mnrs = mnrs
        self.mxrs = mxrs
        mode = 0
        if not nsml:
            mode = auditok.StreamTokenizer.STRICT_MIN_LENGTH
        if dts:
            mode = mode | auditok.StreamTokenizer.DROP_TRAILING_SILENCE
        self.mode = mode
        self.audio_wav = audio_wav
        self.events = []
        self.small_region_count = 0
        self.big_region_count = 0
        self.big_region_count = 0
        self.delta_region_size = 0.0
        self.rank_count = 0

    def __lt__(self, auditok_stats2):
        return self.rank_count < auditok_stats2.rank_count


def auditok_gen_stats_regions(
        auditok_stats,
        asource
):
    """
    Give an AuditokSTATS and return itself with regions.
    """
    validator = auditok.AudioEnergyValidator(
        sample_width=asource.get_sample_width(),
        energy_threshold=auditok_stats.energy_t)
    asource.open()
    tokenizer = auditok.StreamTokenizer(
        validator=validator,
        min_length=int(auditok_stats.mnrs * 100),
        max_length=int(auditok_stats.mxrs * 100),
        max_continuous_silence=int(auditok_stats.mxcs * 100),
        mode=auditok_stats.mode)

    # auditok.StreamTokenizer.DROP_TRAILING_SILENCE
    tokens = tokenizer.tokenize(asource)
    max_region_size = int(auditok_stats.mxrs * 1000)
    small_region_size = max_region_size >> 3
    big_region_size = max_region_size - (max_region_size >> 2)
    total_region_size = 0
    for token in tokens:
        # get start and end times
        auditok_stats.events.append(pysubs2.SSAEvent(
            start=token[1] * 10,
            end=token[2] * 10))
        dura = (token[2] - token[1]) * 10
        total_region_size = total_region_size + dura
        if dura <= small_region_size:
            auditok_stats.small_region_count = auditok_stats.small_region_count + 1
        elif dura >= big_region_size:
            auditok_stats.big_region_count = auditok_stats.big_region_count + 1
    average_region_size = total_region_size / len(auditok_stats.events)
    auditok_stats.delta_region_size = abs(average_region_size - (max_region_size >> 1))
    # reference
    # auditok.readthedocs.io/en/latest/apitutorial.html#examples-using-real-audio-data
    return auditok_stats
