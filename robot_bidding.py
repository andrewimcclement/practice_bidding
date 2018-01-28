# -*- coding: utf-8 -*-
"""
Created on Sat Nov 25 12:51:07 2017

@author: Lynskyder

Automated practice bidding.

Notes:
    - Further define settings manipulation.
"""

from random import choice
from enum import Enum, auto
from xml_parser import Bid
from bridge_parser import parse_with_quit, ParseResults

try:
    from redeal.redeal import Deal
except ImportError:
    print("Using local copy of redeal, not submodule.")
    from redeal import Deal


class BiddingProgram:
    """ The player is assumed to always sit South. """

    class Players(Enum):
        """
        Bridge players at the table, named after the cardinal directions.
        """
        North = auto()
        East = auto()
        South = auto()
        West = auto()

    class Vulnerability(Enum):
        """ Possible vulnerabilities. """
        None_ = auto()
        Favourable = auto()
        All = auto()
        Unfavourable = auto()

    class ProgramMode(Enum):
        """ Possible modes for the program to run in."""
        # The user makes bids for South.
        Default = auto()
        # The program makes all bids.
        Automatic = auto()

    # Integers correspond to board number modulo 4 for which that player
    # is dealer.
    _dealer_map = {1: Players.North, 2: Players.East, 3: Players.South,
                   0: Players.West}
    _vulnerability = {1: Vulnerability.None_, 3: Vulnerability.Favourable,
                      0: Vulnerability.All, 2: Vulnerability.Unfavourable}
    _pass = Bid("P", "Pass", [])

    def __init__(self):
        # Board number set to 0 as self.generate_new_deal increments board
        # number by 1.
        self._board_state = {"board_number": 0,
                             "deal_generator": Deal.prepare({}),
                             "deal": None,
                             "bidding_sequence": [],
                             "opening_bids": {}}
        self.generate_new_deal()

        self._settings = {"mode": self.ProgramMode.Default,
                          "display_meaning_of_bids": False,
                          "display_meaning_of_possible_bids": False}

        # Get lazily.
        self.__xml_source = None

    @property
    def _root(self):
        return self._board_state["opening_bids"]

    @property
    def deal(self):
        """ The current deal. """
        return self._board_state["deal"]

    def generate_new_deal(self):
        """Get a new deal."""
        self._board_state["deal"] = self._board_state["deal_generator"]()
        self._board_state["bidding_sequence"] = []
        self._board_state["board_number"] += 1

    @property
    def bidding_sequence(self):
        """The bidding sequence so far."""
        return self._board_state["bidding_sequence"]

    @property
    def board_number(self):
        """The current board number."""
        return self._board_state["board_number"]

    @property
    def vulnerability(self):
        """Current vulnerability."""
        board_number = self.board_number % 16
        if board_number in {1, 8, 11, 14}:
            return self.Vulnerability.None_
        elif board_number in {2, 5, 12, 15}:
            return self.Vulnerability.Unfavourable
        elif board_number in {3, 6, 9, 0}:
            return self.Vulnerability.Favourable
        elif board_number in {4, 7, 10, 13}:
            return self.Vulnerability.All

    @property
    def _dealer(self):
        return self._dealer_map[(self.board_number) % 4]

    # shift = index in bidding sequence. By default returns the player
    # who is next to bid.
    # board number is reduced by 1 since it starts at
    def _bidder(self, shift=None):
        if shift is None:
            shift = len(self.bidding_sequence)
        return self._dealer_map[(self.board_number + shift) % 4]

    def parse(self, input_, exclude_settings=False):
        """ Parse user input. """
        result = parse_with_quit(input_)
        if result == ParseResults.Settings and not exclude_settings:
            self.edit_settings()

        return result

    def _get_user_input(self, message, valid_inputs):
        result = self.parse(input(message))
        while result not in valid_inputs:
            result = self.parse(input(message))

        return result

    @property
    def _mode(self):
        return self._settings["mode"]

    def get_hand(self, seat=Players.South):
        """ Returns the hand of the player in the given seat. """
        if seat == self.Players.North:
            return self.deal.north
        elif seat == self.Players.East:
            return self.deal.east
        elif seat == self.Players.South:
            return self.deal.south
        elif seat == self.Players.West:
            return self.deal.west
        elif isinstance(seat, self.Players):
            raise ValueError(seat)
        else:
            raise TypeError(seat, self.Players)

    @classmethod
    def is_passed_out(cls, bidding_sequence):
        """ Checks if a bidding sequence is a passout. """
        if len(bidding_sequence) < 4:
            return False

        last_bids = bidding_sequence[-3:]
        for _, bid in last_bids:
            if bid != cls._pass:
                return False

        return True

    def bid(self):
        """ Get the next bid, whether from the user or the program. """

        # Should have defined bids before trying to bid.
        assert self._root
        if self.is_passed_out(self.bidding_sequence):
            # No further bids can be made.
            return

        # Get the next bid made.
        current_bidder = self._bidder()
        if current_bidder in {self.Players.East, self.Players.West}:
            next_bid = self._pass
        elif current_bidder == self.Players.South and \
                self._mode == self.ProgramMode.Default:
            next_bid = self._user_bid()
        else:
            # Program must make a bid.
            next_bid = self._program_bid(self.get_hand(current_bidder))

        # TODO: Move this logic to practice_bidding.
        if ((next_bid != self._pass)
                and self._settings["display_meaning_of_bids"]):
            print(f"{next_bid.value}: {next_bid.description}")
        self.bidding_sequence.append((next_bid.value, next_bid))

    def _program_bid(self, current_hand):
        potential_bids = None

        if len(self.bidding_sequence) >= 2:
            current_bid = self.bidding_sequence[-2][1]
            if current_bid != self._pass:
                # Partner made a non-trivial bid.
                potential_bids = [bid for bid in current_bid.children.values()
                                  if bid.accept(current_hand)]

        if potential_bids is None:
            potential_bids = [bid for bid in self._root.values()
                              if bid.accept(current_hand)]

        try:
            bid = choice(potential_bids)
        except IndexError:
            # No acceptable bidding options.
            bid = self._pass

        return bid

    def set_opening_bids(self, opening_bids):
        """ Set the opening bids. """
        self._board_state["opening_bids"] = opening_bids

    def _user_bid(self):
        # By default this is an opening bid.
        potential_bids = self._root
        if len(self.bidding_sequence) >= 2:
            current_bid = self.bidding_sequence[-2][1]
            if current_bid != self._pass:
                # Our partner made a non-trivial bid.
                potential_bids = current_bid.children

        bid = None
        while bid is None:
            if self._mode == self.ProgramMode.Automatic:
                # The user has changed the mode of the program.
                current_hand = self.get_hand(self.Players.South)
                bid = self._program_bid(current_hand)
                break

            print(potential_bids.keys())
            selected = input("Your bid: ")
            result = self.parse(selected)
            if result == ParseResults.BridgeBid:
                if selected.upper() in {self._pass.value, "PASS"}:
                    bid = self._pass
                    break

                selected = selected.lower()
                try:
                    bid = potential_bids[selected]
                except KeyError:
                    print("That was not an expected response.")
            elif result == ParseResults.Help:
                print("Enter a bid from one of the potential bids listed."
                      " You must use a single character to define the suit.")

        return bid

    def edit_settings(self):
        """
        Edit the settings of the program.
        These will then be written to an xml file.
        """
        print(self._settings)
        settings_keys = list(self._settings.keys())
        for i, key in enumerate(settings_keys):
            print(f"{i}: {key}")

        while True:
            input_ = input("Enter a key to edit the value for that key, or "
                           "'back' to exit the settings editor.\n"
                           "'Exit' will end the program.\n")
            result = self.parse(input_, True)
            if result == ParseResults.Back:
                return
            elif result != ParseResults.Integer:
                continue

            try:
                key = settings_keys[int(input_)]
            except KeyError:
                print("This is not a valid key.")
                continue

            if key == "mode":
                input_ = input(f"Do you wish to change the mode of the program"
                               f" from {self._mode}? (y/n)")
                result = self.parse(input_, True)
                if result == ParseResults.Yes:
                    if self._mode == self.ProgramMode.Automatic:
                        self._settings["mode"] = self.ProgramMode.Default
                    elif self._mode == self.ProgramMode.Default:
                        self._settings["mode"] = self.ProgramMode.Automatic
            else:
                input_ = input(f"Do you wish to change {key} from "
                               f"{self._settings[key]}? (y/n)")
                if self.parse(input_, True) == ParseResults.Yes:
                    self._settings[key] = not self._settings[key]

    def _first_bidder(self):
        if self._dealer in {self.Players.North, self.Players.West}:
            return self.Players.North
        elif self._dealer in {self.Players.South, self.Players.East}:
            return self.Players.South
        raise NotImplementedError

    def get_contract(self, bidding_sequence=None):
        """ Get the contract (including declarer) from a bidding sequence

        This assumes the bidding sequence is for the current board.
        """

        if bidding_sequence is None:
            bidding_sequence = self.bidding_sequence
        assert self.is_passed_out(bidding_sequence)
        # Must have 3 passes.
        last_bid = bidding_sequence[-4][1]
        if last_bid == self._pass:
            return "P"

        index = len(bidding_sequence) - 4
        suit = last_bid.suit
        suit_bid_by_partner = False
        # Work out who bid the suit first.
        for i in range(index - 2, -1, -4):
            partner_bid = bidding_sequence[i][1]
            if partner_bid == self._pass:
                pass
            elif partner_bid.suit == suit:
                suit_bid_by_partner = True

        bidder = self._bidder(index - 2 if suit_bid_by_partner else index)
        contract = last_bid.value.upper()
        player_map = {self.Players.North: "N", self.Players.East: "E",
                      self.Players.South: "S", self.Players.West: "W"}
        contract += player_map[bidder]
        return contract

    def get_double_dummy_result(self, contract):
        """ Get the number of tricks and corresponding score. """

        assert len(contract) == 3
        assert int(contract[0]) in range(10)
        assert contract[1] in {"C", "D", "H", "S", "N"}
        assert contract[2] in {"N", "E", "S", "W"}

        if contract[2] in {"N", "S"}:
            vulnerability = self.vulnerability in {
                self.Vulnerability.All,
                self.Vulnerability.Unfavourable}
        else:
            vulnerability = self.vulnerability in {
                self.Vulnerability.All,
                self.Vulnerability.Favourable}

        return (self.deal.dd_tricks(contract),
                self.deal.dd_score(contract, vulnerability))
