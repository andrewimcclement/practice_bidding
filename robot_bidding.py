# -*- coding: utf-8 -*-
"""
Created on Sat Nov 25 12:51:07 2017

@author: Lynskyder

Automated practice bidding.

Notes:
    - Double check the seat is correct for the contract.
    - Further define settings manipulation.
"""

import sys
import os
import xml.etree.ElementTree as ET
import math
import re

from random import choice
from enum import Enum, auto

try:
    from .redeal.redeal import Evaluator, Deal, Shape
    from .redeal.redeal.global_defs import Strain
except ImportError:
    print("Redeal package not available. Attempt to find redeal on system...")
    from redeal import Evaluator, Deal, Shape
    from redeal.global_defs import Strain

XML_SOURCE = ("You may use your own default bidding system here if desired.")


class EvaluationCondition:
    """ A condition on how good the hand is, by some method of evaluation. """

    def __init__(self, evaluation_method, minimum=0, maximum=math.inf):
        self.minimum = minimum
        self.maximum = maximum
        self._evaluation_method = evaluation_method

    def accept(self, hand):
        """If the hand evaluates to within the specified range."""
        evaluation = self._evaluation_method(hand)
        return self.minimum <= evaluation <= self.maximum

    def __str__(self):
        return (f"Evaluation method: {self._evaluation_method}. Min: "
                f"{self.minimum}. Max: {self.maximum}.")


class ShapeCondition:
    """Specifies a condition on the shape of a hand."""

    _balanced = Shape("(4333)") + Shape("(4432)") + Shape("(5332)")
    _any = Shape("xxxx")
    _unbalanced = _any - _balanced
    _general_types = {"balanced": _balanced, "any": _any,
                      "unbalanced": _unbalanced}

    def __init__(self, type_, **kwargs):
        if type_ in {"clubs", "diamonds", "hearts", "spades"}:
            minimum = kwargs["minimum"]
            maximum = kwargs["maximum"]

            self.info = {"suit": type_, "min": minimum, "max": maximum}

            def _accept(hand):
                return minimum <= len(getattr(hand, type_)) <= maximum

            self._accept = _accept

        elif type_ in {"longer_than", "strictly_longer_than"}:
            longer_suit = kwargs["longer_suit"]
            shorter_suit = kwargs["shorter_suit"]

            self.info = {"longer_suit": longer_suit,
                         "shorter_suit": shorter_suit,
                         "operator": ">=" if type_ == "longer_than" else ">"}

            def _accept(hand):
                long_suit = getattr(hand, longer_suit)
                short_suit = getattr(hand, shorter_suit)
                return len(long_suit) > len(short_suit)

            self._accept = _accept

        elif type_ == "general":
            self.info = {"general": kwargs["general"]}

            def _accept(hand):
                return self._general_types[self.info["general"]](hand)

            self._accept = _accept

        elif type_ == "shape":
            self.info = {"shape": Shape(kwargs["shape"])}
            self._accept = self.info["shape"]

    def accept(self, hand):
        """If the hand satisfies the given shape constraint."""
        return self._accept(hand)

    def __str__(self):
        return f"{type(self)}: {self.info}"


class Condition:
    """ A set of conditions on a hand. """

    def __init__(self, include, evaluation_conditions, shape_conditions):
        self.include = include
        self.evaluation_conditions = evaluation_conditions
        self.shape_conditions = shape_conditions

    def _conditions(self):
        return self.evaluation_conditions + self.shape_conditions

    def accept(self, hand):
        """
        Returns boolean as to whether the hand satisfies the condition or not.
        """
        for condition in self._conditions():
            if not condition.accept(hand):
                return False

        return True

    def __str__(self):
        return (f"Include: {self.include}\n{self.evaluation_conditions}"
                f"\n{self.shape_conditions}")


class Bid:
    """
    Represents a bridge bid, with links to previous and future bids.

    Includes conditions for a hand to make the bid.
    """

    def __init__(self, value, desc, conditions):
        self.children = {}
        self.description = desc
        self.parent = None
        self.value = value
        self.include_conditions = {condition for condition in conditions
                                   if condition.include}
        self.exclude_conditions = {condition for condition in conditions
                                   if not condition.include}
        self.suit = self._get_suit()

    def accept(self, hand):
        """
        Whether the hand is valid for this bid or not.

        Note if there are no include conditions, a hand will always be
        rejected.
        """
        for condition in self.exclude_conditions:
            if condition.accept(hand):
                return False

        for condition in self.include_conditions:
            if condition.accept(hand):
                return True

        return False

    def _get_suit(self):
        try:
            suit_text = self.value[1].lower()
            suits = {"c": Strain.C, "d": Strain.D, "h": Strain.H,
                     "s": Strain.S, "n": Strain.N}
            return suits[suit_text]
        except (KeyError, IndexError):
            return None


class BiddingProgram:
    """ The player is assumed to always sit South. """

    class ParseResults(Enum):
        """ Enum for results of parsing user input. """
        Quit = auto()
        Back = auto()
        Help = auto()
        Describe = auto()
        Settings = auto()
        Filepath = auto()
        Yes = auto()
        No = auto()
        BridgeBid = auto()
        BridgeContract = auto()
        Integer = auto()
        Unknown = auto()

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
    _chimaera_hcp = Evaluator(4.5, 3, 1.5, 0.75, 0.25)
    _normal_hcp = Evaluator(4, 3, 2, 1)
    _pass = Bid("P", "Pass", [])

    def __init__(self, chimaera_hcp=True):
        # Board number set to 0 as self.generate_new_deal increments board
        # number by 1.
        self._board_state = {"board_number": 0,
                             "deal_generator": Deal.prepare({}),
                             "deal": None,
                             "bidding_sequence": [],
                             "opening_bids": {}}
        self.generate_new_deal()
        self._hcp = self._chimaera_hcp if chimaera_hcp else self._normal_hcp

        def _points(hand):
            hcp = self._hcp(hand)
            club_length = max(len(hand.clubs) - 4, 0)
            diamond_length = max(len(hand.diamonds) - 4, 0)
            heart_length = max(len(hand.hearts) - 4, 0)
            spade_length = max(len(hand.spades) - 4, 0)
            return (hcp + club_length + diamond_length + heart_length
                    + spade_length)

        self._points = _points

        important_regexes = {
            re.compile("^settings$", re.I): self.ParseResults.Settings,
            re.compile("^(quit|exit|terminate)$", re.I): self.ParseResults.Quit
            }
        standard_regexes = {
            re.compile("^h(elp|ow ?to)?$", re.I): self.ParseResults.Help,
            re.compile("^b(ack)?$", re.I): self.ParseResults.Back,
            re.compile("^true$", re.I): True,
            re.compile("^false$", re.I): False,
            re.compile("^desc(ribe|ription)?$", re.I):
                self.ParseResults.Describe,
            re.compile("^y(es)?$", re.I): self.ParseResults.Yes,
            re.compile("^no?$", re.I): self.ParseResults.No,
            re.compile("^([1-7][cdhsn]|p(ass)?)$", re.I):
                self.ParseResults.BridgeBid,
            re.compile("^[0-9]+$"): self.ParseResults.Integer,
            re.compile("^([1-7][cdhsn][ensw]|p(ass)?)$", re.I):
                self.ParseResults.BridgeContract
            }

        self._regexes = {"important": important_regexes,
                         "standard": standard_regexes}

        self._settings = {"mode": self.ProgramMode.Default,
                          "display_meaning_of_bids": False,
                          "display_meaning_of_possible_bids": False}

        # Get lazily.
        self.__xml_source = None

        self._get_settings()

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
        for regex, result in self._regexes["important"].items():
            if re.match(regex, input_):
                if result == self.ParseResults.Quit:
                    raise KeyboardInterrupt
                elif result == self.ParseResults.Settings:
                    if not exclude_settings:
                        self.edit_settings()

                    return result

        for regex, result in self._regexes["standard"].items():
            if re.match(regex, input_):
                return result

        if os.path.isfile(input_):
            return self.ParseResults.Filepath

        return self.ParseResults.Unknown

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

        self.bidding_sequence.append((next_bid.value, next_bid))

    def _program_bid(self, current_hand):
        if len(self.bidding_sequence) < 2:
            # First person to bid.
            potential_bids = [bid for bid in self._root.values()
                              if bid.accept(current_hand)]
        else:
            # The last bid made by partner (2 bids ago).
            current_bid = self.bidding_sequence[-2][1]
            potential_bids = [bid for bid in current_bid.children.values()
                              if bid.accept(current_hand)]

        try:
            bid = choice(potential_bids)
        except IndexError:
            # No acceptable bidding options.
            bid = self._pass

        return bid

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
            print(potential_bids.keys())
            selected = input("Your bid: ")
            result = self.parse(selected)
            if result == self.ParseResults.BridgeBid:
                if selected.upper() == self._pass.value:
                    bid = self._pass
                    break

                selected = selected.lower()
                try:
                    bid = potential_bids[selected]
                except KeyError:
                    print("That was not an expected response.")

        return bid

    def edit_settings(self):
        """
        Edit the settings of the program.
        These will then be written to an xml file.
        """
        print(self._settings)
        settings_keys = self._settings.keys()
        for i, key in enumerate(settings_keys):
            print(f"{i}: {key}")

        while True:
            input_ = input("Enter a key to edit the value for that key, or "
                           "'back' to exit the settings editor.\n"
                           "'Exit' will end the program.\n")
            result = self.parse(input_, True)
            if result == self.ParseResults.Back:
                return
            elif result != self.ParseResults.Integer:
                continue

            key = settings_keys[int(input_)]

            if key == "mode":
                input_ = input(f"Do you wish to change the mode of the program"
                               f" from {self._mode}? (y/n)")
                result = self.parse(input_, True)
                if result == self.ParseResults.Yes:
                    if self._mode == self.ProgramMode.Automatic:
                        self._settings["mode"] = self.ProgramMode.Default
                    elif self._mode == self.ProgramMode.Default:
                        self._settings["mode"] = self.ProgramMode.Automatic
            else:
                input_ = input(f"Do you wish to change {key} from "
                               f"{self._settings[key]}? (y/n))")
                if self.parse(input_, True) == self.ParseResults.Yes:
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

        print(f"{suit_bid_by_partner}, {suit}, {index}")
        bidder = self._bidder(index - 2 if suit_bid_by_partner else index)
        contract = last_bid.value.upper()
        player_map = {self.Players.North: "N", self.Players.East: "E",
                      self.Players.South: "S", self.Players.West: "W"}
        contract += player_map[bidder]
        return contract

    # Should get the settings from stored xml file if it exists, else
    # create default settings.
    def _get_settings(self):
        pass

    def _parse_xml(self, source):
        def _define_bid(xml_bid):
            value, desc = xml_bid.find("value"), xml_bid.find("desc")
            xml_conditions = xml_bid.findall("condition")
            conditions = []

            for xml_condition in xml_conditions:
                evaluation_conditions = \
                    _get_evaluation_condition(xml_condition)
                shape_conditions = _get_shape_conditions(xml_condition)
                type_ = xml_condition.attrib["type"]
                if type_ == "include":
                    include = True
                elif type_ == "exclude":
                    include = False
                else:
                    raise NotImplementedError(
                        type_, "Expected 'include' or 'exclude'")

                conditions.append(Condition(include, evaluation_conditions,
                                            shape_conditions))

            return Bid(value.text, desc.text, conditions)

        def _get_evaluation_condition(xml_condition):
            evaluation_conditions = []
            evaluation = xml_condition.find("evaluation")
            if not evaluation:
                return evaluation_conditions

            for method in evaluation:
                if method.tag == "hcp":
                    try:
                        minimum = float(method.find("min").text)
                    except AttributeError:
                        # Minimum is not defined, so is assumed to be 0.
                        minimum = 0

                    try:
                        maximum = float(method.find("max").text)
                    except AttributeError:
                        # Maximum is not defined, so use infinity.
                        maximum = math.inf

                    evaluation_condition = EvaluationCondition(
                        self._hcp, minimum, maximum)

                    evaluation_conditions.append(evaluation_condition)
                elif method.tag == "tricks":
                    # TODO: Add tricks method.
                    continue
                elif method.tag == "points":
                    try:
                        minimum = float(method.find("min").text)
                    except AttributeError:
                        # Minimum is not defined, assumed to be 0.
                        minimum = 0

                    try:
                        maximum = float(method.find("max").text)
                    except AttributeError:
                        maximum = math.inf

                    evaluation_condition = EvaluationCondition(
                        self._points, minimum, maximum)

                    evaluation_conditions.append(evaluation_condition)
                else:
                    raise NotImplementedError(method.tag)

            return evaluation_conditions

        def _get_shape_conditions(xml_condition):
            shapes = xml_condition.findall("shape")
            shape_conditions = []
            for shape in shapes:
                try:
                    type_ = shape.attrib["type"]
                except KeyError:
                    # Empty shape definition.
                    break
                if shape.text:
                    if type_ == "shape":
                        shape_conditions.append(
                            ShapeCondition(type_, shape=shape.text))
                    elif type_ == "general":
                        shape_conditions.append(
                            ShapeCondition(type_, general=shape.text))
                elif type_ in {"clubs", "diamonds", "hearts", "spades"}:
                    try:
                        minimum = shape.find("minimum").text
                    except AttributeError:
                        minimum = 0
                    try:
                        maximum = shape.find("maximum").text
                    except AttributeError:
                        maximum = 13

                    assert minimum <= maximum, f"{type_}: {minimum}->{maximum}"

                    shape_conditions.append(
                        ShapeCondition(type_, minimum=minimum,
                                       maximum=maximum))
                elif type_ in {"longer_than", "strictly_longer_than"}:
                    longer_suit = shape.find("longer_suit").text
                    shorter_suit = shape.find("shorter_suit").text
                    shape_conditions.append(
                        ShapeCondition(type_, longer_suit=longer_suit,
                                       shorter_suit=shorter_suit))
                else:
                    raise NotImplementedError(type_)

            return shape_conditions

        def _find_all_children_bids(bid, xml_bid):
            for child_xml_bid in xml_bid.findall("bid"):
                try:
                    child_bid = _define_bid(child_xml_bid)
                except (NotImplementedError, AssertionError):
                    print(f"Error in XML in child of {bid.value}")
                    while bid.parent:
                        print(f"Parent is {bid.parent.value}")
                        bid = bid.parent
                    raise

                child_bid.parent = bid
                assert child_bid.value not in bid.children
                bid.children[child_bid.value] = child_bid
                _find_all_children_bids(child_bid, child_xml_bid)

        # The actual function.
        tree = ET.parse(source, ET.XMLParser(encoding="utf-8"))
        root = tree.getroot()
        # Reset self._root to empty dictionary of opening bids.
        self._root.clear()
        for xml_bid in root:
            bid = _define_bid(xml_bid)
            assert bid.value not in self._root
            self._root[bid.value] = bid
            _find_all_children_bids(bid, xml_bid)

    def get_double_dummy_result(self, contract):
        """ Get the number of tricks and corresponding score. """
        vulnerability = self.vulnerability in {self.Vulnerability.All,
                                               self.Vulnerability.Unfavourable}
        return (self.deal.dd_tricks(contract),
                self.deal.dd_score(contract, vulnerability))

    @property
    def _xml_source(self):
        if not self.__xml_source:
            self.set_xml_source()
        return self.__xml_source

    def set_xml_source(self):
        """ Edit the xml source file path defining bids for this program. """
        try:
            self.__xml_source = sys.argv[1]
        except IndexError:
            while True:
                print("Please enter the path to the xml source file to be used"
                      " for this program.")
                filepath = input("Path to file: ")
                if filepath.lower() == "default":
                    filepath = XML_SOURCE
                # Check if the user wants to exit/edit settings.
                if self.parse(filepath) == self.ParseResults.Filepath:
                    try:
                        assert filepath.endswith(".xml")
                        self.__xml_source = filepath
                        return
                    except AssertionError:
                        print(f"{filepath} is not a valid file path"
                              ".\nPlease try again.")

    def get_bids(self):
        """ Get bids from predefined xml source """
        self._parse_xml(self._xml_source)
