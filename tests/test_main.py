# -*- coding: utf-8 -*-
"""
Created on Sun Mar 18 13:48:17 2018
"""

__author__ = "Andrew I McClement"

import unittest
from unittest.mock import patch

from practice_bidding.practice_bidding_main import get_xml_source
from practice_bidding.practice_bidding_main import DEFAULT_XML_SOURCE
from practice_bidding.bridge_parser import parse_with_quit


class TestMain(unittest.TestCase):
    """ Tests for main() """

    @patch("builtins.print")
    @patch("builtins.input")
    def test_get_default_xml_source(self, mock_input, mock_print):
        mock_input.return_value = "default"
        self.assertEqual(get_xml_source(parse_with_quit),
                         DEFAULT_XML_SOURCE)


if __name__ == "__main__":
    unittest.main()
