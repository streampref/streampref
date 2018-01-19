# -*- coding: utf-8 -*-
'''
Module to define keywords
'''

from pyparsing import Keyword

from grammar.symbols import ACCORDING_SYM, ALL_SYM, AND_SYM, \
    AS_SYM, BY_SYM, DAY_SYM, EXCEPT_SYM, DISTINCT_SYM, DSTREAM_SYM, \
    FIRST_SYM, FROM_SYM, GROUP_SYM, IF_SYM, ISTREAM_SYM, HOUR_SYM, \
    IDENTIFIED_SYM, MINUTE_SYM, NOT_SYM, NOW_SYM, PREFERENCES_SYM, \
    PREVIOUS_SYM, RANGE_SYM, RSTREAM_SYM, SECOND_SYM, \
    SELECT_SYM, SEQUENCE_SYM, SLIDE_SYM, SUBSEQUENCE_SYM, \
    CONSECUTIVE_SYM, SOME_SYM, TEMPORAL_SYM, THEN_SYM, \
    TO_SYM, TOP_SYM, UNBOUNDED_SYM, WHERE_SYM, UNION_SYM, \
    CURRENT_SYM, REGISTER_SYM, INTERSECT_SYM, OUTPUT_SYM, \
    MINIMUM_SYM, MAXIMUM_SYM, LENGTH_SYM, IS_SYM, BETTER_SYM, \
    QUERY_SYM, CHANGES_SYM, STREAM_SYM, TABLE_SYM, INTEGER_SYM, OR_SYM, \
    FLOAT_SYM, STRING_SYM, INPUT_SYM, TIMESTAMP_SYM, END_SYM, POSITION_SYM,\
    TUPLES_SYM


# Grammar keywords
ACCORDING_KEYWORD = Keyword(ACCORDING_SYM, caseless=True)
ALL_KEYWORD = Keyword(ALL_SYM, caseless=True)
AND_KEYWORD = Keyword(AND_SYM, caseless=True)
AS_KEYWORD = Keyword(AS_SYM, caseless=True)
BETTER_KEYWORD = Keyword(BETTER_SYM, caseless=True)
BY_KEYWORD = Keyword(BY_SYM, caseless=True)
CHANGES_KEYWORD = Keyword(CHANGES_SYM, caseless=True)
CONSECUTIVE_KEYWORD = Keyword(CONSECUTIVE_SYM, caseless=True)
CURRENT_KEYWORD = Keyword(CURRENT_SYM, caseless=True)
DAY_KEYWORD = Keyword(DAY_SYM, caseless=True)
DIFFERENCE_KEYWORD = Keyword(EXCEPT_SYM, caseless=True)
DISTINCT_KEYWORD = Keyword(DISTINCT_SYM, caseless=True)
DSTREAM_KEYWORD = Keyword(DSTREAM_SYM, caseless=True)
END_KEYWORD = Keyword(END_SYM, caseless=True)
EXCEPT_KEYWORD = Keyword(EXCEPT_SYM, caseless=True)
FIRST_KEYWORD = Keyword(FIRST_SYM, caseless=True)
FLOAT_KEYWORD = Keyword(FLOAT_SYM, caseless=True)
FROM_KEYWORD = Keyword(FROM_SYM, caseless=True)
GROUP_KEYWORD = Keyword(GROUP_SYM, caseless=True)
HOUR_KEYWORD = Keyword(HOUR_SYM, caseless=True)
IDENTIFIED_KEYWORD = Keyword(IDENTIFIED_SYM, caseless=True)
IF_KEYWORD = Keyword(IF_SYM, caseless=True)
INPUT_KEYWORD = Keyword(INPUT_SYM, caseless=True)
INTEGER_KEYWORD = Keyword(INTEGER_SYM, caseless=True)
INTERSECT_KEYWORD = Keyword(INTERSECT_SYM, caseless=True)
ISTREAM_KEYWORD = Keyword(ISTREAM_SYM, caseless=True)
IS_KEYWORD = Keyword(IS_SYM, caseless=True)
MAXIMUM_KEYWORD = Keyword(MAXIMUM_SYM, caseless=True)
MINIMUM_KEYWORD = Keyword(MINIMUM_SYM, caseless=True)
MINUTE_KEYWORD = Keyword(MINUTE_SYM, caseless=True)
NOT_KEYWORD = Keyword(NOT_SYM, caseless=True)
NOW_KEYWORD = Keyword(NOW_SYM, caseless=True)
OUTPUT_KEYWORD = Keyword(OUTPUT_SYM, caseless=True)
OR_KEYWORD = Keyword(OR_SYM, caseless=True)
POSITION_KEYWORD = Keyword(POSITION_SYM, caseless=True)
PREFERENCES_KEYWORD = Keyword(PREFERENCES_SYM, caseless=True)
PREVIOUS_KEYWORD = Keyword(PREVIOUS_SYM, caseless=True)
QUERY_KEYWORD = Keyword(QUERY_SYM, caseless=True)
RANGE_KEYWORD = Keyword(RANGE_SYM, caseless=True)
REGISTER_KEYWORD = Keyword(REGISTER_SYM, caseless=True)
RSTREAM_KEYWORD = Keyword(RSTREAM_SYM, caseless=True)
SECOND_KEYWORD = Keyword(SECOND_SYM, caseless=True)
SELECT_KEYWORD = Keyword(SELECT_SYM, caseless=True)
SEQUENCE_KEYWORD = Keyword(SEQUENCE_SYM, caseless=True)
LENGTH_KEYWORD = Keyword(LENGTH_SYM, caseless=True)
SLIDE_KEYWORD = Keyword(SLIDE_SYM, caseless=True)
SOME_KEYWORD = Keyword(SOME_SYM, caseless=True)
STREAM_KEYWORD = Keyword(STREAM_SYM, caseless=True)
STRING_KEYWORD = Keyword(STRING_SYM, caseless=True)
SUBSEQUENCE_KEYWORD = Keyword(SUBSEQUENCE_SYM, caseless=True)
TABLE_KEYWORD = Keyword(TABLE_SYM, caseless=True)
TEMPORAL_KEYWORD = Keyword(TEMPORAL_SYM, caseless=True)
TIMESTAMP_KEYWORD = Keyword(TIMESTAMP_SYM, caseless=True)
TUPLES_KEYWORD = Keyword(TUPLES_SYM, caseless=True)
THEN_KEYWORD = Keyword(THEN_SYM, caseless=True)
TOP_KEYWORD = Keyword(TOP_SYM, caseless=True)
TO_KEYWORD = Keyword(TO_SYM, caseless=True)
UNBOUNDED_KEYWORD = Keyword(UNBOUNDED_SYM, caseless=True)
UNION_KEYWORD = Keyword(UNION_SYM, caseless=True)
WHERE_KEYWORD = Keyword(WHERE_SYM, caseless=True)
