# -*- coding: utf-8 -*-
"""
Created on Sun Mar 18 13:48:17 2018
"""

__author__ = "Andrew I McClement"

import unittest
from unittest.mock import patch

from practice_bidding.practice_bidding_main import get_xml_source
from practice_bidding.practice_bidding_main import DEFAULT_XML_SOURCE
from practice_bidding.xml_parsing.xml_parser import XmlReaderForFile
from practice_bidding.practice_bidding_main import _get_general_bid_details
from practice_bidding.bridge_parser import parse_with_quit


class TestMain(unittest.TestCase):
    """ Tests for main() """

    @patch("builtins.print")
    @patch("builtins.input")
    def test_get_default_xml_source(self, mock_input, mock_print):
        mock_input.return_value = "default"
        self.assertEqual(get_xml_source(parse_with_quit),
                         DEFAULT_XML_SOURCE)

    def test_count_bids(self):
        reader = XmlReaderForFile(DEFAULT_XML_SOURCE)
        bids = reader.get_bids_from_xml()
        bid_count, non_trivial_bid_count = _get_general_bid_details(bids)
        self.assertGreaterEqual(bid_count, non_trivial_bid_count)
        self.assertGreaterEqual(non_trivial_bid_count, 0)


if __name__ == "__main__":
    unittest.main()
