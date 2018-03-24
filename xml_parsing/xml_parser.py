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
import operator

from practice_bidding import standard_formulas
from practice_bidding.redeal.redeal import Evaluator
from practice_bidding.redeal.redeal.global_defs import Strain
from practice_bidding.xml_parsing.conditions import SimpleCondition
from practice_bidding.xml_parsing.conditions import ShapeConditionFactory
from practice_bidding.xml_parsing.conditions import AndCondition, OrCondition
from practice_bidding.xml_parsing.conditions import Condition, BaseCondition
from practice_bidding.xml_parsing.conditions import NotCondition
from practice_bidding.xml_parsing.conditions import EvaluationCondition


CHIMAERA_HCP = Evaluator(4.5, 3, 1.5, 0.75, 0.25)
HCP = Evaluator(4, 3, 2, 1)
OPERATOR = re.compile("([!<>=]=|[<>])")
VALID_EXPRESSION = re.compile("^(-?([cdhs]|[0-9]+))([-+*]([cdhs]|[0-9]+))*$")
SAFE_FORMULA = re.compile("^(-?([0-9]+)([-+*]([0-9]+))*([<>]|[!<>=]=))+"
                          "([0-9]+)([-+*]([0-9]+))*$")
SAFE_EXPRESSION = re.compile("^-?[0-9]+([-+*]([0-9]+))*$")
OPERATOR_MAP = {"==": operator.eq,
                "!=": operator.ne,
                ">=": operator.ge,
                ">": operator.gt,
                "<=": operator.le,
                "<": operator.lt}


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

    def accept(self, hand) -> bool:
        """
        Whether the hand is valid for this bid or not.

        Note if there are no include conditions, a hand will always be
        rejected.
        """
        return self.condition.accept(hand)

    def _get_suit(self) -> str:
        try:
            suit_text = self.value[1].lower()
        except IndexError:
            suit_text = self.value[0].lower()

        return self._suits[suit_text]


class FormulaParser:  # pragma: no cover
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


def _parse_formula(formula, formula_module):  # pragma: no cover
    raise NotImplementedError
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
                            absolute_max=math.inf) -> (float, float):
    """ Returns (minimum, maximum) for XML method."""

    try:
        minimum = float(xml_method.find("min").text)
    except AttributeError:
        # Minimum is not defined, so is assumed to be 0.
        minimum = default_min

    try:
        maximum = float(xml_method.find("max").text)
    except AttributeError:
        # Maximum is not defined, so use infinity.
        maximum = default_max

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
    cmp_operator = None
    while len(result) == 1:
        to_parse = result[0]
        cmp_operator = operators[i]
        result = to_parse.split(cmp_operator)
        i += 1

    assert len(result) == 2

    # Not a foolproof guarantee, but better than nothing.
    for expression in result:
        assert VALID_EXPRESSION.match(expression), expression

    expr_operator_seq = OPERATOR.split(simplified_formula)
    assert len(expr_operator_seq) % 2 == 1
    comparison_count = len(expr_operator_seq) // 2
    comparisons = [(expr_operator_seq[2*i],
                    expr_operator_seq[2*i + 1],
                    expr_operator_seq[2*i + 2])
                   for i in range(comparison_count)]

    def _evaluate_expression(expression: str, hand_shape) -> int:
        s, h, d, c = hand_shape
        evaluated_expression = (expression
                                .replace("s", str(s))
                                .replace("h", str(h))
                                .replace("d", str(d))
                                .replace("c", str(c)))
        assert SAFE_EXPRESSION.match(evaluated_expression), \
            evaluated_expression
        return eval(evaluated_expression)

    def _comparison_accept(comparison, hand) -> bool:
        lhs, operator_string, rhs = comparison
        operator = OPERATOR_MAP[operator_string]
        evaluated_lhs = _evaluate_expression(lhs, hand.shape)
        evaluated_rhs = _evaluate_expression(rhs, hand.shape)
        return operator(evaluated_lhs, evaluated_rhs)

    def _accept(hand) -> bool:
        for comparison in comparisons:
            if not _comparison_accept(comparison, hand):
                return False

        return True

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
    except ImportError:  # pragma: no cover
        print(f"Warning: formula module could not be found at "
              f"{formula_module_location}")
        formula_module = None

    return formula_module


def _get_hcp_method(xml_root, get_formula):
    try:
        # HCP not defined in formula_module.
        hcp_style = xml_root.attrib["hcp"]
    except KeyError:
        print("Warning: HCP style not defined. "
              "Taking hcp from formula module.")
        hcp_style = None

    if hcp_style == "standard":
        return HCP
    elif hcp_style == "chimaera":
        return CHIMAERA_HCP

    # Default.
    return get_formula("hcp")


def _get_shape_conditions(xml_condition):
    shapes = xml_condition.findall("shape")
    shape_conditions = []
    for shape in shapes:
        type_ = shape.attrib["type"]

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
            shape_condition = SimpleCondition(accept, formula)
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
            cmp_operator = "<=" if type_ == "longer_than" else "<"
            formula = f"{shorter_suit} {cmp_operator} {longer_suit}"
            accept = _parse_formula_for_condition(formula)
            shape_condition = SimpleCondition(accept,
                                              f"Formula: {formula}")
        else:
            raise NotImplementedError(type_)

        shape_conditions.append(shape_condition)

    return shape_conditions


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
            except AttributeError:  # pragma: no cover
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

    def _define_bid(xml_bid) -> Bid:
        value, desc = xml_bid.find("value").text, xml_bid.find("desc").text

        and_ = xml_bid.find("and")
        or_ = xml_bid.find("or")
        not_ = xml_bid.find("not")
        xml_condition = and_ or or_ or not_

        if xml_condition:
            # In new style should have exactly one condition for a bid.
            assert bool(and_) + bool(or_) + bool(not_) == 1
            condition = _define_logical_condition(xml_condition)
            return Bid(value, desc, condition)

        # New style and/or not defined. Take legacy path.
        xml_conditions = xml_bid.findall("condition")

        # Include conditions
        or_ = OrCondition()
        # All conditions
        and_ = AndCondition([or_])

        for xml_condition in xml_conditions:
            evaluation_conditions = \
                _get_evaluation_conditions(xml_condition)

            evaluation_conditions.extend(_get_formulas(xml_condition))
            shape_conditions = _get_shape_conditions(xml_condition)
            type_ = xml_condition.attrib["type"]

            condition = Condition(evaluation_conditions, shape_conditions)

            if type_ == "include":
                or_.conditions.append(condition)
            if type_ == "exclude":
                condition = NotCondition(condition)
                and_.conditions.append(condition)
            elif type_ != "include":  # pragma: no cover
                raise NotImplementedError(
                    type_, "Expected 'include' or 'exclude'")

        return Bid(value, desc, and_)

    def _define_logical_condition(xml_condition) -> BaseCondition:
        tag = xml_condition.tag
        child_conditions = []

        for and_ in xml_condition.findall("and"):
            child_conditions.append(_define_logical_condition(and_))

        for or_ in xml_condition.findall("or"):
            child_conditions.append(_define_logical_condition(or_))

        for not_ in xml_condition.findall("not"):
            child_conditions.append(_define_logical_condition(not_))

        child_conditions.extend(_get_evaluation_conditions(xml_condition))
        child_conditions.extend(_get_shape_conditions(xml_condition))

        if tag == "and":
            base_condition = AndCondition(child_conditions)
        elif tag == "or":
            base_condition = OrCondition(child_conditions)
        elif tag == "not":
            assert len(child_conditions) == 1
            base_condition = NotCondition(child_conditions[0])
        else:
            raise ValueError(f"Incorrect tag for logical condition: {tag}.")

        return base_condition

    # Using no cover since _parse_formula not implemented yet.
    # TODO: Remove this when it gets implemented.
    def _get_formulas(xml_condition):  # pragma: no cover
        formulas = []
        for xml_formula in xml_condition.findall("formula"):
            formula_text = xml_formula.text
            formula = _parse_formula(formula_text, formula_module)
            formulas.append(formula)

        return formulas

    def _get_evaluation_conditions(xml_condition):
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

    def _find_all_children_bids(bid, xml_bid):
        for child_xml_bid in xml_bid.findall("bid"):
            try:
                child_bid = _define_bid(child_xml_bid)
            except Exception:  # pragma: no cover
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
        except Exception:  # pragma: no cover
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
