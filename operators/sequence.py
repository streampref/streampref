# -*- coding: utf-8 -*-
'''
Module with operators
'''

from abc import abstractmethod
import logging

from grammar.symbols import POS_SYM, INTEGER_SYM, STREAM_SYM
from control.attribute import Attribute
from control.config import SUBSEQ_ALG_NAIVE, \
    SUBSEQ_ALG_INCREMENTAL
from control.sequence import Sequence
from operators.basic import UnaryOp, record_projection
from operators.window import get_start_end


LOG = logging.getLogger(__name__)


class GenericSeqOp(UnaryOp):
    '''
    Generic sequence operator
    '''
    def __init__(self, operand):
        UnaryOp.__init__(self, operand)
        self._sequence_list = []

    def _update_record_list(self):
        '''
        Update record list according to sequence dictionary
        '''
        self._current_list = []
        # For each sequence in the list
        for seq in self._sequence_list:
            # Get sequence records
            self._current_list += seq.get_record_list()

    def get_sequence_list(self):
        '''
        Get a list of sequences
        '''
        return self._sequence_list

    def debug_run(self):
        '''
        Debug operator run
        '''
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('%s executed at timestamp %s',
                      self._operator_str, self._timestamp)
            str_list = [str(item) for item in self.get_sequence_list()]
            LOG.debug('Current List (' + str(len(str_list)) + '):\n' +
                      '\n'.join(str_list))

    @abstractmethod
    def run(self, timestamp):
        '''
        Must be override
        '''
        raise NotImplementedError('Run method not implemented')


class SeqOp(GenericSeqOp):  # IGNORE:too-many-instance-attributes
    '''
    Sequence operator

    The sequence operator builds sequences with a maximum size based in a
    identifier, if there are simultaneous records with same identifier
    the identified sequence is copied, one copy for each record
    '''
    def __init__(self, operand, identifier_list, range_slide):
        GenericSeqOp.__init__(self, operand)
        # Copy operand attribute list because it will be changed
        self._attribute_list = operand.get_attribute_list()[:]
        # Bound and slide to build sequences
        self._bound, self._slide = range_slide
        # Identifier attributes
        self._identifier_attribute_list = []
        for parsed_att in identifier_list:
            att = self.find_attribute(parsed_att.get_name(),
                                      parsed_att.get_table())
            self._identifier_attribute_list.append(att)
        # record attributes are the attributes not present in
        # identifier attributes
        self._record_attribute_list = []
        for att in self._attribute_list:
            if att not in self._identifier_attribute_list:
                self._record_attribute_list.append(att)
        # Position attribute (always the last attribute)
        att = Attribute(POS_SYM, INTEGER_SYM)
        self._attribute_list.insert(0, att)
        self._operator_name = 'SEQ'
        self._operator_str = 'SEQ[{ran},{sli}]'\
            .format(ran=self._bound, sli=self._slide)
        # Sequences dictionary, each key has a list of sequences
        self._sequence_dict = {}

    def _group_records(self, record_list):
        '''
        Group records of record list in a dictionary, the keys are values of
        identifier attributes and each entry is a list of records
        with record attributes
        '''
        result_dict = {}
        # For every record of the record list
        for rec in record_list:
            # Get record id
            rec_id = record_projection(rec, self._identifier_attribute_list)
            # Convert record id to tuple
            tup_id = tuple(rec_id.items())
            # Get new record without identifier attributes
            new_rec = record_projection(rec, self._record_attribute_list)
            # Add map tuple id -> new record
            result_dict[tup_id] = new_rec
        return result_dict

    def _add_records_to_sequences(self, record_list, timestamp, start, end):
        '''
        Add record to last position of correspondent sequence
        '''
        # Group records by identifier attributes
        group_rec_dict = self._group_records(record_list)
        # Put records into correspondent sequences
        # For every key
        for rec_key in group_rec_dict:
            # Get record for this key
            record = group_rec_dict[rec_key]
            # Append into existent sequence
            if rec_key in self._sequence_dict:
                seq = self._sequence_dict[rec_key]
                seq.append_position(record, timestamp, start, end)
            else:
                # Create a new sequence for each record
                rec_id = dict(rec_key)
                seq = Sequence(rec_id)
                seq.append_position(record, timestamp, start, end)
                self._sequence_dict[rec_key] = seq

    def is_consistent(self):
        if not UnaryOp.is_consistent(self):
            return False
        if self._operand.get_result_type() != STREAM_SYM \
                or None in self._identifier_attribute_list:
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    def _delete_expired_positions(self, timestamp):
        '''
        Delete expired positions of all sequences
        position with timestamp less than start
        '''
        # List of sequences identifiers to delete (empty sequences)
        delete_list = []
        # For all sequences
        for seq_id in self._sequence_dict:
            seq = self._sequence_dict[seq_id]
            # Remove expired positions from sequence
            seq.delete_expired_positions(timestamp)
            # Check if sequence is empty
            if len(seq) == 0:
                # Put in deletion list
                delete_list.append(seq_id)
        # Delete entries with empty list
        for seq_id in delete_list:
            del self._sequence_dict[seq_id]

    def _update_sequence_list(self, timestamp):
        '''
        Update record lists
        '''
        # Check if temporal range is UNBOUNDED (size = -1)
        if self._bound == -1:
            # For UNBOUNDED, just add records (
            rec_list = self._operand.get_inserted_list()
            self._add_records_to_sequences(rec_list, timestamp, -1, -1)
        else:
            self._delete_expired_positions(timestamp)
            # Get start and end valid timestamps
            start, end = get_start_end(timestamp, self._bound, self._slide)
            if start <= timestamp <= end:
                rec_list = self._operand.get_inserted_list()
                self._add_records_to_sequences(rec_list, timestamp, start, end)
        self._sequence_list = self._sequence_dict.values()

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._update_sequence_list(timestamp)
            self._update_record_list()
            self.debug_run()
            self.run_father(timestamp)


class ConseqOp(GenericSeqOp):
    '''
    Temporal preference operator
    '''
    def __init__(self, operand, subseq_alg):
        GenericSeqOp.__init__(self, operand)
        # Subsequence algorithm
        self._subseq_alg = subseq_alg
        # List of sequences
        self._sequence_list = []
        # Operator string name
        self._operator_name = 'CONSEQ'
        self._operator_str = 'CONSEQ'
        # Subsequence dictionary
        self._subsequence_dict = {}

    def is_consistent(self):
        # Must be over another sequence operator
        if not UnaryOp.is_consistent(self):
            return False
        if not isinstance(self._operand, GenericSeqOp):
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    def _get_subsequences_scratch(self):
        '''
        Get subsequences with consecutive timestamps from scratch
        '''
        # Get list of input sequences
        seq_list = self._operand.get_sequence_list()
        # Create the list of ct-subsequences
        subseq_list = []
        # For every input sequence
        for seq in seq_list:
            # Get ct-subsequences for current sequence
            subseq_list += seq.get_ctsubsequences()
        return subseq_list

    def _update_subsequences(self):
        '''
        Update incrementally subsequences with consecutive timestamps
        '''
        result_list = []
        # New subsequence dictionary
        new_subseq_dict = {}
        # Get list of input sequences
        seq_list = self._operand.get_sequence_list()
        # For every sequence
        for seq in seq_list:
            # Get sequence id
            seq_id = id(seq)
            # Check if seq id is not in the subsequences dict
            if seq_id not in self._subsequence_dict:
                # Build ct-subsequences
                subseq_list = seq.get_ctsubsequences()
                # Restart seq counters
                seq.restart_inserted()
                seq.restart_deleted()
            # Else (seq is already in the subsequence dict)
            else:
                # Get curret subsequence list
                subseq_list = self._subsequence_dict.pop(seq_id)
                # Update subsequence list
                _delete_conseq(subseq_list, seq)
                _insert_conseq(subseq_list, seq)
            # Add entry of seq id to subsequence list
            new_subseq_dict[seq_id] = subseq_list
            # Add ct-subsequences of seq into result list
            result_list += subseq_list
        # Update subsequence dictionary
        self._subsequence_dict = new_subseq_dict
        return result_list

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._current_list = []
            if self._subseq_alg == SUBSEQ_ALG_NAIVE:
                self._sequence_list = self._get_subsequences_scratch()
            elif self._subseq_alg == SUBSEQ_ALG_INCREMENTAL:
                self._sequence_list = self._update_subsequences()
            else:
                raise NotImplementedError('Algorithm not implemented: {m}'.
                                          format(m=self._subseq_alg))
            self._update_record_list()
            self.debug_run()
            self.run_father(timestamp)


class EndseqOp(GenericSeqOp):
    '''
    Temporal preference operator
    '''
    def __init__(self, operand, subseq_alg):
        GenericSeqOp.__init__(self, operand)
        # Subsequence algorithm
        self._subseq_alg = subseq_alg
        # List of sequences
        self._sequence_list = []
        # Operator string name
        self._operator_name = 'ENDSEQ'
        self._operator_str = 'ENDSEQ'
        # Subsequence dictionary
        self._subsequence_dict = {}

    def is_consistent(self):
        # Must be over another sequence operator
        if not UnaryOp.is_consistent(self):
            return False
        if not isinstance(self._operand, GenericSeqOp):
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    def _get_subsequences_scratch(self):
        '''
        Get subsequences with end position from scratch
        '''
        seq_list = self._operand.get_sequence_list()
        subseq_list = []
        for seq in seq_list:
            subseq_list += seq.get_ep_subsequences()
        return subseq_list

    def _update_subsequences(self):
        '''
        Update incrementally subsequences with end positions
        '''
        result_list = []
        # New subsequence dictionary
        new_subseq_dict = {}
        seq_list = self._operand.get_sequence_list()
        # For every input seq at current instant
        for seq in seq_list:
            # Get sequence id
            seq_id = id(seq)
            # Check if seq id is no in the subsequences dict
            if seq_id not in self._subsequence_dict:
                # Build subsequences for seq
                subseq_list = seq.get_ep_subsequences()
                # Restart seq counters
                seq.restart_inserted()
                seq.restart_deleted()
            # Else (seq is already in the subsequence dict)
            else:
                # Get current subsequence list
                subseq_list = self._subsequence_dict.pop(seq_id)
                # Get the number of deletions and insertions
                deleted = seq.restart_deleted()
                inserted = seq.restart_inserted()
                # Update subsequence list
                _delete_endseq(subseq_list, seq, deleted, inserted)
                _insert_endseq(subseq_list, seq, inserted)
            # Add entry of seq id to subsequence list
            new_subseq_dict[seq_id] = subseq_list
            # Add ep-subsequences of seq into result list
            result_list += subseq_list
        # Update subsequence dictionary
        self._subsequence_dict = new_subseq_dict
        return result_list

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._current_list = []
            if self._subseq_alg == SUBSEQ_ALG_NAIVE:
                self._sequence_list = self._get_subsequences_scratch()
            elif self._subseq_alg == SUBSEQ_ALG_INCREMENTAL:
                self._sequence_list = self._update_subsequences()
            else:
                raise NotImplementedError('Algorithm not implemented: {m}'.
                                          format(m=self._subseq_alg))
            self._update_record_list()
            self.debug_run()
            self.run_father(timestamp)


class MaxseqOp(GenericSeqOp):
    '''
    Operator for sequence filtering by maximum length
    '''
    def __init__(self, operand, max_length):
        GenericSeqOp.__init__(self, operand)
        # Maximum length
        self._max_length = max_length
        # List of sequences
        self._sequence_list = []
        # Operator string name
        self._operator_name = 'MAXSEQ'
        self._operator_str = 'MAXSEQ[' + str(max_length) + ']'
        # Subsequence dictionary
        self._subsequence_dict = {}

    def is_consistent(self):
        # Must be over another sequence operator
        if not UnaryOp.is_consistent(self):
            return False
        if not isinstance(self._operand, GenericSeqOp):
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._sequence_list = []
            for seq in self._operand.get_sequence_list():
                if len(seq) <= self._max_length:
                    self._sequence_list.append(seq)
            self._update_record_list()
            self.debug_run()
            self.run_father(timestamp)


class MinseqOp(GenericSeqOp):
    '''
    Operator for sequence filtering by maximum length
    '''
    def __init__(self, operand, min_length):
        GenericSeqOp.__init__(self, operand)
        # Maximum length
        self._min_length = min_length
        # List of sequences
        self._sequence_list = []
        # Operator string name
        self._operator_name = 'MINSEQ'
        self._operator_str = 'MINSEQ[' + str(min_length) + ']'
        # Subsequence dictionary
        self._subsequence_dict = {}

    def is_consistent(self):
        # Must be over another sequence operator
        if not UnaryOp.is_consistent(self):
            return False
        if not isinstance(self._operand, GenericSeqOp):
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._sequence_list = []
            for seq in self._operand.get_sequence_list():
                if len(seq) >= self._min_length:
                    self._sequence_list.append(seq)
            self._update_record_list()
            self.debug_run()
            self.run_father(timestamp)


def _delete_conseq(subsequence_list, sequence):
    '''
    Delete invalid ct-subsequences in subsequence list according to deleted
    positions of sequence
    '''
    # Count for deleted positions
    count = 0
    deleted = sequence.restart_deleted()
    # While count be less than deletions
    while count < deleted:
        # Remove first subsequence of the list
        subseq = subsequence_list.pop(0)
        # Count number of positions of this subsequence
        count += len(subseq)
    # If count of deleted positions is greater than deleted positions
    if count > deleted:
        # Number of positions to be deleted in subsequence
        count = deleted - (count - len(subseq))
        subseq.delete_first(count)
        # Put subsequence back in the list
        subsequence_list.insert(0, subseq)


def _insert_conseq(subsequence_list, sequence):
    '''
    Append inserted positions of the sequence into list of subsequences
    '''
    # Get number of inserted positions
    inserted = sequence.restart_inserted()
    # Check if there was insertions
    if inserted > 0:
        # Get positions inserted as a subsequence
        start = len(sequence) - inserted
        inserted_subseq = sequence.subsequence(start, len(sequence))
        # Build a list of ct-subsequences over inserted positions
        new_list = inserted_subseq.get_ctsubsequences()
        # Get the last subsequence of current list
        last_subseq = subsequence_list.pop()
        # Get the first subsequence of new list
        new_subseq = new_list.pop(0)
        # Get first timestamp of new first subsequence in new list
        new_timestamp = new_subseq.get_timestamp_list()[0]
        # Get last timestamp of last subsequence in current list
        last_timestamp = last_subseq.get_timestamp_list()[-1]
        # Check if these timestamps are consecutive
        if new_timestamp == last_timestamp + 1:
            # If yes, concatenate these subsequences
            last_subseq.append_sequence(new_subseq)
        else:
            # Else, put back new subsequence at the beginning of new list
            new_list.insert(0, new_subseq)
        # Put back last subsequence of current list
        subsequence_list.append(last_subseq)
        # Concatenate lists of subsequences
        subsequence_list += new_list


def _delete_endseq(subsequence_list, sequence, deleted, inserted):
    '''
    Delete invalid ep-subsequences in subsequence list according to deleted
    positions of sequence

    The subsequence list must be decreasingly sorted by sequence length
    '''
    # Check if there were deletions
    if deleted > 0:
        # Calculate maximum size valid for subsequences
        max_length = len(sequence) - inserted
        while True:
            # subsequence list is not empty
            if len(subsequence_list) == 0:
                break
            # Remove invalid subsequences
            subseq = subsequence_list.pop(0)
            if len(subseq) <= max_length:
                subsequence_list.insert(0, subseq)
                break


def _insert_endseq(subsequence_list, sequence, inserted):
    '''
    Append inserted positions of the sequence into list of subsequences
    and create new ones
    '''
    # Check if there were insertions
    if inserted > 0:
        # Calculate first inserted position
        start = len(sequence) - inserted
        # Get a subsequence with inserted positions
        new_seq = sequence.subsequence(start, len(sequence))
        # Append these positions to existing subsequences
        for subseq in subsequence_list:
            subseq.append_sequence(new_seq)
        # Get subsequences from inserted positions
        subsequence_list += new_seq.get_ep_subsequences()
