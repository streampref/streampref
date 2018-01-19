# -*- coding: utf-8 -*-
'''
Module with operators
'''

import logging

from grammar.symbols import TABLE_SYM, STREAM_SYM
from operators.basic import UnaryOp


LOG = logging.getLogger(__name__)


class WindowOp(UnaryOp):  # IGNORE:too-many-instance-attributes
    '''
    Window operator
    '''
    def __init__(self, operand, bound, slide=1):
        UnaryOp.__init__(self, operand)
        # Window bound and slide
        self._bound = bound
        self._slide = slide
        self._operator_name = 'WIN'
        self._operator_str = \
            'WIN[{b},{s}]'.format(b=self._bound, s=self._slide)
        # List of records for each timestamp
        self._history_dict = {}
        # Valid intervals (start and end) for each timestamp
        self._start_end_dict = {}
        # Deleted records in current instant
        self._deleted_list = []
        # Inserted records in current instant
        self._inserted_list = []
        self._result_type = TABLE_SYM

    def is_consistent(self):
        if not UnaryOp.is_consistent(self):
            return False
        if self._operand.get_result_type() != STREAM_SYM:
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    def _update_record_list(self, timestamp):
        '''
        Update record lists
        '''
        self._deleted_list = []
        self._inserted_list = []
        # Check if it is a UNBOUNDED window (size = -1)
        if self._bound == -1:
            self._current_list = self._previous_list + \
                self._operand.get_inserted_list()
            self._inserted_list = self._operand.get_inserted_list()
        else:
            # Get start and end valid timestamps
            # Remove expired records
            expired_list = []
            for old_timestamp in self._start_end_dict:
                start, end = self._start_end_dict[old_timestamp]
                if not start <= timestamp <= end:
                    expired_list.append(old_timestamp)
            for expired_timestamp in expired_list:
                self._deleted_list += self._history_dict[expired_timestamp]
                del self._history_dict[expired_timestamp]
                del self._start_end_dict[expired_timestamp]
            # Get operand records
            start, end = get_start_end(timestamp, self._bound, self._slide)
            if start <= timestamp <= end:
                self._history_dict[timestamp] = \
                    self._operand.get_inserted_list()
                self._start_end_dict[timestamp] = (start, end)
                self._inserted_list = self._operand.get_inserted_list()
            self._current_list = []
            for rec_list in self._history_dict.values():
                self._current_list += rec_list

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._update_record_list(timestamp)
            self.debug_run()
            self.run_father(timestamp)

    def get_deleted_list(self):
        return self._deleted_list

    def get_inserted_list(self):
        return self._inserted_list

    def get_name(self):
        '''
        Return operand name
        '''
        return self._operand.get_name()


def get_start_end(timestamp, bound, slide):
    '''
    Compute start and end timestamps based on current timestamp,
    bound and slide
    '''
    from math import trunc
    start = trunc((timestamp) / slide) * slide
    end = start + bound - 1
    return start, end
