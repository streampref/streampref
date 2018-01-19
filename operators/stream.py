# -*- coding: utf-8 -*-
'''
Module with operators
'''

from abc import abstractmethod
import logging

from grammar.symbols import TABLE_SYM, STREAM_SYM, ISTREAM_SYM, \
    DSTREAM_SYM, RSTREAM_SYM
from operators.basic import UnaryOp


LOG = logging.getLogger(__name__)


class StreamOp(UnaryOp):
    '''
    Stream operators
    '''
    def __init__(self, operand):
        UnaryOp.__init__(self, operand)
        self._result_type = STREAM_SYM

    def is_consistent(self):
        if not UnaryOp.is_consistent(self):
            return False
        if self._operand.get_result_type() != TABLE_SYM:
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    @abstractmethod
    def run(self, timestamp):
        '''
        Must be override
        '''
        raise NotImplementedError('Run method not implemented')

    def get_inserted_list(self):
        return self._current_list

    def get_deleted_list(self):
        return []


class StreamDeleteOp(StreamOp):
    '''
    Delete stream operator
    '''
    def __init__(self, operand):
        StreamOp.__init__(self, operand)
        self._operator_name = DSTREAM_SYM
        self._operator_str = DSTREAM_SYM

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._current_list = self._operand.get_deleted_list()
            self.debug_run()
            self.run_father(timestamp)


class StreamInsertOp(StreamOp):
    '''
    Insert stream operator
    '''
    def __init__(self, operand):
        StreamOp.__init__(self, operand)
        self._operator_name = ISTREAM_SYM
        self._operator_str = ISTREAM_SYM

    def run(self, timestamp):
        if self.can_run(timestamp):
            self.debug_run()
            self._current_list = self._operand.get_inserted_list()
            self.run_father(timestamp)


class StreamRelationOp(StreamOp):
    '''
    Relation stream operator
    '''
    def __init__(self, operand):
        StreamOp.__init__(self, operand)
        self._operator_name = RSTREAM_SYM
        self._operator_str = RSTREAM_SYM

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._current_list = self._operand.get_current_list()
            self.debug_run()
            self.run_father(timestamp)
