# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 20:08:26 2017

@author: Lynskyder
"""

import unittest
from xml_parser import get_bids_from_xml


class XmlParserTests(unittest.TestCase):
    def test_parse_chimaera_bids(self):
        get_bids_from_xml("chimaera.xml")

    def test_parse_acol_bids(self):
        get_bids_from_xml("acol.xml")


if __name__ == "__main__":
    unittest.main()
