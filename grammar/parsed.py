# -*- coding: utf-8 -*-
'''
Module for parsed structures
'''
# StreamPref import
from grammar.symbols import MULTI_OP, DOT, AS_SYM, EQUAL_OP, \
    TABLE_SYM, STREAM_SYM, AND_SYM, OR_SYM
from preference.interval import Interval


def convert_size(size, unit):
    '''
    Convert size (with unit) to seconds
    '''
    from grammar.symbols import MINUTE_SYM, HOUR_SYM, DAY_SYM
    if len(unit):
        if unit == MINUTE_SYM:
            size *= 60
        elif unit == HOUR_SYM:
            size *= 3600
        elif unit == DAY_SYM:
            size *= 86400
    return size


# This class is useful to separate attributes from strings
class ParsedAttribute(object):
    '''
    class to represent parsed attributes
    '''
    def __init__(self, parsed_term):
        self._name = parsed_term.attribute_name
        self._table = None
        if len(parsed_term.table_name):
            self._table = parsed_term.table_name

    def get_name(self):
        '''
        Return attribute name
        '''
        return self._name

    def get_table(self):
        '''
        Return attribute table
        '''
        return self._table

    def get_fullname(self):
        '''
        Return full name of attribute in string format
        '''
        if self._table is not None:
            return '{t}.{n}'.format(t=self._table, n=self._name)
        else:
            return '{n}'.format(n=self._name)

    def __str__(self):
        return self.get_fullname()

    def __repr__(self):
        return self.__str__()


# This class is useful to detect SELECT *
class ParsedSelectTerm(object):
    '''
    class to represent attributes
    '''
    def __init__(self, parsed_term):
        self._table = self._expression = self._alias = None
        # Check if term is * or Table.*
        if len(parsed_term.all):
            if len(parsed_term.all.table):
                self._table = parsed_term.all.table
            self._expression = MULTI_OP
        # Term is an expression
        else:
            self._expression = parsed_term.expression
            if len(parsed_term.alias):
                self._alias = parsed_term.alias

    def get_alias(self):
        '''
        Return alias
        '''
        return self._alias

    def get_expression(self):
        '''
        Return expression
        '''
        return self._expression

    def get_all_table(self):
        '''
        Return table of all attributes
        '''
        return self._table

    def __str__(self):
        term_str = 'TERM('
        if self._expression == MULTI_OP:
            if self._table is not None:
                term_str += self._table + DOT + MULTI_OP
            else:
                term_str += MULTI_OP
        else:
            term_str += str(self._expression)
            if self._alias is not None:
                term_str += ' ' + AS_SYM + ' ' + str(self._alias)
        return term_str + ')'

    def __repr__(self):
        return self.__str__()


# This class is useful to calculate correct window ranges and slides
class ParsedTable(object):
    '''
    class to represent tables
    '''
    def __init__(self, parsed_term):
        self._name = parsed_term.table_name
        self._alias = None
        self._window = None
        self._slide = None
        if len(parsed_term.alias):
            self._alias = parsed_term.alias
        if len(parsed_term.range_slide):
            self._window, self._slide = \
                _get_range_slide(parsed_term.range_slide)

    def get_name(self):
        '''
        Return name
        '''
        return self._name

    def get_alias(self):
        '''
        Return alias
        '''
        return self._alias

    def get_window(self):
        '''
        Return window
        '''
        return self._window

    def get_slide(self):
        '''
        Return slide
        '''
        return self._slide

    def __str__(self):
        str_table = 'TAB({n})'.format(n=self._name)
        if self._alias is not None:
            str_table += '(' + str(self._alias) + ')'
        if self._window is not None:
            str_win = str(self._window)
            if self._slide is not None:
                str_win += ',' + str(self._slide)
            str_table += 'W(' + str_win + ')'
        return str_table

    def __repr__(self):
        return self.__str__()


class ParsedPredicate(object):
    '''
    Class to represent parsed predicates
    '''

    def __init__(self, parsed_term):
        self._attribute = parsed_term.attribute
        # attribute <operator> value
        if len(parsed_term.operator):
            self._interval = Interval([parsed_term.operator,
                                       parsed_term.value])
        # value <operator> attribute <operator> value
        else:
            self._interval = Interval([parsed_term.left_value,
                                       parsed_term.left_operator,
                                       parsed_term.right_operator,
                                       parsed_term.right_value])

    def __str__(self):
        predicate_str = ''
        if self._interval.left_value() is not None:
            predicate_str += str(self._interval.left_value())
        else:
            predicate_str += '-INF'
        predicate_str += ' ' + self._interval.left_operator() + \
            ' ' + str(self._attribute) + ' ' + \
            self._interval.right_operator() + ' '
        if self._interval.right_value() is not None:
            predicate_str += str(self._interval.right_value())
        else:
            predicate_str += '+INF'
        return '({p})'.format(p=predicate_str)

    def __repr__(self):
        return self.__str__()

    def get_attribute(self):
        '''
        Return the predicate attribute
        '''
        return self._attribute

    def get_interval(self):
        '''
        Return the predicate interval
        '''
        return self._interval


# This class is useful to pre-process temporal predicates
class ParsedTemporalPredicate(object):
    '''
    Class to represent a past predicate

    Past predicate are like:
        <simple-predicate>
        FIRST
        [[ALL | SOME] PREVIOUS] <simple-predicate>
    '''

    def __init__(self, parsed_term):
        from grammar.symbols import FIRST_SYM, PREVIOUS_SYM, \
            SOME_SYM, ALL_SYM
        self._operator_list = []
        self._predicate = None
        if len(parsed_term.first):
            self._operator_list = [FIRST_SYM]
        else:
            self._predicate = parsed_term.predicate
            if len(parsed_term.previous):
                self._operator_list = [PREVIOUS_SYM]
                if len(parsed_term.some):
                    self._operator_list.insert(0, SOME_SYM)
                elif len(parsed_term.all):
                    self._operator_list.insert(0, ALL_SYM)

    def __str__(self):
        return '{o}{p}'.format(o=self._operator_list,
                               p=self._predicate)

    def __repr__(self):
        return self.__str__()

    def get_predicate(self):
        '''
        Return the predicate
        '''
        return self._predicate

    def get_past_operator_list(self):
        '''
        Return the past operators
        '''
        return self._operator_list


# This class is useful to pre-process preference rules
class ParsedRule(object):
    '''
    Class to represent a conditional preference rule
    '''
    def __init__(self, parsed_term):
        self._condition_list = []
        self._best = parsed_term.preference.best
        self._worst = parsed_term.preference.worst
        self._indifferent_list = []
        if len(parsed_term.condition):
            self._condition_list = parsed_term.condition
        if len(parsed_term.indifferent):
            self._indifferent_list = parsed_term.indifferent

    def __str__(self):
        rule_str = ''
        if len(self._condition_list):
            rule_str = 'IF' + ' ' + str(self._condition_list) + \
                ' ' + 'THEN' + ' '
        rule_str += str(self._best) + ' BETTER ' + str(self._worst)
        if len(self._indifferent_list):
            rule_str += ' ' + 'INDIFF(' + \
                str(self._indifferent_list) + ')'
        return 'RULE({c})'.format(c=rule_str)

    def __repr__(self):
        return self.__str__()

    def get_condition_list(self):
        '''
        Return condition list
        '''
        return self._condition_list

    def get_best_interval(self):
        '''
        Return best values
        '''
        return self._best

    def get_worst_interval(self):
        '''
        Return worst values
        '''
        return self._worst

    def get_indifferent_list(self):
        '''
        Return indifferent attribute list
        '''
        return self._indifferent_list


class ParsedStreamQuery(object):
    '''
    Class to represent a stream query
    '''
    def __init__(self, parsed_term):
        self._stream_operation = parsed_term.stream_operation
        self._table = parsed_term.table

    def __str__(self):
        query_str = 'STREAM OPERATION: ' + str(self._stream_operation)
        query_str += '\nTABLE: ' + str(self._table)
        return query_str

    def __repr__(self):
        return self.__str__()

    def get_stream_operation(self):
        '''
        Return stream operation
        '''
        return self._stream_operation

    def get_table(self):
        '''
        Return table
        '''
        return self._table


class ParsedSimpleQuery(object):  # IGNORE:too-many-instance-attributes
    '''
    Class to represent a simple query (without bag operations)
    '''
    def __init__(self, parsed_term):
        select = parsed_term.select_clause
        self._selected = list(select.selected)
        self._tables = list(parsed_term.from_clause)
        self._selection_conditions = []
        self._join_conditions = []
        self._select_connector = None
        # Check if there is WHERE clause
        if len(parsed_term.where_clause):
            # Consider first WHERE condition
            cond_list = [parsed_term.where_clause]
            # Suppose connector AND
            self._select_connector = AND_SYM
            # Check if connector is OR
            if len(parsed_term.where_or):
                self._select_connector = OR_SYM
                self._selection_conditions = cond_list + \
                    list(parsed_term.where_or)
            else:
                if len(parsed_term.where_and):
                    cond_list += list(parsed_term.where_and)
                self._separate_conditions(cond_list)
        self._group_by = None
        if len(parsed_term.group_clause):
            self._group_by = parsed_term.group_clause
        self._top = -1
        self._distinct = False
        if len(parsed_term.distinct):
            self._distinct = True
        if len(select.top):
            self._top = int(select.top)
        self._preferences = parsed_term.preference_clause

    def _separate_conditions(self, parsed_conditions):
        '''
        Separate join conditions and selection conditions
        '''
        for cond in parsed_conditions:
            # Join condition has the format ATT = ATT
            if len(cond) == 3 \
                    and isinstance(cond[0], ParsedAttribute) \
                    and cond[1] == EQUAL_OP \
                    and isinstance(cond[2], ParsedAttribute):
                self._join_conditions.append(cond)
            else:
                cond = list(cond)
                self._selection_conditions.append(cond)

    def __str__(self):
        query_str = ''
        if self.is_distinct():
            query_str += 'DISTINCT '
        query_str += 'PROJECTION: ' + str(self._selected)
        if len(self._selection_conditions):
            condition_list = [str(cond) for cond in self._selection_conditions]
            conec = ' ' + self._select_connector + ' '
            query_str += '\nSELECTION:  ' + conec.join(condition_list)
        if len(self._tables) >= 1:
            query_str += '\nTABLES: ' + str(self._tables)
            if len(self._join_conditions):
                condition_list = [str(cond) for cond in self._join_conditions]
                query_str += '\nJOIN: ' + ' AND '.join(condition_list)
        if len(self._preferences):
            if self._top != -1:
                query_str += '\nTOP-K'
            rule_list = [str(rule) for rule in self._preferences]
            query_str += '\nPREFERENCES:\n  ' + '\n  '.join(rule_list)
        if self._group_by is not None:
            query_str += '\nGROUP BY: ' + str(self._group_by)
        return query_str

    def __repr__(self):
        return self.__str__()

    def get_selection_connector(self):
        '''
        Return selection connector
        '''
        return self._select_connector

    def get_selected(self):
        '''
        Return projection parameters
        '''
        return self._selected

    def get_group_by(self):
        '''
        Return group by parameters
        '''
        return self._group_by

    def get_selection_conditions(self):
        '''
        Return selection conditions
        '''
        return self._selection_conditions

    def get_parsed_tables(self):
        '''
        Return tables
        '''
        return self._tables

    def get_join_conditions(self):
        '''
        Return join conditions
        '''
        return self._join_conditions

    def get_top(self):
        '''
        Return True if query is top, otherwise return False
        '''
        return self._top

    def get_preferences(self):
        '''
        Return preferences
        '''
        return self._preferences

    def is_distinct(self):
        '''
        Return True if query has distinct option, otherwise return False
        '''
        return self._distinct


class ParsedSequenceQuery(object):  # IGNORE:too-many-instance-attributes
    '''
    Class to represent a simple query (without bag operations)
    '''
    def __init__(self, parsed_term):
        # Identifier
        self._identifier = list(parsed_term.identifier)
        # Range and slide
        self._range, self._slide = \
            _get_range_slide(parsed_term.range_slide)
        self._consecutive = False
        self._end = False
        # CONSEQ and ENDSEQ
        if len(parsed_term.consecutive_timestamp):
            self._consecutive = True
        if len(parsed_term.end_position):
            self._end = True
        # Table and stream operation
        self._table = parsed_term.table
        self._strem_operation = None
        if len(parsed_term.stream_operation):
            self._strem_operation = parsed_term.stream_operation
        self._alias = None
        # Alias
        if len(parsed_term.alias):
            self._alias = parsed_term.alias
        # MINSEQ and MAXSEQ
        self._min = None
        self._max = None
        if len(parsed_term.where_clause):
            where = parsed_term.where_clause
            if len(where.min):
                self._min = int(where.min)
            if len(where.max):
                self._max = int(where.max)
        # Preferences
        self._top = -1
        if len(parsed_term.top):
            self._top = int(parsed_term.top)
        self._preferences = parsed_term.preference_clause

    def __str__(self):
        query_str = 'SEQUENCE:\n  ID:' + str(self._identifier)
        query_str += '\n  RANGE: ' + str(self._range)
        query_str += '\n  SLIDE: ' + str(self._slide)
        if self._consecutive:
            query_str += '\nCONSECUTIVE'
        if self._end:
            query_str += '\nEND'
        if self._min is not None:
            query_str += '\nMINIMUM SISE: ' + str(self._min)
        if self._max is not None:
            query_str += '\nMAXIMUM SISE: ' + str(self._max)
        if self._preferences is not None:
            if self._top:
                query_str += '\nTOP-K'
            rule_list = [str(rule) for rule in self._preferences]
            query_str += '\nPREFERENCES:\n  ' + '\n  '.join(rule_list)
        if self._strem_operation is not None:
            query_str += '\nSTREAM OPERATION: ' + str(self._strem_operation)
        query_str += '\nTABLE: ' + str(self._table)
        return query_str

    def __repr__(self):
        return self.__str__()

    def get_identifier(self):
        '''
        Return identifier
        '''
        return self._identifier

    def get_range(self):
        '''
        Return range size
        '''
        return self._range

    def get_slide(self):
        '''
        Return range size
        '''
        return self._slide

    def is_consecutive(self):
        '''
        Return True if query has consecutive operator, otherwise return False
        '''
        return self._consecutive

    def is_end(self):
        '''
        Return True if query has end operator, otherwise return False
        '''
        return self._end

    def get_max(self):
        '''
        Return maximum size condition
        '''
        return self._max

    def get_min(self):
        '''
        Return minimum size condition
        '''
        return self._min

    def get_stream_operation(self):
        '''
        Return stream operation
        '''
        return self._strem_operation

    def get_table(self):
        '''
        Return table
        '''
        return self._table

    def get_alias(self):
        '''
        Return alias
        '''
        return self._alias

    def get_top(self):
        '''
        Return True if query is top-k, otherwise return False
        '''
        return self._top

    def get_preferences(self):
        '''
        Return preferences
        '''
        return self._preferences


class ParsedEnvironmentItem(object):
    '''
    Class to represent environment items
    '''
    def __init__(self, parsed_term):
        self._type = parsed_term.type
        self._input_file = parsed_term.input
        self._name = parsed_term.name
        self._attribute_list = []
        self._type_list = []
        self._output_file = None
        self._show_changes = False
        if self._type in [TABLE_SYM, STREAM_SYM]:
            for parsed_att in parsed_term.schema:
                self._attribute_list.append(parsed_att[0])
                self._type_list.append(parsed_att[1])
        else:
            if len(parsed_term.output):
                self._output_file = parsed_term.output
                if len(parsed_term.changes):
                    self._show_changes = True

    def __str__(self):
        item_str = self._type + ' ' + self._name
        item_str += '\nINPUT FILE: ' + self._input_file
        if self._type in [TABLE_SYM, STREAM_SYM]:
            for index, att in enumerate(self._attribute_list):
                item_str += '\n  ' + att + ': ' + self._type_list[index]
        elif self._output_file is not None:
            item_str += '\nOUTPUT FILE: ' + self._output_file
            if self._show_changes:
                item_str += '\nSHOW CHANGES'
        return item_str

    def __repr__(self):
        return self.__str__()

    def get_type(self):
        '''
        Return item type
        '''
        return self._type

    def get_name(self):
        '''
        Return item name
        '''
        return self._name

    def get_input_file(self):
        '''
        Return item input file
        '''
        return self._input_file

    def get_attribute_list(self):
        '''
        Return attribute list
        '''
        return self._attribute_list

    def get_type_list(self):
        '''
        Return list of attribute types
        '''
        return self._type_list

    def get_output_file(self):
        '''
        Return item output file
        '''
        return self._output_file

    def is_show_changes(self):
        '''
        Return True, if item has show changes, otherwise return false
        '''
        return self._show_changes


def _get_range_slide(range_slide):
    '''
    Get range and slide from a range parsed term
    '''
    range_size = 1
    slide_size = 1
    if len(range_slide.now):
        range_size = 1
        slide_size = 1
    elif len(range_slide.unbounded):
        range_size = -1
        slide_size = 1
    else:
        range_size = convert_size(range_slide.range_size,
                                  range_slide.range_unit)
        if len(range_slide.slide_size):
            slide_size = convert_size(range_slide.slide_size,
                                      range_slide.slide_unit)
    return (int(range_size), int(slide_size))
