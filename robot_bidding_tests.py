# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 17:27:28 2017

@author: Lynskyder
"""

import unittest
import robot_bidding as bidding


class BiddingProgramTests(unittest.TestCase):
    """ Tests for BiddingProgram class. """

    def setUp(self):
        self._program = bidding.BiddingProgram()
        self._program._BiddingProgram__xml_source = "chimaera.xml"

    @property
    def _parse_results(self):
        return self._program.ParseResults

    def test_parse_bridge_bid(self):
        """ Parse bridge bids correctly. """

        suits = {"c", "d", "h", "s", "n"}
        levels = set(range(1, 8))

        for suit in suits:
            for level in levels:
                bid = f"{level}{suit}"
                with self.subTest(bid=bid):
                    self.assertEqual(self._parse_results.BridgeBid,
                                     self._program.parse(bid))
                    self.assertEqual(self._parse_results.BridgeBid,
                                     self._program.parse(bid.upper()))

        fails = {"0s", "1e", "h", "8c", "12d", "2HS"}
        for bid in fails:
            with self.subTest(bid=bid):
                self.assertNotEqual(self._parse_results.BridgeBid,
                                    self._program.parse(bid))

    def test_parse_yes_no(self):
        """ Check if the program parses yes/no responses correctly. """
        pass

    def test_parse_quit(self):
        """ Check KeyboardInterrupt is raised when user tries to quit. """

        exit_options = {"quit", "EXIT", "Terminate"}
        for option in exit_options:
            with self.subTest(option=option):
                with self.assertRaises(KeyboardInterrupt):
                    self._program.parse(option)


if __name__ == "__main__":
    unittest.main()
