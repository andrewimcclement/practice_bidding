# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 20:49:14 2017
"""

__author__ = "Andrew I McClement"
__email__ = "andrewimcclement@gmail.com"


import os
import sys
from time import sleep
import traceback
from typing import Callable, Dict

from practice_bidding.xml_parsing.xml_parser import Bid
from practice_bidding.bridge_parser import ParseResults
from practice_bidding.redeal.redeal import Hand
from practice_bidding.redeal import redeal
from practice_bidding.robot_bidding import BiddingProgram
from practice_bidding.xml_parsing.xml_parser import get_bids_from_xml

redeal.SUITS_FORCE_UNICODE = True

# You may use your own default bidding system here if desired.
_DEFAULT_XML_SOURCE = "chimaera.xml"
DEFAULT_XML_SOURCE = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                  "example_systems",
                                  _DEFAULT_XML_SOURCE)


def hand_to_str(hand: Hand) -> str:
    """ Improved one line string representation of a Hand object."""
    # For some reason, redeal.Suit seems to fail under certain circumstances.
    # I assume there is some name collision in the redeal module somewhere
    # and the multiple "from module import *" statements in place cause
    # Suit not to be available.
    return " ".join(map("{}{}".format, redeal.redeal.Suit, hand))


def get_xml_source(parse: Callable[[str], ParseResults]) -> str:
    """ Get the xml source file path defining bids for this program. """
    filepath = ""
    if __name__ == "__main__":
        try:
            filepath = sys.argv[1]
        except IndexError:
            pass

    result = ParseResults.Filepath
    while result != ParseResults.Filepath or not filepath.endswith(".xml"):
        if result != ParseResults.Filepath:
            # Previous attempt failed to give a valid filepath.
            print(f"\"{filepath}\" is not a valid file path."
                  "\nPlease try again.")
        elif filepath:
            print(f"\"{filepath}\" is not an XML file.")

        print("Please enter the path to the xml source file to be used"
              " for this program.")
        filepath = input("Path to file: ")
        if filepath.lower() == "default":
            filepath = DEFAULT_XML_SOURCE

        result = parse(filepath)
        if result == ParseResults.Help:
            print("Do not escape backslashes. The input is expected "
                  "to be raw.\n\nIf the filename you are trying "
                  "to enter conflicts with a regex used by this "
                  "program, please rename the file to something more "
                  "appropriate.")

    return filepath


def _get_final_contract(parse_method,
                        rejection_options) -> (bool, str):
    result = None
    help_message = ("Enter the correct contract in the form '4HS' for"
                    " 4 hearts by South. Else, enter 'back' or 'no' to "
                    "skip entering the correct final contract.")
    input_, result = parse_method(
        "Please enter the final contract: ",
        {ParseResults.BridgeContract}.union(rejection_options),
        help_message)

    # Convert to upper case for returning a bridge contract.
    return result not in rejection_options, input_.upper()


def _play_board(program, get_user_input, parse_user_input):
    print(f"\nBoard: {program.board_number}. Vulnerability: "
          f"{program.vulnerability}")
    print(f"{program.Players.South}: {program.get_hand()}")
    while not program.is_passed_out(program.bidding_sequence):
        program.bid()
        print([bid.value for bid in program.bidding_sequence])

    contract = program.get_contract()
    print(f"Contract: {program.get_contract()}")

    for seat in program.Players:
        print(seat, program.get_hand(seat))

    if contract != "P":
        dd_result = program.get_double_dummy_result(contract)
        print(f"Double dummy result: {contract} {dd_result}")

    input_ = input("Is this the correct final contract? (y/n) ")
    if parse_user_input(input_) == ParseResults.No:
        rejection_options = {ParseResults.Back, ParseResults.No}
        result, contract = _get_final_contract(program.get_validated_input,
                                               rejection_options)
        if result and contract not in {"P", "PASS"}:
            dd_result = program.get_double_dummy_result(contract)
            print(f"Double dummy result: {contract} {dd_result}")

    # TODO: Add optimal contract (dd_solve).

    input_, result = get_user_input("Play another hand? (y/n)",
                                    {ParseResults.Yes, ParseResults.No})

    return result == ParseResults.Yes


def _get_general_bid_details(bids) -> (int, int):
    """ Gets #bids and #bids with non trivial conditions."""
    counts = [0, 0]

    def _process_bid(bid):
        counts[0] += 1
        counts[1] += bid.condition.is_non_trivial_condition
        for _, child in bid.children.items():
            _process_bid(child)

    for _, bid in bids.items():
        _process_bid(bid)

    return counts


def print_general_bid_details(bids: Dict[str, Bid]):
    """ Prints how many bids there are. """
    bid_count, non_trivial_bid_count = _get_general_bid_details(bids)

    print(f"{bid_count} bids found.")
    print(f"{non_trivial_bid_count} non-trivial bids found.")


def main():
    """
    Bid practice hands opposite a robot.

    The system is taken from an xml document, which can be defined at runtime.
    """

    # Set a prettier printed version of a Hand object.
    Hand.__str__ = hand_to_str

    program = BiddingProgram()

    try:
        source = get_xml_source(program.parse)
        bids = get_bids_from_xml(source)
        print_general_bid_details(bids)
        program.set_opening_bids(bids)
        while _play_board(program, program.get_validated_input,
                          program.parse):
            program.generate_new_deal()

    except KeyboardInterrupt:
        # Exit gracefully.
        return
    except Exception as ex:
        print("Sorry! We've hit an error:")
        print(ex)
        traceback.print_exc()
        print(f"Copy the exception and email {__email__} with "
              "the results to help fix your problem.")
        sleep(30)
        raise
    finally:
        print("Thank you for playing!")
        sleep(1)


if __name__ == "__main__":
    main()
