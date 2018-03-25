# -*- coding: utf-8 -*-
"""
Created on Sat Mar 24 16:40:01 2018
"""

__author__ = "Andrew I McClement"

import unittest
import inspect

from practice_bidding import standard_formulas
from practice_bidding.example_systems import chimaera_evaluation_methods


class FormulaModuleTests(unittest.TestCase):

    def test_all_methods_lower_case(self):
        modules = {standard_formulas, chimaera_evaluation_methods}
        for module in modules:
            with self.subTest(module=module):
                methods = inspect.getmembers(module, inspect.isfunction)
                for method in methods:
                    method_name = method[0]
                    self.assertEqual(method_name, method_name.lower())


if __name__ == "__main__":
    unittest.main()
