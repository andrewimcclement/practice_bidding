# -*- coding: utf-8 -*-
"""
Created on Sat Feb 17 22:35:39 2018
"""

__author__ = "Andrew I McClement"

import unittest
from practice_bidding.robot_bidding import BiddingProgram


class RobotBiddingTests(unittest.TestCase):

    def setUp(self):
        self._program = BiddingProgram()

    def test_generate_new_deal(self):
        """ Assert that a new deal is generated randomly. """
        initial_deal = self._program.deal
        self._program.generate_new_deal()
        final_deal = self._program.deal

        assert ((str(initial_deal.north) != str(final_deal.north))
                or (str(initial_deal.east) != str(final_deal.east))
                or (str(initial_deal.south) != str(final_deal.south))
                or (str(initial_deal.west) != str(final_deal.west)))


if __name__ == "__main__":
    unittest.main()
