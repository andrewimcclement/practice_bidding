# -*- coding: utf-8 -*-
"""
Created on Sun Dec 17 04:44:04 2017

@author: Lynskyder
"""

import math
import xml.etree.ElementTree as ET
import re

from practice_bidding import standard_formulas
from practice_bidding.redeal.redeal import Shape, Evaluator
from practice_bidding.redeal.redeal.global_defs import Strain


CHIMAERA_HCP = Evaluator(4.5, 3, 1.5, 0.75, 0.25)
HCP = Evaluator(4, 3, 2, 1)
OPERATOR = re.compile("<[^=]|>[^=]|[!<>=]=")
VALID_EXPRESSION = re.compile("^([cdhs]|[0-9]+)([-+*]([cdhs]|[0-9]+))*$")


def standard_shape_points(hand):
    return sum((max(len(suit) - 4, 0)) for suit in hand.shape)


def freakness_points(hand):
    """Points for the shape of a hand based on its freakiness."""
    return hand.freakness/2 - 0.5


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
    general_types = {"balanced": _balanced, "any": _any,
                     "unbalanced": _unbalanced}

    def __init__(self, info, accept):
        self._accept = accept
        self.info = info

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


class MultiCondition:
    def __init__(self, conditions):
        assert conditions
        self.conditions = conditions

    def accept(self, hand):
        raise NotImplementedError("Abstract method.")


class AndCondition(MultiCondition):
    """
    Collection of conditions which are all required to be true to accept a
    hand.
    """

    def accept(self, hand):
        """
        If all conditions are satisfied by the hand or not.
        """
        for condition in self.conditions:
            if not condition.accept(hand):
                return False

        return True


class NotCondition:
    """ An inverted condition """
    def __init__(self, condition):
        assert condition
        self.condition = condition

    def accept(self, hand):
        """ The inverse of self.condition """
        return not self.condition.accept(hand)


class OrCondition:
    """
    Collection of conditions of which at least one is required to be true to
    accept a hand.
    """

    def accept(self, hand):
        for condition in self.conditions:
            if condition.accept(hand):
                return True

        return False


def _parse_general_formula(formula):
    raise NotImplementedError

    formula = "".join(formula.split()).lower()

    assert len(OPERATOR.findall(formula)) >= 1
    assert ("clubs" in formula
            or "diamonds" in formula
            or "hearts" in formula
            or "spades" in formula
            or "hcp" in formula
            or "top_three" in formula
            or "controls" in formula
            or "aces" in formula
            or "rkcbc" in formula
            or "rkcbd" in formula
            or "rkcbh" in formula
            or "rkcbs" in formula
            or "top_three_c" in formula
            or "top_three_d" in formula
            or "top_three_h" in formula
            or "top_three_s" in formula
            or "ace_c" in formula
            or "ace_d" in formula
            or "ace_h" in formula
            or "ace_s" in formula
            or "king_c" in formula
            or "king_d" in formula
            or "king_h" in formula
            or "king_s" in formula
            or "queen_s" in formula
            or "")


class FormulaParser:
    _VALID_EXPRESSION = re.compile("^([cdhs]|[0-9]+)([-+*]([cdhs]|[0-9]+))*$")

    def __init__(self, formula_module):
        self._valid_formula_regex = self._get_formula_regex(formula_module)

    @staticmethod
    def _get_formula_regex(formula_module):
        pass


def _parse_formula(formula):
    formula = "".join(formula.split()).lower()
    assert OPERATOR.findall(formula)


# Does NOT accept brackets in formula!
def _parse_formula_for_condition(formula):
    """ Parse a formula involving suit lengths.

    Returns a function to accept or reject a hand.
    """

    formula = formula.lower()
    formula = "".join(formula.split())

    assert ("clubs" in formula
            or "diamonds" in formula
            or "hearts" in formula
            or "spades" in formula)

    # Order matters - must check for >=/<= before >/<.
    operators = ["==", "!=", ">=", "<=", ">", "<"]
    assert len(OPERATOR.findall(formula)) == 1

    simplified_formula = formula.replace("spades", "s")
    simplified_formula = simplified_formula.replace("hearts", "h")
    simplified_formula = simplified_formula.replace("diamonds", "d")
    simplified_formula = simplified_formula.replace("clubs", "c")

    result = [simplified_formula]
    i = 0
    operator = None
    while len(result) == 1:
        to_parse = result[0]
        operator = operators[i]
        result = to_parse.split(operator)
        i += 1

    assert len(result) == 2

    # Not a foolproof guarantee, but better than nothing.
    for expression in result:
        assert VALID_EXPRESSION.match(expression), expression

    def _accept(hand):
        s, h, d, c = hand.shape
        return eval(f"{simplified_formula}")

    return _accept


def get_bids_from_xml(filepath=None):
    """ Returns a dictionary of opening bids. """
    tree = ET.parse(filepath, ET.XMLParser(encoding="utf-8"))
    root = tree.getroot()

    try:
        formula_module_location = root.attrib["formulas"]
        formula_module = __import__(formula_module_location)
    except KeyError:
        formula_module = None

    def get_formula(method_name):
        try:
            return getattr(formula_module, method_name)
        except AttributeError:
            try:
                return getattr(standard_formulas, method_name)
            except AttributeError:
                raise NotImplementedError(f"{method_name} not defined in "
                                          f"{formula_module_location}.")

    try:
        hcp = get_formula("HCP")
    except AttributeError:
        # HCP not defined in formula_module.
        hcp_style = root.attrib["hcp"]
        if hcp_style == "standard":
            hcp = HCP
        elif hcp_style == "chimaera":
            hcp = CHIMAERA_HCP
        else:
            raise NotImplementedError("HCP style not defined.")

    shape_style = root.attrib["shape"]
    if shape_style == "standard":
        shape_points = standard_shape_points
    elif shape_style == "freakiness":
        shape_points = freakness_points
    else:
        raise NotImplementedError("Shape points not defined.")

    def _points(hand):
        return hcp(hand) + shape_points(hand)

    def _define_bid(xml_bid):
        value, desc = xml_bid.find("value"), xml_bid.find("desc")
        xml_conditions = xml_bid.findall("condition")
        conditions = []

        for xml_condition in xml_conditions:
            evaluation_conditions = \
                _get_evaluation_condition(xml_condition)

            evaluation_conditions.append(_get_formulas(xml_condition))
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

    def _get_formulas(xml_condition):
        formulas = []
        for xml_formula in xml_condition.findall("formula"):
            formula_text = xml_formula.text
            formula = _parse_formula(formula_text, formula_module)
            formulas.append(formula)

        return formulas

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
                    hcp, minimum, maximum)

                evaluation_conditions.append(evaluation_condition)
            elif method.tag == "tricks":
                try:
                    minimum = float(method.find("min").text)
                except AttributeError:
                    minimum = 0

                try:
                    maximum = float(method.find("max").text)
                except AttributeError:
                    maximum = math.inf

                assert (minimum, maximum) != (0, math.inf)

                try:
                    tricks = get_formula("tricks")
                except NotImplementedError:
                    def pt(hand):
                        return hand.pt

                    tricks = pt

                evaluation_condition = EvaluationCondition(
                    tricks, minimum, maximum)
                evaluation_conditions.append(evaluation_condition)

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
                    _points, minimum, maximum)

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
                print("Warning: empty shape definition.")
                continue

            if type_ == "shape":
                info = {type_: shape.text}
                shape_condition = ShapeCondition(info, Shape(shape.text))
            elif type_ == "general":
                info = {type_: shape.text}
                accept = ShapeCondition.general_types[shape.text]
                shape_condition = ShapeCondition(info, accept)
            elif type_ == "formula":
                formula = shape.text
                accept = _parse_formula_for_condition(formula)
                info = {type_: formula}
                shape_condition = ShapeCondition(info, accept)
            elif type_ in {"clubs", "diamonds", "hearts", "spades"}:
                try:
                    minimum = max(int(shape.find("min").text), 0)
                except AttributeError:
                    minimum = 0
                try:
                    maximum = min(int(shape.find("max").text), 13)
                except AttributeError:
                    maximum = 13

                assert minimum <= maximum, f"{type_}: {minimum}->{maximum}"
                assert (minimum, maximum) != (0, 13), "Min/max not defined."

                info = {"formula": f"{minimum} <= {type_} <= {maximum}"}

                def get_accept(suit):

                    def accept(hand):
                        return minimum <= len(getattr(hand, suit)) <= maximum

                    return accept

                shape_condition = ShapeCondition(info, get_accept(type_))
            elif type_ in {"longer_than", "strictly_longer_than"}:
                longer_suit = shape.find("longer_suit").text
                shorter_suit = shape.find("shorter_suit").text
                operator = "<=" if type_ == "longer_than" else "<"
                info = {"formula": f"{shorter_suit} {operator} {longer_suit}"}
                accept = _parse_formula_for_condition(info["formula"])
                shape_condition = ShapeCondition(info, accept)
            else:
                raise NotImplementedError(type_)

            shape_conditions.append(shape_condition)

        return shape_conditions

    def _find_all_children_bids(bid, xml_bid):
        for child_xml_bid in xml_bid.findall("bid"):
            try:
                child_bid = _define_bid(child_xml_bid)
            except Exception:
                value = child_xml_bid.find("value")
                if value:
                    print(f"Error in XML of {value.text}")

                try:
                    id_ = child_xml_bid.attrib["id"]
                    print(f"Error in XML of bid with ID {id_}")
                except KeyError:
                    pass

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
    # Reset self._root to empty dictionary of opening bids.
    result = {}
    for xml_bid in root:
        bid = _define_bid(xml_bid)
        assert bid.value not in result
        result[bid.value] = bid
        _find_all_children_bids(bid, xml_bid)

    return result
