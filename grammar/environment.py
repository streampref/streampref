#!/usr/bin/python
# -*- coding: utf-8 -*-
'''
Module to parse environment files
'''

# System imports
import logging
import os
import sys
from pyparsing import Suppress, sglQuotedString, delimitedList, Group, \
    ParseException, OneOrMore, restOfLine, Optional


LOG = logging.getLogger(__name__)


# Required to relative package imports
PATH = os.path.dirname(os.path.realpath(__file__))
sys.path.append(os.path.realpath(os.path.join(PATH, '..', '..')))


class EnvironmentGrammar(object):
    '''Class to parse environment files.

    Grammar:
        <env> ::= (<env-item> ';')+
        <env-item> ::= <table> | <query>
        <table> ::= 'REGISTER' ('STREAM' | 'TABLE')
            <identifier> '(' <attribute> <type> (, <attribute> <type> )*  ')'
            'INPUT' <file>
        <query> ::= 'REGISTER' 'QUERY' <identifier>
            'INPUT' <file>
            'OUTPUT' ['CHANGES'] <file>
        <type> ::= 'STRING' | 'INTEGER' | 'FLOAT'
    '''
    @classmethod
    def grammar(cls):
        '''
        Return grammar for environments
        '''
        from grammar.symbols import SEMICOLON
        from grammar.keywords import REGISTER_KEYWORD
        from grammar.parsed import ParsedEnvironmentItem
        env_term = table_term() | query_term()
        env_term.setParseAction(ParsedEnvironmentItem)
        grammar = OneOrMore(Suppress(REGISTER_KEYWORD) + env_term +
                            Suppress(SEMICOLON))
        # Comments starting with #
        grammar.ignore('#' + restOfLine)
        return grammar

    @classmethod
    def parse(cls, text):
        '''
        Parse a text to ParseResult
        '''
        try:
            LOG.debug('Parsing environment configuration')
            parsed_env = cls.grammar().parseString(text)
            return parsed_env
        except ParseException as p_e:
            LOG.exception('Invalid environment configuration:' + p_e.line)
            LOG.exception('Parsing error: %s', p_e)


def query_term():
    '''
    Grammar for query term
    '''
    from grammar.keywords import QUERY_KEYWORD, \
        OUTPUT_KEYWORD, CHANGES_KEYWORD, INPUT_KEYWORD
    from grammar.basic import identifier_token
    file_t = file_term()
    identifier_t = identifier_token()
    query_t = QUERY_KEYWORD.setResultsName('type') + \
        identifier_t.setResultsName('name') + \
        Suppress(INPUT_KEYWORD) + \
        file_t.setResultsName('input') + \
        Optional(Suppress(OUTPUT_KEYWORD) +
                 Optional(CHANGES_KEYWORD).setResultsName('changes') +
                 file_t.setResultsName('output'))
    return query_t


def file_term():
    '''
    Grammar for file term
    '''
    file_t = sglQuotedString
    file_t.setParseAction(lambda t: t[0][1:-1])
    return file_t


def table_term():
    '''
    Grammar for table term

    'REGISTER' ('STREAM' | 'TABLE')
    <identifier> '(' <attribute> <type> (',' <attribute> <type> )*  ')'
    'DATA' <file>
    '''
    from grammar.keywords import TABLE_KEYWORD, \
        STREAM_KEYWORD, INPUT_KEYWORD
    from grammar.basic import identifier_token
    id_t = identifier_token()
    table_type_t = TABLE_KEYWORD | STREAM_KEYWORD
    schema_t = schema_term()
    file_t = file_term()
    table_t = table_type_t.setResultsName('type') + \
        id_t.setResultsName('name') + \
        Group(schema_t).setResultsName('schema') + \
        Suppress(INPUT_KEYWORD) + \
        file_t.setResultsName('input')
    return table_t


def schema_term():
    '''
    Grammar for schema term
    '''
    from grammar.symbols import LEFT_PAR, RIGHT_PAR, COMMA
    from grammar.keywords import INTEGER_KEYWORD, FLOAT_KEYWORD, \
        STRING_KEYWORD
    from grammar.basic import identifier_token
    type_t = INTEGER_KEYWORD | FLOAT_KEYWORD | STRING_KEYWORD
    attribute_t = Group(identifier_token() + type_t)
    schema_t = Suppress(LEFT_PAR) + delimitedList(attribute_t, COMMA) + \
        Suppress(RIGHT_PAR)
    return schema_t


def print_parsed(parsed_terms):
    '''
    Print a ParseResult of environment file
    '''
    for number, item in enumerate(list(parsed_terms)):
        print '\nItem {c}'.format(c=number)
        print item


def get_file_text():
    '''
    Get text from file
    '''
    if len(sys.argv) == 2:
        conf_file = open(sys.argv[1])
        return conf_file.read()
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
    FILE_TEXT = get_file_text().strip()
    if FILE_TEXT == '':
        exit(0)
    try:
        PARSED = EnvironmentGrammar.parse(FILE_TEXT)
        print 'Original file:'
        print FILE_TEXT
        print ''
        print 'ParseResult object:'
        print PARSED
        print ''
        print 'ParseResult detailed:'
        print_parsed(PARSED)
    except ParseException as parse_exception:
        print 'EnvParser error:'
        print parse_exception.line
        print parse_exception
