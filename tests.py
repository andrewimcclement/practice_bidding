""" Test suite for practice_bidding. """

import sys
import os
import unittest


def _update_path():
    directory = os.path.dirname(os.path.realpath(__file__))
    # Need the directory one up from /practice_bidding.
    sys.path.append(os.path.split(directory)[0])


try:
    from practice_bidding import parser_tests
    from practice_bidding import xml_parser_tests
except ImportError:
    # This is in place for Travis. It is expected that under normal
    # circumstances the practice_bidding package will be found on sys.path.
    _update_path()

    from practice_bidding import parser_tests
    from practice_bidding import xml_parser_tests


def main():
    """ Run all unit tests in practice_bidding. """
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


if __name__ == "__main__":
    main()
