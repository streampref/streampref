# -*- coding: utf-8 -*-
'''
Module of system control
'''

import csv
import logging
import os
import time
import psutil

from grammar.environment import EnvironmentGrammar
from grammar.symbols import TABLE_SYM, STREAM_SYM, QUERY_SYM
from control.query import Query
from control.table import Table


# Start logger
LOG = logging.getLogger(__name__)


class Manager(object):
    '''
    Class to manage tables and queries
    '''

    def __init__(self, conf):
        # Dictionary of tables
        self._table_dict = {}
        # Dictionary of queries
        self._query_dict = {}
        # File of environment configuration
        self._env_file = conf.get_environment_filename()
        # Maximum timestamp to run
        self._max_timestamp = conf.get_maximum_timestamp()
        # Store total run time
        self._total_time = 0.0
        # Store configurations
        self._conf = conf
        # Dictionary for execution details
        self._details_list = []

    def initialize(self):
        '''
        Read the environment file
        Register tables and queries
        '''
        # Get initial time
        runtime = time.time()
        # Read configuration file
        LOG.debug('Opening: %s', self._env_file)
        env_file = open(self._env_file)
        env_str = env_file.read()
        env_item_list = EnvironmentGrammar.parse(env_str)
        # Register tables (relations and streams)
        LOG.info('Registering tables')
        if not self._register_tables(env_item_list):
            LOG.error('Tables cannot be registered')
            return False
        LOG.info('Tables registered')
        # Register queries
        LOG.info('Registering queries')
        if not self._register_queries(env_item_list):
            LOG.error('Queries cannot be registered')
            return False
        LOG.info('Queries registered')
        # Get initialization runtime
        runtime = time.time() - runtime
        # Get process information (memory usage)
        process = psutil.Process(os.getpid())
        # Store initialization information
        self._detail(-1, runtime, process, False)
        return True

    def _register_tables(self, env_item_list):
        '''
        Register tables
        Return True if successful or False if some table cannot be registered
        '''
        for item in env_item_list:
            if item.get_type() in [TABLE_SYM, STREAM_SYM]:
                # Check if table already exists
                if item.get_name() in self._table_dict:
                    LOG.error('Duplicated table name: %s',
                              item.get_name())
                    return False
                else:
                    LOG.debug('Registering table: %s %s',
                              item.get_type(),
                              item.get_name())
                    new_table = Table(item.get_type(), item.get_input_file(),
                                      self._conf.get_delimiter())
                    # Try add attributes
                    type_list = item.get_type_list()
                    for index, att in enumerate(item.get_attribute_list()):
                        att_type = type_list[index]
                        if not new_table.add_attribute(att, att_type):
                            return False
                    self._table_dict[item.get_name()] = new_table
                    LOG.debug('Registered table: %s %s',
                              item.get_type(), item.get_name())
                    LOG.debug('Initialing table: %s %s',
                              item.get_type(), item.get_name())
                    if not new_table.initialize():
                        return False
                    LOG.debug('Table initialized: %s %s',
                              item.get_type(), item.get_name())
        return True

    def _register_queries(self, env_item_list):
        '''
        Register queries
        '''
        consistent_queries = True
        for item in env_item_list:
            if item.get_type() == QUERY_SYM:
                if item.get_name() in self._query_dict\
                        or item.get_name() in self._table_dict:
                    LOG.error('Duplicated query name: %s',
                              item.get_name())
                    return False
                else:
                    LOG.debug('Registering query: %s',
                              item.get_name())
                    # Create query
                    new_query = Query(item.get_name(), item.get_input_file(),
                                      self._conf)
                    # Set output options
                    output_file = item.get_output_file()
                    if output_file is not None:
                        new_query.set_output(output_file,
                                             item.is_show_changes())
                    LOG.debug('Validating query: %s',
                              item.get_name())
                    if not new_query.is_consistent(self._table_dict):
                        LOG.error('Invalid query: %s',
                                  item.get_name())
                        consistent_queries = False
                    LOG.debug('Registered query: %s',
                              item.get_name())
                    self._query_dict[item.get_name()] = new_query
                    self._table_dict[item.get_name()] = new_query
        return consistent_queries

    def _sync_tables_timestamp(self, current_ts):
        '''
        Update tables timestamp
        '''
        for table_id in self._table_dict:
            LOG.debug('Synchronizing table %s with timestamp %s',
                      table_id, current_ts)
            table = self._table_dict[table_id]
            if isinstance(table, Table):
                while table.get_timestamp() < current_ts:
                    table.next_timestamp()

    def _run_consumers(self, timestamp):
        '''
        Run tables consumer
        '''
        for table_id in self._table_dict:
            table = self._table_dict[table_id]
            for consumer in table.get_consumers_list():
                consumer.run(timestamp)

    def _get_min_query_timestamp(self):
        '''
        Get minimum query timestamp
        '''
        # Set min_ts to infinity
        min_ts = float('inf')
        for query_id in self._query_dict:
            query = self._query_dict[query_id]
            if query.get_timestamp() < min_ts:
                min_ts = query.get_timestamp()
        return min_ts

    def _output_queries(self):
        '''
        Call output for all queries
        '''
        for query_id in self._query_dict:
            query = self._query_dict[query_id]
            query.output()

    def _sync_queries(self, timestamp):
        '''
        Sync queries timestamp
        '''
        for query_id in self._query_dict:
            query = self._query_dict[query_id]
            query.update_timestamp(timestamp)

    def run(self):
        '''
        Run environment
        '''
        current_ts = 0
        # Run queries while 'max_timestamp' is not reached
        while current_ts <= self._max_timestamp:
            runtime = time.time()
            self._sync_tables_timestamp(current_ts)
            # Run consumer until all queries reach 'current_ts'
            while self._get_min_query_timestamp() < current_ts:
                self._run_consumers(current_ts)
                self._sync_queries(current_ts)
            self._output_queries()
            runtime = time.time() - runtime
            process = psutil.Process(os.getpid())
            if current_ts < self._max_timestamp:
                self._detail(current_ts, runtime, process, False)
            else:
                self._detail(current_ts, runtime, process, True)
            current_ts += 1

    def _detail(self, timestamp, runtime, process, final=False):
        '''
        Log execution details
        '''
        if self._conf.get_details_file() is not None:
            mem = process.memory_info()[0] / 1024.0 / 1024.0
            rec = {'timestamp': timestamp, 'runtime': runtime, 'memory': mem}
            self._details_list.append(rec)
            if final:
                self._details_list.pop()
                filename = self._conf.get_details_file()
                out_file = open(filename, 'w')
                out_write = csv.DictWriter(out_file,
                                           ['timestamp', 'runtime', 'memory'])
                out_write.writeheader()
                for rec in self._details_list:
                    out_write.writerow(rec)
                out_file.close()
