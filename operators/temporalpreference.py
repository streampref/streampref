# -*- coding: utf-8 -*-
'''
Module with operators
'''

import csv
import logging
import sys

from grammar.symbols import TS_SYM
from control.config import SEQ_ALG_DEPTH_SEARCH, SEQ_ALG_SEQTREE, \
    SEQ_ALG_SEQTREE_PRUNING, COMP_IN_MIN, COMP_IN_MAX, \
    COMP_IN_AVG, COMP_OUT_AVG, COMP_OUT_MAX, COMP_OUT_MIN, COMP, \
    COMP_ATT_LIST, COMP_IN, COMP_OUT
from operators.basic import UnaryOp
from operators.seqtreeindex import SeqIndex
from operators.sequence import GenericSeqOp


LOG = logging.getLogger(__name__)
csv.register_dialect('out', delimiter=',', skipinitialspace=True)


class TemporalPreferenceOp(GenericSeqOp):  # IGNORE:too-many-instance-attributes
    '''
    Temporal preference operator
    '''
    def __init__(self, operand, tcptheory, tpref_alg, topk, out_file):  # IGNORE:too-many-arguments
        GenericSeqOp.__init__(self, operand)
        # TCP-Theory
        self._tcptheory = tcptheory
        # Top-k
        self._top = topk
        self._tpref_alg = tpref_alg
        self._operator_name = 'BESTSEQ'
        self._operator_str = 'BESTSEQ'
        self._out_file = out_file
        self._comparisons = 0
        if topk != -1:
            self._operator_name = 'TOPKSEQ'
            self._operator_str = 'TOPKSEQ[' + str(topk) + ']'
        if tpref_alg == SEQ_ALG_DEPTH_SEARCH:
            self._seqindex = None
        elif tpref_alg in [SEQ_ALG_SEQTREE, SEQ_ALG_SEQTREE_PRUNING]:
            self._seqindex = SeqIndex(tcptheory, tpref_alg)

    def is_consistent(self):
        if not UnaryOp.is_consistent(self):
            return False
        if not isinstance(self._operand, GenericSeqOp):
            return False
        if not self._tcptheory.is_consistent():
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    def _get_dominant_dominated(self, sequence_list):
        '''
        Get dominant and dominated sequences according to TCPTheory

        A sequence is dominant if it is not dominated by any other sequence
        '''
        self._comparisons = 0
        dominant_list = []
        dominated_list = []
        while sequence_list != []:
            # Get a sequence
            seq = sequence_list.pop(0)
            not_dominated_list = []
            # Suppose that it not will be dominated
            dominated = False
            while sequence_list != [] and not dominated:
                # Get other sequence
                other_seq = sequence_list.pop(0)
                # Check if sequence dominates other sequence
                if self._tcptheory.dominates_by_search(seq, other_seq):
                    self._comparisons += 1
                    dominated_list.append(other_seq)
                # Check if other sequence dominates sequence
                elif self._tcptheory.dominates_by_search(other_seq, seq):
                    self._comparisons += 1
                    dominated_list.append(seq)
                    not_dominated_list.append(other_seq)
                    dominated = True
                    break
                else:
                    not_dominated_list.append(other_seq)
            # Put not dominated sequences back to sequence list
            sequence_list += not_dominated_list
            # If the sequence was not dominated by any other
            # then it is dominant
            if not dominated:
                dominant_list.append(seq)
        return dominant_list, dominated_list

    def _get_topk_search(self):
        '''
        Returns the top-k sequence (dominance test by search)

        The top-k sequences are those with lowest level according to
        to CPTheory
        '''
        dominated_list = self._operand.get_sequence_list()[:]
        self._tcptheory.debug_btg(dominated_list)
        topk_list = []
        while len(topk_list) < self._top and len(dominated_list) > 0:
            dominant_list, dominated_list = \
                self._get_dominant_dominated(dominated_list)
            topk_list += dominant_list
        return topk_list[:self._top]

    def _get_best_search(self):
        '''
        Get best records according to TCP-Theory (Search based algorithm)
        '''
        seq_list = self._operand.get_sequence_list()[:]
        self._tcptheory.debug_btg(seq_list)
        result, _ = self._get_dominant_dominated(seq_list)
        return result

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._comparisons = 0
            self._sequence_list = []
            if self._top == 0:
                self._sequence_list = []
            elif self._top > 0:
                if self._tpref_alg == SEQ_ALG_DEPTH_SEARCH:
                    self._sequence_list = self._get_topk_search()
                elif self._tpref_alg in [SEQ_ALG_SEQTREE,
                                         SEQ_ALG_SEQTREE_PRUNING]:
                    seq_list = self._operand.get_sequence_list()
                    self._seqindex.update(seq_list)
                    self._sequence_list = \
                        self._seqindex.topk_sequences(self._top)
                else:
                    raise NotImplementedError('Method not implemented: {m}'.
                                              format(m=self._tpref_alg))
            else:
                if self._tpref_alg == SEQ_ALG_DEPTH_SEARCH:
                    self._sequence_list = self._get_best_search()
                elif self._tpref_alg in [SEQ_ALG_SEQTREE,
                                         SEQ_ALG_SEQTREE_PRUNING]:
                    seq_list = self._operand.get_sequence_list()
                    self._seqindex.update(seq_list)
                    self._sequence_list = \
                        self._seqindex.get_best_sequences_recursive()
                else:
                    raise NotImplementedError('Method not implemented: {m}'.
                                              format(m=self._tpref_alg))
            self._current_list = \
                _sequence_list_to_record_list(self._sequence_list)
            self.debug_run()
            if self._out_file is not None:
                self.store_comparisons_stats()
            self.run_father(timestamp)

    def store_comparisons_stats(self):
        '''
        Store comparisons statistics
        '''
        in_seq_list = self._operand.get_sequence_list()
        out_seq_list = self._sequence_list
        rec = {}
        rec[COMP_IN] = len(in_seq_list)
        if len(in_seq_list):
            rec[COMP_IN_MIN], rec[COMP_IN_MAX], \
                rec[COMP_IN_AVG] = get_min_max_avg(in_seq_list)
        else:
            rec[COMP_IN_MIN], rec[COMP_IN_MAX], \
                rec[COMP_IN_AVG] = -1, -1, -1
        if len(out_seq_list):
            rec[COMP_OUT_MIN], rec[COMP_OUT_MAX], \
                rec[COMP_OUT_AVG] = get_min_max_avg(out_seq_list)
        else:
            rec[COMP_OUT_MIN], rec[COMP_OUT_MAX], \
                rec[COMP_OUT_AVG] = -1, -1, -1
        rec[COMP_OUT] = len(out_seq_list)
        rec[COMP] = self._comparisons
        rec[TS_SYM] = self._timestamp
        att_list = [TS_SYM] + COMP_ATT_LIST
        if self._timestamp == 0:
            out_file = open(self._out_file, 'w')
        else:
            out_file = open(self._out_file, 'a')
        out_write = \
            csv.DictWriter(out_file, att_list, dialect='out')
        if self._timestamp == 0:
            out_write.writeheader()
        out_write.writerow(rec)
        out_file.close()


def _sequence_list_to_record_list(sequence_list):
    '''
    Build a list of records using the records of all sequences
    in a sequence list
    '''
    result_list = []
    # For each sequence in the list
    for seq in sequence_list:
        # Get sequence records
        result_list += seq.get_record_list()
    return result_list


def get_min_max_avg(sequence_list):
    '''
    Get min, max and average length for a sequence list
    '''
    max_len = -1
    min_len = sys.maxsize
    sum_len = 0
    for seq in sequence_list:
        min_len = min([min_len, len(seq)])
        max_len = max([max_len, len(seq)])
        sum_len += len(seq)
    avg_len = sum_len / len(sequence_list)
    return (min_len, max_len, avg_len)
