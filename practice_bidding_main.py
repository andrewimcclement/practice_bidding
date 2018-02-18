# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 20:49:14 2017

@author: Lynskyder
"""

import sys
import os
import traceback

from time import sleep
from practice_bidding.robot_bidding import BiddingProgram
from practice_bidding.xml_parsing.xml_parser import get_bids_from_xml
from practice_bidding.bridge_parser import parse_with_quit, ParseResults
from practice_bidding.redeal.redeal import Hand
from practice_bidding.redeal import redeal

redeal.SUITS_FORCE_UNICODE = True

# You may use your own default bidding system here if desired.
_DEFAULT_XML_SOURCE = "chimaera.xml"
DEFAULT_XML_SOURCE = os.path.join(os.path.dirname(os.path.realpath(__file__)),
                                  "example_systems",
                                  _DEFAULT_XML_SOURCE)


def hand_to_str(hand):
    """ Improved one line string representation of a Hand object."""
    # For some reason, redeal.Suit seems to fail under certain circumstances.
    # I assume there is some name collision in the redeal module somewhere
    # and the multiple "from module import *" statements in place cause
    # Suit not to be available.
    return " ".join(map("{}{}".format, redeal.redeal.Suit, hand))


def get_xml_source():
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
        else:
            print(f"\"{filepath}\" is not an XML file.")

        print("Please enter the path to the xml source file to be used"
              " for this program.")
        filepath = input("Path to file: ")
        if filepath.lower() == "default":
            filepath = DEFAULT_XML_SOURCE

        result = parse_with_quit(filepath)
        if result == ParseResults.Help:
            print("Do not escape backslashes. The input is expected "
                  "to be raw.\n\nIf the filename you are trying "
                  "to enter conflicts with a regex used by this "
                  "program, please rename the file to something more "
                  "appropriate.")

    return filepath


def main():
    """
    Bid practice hands opposite a robot.

    The system is taken from an xml document, which can be defined at runtime.
    """

    # Set a prettier printed version of a Hand object.
    # TODO: this doesn't work for some reason.
    Hand._short_str = hand_to_str

    program = BiddingProgram()

    def parse_user_input(input_):
        """
        Parse user input, allowing them to quit and edit program settings.
        """
        result = parse_with_quit(input_)
        if result == ParseResults.Settings:
            program.edit_settings()

        return result

    def _play_board():
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
            result = None
            while result not in {ParseResults.Back, ParseResults.No}:
                input_ = input("Please enter the final contract: ")
                result = parse_user_input(input_)
                if result == ParseResults.BridgeContract:
                    contract = input_.upper()

                    if contract not in {"P", "PASS"}:
                        dd_result = program.get_double_dummy_result(contract)
                        print(f"Double dummy result: {contract} {dd_result}")
                    break
                elif result == ParseResults.Help:
                    print("Enter the correct contract in the form '4HS' for"
                          " 4 hearts by South. Else, enter 'back' or 'no' to "
                          "skip entering the correct final contract.")
                else:
                    print("Sorry, that wasn't a valid contract. Example: "
                          "4HS for 4 hearts by South.")

        # TODO: Add optimal contract (dd_solve).

        result = None
        while result not in {ParseResults.Yes,
                             ParseResults.No}:
            input_ = input("Play another hand? (y/n) ")
            result = parse_user_input(input_)

        return result == ParseResults.Yes

    # Here is the main program.
    try:
        source = get_xml_source()
        bids = get_bids_from_xml(source)
        program.set_opening_bids(bids)
        while _play_board():
            program.generate_new_deal()

    except KeyboardInterrupt:
        # Exit gracefully.
        return
    except Exception as ex:
        print("Sorry! We've hit an error:")
        print(ex)
        traceback.print_exc()
        print("Copy the exception and email andrewimcclement@gmail.com with "
              "the results to help fix your problem.")
        sleep(30)
        raise
    finally:
        print("Thank you for playing!")
        sleep(1)


if __name__ == "__main__":
    main()
