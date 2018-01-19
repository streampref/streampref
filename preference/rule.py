# -*- coding: utf-8 -*-
'''
Module to manipulate conditional preference rules (cp-rules)
'''

import logging

from grammar.symbols import FIRST_SYM, PREVIOUS_SYM, SOME_SYM, \
    ALL_SYM
from grammar.symbols import IF_SYM, THEN_SYM


LOG = logging.getLogger(__name__)


class CPCondition(object):
    '''
    Class to represent rule condition
    '''
    def __init__(self, parsed_condition_list, operator):
        # Rule condition dictionaries
        self._present_condition_dict = {}
        # Invalid attributes (used just at validation)
        self._invalid_attribute_list = []
        if parsed_condition_list is not None and operator is not None:
            self._initialize(parsed_condition_list, operator)

    def __str__(self):
        str_list = get_predicate_string_list(self._present_condition_dict)
        return ' AND '.join(str_list)

    def __len__(self):
        return len(self._present_condition_dict)

    def _initialize(self, parsed_condition_list, operator):
        '''
        Initialize past conditions
        '''
        # Evaluate each condition
        for parsed_pred in parsed_condition_list:
            parsed_att = parsed_pred.get_attribute()
            # Get operand attribute
            att = operator.find_attribute(parsed_att.get_name(),
                                          parsed_att.get_table())
            # Check if attribute is valid
            if att is None:
                self._invalid_attribute_list.append(parsed_att)
            else:
                # Set proposition
                interval = parsed_pred.get_interval()
                self._present_condition_dict[att] = interval

    def copy(self):
        '''
        Create a copy
        '''
        copy_cond = CPCondition(None, None)
        copy_cond.__dict__.update(self.__dict__)
        return copy_cond

    def get_invalid_attribute_list(self):
        '''
        Get invalid attribute list
        '''
        return self._invalid_attribute_list

    def get_present_condition_dict(self):
        '''
        Get condition dictionary
        '''
        return self._present_condition_dict

    def get_interval_list(self, attribute):
        '''
        Get a list of intervals for an attribute
        '''
        if attribute in self._present_condition_dict:
            return [self._present_condition_dict[attribute]]
        else:
            return []

    def get_attribute_list(self):
        '''
        Get all attributes present in the condition
        '''
        return self._present_condition_dict.keys()

    def is_present_compatible(self, other):
        '''
        Check if a condition is present compatible with another condition.
        A condition is present compatible with another condition if
        they have the same value to same attributes in the present conditions
        '''
        other_cond_dict = other.get_present_condition_dict()
        return are_compatible_dicts(self._present_condition_dict,
                                    other_cond_dict)

    def is_valid_by_formula(self, formula):
        '''
        Check if condition is satisfied by a formula
        '''
        for att in self._present_condition_dict:
            if att not in formula \
                    or formula[att] != self._present_condition_dict[att]:
                return False
        return True

    def is_valid_by_record(self, record):
        '''
        Check if conditions is satisfied by a record
        '''
        return is_condition_valid_by_record(self._present_condition_dict,
                                            record)

    def split_by_interval(self, attribute, interval):
        '''
        Split the condition, if an interval overlaps with attribute interval
        '''
        split_list = []
        # Try to split intervals of condition dictionary
        new_dict_list = split_condition_dict(self._present_condition_dict,
                                             attribute, interval)
        if len(new_dict_list):
            original_cond_dict = self._present_condition_dict
            # Check if there was split
            for new_dict in new_dict_list:
                # Create a new condition for each split dictionary
                self._present_condition_dict = new_dict
                new_cond = self.copy()
                split_list.append(new_cond)
            # Restore original dictionary
            self._present_condition_dict = original_cond_dict
        return split_list

    def get_atomic_formulas_list(self):
        '''
        Get atomic formulas for present conditions
        '''
        formulas_list = []
        # Get intervals in antecedent
        for att in self._present_condition_dict:
            formula = {att: self._present_condition_dict[att]}
            formulas_list.append(formula)
        return formulas_list


class CPPreference(object):
    '''
    Class to represent rule preference
    '''
    def __init__(self, parsed_best, parsed_worst, indifferent_list, operator):
        '''
        Initialize rule by a ParsedRule
        '''
        # Invalid attributes (just for information)
        self._invalid_attribute_list = []
        # Preference attribute
        self._attribute = None
        # Preferred Interval
        self._best_interval = None
        # non preferred interval
        self._worst_interval = None
        # Indifferent attributes
        self._indifferent_attribute_set = set()
        if parsed_best is not None and parsed_worst is not None and \
                indifferent_list is not None and operator is not None:
            self._initialize(parsed_best, parsed_worst, indifferent_list,
                             operator)

    def _initialize(self, parsed_best, parsed_worst, indifferent_list,
                    operator):
        '''
        Initialize by parsed term
        '''
        # Get consequent attribute
        att_best = parsed_best.get_attribute()
        att_worst = parsed_worst.get_attribute()
        att_best = operator.find_attribute(att_best.get_name(),
                                           att_best.get_table())
        att_worst = operator.find_attribute(att_worst.get_name(),
                                            att_worst.get_table())
        # Check if attribute is valid
        if att_best is None or att_worst is None or att_best != att_worst:
            self._invalid_attribute_list.\
                append(parsed_best.get_attribute())
            self._invalid_attribute_list.\
                append(parsed_worst.get_attribute())
        self._attribute = att_best
        # Get preferred and non preferred intervals
        self._best_interval = parsed_best.get_interval()
        self._worst_interval = parsed_worst.get_interval()
        # Build indifferent attribute set
        for parsed_att in indifferent_list:
            # Check if each indifferent attributes is valid
            att = operator.find_attribute(parsed_att.get_name(),
                                          parsed_att.get_table())
            self._indifferent_attribute_set.add(att)
            if att is None:
                self._invalid_attribute_list.append(parsed_att)

    def __str__(self):
        pref_str = self._best_interval.get_string(self._attribute)
        pref_str += ' BETTER ' + \
            self._worst_interval.get_string(self._attribute)
        indiff_str_list = [str(att) for att in self._indifferent_attribute_set]
        pref_str += '[' + ', '.join(indiff_str_list) + ']'
        return pref_str

    def get_invalid_attribute_list(self):
        '''
        Get invalid attribute list
        '''
        return self._invalid_attribute_list

    def get_preference_attribute(self):
        '''
        Get preference attribute
        '''
        return self._attribute

    def get_best_interval(self):
        '''
        Get preferred value for preference attribute
        '''
        return self._best_interval

    def get_worst_interval(self):
        '''
        Get non preferred value for preference attribute
        '''
        return self._worst_interval

    def get_indifferent_set(self):
        '''
        Get indifferent attribute set
        '''
        return self._indifferent_attribute_set

    def is_best_valid_by_formula(self, formula):
        '''
        Check if a formula satisfies the preferred interval
        '''
        return self._attribute in formula and \
            formula[self._attribute] == self._best_interval

    def is_worst_valid_by_formula(self, formula):
        '''
        Check if a formula satisfies the non preferred interval
        '''
        return self._attribute in formula and \
            formula[self._attribute] == self._worst_interval

    def is_best_valid_by_record(self, record):
        '''
        Check if a record satisfies the preferred interval
        '''
        return self._attribute in record and \
            self._best_interval.\
            is_inside_or_equal(record[self._attribute])

    def is_worst_valid_by_record(self, record):
        '''
        Check if a record satisfies the non preferred interval
        '''
        return self._attribute in record and \
            self._worst_interval.\
            is_inside_or_equal(record[self._attribute])

    def copy(self):
        '''
        Create a copy
        '''
        copy_pref = CPPreference(None, None, None, None)
        copy_pref.__dict__.update(self.__dict__)
        return copy_pref

    def split_by_interval(self, interval):
        '''
        Split, if an interval overlaps with attribute interval
        '''
        split_list = []
        # Take preferred interval
        best_interval = self._best_interval
        # Try to split preferred interval
        new_interval_list = best_interval.split_by_interval(interval)
        # Check if the was split
        if len(new_interval_list):
            for new_interval in new_interval_list:
                # Create a new rule preference for each split interval
                self._best_interval = new_interval
                new_rulepref = self.copy()
                split_list.append(new_rulepref)
                self._best_interval = best_interval
            # Restore original interval
            self._best_interval = best_interval
            return split_list
        # The same for non preferred interval
        worst_interval = self._worst_interval
        new_interval_list = worst_interval.split_by_interval(interval)
        if len(new_interval_list):
            for new_interval in new_interval_list:
                self._worst_interval = new_interval
                new_rulepref = self.copy()
                split_list.append(new_rulepref)
            self._worst_interval = worst_interval
        return split_list


class CPRule(object):
    '''
    Class to represent a conditional preference rule
    '''

    def __init__(self, parsed_term=None, operator=None):
        # Rule condition
        self._condition = None
        # Rule Preference
        self._preference = None
        if parsed_term is not None and operator is not None:
            self._initialize(parsed_term, operator)
            # Invalid attributes (used just at validation)
            self._invalid_attribute_list = \
                self._condition.get_invalid_attribute_list() + \
                self._preference.get_invalid_attribute_list()

    def _initialize(self, parsed_rule, operator):
        '''
        Initialize rule by a ParsedRule
        '''
        # Initialize rule condition
        self._condition = CPCondition(parsed_rule.get_condition_list(),
                                      operator)
        # Initialize rule preference
        indifferent_list = parsed_rule.get_indifferent_list()
        self._preference = CPPreference(parsed_rule.get_best_interval(),
                                        parsed_rule.get_worst_interval(),
                                        indifferent_list, operator)

    def __str__(self):
        rule_str = ''
        if len(self._condition):
            rule_str = IF_SYM + ' ' + str(self._condition) + ' ' + \
                THEN_SYM + ' '
        rule_str += str(self._preference)
        return rule_str

    def __repr__(self):
        return self.__str__()

    # Used for set of rules
    def __cmp__(self, other):
        if type(self) != type(other):  # IGNORE:unidiomatic-typecheck
            return 1
        else:
            return cmp(str(self), str(other))

    # Used for set of rules
    def __eq__(self, other):
        return type(self) == type(other) and str(self) == str(other)

    # Used for set of rules
    def __ne__(self, other):
        return not self.__eq__(other)

    # Used for set of rules
    def __hash__(self):
        return hash(str(self))

    def get_condition(self):
        '''
        Get rule condition
        '''
        return self._condition

    def get_preference(self):
        '''
        Get rule preference
        '''
        return self._preference

    def is_consistent(self):
        '''
        Check if the rule is consistent
        '''
        # Must not exists invalid attributes
        if len(self._invalid_attribute_list):
            LOG.error('Invalid attributes: %s',
                      self._invalid_attribute_list)
            return False
        att = self._preference.get_preference_attribute()
        # Rule attribute must not be in condition rule
        if att in self._condition.get_present_condition_dict():
            LOG.error('Preference attribute present in rule condition')
            return False
        # Rule attribute must not be in indifferent attributes
        if att in self._preference.get_indifferent_set():
            LOG.error('Preference attribute present in indifferent attributes')
            return False
        # Condition attributes and indifferent attributes must be disjoint
        for att in self._preference.get_indifferent_set():
            if att in self._condition.get_present_condition_dict():
                LOG.error('indifferent attribute present in rule condition')
                return False
        return True

    def copy(self):
        '''
        Create a copy
        '''
        copy_rule = CPRule(None, None)
        copy_rule.__dict__.update(self.__dict__)
        return copy_rule

    def get_interval_list(self, attribute):
        '''
        Get a list of intervals for informed attribute present in the rule
        '''
        interval_list = self._condition.get_interval_list(attribute)
        if self._preference.get_preference_attribute() == attribute:
            interval_list.append(self._preference.get_best_interval())
            interval_list.append(self._preference.get_worst_interval())
        return interval_list

    def change_record(self, record):
        '''
        Generate a worst record when it is possible,
        when it is not then return None
        '''
        cond = self._condition
        pref = self._preference
        pref_att = pref.get_preference_attribute()
        best_interval = pref.get_best_interval()
        if cond.is_valid_by_record(record) and \
                (pref_att not in record or
                 (pref_att in record and
                  best_interval.is_inside_or_equal(record[pref_att]))):
            new_record = record.copy()
            new_record[pref_att] = pref.get_worst_interval()
            for att in pref.get_indifferent_set():
                if att in new_record:
                    del new_record[att]
            return new_record
        else:
            return None

    def get_atomic_formulas_list(self):
        '''
        Get atomic formulas in rule
        '''
        formulas_list = self._condition.get_atomic_formulas_list()
        formula = {self._preference.get_preference_attribute():
                   self._preference.get_best_interval()}
        formulas_list.append(formula)
        formula = {self._preference.get_preference_attribute():
                   self._preference.get_worst_interval()}
        formulas_list.append(formula)
        return formulas_list

    def get_attribute_list(self):
        '''
        Get attribute list present in rule
        '''
        cond = self._condition
        pref = self._preference
        att_list = cond.get_attribute_list() + list(pref.get_indifferent_set())
        att_list.append(pref.get_preference_attribute())
        return att_list

    def _split_by_interval(self, attribute, interval):
        '''
        Split the rule, if an interval overlaps with some interval of
        other rule (in same attribute)
        '''
        split_list = []
        # Try to split condition
        original_cond = self._condition
        new_cond_list = original_cond.split_by_interval(attribute, interval)
        # Check if there was split
        if len(new_cond_list):
            # Create new rule for each split condition
            for new_cond in new_cond_list:
                self._condition = new_cond
                new_rule = self.copy()
                split_list.append(new_rule)
            # Restore original condition after split
            self._condition = original_cond
            # Stop after first split
            return split_list
        # Try to split preference if there was not split in condition
        if attribute == self._preference.get_preference_attribute():
            original_pref = self._preference
            new_pref_list = original_pref.split_by_interval(interval)
            if len(new_pref_list):
                for new_pref in new_pref_list:
                    self._preference = new_pref
                    new_rule = self.copy()
                    split_list.append(new_rule)
            self._preference = original_pref
        return split_list

    def split(self, other):
        '''
        Split the rule, if an interval overlaps with some interval of
        other rule (in same attribute)
        '''
        # Get the list of attributes of other rule
        att_list = other.get_attribute_list()
        # For each attribute
        for att in att_list:
            # Get intervals for current attribute
            interval_list = other.get_interval_list(att)
            # For each interval
            for interval in interval_list:
                new_rule_list = self._split_by_interval(att, interval)
                if len(new_rule_list):
                    return new_rule_list
        return []

    def is_compatible_to(self, other):
        '''
        Check if a rule is compatible with another rule

        A rule is compatible with another rule
        if they are over the same preference attribute
        and they have the same value to same attributes
        in the present conditions
        '''
        if self.get_preference().get_preference_attribute() != \
                other.get_preference().get_preference_attribute() or \
                not self._condition.\
                is_present_compatible(other.get_condition()):
            return False
        else:
            return True

    def formula_dominates(self, formula1, formula2):
        '''
        Returns True if formula1 dominates (is preferred to) formula2
        according to rule
        '''
        # Check if formula1 has preferred value
        # and other formula1 has non preferred value
        pref = self._preference
        if not pref.is_best_valid_by_formula(formula1) or \
                not pref.is_worst_valid_by_formula(formula2):
            return False
        # Check if formulas satisfy rule conditions
        cond = self._condition
        if not cond.is_valid_by_formula(formula1) or \
                not cond.is_valid_by_formula(formula2):
            return False
        # Check if all another attributes are equal except
        # Preference attribute, condition attributes and indifferent attributes
        att_set = set(formula1.keys() + formula2.keys())
        att_set = att_set.difference(set([pref.get_preference_attribute()]))
        att_set = att_set.difference(pref.get_indifferent_set())
        for att in att_set:
            if att not in formula1 or \
                    att not in formula2 or \
                    formula1[att] != formula2[att]:
                return False
        return True

    def record_dominates(self, record1, record2):
        '''
        Returns True if record1 dominates (is preferred to) record2
        according to rule
        '''
        # Check if record1 has preferred value
        # and other formula1 has non preferred value
        pref = self._preference
        if not pref.is_best_valid_by_record(record1) or \
                not pref.is_worst_valid_by_record(record2):
            return False
        # Check if formulas satisfy rule conditions
        cond = self._condition
        if not cond.is_valid_by_record(record1) or \
                not cond.is_valid_by_record(record2):
            return False
        # Check if all another attributes are equal except
        # Preference attribute and indifferent attributes
        att_set = set(record1.keys() + record2.keys())
        att_set = att_set.difference(set([pref.get_preference_attribute()]))
        att_set = att_set.difference(pref.get_indifferent_set())
        for att in att_set:
            if att not in record1 or \
                    att not in record2 or \
                    record1[att] != record2[att]:
                return False
        return True


def split_condition_dict(condition_dict, attribute, interval):
    '''
    Try to split dictionary intervals according to
    an attribute and an interval list for this attribute
    If there exists some split, return a list of split dictionaries
    Else return a empty list
    '''
    new_dict_list = []
    # Check if attribute is present in the dictionary
    if attribute in condition_dict:
        cond_interval = condition_dict[attribute]
        # Try split condition interval
        new_interval_list = cond_interval.split_by_interval(interval)
        # Check if there was split
        if len(new_interval_list):
            # Create a new dictionary for each new interval
            for new_interval in new_interval_list:
                new_dict = condition_dict.copy()
                # Change original interval by new interval
                new_dict[attribute] = new_interval
                # Add a rule copy to result
                new_dict_list.append(new_dict)
    return new_dict_list


def is_condition_valid_by_record(condition_dict, record):
    '''
    Check if a record satisfies a condition dictionary
    '''
    for att in condition_dict:
        interval = condition_dict[att]
        if att not in record or \
                not interval.is_inside_or_equal(record[att]):
            return False
    return True


def are_compatible_dicts(dict1, dict2):
    '''
    Check if two dictionaries are compatible

    Two dictionaries are compatible if they have the same values
     same attributes
    '''
    for key in dict1:
        if key in dict2 \
                and dict1[key] != dict2[key]:
            return False
    return True


def get_predicate_string_list(condition_dict, prefix=''):
    '''
    Get a list of prefixed string predicates from condition dictionary
    '''
    str_list = []
    for att in condition_dict:
        interval = condition_dict[att]
        pred_str = prefix + ' ' + interval.get_string(att)
        str_list.append(pred_str.strip())
    return str_list


class TCPCondition(CPCondition):
    '''
    Class to represent a temporal condition
    '''
    def __init__(self, parsed_condition_list, operator):
        presend_cond_list = []
        if parsed_condition_list is not None:
            for parsed_tpred in parsed_condition_list:
                if len(parsed_tpred.get_past_operator_list()) == 0:
                    presend_cond_list.append(parsed_tpred.get_predicate())
        CPCondition.__init__(self, presend_cond_list, operator)
        # First predicate is False by default
        self._first = False
        # Rule condition dictionaries
        self._past_dict = {}
        self._past_dict[PREVIOUS_SYM] = {}
        self._past_dict[SOME_SYM] = {}
        self._past_dict[ALL_SYM] = {}
        if parsed_condition_list is not None and operator is not None:
            self._init_past_conditions(parsed_condition_list, operator)

    def __str__(self):
        str_list = []
        # First predicate
        if self._first:
            str_list.append(FIRST_SYM)
        str_list += get_predicate_string_list(self._present_condition_dict)
        str_list += get_predicate_string_list(self._past_dict[PREVIOUS_SYM],
                                              PREVIOUS_SYM)
        str_list += \
            get_predicate_string_list(self._past_dict[SOME_SYM],
                                      SOME_SYM + ' ' + PREVIOUS_SYM)
        str_list += \
            get_predicate_string_list(self._past_dict[ALL_SYM],
                                      ALL_SYM + ' ' + PREVIOUS_SYM)
        return ' AND '.join(str_list)

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        cond_len = CPCondition.__len__(self)
        if self._first:
            cond_len += 1
        cond_len += len(self._past_dict[PREVIOUS_SYM])
        cond_len += len(self._past_dict[SOME_SYM])
        cond_len += len(self._past_dict[ALL_SYM])
        return cond_len

    def _init_past_conditions(self, parsed_condition_list, operator):
        '''
        Initialize past conditions
        '''
        # Evaluate each condition
        for parsed_tpred in parsed_condition_list:
            pred = parsed_tpred.get_predicate()
            past_op_list = parsed_tpred.get_past_operator_list()
            if FIRST_SYM in past_op_list:
                # First predicate doesn't have proposition
                self._first = True
            elif PREVIOUS_SYM in past_op_list:
                parsed_att = pred.get_attribute()
                att = operator.find_attribute(parsed_att.get_name(),
                                              parsed_att.get_table())
                interval = pred.get_interval()
                # Set key to correct past condition dictionary
                if SOME_SYM in past_op_list:
                    self._past_dict[SOME_SYM][att] = interval
                elif ALL_SYM in past_op_list:
                    self._past_dict[ALL_SYM][att] = interval
                else:
                    self._past_dict[PREVIOUS_SYM][att] = interval
                # Check if attribute is valid
                if att is None:
                    self._invalid_attribute_list.append(parsed_att)

    def copy(self):
        '''
        Create a copy
        '''
        copy_cond = TCPCondition(None, None)
        for key in self.__dict__:
            value = self.__dict__[key]
            if isinstance(value, dict):
                value = value.copy()
            copy_cond.__dict__[key] = value
        return copy_cond

    def has_first(self):
        '''
        Check if rule has first predicate
        '''
        return self._first

    def has_previous(self):
        '''
        Check if condition has some temporal predicates
        PREVIOUS, SOME PREVIOUS or ALL PREVIOUS
        '''
        return len(self._past_dict[PREVIOUS_SYM]) > 0 or \
            len(self._past_dict[SOME_SYM]) > 0 or \
            len(self._past_dict[ALL_SYM]) > 0

    def get_interval_list(self, attribute):
        interval_list = CPCondition.get_interval_list(self, attribute)
        if attribute in self._past_dict[PREVIOUS_SYM]:
            interval_list.append(self._past_dict[PREVIOUS_SYM][attribute])
        if attribute in self._past_dict[SOME_SYM]:
            interval_list.append(self._past_dict[SOME_SYM][attribute])
        if attribute in self._past_dict[ALL_SYM]:
            interval_list.append(self._past_dict[ALL_SYM][attribute])
        return interval_list

    def get_attribute_list(self):
        '''
        Get all attributes present in the condition
        '''
        att_list = CPCondition.get_attribute_list(self)
        for past_key in self._past_dict:
            att_list += self._past_dict[past_key]
        return att_list

    def is_temporal_compatible_to(self, other):
        '''
        Check if two conditions are temporal compatible
        '''
        # FIRST is not compatible to PREVIOS, SOME PREVIOUS or ALL PREVIOUS
        if self.has_first() and other.has_previous():
            return False
        other_past_dit = other.get_past_dict()
        # PREVIOS Q(A) is not compatible to PREVIOS Q'(B) or ALL PREVIOS Q'(B)
        # if A = B and sets correspondent to Q(A) and Q'(B) have intersection
        if are_compatible_dicts(self._past_dict[PREVIOUS_SYM],
                                other_past_dit[PREVIOUS_SYM]) or \
                are_compatible_dicts(self._past_dict[PREVIOUS_SYM],
                                     other_past_dit[PREVIOUS_SYM]):
            return False
        # ALL PREVIOS Q(A) is not compatible to PREVIOS Q'(B),
        # SOME PREVIOS Q'(B) or ALL PREVIOS Q'(B)
        # if A = B and sets correspondent to Q(A) and Q'(B) have intersection
        elif are_compatible_dicts(self._past_dict[ALL_SYM],
                                  other_past_dit[PREVIOUS_SYM]) or \
                are_compatible_dicts(self._past_dict[ALL_SYM],
                                     other_past_dit[SOME_SYM]) or \
                are_compatible_dicts(self._past_dict[ALL_SYM],
                                     other_past_dit[ALL_SYM]):
            return False
        else:
            return True

    def _is_previous_valid_by(self, sequence, position):
        '''
        Check if previous conditions are satisfied by a sequence position
        '''
        if not self.has_previous():
            return True
        if position > 0:
            rec = sequence.get_position(position - 1)
            return is_condition_valid_by_record(self._past_dict[PREVIOUS_SYM],
                                                rec)
        return False

    def _is_some_valid_by(self, sequence, position):
        '''
        Check if some previous conditions are satisfied by a sequence position
        '''
        if not self.has_previous():
            return True
        if position > 0:
            for pos in range(position):
                rec = sequence.get_position(pos)
                if is_condition_valid_by_record(self._past_dict[SOME_SYM],
                                                rec):
                    return True
            # No valid previous position was found
            return False
        # There is no previous position
        return False

    def _is_all_valid_by(self, sequence, position):
        '''
        Check if all previous conditions are satisfied by a sequence position
        '''
        if not self.has_previous():
            return True
        if position > 0:
            for pos in range(position):
                rec = sequence.get_position(pos)
                if not is_condition_valid_by_record(self._past_dict[ALL_SYM],
                                                    rec):
                    return False
            # Some previous position was not valid
            return True
        # There is no previous position
        return False

    def is_valid_by_position(self, sequence, position):
        '''
        Check if TCPRule is satisfied by position of a sequence
        '''
        rec = sequence.get_position(position)
        if self.has_first() and position != 0:
            return False
        elif not self.is_valid_by_record(rec):
            return False
        elif not self._is_previous_valid_by(sequence, position):
            return False
        elif not self._is_some_valid_by(sequence, position):
            return False
        elif not self._is_all_valid_by(sequence, position):
            return False
        return True

    def is_temporal_valid_by_position(self, sequence, position):
        '''
        Check if TCPRule is temporal satisfied by position of a sequence
        '''
        if self.has_first() and position != 0:
            return False
        elif not self._is_previous_valid_by(sequence, position):
            return False
        elif not self._is_some_valid_by(sequence, position):
            return False
        elif not self._is_all_valid_by(sequence, position):
            return False
        return True

    def split_by_interval(self, attribute, interval):
        '''
        Split the condition, if an interval overlaps with some attribute
        interval
        '''
        split_list = []
        cond_dict = self._present_condition_dict
        # Try to split intervals of condition dictionary
        new_dict_list = split_condition_dict(self._present_condition_dict,
                                             attribute, interval)
        # Check if there was split
        if len(new_dict_list):
            for new_dict in new_dict_list:
                # Create a new condition for each split dictionary
                self._present_condition_dict = new_dict
                new_cond = self.copy()
                split_list.append(new_cond)
            # Restore original dictionary
            self._present_condition_dict = cond_dict
            # Stop at the first split
            return split_list
        for past_key in self._past_dict:
            # Try to split intervals of condition dictionary
            new_dict_list = split_condition_dict(self._past_dict[past_key],
                                                 attribute, interval)
            # Check if there was split
            if len(new_dict_list):
                cond_dict = self._past_dict[past_key]
                for new_dict in new_dict_list:
                    # Create a new condition for each split dictionary
                    self._past_dict[past_key] = new_dict
                    new_cond = self.copy()
                    split_list.append(new_cond)
                # Restore original dictionary
                self._past_dict[past_key] = cond_dict
                return split_list
        return split_list

    def get_past_dict(self):
        '''
        Return past conditions
        '''
        return self._past_dict


class TCPRule(CPRule):
    '''
    Class to represent a temporal conditional preference rule
    '''
    def _initialize(self, parsed_rule, operator):
        '''
        Initialize rule by a ParsedRule
        '''
        # Initialize rule condition
        self._condition = TCPCondition(parsed_rule.get_condition_list(),
                                       operator)
        # Initialize rule preference
        indifferent_list = parsed_rule.get_indifferent_list()
        self._preference = CPPreference(parsed_rule.get_best_interval(),
                                        parsed_rule.get_worst_interval(),
                                        indifferent_list, operator)

    def copy(self):
        '''
        Create a copy
        '''
        copy_rule = TCPRule()
        copy_rule.__dict__.update(self.__dict__)
        return copy_rule

    def get_cprule(self):
        '''
        Get a CPRule over the rule
        '''
        return CPRule(self.copy())
