# -*- coding: utf-8 -*-
'''
Module to manipulate conditional preference theories (cp-theories)
'''

import logging

from control.config import TUP_ALG_PARTITION, \
    TUP_ALG_DEPTH_SEARCH, TUP_ALG_INC_ANCESTORS, TUP_ALG_INC_PARTITION, \
    TUP_ALG_INC_GRAPH, TUP_ALG_INC_GRAPH_NO_TRANSITIVE
from preference.comparison import Comparison, build_comparison, \
    get_string_formula
from preference.interval import Interval
from preference.preferencegraph import PreferenceGraph


LOG = logging.getLogger(__name__)


class CPTheory(object):
    '''
    Class to represent a conditional preference theory
    '''
    def __init__(self, rule_list, pref_alg, skip_consistency=False):
        # Best algorithm to be used
        self._pref_alg = pref_alg
        # List of rules
        self._rule_list = rule_list
        # List of formulas (used by partition method)
        self._formula_list = []
        # List of comparisons (used by partition method)
        self._comparison_list = []
        self._consistent = True
        if not skip_consistency:
            self._consistent = self._check_consistency()
        if self._pref_alg in [TUP_ALG_DEPTH_SEARCH,
                              TUP_ALG_INC_ANCESTORS,
                              TUP_ALG_INC_GRAPH]:
            # Use dominance test by search for others algorithms
            self.dominates = self._dominates_by_search
        elif self._pref_alg == TUP_ALG_INC_GRAPH_NO_TRANSITIVE:
            self.dominates = self._direct_dominates
        if self._pref_alg in [TUP_ALG_PARTITION,
                              TUP_ALG_INC_PARTITION] and \
                self.is_consistent():
            # Build comparisons for partition algorithm
            self._build_comparisons()

    def __len__(self):
        return len(self._rule_list)

    def __str__(self):
        rule_str_list = [str(rule) for rule in self._rule_list]
        return '\n'.join(rule_str_list)

    def __repr__(self):
        return self.__str__()

    def _check_consistency(self):
        '''
        Check theory consistency
        '''
        if check_rules_consistency(self._rule_list):
            # Split rules interval
            self._rule_list = _split_rules(self._rule_list)
            if self._is_global_consistent() \
                    and self._is_local_consistent():
                return True
        return False

    def _is_global_consistent(self):
        '''
        Check global consistency of theory

        Build a graph with edges (C) -> (P) and (P) -> (I), where:
            (C) are the attributes in the condition
            (P) is the rule attribute
            (I) are the rule indifferent attributes
        All rules are considered
        If builded graph is acyclic, then theory is globally consistent
        '''
        # Initialize graph
        graph = PreferenceGraph()
        # For each rule
        for rule in self._rule_list:
            # For each condition in rule
            cond = rule.get_condition()
            pref = rule.get_preference()
            for att in cond.get_present_condition_dict():
                # Add edge (C) -> (P)
                graph.add_edge(att, pref.get_preference_attribute())
            # For each indifferent attribute
            for indiff_att in pref.get_indifferent_set():
                # Add edge (P) -> (I)
                graph.add_edge(pref.get_preference_attribute(), indiff_att)
        # Check if graph is acyclic
        return graph.is_acyclic()

    def _get_rule_list_by_attribute(self, attribute):
        '''
        Get rules with attribute key is equal specified attribute
        '''
        rules_list = []
        for rule in self._rule_list:
            if rule.get_preference_attribute() == attribute:
                rules_list.append(rule)
        return rules_list

    def _is_local_consistent(self):
        '''
        Check if theory is local consistent

        A theory is local inconsistent if there are a set of compatible rules
        such that an interval is preferred than itself
        '''
        for rule_set in self._get_compatible_sets():
            rule_list = [self._rule_list[index] for index in rule_set]
            graph = _build_interval_graph(rule_list)
            if not graph.is_acyclic():
                return False
        return True

    def _build_formulas(self):
        '''
        Generate a list of formulas combining all intervals of attributes
        '''
        # Get atomic formulas in all rules
        atomic_formula_list = []
        for rule in self._rule_list:
            for formula in rule.get_atomic_formulas_list():
                if formula not in self._formula_list:
                    self._formula_list.append(formula)
                    atomic_formula_list.append(formula)
        # Combined formulas
        for atomic in atomic_formula_list:
            new_formula_list = []
            att = atomic.keys()[0]
            for formula in self._formula_list:
                if att not in formula:
                    formula_copy = formula.copy()
                    formula_copy[att] = atomic[att]
                    if formula_copy not in self._formula_list \
                            and formula_copy not in new_formula_list:
                        new_formula_list.append(formula_copy)
            self._formula_list += new_formula_list

    def _clean_comparisons(self):
        '''
        Remove not essential comparisons
        '''
        # Copy comparison list
        initial_list = self._comparison_list[:]
        # List of essential comparisons
        essential_list = []
        # Run while there is comparisons to process
        while len(initial_list) > 0:
            # Take one comparison
            comp = initial_list.pop()
            # Suppose comparison is essential
            essential = True
            # Check all another comparisons
            for other_comp in initial_list + essential_list:
                # Check if other comparison is more generic
                if other_comp.is_more_generic_than(comp):
                    # So, comparison is not essential
                    essential = False
                    break
            # If no one is more generic, comparison is essential
            if essential:
                essential_list.append(comp)
        self._comparison_list = essential_list

    def _build_comparisons(self):
        '''
        Generate comparisons
        '''
        # Build formulas
        self._build_formulas()
        if LOG.isEnabledFor(logging.DEBUG):
            formula_str_list = [get_string_formula(formula)
                                for formula in self._formula_list]
            LOG.debug('Formulas:\n' + '\n'.join(formula_str_list))
        # Generate direct comparisons
        comp_dict = {}
        for idx1, formula1 in enumerate(self._formula_list):
            comp_dict[idx1] = {}
            for idx2, formula2 in enumerate(self._formula_list):
                tmp_set = set()
                if idx1 != idx2:
                    for rule in self._rule_list:
                        # Check if formula1 dominates formula2
                        if rule.formula_dominates(formula1, formula2):
                            comp = build_comparison(formula1, formula2, rule)
                            if comp not in tmp_set:
                                tmp_set.add(comp)
                comp_dict[idx1][idx2] = tmp_set
        self._build_transitive_comparisons(comp_dict)

    def _build_transitive_comparisons(self, comp_dict):
        '''
        Generate transitive comparisons (Floyd-Warshall Algorithm)
        '''
        # Generate transitive
        for k in range(len(self._formula_list)):
            for i in range(len(self._formula_list)):
                for j in range(len(self._formula_list)):
                    ik_set = comp_dict[i][k]
                    kj_set = comp_dict[k][j]
                    if len(ik_set) and len(kj_set):
                        comp_set = _combine_transitive(ik_set, kj_set)
                        comp_set = comp_set.union(comp_dict[i][j])
                        comp_dict[i][j] = comp_set
        self._comparison_list = []
        for i in range(len(self._formula_list)):
            for j in range(len(self._formula_list)):
                self._comparison_list += list(comp_dict[i][j])
        # Remove not essential comparisons
        self._comparison_list.sort()
        if LOG.isEnabledFor(logging.DEBUG):
            comp_str_list = [str(comp) for comp in self._comparison_list]
            LOG.debug('All Comparisons:\n' + '\n'.join(comp_str_list))
        self._clean_comparisons()
        self._comparison_list.sort()
        if LOG.isEnabledFor(logging.DEBUG):
            comp_str_list = [str(comp) for comp in self._comparison_list]
            LOG.debug('Essential Comparisons:\n' + '\n'.join(comp_str_list))

    def _dominates_by_search(self, record1, record2):
        '''
        Returns True if record1 dominates (is preferred to) record2
        according to theory (dominance test by search)
        '''
        if record1 != record2:
            return _dominates_by_search(self._rule_list, record1, record2)
        return False

    def _get_compatible_sets(self):
        '''
        Get a list of maximal sets of compatible rules

        Two CPRules are compatibles if they have the same preference attribute
        and their conditions are compatibles
        '''
        # Initial list of sets (one rule per set)
        set_list = [set([rule_id]) for rule_id in range(len(self._rule_list))]
        change = True
        # Suppose no changes
        while change:
            change = False
            # New list of combined sets
            new_set_list = []
            for rule_set in set_list:
                # Suppose no combination
                combined = False
                # For each rules
                for rule_id in range(len(self._rule_list)):
                    # Check if rule is compatible with set
                    # and rule not in this set
                    if self._is_cprule_compatible_to_list(rule_id, rule_set) \
                            and rule_id not in rule_set:
                        combined = True
                        # Create new set and add this rule
                        new_set = rule_set.copy()
                        new_set.add(rule_id)
                        # Check if set does not exists
                        if new_set not in new_set_list:
                            change = True
                            new_set_list.append(new_set)
                # if there was not combinations consider original set
                if not combined:
                    new_set_list.append(rule_set)
            set_list = new_set_list
        return set_list

    def _is_cprule_compatible_to_list(self, rule_id, rule_id_list):
        '''
        Check if a cp-rule is compatible to every other cp-rule in a list
        '''
        cprule = self._rule_list[rule_id]
        for other_id in rule_id_list:
            other = self._rule_list[other_id]
            if not cprule.is_compatible_to(other):
                return False
        return True

    def is_consistent(self):
        '''
        Return True if cp-theory is consistent, else return False
        '''
        return self._consistent

    def get_comparison_list(self):
        '''
        Return the comparison list
        '''
        return self._comparison_list

    def debug_btg(self, record_list):
        '''
        Debug a BTG over a record list according to rules of theory
        '''
        if LOG.isEnabledFor(logging.DEBUG):
            str_btg = "\nTuples:"
            for index, record in enumerate(record_list):
                str_btg += "\nt" + str(index + 1) + " = " + str(record)
            str_btg += "\n\nRules:"
            for index, rule in enumerate(self._rule_list):
                str_btg += "\n(R" + str(index + 1) + ") = " + str(rule)
            str_btg += "\n\nDirect BTG:"
            for index1, record1 in enumerate(record_list):
                for index2, record2 in enumerate(record_list):
                    for index, rule in enumerate(self._rule_list):
                        if rule.record_dominates(record1, record2):
                            str_btg += "\nt" + str(index1+1) + \
                                " (R" + str(index+1) + ") t" + str(index2+1)
            str_btg += "\n\nFull BTG:"
            for index1, record1 in enumerate(record_list):
                for index2, record2 in enumerate(record_list):
                    if self.dominates(record1, record2):
                        str_btg += "\nt" + str(index1 + 1) + \
                                " -> t" + str(index2 + 1)
            LOG.debug("BTG:" + str_btg)

    def _direct_dominates(self, record1, record2):
        '''
        Check if record1 dominates directly by one rule record2
        '''
        for rule in self._rule_list:
            if rule.record_dominates(record1, record2):
                return True
        return False


class TCPTheory(object):
    '''
    Class to represent temporal conditional preference theory (tcp-theory)
    '''
    def __init__(self, rule_list, pref_alg):
        # Rules list
        self._rule_list = rule_list
        self._pref_alg = pref_alg
        self._consistent = True
        self._consistent = self._check_consistency()

    def __len__(self):
        return len(self._rule_list)

    def __str__(self):
        rule_str_list = [str(rule) for rule in self._rule_list]
        return '\n'.join(rule_str_list)

    def __repr__(self):
        return self.__str__()

    def _get_temporal_compatible_sets(self):
        '''
        Get a list of lists of temporal compatible rules

        Two TCPRules are temporal compatible if their past conditions
        are compatibles
        '''
        # Initial list of sets
        set_list = []
        # For each rule
        for rule in self._rule_list:
            rule_set = set([rule])
            # Check if every other rule is temporal compatible
            for other_rule in self._rule_list:
                cond = rule.get_condition()
                other_cond = other_rule.get_condition()
                if cond.is_temporal_compatible_to(other_cond):
                    rule_set.add(other_rule)
            # Add set to set list
            set_list.append(rule_set)
        # Remove duplicated sets
        result_list = []
        for rule_set in set_list:
            if rule_set not in result_list:
                result_list.append(rule_set)
        return result_list

    def _check_consistency(self):
        '''
        Check if TCPTheory is consistent

        A TCPTHeory is consistent if all sets of temporal compatible rules
        are consistent
        '''
        if check_rules_consistency(self._rule_list):
            LOG.debug('Original TCPTheory: %s', self)
            # Split rules interval
            self._rule_list = _split_rules(self._rule_list)
            LOG.debug('TCPTheory after split: %s', self)
            # Build the sets of temporal compatible rules
            set_list = self._get_temporal_compatible_sets()
            # Test each set
            for rule_set in set_list:
                # Build a CPTheory over the set
                cptheory = CPTheory(list(rule_set), TUP_ALG_DEPTH_SEARCH)
                # Check if this CPTheory is consistent
                if not cptheory.is_consistent():
                    return False
        return True

    def get_valid_rules(self, sequence, position):
        '''
        Get all valid rules for a position of a sequence
        '''
        result_list = []
        for rule in self._rule_list:
            cond = rule.get_condition()
            if cond.is_valid_by_position(sequence, position):
                result_list.append(rule)
        return result_list

#     def get_temporal_valid_rules(self, sequence, position):
#         '''
#         Get all valid rules for a position of a sequence
#         '''
#         result_list = []
#         for rule in self._rule_list:
#             cond = rule.get_condition()
#             if sequence is None and not cond.has_previous():
#                 result_list.append(rule)
#             if cond.is_temporal_valid_by_position(sequence, position):
#                 result_list.append(rule)
#         return result_list

#     def get_rules_first_position(self):
#         '''
#         Get rules temporally valid only in the first position of any sequence
#         '''
#         result_list = []
#         for rule in self._rule_list:
#             cond = rule.get_condition()
#             if not cond.has_previous():
#                 result_list.append(rule)
#         return result_list

    def is_consistent(self):
        '''
        Return True if tcp-theory is consistent, else return False
        '''
        return self._consistent

    def dominates_by_search(self, sequence, goal_sequence):
        '''
        Check if a sequence dominate other sequence
        '''
        # Search for first different position
        pos = sequence.get_first_different_position(goal_sequence)
        if pos != -1:
            # Get records of this position
            rec = sequence.get_position(pos)
            goal_rec = goal_sequence.get_position(pos)
            # Get valid rules for this position
            valid_rule_list = self.get_valid_rules(sequence, pos)
            cptheory = CPTheory(valid_rule_list, TUP_ALG_DEPTH_SEARCH,
                                skip_consistency=True)
            return cptheory.dominates(rec, goal_rec)
        else:
            return False

    def is_candidate_position(self, record):
        '''
        Check if a record is a candidate position
        '''
        for rule in self._rule_list:
            pref = rule.get_preference()
            cond = rule.get_condition()
            if cond.is_valid_by_record(record):
                if pref.is_best_valid_by_record(record) or \
                        pref.is_worst_valid_by_record(record):
                    return True
        return False

    def get_rule_list(self):
        '''
        Return a list of rules of tcp-theory
        '''
        return self._rule_list

    def debug_btg(self, sequence_list):
        '''
        Debug a BTG over a sequence list according to the rules
        '''
        if LOG.isEnabledFor(logging.DEBUG):
            str_btg = "\nSequences:"
            for index, seq in enumerate(sequence_list):
                str_btg += "\ns" + str(index + 1) + " = " + str(seq)
            str_btg += "\n\nRules:"
            for index, rule in enumerate(self._rule_list):
                str_btg += "\n(R" + str(index + 1) + ") = " + str(rule)
            str_btg += "\n\nDirect BTG:"
            for index1, seq1 in enumerate(sequence_list):
                for index2, seq2 in enumerate(sequence_list):
                    for index, rule in enumerate(self._rule_list):
                        if directly_dominates(rule, seq1, seq2):
                            str_btg += "\ns" + str(index1+1) + \
                                " (R" + str(index+1) + ") s" + str(index2+1)
            str_btg += "\n\nFull BTG:"
            for index1, seq1 in enumerate(sequence_list):
                for index2, seq2 in enumerate(sequence_list):
                    if self.dominates_by_search(seq1, seq2):
                        str_btg += "\ns" + str(index1 + 1) + \
                                " -> s" + str(index2 + 1)
            LOG.debug("BTG:" + str_btg)


def _build_interval_graph(rule_list):
    '''
    Build a graph with edges (P) -> (NP) over a rule list

    (P) is the preferred interval and (NP) is the non preferred interval
    of each rule
    '''
    graph = PreferenceGraph()
    for rule in rule_list:
        pref = rule.get_preference()
        graph.add_edge(str(pref.get_best_interval()),
                       str(pref.get_worst_interval()))
    return graph


def _split_rules(rule_list):
    '''
    Searches for rules with intersection in intervals.
    When that is found, new rules are generated with disjoint intervals.
    Example:
        - Two intersected intervals: (1 < A < 9) and (2 < A < 10)
        - Three three new intervals: (1 < A <= 2) and (2 < A <= 9) and
                                    (9 < A < 10)
    The original number of rules can be increased
    '''
    change = True
    # While there are splits
    while change:
        # Suppose that not will be splits
        change = False
        # List of new splits
        new_split_list = []
        for rule in rule_list:
            for other_rule in rule_list:
                # Try split 'rule'
                new_split_list = rule.split(other_rule)
                # Break on splits
                if new_split_list != []:
                    break
            # If there are splits
            if new_split_list != []:
                change = True
                # Remove original rule
                rule_list.remove(rule)
                # Add new split rules
                for new_rule in new_split_list:
                    if new_rule not in rule_list:
                        rule_list.append(new_rule)
                break
    return rule_list


def check_rules_consistency(rule_list):
    '''
    Check the consistency of a list of rules
    '''
    for rule in rule_list:
        if not rule.is_consistent():
            return False
    return True


def is_goal_record(record, goal_record):
    '''
    Check if first record reaches goal record

    A record reaches a goal if its attributes are inside or equal of
    correspondent goal attributes
    Indifferent attributes of goal are ignored
    '''
    for att in goal_record:
        if att not in record:
            return False
        goal_value = goal_record[att]
        value = record[att]
        # Check if goal attribute is an interval
        # and record attribute is inside it
        if isinstance(goal_value, Interval) and \
                goal_value.is_inside_or_equal(value):
            continue
        # Check if record attribute is equal to goal attribute
        elif value == goal_value:
            continue
        else:
            return False
    return True


def is_goal_formula(formula, goal_formula):
    '''
    Check if first formula reaches goal formula

    A formula reaches a goal if its attributes are inside or equal of
    correspondent goal attributes
    '''
    for att in formula:
        # Just check attribute presents in goal (indifferent ones were dropped)
        if att in goal_formula:
            value = formula[att]
            goal_value = goal_formula[att]
            # check if record attribute is inside or equal to goal attribute
            if goal_value.is_inside_or_equal(value):
                return False
    return True


def _combine_transitive(set1, set2):
    '''
    Combine two set of transitive comparisons
    b: f1 > f2[W] and b': f1' > f2'[W'] are transitive if
    f2 = f1'
    The combination of then is b'': f1 > f2' [W + W']
    '''
    result_set = set()
    for comp1 in set1:
        for comp2 in set2:
            indiff_set = comp1.get_indifferent_set()
            indiff_set = indiff_set.union(comp2.get_indifferent_set())
            comp = Comparison(comp1.get_preferred_formula(),
                              comp2.get_notpreferred_formula(),
                              indiff_set)
            result_set.add(comp)
    return result_set


def _dominates_by_search(rule_list, record1, record2):
    '''
    Returns True if record1 dominates (is preferred to) record2
    according to theory (dominance test by search)
    '''
    # Check if record2 is the goal (record1)
    if is_goal_record(record2, record1):
        return True
    else:
        # For every rule
        for index, rule in enumerate(rule_list):
            # try to create new record by applying current rule
            new_rec = rule.change_record(record1)
            # Check if new record is valid
            if new_rec is not None:
                # Create new rule list excluding curent rule
                new_rule_list = [rule2
                                 for index2, rule2 in enumerate(rule_list)
                                 if index != index2]
                # Make the recursive call
                if _dominates_by_search(new_rule_list, new_rec, record2):
                    return True
        return False


def directly_dominates(rule, sequence, goal_sequence):
    '''
    Check if a sequence dominate other sequence according to a rule
    '''
    # Search for first different position
    pos = sequence.get_first_different_position(goal_sequence)
    if pos != -1:
        cond = rule.get_condition()
        if cond.is_valid_by_position(sequence, pos):
            # Get records of this position
            rec = sequence.get_position(pos)
            goal_rec = goal_sequence.get_position(pos)
            cptheory = CPTheory([rule], TUP_ALG_DEPTH_SEARCH,
                                skip_consistency=True)
            return cptheory.dominates(rec, goal_rec)
    return False
