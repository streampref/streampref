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



class TemporalTheoryGrammar(object):
    '''
    Class for cp-theory grammar

    <temporal-theory-grammar> ::=
        <temporal-rule-term> {'AND' <temporal-rule-term>}*
    <temporal-rule-term> ::=
        [<antecedent>] <preference> [<indifferent-list>]
    <condition-term> ::=
        'IF' <temporal-predicate> ('AND' <temporal-predicate>)* 'THEN'
    <preference-term> ::=
        <predicate> 'BETTER' <predicate>' |
        <predicate> '>' <predicate>
    <indifferent-list> ::=
        '[' <attribute> (, <attribute>)* ']' |
        '(' <attribute> (, <attribute>)* ')'
    <predicate-term> ::=
        <attribute> ('<' | '<=' | '>' | '>=' | '=') <value> |
        <value> ('<' | '<=') <attribute> ('<' | '<=') <value>
    '''

    @classmethod
    def grammar(cls):
        '''
        Return grammar for cp-theories
        '''
        from grammar.keywords import AND_KEYWORD
        tr_term = temporal_rule_term()
        grammar = delimitedList(tr_term, AND_KEYWORD)
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
            log.debug('Parsing temporal theory')
            parsed_cql = cls.grammar().parseString(string, parseAll=True)
            return parsed_cql
        except ParseException as p_e:
            log.error('Invalid code:' + string)
            log.error('Invalid line:' + p_e.line)
            log.exception('Parsing error: %s', p_e)
            return None


def temporal_rule_term():
    '''
    Grammar for cp-rules

    [<antecedent>] <preference> [<indifferent-list>]
    '''
    from grammar.parsed import ParsedRule
    from grammar.theory import preference_term, indifferent_list
    condition = temporal_condition_term()
    preference = preference_term()
    indiff_list = indifferent_list()
    rule = \
        Optional(condition).setResultsName('condition') + \
        preference.setResultsName('preference') + \
        Optional(indiff_list).setResultsName('indifferent')
    rule.setParseAction(ParsedRule)
    return rule


def temporal_condition_term():
    '''
    Grammar for condition term

    'IF' <predicate> {'AND' <predicate>}* 'THEN'
    '''
    from grammar.keywords import IF_KEYWORD, AND_KEYWORD, \
        THEN_KEYWORD
    predicate = temporal_predicate_term()
    condition = Group(Suppress(IF_KEYWORD) +
                      delimitedList(predicate, AND_KEYWORD) +
                      Suppress(THEN_KEYWORD))
    condition.setParseAction(lambda t: t[0].asList())
    return condition


def temporal_predicate_term():
    '''
    Grammar for temporal predicates

    'PREVIOUS' <predicate>
    'SOME PREVIOUS' <predicate>
    'ALL PREVIOUS' <predicate>
    'FIRST'
    <predicate>
    '''
    from grammar.keywords import SOME_KEYWORD, \
        PREVIOUS_KEYWORD, ALL_KEYWORD, FIRST_KEYWORD
    from grammar.basic import predicate_term
    from grammar.parsed import ParsedTemporalPredicate
    predicate = predicate_term()
    temporal_predicate = \
        FIRST_KEYWORD.setResultsName('first') | \
        Optional(
                 Optional(SOME_KEYWORD.setResultsName('some') |
                          ALL_KEYWORD.setResultsName('all')) +
                 PREVIOUS_KEYWORD.setResultsName('previous')) + \
        predicate.setResultsName('predicate')
    temporal_predicate.setParseAction(ParsedTemporalPredicate)
    return temporal_predicate


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
        PARSED = TemporalTheoryGrammar.parse(FILE_TEXT)
        print 'Original string:'
        print FILE_TEXT
        print ''
        print 'ParseResult object:'
        for tcprule in PARSED:
            print tcprule
    except ParseException as parse_exception:
        print 'Parse error:'
        print parse_exception.line
        print parse_exception
