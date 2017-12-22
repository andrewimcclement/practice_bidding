import sys
import unittest

import parser_tests
import xml_parser_tests

if __name__ == "__main__":
    try:
        verbosity = int(sys.argv[1])
    except (ValueError, IndexError):
        verbosity = 1

    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    suite.addTests(loader.loadTestsFromModule(parser_tests))
    suite.addTests(loader.loadTestsFromModule(xml_parser_tests))

    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(suite)

    sys.exit(not result.wasSuccessful())
