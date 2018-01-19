# -*- coding: utf-8 -*-
'''
Module to manage tables (streams and relations)
'''

import logging

from grammar.symbols import INTEGER_SYM, FLAG_SYM, FLOAT_SYM, \
    TS_SYM, STREAM_SYM, PLUS_OP, MINUS_OP
from control.attribute import Attribute
from control.config import DEFAULT_LINES_NUMBER_READ


LOG = logging.getLogger(__name__)


class Table(object):  # IGNORE:too-many-instance-attributes
    '''
    Class of tables (streams and relations)
    '''

    def __init__(self, table_type, input_filename, delimiter):
        # Result type: STREAM or TABLE
        self._result_type = table_type
        # Source filename to read records
        self._input_filename = input_filename
        self._attribute_list = []
        # List of consumer operator of table
        self._consumer_list = []
        # Current timestamp
        self._timestamp = -1
        # List of records at current timestamp
        self._current_list = []
        # List of inserted records at current timestamp
        self._inserted_list = []
        # List of deleted records at current timestamp
        self._deleted_list = []
        # File to read records
        self._input_file = None
        # Attribute list of file
        self._file_attributes_list = []
        # Buffer of file
        self._file_lines_buffer = []
        # Field separator on file
        self._delimiter = delimiter

    def __str__(self):
        str_table = self._result_type + '('
        att_list = []
        for att in self._attribute_list:
            att_list.append(str(att) + ': ' + att.get_data_type())
        str_table += ', '.join(att_list) + ')'
        return str_table

    def __repr__(self):
        return self.__str__()

    def __del__(self):
        self._input_file.close()

    def get_attribute_list(self):
        '''
        Get the attribute list
        '''
        return self._attribute_list

    def add_attribute(self, name, data_type):
        '''
        Add new attribute if it does not exist
        '''
        att = Attribute(name, data_type)
        if att not in self._attribute_list:
            self._attribute_list.append(att)
            return True
        else:
            return False

    def get_result_type(self):
        '''
        Return table type ('STREAM' or 'RELATION')
        '''
        return self._result_type

    def add_consumer(self, consumer):
        '''
        Add a consumer
        '''
        self._consumer_list.append(consumer)

    def get_consumers_list(self):
        '''
        Get consumer list
        '''
        return self._consumer_list

    def next_timestamp(self):
        '''
        Set the go to next timestamp
        '''
        self._timestamp += 1
        self._update_record_list()

    def get_timestamp(self):
        '''
        Get the timestamp
        '''
        return self._timestamp

    def _update_record(self, file_record):
        '''
        convert and add a file record to record list
        '''
        # Stream just append the record
        if self._result_type == STREAM_SYM:
            rec = self._convert_record(file_record)
            self._inserted_list.append(rec)
        else:
            flag = file_record[FLAG_SYM]
            rec = self._convert_record(file_record)
            if flag == PLUS_OP:
                self._current_list.append(rec)
                self._inserted_list.append(rec)
            elif flag == MINUS_OP:
                self._remove_record(rec)

    def _remove_record(self, record):
        '''
        Delete a record from records list
        '''
        # Check if deleted record exists
        deleted = False
        for index, rec in enumerate(self._current_list):
            if rec == record:
                self._deleted_list.append(rec)
                del self._current_list[index]
                deleted = True
                break
        if not deleted:
            LOG.error('Invalid deletion: %s', record)

    def _next_file_line(self):
        '''
        Get the next file line
        Returns the file line or 'None' when file ends
        '''
        if len(self._file_lines_buffer):
            line = self._file_lines_buffer.pop(0)
            return line.strip()
        else:
            # Try read more lines from file
            self._file_lines_buffer = \
                self._input_file.readlines(DEFAULT_LINES_NUMBER_READ)
            if len(self._file_lines_buffer):
                line = self._file_lines_buffer.pop(0)
                return line.strip()
            else:
                return None

    def _convert_record(self, file_record):
        '''
        Convert dictionary values according to attributes types
        '''
        new_record = {}
        try:
            # Convert each attribute value to correct type
            for att in self._attribute_list:
                value = file_record[att.get_name()]
                if att.get_data_type() == INTEGER_SYM:
                    value = int(value)
                elif att.get_data_type() == FLOAT_SYM:
                    value = float(value)  # IGNORE:redefined-variable-type
                new_record[att] = value
        except KeyError as kerr:
            LOG.exception('Error on attribute name')
            LOG.exception(kerr)
            return False
        return new_record

    def _update_record_list(self):
        '''
        Update dictionary lists using file data
        '''
        self._inserted_list = []
        self._deleted_list = []
        line = self._next_file_line()
        timestamp = 0
        while line is not None \
                and timestamp <= self._timestamp:
            # Convert line to dictionary
            values_list = line.split(self._delimiter)
            values_list = [value.strip() for value in values_list]
            file_rec = dict(zip(self._file_attributes_list, values_list))
            # Convert timestamp value to integer
            timestamp = int(file_rec[TS_SYM])
            # check dic timestamp is equal to table timestamp
            if timestamp == self._timestamp:
                self._update_record(file_rec)
            # Check if timestamp is greater than table time stamp
            if timestamp > self._timestamp:
                # Put back on lines buffer to use later
                self._file_lines_buffer.insert(0, line)
            else:
                # Go to next line
                line = self._next_file_line()

    def initialize(self):
        '''
        Initialize table
        '''
        LOG.debug('Reading data file: %s', self._input_filename)
        try:
            # Open source file
            self._input_file = open(self._input_filename)
            # Read file reader
            first_line = self._input_file.readline().strip()
            att_list = first_line.split(self._delimiter)
            self._file_attributes_list = [att.strip().upper()
                                          for att in att_list]
            LOG.debug('File attributes %s', self._file_attributes_list)
            # Fill file buffer
            self._file_lines_buffer = self._input_file.readlines(100000)
        except IOError as file_e:
            LOG.exception('Error reading source file')
            LOG.exception(file_e)
            return False
        LOG.debug('Data file read: %s', self._input_filename)
        return True

    def get_current_list(self):
        '''
        Return current list
        '''
        return self._current_list

    def get_inserted_list(self):
        '''
        Return new list
        '''
        return self._inserted_list

    def get_deleted_list(self):
        '''
        Return removed list
        '''
        return self._deleted_list
