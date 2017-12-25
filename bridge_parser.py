# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 00:10:37 2017

@author: Lynskyder
"""

import os
import re
from enum import Enum, auto


class ParseResults(Enum):
    """ Enum for results of parsing user input. """
    Quit = auto()
    Back = auto()
    Help = auto()
    Describe = auto()
    Settings = auto()
    Filepath = auto()
    Yes = auto()
    No = auto()
    BridgeBid = auto()
    BridgeContract = auto()
    Integer = auto()
    Unknown = auto()


IMPORTANT_REGEXES = {
    re.compile("^settings$", re.I): ParseResults.Settings,
    re.compile("^(quit|exit|terminate)$", re.I): ParseResults.Quit
    }
STANDARD_REGEXES = {
    re.compile("^h(elp|ow ?to)$", re.I): ParseResults.Help,
    re.compile("^(back|cancel)$", re.I): ParseResults.Back,
    re.compile("^true$", re.I): True,
    re.compile("^false$", re.I): False,
    re.compile("^desc(ribe|ription)?$", re.I): ParseResults.Describe,
    re.compile("^y(es)?$", re.I): ParseResults.Yes,
    re.compile("^no?$", re.I): ParseResults.No,
    re.compile("^([1-7][cdhsn]|p(ass)?)$", re.I): ParseResults.BridgeBid,
    re.compile("^[0-9]+$"): ParseResults.Integer,
    re.compile("^([1-7][cdhsn][ensw]|p(ass)?)$", re.I):
        ParseResults.BridgeContract
    }


def parse(input_):
    """ Parse user input to get its type. """
    for regex, result in IMPORTANT_REGEXES.items():
        if regex.match(input_):
            return result

    for regex, result in STANDARD_REGEXES.items():
        if regex.match(input_):
            return result

    if os.path.isfile(input_):
        return ParseResults.Filepath

    return ParseResults.Unknown


def parse_with_quit(input_):
    result = parse(input_)
    if result == ParseResults.Quit:
        raise KeyboardInterrupt

    return result
