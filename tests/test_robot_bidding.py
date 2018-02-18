# -*- coding: utf-8 -*-
"""
Created on Sat Feb 17 22:35:39 2018
"""

__author__ = "Andrew I McClement"

import unittest
from practice_bidding.practice_bidding_main import DEFAULT_XML_SOURCE
from practice_bidding.practice_bidding_main import get_bids_from_xml
from practice_bidding.robot_bidding import BiddingProgram


class RobotBiddingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls._chimaera_bids = get_bids_from_xml(DEFAULT_XML_SOURCE)

    def setUp(self):
        self._program = BiddingProgram()

    def test_generate_new_deal(self):
        """ Assert that a new deal is generated randomly. """
        initial_deal = self._program.deal
        self._program.generate_new_deal()
        final_deal = self._program.deal

        self.assertTrue((str(initial_deal.north) != str(final_deal.north))
                        or (str(initial_deal.east) != str(final_deal.east))
                        or (str(initial_deal.south) != str(final_deal.south))
                        or (str(initial_deal.west) != str(final_deal.west)))

    def test_initial_state(self):
        """ Check the program starts with board 1 etc. """
        self.assertEqual(self._program.board_number, 1)
        self.assertEqual(self._program.vulnerability,
                         BiddingProgram.Vulnerability.None_)
        self.assertEqual(self._program._dealer, self._program.Players.North)
        self.assertFalse(self._program.bidding_sequence)

    def test_is_passed_out_all_pass(self):
        """ Check the program correctly knows when a passout occurs. """

        bidding_sequence = []
        for i in range(4):
            self.assertFalse(self._program.is_passed_out(bidding_sequence))
            bidding_sequence.append(self._program._pass)

        self.assertTrue(self._program.is_passed_out(bidding_sequence))

    def test_can_bid_automatically(self):
        self._program.set_opening_bids(self._chimaera_bids)
        self._program._settings["mode"] = \
            self._program.ProgramMode.Automatic

        for _ in range(16):
            with self.subTest(board_number=self._program.board_number):
                count = 0
                while not self._program.is_passed_out(
                        self._program.bidding_sequence):
                    count += 1
                    self._program.bid()
                    self.assertEqual(len(self._program.bidding_sequence),
                                     count)

                self._program.generate_new_deal()


if __name__ == "__main__":
    unittest.main()
