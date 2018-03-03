# -*- coding: utf-8 -*-
"""
Created on Sun Dec 17 04:44:04 2017

@author: Lynskyder
"""

import os
import importlib.util
import math
import xml.etree.ElementTree as ET
import re

from practice_bidding import standard_formulas
from practice_bidding.redeal.redeal import Shape, Evaluator, Hand
from practice_bidding.redeal.redeal.global_defs import Strain


CHIMAERA_HCP = Evaluator(4.5, 3, 1.5, 0.75, 0.25)
HCP = Evaluator(4, 3, 2, 1)
OPERATOR = re.compile("<[^=]|>[^=]|[!<>=]=")
VALID_EXPRESSION = re.compile("^([cdhs]|[0-9]+)([-+*]([cdhs]|[0-9]+))*$")


def standard_shape_points(hand):
    """ Points for length above 4 in a suit. """
    return sum((max(suit_length - 4, 0)) for suit_length in hand.shape)


def freakness_points(hand):
    """Points for the shape of a hand based on its freakiness."""
    return hand.freakness/2 - 0.5


class Bid:
    """
    Represents a bridge bid, with links to previous and future bids.

    Includes conditions for a hand to make the bid.
    """

    _suits = {"c": Strain.C, "d": Strain.D, "h": Strain.H,
              "s": Strain.S, "n": Strain.N, "p": None}

    def __init__(self, value, desc, condition):
        self.children = {}
        self.description = desc
        self.parent = None
        self.value = value

        self.condition = condition
        self.suit = self._get_suit()

    def accept(self, hand):
        """
        Whether the hand is valid for this bid or not.

        Note if there are no include conditions, a hand will always be
        rejected.
        """
        return self.condition.accept(hand)

    def _get_suit(self):
        try:
            suit_text = self.value[1].lower()
        except IndexError:
            suit_text = self.value[0].lower()

        return self._suits[suit_text]


class BaseCondition:
    """ Base class for all condition classes. """
    _trial_hand = Hand.from_str("AKQJ T98 765 432")

    def __init__(self, accept, info):
        accept(self._trial_hand)
        self._accept = accept
        assert info
        self._info = info

    @property
    def info(self):
        """ Get a description of the condition. """
        return self._info

    def accept(self, hand):
        """ Determine if the hand satisfies the condition or not. """
        return self._accept(hand)

    def __str__(self):
        return f"{type(self)}: {self.info}"


class EvaluationCondition(BaseCondition):
    """ A condition on how good the hand is, by some method of evaluation. """

    def __init__(self, evaluation_method, minimum, maximum):
        self.minimum = minimum
        self.maximum = maximum
        self._evaluation_method = evaluation_method
        info = (f"Evaluation method: {self._evaluation_method}. Min: "
                f"{self.minimum}. Max: {self.maximum}.")

        def accept(hand):
            """If the hand evaluates to within the specified range."""
            evaluation = self._evaluation_method(hand)
            return self.minimum <= evaluation <= self.maximum
        super().__init__(accept, info)


class ShapeConditionFactory:
    """ Creates ShapeConditions. """

    _balanced = Shape("(4333)") + Shape("(4432)") + Shape("(5332)")
    _any = Shape("xxxx")
    _unbalanced = _any - _balanced
    general_types = {"balanced": _balanced, "any": _any,
                     "unbalanced": _unbalanced}
    # Use capture groups to ensure we keep this information.
    _binary_operator = re.compile("([-+])")

    @classmethod
    def create_general_shape_condition(cls, type_):
        """ Create a condition based on general shape types. """
        accept = cls.general_types[type_]
        info = f"Shape is {type_}."
        return BaseCondition(accept, info)

    @classmethod
    def create_shape_condition(cls, shape_string):
        shape_string = "".join(shape_string.split()).lower()
        regex = re.compile(r"^([-+\dx]|[()])+$")
        assert regex.match(shape_string)
        shapes = cls._binary_operator.split(shape_string)
        converted_shapes = [shape if shape in {"+", "-"} else
                            f"Shape('{shape}')" for shape in shapes]
        overall_shape = eval("".join(converted_shapes))
        return BaseCondition(overall_shape,
                             f"Shape: {' '.join(converted_shapes)}")

    @staticmethod
    def create_suit_length_condition(suit, minimum, maximum):
        def get_accept(suit):

            def accept(hand):
                return minimum <= len(getattr(hand, suit)) <= maximum

            return accept

        return BaseCondition(get_accept(suit),
                             f"{minimum} <= {suit} <= {maximum}")


class Condition:
    """ A set of conditions on a hand. """

    def __init__(self, evaluation_conditions, shape_conditions):
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

    # TODO: Make Condition a subclass of BaseCondition
    @property
    def info(self):
        return str(self)

    def __str__(self):
        return (f"{self.evaluation_conditions}"
                f"\n{self.shape_conditions}")


class MultiCondition(BaseCondition):
    def __init__(self, conditions=None):
        self.conditions = list(conditions or [])
        super().__init__(self._get_accept(), self._get_info())

    # Should use self.conditions to determine acceptance.
    def _get_accept(self):
        raise NotImplementedError("Abstract method.")

    # Should use self.conditions to get info from them.
    def _get_info(self):
        raise NotImplementedError("Abstract method.")

    # Override this as self.conditions could change.
    @property
    def info(self):
        return self._get_info()


class AndCondition(MultiCondition):
    """
    Collection of conditions which are all required to be true to accept a
    hand.
    """
    def _get_info(self):
        infos = (condition.info for condition in self.conditions)
        return f"AND ({', '.join(infos)})"

    def _get_accept(self):
        def _accept(hand):
            """
            If all conditions are satisfied by the hand or not.
            """
            for condition in self.conditions:
                if not condition.accept(hand):
                    return False

            return True
        return _accept


class NotCondition(BaseCondition):
    """ An inverted condition """
    def __init__(self, condition):
        assert condition
        self.condition = condition

        def _accept(hand):
            """ The inverse of self.condition """
            return not self.condition.accept(hand)

        super().__init__(_accept, f"NOT ({self.condition.info})")


class OrCondition(MultiCondition):
    """
    Collection of conditions of which at least one is required to be true to
    accept a hand.
    """

    def _get_info(self):
        infos = (condition.info for condition in self.conditions)
        return f"OR ({', '.join(infos)})"

    def _get_accept(self):
        def _accept(hand):
            for condition in self.conditions:
                if condition.accept(hand):
                    return True

            return False

        return _accept


class FormulaParser:
    _VALID_EXPRESSION = re.compile("^([cdhs]|[0-9]+)([-+*]([cdhs]|[0-9]+))*$")
    _BINARY_OPERATOR = re.compile("[-+*]")

    def __init__(self, formula_module):
        self._valid_formula_regex = self._get_formula_regex(formula_module)

    @staticmethod
    def _get_formula_regex(formula_module):
        raise NotImplementedError

    @staticmethod
    def _validate_formula_expression(formula_module):
        raise NotImplementedError


def _parse_formula(formula, formula_module):
    formula = "".join(formula.split()).lower()
    assert OPERATOR.findall(formula)

    def _get_accept(formula_text):
        def accept(hand):
            return eval(formula_text)

        return accept

    return _get_accept(formula)


def _get_min_max_for_method(xml_method,
                            default_min=0,
                            default_max=math.inf,
                            absolute_min=-math.inf,
                            absolute_max=math.inf):
    """ Returns (minimum, maximum) for XML method."""

    # This is so defaults need not be altered when the absolute values
    # conflict.
    default_min = max(default_min, absolute_min)
    default_max = min(default_max, absolute_max)

    try:
        minimum = float(xml_method.find("min").text)
    except AttributeError:
        # Minimum is not defined, so is assumed to be 0.
        minimum = default_min

    try:
        maximum = float(xml_method.find("max").text)
    except AttributeError:
        # Maximum is not defined, so use infinity.
        maximum = math.inf

    result = (max(minimum, absolute_min), min(maximum, absolute_max))
    assert result[0] <= result[1], f"minimum, maximum == {result}"
    assert (not (result[0] in {default_min, absolute_min}
                 and result[1] in {default_max, absolute_max})), xml_method.tag

    return result


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


def _get_formula_module(xml_root, current_directory):
    try:
        formula_module_name = xml_root.attrib["formulas"]
        formula_module_location = os.path.join(current_directory,
                                               formula_module_name)
        spec = importlib.util.spec_from_file_location("bridge_formulas",
                                                      formula_module_location)
        formula_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(formula_module)
    except KeyError:
        formula_module = None
    except ImportError:
        print(f"Warning: formula module count not be found at "
              f"{formula_module_location}")
        formula_module = None

    return formula_module


def _get_hcp_method(xml_root, get_formula):
    try:
        # HCP not defined in formula_module.
        hcp_style = xml_root.attrib["hcp"]
    except (AttributeError, KeyError):  # TODO: Check which is correct.
        print("Warning: HCP style not defined. "
              "Taking hcp from formula module.")
        hcp_style = None

    if hcp_style == "standard":
        return HCP
    elif hcp_style == "chimaera":
        return CHIMAERA_HCP

    # Default.
    return get_formula("hcp")


def get_bids_from_xml(filepath=None):
    """ Returns a dictionary of opening bids. """
    tree = ET.parse(filepath, ET.XMLParser(encoding="utf-8"))
    root = tree.getroot()

    # parser = FormulaParser(formula_module)

    directory = os.path.dirname(filepath)
    formula_module = _get_formula_module(root, directory)

    def get_formula(method_name):
        try:
            return getattr(formula_module, method_name)
        except AttributeError:
            try:
                return getattr(standard_formulas, method_name)
            except AttributeError:
                location = os.path.realpath(formula_module.__file__)
                raise NotImplementedError(f"{method_name} not defined in "
                                          f"{location}.")

    hcp = _get_hcp_method(root, get_formula)

    try:
        shape_style = root.attrib["shape"]
        if shape_style == "standard":
            shape_points = standard_shape_points
        elif shape_style == "freakiness":
            shape_points = freakness_points

        def _points(hand):
            return hcp(hand) + shape_points(hand)
    except KeyError:
        _points = get_formula("points")

    def _define_bid(xml_bid):
        value, desc = xml_bid.find("value"), xml_bid.find("desc")
        xml_conditions = xml_bid.findall("condition")
        # Include conditions
        or_ = OrCondition()
        # All conditions
        and_ = AndCondition([or_])

        for xml_condition in xml_conditions:
            evaluation_conditions = \
                _get_evaluation_condition(xml_condition)

            evaluation_conditions.extend(_get_formulas(xml_condition))
            shape_conditions = _get_shape_conditions(xml_condition)
            type_ = xml_condition.attrib["type"]

            condition = Condition(evaluation_conditions, shape_conditions)

            if type_ == "include":
                or_.conditions.append(condition)
            if type_ == "exclude":
                condition = NotCondition(condition)
                and_.conditions.append(condition)
            elif type_ != "include":
                raise NotImplementedError(
                    type_, "Expected 'include' or 'exclude'")

        return Bid(value.text, desc.text, and_)

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
            minimum, maximum = _get_min_max_for_method(method)

            if method.tag == "hcp":
                evaluation_condition = EvaluationCondition(
                    hcp, minimum, maximum)
            elif method.tag == "tricks":
                tricks = get_formula("tricks")

                evaluation_condition = EvaluationCondition(
                    tricks, minimum, maximum)
            elif method.tag == "points":
                evaluation_condition = EvaluationCondition(
                    _points, minimum, maximum)
            else:
                raise NotImplementedError(method.tag)

            evaluation_conditions.append(evaluation_condition)

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
                shape_condition = \
                    ShapeConditionFactory.create_shape_condition(shape.text)
            elif type_ == "general":
                shape_condition = \
                    ShapeConditionFactory.create_general_shape_condition(
                        shape.text)
            elif type_ == "formula":
                formula = shape.text
                accept = _parse_formula_for_condition(formula)
                shape_condition = BaseCondition(accept, formula)
            elif type_ in {"clubs", "diamonds", "hearts", "spades"}:
                minimum, maximum = _get_min_max_for_method(
                    shape,
                    absolute_min=0,
                    absolute_max=13)

                shape_condition = \
                    ShapeConditionFactory.create_suit_length_condition(
                        type_, minimum, maximum)
            elif type_ in {"longer_than", "strictly_longer_than"}:
                longer_suit = shape.find("longer_suit").text
                shorter_suit = shape.find("shorter_suit").text
                operator = "<=" if type_ == "longer_than" else "<"
                formula = f"{shorter_suit} {operator} {longer_suit}"
                accept = _parse_formula_for_condition(formula)
                shape_condition = BaseCondition(accept, f"Formula: {formula}")
            else:
                raise NotImplementedError(type_)

            shape_conditions.append(shape_condition)

        return shape_conditions

    def _find_all_children_bids(bid, xml_bid):
        for child_xml_bid in xml_bid.findall("bid"):
            try:
                child_bid = _define_bid(child_xml_bid)
            except Exception:
                # -------------------------------------------------------------
                # This is very useful at finding the correct bit of XML which
                # is invalid.
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
                # -------------------------------------------------------------

            child_bid.parent = bid
            assert child_bid.value not in bid.children
            bid.children[child_bid.value] = child_bid
            _find_all_children_bids(child_bid, child_xml_bid)

    # The actual function.
    result = {}
    for xml_bid in root:
        try:
            bid = _define_bid(xml_bid)
        except Exception:
            value = xml_bid.find("value")
            if value:
                print(f"Error in XML of {value.text}")

            try:
                id_ = xml_bid.attrib["id"]
                print(f"Error in XML of bid with ID {id_}")
            except KeyError:
                pass

            raise

        assert bid.value not in result
        result[bid.value] = bid
        _find_all_children_bids(bid, xml_bid)

    return result
