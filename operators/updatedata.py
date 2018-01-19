# -*- coding: utf-8 -*-
'''
Module UpdateLevel classes used by incremental algorithms to get best tuples
'''
from abc import abstractmethod
import logging

from operators.basic import record_projection


LOG = logging.getLogger(__name__)


class Hierarchy(object):
    '''
    Base class for data record update
    '''
    def __init__(self, cptheory):
        # Current id for next record to be added
        self._current_id = 1
        # Dictionary id : tuple
        self._id_dict = {}
        # Dictionary tuple : id
        self._tuple_id_dict = {}
        # Count for records
        self._count_dict = {}
        # Set of dominant id
        self._best_set = set()
        # CP-Theory to update record information
        self._cptheory = cptheory

    def _clean(self, del_id):
        '''
        Clean information of a record id
        '''
        # Remove entry record: id
        del_tup = self._id_dict.pop(del_id)
        # Remove entry id: record
        del self._tuple_id_dict[del_tup]
        # Remove counter
        del self._count_dict[del_id]

    def _add(self, record):
        '''
        Add a record to update data
        Return the id of record
        '''
        tup = tuple(record.items())
        # Check if record already exists
        if tup in self._tuple_id_dict:
            # Get record id
            new_id = self._tuple_id_dict[tup]
            # Just increment the count
            self._count_dict[new_id] += 1
        else:
            # Get new record id
            new_id = self._current_id
            # Add the record in id dictionary
            self._tuple_id_dict[tup] = new_id
            # Add the id in record dictionary
            self._id_dict[new_id] = tup
            # Add counter for record
            self._count_dict[new_id] = 1
            # Increment current record id (for next record)
            self._current_id += 1
        return new_id

    def _delete(self, record):
        '''
        Delete a record of update data
        '''
        # Get id of deleted record
        tup = tuple(record.items())
        del_id = self._tuple_id_dict[tup]
        # Decrement counter
        self._count_dict[del_id] -= 1
        if self._count_dict[del_id] == 0:
            self._clean(del_id)
            if del_id in self._best_set:
                self._best_set.remove(del_id)
        return del_id

    def _add_list(self, record_list):
        '''
        Add a list of records
        '''
        # Add each record
        for rec in record_list:
            self._add(rec)

    def _delete_list(self, record_list):
        '''
        Delete a list of records
        '''
        # remove all records
        for rec in record_list:
            self._delete(rec)

    def update(self, delete_list, insert_list):
        '''
        Delete and insert lists of records
        '''
        self._delete_list(delete_list)
        self._add_list(insert_list)
        self.debug()

    def get_best_records(self):
        '''
        Return the dominant records
        '''
        result_list = []
        # Search for records with level equal to zero
        for tup_id in self._best_set:
            # Get correspondent record
            tup = self._id_dict[tup_id]
            rec = dict(tup)
            # Get correct count of records
            rec_list = [rec] * self._count_dict[tup_id]
            result_list += rec_list
        return result_list

    @abstractmethod
    def debug(self):
        '''
        Debug UpdateData
        '''

    @abstractmethod
    def get_topk(self, topk):
        '''
        Must be override
        '''
        raise NotImplementedError('Run method not implemented')


class HierarchyAncestors(Hierarchy):
    '''
    Class to store levels and ancestors of records
    '''
    def __init__(self, cptheory, initial_list=None):
        Hierarchy.__init__(self, cptheory)
        # Ancestors of records
        self._ancestors_dict = {}
        # Levels of records
        self._level_dict = {}
        # Records do be updated (level = -1)
        self._update_list = []
        # Add records of initial record list
        if initial_list is not None:
            self._add_list(initial_list)

    def _clean(self, del_id):
        # Get level of deleted record
        del_level = self._level_dict[del_id]
        # Hierarchy all other records
        # (maybe deleted is an ancestor of someone)
        for rec_id in self._ancestors_dict:
            # Get level of other record
            level = self._level_dict[rec_id]
            # Skip (deleted record cannot be an ancestor of current record)
            if level <= del_level:
                continue
            # Take the ancestor set
            anc_set = self._ancestors_dict[rec_id]
            # Check if deleted record is in ancestor set
            if del_id in anc_set:
                # Remove deleted record from ancestor set
                anc_set.remove(del_id)
                # Put record with ancestors changed to be updated
                self._update_list.append(rec_id)
        Hierarchy._clean(self, del_id)
        del self._level_dict[del_id]
        del self._ancestors_dict[del_id]

    def _add(self, record):
        new_id = Hierarchy._add(self, record)
        # Add "new" record id to update set
        if self._count_dict[new_id] == 1:
            # Add new record to update list
            self._update_list.append(new_id)
            # Add record id to level dictionary
            self._level_dict[new_id] = -1
            # Add record id to ancestor dictionary
            self._ancestors_dict[new_id] = []
            # Hierarchy ancestors of existent records
            self._update_ancestors(new_id, record)

    def _update_ancestors(self, rec_id, record):
        '''
        Hierarchy ancestor according to a record id
        '''
        # Consider all other records
        for other_id, tup in self._id_dict.iteritems():
            # Take an existent record
            other_rec = dict(tup)
            # Check if existent record dominates new record
            if self._cptheory.dominates(other_rec, record):
                self._ancestors_dict[rec_id].append(other_id)
            # Check the opposite
            elif self._cptheory.dominates(record, other_rec):
                # Put existent record in update list
                self._ancestors_dict[other_id].append(rec_id)
                self._update_list.append(other_id)
                if self._level_dict[other_id] == 0:
                    self._best_set.remove(other_id)
                self._level_dict[other_id] = -1

    def _update_level(self):
        '''
        Hierarchy level of records in update list
        '''
        # While there are records to update
        while len(self._update_list) > 0:
            # Take the first record
            rec_id = self._update_list.pop(0)
            # Check if record is already deleted
            if rec_id not in self._ancestors_dict:
                continue
            # Check if record has no ancestors
            if len(self._ancestors_dict[rec_id]) == 0:
                self._level_dict[rec_id] = 0
                self._best_set.add(rec_id)
            else:
                # Ancestor level
                anc_level = -1
                # Search for the maximum ancestor level
                for anc_id in self._ancestors_dict[rec_id]:
                    # If some ancestor level is -1
                    # then the record cannot be updated
                    if self._level_dict[anc_id] == -1:
                        anc_level = -1
                        break
                    else:
                        anc_level = max([anc_level,
                                         self._level_dict[anc_id]])
                # If all ancestor has updated levels then update record
                if anc_level != -1:
                    self._level_dict[rec_id] = anc_level + 1
                else:
                    # Put record to be processed again
                    self._update_list.append(rec_id)

    def update(self, delete_list, insert_list):
        Hierarchy.update(self, delete_list, insert_list)
        self._update_level()

    def get_topk(self, topk):
        '''
        Return the top-k records with lowest level
        '''
        result_list = []
        # List of (level, id, count) to sort
        sort_list = [(self._level_dict[rec_id], rec_id,
                      self._count_dict[rec_id])
                     for rec_id in self._level_dict]
        # Sort list according to level
        sort_list.sort()
        for item in sort_list:
            tup = self._id_dict[item[1]]
            rec = dict(tup)
            count = item[2]
            result_list += [rec] * count
            if len(result_list) >= topk:
                break
        return result_list[:topk]

    def debug(self):
        '''
        Debug UpdateData
        '''
        if LOG.isEnabledFor(logging.DEBUG):
            str_dbg = '\nTuples:'
            for tup_id, tup in self._id_dict.iteritems():
                str_dbg += "\nt" + str(tup_id + 1) + " = " + str(dict(tup))
            str_dbg += '\n\nBest:' + str(self._best_set)
            str_dbg += '\n\nAncestors:'
            for tup_id, anc_list in self._ancestors_dict.iteritems():
                str_dbg += "\nAnc(" + str(tup_id) + ") = " + str(anc_list)
            str_dbg += '\n\nLevels:\n'
            for tup_id, level in self._level_dict.iteritems():
                str_dbg += "\nLevel(" + str(tup_id) + ") = " + str(level)
            LOG.debug("UpdateData:" + str_dbg)


class HierarchyPartition(Hierarchy):
    '''
    Class to use partition method incrementally
    '''
    def __init__(self, cptheory, initial_list=None):
        Hierarchy.__init__(self, cptheory)
        # Partitions dominated count
        self._pdom_count = {}
        # Partitions count
        self._pref_count_dict = {}
        self._notpref_set_dict = {}
        # Comparison list
        self._comparison_list = cptheory.get_comparison_list()
        # Add records of initial record list
        if initial_list is not None:
            self._add_list(initial_list)

    def _add(self, record):
        rec_id = Hierarchy._add(self, record)
        if self._count_dict[rec_id] == 1:  # IGNORE:too-many-nested-blocks
            remove_best_set = set()
            dominated = False
            # For each comparison
            for comp_id, comp in enumerate(self._comparison_list):
                # Get partition id
                pid = get_partition_id(record, comp_id, comp)
                # Check if record is preferred
                if comp.is_best_record(record):
                    # Put record into preferred partition
                    inc_count_dict(self._pref_count_dict, pid)
                    if self._pref_count_dict[pid] == 1:
                        # Increase ancestor count for dominated records
                        if pid in self._notpref_set_dict:
                            for other_id in self._notpref_set_dict[pid]:
                                inc_count_dict(self._pdom_count, other_id)
                                remove_best_set.add(other_id)
                # Check if record is non preferred
                elif comp.is_worst_record(record):
                    # Put record into non preferred partition
                    add_to_set_id(self._notpref_set_dict, pid, rec_id)
                    if pid in self._pref_count_dict:
                        inc_count_dict(self._pdom_count, rec_id)
                        dominated = True
            self._best_set = self._best_set.difference(remove_best_set)
            if not dominated:
                self._best_set.add(rec_id)

    def _delete(self, record):
        del_id = Hierarchy._delete(self, record)
        if del_id not in self._count_dict:  # IGNORE:too-many-nested-blocks
            for comp_id, comp in enumerate(self._comparison_list):
                pid = get_partition_id(record, comp_id, comp)
                if comp.is_best_record(record):
                    dec_count_dict(self._pref_count_dict, pid)
                    # Decrease ancestor count for dominated records
                    if pid in self._notpref_set_dict:
                        for other_id in self._notpref_set_dict[pid]:
                            dec_count_dict(self._pdom_count, other_id)
                            if other_id not in self._pdom_count:
                                self._best_set.add(other_id)
                elif comp.is_worst_record(record):
                    delete_from_set_id(self._notpref_set_dict, pid, del_id)

    def _best_records(self, id_dict, pref_dict):
        '''
        Return a list with best tuples in tuple dictionary
        Those tuples are removed from tuple dictionary
        The partitions dictionaries are updated
        '''
        result_list = []
        remove_list = []
        # For all tuples
        for tup_id, tup in id_dict.iteritems():
            # Get correspondent record
            rec = dict(tup)
            # Suppose record is not dominated
            dominated = False
            # Check if record is dominated
            for comp_id, comp in enumerate(self._comparison_list):
                # Get partition id
                pid = get_partition_id(rec, comp_id, comp)
                # A record is dominated if it is non preferred by some
                # comparison and this comparison has some preferred record
                if comp.is_worst_record(rec) and \
                        pid in pref_dict:
                    dominated = True
                    break
            if not dominated:
                # If record is not dominated it is in result
                result_list += [rec] * self._count_dict[tup_id]
                remove_list.append(tup_id)
        self._remove_id_list(id_dict, pref_dict, remove_list)
        return result_list

    def _remove_id_list(self, id_dict, pref_dict, toremove_list):
        '''
        Remove best records from ID dictionary and partition dictionary
        '''
        for tup_id in toremove_list:
            tup = id_dict[tup_id]
            rec = dict(tup)
            for comp_id, comp in enumerate(self._comparison_list):
                # Get partition id
                pid = get_partition_id(rec, comp_id, comp)
                if comp.is_best_record(rec):
                    # Decrease count for preferred partition
                    dec_count_dict(pref_dict, pid)
            del id_dict[tup_id]

    def get_topk(self, topk):
        id_dict = self._id_dict.copy()
        pref_dict = self._pref_count_dict.copy()
        rec_list = []
        for tup_id in self._best_set:
            tup = self._id_dict[tup_id]
            rec = dict(tup)
            rec_list += [rec] * self._count_dict[tup_id]
        self._remove_id_list(id_dict, pref_dict, self._best_set)
        while len(rec_list) < topk and len(id_dict) > 0:
            new_list = self._best_records(id_dict, pref_dict)
            rec_list += new_list
        return rec_list[:topk]

    def debug(self):
        '''
        Debug UpdateData
        '''
        if LOG.isEnabledFor(logging.DEBUG):
            str_dbg = '\nTuples:'
            for tup_id, tup in self._id_dict.iteritems():
                str_dbg += "\nt" + str(tup_id + 1) + " = " + str(dict(tup))
            str_dbg += '\n\nComparisons:'
            for index, comp in enumerate(self._comparison_list):
                str_dbg += "\ncomp" + str(index + 1) + " = " + str(comp)
            str_dbg += '\n\nPref Counters:\n'
            str_list = []
            for pid, count in self._pref_count_dict.iteritems():
                str_list.append(str(pid) + " = " + str(count))
            str_list.sort()
            str_dbg += '\n'.join(str_list)
            str_dbg += '\n\nNotPref Sets:\n'
            str_list = []
            for pid, tup_set in self._notpref_set_dict.iteritems():
                str_list.append(str(pid) + " = " +
                                str(['t' + str(t+1) for t in tup_set]))
            str_list.sort()
            str_dbg += '\n'.join(str_list)
            str_dbg += '\n\nPDomCount:'
            for tup_id, count in self._pdom_count.iteritems():
                if tup_id in self._id_dict:
                    str_dbg += '\nt' + str(tup_id+1) + " = " + str(count)
            str_dbg += '\n\nBest set: ' + \
                str(['t' + str(t+1) for t in self._best_set])
            LOG.debug("UpdateData:" + str_dbg)


class HierarchyGraph(Hierarchy):
    '''
    Class to use graph method
    '''
    def __init__(self, cptheory, initial_list=None):
        Hierarchy.__init__(self, cptheory)
        # Dictionary of successors nodes
        self._successors_dict = {}
        # Dictionary of ancestors nodes
        self._ancestors_dict = {}
        if initial_list is not None:
            self._add_list(initial_list)

    def _add_edge(self, from_id, to_id):
        '''
        Add an edge "from_id" to "to_id"
        '''
        # Hierarchy ancestors dictionary
        if to_id not in self._ancestors_dict:
            self._ancestors_dict[to_id] = [from_id]
        else:
            self._ancestors_dict[to_id].append(from_id)
        # Hierarchy successors dictionary
        if from_id not in self._successors_dict:
            self._successors_dict[from_id] = [to_id]
        else:
            self._successors_dict[from_id].append(to_id)

    def _add(self, record):
        new_id = Hierarchy._add(self, record)
        # Check if it is a "new" record
        if self._count_dict[new_id] == 1:
            dominated = False
            # Compare to all other id
            for other_id, tup in self._id_dict.iteritems():
                other_rec = dict(tup)
                if self._cptheory.dominates(record, other_rec):
                    self._add_edge(new_id, other_id)
                    if other_id in self._best_set:
                        self._best_set.remove(other_id)
                elif self._cptheory.dominates(other_rec, record):
                    dominated = True
                    self._add_edge(other_id, new_id)
            if not dominated:
                self._best_set.add(new_id)

    def _clean(self, del_id):
        Hierarchy._clean(self, del_id)
        # Remove from previous dictionary
        if del_id in self._ancestors_dict:
            id_list = self._ancestors_dict.pop(del_id)
            # Remove input edges
            for other_id in id_list:
                self._successors_dict[other_id].remove(del_id)
        # Remove from next dictionary
        if del_id in self._successors_dict:
            id_list = self._successors_dict.pop(del_id)
            # Remove output edges
            for other_id in id_list:
                self._ancestors_dict[other_id].remove(del_id)
                # Check if other id has no more input edges
                if len(self._ancestors_dict[other_id]) == 0:
                    # If yes, put it in root set
                    self._best_set.add(other_id)

    def get_topk(self, topk):
        result_list = []
        # List of current nodes (starting with root nodes of best set)
        current_list = list(self._best_set)
        # Copy ancestors dictionary
        anc_dict = {}
        for rec_id in self._ancestors_dict:
            anc_dict[rec_id] = self._ancestors_dict[rec_id][:]
        # While top-k is not reached and there are id to be processed
        id_count = 0
        while len(result_list) < topk and \
                id_count < len(self._id_dict):
            next_list = []
            # For each current node
            for rec_id in current_list:
                id_count += 1
                # Put record in result list
                rec = dict(self._id_dict[rec_id])
                result_list += [rec] * self._count_dict[rec_id]
                # For each node from "rec_id"
                if rec_id in self._successors_dict:
                    for next_id in self._successors_dict[rec_id]:
                        # Remove entry (rec_id) -> (next_id)
                        anc_dict[next_id].remove(rec_id)
                        # If next_id has no more parents
                        if len(anc_dict[next_id]) == 0:
                            # Put id for next iteration
                            next_list.append(next_id)
            current_list = next_list
        return result_list[:topk]

    def debug(self):
        '''
        Debug UpdateData
        '''
        if LOG.isEnabledFor(logging.DEBUG):
            str_dbg = '\nTuples:'
            for tup_id, tup in self._id_dict.iteritems():
                str_dbg += "\nt" + str(tup_id + 1) + \
                    '[' + str(self._count_dict[tup_id]) + ']' + \
                    " = " + str(dict(tup))
            str_dbg += '\n\nBest:' + str(self._best_set)
            str_dbg += '\n\nAncestors:'
            for tup_id, anc_list in self._ancestors_dict.iteritems():
                str_dbg += "\nAnc(" + str(tup_id) + ") = " + str(anc_list)
            str_dbg += '\n\nSuccessors:\n'
            for tup_id, suc_list in self._successors_dict.iteritems():
                str_dbg += "\nSucc(" + str(tup_id) + ") = " + str(suc_list)
            LOG.debug("UpdateData:" + str_dbg)


def get_partition_id(record, comparison_id, comparison):
    '''
    Get partition id (tuple) for a record based on a comparison
    '''
    # Get record attributes
    att_list = record.keys()
    att_set = set(att_list)
    # Get partition id
    # (record attributes not present in the comparison)
    att_set = att_set.difference(comparison.get_indifferent_set())
    rec_proj = record_projection(record, att_set)
    tup_id = tuple(rec_proj.items())
    return (comparison_id+1, tup_id)


def add_to_set_id(set_dict, set_id, element):
    '''
    Add an item to a partition
    '''
    if set_id in set_dict:
        set_dict[set_id].add(element)
    else:
        set_dict[set_id] = set([element])


def delete_from_set_id(set_dict, sed_id, element):
    '''
    Delete an item from a partition
    '''
    set_dict[sed_id].remove(element)
    if len(set_dict[sed_id]) == 0:
        del set_dict[sed_id]


def inc_count_dict(count_dict, count_id, count=1):
    '''
    Increment a counter dictionary
    '''
    if count_id in count_dict:
        count_dict[count_id] += count
    else:
        count_dict[count_id] = count


def dec_count_dict(count_dict, count_id, count=1):
    '''
    Decrement a counter dictionary
    '''
    if count_id in count_dict:
        count_dict[count_id] -= count
        if count_dict[count_id] <= 0:
            del count_dict[count_id]


def get_count_dict(count_dict, count_id):
    '''
    Return the counter for a count id
    if id does not exists return 0
    '''
    if count_id in count_dict:
        return count_dict[count_id]
    else:
        return 0
