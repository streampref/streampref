# -*- coding: utf-8 -*-
'''
Module with operators
'''

from abc import abstractmethod
import logging

from grammar.symbols import POS_SYM, INTEGER_SYM, STREAM_SYM
from control.attribute import Attribute
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

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._current_list = []
            raise NotImplementedError('Algorithm not implemented: {m}'.
                                      format(m=self._subseq_alg))


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

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._current_list = []
            raise NotImplementedError('Algorithm not implemented: {m}'.
                                      format(m=self._subseq_alg))


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
            raise NotImplementedError('Operator not implemented: {m}'.
                                      format(m=self._operator_name))


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
            raise NotImplementedError('Operator not implemented: {m}'.
                                      format(m=self._operator_name))
