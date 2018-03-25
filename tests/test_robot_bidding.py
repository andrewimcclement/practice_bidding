# -*- coding: utf-8 -*-
"""
Created on Sat Feb 17 22:35:39 2018
"""

__author__ = "Andrew I McClement"

import unittest
from unittest.mock import patch
from practice_bidding.practice_bidding_main import DEFAULT_XML_SOURCE
from practice_bidding.practice_bidding_main import XmlReaderForFile
from practice_bidding.robot_bidding import BiddingProgram, Bid


class RobotBiddingTests(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        reader = XmlReaderForFile(DEFAULT_XML_SOURCE)
        cls._chimaera_bids = reader.get_bids_from_xml()

    def setUp(self):
        self._program = BiddingProgram()

    @patch("builtins.print")
    @patch("builtins.input")
    def test_edit_settings(self, mock_input, mock_print):
        for i, setting in enumerate(self._program._settings):
            with self.subTest(setting=setting):
                # Select the correct setting, yes to change, back to exit.
                mock_input.side_effect = [f"{i}", "y", "back"]
                original_value = self._program._settings[setting]
                self._program.edit_settings()
                new_value = self._program._settings[setting]
                self.assertNotEqual(new_value, original_value)

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
        """ Check the program knows when a passout occurs. """

        bidding_sequence = []
        for i in range(4):
            self.assertFalse(self._program.is_passed_out(bidding_sequence))
            bidding_sequence.append(self._program._pass)

        self.assertTrue(self._program.is_passed_out(bidding_sequence))
        self.assertEqual(self._program.get_contract(bidding_sequence), "P")

    def test_get_contract_when_suit_bid_by_only_one_player(self):
        pass_ = self._program._pass
        one_spade = Bid("1s", "one spade", [])
        first_bidder_to_bidding_sequence = {
                "N": [one_spade] + [pass_]*3,
                "E": [pass_, one_spade] + [pass_]*3,
                "S": [pass_]*2 + [one_spade] + [pass_]*3,
                "W": [pass_]*3 + [one_spade] + [pass_]*3}

        for bidder in first_bidder_to_bidding_sequence:
            with self.subTest(bidder=bidder):
                bid_sequence = first_bidder_to_bidding_sequence[bidder]
                self._assert_bid_sequence(bid_sequence, f"1S{bidder}")

    def test_get_contract_when_suit_bid_by_several_players(self):
        pass_ = self._program._pass
        one_spade = Bid("1s", "one spade", [])
        two_spades = Bid("2s", "two spades", [])
        three_spades = Bid("3s", "three spades", [])
        competitive_bidding = [one_spade, two_spades, three_spades]

        first_bidder_to_bidding_sequence = {
                "N": competitive_bidding + [pass_]*3,
                "E": [pass_] + competitive_bidding + [pass_]*3,
                "S": [pass_]*2 + competitive_bidding + [pass_]*3,
                "W": [pass_]*3 + competitive_bidding + [pass_]*3}

        for bidder in first_bidder_to_bidding_sequence:
            with self.subTest(bidder=bidder):
                bid_sequence = first_bidder_to_bidding_sequence[bidder]
                self._assert_bid_sequence(bid_sequence, f"3S{bidder}")

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

    @unittest.skip("Test not written yet.")
    def test_gets_valid_double_dummy_result(self):
        pass

    def _assert_bid_sequence(self, bid_sequence, expected_contract):
        self.assertEqual(self._program.get_contract(bid_sequence),
                         expected_contract)

        # Should get the same when using the internal bidding sequence.
        self._program.bidding_sequence.clear()
        self._program.bidding_sequence.extend(bid_sequence)
        self.assertEqual(self._program.get_contract(),
                         expected_contract)


if __name__ == "__main__":
    unittest.main()
