# -*- coding: utf-8 -*-
'''
Module to manage queries
'''

import csv
import logging

from grammar.query import QueryGrammar
from grammar.symbols import TS_SYM, FLAG_SYM, PLUS_OP, \
    MINUS_OP
from control.attribute import Attribute
from control.planner import build_plan


LOG = logging.getLogger(__name__)


class Query(object):  # IGNORE:too-many-instance-attributes
    '''
    Class of queries and views
    '''

    def __init__(self, name, input_filename, conf):
        # Store configuration
        self._conf = conf
        # Query name
        self._name = name
        # File of query
        self._input_filename = input_filename
        # File to output query results
        self._output_file = None
        # Show changes (insertions and deletions) instead normal output
        self._show_changes = False
        # Original CQL query string
        self._cql = ''
        # Plan for query execution
        self._plan = None
        # Consumer operators list
        self._consumer_list = []
        # Last timestamp processed
        self._timestamp = -1
        # List of attributes of query result
        self._attribute_list = []
        # Lists of records
        self._current_list = []
        self._inserted_list = []
        self._deleted_list = []
        # Timestamp of lists
        self._current_list_timestamp = -1
        self._inserted_list_timestamp = -1
        self._deleted_list_timestamp = -1

    def __str__(self):
        str_query = 'Source file: ' + self._input_filename + '\n'
        if self._output_file != '':
            str_query += 'Output file: ' + self._output_file + '\n'
        if self._show_changes:
            str_query += 'Show _show_changes' + '\n'
        str_query += 'Query:\n' + self._cql
        return str_query

    def __repr__(self):
        return self.__str__()

    def _build_attributes(self):
        '''
        Build the query attributes list
        '''
        # For each attribute in top plan operator
        for att in self._plan.get_attribute_list():
            # Use just attribute name (without table)
            attr = Attribute(att.get_name(), att.get_data_type())
            self._attribute_list.append(attr)

    def _initilize_file(self):
        '''
        Write the file header
        '''
        if self._output_file is not None:
            # Clear output file
            out_file = open(self._output_file, 'w')
            str_att_list = [att.get_name() for att in self._attribute_list]
            str_att_list.insert(0, TS_SYM)
            if self._show_changes:
                str_att_list.insert(1, FLAG_SYM)
            delimiter = self._conf.get_delimiter()
            header = delimiter.join(str_att_list)
            out_file.write(header + '\n')
            out_file.close()

    def set_output(self, output_file, show_changes=False):
        '''
        Set output configurations for query
        '''
        self._output_file = output_file
        self._show_changes = show_changes

    def is_consistent(self, table_dict):
        '''
        Validate query code
        '''
        # Read query from file
        LOG.debug('Query %s: Reading source file: %s', self._name,
                  self._input_filename)
        query_file = open(self._input_filename)
        self._cql = query_file.read()
        parsed_query = QueryGrammar.parse(self._cql)
        if parsed_query is None:
            return False
        LOG.debug('Query %s: building plan', self._name)
        self._plan = build_plan(parsed_query.query, table_dict,
                                self._conf)
        self._build_attributes()
        LOG.debug('Query %s, plan build: %s', self._name, self._plan)
        LOG.debug('Checking query consistency for query %s', self._name)
        if self._plan.is_consistent():
            LOG.debug('Query %s: consistent', self._name)
            self._initilize_file()
            return True
        else:
            LOG.error('Query %s: not consistent', self._name)
            LOG.error('Query plan %s:\n', self._plan)
            return False

    def get_attribute_list(self):
        '''
        Get the attributes list
        '''
        return self._attribute_list

    def get_result_type(self):
        '''
        Return result type ('STREAM' or 'RELATION')
        '''
        return self._plan.get_result_type()

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

    def get_timestamp(self):
        '''
        Get the timestamp
        '''
        return self._timestamp

    def update_timestamp(self, timestamp):
        '''
        Update query timestamp if top plan operator is ready
        '''
        if self._plan.get_timestamp() == timestamp \
                and self._timestamp < timestamp:
            self._timestamp = timestamp

    def output(self):
        '''
        Store query result in the output file, if this file was informed
        '''
        # Check output file was informed
        # And if there are records to output
        if self._output_file is not None:
            # Open output file in append mode
            out_file = open(self._output_file, 'a')
            csv.register_dialect('table', delimiter=self._conf.get_delimiter(),
                                 skipinitialspace=True)
            att_list = [att.key() for att in self._attribute_list]
            att_list.insert(0, TS_SYM)
            if self._show_changes:
                att_list.insert(0, FLAG_SYM)
                file_writer = csv.DictWriter(out_file, att_list,
                                             dialect='table')
                # Write output with changes (+ and -)
                rec_list = self.get_deleted_list()
                rec_list = self._map_to_output(rec_list, MINUS_OP)
                for rec in rec_list:
                    file_writer.writerow(rec)
                rec_list = self.get_inserted_list()
                rec_list = self._map_to_output(rec_list, PLUS_OP)
                for rec in rec_list:
                    file_writer.writerow(rec)
            else:
                # Write simple output
                file_writer = csv.DictWriter(out_file, att_list,
                                             dialect='table')
                rec_list = self.get_current_list()
                rec_list = self._map_to_output(rec_list, None)
                for rec in rec_list:
                    file_writer.writerow(rec)
            out_file.close()

    def get_inserted_list(self):
        '''
        Get the list of new records
        '''
        if self._inserted_list_timestamp < self._timestamp:
            ins_list = self._plan.get_inserted_list()
            self._inserted_list = self._map_to_query(ins_list)
            self._inserted_list_timestamp = self._timestamp
        return self._inserted_list

    def get_deleted_list(self):
        '''
        Get the list of deleted records
        '''
        if self._deleted_list_timestamp < self._timestamp:
            del_list = self._plan.get_deleted_list()
            self._deleted_list = self._map_to_query(del_list)
            self._deleted_list_timestamp = self._timestamp
        return self._deleted_list

    def get_current_list(self):
        '''
        Get current query record list
        '''
        if self._current_list_timestamp < self._timestamp:
            cur_list = self._plan.get_current_list()
            self._current_list = self._map_to_query(cur_list)
            self._current_list_timestamp = self._timestamp
        return self._current_list

    def _map_to_query(self, record_list):
        '''
        Rename attributes using query attribute names
        '''
        result_list = []
        for rec in record_list:
            new_rec = {}
            for att in self._plan.get_attribute_list():
                query_att = Attribute(att.get_name(), att.get_data_type())
                new_rec[query_att] = rec[att]
            result_list.append(new_rec)
        return result_list

    def _map_to_output(self, record_list, flag=None):
        '''
        Rename attributes using query attribute names
        '''
        result_list = []
        for rec in record_list:
            new_rec = {}
            for att in rec:
                new_rec[att.get_name()] = rec[att]
            new_rec[TS_SYM] = self._timestamp
            if flag is not None:
                new_rec[FLAG_SYM] = flag
            result_list.append(new_rec)
        return result_list
