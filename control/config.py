# -*- coding: utf-8 -*-
'''
Module to manage configurations
'''

import logging
from grammar.symbols import COMMA


###############################################################################

# Log configurations
LOG_LEVEL_DEBUG = 'DEBUG'
LOG_LEVEL_INFO = 'INFO'

###############################################################################

# Algorithms for tuples comparison
# Algorithm based on search (not incremental)
TUP_ALG_DEPTH_SEARCH = 'depth_search'
# Algorithm based on partition (not incremental)
TUP_ALG_PARTITION = 'partition'

# Incremental algorithm based on ancestor list
TUP_ALG_INC_ANCESTORS = 'inc_ancestors'
# Incremental algorithm based on graph
TUP_ALG_INC_GRAPH = 'inc_graph'
# Incremental algorithm based on graph (no transitive)
TUP_ALG_INC_GRAPH_NO_TRANSITIVE = 'inc_graph_no_transitive'
# Incremental algorithm based on partition
TUP_ALG_INC_PARTITION = 'inc_partition'

# List of algorithms for tuples
TUP_ALG_LIST = [TUP_ALG_INC_ANCESTORS, TUP_ALG_DEPTH_SEARCH, TUP_ALG_INC_GRAPH,
                TUP_ALG_INC_GRAPH_NO_TRANSITIVE, TUP_ALG_PARTITION,
                TUP_ALG_INC_PARTITION]
# Default algorithm for tuples
TUP_DEFAULT_ALG = TUP_ALG_INC_PARTITION

###############################################################################

# Algorithms for sequences comparison
# Algorithm based on search (not incremental)
SEQ_ALG_DEPTH_SEARCH = 'depth_search'
# Incremental algorithm based on sequences tree
SEQ_ALG_SEQTREE = 'inc_seqtree'
# Incremental algorithm based on sequences tree with pruning
SEQ_ALG_SEQTREE_PRUNING = 'inc_seqtree_pruning'
SEQ_ALG_LIST = [SEQ_ALG_DEPTH_SEARCH, SEQ_ALG_SEQTREE,
                SEQ_ALG_SEQTREE_PRUNING]

# List of algorithms for sequences
# Default algorithm for sequences
SEQ_DEFAULT_ALG = SEQ_ALG_SEQTREE_PRUNING

###############################################################################
# Subsequence algorithm configuration
SUBSEQ_ALG_NAIVE = 'naive'
SUBSEQ_ALG_INCREMENTAL = 'incremental'
SUBSEQ_ALG_LIST = [SUBSEQ_ALG_NAIVE, SUBSEQ_ALG_INCREMENTAL]
DEFAULT_SUBSEQ_ALG = SUBSEQ_ALG_INCREMENTAL

###############################################################################
# Comparisons statistics
COMP_IN = 'in'
COMP_IN_MIN = 'in_min'
COMP_IN_MAX = 'in_max'
COMP_IN_AVG = 'in_avg'
COMP = 'comp'
COMP_OUT = 'out'
COMP_OUT_MIN = 'out_min'
COMP_OUT_MAX = 'out_max'
COMP_OUT_AVG = 'out_avg'
COMP_ATT_LIST = [COMP_IN, COMP_IN_MIN, COMP_IN_MAX, COMP_IN_AVG, COMP,
                 COMP_OUT, COMP_OUT_MIN, COMP_OUT_MAX, COMP_OUT_AVG]

###############################################################################
# Other configuration

# Field separator configuration
DEFAULT_DELIMITER = COMMA

# Iterations number configuration
DEFAULT_MAX_TIMESTAMP = 10

# Default lines number to read from files
DEFAULT_LINES_NUMBER_READ = 100000

# Default log file
DEFAULT_LOG_FILE = 'streampref.log'


class Config(object):
    '''
    Class to represent configurations
    '''
    def __init__(self, args):
        # Environment file
        self._env_filename = args.env
        # Maximum timestamp to run
        self._max_timestamp = args.max
        # Execution details
        self._details_file = args.details
        # File delimiter
        self._delimiter = args.delimiter
        # Preference algorithm
        self._pref_alg = args.pref
        # Temporal preference algorithm
        self._tpref_alg = args.tpref
        # Subsequence algorithm
        self._subseq_alg = args.subseq
        # Output file for operators details
        self._out_operator_file = args.outcomparisons

    def __str__(self):
        return str(self.__dict__)

    def __repr__(self):
        return self.__str__()

    def get_environment_filename(self):
        '''
        Return environment file name
        '''
        return self._env_filename

    def get_maximum_timestamp(self):
        '''
        Return maximum timestamp to run
        '''
        return self._max_timestamp

    def get_details_file(self):
        '''
        Return file to store details executions
        '''
        return self._details_file

    def get_delimiter(self):
        '''
        Return delimiter
        '''
        return self._delimiter

    def get_pref_alg(self):
        '''
        Return preference algorithm
        '''
        return self._pref_alg

    def get_tpref_alg(self):
        '''
        Return temporal preference algorithm
        '''
        return self._tpref_alg

    def get_subseq_alg(self):
        '''
        Return subsequence algorithm
        '''
        return self._subseq_alg

    def get_outoperator_file(self):
        '''
        Return temporal preference algorithm
        '''
        return self._out_operator_file


def config_log(log_filename, debug=True):
    '''
    Configure log
    '''
    logger = logging.getLogger()
    str_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    log_format = logging.Formatter(str_format)
    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(log_format)
    console_hanler = logging.StreamHandler()
    console_hanler.setFormatter(log_format)
    logger.addHandler(file_handler)
    logger.addHandler(console_hanler)
    if debug:
        logger.setLevel(logging.DEBUG)
    else:
        logger.setLevel(logging.INFO)
