#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Module for conditional preference theory grammar
'''

# PyParsing import
import logging
import os
import sys
from pyparsing import Suppress, Optional, delimitedList, operatorPrecedence, \
    ParseException, restOfLine, oneOf, opAssoc, Group, ZeroOrMore, \
    Literal, ParseResults


LOG = logging.getLogger(__name__)

# Required to relative package imports
PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.realpath(os.path.join(PATH, '..')))


class QueryGrammar(object):
    '''
    Class for query grammar

    <query-grammar> ::=
        <stream-query> ';'
        | <sequence-query> ';'
        | <bag-query> ';'
    <stream-query> ::=
        'SELECT' <stream-operation> 'FROM' '(' <table-window> ')'
    <sequence-query> :=
        'SELECT' ['TOP('<integer>')']
            [['SUBSEQUENCE' 'END' 'POSITION' 'FROM']
            'SUBSEQUENCE' 'CONSECUTIVE' 'TIMESTAMP' 'FROM']
            'SEQUENCE' 'IDENTIFIED' 'BY' <attribute-list>
            '[' RANGE' <range-size> [, 'SLIDE' <slide-size>] ']'
        'FROM' <stream> ['AS' <identifier>]
            | <stream-operation> 'FROM' '(' <table-window> ')'
        ['WHERE' <lenght-term>]
        ['ACCORDING' 'TO'] 'TEMPORAL' 'PREFERENCES' <temporal-theory-grammar>
    <lenght-term> ::=
        'MINIMUM' 'LENGTH' 'IS <integer>
        |'MAXIMUM' 'LENGTH' 'IS <integer>
        | 'MINIMUM' 'LENGTH' 'IS <integer> 'AND'
            'MAXIMUM' 'LENGTH' 'IS <integer>
    <stream-operation> ::=
        'DSTREAM' | 'ISTREAM' | 'RSTREAM'
    <bag-query> ::=
        <simple-query> (<bag-operation> <simple-query> )*
    <bag-operation> ::=
        'UNION' | 'DIFFERENCE' | 'EXCEPT'
    <simple-query> ::=
        'SELECT' ['DISTINCT'] ['TOP('<integer>')']
        <select-term> (',' <select-term>)*
        'FROM' <table-window> (',' <table-window>)*
        [<where-condition>]
        [['ACCORDING' 'TO'] 'PREFERENCES' <theory-grammar>]
        ['GROUP BY' <identifier> (',' <identifier>)* ]
    <select-term> ::=
        <expression> ['AS' <identifier>] |
        [<identifier> '.'] '*'
    <where-condition> ::=
        'WHERE' <where-term> ('AND' <where-term>)*
        | 'WHERE' <where-term> ('OR' <where-term>)*
    <where-term> ::=
        ['NOT'] <expression> <comparison-token> <expression>
    <table-window> ::=
        <identifier> [ <window> ] ['AS' <identifier>]
    <window> ::=
        'NOW' | ['RANGE'] 'UNBOUNDED' |
        'RANGE' <range-size> [',' 'SLIDE' <slide-size>]
    <range-size> ::=
        <slide-size>
    <slide-size> ::=
        <integer> ('SECOND' | 'MINUTE' | 'HOUR' | 'DAY')
    '''

    @classmethod
    def grammar(cls):
        '''
        Return grammar for queries
        '''
        from grammar.symbols import SEMICOLON
        query = stream_query() | sequence_query() | Group(bag_query())
        grammar = query.setResultsName('query') + \
            Suppress(SEMICOLON)
        # Comments
        grammar.ignore('--' + restOfLine)
        return grammar

    @classmethod
    def parse(cls, string):
        '''Parse a string using the grammar'''
        try:
            LOG.debug('Parsing query')
            parsed_cql = cls.grammar().parseString(string)
            return parsed_cql
        except ParseException as p_e:
            LOG.error('Invalid code:' + string)
            LOG.error('Invalid line:' + p_e.line)
            LOG.exception('Parsing error: %s', p_e)
            return None


def bag_query():
    '''
    Grammar for queries (simple or bag operations)
    '''
    from grammar.keywords import UNION_KEYWORD, EXCEPT_KEYWORD, \
        INTERSECT_KEYWORD
    simple_q = simple_query()
    bag_op = UNION_KEYWORD | EXCEPT_KEYWORD | INTERSECT_KEYWORD
    bag_q = simple_q + ZeroOrMore(bag_op + simple_q)
    return bag_q


def simple_query():  # IGNORE:too-many-locals
    '''
    Grammar for simple queries

    <simple-query> ::=
        'SELECT' ['DISTINCT'] ['TOP('<integer>')']
        <select-term> (',' <select-term>)*
        'FROM' <table-term> (',' <table-term>)*
        [<where-condition>]
        [['ACCORDING' 'TO'] 'PREFERENCES' <theory-grammar>]
        ['GROUP BY' <identifier> (',' <identifier>)* ]
    '''
    from grammar.keywords import AND_KEYWORD, \
        ACCORDING_KEYWORD, TO_KEYWORD, DISTINCT_KEYWORD, \
        PREFERENCES_KEYWORD, SELECT_KEYWORD, FROM_KEYWORD, WHERE_KEYWORD, \
        GROUP_KEYWORD, BY_KEYWORD, OR_KEYWORD
    from grammar.basic import attribute_term
    from grammar.symbols import COMMA
    from grammar.theory import TheoryGrammar
    from grammar.parsed import ParsedSimpleQuery
    select_clause = \
        Suppress(SELECT_KEYWORD) + \
        Optional(DISTINCT_KEYWORD).setResultsName('distinct') + \
        Optional(top_term()).setResultsName('top') + \
        delimitedList(select_term(), COMMA).setResultsName('selected')
    group_by_clause = Suppress(GROUP_KEYWORD) + Suppress(BY_KEYWORD) + \
        delimitedList(attribute_term(), COMMA)
    preference_clause = Optional(Suppress(ACCORDING_KEYWORD + TO_KEYWORD)) + \
        Suppress(PREFERENCES_KEYWORD) + TheoryGrammar.grammar()
    where_single = Group(where_term())
    where_or = Suppress(OR_KEYWORD) + \
        delimitedList(Group(where_term()), OR_KEYWORD)
    where_and = Suppress(AND_KEYWORD) + \
        delimitedList(Group(where_term()), AND_KEYWORD)
    where_t = (where_or.setResultsName('where_or') |
               where_and.setResultsName('where_and'))
    simple_q = select_clause.setResultsName('select_clause') + \
        Suppress(FROM_KEYWORD) + \
        delimitedList(table_term(),
                      COMMA).setResultsName('from_clause') + \
        Optional(Suppress(WHERE_KEYWORD) +
                 where_single.setResultsName('where_clause') +
                 Optional(where_t)) + \
        Optional(group_by_clause.setResultsName('group_clause') |
                 preference_clause.setResultsName('preference_clause'))
    simple_q.setParseAction(ParsedSimpleQuery)
    return simple_q


def select_term():
    '''
    Grammar for select terms
    '''
    from grammar.symbols import DOT, MULTI_OP
    from grammar.basic import identifier_token
    from grammar.parsed import ParsedSelectTerm
    identifier = identifier_token()
    arithmetic = arithmetic_term()
    alias = alias_term()
    all_attributes = \
        Optional(identifier.setResultsName('table') + Suppress(DOT)) + \
        Literal(MULTI_OP)
    select_t = \
        arithmetic.setResultsName('expression') + Optional(alias) | \
        all_attributes.setResultsName('all')
    select_t.setParseAction(ParsedSelectTerm)
    return select_t


def where_term():
    '''
    Grammar for where terms
    '''
    from grammar.basic import comparision_operation
    from grammar.keywords import NOT_KEYWORD
    comparison = comparision_operation()
    arithmetic = arithmetic_term()
    and_term = Optional(NOT_KEYWORD).setResultsName('not') + \
        arithmetic.setResultsName('term1') + \
        comparison.setResultsName('operator') + \
        arithmetic.setResultsName('term2')
    return and_term


def alias_term():
    '''
    Grammar for alias terms
    '''
    from grammar.keywords import AS_KEYWORD
    from grammar.basic import identifier_token
    identifier = identifier_token()
    alias = Suppress(AS_KEYWORD) + identifier.setResultsName('alias')
    return alias


def arithmetic_term():
    '''
    Grammar for arithmetic expressions
    '''
    from grammar.keywords import CURRENT_KEYWORD
    from grammar.symbols import MULTI_OP_SET, PLUS_OP_SET
    from grammar.basic import attribute_term, value_term
    from grammar.symbols import LEFT_PAR, RIGHT_PAR,\
        AGGREGATE_FUNCTIONS_SET
    # Arithmetic operators
    multiply_op = oneOf(list(MULTI_OP_SET))
    addition_op = oneOf(list(PLUS_OP_SET))
    operand_token = CURRENT_KEYWORD | attribute_term() | value_term()
    # Arithmetic expression
    precedence_list = [(multiply_op, 2, opAssoc.LEFT),
                       (addition_op, 2, opAssoc.LEFT)]
    expression_t = operatorPrecedence(operand_token, precedence_list)
    # Aggregate function
    aggregate_function = oneOf(list(AGGREGATE_FUNCTIONS_SET), caseless=True)
    arithmetic_t = Group(aggregate_function + Suppress(LEFT_PAR) +
                         expression_t + Suppress(RIGHT_PAR)) | \
        expression_t
    arithmetic_t.setParseAction(lambda t: t.asList())
    return arithmetic_t


def table_term():
    '''
    Grammar for table terms
    '''
    from grammar.basic import identifier_token
    from grammar.parsed import ParsedTable
    identifier = identifier_token()
    alias = alias_term()
    table = \
        identifier.setResultsName('table_name') + \
        Optional(range_slide_term()).setResultsName('range_slide') + \
        Optional(alias)
    table.setParseAction(ParsedTable)
    return table


def range_slide_term():
    '''
    Grammar for range terms
    '''
    from grammar.keywords import RANGE_KEYWORD, NOW_KEYWORD, \
        UNBOUNDED_KEYWORD, SLIDE_KEYWORD
    from grammar.symbols import COMMA, LEFT_BRA, RIGHT_BRA, \
        TIME_UNIT_SYM_SET
    from grammar.basic import integer_value
    integer = integer_value()
    time_unit = oneOf(list(TIME_UNIT_SYM_SET), caseless=True)
    # Size Term
    range_size = Suppress(RANGE_KEYWORD) + \
        integer.setResultsName('range_size') + \
        time_unit.setResultsName('range_unit')
    # Slide Term
    slide = Suppress(COMMA + SLIDE_KEYWORD) + \
        integer.setResultsName('slide_size') + \
        time_unit.setResultsName('slide_unit')
    range_slide = \
        Suppress(LEFT_BRA) + \
        (NOW_KEYWORD.setResultsName('now') |
         range_size + Optional(slide) |
         Optional(Suppress(RANGE_KEYWORD)) +
         UNBOUNDED_KEYWORD.setResultsName('unbounded')
         ) + Suppress(RIGHT_BRA)
    return range_slide


def stream_query():
    '''
    <stream-query> ::=
        'SELECT' <stream-operation> '(' <table-window> ')'
    '''
    from grammar.keywords import SELECT_KEYWORD
    from grammar.parsed import ParsedStreamQuery
    stream_q = \
        Suppress(SELECT_KEYWORD) + stream_term()
    stream_q.setParseAction(ParsedStreamQuery)
    return stream_q


def sequence_query():
    '''
    <sequence-query> :=
        'SELECT' ['TOP('<integer>')']
            [['SUBSEQUENCE' 'END' 'POSITION' 'FROM']
            'SUBSEQUENCE' 'CONSECUTIVE' 'TIMESTAMP' 'FROM']
            'SEQUENCE' 'IDENTIFIED' 'BY' <attribute-list>
            '[' RANGE' <range-size> [, 'SLIDE' <slide-size>] ']'
        'FROM' <stream> ['AS' <identifier>]|
            <stream-operation> 'FROM' '(' <table-window> ')'
        ['WHERE'
            'MINIMUM' 'LENGTH' 'IS <integer> 'AND'
            'MAXIMUM' 'LENGTH' 'IS <integer>]
        ['ACCORDING' 'TO'] 'TEMPORAL' 'PREFERENCES' <temporal-theory-grammar>
    '''
    from grammar.keywords import SELECT_KEYWORD, FROM_KEYWORD, \
        WHERE_KEYWORD, ACCORDING_KEYWORD, \
        TO_KEYWORD, TEMPORAL_KEYWORD, PREFERENCES_KEYWORD
    from grammar.temporal_theory import TemporalTheoryGrammar
    from grammar.parsed import ParsedSequenceQuery
    sequence = sequence_term()
    select_clause = Suppress(SELECT_KEYWORD) + \
        Optional(top_term()) + \
        Optional(subsequence_term()) + \
        sequence.setResultsName('sequence')
    table_t = table_term()
    stream = stream_term() | table_t.setResultsName('table') + \
        Optional(alias_term())
    seq_query = select_clause + \
        Suppress(FROM_KEYWORD) + stream + \
        Optional(Suppress(WHERE_KEYWORD) +
                 sequence_where_clause()).setResultsName('where_clause') + \
        Optional(Suppress(Optional(ACCORDING_KEYWORD + TO_KEYWORD) +
                 TEMPORAL_KEYWORD + PREFERENCES_KEYWORD) +
                 TemporalTheoryGrammar.grammar()
                 ).setResultsName('preference_clause')
    seq_query.setParseAction(ParsedSequenceQuery)
    return seq_query


def stream_term():
    '''
    Grammar for stream term
    '''
    from grammar.keywords import RSTREAM_KEYWORD, \
        ISTREAM_KEYWORD, DSTREAM_KEYWORD, FROM_KEYWORD
    stream_op = RSTREAM_KEYWORD | ISTREAM_KEYWORD | DSTREAM_KEYWORD
    table = table_term()
    stream = \
        stream_op.setResultsName('stream_operation') + \
        Suppress(FROM_KEYWORD) + \
        table.setResultsName('table')
    return stream


def sequence_where_clause():
    '''
    Grammar for where clause of sequence queries
    '''
    from grammar.keywords import MINIMUM_KEYWORD, LENGTH_KEYWORD, \
        MAXIMUM_KEYWORD, IS_KEYWORD, AND_KEYWORD
    from grammar.basic import integer_value
    integer = integer_value()
    where_clause = \
        Suppress(MINIMUM_KEYWORD + LENGTH_KEYWORD + IS_KEYWORD) + \
        integer.setResultsName('min') + \
        Optional(Suppress(AND_KEYWORD) +
                 Suppress(MAXIMUM_KEYWORD + LENGTH_KEYWORD + IS_KEYWORD) +
                 integer.setResultsName('max')) | \
        Suppress(MAXIMUM_KEYWORD + LENGTH_KEYWORD + IS_KEYWORD) + \
        integer.setResultsName('max') + \
        Optional(Suppress(AND_KEYWORD) +
                 Suppress(MINIMUM_KEYWORD + LENGTH_KEYWORD + IS_KEYWORD) +
                 integer.setResultsName('min'))
    return where_clause


def subsequence_term():
    '''
    Grammar for subsequence terms
    '''
    from grammar.keywords import CONSECUTIVE_KEYWORD, \
        SUBSEQUENCE_KEYWORD, FROM_KEYWORD, TIMESTAMP_KEYWORD, END_KEYWORD, \
        POSITION_KEYWORD, TUPLES_KEYWORD
    tuples_or_timestamp = TUPLES_KEYWORD | TIMESTAMP_KEYWORD
    consecutive_timestamp_t = Suppress(SUBSEQUENCE_KEYWORD) + \
        Group(CONSECUTIVE_KEYWORD +
              tuples_or_timestamp).setResultsName('consecutive_timestamp') + \
        Suppress(FROM_KEYWORD)
    end_position_t = Suppress(SUBSEQUENCE_KEYWORD) + \
        Group(END_KEYWORD +
              POSITION_KEYWORD).setResultsName('end_position') + \
        Suppress(FROM_KEYWORD)
    subseq_t = Optional(end_position_t) + consecutive_timestamp_t | \
        end_position_t
    return subseq_t


def sequence_term():
    '''
    Grammar for sequence term
    '''
    from grammar.keywords import SEQUENCE_KEYWORD, \
        IDENTIFIED_KEYWORD, BY_KEYWORD
    from grammar.symbols import COMMA
    from grammar.basic import attribute_term
    attribute = attribute_term()
    identifier_list = delimitedList(attribute, COMMA)
    range_slide = range_slide_term()
    range_slide.setResultsName('range_slide')
    sequence = \
        Suppress(SEQUENCE_KEYWORD + IDENTIFIED_KEYWORD + BY_KEYWORD) + \
        identifier_list.setResultsName('identifier') + \
        range_slide.setResultsName('range_slide')
    return sequence


def top_term():
    '''
    Grammar for top-k term
    '''
    from grammar.keywords import TOP_KEYWORD
    from grammar.symbols import LEFT_PAR, RIGHT_PAR
    from grammar.basic import integer_value
    integer = integer_value()
    top = Suppress(TOP_KEYWORD) + \
        Suppress(LEFT_PAR) + \
        integer.setResultsName('top') + \
        Suppress(RIGHT_PAR)
    return top


def get_file_text():
    '''Get CQL query from file'''
    if len(sys.argv) == 2:
        pref_file = open(sys.argv[1])
        return pref_file.read()
    else:
        return ''


def start_log():
    '''
    Configure log options
    '''
    from control.config import config_log
    from control.config import DEFAULT_LOG_FILE
    config_log(DEFAULT_LOG_FILE)


# Check if file is executed as a program
if __name__ == '__main__':
    start_log()
    LOG = logging.getLogger(__name__)
    FILE_TEXT = get_file_text()
    if FILE_TEXT == '':
        exit(0)
    try:
        PARSED = QueryGrammar.parse(FILE_TEXT)
        print 'Original string:'
        print FILE_TEXT
        print ''
        print 'ParseResult object:'
        print type(PARSED.query)
        if isinstance(PARSED.query, ParseResults):
            for s_query in PARSED.query:
                if isinstance(s_query, str):
                    print 'Operation:\n' + str(s_query)
                else:
                    print 'Query:\n' + str(s_query)
        else:
            print PARSED.query
    except ParseException as parse_exception:
        print 'Parse error:'
        print parse_exception.line
        print parse_exception
