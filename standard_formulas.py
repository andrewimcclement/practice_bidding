# -*- coding: utf-8 -*-
"""
All methods must be lower case.
"""

from practice_bidding.redeal.redeal import Evaluator

HCP = Evaluator(4, 3, 2, 1)


def hcp(hand):
    """ Get the high card point count for a hand."""
    return HCP(hand)


def tricks(hand):
    """ Get the playing tricks for a hand. """
    return hand.pt
