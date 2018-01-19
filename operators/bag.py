# -*- coding: utf-8 -*-
'''
Module with operators
'''

from abc import abstractmethod
import logging

from operators.basic import Operator


LOG = logging.getLogger(__name__)


class BinaryOp(Operator):
    '''
    Binary operator
    '''
    def __init__(self, operand1, operand2):
        Operator.__init__(self)
        # Initialize operand list
        self._operand_list = [operand1, operand2]
        # Create left and right operands
        self._left_operand = operand1
        self._right_operand = operand2
        operand1.set_father(self)
        operand2.set_father(self)

    def is_consistent(self):
        '''
        Check if operator is consistent

        Check if operator has just two operands
        Check if operands are consistent
        '''
        if not Operator.is_consistent(self):
            return False
        if len(self._operand_list) != 2:
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    @abstractmethod
    def run(self, timestamp):
        '''
        Must be override
        '''
        raise NotImplementedError('Run method not implemented')


class BagOp(BinaryOp):
    '''
    Bag operators UNION, INTERSECT, EXCEPT
    '''
    def __init__(self, operand1, operand2):
        BinaryOp.__init__(self, operand1, operand2)
        # Get attribute from first operand
        self._attribute_list = operand1.get_attribute_list()

    def is_consistent(self):
        if not BinaryOp.is_consistent(self):
            return False
        left_att_list = self._left_operand.get_attribute_list()
        right_att_list = self._right_operand.get_attribute_list()
        left_type_list = [att.get_data_type() for att in left_att_list]
        right_type_list = [att.get_data_type() for att in right_att_list]
        # Bags operators are consistent if the attribute type list of the
        # operands are equal
        if left_type_list != right_type_list:
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    @abstractmethod
    def run(self, timestamp):
        '''
        Must be override
        '''
        raise NotImplementedError('Run method not implemented')


class BagUnionOp(BagOp):
    '''
    Union operator
    '''
    def __init__(self, operand1, operand2):
        BagOp.__init__(self, operand1, operand2)
        self._operator_str = 'UNION'
        self._operator_name = 'UNION'

    def run(self, timestamp):
        # Check if operands are ready
        if self.can_run(timestamp):
            # Get record list of left and right operands
            left_list = self._left_operand.get_current_list()
            right_list = self._right_operand.get_current_list()
            right_att_list = self._right_operand.get_attribute_list()
            left_att_list = self._left_operand.get_attribute_list()
            # Rename record attributes of right list (if it is needed)
            if left_att_list != right_att_list:
                right_list = _rename_record_attributes(right_list,
                                                       right_att_list,
                                                       left_att_list)
            self._current_list = left_list + right_list
            self.debug_run()
            self.run_father(timestamp)


class BagIntersectOp(BagOp):
    '''
    Intersect operator
    '''
    def __init__(self, operand1, operand2):
        BagOp.__init__(self, operand1, operand2)
        self._operator_str = 'INTERSECT'
        self._operator_name = 'INTERSECT'

    def run(self, timestamp):
        # Check if operands are ready
        if self.can_run(timestamp):
            # Get record list of left and right operands
            left_list = self._left_operand.get_current_list()
            right_list = self._right_operand.get_current_list()
            right_att_list = self._right_operand.get_attribute_list()
            left_att_list = self._left_operand.get_attribute_list()
            # Rename record attributes of right list (if it is needed)
            if left_att_list != right_att_list:
                right_list = _rename_record_attributes(right_list,
                                                       right_att_list,
                                                       left_att_list)
            self._current_list = bag_intersect(left_list, right_list)
            # Update timestamp
            self.debug_run()
            self.run_father(timestamp)


class BagExceptOp(BagOp):
    '''
    Except operator
    '''
    def __init__(self, operand1, operand2):
        BagOp.__init__(self, operand1, operand2)
        self._operator_str = 'EXCEPT'
        self._operator_name = 'EXCEPT'

    def run(self, timestamp):
        # Check if operands are ready
        if self.can_run(timestamp):
            # Get record list of left and right operands
            left_list = self._left_operand.get_current_list()
            right_list = self._right_operand.get_current_list()
            right_att_list = self._right_operand.get_attribute_list()
            left_att_list = self._left_operand.get_attribute_list()
            # Rename record attributes of right list (if it is needed)
            if left_att_list != right_att_list:
                right_list = _rename_record_attributes(right_list,
                                                       right_att_list,
                                                       left_att_list)
            self._current_list = bag_except(left_list, right_list)
            # Update timestamp
            self.debug_run()
            self.run_father(timestamp)


def _group_equal_records(record_list):
    '''
    Group equals records into a dictionary

    Each entry has the record values as key
    and a list of equal records
    '''
    group_dict = {}
    for rec in record_list:
        rec_key = tuple(rec.items())
        if rec_key in group_dict:
            group_dict[rec_key].append(rec)
        else:
            group_dict[rec_key] = [rec]
    return group_dict


def bag_intersect(left_list, right_list):
    '''
    Bag intersection between two list
    '''
    # Count element of each list
    left_dict = _group_equal_records(left_list)
    right_dict = _group_equal_records(right_list)
    result_list = []
    for rec_key in left_dict:
        if rec_key in right_dict:
            if len(left_dict[rec_key]) < len(right_dict[rec_key]):
                result_list += left_dict[rec_key]
            else:
                result_list += right_dict[rec_key]
    return result_list


def bag_except(left_list, right_list):
    '''
    Bag exception (difference) between two list
    '''
    result_list = []
    # Count element of each operand
    left_dict = _group_equal_records(left_list)
    right_dict = _group_equal_records(right_list)
    for rec_key in left_dict:
        # Check if left record and in right side
        if rec_key in right_dict:
            # Check if left count is greater than right count
            left_len = len(left_dict[rec_key])
            right_len = len(right_dict[rec_key])
            if left_len > right_len:
                count = left_len - right_len
                # Put correct count in output
                left_list = left_dict[rec_key]
                result_list += left_list[:count]
        else:
            # If record is only in left side, put it on output
            result_list += left_dict[rec_key]
    return result_list


def _rename_record_attributes(record_list, old_attribute_list,
                              new_attribute_list):
    '''
    Rename record attributes
    '''
    result_list = []
    for rec in record_list:
        new_rec = {}
        for index, old_att in enumerate(old_attribute_list):
            new_att = new_attribute_list[index]
            new_rec[new_att] = rec[old_att]
        result_list.append(new_rec)
    return result_list
