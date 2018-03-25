# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 20:08:26 2017

@author: Lynskyder
"""

import os
import unittest
import math

from practice_bidding.xml_parsing.xml_parser import XmlReaderForFile
from practice_bidding.xml_parsing.xml_parser import \
    _parse_formula_for_condition
from practice_bidding.xml_parsing.xml_parser import VALID_EXPRESSION
from practice_bidding.xml_parsing.xml_parser import _get_min_max_for_method
from practice_bidding.practice_bidding_main import DEFAULT_XML_SOURCE
from practice_bidding.redeal.redeal import Hand


class FakeXmlElement:
    def __init__(self, tag=None, text=None):
        self._sub_elements = {}
        self.tag = None
        self.text = text

    def find(self, tag):
        try:
            return self._sub_elements[tag][0]
        except (KeyError, IndexError):
            return None

    def findall(self, tag):
        return self._sub_elements[tag]

    def add_element(self, tag, text):
        element = FakeXmlElement(tag, text)
        try:
            self._sub_elements[tag].append(element)
        except KeyError:
            self._sub_elements[tag] = [element]


class XmlParserTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # An example hand.
        cls._hand = Hand.from_str("KQJ3 AK32 T5 J32")
        directory = os.path.dirname(DEFAULT_XML_SOURCE)
        cls._acol_location = os.path.join(directory, "acol.xml")
        cls._chimaera_location = DEFAULT_XML_SOURCE

    def test_get_min_max_throws_with_no_values(self):
        element = FakeXmlElement()
        with self.assertRaises(AssertionError):
            _get_min_max_for_method(element)

    def test_get_min_max_throws_with_invalid_values(self):
        element = FakeXmlElement()
        element.add_element("min", "1")
        element.add_element("max", "0")
        with self.assertRaises(AssertionError):
            _get_min_max_for_method(element)

    def test_parse_system_bids(self):
        systems = {self._acol_location, self._chimaera_location}
        for system in systems:
            with self.subTest(system=system):
                reader = XmlReaderForFile(system)
                bids = reader.get_bids_from_xml()
                expected_accept_values = {True, False}
                all_bids = []

                def _add_bid_to_all_bids(bid):
                    all_bids.append(bid)
                    for child_bid in bid.children.values():
                        _add_bid_to_all_bids(child_bid)

                for bid in bids.values():
                    _add_bid_to_all_bids(bid)

                for bid in all_bids:
                    with self.subTest(bid_value=bid.value):
                        self.assertIn(bid.accept(self._hand),
                                      expected_accept_values)

    def test_valid_expressions(self):
        passes = ["h+s-d*2", "h*s-d*c", "12"]
        fails = ["x*h*s", "1.0+d", "d/c"]
        for expression in passes:
            with self.subTest(expression=expression):
                self.assertTrue(VALID_EXPRESSION.match(expression))

        for expression in fails:
            with self.subTest(expression=expression):
                self.assertFalse(VALID_EXPRESSION.match(expression))

    def test_parse_formula_different_operators(self):
        expression1 = "2 * hearts - diamonds+ 1"
        expression2 = " spades + clubs"
        expression3 = "4"
        hand = self._hand
        operators = ["==", ">=", "<=", ">", "<"]

        for operator in operators:
            # formula1 has lhs == rhs.
            formula1 = f"{expression1}{operator}{expression2}"
            # formula2 has lhs > rhs.
            formula2 = f"{expression2}{operator}{expression3}"
            with self.subTest(operator=operator):
                accept1 = _parse_formula_for_condition(formula1)
                accept2 = _parse_formula_for_condition(formula2)

                if "=" in operator:
                    self.assertTrue(accept1(hand))
                else:
                    self.assertFalse(accept1(hand))

                if ">" in operator:
                    self.assertTrue(accept2(hand))
                else:
                    self.assertFalse(accept2(hand))


if __name__ == "__main__":
    unittest.main()
