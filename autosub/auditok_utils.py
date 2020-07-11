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


def validate_atrim_config(
        trim_dict,
        args=None):
    """
    Validate auditok trim config.
    """
    if "include_before" not in trim_dict or not trim_dict["include_before"]:
        if not args:
            trim_dict["include_before"] = constants.DEFAULT_CONTINUOUS_SILENCE
        else:
            trim_dict["include_before"] = args.max_continuous_silence

    if "include_after" not in trim_dict or not trim_dict["include_after"]:
        if not args:
            trim_dict["include_after"] = constants.DEFAULT_CONTINUOUS_SILENCE
        else:
            trim_dict["include_after"] = args.max_continuous_silence

    if "trim_size" not in trim_dict or not trim_dict["trim_size"]:
        if not args:
            trim_dict["trim_size"] = constants.DEFAULT_CONTINUOUS_SILENCE
        else:
            trim_dict["trim_size"] = args.max_continuous_silence

    if "max_speed" not in trim_dict or not trim_dict["max_speed"]:
        trim_dict["max_speed"] = 18

    validate_auditok_config(trim_dict)


def validate_auditok_config(  # pylint: disable=too-many-branches
        auditok_dict,
        args=None):
    """
    Validate auditok config.
    """
    if "mxcs" not in auditok_dict or not auditok_dict["mxcs"]:
        if not args:
            auditok_dict["mxcs"] = constants.DEFAULT_CONTINUOUS_SILENCE
        else:
            auditok_dict["mxcs"] = args.max_continuous_silence

    if "et" not in auditok_dict or not auditok_dict["et"]:
        if not args:
            auditok_dict["et"] = constants.DEFAULT_ENERGY_THRESHOLD
        else:
            auditok_dict["et"] = args.energy_threshold

    if "mnrs" not in auditok_dict or not auditok_dict["mnrs"]:
        if not args:
            auditok_dict["mnrs"] = constants.DEFAULT_MIN_REGION_SIZE
        else:
            auditok_dict["mnrs"] = args.min_region_size

    if "mxrs" not in auditok_dict or not auditok_dict["mxrs"]:
        if not args:
            auditok_dict["mxrs"] = constants.DEFAULT_MAX_REGION_SIZE
        else:
            auditok_dict["mxrs"] = args.max_region_size

    if "nsml" not in auditok_dict or not auditok_dict["nsml"]:
        if not args:
            auditok_dict["nsml"] = False
        else:
            auditok_dict["nsml"] = args.not_strict_min_length

    if "dts" not in auditok_dict or not auditok_dict["dts"]:
        if not args:
            auditok_dict["dts"] = False
        else:
            auditok_dict["dts"] = args.drop_trailing_silence


def validate_astats_config(
        astats_dict):
    """
    Validate auditok stats config.
    """
    if "max_et" not in astats_dict or not astats_dict["max_et"]:
        astats_dict["max_et"] = 60

    if "min_et" not in astats_dict or not astats_dict["min_et"]:
        astats_dict["min_et"] = 45

    if astats_dict["max_et"] <= astats_dict["min_et"]:
        astats_dict["max_et"] = astats_dict["min_et"] ^ astats_dict["max_et"]
        astats_dict["min_et"] = astats_dict["min_et"] ^ astats_dict["max_et"]
        astats_dict["max_et"] = astats_dict["min_et"] ^ astats_dict["max_et"]

    if "et_pass" not in astats_dict or not astats_dict["et_pass"] or astats_dict["et_pass"] <= 0:
        astats_dict["et_pass"] = 3

    if "max_mxcs" not in astats_dict or not astats_dict["max_mxcs"]:
        astats_dict["max_mxcs"] = 0.2

    if "min_mxcs" not in astats_dict or not astats_dict["min_mxcs"]:
        astats_dict["min_mxcs"] = 0.05

    if astats_dict["max_mxcs"] <= astats_dict["min_mxcs"]:
        astats_dict["max_mxcs"] = astats_dict["min_mxcs"] ^ astats_dict["max_mxcs"]
        astats_dict["min_mxcs"] = astats_dict["min_mxcs"] ^ astats_dict["max_mxcs"]
        astats_dict["max_mxcs"] = astats_dict["min_mxcs"] ^ astats_dict["max_mxcs"]

    if "mxcs_pass" not in astats_dict or not astats_dict["mxcs_pass"]\
            or astats_dict["mxcs_pass"] <= 0:
        astats_dict["mxcs_pass"] = 3

    validate_auditok_config(astats_dict)


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
