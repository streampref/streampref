#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Module for conditional preference theory grammar
'''

# PyParsing import
import logging
import os
import sys
from pyparsing import Suppress, Optional, delimitedList, Group, \
    ParseException


# Required to relative package imports
PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.realpath(os.path.join(PATH, '..')))


class TheoryGrammar(object):
    '''
    Class for cp-theory grammar

    <theory-grammar> ::= <rule-term> {'AND' <rule-term>}*
    <rule-term> ::= [<antecedent>] <preference> [<indifferent-list>]
    <condition-term> ::= 'IF' <predicate> {'AND' <predicate>}* 'THEN'
    <preference-term> ::=
        <predicate> 'BETTER' <predicate>' |
        <predicate> '>' <predicate>
    <indifferent-list> ::=
        '[' <attribute> (',' <attribute>)* ']' |
        '(' <attribute> (',' <attribute>)* ')'
    <predicate-term> ::=
        <attribute> {'<' | '<=' | '>' | '>=' | '='} <value> |
        <value> {'<' | '<='} <attribute> {'<' | '<='} <value>
    '''

    @classmethod
    def grammar(cls):
        '''
        Return grammar for cp-theories
        '''
        from grammar.keywords import AND_KEYWORD
        rule = rule_term()
        grammar = delimitedList(rule, AND_KEYWORD)
        grammar.setParseAction(lambda t: t.asList())
        return grammar

    @classmethod
    def parse(cls, string):
        '''Parse a string using the grammar'''
        log = logging.getLogger(__name__)
        if len(log.handlers) == 0:
            logging.getLogger()
            console_hanler = logging.StreamHandler()
            log.addHandler(console_hanler)
            log.setLevel(logging.DEBUG)
        try:
            log.debug('Parsing theory')
            parsed_cql = cls.grammar().parseString(string, parseAll=True)
            return parsed_cql
        except ParseException as p_e:
            log.error('Invalid code:' + string)
            log.error('Invalid line:' + p_e.line)
            log.exception('Parsing error: %s', p_e)
            return None


def rule_term():
    '''
    Grammar for cp-rules

    [<condition>] <preference> [<indifferent-list>]
    '''
    from grammar.parsed import ParsedRule
    condition = condition_term()
    preference = preference_term()
    indiff_list = indifferent_list()
    rule = \
        Optional(condition).setResultsName('condition') + \
        preference.setResultsName('preference') + \
        Optional(indiff_list).setResultsName('indifferent')
    rule.setParseAction(ParsedRule)
    return rule


def condition_term():
    '''
    Grammar for condition term

    'IF' <predicate> {'AND' <predicate>}* 'THEN'
    '''
    from grammar.keywords import IF_KEYWORD, AND_KEYWORD, \
        THEN_KEYWORD
    from grammar.basic import predicate_term
    predicate = predicate_term()
    condition = Group(Suppress(IF_KEYWORD) +
                      delimitedList(predicate, AND_KEYWORD) +
                      Suppress(THEN_KEYWORD))
    condition.setParseAction(lambda t: t[0].asList())
    return condition


def preference_term():
    '''
    Grammar for preference term

    <predicate> 'BETTER' <predicate>'
    <predicate> '>' <predicate>
    '''
    from grammar.keywords import BETTER_KEYWORD
    from grammar.symbols import GREATER_OP
    from grammar.basic import predicate_term
    predicate = predicate_term()
    preference = predicate.setResultsName('best') + \
        Suppress(BETTER_KEYWORD | GREATER_OP) + \
        predicate.setResultsName('worst')
    return preference


def indifferent_list():
    '''
    Grammar for list of indifferent attributes

    '[' <attribute> (, <attribute>)* ']'
    '(' <attribute> (, <attribute>)* ')'
    '''
    from grammar.symbols import LEFT_BRA, RIGHT_BRA, LEFT_PAR, \
        RIGHT_PAR, COMMA
    from grammar.basic import attribute_term
    att_term = attribute_term()
    indiff_par = Suppress(LEFT_PAR) + \
        delimitedList(att_term, COMMA) + \
        Suppress(RIGHT_PAR)
    indiff_bra = Suppress(LEFT_BRA) + \
        delimitedList(att_term, COMMA) + \
        Suppress(RIGHT_BRA)
    indiff_list = Group(indiff_par | indiff_bra)
    indiff_list.setParseAction(lambda t: t[0].asList())
    return indiff_list


def get_file_text():
    '''Get text from file'''
    if len(sys.argv) == 2:
        pref_file = open(sys.argv[1])
        return pref_file.read()
    else:
        return ''


# Check if file is executed as a program
if __name__ == '__main__':
    FILE_TEXT = get_file_text()
    if FILE_TEXT == '':
        exit(0)
    try:
        PARSED = TheoryGrammar.parse(FILE_TEXT)
        print 'Original string:'
        print FILE_TEXT
        if PARSED is not None:
            print ''
            print 'ParseResult object:'
            for cprule in PARSED:
                print cprule
    except ParseException as parse_exception:
        print 'Parse error:'
        print parse_exception.line
        print parse_exception
