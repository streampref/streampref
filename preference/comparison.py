# -*- coding: utf-8 -*-
'''
Module to manipulate comparisons
'''


class Comparison(object):
    '''
    Class to represent comparisons
    '''

    def __init__(self, best_formula_dict, worst_formula_dict,
                 indifferent_set):
        # Preferred formula
        self._best_formula_dict = best_formula_dict
        # non preferred formula
        self._worst_formula_dict = worst_formula_dict
        # Indifferent set
        self._indifferent_set = indifferent_set

    def __str__(self):
        comp_str = get_string_formula(self._best_formula_dict)
        comp_str += ' > '
        comp_str += get_string_formula(self._worst_formula_dict)
        str_list = [str(att) for att in self._indifferent_set]
        comp_str += '[' + ','.join(str_list) + ']'
        return comp_str

    def __repr__(self):
        return self.__str__()

    def __cmp__(self, other):
        len_self_indif = len(self.get_indifferent_set())
        len_other_indif = len(other.get_indifferent_set())
        if len_self_indif != len_other_indif:
            return -1 * cmp(len(self.get_indifferent_set()),
                            len(other.get_indifferent_set()))
        else:
            len_self_form = len(self.get_preferred_formula()) + \
                len(self.get_notpreferred_formula())
            len_other_form = len(other.get_preferred_formula()) + \
                len(other.get_notpreferred_formula())
            return cmp(len_self_form, len_other_form)

    def __eq__(self, other):
        return isinstance(self, Comparison) and \
            isinstance(other, Comparison) and \
            str(self) == str(other)

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(str(self))

    def get_preferred_formula(self):
        '''
        Get preferred formula
        '''
        return self._best_formula_dict

    def get_notpreferred_formula(self):
        '''
        Get non preferred formula
        '''
        return self._worst_formula_dict

    def get_indifferent_set(self):
        '''
        Get preferred indifferent set
        '''
        return self._indifferent_set

    def is_best_record(self, record):
        '''
        Check if record satisfies preferred values
        '''
        return _is_formula_valid_by_record(self._best_formula_dict, record)

    def is_worst_record(self, record):
        '''
        Check if record satisfies non preferred values
        '''
        return _is_formula_valid_by_record(self._worst_formula_dict, record)

    def dominates(self, record1, record2):
        '''
        Returns True if 'record1' dominates (is preferred to)
        'record2' according to comparison
        '''
        # Check if record1 satisfies preferred values
        if not self.is_best_record(record1):
            return False
        # Check if other record1 satisfies non preferred values
        if not self.is_worst_record(record2):
            return False
        # Check if attributes of records
        # (except attributes in indifferent set)
        # have the same value
        att_records_set = set(record1.keys() + record2.keys())
        for att in att_records_set:
            if att not in self._indifferent_set:
                if att not in record1 or \
                        att not in record2 or \
                        record1[att] != record2[att]:
                    return False
        return True

    def is_more_generic_than(self, other):
        '''
        Return True if self is more generic than other, otherwise return False

        A comparison b: f+ > f-[W] (self) is more generic than
        b': g+^a+ > g-^a-[W2] (other) if (1) or (2).
          (1) g+ = f+, g-= f-, a+ = a- and W2 is subset of W
          (2) g+ = f+, g- = f-, (Attr(a+) union W2) is subset of W
              and (Attr(a-) union W2) is subset of W
        '''
        # W
        w_indiff = self.get_indifferent_set()
        # f+
        f_pref = self._best_formula_dict
        # f-
        f_notpref = self._worst_formula_dict
        # W2
        w2_indiff = other.get_indifferent_set()
        # a+ = (g+ ^ a+) - (f+)
        a_pref = get_difference_formula(other.get_preferred_formula(), f_pref)
        # a- = (g- ^ a-) - (f-)
        a_notpref = get_difference_formula(other.get_notpreferred_formula(),
                                           f_notpref)
        # g+ = (g+ ^ a+) - (a+)
        g_pref = get_difference_formula(other.get_preferred_formula(), a_pref)
        # g- = (g- ^ a-) - (a-)
        g_notpref = get_difference_formula(other.get_notpreferred_formula(),
                                           a_notpref)
        # Check if f+ = g+ and f- = g-
        if f_pref == g_pref and f_notpref == g_notpref:
            # Check if a+ = a-, W2 is subset of W
            if a_pref == a_notpref and w2_indiff.issubset(w_indiff):
                return True
            # W2 union Att(a+)
            aw2_pref = w2_indiff.union(set(a_pref.keys()))
            # W2 union Att(a-)
            aw2_notpref = w2_indiff.union(set(a_notpref.keys()))
            # Check if Att(a+) union W2) is subset of W
            # and (Att(a-) union W2) is subset of W
            if aw2_pref.issubset(w_indiff) and aw2_notpref.issubset(w_indiff):
                return True
        return False


def get_string_formula(formula):
    '''
    Convert a formula stored in dictionary in a string
    '''
    attribution_list = []
    for att in formula:
        interval = formula[att]
        attribution_list.append(interval.get_string(att))
    return '(' + ')^('.join(attribution_list) + ')'


def get_difference_formula(big_formula, small_formula):
    '''
    Return attributions in big formula and not in small formula
    '''
    formula = {}
    for att in big_formula:
        if att not in small_formula:
            formula[att] = big_formula[att]
    return formula


def _is_formula_valid_by_record(formula, record):
    '''
    Return True if the record satisfies the formula, else return False
    '''
    # For each formula proposition attribute
    for att in formula:
        # Take the interval of attribute in the formula
        interval = formula[att]
        # Check if attribute does not exists in record or
        # if record attribute value does not match with correspondent
        # formula interval
        if att not in record or \
                not interval.is_inside_or_equal(record[att]):
            return False
    # Returns true if all attributes are ok
    return True


def build_comparison(formula1, formula2, rule):
    '''
    Build a comparison using formula1 and non preferred formula1,
    when possible.

    If formula1 is preferred to formula2 build and return the comparison
    Else return None
    '''
    pref = rule.get_preference()
    indiff_set = set([pref.get_preference_attribute()])
    indiff_set = indiff_set.union(pref.get_indifferent_set())
    return Comparison(formula1, formula2, indiff_set)
