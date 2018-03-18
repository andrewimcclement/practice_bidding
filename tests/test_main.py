# -*- coding: utf-8 -*-
"""
Created on Sun Mar 18 13:48:17 2018
"""

__author__ = "Andrew I McClement"

import unittest
from unittest import mock
import builtins

from practice_bidding.practice_bidding_main import get_xml_source
from practice_bidding.practice_bidding_main import DEFAULT_XML_SOURCE
from practice_bidding.bridge_parser import parse_with_quit


class TestMain(unittest.TestCase):
    """ Tests for main() """

    def test_get_default_xml_source(self):
        with mock.patch.object(builtins, "input", lambda x: "default"):
            self.assertEqual(get_xml_source(parse_with_quit),
                             DEFAULT_XML_SOURCE)


if __name__ == "__main__":
    unittest.main()
