# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 17:27:28 2017

@author: Lynskyder
"""

import os
import unittest
from practice_bidding.bridge_parser import parse, parse_with_quit, ParseResults


class ParserTests(unittest.TestCase):
    """ Tests for parse method. """
    # TODO: Add tests for other ParseResults.

    def test_parse_bridge_bid(self):
        """ Parse bridge bids correctly. """

        suits = {"c", "d", "h", "s", "n"}
        levels = set(range(1, 8))

        for suit in suits:
            for level in levels:
                bid = f"{level}{suit}"
                with self.subTest(bid=bid):
                    self.assertEqual(ParseResults.BridgeBid, parse(bid))
                    self.assertEqual(ParseResults.BridgeBid,
                                     parse(bid.upper()))
                    self.assertEqual(ParseResults.BridgeBid,
                                     parse_with_quit(bid))

        fails = {"0s", "1e", "h", "8c", "12d", "2HS"}
        for bid in fails:
            with self.subTest(bid=bid):
                self.assertNotEqual(ParseResults.BridgeBid, parse(bid))

    def test_parse_yes_no(self):
        """ Check if the program parses yes/no responses correctly. """
        successes = {"y", "n", "Y", "No", "yES"}
        fails = {"yo", "ya", "ja", "nein", "Never", "yesss", "noooo"}
        results = {ParseResults.Yes, ParseResults.No}

        self.assertEqual(ParseResults.Yes, parse("yes"))

        for input_ in successes:
            with self.subTest(success=input_):
                self.assertIn(parse(input_), results)

        for input_ in fails:
            with self.subTest(fail=input_):
                self.assertNotIn(parse(input_), results)

    def test_parse_quit(self):
        """ Check that attempts to quit are parsed correctly. """

        exit_options = {"quit", "EXIT", "Terminate"}
        for option in exit_options:
            with self.subTest(option=option):
                self.assertEqual(ParseResults.Quit, parse(option))
                with self.assertRaises(KeyboardInterrupt):
                    parse_with_quit(option)

    def test_parse_filepath(self):
        """ Check a filepath is parsed correctly. """
        path = os.path.realpath(__file__)
        self.assertEqual(parse_with_quit(path), ParseResults.Filepath)


if __name__ == "__main__":
    unittest.main()
