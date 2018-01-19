# -*- coding: utf-8 -*-
'''
Module UpdateLevel classes used by incremental algorithms to get best tuples
'''
from abc import abstractmethod
import logging

from control.config import TUP_ALG_PARTITION, \
    SEQ_ALG_SEQTREE, SEQ_ALG_SEQTREE_PRUNING
from control.sequence import Sequence
from preference.theory import CPTheory
from operators.updatedata import get_partition_id, inc_count_dict, \
    add_to_set_id, dec_count_dict, delete_from_set_id


LOG = logging.getLogger(__name__)


class PreferenceDict(object):  # IGNORE:too-few-public-methods
    '''
    Class of preference dictionary
    '''
    def __init__(self, tcptheory, hierarchy_type):
        # TCP-Theory
        self._tcptheory = tcptheory
        # CP-Theory dictionary: rules hash -> cp-theory
        self._cptheory_dict = {}
        # Type of hierarchy
        self._hierarchy_type = hierarchy_type

    def _get_theory(self, sequence):
        '''
        Get a cp-theory for a sequence
        '''
        tcptheory = self._tcptheory
        # Get valid rules for last sequence position
        rule_list = get_rules_for_sequence(sequence, tcptheory)
        # Get hash key for rule list
        theory_hash = hash(str(rule_list))
        # Check if hash key does not exists
        if theory_hash not in self._cptheory_dict:
            # Create a cp-theory for rule list
            cptheory = CPTheory(rule_list, TUP_ALG_PARTITION,
                                skip_consistency=True)
            self._cptheory_dict[theory_hash] = cptheory
        else:
            # Take the existent cp-theory
            cptheory = self._cptheory_dict[theory_hash]
        return cptheory

    def get_hierarchy(self, sequence):
        '''
        Get a preference hierarchy for sequence according to hierarchy type
        '''
        if self._hierarchy_type in [SEQ_ALG_SEQTREE,
                                    SEQ_ALG_SEQTREE_PRUNING]:
            cptheory = self._get_theory(sequence)
            return PartitionHierarchy(cptheory)
        else:
            raise NotImplementedError('Hierarchy not implemented: {m}'.
                                      format(m=self._hierarchy_type))


class Hierarchy(object):
    '''
    Generic preference hierarchy
    '''
    def __init__(self, cptheory):
        # CP-Theory for hierarchy
        self._cptheory = cptheory
        # List of comparisons
        if cptheory is not None:
            self._comparison_list = cptheory.get_comparison_list()
        # Dictionary of records
        # ID -> record
        self._record_dict = {}
        # Number of preferred items in a partition
        # partition ID -> count
        self._pref_count_dict = {}

    def add(self, new_record):
        '''
        Add a record to hierarchy
        '''
        new_rec_id = tuple(new_record.items())
        self._record_dict[new_rec_id] = new_record
        return new_rec_id

    def delete(self, del_record):
        '''
        Delete a record from hierarchy
        '''
        del_rec_id = tuple(del_record.items())
        del self._record_dict[del_rec_id]
        return del_rec_id

    @abstractmethod
    def copy(self):
        '''
        Get backup from hierarchy
        '''

    @abstractmethod
    def get_best(self):
        '''
        Return the best (dominant) records
        '''

    @abstractmethod
    def get_string(self):
        '''
        Return a string representing the hierarchy
        '''

    @abstractmethod
    def get_dominant_dominated(self):
        '''
        Return the set of dominant and the set of dominated tuples
        '''

    @abstractmethod
    def get_dominated(self):
        '''
        Return dominated tuples
        '''


class PartitionHierarchy(Hierarchy):
    '''
    Hierarchy partition
    '''
    def __init__(self, cptheory):
        Hierarchy.__init__(self, cptheory)
        # List of non preferred records in a partition
        # partition ID -> records set
        self._nonpref_set_dict = {}
        # Dictionary for dominated count
        # record ID -> count
        self._dominated_count = {}

    def add(self, new_record):
        '''
        Add an item to hierarchy
        Return True for dominated record
        and False for otherwise
        '''
        new_rec_id = Hierarchy.add(self, new_record)
        # For each comparison
        for comp_id, comp in enumerate(self._comparison_list):
            # Get partition id
            pid = get_partition_id(new_record, comp_id, comp)
            # Check if new record is preferred
            if comp.is_best_record(new_record):
                # Increment the number of preferred records
                inc_count_dict(self._pref_count_dict, pid)
                # Check if it was the first preferred record in the partition
                # Nodes in non preferred list become dominated
                if self._pref_count_dict[pid] == 1 and \
                        pid in self._nonpref_set_dict:
                    # For each record in non preferred list
                    for rec_id in self._nonpref_set_dict[pid]:
                        # Increment the number of dominations over the record
                        inc_count_dict(self._dominated_count, rec_id)
            elif comp.is_worst_record(new_record):
                # Add record to non preferred list
                add_to_set_id(self._nonpref_set_dict, pid, new_rec_id)
                # Check if partition has preferred records
                if pid in self._pref_count_dict:
                    # Increment the number of dominations over the record
                    inc_count_dict(self._dominated_count, new_rec_id)
        return new_rec_id in self._dominated_count

    def delete(self, del_record):
        '''
        Delete a record from hierarchy
        '''
        del_rec_id = Hierarchy.delete(self, del_record)
        # For each comparison
        for comp_id, comp in enumerate(self._comparison_list):
            # Get partition id
            pid = get_partition_id(del_record, comp_id, comp)
            # Check if new record is preferred
            if comp.is_best_record(del_record):
                # Decrement preferred counter for partition
                dec_count_dict(self._pref_count_dict, pid)
                # Check if non preferred records become non dominated
                if pid not in self._pref_count_dict \
                        and pid in self._nonpref_set_dict:
                    # Decrement partition dominated counter for these records
                    for rec_id in self._nonpref_set_dict[pid]:
                        dec_count_dict(self._dominated_count, rec_id)
            elif comp.is_worst_record(del_record):
                # Remove from a non preferred list
                delete_from_set_id(self._nonpref_set_dict, pid, del_rec_id)
                if del_rec_id in self._dominated_count:
                    del self._dominated_count[del_rec_id]

    def copy(self):
        hierarchy = PartitionHierarchy(self._cptheory)
        copy_nonpref_set_dict = {}
        for pid, tup_set in self._nonpref_set_dict.items():
            copy_nonpref_set_dict[pid] = tup_set.copy()
        for item, value in self.__dict__.items():
            if isinstance(value, dict):
                hierarchy.__dict__[item] = value.copy()
        self._nonpref_set_dict = copy_nonpref_set_dict
        return hierarchy

    def get_best(self):
        best_list = []
        # For every ID
        for rec_id in self._record_dict:
            # Check if ID is not dominated
            if rec_id not in self._dominated_count:
                best_list.append(rec_id)
        return best_list

    def get_dominant_dominated(self):
        dominant_list = []
        dominated_list = []
        for rec_id in self._record_dict:
            # Check if ID is not dominated
            if rec_id in self._dominated_count:
                dominated_list.append(rec_id)
            else:
                dominant_list.append(rec_id)
        return dominant_list, dominated_list

    def get_dominated(self):
        dominated_list = []
        for rec_id in self._record_dict:
            # Check if ID is not dominated
            if rec_id in self._dominated_count:
                dominated_list.append(rec_id)
        return dominated_list

    def get_string(self):
        hstr = 'CP-Theory: ' + str(self._cptheory)
        hstr += '\nComparisons:'
        str_list = [str(comp) for comp in self._comparison_list]
        hstr += '\n'.join(str_list)
        hstr += '\nRecords:\n'
        str_list = []
        for rec_id, record in self._record_dict.items():
            str_list.append(str(rec_id) + " -> " + str(record))
        hstr += '\n'.join(str_list)
        hstr += '\nPref:\n'
        str_list = []
        for pid, count in self._pref_count_dict.items():
            str_list.append(str(pid) + " = " + str(count))
        str_list.sort()
        hstr += '\n'.join(str_list)
        hstr += '\nNotPref Sets:\n'
        str_list = []
        for pid, tup_set in self._nonpref_set_dict.items():
            str_list.append(str(pid) + " = " +
                            str([str(t) for t in tup_set]))
        str_list.sort()
        hstr += '\n'.join(str_list)
        hstr += '\nPartition Dominated Count:'
        for rec_id, count in self._dominated_count.items():
            hstr += '\n' + str(rec_id) + " = " + str(count)
        return hstr


def get_rules_for_sequence(sequence, tcptheory):
    '''
    Get all valid rules for a position of a sequence
    '''
    # List of rules to be returned
    result_list = []
    # List of rules of input tcp-theory
    rule_list = tcptheory.get_rule_list()
    # Create a fake sequence with additional position for rule validation
    seq = Sequence({})
    if sequence is not None:
        seq = sequence.copy()
    seq.append_position({}, 0, 0, 0)
    # For every rule
    for rule in rule_list:
        # Get rule condition
        cond = rule.get_condition()
        # Check if sequence is not None and rule conditions are valid
        if cond.is_temporal_valid_by_position(seq, len(seq)-1):
            result_list.append(rule)
    return result_list
