# -*- coding: utf-8 -*-
'''
Module for basic grammar used by others grammars
'''

# PyParsing import
from pyparsing import Suppress, Word, alphas, alphanums, \
    oneOf, nums, Optional, sglQuotedString, Combine

from grammar.parsed import ParsedAttribute, ParsedPredicate
from grammar.symbols import MINUS_OP


# StremPref import
def comparision_operation():
    '''
    Grammar for comparison operators
    '''
    from grammar.symbols import COMPARISON_OP_SET
    return oneOf(list(COMPARISON_OP_SET))


def predicate_term():
    '''
    Grammar for predicates

    <attribute> {'<' | '<=' | '>' | '>=' | '='} <value>
    <value> {'<' | '<='} <attribute> {'<' | '<='} <value>
    '''
    from grammar.symbols import LEFT_PAR, RIGHT_PAR, \
        INTERVAL_OP_SET
    # Interval and comparison operators
    interval_op = oneOf(list(INTERVAL_OP_SET))
    comparison_op = comparision_operation()
    value_tok = value_term()
    att_term = attribute_term()
    # Interval predicate
    interval_term = value_tok.setResultsName('left_value') + \
        interval_op.setResultsName('left_operator') + \
        att_term.setResultsName('attribute') + \
        interval_op.setResultsName('right_operator') + \
        value_tok.setResultsName('right_value')
    # Comparison predicate
    comparison_term = att_term.setResultsName('attribute') + \
        comparison_op.setResultsName('operator') + \
        value_tok.setResultsName('value')
    # Predicate is interval or comparison
    simple_predicate_term = interval_term | comparison_term
    pred_term = simple_predicate_term | \
        Suppress(LEFT_PAR) + simple_predicate_term + Suppress(RIGHT_PAR)
    pred_term.setParseAction(ParsedPredicate)
    return pred_term


def attribute_term():
    '''
    Grammar for attributes

    [<identifier>.]<identifier>
    '''
    from grammar.symbols import DOT
    # Attribute term
    id_tok = identifier_token()
    att_term = \
        Optional(id_tok.setResultsName('table_name') + Suppress(DOT)) + \
        id_tok.setResultsName('attribute_name')
    att_term.setParseAction(ParsedAttribute)
    return att_term


def string_value():
    '''
    Grammar for string values
    '''
    string_token = sglQuotedString
    string_token.setParseAction(lambda t: t[0][1:-1])
    return string_token


def float_value():
    '''
    Grammar for float values
    '''
    from grammar.symbols import DOT
    float_t = Combine(Optional(MINUS_OP) + Word(nums) + DOT + Word(nums))
    float_t.setParseAction(lambda t: float(t[0]))
    return float_t


def value_term():
    '''
    Grammar for value tokens
    A value is an integer, a float or a string
    '''
    integer_tok = integer_value()
    integer_tok.setParseAction(lambda t: int(t[0]))
    float_token = float_value()
    float_token.setParseAction(lambda t: float(t[0]))
    string_tok = string_value()
    value_tok = (string_tok | float_token | integer_tok)
    return value_tok


def identifier_token():
    '''
    Grammar for identifiers

    {[A-Z]|[a-z]|_)([A-Z]|[a-z]|[0-9]|_}*
    '''
    from grammar.symbols import UNDERLINE
    # Identifier begin with letter and have letters, numbers or underline
    identifier_tok = Word(alphas + UNDERLINE, alphanums + UNDERLINE)
    # Convert identifier to upper case
    identifier_tok.setParseAction(lambda t: t[0].upper())
    return identifier_tok


def integer_value():
    '''
    Grammar for integer numbers
    '''
    integer_t = Combine(Optional(MINUS_OP) + Word(nums))
    return integer_t
