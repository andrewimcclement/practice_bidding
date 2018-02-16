# -*- coding: utf-8 -*-
"""
Created on Fri Feb  2 00:18:45 2018

@author: Lynskyder
"""

from redeal.redeal import A, K, Q, J, T, Hand, Shape, Evaluator


SUITS = ("clubs", "diamonds", "hearts", "spades")


def _get_top_three_suit(suit):
    def top_three_in_suit(hand):
        f""" Count how many of AKQ are in the given {suit}."""
        holding = getattr(hand, suit)
        return holding.count(A) + holding.count(K) + holding.count(Q)

    return top_three_in_suit


top_three_c = _get_top_three_suit("clubs")
top_three_d = _get_top_three_suit("diamonds")
top_three_h = _get_top_three_suit("hearts")
top_three_s = _get_top_three_suit("spades")


def top_three(hand):
    return (top_three_c(hand) + top_three_d(hand) + top_three_h(hand)
            + top_three_s(hand))


def _get_tricks(suit):
    def tricks(hand):
        f""" The number of playing tricks in {suit if suit else 'hand'}."""
        return hand.pt if suit is None else getattr(hand, suit).pt

    return tricks


tricks = _get_tricks(None)
tricks_c = _get_tricks("clubs")
tricks_d = _get_tricks("diamonds")
tricks_h = _get_tricks("hearts")
tricks_s = _get_tricks("spades")

gerber = Evaluator(1)
controls = Evaluator(2, 1)


def _get_rkcb(suit):
    def rkcb(hand):
        f"""Roman Keycard Blackwood in {suit}."""
        holding = getattr(hand, suit)
        return gerber(hand) + holding.count(K), holding.count(Q)

    return rkcb


rkcb_c = _get_rkcb("clubs")
rkcb_d = _get_rkcb("diamonds")
rkcb_h = _get_rkcb("hearts")
rkcb_s = _get_rkcb("spades")
