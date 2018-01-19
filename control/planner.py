# -*- coding: utf-8 -*-
'''
Module to manage plans of queries
'''

import logging

from grammar.parsed import ParsedSequenceQuery, ParsedStreamQuery
from grammar.symbols import BAG_SYM_SET, UNION_SYM, \
    INTERSECT_SYM
from operators.bag import BagExceptOp, BagIntersectOp, \
    BagUnionOp
from operators.basic import TableOp, SelectionOp, \
    ProjectionOp, DistinctOp
from operators.join import JoinOp
from operators.sequence import SeqOp, ConseqOp, EndseqOp, MinseqOp,\
    MaxseqOp
from operators.simplepreference import PreferenceOp
from operators.stream import StreamDeleteOp, \
    StreamInsertOp, StreamRelationOp
from operators.temporalpreference \
    import TemporalPreferenceOp
from operators.window import WindowOp
from preference.rule import CPRule, TCPRule
from preference.theory import CPTheory, TCPTheory


# Start logger
LOG = logging.getLogger(__name__)


def build_tcptheory(parsed_theory, operator, preference_algorithm):
    '''
    Build a TCPTheory from parser
    '''
    LOG.debug('Building TCPTheory')
    tcprule_list = []
    for parsed_tcprule in parsed_theory:
        tcprule = TCPRule(parsed_tcprule, operator)
        tcprule_list.append(tcprule)
    tcptheory = TCPTheory(tcprule_list, preference_algorithm)
    LOG.debug('TCPTheory build: %s', tcptheory)
    return tcptheory


def build_cptheory(parsed_cprule_list, operator, preference_method):
    '''
    Build a CPTheory from parsed list of ParsedCPRules
    '''
    LOG.debug('Building CPTheory')
    rule_list = []
    for parsed_cprule in parsed_cprule_list:
        cprule = CPRule(parsed_cprule, operator)
        rule_list.append(cprule)
    cptheory = CPTheory(rule_list, preference_method)
    LOG.debug('CPTheory build: %s', cptheory)
    return cptheory


def build_sequence(seq_query, table_dict, conf):
    '''
    Build a sequence operation
    '''
    if seq_query.get_stream_operation() is not None:
        operator = build_stream(seq_query, table_dict)
    else:
        operator = build_table_window(seq_query.get_table(), table_dict)
    LOG.debug('Building SEQ operation')
    range_slide = (seq_query.get_range(), seq_query.get_slide())
    operator = SeqOp(operator, seq_query.get_identifier(), range_slide)
    LOG.debug('SEQ operator build: %s', operator)
    if seq_query.is_consecutive():
        LOG.debug('Building CONSEQ operation')
        operator = ConseqOp(operator, conf.get_subseq_alg())
        LOG.debug('CONSEQ operator build: %s', operator)
    if seq_query.is_end():
        LOG.debug('Building ENDSEQ operation')
        operator = EndseqOp(operator, conf.get_subseq_alg())
        LOG.debug('ENDSEQ operator build: %s', operator)
    min_len = seq_query.get_min()
    if min_len is not None:
        LOG.debug('Building MINSEQ operation')
        operator = MinseqOp(operator, min_len)
        LOG.debug('MINSEQ operator build: %s', operator)
    max_len = seq_query.get_max()
    if max_len is not None:
        LOG.debug('Building MAXSEQ operation')
        operator = MaxseqOp(operator, max_len)
        LOG.debug('MAXSEQ operator build: %s', operator)
    parsed_rule_list = seq_query.get_preferences()
    if len(parsed_rule_list):
        tcptheory = build_tcptheory(parsed_rule_list,
                                    operator, conf.get_tpref_alg())
        operator = TemporalPreferenceOp(operator, tcptheory,
                                        conf.get_tpref_alg(),
                                        seq_query.get_top(),
                                        conf.get_outoperator_file())
    return operator


def build_table_window(parsed_table, table_dict):
    '''
    Build a table or window operator
    '''
    alias = None
    if parsed_table.get_alias() is not None:
        alias = parsed_table.get_alias()
    LOG.debug('Building table operation')
    operator = TableOp(parsed_table.get_name(), table_dict, alias)
    LOG.debug('Table operator build: %s', operator)
    # Check if there is a window
    if parsed_table.get_window() is not None:
        LOG.debug('Building window operation')
        operator = WindowOp(operator, parsed_table.get_window(),
                            parsed_table.get_slide())
        LOG.debug('Window operator build: %s', operator)
    return operator


def build_stream(parsed_cql, table_dict):
    '''
    Build a stream operation
    '''
    LOG.debug('Building stream operation')
    parsed_table = parsed_cql.get_table()
    operator = build_table_window(parsed_table, table_dict)
    stream_operation = parsed_cql.get_stream_operation()
    if stream_operation == 'DSTREAM':
        operator = StreamDeleteOp(operator)
    elif stream_operation == 'ISTREAM':
        operator = StreamInsertOp(operator)  # IGNORE:redefined-variable-type
    else:
        operator = StreamRelationOp(operator)
    LOG.debug('Stream operator build: %s', operator)
    return operator


def build_simple_plan(parsed_query, table_dict, conf):
    '''
    Build plan from a simple query
    (below simple preference and select operator)
    '''
    operator = None
    parsed_table_list = parsed_query.get_parsed_tables()
    # Check if there is just one table
    if len(parsed_table_list) == 1:
        operator = build_table_window(parsed_table_list[0], table_dict)
    else:
        table_list = []
        for parsed_table in parsed_table_list:
            table_list.append(build_table_window(parsed_table, table_dict))
        # Build join operation
        operator = JoinOp(table_list, parsed_query.get_join_conditions())
    # Check if there exists select operation
    select_cond_list = parsed_query.get_selection_conditions()
    if len(select_cond_list):
        select_connector = parsed_query.get_selection_connector()
        operator = SelectionOp(operator, select_cond_list,
                               select_connector)
    # Check if there exists preference operation
    parsed_rule_list = parsed_query.get_preferences()
    if len(parsed_rule_list):
        cptheory = build_cptheory(parsed_rule_list,
                                  operator, conf.get_pref_alg())
        operator = PreferenceOp(operator, cptheory, conf.get_pref_alg(),
                                parsed_query.get_top())
    operator = ProjectionOp(operator, parsed_query.get_selected(),
                            parsed_query.get_group_by())
    if parsed_query.is_distinct():
        operator = DistinctOp(operator)
    return operator


def build_bag(query, table_dict, conf):
    '''
    Build bag operations if there exists and below operations
    '''
    operator = None
    if len(query) == 1:
        operator = build_simple_plan(query[0], table_dict, conf)
    else:
        new_list = []
        # Build simple queries
        for item in query:
            if item not in BAG_SYM_SET:
                new_item = build_simple_plan(item, table_dict, conf)
            else:
                new_item = item
            new_list.append(new_item)
        # Bag operations over simples queries
        while len(new_list) > 1:
            operand1 = new_list.pop(0)
            bag_operation = new_list.pop(0)
            operand2 = new_list.pop(0)
            LOG.debug('Building bag operation')
            if bag_operation == UNION_SYM:
                operator = BagUnionOp(operand1, operand2)
                LOG.debug('Bag operation builded: %s', operator)
            elif bag_operation == INTERSECT_SYM:
                operator = BagIntersectOp(operand1, operand2)
                LOG.debug('Bag operation builded: %s', operator)
            else:
                operator = BagExceptOp(operand1, operand2)
                LOG.debug('Bag operation builded: %s', operator)
            new_list.insert(0, operator)
    return operator


def build_plan(parsed_cql, table_dict, conf):
    '''
    Build a plan from parser
    '''
    if isinstance(parsed_cql, ParsedSequenceQuery):
        operator = build_sequence(parsed_cql, table_dict, conf)
    elif isinstance(parsed_cql, ParsedStreamQuery):
        operator = build_stream(parsed_cql, table_dict)
    else:
        operator = build_bag(parsed_cql, table_dict, conf)
    return operator
