# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 20:08:26 2017

@author: Lynskyder
"""

import unittest
from xml_parser import get_bids_from_xml
from xml_parser import _parse_formula_for_condition
from xml_parser import VALID_EXPRESSION
from redeal.redeal import Hand


class XmlParserTests(unittest.TestCase):

    def test_parse_chimaera_bids(self):
        get_bids_from_xml("chimaera.xml")

    def test_parse_acol_bids(self):
        get_bids_from_xml("acol.xml")

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
        hand = Hand.from_str("KQJ3 AK32 T5 J32")
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
