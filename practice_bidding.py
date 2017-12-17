# -*- coding: utf-8 -*-
"""
Created on Sat Dec 16 20:49:14 2017

@author: Lynskyder
"""

import traceback

from time import sleep
from robot_bidding import BiddingProgram


def main():
    """
    Bid practice hands opposite a robot.

    The system is taken from an xml document, which can be defined at runtime.
    """

    program = BiddingProgram()

    def _parse(input_):
        return program.parse(input_)

    def _play_board():
        print(f"Board: {program.board_number}. Vulnerability: "
              f"{program.vulnerability}")
        print(program.get_hand())
        while not program.is_passed_out(program.bidding_sequence):
            program.bid()
            print([value for value, bid in program.bidding_sequence])

        contract = program.get_contract()
        print(f"Contract: {program.get_contract()}")

        for seat in program.Players:
            print(seat, program.get_hand(seat))

        input_ = input("Is this the correct final contract? (y/n) ")
        if _parse(input_) == program.ParseResults.No:
            result = None
            while result != program.ParseResults.BridgeContract:
                input_ = input("Please enter the final contract: ")
                result = _parse(input_)
                if result == program.ParseResults.No:
                    result = contract
                    break

            contract = result.upper()

        dd_result = program.get_double_dummy_result(contract)
        print(f"Double dummy result: {contract} {dd_result}")

        result = None
        while result not in {program.ParseResults.Yes,
                             program.ParseResults.No}:
            input_ = input("Play another hand? (y/n) ")
            result = _parse(input_)

        return result == program.ParseResults.Yes

    # Here is the main program.
    play_another = True

    try:
        program.get_bids()
        while play_another:
            play_another = _play_board()
            program.generate_new_deal()
    except KeyboardInterrupt:
        print("Thank you for playing!")
        sleep(1)
    except Exception as ex:
        print("Sorry! We've hit an error:")
        print(ex)
        traceback.print_exc()
        print("Copy the exception and email andrewimcclement@gmail.com with "
              "the results to help fix your problem.")
        sleep(20)
        raise


if __name__ == "__main__":
    main()
