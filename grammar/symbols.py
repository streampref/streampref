# -*- coding: utf-8 -*-
'''
Module to define symbols
'''

# Preference keywords
TOP_SYM = 'TOP'
ACCORDING_SYM = 'ACCORDING'
TO_SYM = 'TO'
PREFERENCES_SYM = 'PREFERENCES'
IF_SYM = 'IF'
AND_SYM = 'AND'
THEN_SYM = 'THEN'
BETTER_SYM = 'BETTER'
PREFERENCES_SYM_SET = \
    set([TOP_SYM,
         ACCORDING_SYM,
         TO_SYM,
         PREFERENCES_SYM,
         IF_SYM,
         THEN_SYM,
         BETTER_SYM])

# Temporal preference keywords
TEMPORAL_SYM = 'TEMPORAL'
FIRST_SYM = 'FIRST'
SOME_SYM = 'SOME'
ALL_SYM = 'ALL'
PREVIOUS_SYM = 'PREVIOUS'
TEMPORAL_PREFERENCE_SYM_SET = \
    PREFERENCES_SYM_SET.union(set([TEMPORAL_SYM,
                                  FIRST_SYM,
                                  SOME_SYM,
                                  ALL_SYM,
                                  PREVIOUS_SYM]))

# Time unit keywords
SECOND_SYM = 'SECOND'
MINUTE_SYM = 'MINUTE'
HOUR_SYM = 'HOUR'
DAY_SYM = 'DAY'
TIME_UNIT_SYM_SET = set([SECOND_SYM, MINUTE_SYM, HOUR_SYM, DAY_SYM])

# Sequence keywords
SEQUENCE_SYM = 'SEQUENCE'
SUBSEQUENCE_SYM = 'SUBSEQUENCE'
IDENTIFIED_SYM = 'IDENTIFIED'
BY_SYM = 'BY'
CONSECUTIVE_SYM = 'CONSECUTIVE'
TIMESTAMP_SYM = 'TIMESTAMP'
TUPLES_SYM = 'TUPLES'
END_SYM = 'END'
POSITION_SYM = 'POSITION'
MINIMUM_SYM = 'MINIMUM'
MAXIMUM_SYM = 'MAXIMUM'
LENGTH_SYM = 'LENGTH'
IS_SYM = 'IS'
# ALL_SYM is already defined
SEQUENCE_SYM_SET = set([SEQUENCE_SYM, SUBSEQUENCE_SYM, IDENTIFIED_SYM, BY_SYM,
                       MINIMUM_SYM, MAXIMUM_SYM, LENGTH_SYM, IS_SYM, ALL_SYM]
                       ).union(TIME_UNIT_SYM_SET)

# Stream keywords
DSTREAM_SYM = 'DSTREAM'
ISTREAM_SYM = 'ISTREAM'
RSTREAM_SYM = 'RSTREAM'
STREAM_SYM_SET = set([DSTREAM_SYM, ISTREAM_SYM, RSTREAM_SYM])

# Window keywords
NOW_SYM = 'NOW'
RANGE_SYM = 'RANGE'
UNBOUNDED_SYM = 'UNBOUNDED'
SLIDE_SYM = 'SLIDE'
WINDOW_SYM_SET = set([NOW_SYM, RANGE_SYM, UNBOUNDED_SYM, SLIDE_SYM]
                     ).union(TIME_UNIT_SYM_SET)

# Query keywords
# Select ... from ... where
SELECT_SYM = 'SELECT'
DISTINCT_SYM = 'DISTINCT'
FROM_SYM = 'FROM'
WHERE_SYM = 'WHERE'
GROUP_SYM = 'GROUP'
AS_SYM = 'AS'
NOT_SYM = 'NOT'
OR_SYM = 'OR'
SIMPLE_QUERY_SYM_SET = \
    set([SELECT_SYM,
        DISTINCT_SYM,
        FROM_SYM,
        WHERE_SYM,
        GROUP_SYM,
        BY_SYM,
        AS_SYM,
        NOT_SYM,
        OR_SYM,
        AND_SYM]).union(WINDOW_SYM_SET
                        ).union(PREFERENCES_SYM_SET)


# Bag
UNION_SYM = 'UNION'
INTERSECT_SYM = 'INTERSECT'
EXCEPT_SYM = 'EXCEPT'
BAG_SYM_SET = set([UNION_SYM, INTERSECT_SYM, EXCEPT_SYM])

QUERY_SYM_SET = \
    SIMPLE_QUERY_SYM_SET.union(STREAM_SYM_SET
                               ).union(SEQUENCE_SYM_SET
                                       ).union(TEMPORAL_PREFERENCE_SYM_SET)

# Symbols
LEFT_BRA = '['
RIGHT_BRA = ']'
LEFT_PAR = '('
RIGHT_PAR = ')'
COMMA = ','
DOT = '.'
SEMICOLON = ';'
UNDERLINE = '_'
SYMBOLS_SET = set([LEFT_BRA,
                   RIGHT_BRA,
                   LEFT_PAR,
                   RIGHT_PAR,
                   COMMA,
                   DOT,
                   SEMICOLON,
                   UNDERLINE])

# Operators
LESS_OP = '<'
GREATER_OP = '>'
LESS_EQUAL_OP = '<='
GREATER_EQUAL_OP = '>='
EQUAL_OP = '='
DIFFERENT_OP = '<>'
COMPARISON_OP_SET = set([EQUAL_OP,
                         LESS_OP,
                         LESS_EQUAL_OP,
                         GREATER_OP,
                         GREATER_EQUAL_OP])
INTERVAL_OP_SET = set([LESS_OP, LESS_EQUAL_OP])

MINUS_OP = '-'
PLUS_OP = '+'
DIVID_OP = '/'
MULTI_OP = '*'
MULTI_OP_SET = set([DIVID_OP, MULTI_OP])
PLUS_OP_SET = set([MINUS_OP, PLUS_OP])
ARITHMETIC_OP_SET = set([MINUS_OP,
                         PLUS_OP,
                         DIVID_OP,
                         MULTI_OP])
# Functions keywords
CURRENT_SYM = 'CURRENT()'

# Aggregation functions
MIN_SYM = 'MIN'
MAX_SYM = 'MAX'
SUM_SYM = 'SUM'
COUNT_SYM = 'COUNT'
AGGREGATE_FUNCTIONS_SET = set([MIN_SYM, MAX_SYM, SUM_SYM, COUNT_SYM])

# System keywords
STRING_SYM = 'STRING'
INTEGER_SYM = 'INTEGER'
FLOAT_SYM = 'FLOAT'
TYPES_SYM_SET = set([STRING_SYM, INTEGER_SYM, FLOAT_SYM])

POS_SYM = '_POS'
TS_SYM = '_TS'
FLAG_SYM = '_FL'
CHANGES_SYM = 'CHANGES'
REGISTER_SYM = 'REGISTER'
TABLE_SYM = 'TABLE'
INPUT_SYM = 'INPUT'
QUERY_SYM = 'QUERY'
OUTPUT_SYM = 'OUTPUT'
STREAM_SYM = 'STREAM'
DELIMITER_SYM = 'DELIMITER'
METHOD_SYM = 'METHOD'

INITIAL_SYSTEM_SYM_SET = set([POS_SYM,
                             TS_SYM,
                             FLAG_SYM,
                             CHANGES_SYM,
                             REGISTER_SYM,
                             TABLE_SYM,
                             INPUT_SYM,
                             QUERY_SYM,
                             OUTPUT_SYM,
                             DELIMITER_SYM,
                             METHOD_SYM,
                             STREAM_SYM]
                             )
SYSTEM_SYM_SET = INITIAL_SYSTEM_SYM_SET.union(TYPES_SYM_SET)

RESERVERD_SYM_SET = SYSTEM_SYM_SET.union(QUERY_SYM_SET)


def is_reserved_word(word):
    '''
    Check if 'keyword' is a reserved keyword
    '''
    return word.upper() in RESERVERD_SYM_SET
