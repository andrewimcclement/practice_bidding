# -*- coding: utf-8 -*-

from practice_bidding.redeal.redeal import Evaluator

HCP = Evaluator(4, 3, 2, 1)


def tricks(hand):
    return hand.pt
