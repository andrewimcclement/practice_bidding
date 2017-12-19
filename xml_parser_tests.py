# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 20:08:26 2017

@author: Lynskyder
"""

import unittest
from xml_parser import get_bids_from_xml
from practice_bidding import DEFAULT_XML_SOURCE


class XmlParserTests(unittest.TestCase):
    def test_parse_chimaera_bids(self):
        get_bids_from_xml(DEFAULT_XML_SOURCE)


if __name__ == "__main__":
    unittest.main()
