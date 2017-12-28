# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 20:49:14 2017

@author: Lynskyder
"""

import sys
import traceback

from time import sleep
from robot_bidding import BiddingProgram
from xml_parser import get_bids_from_xml
from bridge_parser import parse, parse_with_quit, ParseResults


# You may use your own default bidding system here if desired.
DEFAULT_XML_SOURCE = "chimaera.xml"


def get_xml_source():
    """ Get the xml source file path defining bids for this program. """
    try:
        return sys.argv[1]
    except IndexError:
        pass

    while True:
        print("Please enter the path to the xml source file to be used"
              " for this program.")
        filepath = input("Path to file: ")
        if filepath.lower() == "default":
            filepath = DEFAULT_XML_SOURCE

        result = parse(filepath)
        if result == ParseResults.Quit:
            raise KeyboardInterrupt
        elif result == ParseResults.Help:
            print("Do not escape backslashes. The input is expected "
                  "to be raw.\n\nIf the filename you are trying "
                  "to enter conflicts with a regex used by this "
                  "program, please rename the file to something more "
                  "appropriate.")
        elif result == ParseResults.Filepath:
            try:
                assert filepath.endswith(".xml")
                return filepath
            except AssertionError:
                print(f"{filepath} is not a valid file path"
                      ".\nPlease try again.")


def main():
    """
    Bid practice hands opposite a robot.

    The system is taken from an xml document, which can be defined at runtime.
    """

    program = BiddingProgram()

    def _play_board():
        print(f"\nBoard: {program.board_number}. Vulnerability: "
              f"{program.vulnerability}")
        print(f"{program.Players.South}: {program.get_hand()}")
        while not program.is_passed_out(program.bidding_sequence):
            program.bid()
            print([value for value, bid in program.bidding_sequence])

        contract = program.get_contract()
        print(f"Contract: {program.get_contract()}")

        for seat in program.Players:
            print(seat, program.get_hand(seat))

        if contract != "P":
            dd_result = program.get_double_dummy_result(contract)
            print(f"Double dummy result: {contract} {dd_result}")

        input_ = input("Is this the correct final contract? (y/n) ")
        if parse(input_) == ParseResults.No:
            result = None
            while result not in {ParseResults.Back, ParseResults.No}:
                input_ = input("Please enter the final contract: ")
                result = parse_with_quit(input_)
                if result == ParseResults.BridgeContract:
                    contract = input_.upper()

                    if contract not in {"P", "PASS"}:
                        dd_result = program.get_double_dummy_result(contract)
                        print(f"Double dummy result: {contract} {dd_result}")
                    break
                elif result == ParseResults.Help:
                    # TODO: Add Help message.
                    pass
                else:
                    print("Sorry, that wasn't a valid contract. Example: "
                          "4HS for 4 hearts by South.")

        # TODO: Add optimal contract (dd_solve).

        result = None
        while result not in {ParseResults.Yes,
                             ParseResults.No}:
            input_ = input("Play another hand? (y/n) ")
            result = parse_with_quit(input_)
            if result == ParseResults.Help:
                # TODO: Add help message about back and no being options to
                #       cancel this option.
                pass

        return result == ParseResults.Yes

    # Here is the main program.
    play_another = True

    try:
        source = get_xml_source()
        bids = get_bids_from_xml(source)
        program.set_opening_bids(bids)
        while play_another:
            play_another = _play_board()
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
        sleep(20)
        raise
    finally:
        print("Thank you for playing!")
        sleep(1)


if __name__ == "__main__":
    main()
