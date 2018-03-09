# -*- coding: utf-8 -*-

import re
from practice_bidding.redeal.redeal import Shape


class BaseCondition:
    """ Base class for all condition classes. """

    def __init__(self, accept, info):
        self._accept = accept
        assert info
        # A description of the condition.
        self.info = info

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
        self.info = (f"Evaluation method: {self._evaluation_method}. Min: "
                     f"{self.minimum}. Max: {self.maximum}.")

    def accept(self, hand):
        """If the hand evaluates to within the specified range."""
        evaluation = self._evaluation_method(hand)
        return self.minimum <= evaluation <= self.maximum


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


class NotCondition(BaseCondition):
    """ An inverted condition """
    def __init__(self, condition):
        assert condition
        self.condition = condition

        def _accept(hand):
            """ The inverse of self.condition """
            return not self.condition.accept(hand)

        super().__init__(_accept, f"NOT ({self.condition.info})")


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


class Condition(MultiCondition):
    """ A set of conditions on a hand. """

    def __init__(self, evaluation_conditions, shape_conditions):
        self.evaluation_conditions = list(evaluation_conditions)
        self.shape_conditions = list(shape_conditions)

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


if __name__ == "__main__":
    or_ = OrCondition()
