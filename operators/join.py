# -*- coding: utf-8 -*-
'''
Module with operators
'''
import logging

from grammar.symbols import TABLE_SYM
from operators.basic import Operator


LOG = logging.getLogger(__name__)


class JoinOp(Operator):
    '''
    Join Operator
    '''
    def __init__(self, operand_list, where_list):
        Operator.__init__(self)
        self._operand_list = operand_list
        # Join conditions
        self._contition_list = []
        # Attribute list of each operand
        self._operand_attribute_dict = {}
        # Build attribute list
        for index, operand in enumerate(self._operand_list):
            operand.set_father(self)
            self._operand_attribute_dict[index] = []
            for att in operand.get_attribute_list():
                # Add attribute
                new_att = self._add_attribute(att.get_name(),
                                              att.get_data_type(),
                                              att.get_table())
                # Link attribute to correspondent operand
                new_att.set_link(att)
                self._operand_attribute_dict[index].append(new_att)
        self._build_join_condition(where_list)
        self._operator_name = 'JOIN'
        self._operator_str = 'JOIN[{j}]'.format(j=str(self._contition_list))

    def _build_join_condition(self, where_list):
        '''
        Build join conditions from where_list
        '''
        # For each condition in where list
        for cond in where_list:
            # Get first parsed attribute
            parsed_att = cond[0]
            # Look for this attribute in the attribute list
            att1 = self.find_attribute(parsed_att.get_name(),
                                       parsed_att.get_table())
            # Same for second attribute
            parsed_att = cond[2]
            att2 = self.find_attribute(parsed_att.get_name(),
                                       parsed_att.get_table())
            # Add to condition list
            new_cond = [att1, att2]
            self._contition_list.append(new_cond)

    def is_consistent(self):
        if not Operator.is_consistent(self):
            return False
        for operand in self._operand_list:
            if operand.get_result_type() != TABLE_SYM:
                LOG.error('Operator %s not consistent', self)
                LOG.error('Operator input is not a table')
                return False
        for cond in self._contition_list:
            # Check if some attribute is invalid
            if None in cond:
                LOG.error('Operator %s not consistent', self)
                LOG.error('Invalid condition: %s', str(self._contition_list))
                return False
        return True

    def _get_matched_conditions(self, jtable1, jtable2):
        '''
        Check if a join tables match with
        some join condition and returns matched conditions.
        The matched conditions are mapped to link attributes
        '''
        matched_list = []
        for cond in self._contition_list:
            att1 = cond[0]
            att2 = cond[1]
            # Alwaws put joint jtable1 attributes first in the condition
            if att1.get_table() in jtable1.get_name_list() \
                    and att2.get_table() in jtable2.get_name_list():
                matched_list.append([att1, att2])
            elif att2.get_table() in jtable1.get_name_list() \
                    and att1.get_table() in jtable2.get_name_list():
                matched_list.append([att2, att1])
        return matched_list

    def run(self, timestamp):
        if self.can_run(timestamp):
            jtable_list = []
            # Get jtables
            for index, operand in enumerate(self._operand_list):
                jtable = JoinTable(operand.get_name(),
                                   self._operand_attribute_dict[index],
                                   operand.get_current_list())
                jtable_list.append(jtable)
            # Join
            jtable_list = self._join(jtable_list)
            # Cross product
            jtable = _cross_product_jtable_list(jtable_list)
            self._current_list = jtable.get_record_list()
            self.debug_run()
            self.run_father(timestamp)

    def _join(self, jtable_list):
        '''
        Join jtables of jtable list
        '''
        # Sort jtables by length
        jtable_list.sort(key=len)
        cross_list = []
        # Join jtables
        while len(jtable_list) > 0:
            # Take one jtable
            jtable = jtable_list.pop(0)
            joined = False
            # Try to join this jtable with another
            for index, other_jtable in enumerate(jtable_list):
                matched_cond = self._get_matched_conditions(jtable,
                                                            other_jtable)
                # Check if there can be joined
                if matched_cond != []:
                    joined = True
                    jtable.join(other_jtable, matched_cond)
                    # Remove the second joined jtable
                    del jtable_list[index]
                    break
            # Check if jtable cannot be joined
            if not joined:
                cross_list.append(jtable)
            else:
                jtable_list.insert(0, jtable)
        return cross_list


class JoinTable(object):
    '''
    Class to represent join-tables
    '''
    def __init__(self, name, attribute_list, record_list):
        self._name_list = [name]
        # Copy attribute list because it will be changed every run
        self._attribute_list = attribute_list[:]
        self._record_list = record_list

    def __len__(self):
        return len(self._record_list)

    def __str__(self):
        return str(self._name_list) + '(' + \
            str(len(self._record_list)) + ')'

    def __repr__(self):
        return self.__str__()

    def get_name_list(self):
        '''
        Get the name list
        '''
        return self._name_list

    def get_record_list(self):
        '''
        Get the record list
        '''
        return self._record_list

    def get_attribute_list(self):
        '''
        Get attribute list
        '''
        return self._attribute_list

    def join(self, other, condition_list):
        '''
        Join with other jtable
        '''
        # Attribute list to be used in join
        self_att_list = [cond[0] for cond in condition_list]
        other_att_list = [cond[1] for cond in condition_list]
        # Update name list
        self._name_list += other.get_name_list()
        # Update attribute list
        self._attribute_list += other.get_attribute_list()
        # Do the hash join
        self._record_list = _hash_join(self.get_record_list(),
                                       other.get_record_list(),
                                       self_att_list, other_att_list)

    def cross_product(self, other):
        '''
        Cross product with other j-table
        '''
        # Update name list
        self._name_list += other.get_name_list()
        # Update attribute list
        self._attribute_list += other.get_attribute_list()
        self._record_list = \
            _cross_product_lists(self._record_list,
                                 other.get_record_list())


def _hash_join(small_record_list, big_record_list, small_att_list,
               big_att_list):
    '''
    Hash join between two records list
    '''
    result_list = []
    # Check if small record list is not empty
    if len(small_record_list) > 0:
        # Build hash over small record list
        hash_dict = {}
        for rec in small_record_list:
            rec_key = _get_join_key(rec, small_att_list)
            if rec_key in hash_dict:
                hash_dict[rec_key].append(rec)
            else:
                hash_dict[rec_key] = [rec]
        # Do the join
        for rec in big_record_list:
            rec_key = _get_join_key(rec, big_att_list)
            if rec_key in hash_dict:
                # Combine a record with a record list
                result_list += _cross_product_lists([rec],
                                                    hash_dict[rec_key])
    return result_list


def _cross_product_lists(record_list1, record_list2):
    '''
    Cross product between two records list
    '''
    result_list = []
    # Check if one of the list is empty
    if record_list1 == [] or record_list2 == []:
        return result_list
    # Combine records
    for rec1 in record_list1:
        for rec2 in record_list2:
            new_rec = rec1.copy()
            new_rec.update(rec2)
            result_list.append(new_rec)
    return result_list


def _cross_product_jtable_list(jtable_list):
    '''
    Cross product over jtables in jtable list
    '''
    while len(jtable_list) > 1:
        jtable1 = jtable_list.pop(0)
        jtable2 = jtable_list.pop(0)
        jtable1.cross_product(jtable2)
        jtable_list.append(jtable1)
    return jtable_list[0]


def _get_join_key(record, attribute_list):
    '''
    Get a key for record based in a attribute list
    The key is composed by attribute position and its value on record
    '''
    key_list = []
    for att in attribute_list:
        key_list.append(record[att])
    return tuple(key_list)
