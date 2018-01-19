# -*- coding: utf-8 -*-
'''
Module with operators
'''
import logging

from control.config import TUP_ALG_INC_ANCESTORS, \
    TUP_ALG_DEPTH_SEARCH, TUP_ALG_PARTITION, \
    TUP_ALG_INC_PARTITION, TUP_ALG_INC_GRAPH, TUP_ALG_INC_GRAPH_NO_TRANSITIVE
from operators.basic import UnaryOp, record_projection
from operators.updatedata import HierarchyAncestors, \
    HierarchyPartition, HierarchyGraph


LOG = logging.getLogger(__name__)


class PreferenceOp(UnaryOp):
    '''
    Preference operator
    '''
    def __init__(self, operand, cptheory, pref_alg, topk=-1):
        UnaryOp.__init__(self, operand)
        self._operator_name = 'BEST'
        self._operator_str = 'BEST'
        if topk != -1:
            self._operator_name = 'TOPK'
            self._operator_str = 'TOPK[' + str(topk) + ']'
        # CP-Theory
        self._cptheory = cptheory
        # Top-k (default is -1, the operator returns just dominant records)
        self._top = topk
        # Best algorithm to be used
        self._pref_alg = pref_alg
#         LOG.info(str(self) + ' - Preference algorithm:' + self._pref_alg)
        # Update data (level, ancestor)
        # Used in some algorithms
        self._update_data_level = None

    def is_consistent(self):
        if not UnaryOp.is_consistent(self):
            return False
        if not self._cptheory.is_consistent():
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    def _get_best_partition(self):
        '''
        Get best records according to CPTheory (partition algorithm)
        '''
        # Get record list from operand
        record_list = self._operand.get_current_list()[:]
        if len(record_list):
            for comp in self._cptheory.get_comparison_list():
                record_list = self.best_partition(record_list, comp)[0]
        return record_list

    def _get_topk_partition(self):
        '''
        Returns the top-k records with lowest level according to
        to CPTheory (partition algorithm)
        '''
        # Initial record list
        record_list = self._operand.get_current_list()[:]
        # Topk list to be returned
        topk_list = []
        # While topk is not reached and there are records in record list
        while len(topk_list) < self._top and len(record_list) > 0:
            # List u=of dominated records
            dominated_list = []
            # Get dominant records according to comparison list
            for comp in self._cptheory.get_comparison_list():
                record_list, notpref_list = \
                    self.best_partition(record_list,
                                        comp)
                # Keep dominated records
                dominated_list += notpref_list
            # Put dominant records in top-k list
            topk_list += record_list
            # Put dominated records in record list to process
            record_list = dominated_list
        if len(topk_list) > self._top:
            topk_list = topk_list[:self._top]
        return topk_list

    def _get_best_update(self):
        '''
        Get best records according to CPTheory (update algorithm)
        '''
        self._update_list()
        return self._update_data_level.get_best_records()

    def _get_topk_update(self):
        '''
        Returns the top-k records with lowest level according to
        to CPTheory (update algorithm)
        '''
        self._update_list()
        return self._update_data_level.get_topk(self._top)

    def _update_list(self):
        '''
        Update data level
        '''
        updata = self._update_data_level
        if updata is None:
            # First update
            if self._pref_alg == TUP_ALG_INC_ANCESTORS:
                updata = \
                    HierarchyAncestors(self._cptheory)
            elif self._pref_alg == TUP_ALG_INC_PARTITION:
                updata = \
                    HierarchyPartition(self._cptheory)
            elif self._pref_alg in [TUP_ALG_INC_GRAPH, TUP_ALG_INC_GRAPH_NO_TRANSITIVE]:
                updata = HierarchyGraph(self._cptheory)
            self._update_data_level = updata
        delete_list = self._operand.get_deleted_list()
        insert_list = self._operand.get_inserted_list()
        # Update record levels
        updata.update(delete_list, insert_list)

    def _get_topk_search(self):
        '''
        Returns the top-k records with lowest level according to
        to CPTheory (classical algorithm)
        '''
        dominated_list = self._operand.get_current_list()[:]
        topk_list = []
        self._cptheory.debug_btg(dominated_list)
        while len(topk_list) < self._top and len(dominated_list) > 0:
            dominant_list, dominated_list = \
                self._get_dominant_and_dominated(dominated_list)
            topk_list += dominant_list
        if len(topk_list) > self._top:
            topk_list = topk_list[:self._top]
        return topk_list

    def _get_best_search(self):
        '''
        Get best records according to CPTheory (classical algorithm)

        A record is best if it is not dominated by any other record
        '''
        record_list = self._operand.get_current_list()[:]
        self._cptheory.debug_btg(record_list)
        result, _ = self._get_dominant_and_dominated(record_list)
        return result

    def _get_dominant_and_dominated(self, record_list):
        '''
        Returns two list: dominant list, dominated list
        According to CPTheory (classical algorithm)

        A record is dominant if it is not dominated by any other record
        '''
        # List of worst (dominated) records
        worst_list = []
        # List of best (dominant) records
        best_list = []
        while record_list != []:
            # Get a record
            rec = record_list.pop()
            # List of recors incomparable to current record
            incomparable_list = []
            # Suppose that current record is dominant (not dominated)
            dominated = False
            # While there are record to be compared
            while record_list != []:
                # Get other record
                other_rec = record_list.pop()
                # Check if other record dominates current record
                if self._cptheory.dominates(other_rec, rec):
                    # Mark current record as dominated
                    dominated = True
                    # Add current record into worst list
                    worst_list.append(rec)
                    # Add other record to incomprable list
                    # It must be compared to remaing records
                    incomparable_list.append(other_rec)
                    break
                # Check if record dominates other record
                elif self._cptheory.dominates(rec, other_rec):
                    # Add other record to dominated records
                    worst_list.append(other_rec)
                # Else the records are incomparable
                else:
                    incomparable_list.append(other_rec)
            record_list += incomparable_list
            # If the record was not dominated by any other
            # then it is dominant
            if not dominated:
                best_list.append(rec)
        return best_list, worst_list

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._current_list = []
            if self._top > 0:
                if self._pref_alg == TUP_ALG_DEPTH_SEARCH:
                    self._current_list = self._get_topk_search()
                elif self._pref_alg == TUP_ALG_PARTITION:
                    self._current_list = self._get_topk_partition()
                elif self._pref_alg in [TUP_ALG_INC_ANCESTORS,
                                        TUP_ALG_INC_PARTITION,
                                        TUP_ALG_INC_GRAPH,
                                        TUP_ALG_INC_GRAPH_NO_TRANSITIVE]:
                    self._current_list = self._get_topk_update()
                else:
                    raise NotImplementedError('Method not implemented: {m}'.
                                              format(m=self._pref_alg))
            elif self._top != 0:
                if self._pref_alg == TUP_ALG_DEPTH_SEARCH:
                    self._current_list = self._get_best_search()
                elif self._pref_alg == TUP_ALG_PARTITION:
                    self._current_list = self._get_best_partition()
                elif self._pref_alg in [TUP_ALG_INC_ANCESTORS,
                                        TUP_ALG_INC_PARTITION,
                                        TUP_ALG_INC_GRAPH,
                                        TUP_ALG_INC_GRAPH_NO_TRANSITIVE]:
                    self._current_list = self._get_best_update()
                else:
                    raise NotImplementedError('Method not implemented: {m}'.
                                              format(m=self._pref_alg))
            self.debug_run()
            self.run_father(timestamp)

    def best_partition(self, record_list, comparison):
        '''
        Returns two list: dominant list, dominated list
        according to the comparison
        '''
        dominant_list = []
        dominanted_list = []
        # Get record attributes
        rec_att_set = set(self._attribute_list)
        # Get record attributes not present in the comparison
        att_set = rec_att_set.difference(comparison.get_indifferent_set())
        partition_dict = build_partitions(record_list, att_set)
        LOG.debug("Comparison: " + str(comparison))
        LOG.debug("Partitions: " + str(len(partition_dict)) + "\n" +
                  str(partition_dict))
        # Get dominant records in each partition according to 'comparison'
        for rec_key in partition_dict:
            LOG.debug("Partition: " + str(rec_key) + "\n" +
                      str(len(partition_dict[rec_key])) + "\n" +
                      str(partition_dict[rec_key]))
            pref_list, notpref_list = best_direct(partition_dict[rec_key],
                                                  comparison)
            dominant_list += pref_list
            dominanted_list += notpref_list
        return dominant_list, dominanted_list


def best_direct(record_list, comparison):
    '''
    Returns two list: dominant list, dominated list
    according to the comparison
    '''
    preferred_list = []
    notpreferred_list = []
    incomparable_list = []
    for rec in record_list:
        # Check if record is preferred
        if comparison.is_best_record(rec):
            preferred_list.append(rec)
        # Check if record is non preferred
        elif comparison.is_worst_record(rec):
            notpreferred_list.append(rec)
        # Check if record is incomparable
        else:
            incomparable_list.append(rec)
    LOG.debug("Dominant tuples: " + str(preferred_list))
    LOG.debug("Dominated tuples: " + str(notpreferred_list))
    LOG.debug("Incomparable tuples: " + str(incomparable_list))
    # Check if there no exists preferred records
    if preferred_list == []:
        # All records are dominant and there is no dominated ones
        return record_list, []
    else:
        # Return dominant records (preferred and incomparable) and
        # dominated (non preferred)
        return preferred_list + incomparable_list, notpreferred_list


def build_partitions(record_list, attributes_set):
    '''
    Build a partition set over the record list based on the attribute set

    For each values combination of attributes, a partition is created
    '''
    partition_dict = {}
    # Check if attribute set is empty
    if len(attributes_set) == 0:
        partition_dict[()] = record_list
    else:
        for rec in record_list:
            # Get record rec_key
            rec_key = record_projection(rec, attributes_set)
            tup_key = tuple(rec_key.items())
            # Check if partition already exists
            if tup_key in partition_dict:
                partition_dict[tup_key].append(rec)
            else:
                partition_dict[tup_key] = [rec]
    return partition_dict
