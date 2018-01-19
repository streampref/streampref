# -*- coding: utf-8 -*-
'''
Module with operators
'''

from abc import abstractmethod
import logging

from grammar.parsed import ParsedAttribute
from grammar.symbols import INTEGER_SYM, FLOAT_SYM, STRING_SYM, \
    TABLE_SYM, LESS_OP, LESS_EQUAL_OP, GREATER_OP, GREATER_EQUAL_OP, \
    EQUAL_OP, DIFFERENT_OP, CURRENT_SYM, MULTI_OP, TS_SYM, NOT_SYM,\
    AGGREGATE_FUNCTIONS_SET, MAX_SYM, MIN_SYM, SUM_SYM, COUNT_SYM, AND_SYM,\
    OR_SYM
from control.attribute import Attribute


LOG = logging.getLogger(__name__)


class Operator(object):  # IGNORE:too-many-instance-attributes
    '''
    Interface for all operators
    '''
    def __init__(self):
        # Operand list
        self._operand_list = []
        # Result type (STREAM or TABLE)
        self._result_type = TABLE_SYM
        # Father operator
        self._father = None
        # Attribute list
        self._attribute_list = []
        # Operator name
        self._operator_name = '?'
        # Operator string
        self._operator_str = '?'
        # Timestamp
        self._timestamp = -1
        # Lists of records in current timestamp
        self._current_list = []
        # List of records in previous timestamp
        self._previous_list = []

    def is_consistent(self):
        '''
        Check if operator is consistent
        Must be improved by specific operators
        '''
        # The operator is consistent if all its operands are consistent
        for operand in self._operand_list:
            if not operand.is_consistent():
                return False
        # And if all attributes are valid
        for att in self._attribute_list:
            if att is None or att.get_data_type() is None:
                LOG.error('Operator %s not consistent', self)
                LOG.error('Invalid attribute: %s', att)
                return False
        return True

    def get_attribute_list(self):
        '''
        Get the attribute list
        '''
        return self._attribute_list

    def set_father(self, father):
        '''
        Set the operator father
        '''
        self._father = father

    def get_result_type(self):
        '''
        Get the operator result type
        '''
        return self._result_type

    def find_attribute(self, attribute_name, table_name):
        '''
        Return an attribute if just one matches with searched
        Else return 'None'
        '''
        att_list = []
        for att in self._attribute_list:
            # Check if table name and attribute name matches
            # Or just attribute matches when table name is None
            if (attribute_name == att.get_name() and
                table_name == att.get_table()) or \
                    (table_name is None and
                     attribute_name == att.get_name()):
                att_list.append(att)
        # Check if just one attribute matches
        if len(att_list) == 1:
            return att_list[0]
        else:
            return None

    def get_deleted_list(self):
        '''
        Return just removed records
        '''
        from operators.bag import bag_except
        return bag_except(self._previous_list, self._current_list)

    def get_inserted_list(self):
        '''
        Return just inserted records
        '''
        from operators.bag import bag_except
        return bag_except(self._current_list, self._previous_list)

    def get_current_list(self):
        '''
        Return just current records
        '''
        return self._current_list

    def get_timestamp(self):
        '''
        Return current operator timestamp
        '''
        return self._timestamp

    def can_run(self, timestamp):
        '''
        Check if operator can run
        '''
        # Check if operator is already executed in specified timestamp
        if self._timestamp >= timestamp:
            return False
        # Check if all operator operands are already executed
        for operand in self._operand_list:
            if operand.get_timestamp() != timestamp:
                return False
        # Copy current lit to previous list
        self._previous_list = self._current_list
        self._current_list = []
        # Sync timestamp
        self._timestamp = timestamp
        return True

    def debug_run(self):
        '''
        Debug operator run
        '''
        if LOG.isEnabledFor(logging.DEBUG):
            LOG.debug('%s executed at timestamp %s',
                      self._operator_str, self._timestamp)
            str_list = [str(item) for item in self._previous_list]
            LOG.debug(self._operator_str +
                      ' - Previous: (' + str(len(str_list)) + ')\n' +
                      '\n'.join(str_list))
            str_list = [str(item) for item in self.get_inserted_list()]
            LOG.debug(self._operator_str +
                      ' - Inserted: (' + str(len(str_list)) + ')\n' +
                      '\n'.join(str_list))
            str_list = [str(item) for item in self.get_deleted_list()]
            LOG.debug(self._operator_str +
                      ' - Deleted: (' + str(len(str_list)) + ')\n' +
                      '\n'.join(str_list))
            str_list = [str(item) for item in self.get_current_list()]
            LOG.debug(self._operator_str +
                      ' - Current: (' + str(len(str_list)) + ')\n' +
                      '\n'.join(str_list))

    def run_father(self, timestamp):
        '''
        Run operator father, if it exists
        '''
        if self._father is not None:
            self._father.run(timestamp)

    @abstractmethod
    def run(self, timestamp):
        '''
        Must be override
        '''
        raise NotImplementedError('Run method not implemented')

    def _add_attribute(self, attribute_name, data_type, table=None):
        '''
        Add attribute
        '''
        att = Attribute(attribute_name, data_type, table)
        self._attribute_list.append(att)
        return self._attribute_list[-1]

    def __str__(self):
        if len(self._operand_list):
            str_operand_list = [str(op) for op in self._operand_list]
            return self._operator_str + '(' + ', '.join(str_operand_list) + ')'
        else:
            return self._operator_str
        return self._operator_str

    def __repr__(self):
        #         return self.__str__()
        return self._operator_str


class UnaryOp(Operator):
    '''
    Unary operator
    '''
    def __init__(self, operand):
        Operator.__init__(self)
        # Just one operand
        self._operand_list = [operand]
        self._operand = operand
        # Attributes are the same of operand
        self._attribute_list = operand.get_attribute_list()
        operand.set_father(self)

    def is_consistent(self):
        '''
        Check if operator is consistent

        Check if operator has just two operands
        Check if operands are consistent
        '''
        if not Operator.is_consistent(self):
            return False
        if len(self._operand_list) != 1:
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    @abstractmethod
    def run(self, timestamp):
        '''
        Must be override
        '''
        raise NotImplementedError('Run method not implemented')


class TableOp(Operator):  # IGNORE:too-many-instance-attributes
    '''
    Table operator
    '''
    def __init__(self, parsed_name, table_dict, alias=None):
        Operator.__init__(self)
        self._operator_name = 'TABLE'
        self._operator_str = 'TABLE[???]'
        # List of records inserted
        self._inserted_list = []
        # List of records deleted
        self._deleted_list = []
        # Define name (when table is renamed) and table name
        self._table_name = self._name = parsed_name
        # Default result type is TABLE
        self._result_type = TABLE_SYM
        if alias is not None:
            self._name = alias
        self._table = None
        # Check if table is in table dictionary
        if self._table_name in table_dict:
            self._table = table_dict[self._table_name]
            # Add consumers in table
            self._table.add_consumer(self)
            self._result_type = self._table.get_result_type()
            self._operator_name = 'TABLE[{n}({t})]'.\
                format(n=self._name, t=self._table_name)
            self._operator_str = 'TABLE[name={n}, {r}={t}]'.\
                format(r=self._result_type, n=self._name,
                       t=self._table_name)
            # Get attributes from table
            for att in self._table.get_attribute_list():
                # Attributes use the renamed name
                self._add_attribute(att.get_name(), att.get_data_type(),
                                    table=self._name)

    def get_name(self):
        '''
        Return the name (or renamed name) of the table
        '''
        return self._name

    def is_consistent(self):
        if self._table is None:
            LOG.error('Invalid table: %s', self._table_name)
            LOG.error('Operator %s not consistent', self)
            return False
        return True

    def run(self, timestamp):
        if self._table.get_timestamp() == timestamp \
                and self._timestamp < timestamp:
            self._timestamp = timestamp
            self._inserted_list = []
            self._current_list = []
            self._deleted_list = []
            # Get records from table
            rec_list = self._table.get_current_list()
            self._current_list = _map_from_table(rec_list,
                                                 self._attribute_list)
            rec_list = self._table.get_inserted_list()
            self._inserted_list = _map_from_table(rec_list,
                                                  self._attribute_list)
            rec_list = self._table.get_deleted_list()
            self._deleted_list = _map_from_table(rec_list,
                                                 self._attribute_list)
            self.debug_run()
            self.run_father(timestamp)

    def get_inserted_list(self):
        return self._inserted_list

    def get_deleted_list(self):
        return self._deleted_list


class SelectionOp(UnaryOp):
    '''
    Selection operator
    '''
    def __init__(self, operand, where_list, selection_connector):
        UnaryOp.__init__(self, operand)
        # Initialize selection conditions
        self._condition_list = []
        self._selection_connector = selection_connector
        self._build_select_conditions(where_list)
        self._operator_name = 'SELECT'
        self._operator_str = 'SELECT[{c}]'.format(c=str(self._condition_list))

    def _build_select_conditions(self, where_list):
        '''
        Build join conditions from where_list
        '''
        for cond in where_list:
            # Check if a condition has NOT
            not_term = cond.pop(0)
            if not_term == NOT_SYM:
                cond.append(not_term)
            else:
                cond.insert(0, not_term)
            term1 = cond[0]
            # Check if first term is a parsed attribute
            if isinstance(term1, ParsedAttribute):
                term1 = self.find_attribute(term1.get_name(),
                                            term1.get_table())
            # Check if first term is an expression
            elif not is_value(term1):
                term1 = Expression(term1, self)
            term2 = cond[2]
            # Check second term is a parsed attribute
            if isinstance(term2, ParsedAttribute):
                term2 = self.find_attribute(term2.get_name(),
                                            term2.get_table())
            # Check if second term is an expression
            elif not is_value(term2):
                term2 = Expression(term2, self)
            if len(cond) == 3:
                new_cond = [term1, cond[1], term2]
            elif len(cond) == 4:
                new_cond = [term1, cond[1], term2, NOT_SYM]
            self._condition_list.append(new_cond)

    def is_consistent(self):
        if not Operator.is_consistent(self):
            return False
        for cond in self._condition_list:
            if cond[0] is None or cond[2] is None:
                LOG.error('Operator %s not consistent', self)
                LOG.error('Invalid condition: %s', cond)
                return False
        return True

    def _is_valid_record_and(self, record, timestamp):
        '''
        Check if record is validated by all conditions (AND)
        '''
        for cond in self._condition_list:
            # Condition without NOT
            if len(cond) == 3 \
                    and not _is_valid_by_condition(record, cond, timestamp):
                return False
            # Condition with NOT
            elif len(cond) == 4 \
                    and _is_valid_by_condition(record, cond, timestamp):
                return False
        return True

    def _is_valid_record_or(self, record, timestamp):
        '''
        Check if record is validated by any conditions (OR)
        '''
        for cond in self._condition_list:
            # Condition without NOT
            if len(cond) == 3 \
                    and _is_valid_by_condition(record, cond, timestamp):
                return True
            # Condition with NOT
            elif len(cond) == 4 \
                    and not _is_valid_by_condition(record, cond, timestamp):
                return True
        return False

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._current_list = []
            if self._selection_connector == AND_SYM:
                for rec in self._operand.get_current_list():
                    if self._is_valid_record_and(rec, timestamp):
                        self._current_list.append(rec)
            elif self._selection_connector == OR_SYM:
                for rec in self._operand.get_current_list():
                    if self._is_valid_record_or(rec, timestamp):
                        self._current_list.append(rec)
            self.debug_run()
            self.run_father(timestamp)


class ProjectionOp(UnaryOp):
    '''
    Projection operator
    '''
    def __init__(self, operand, select_list, group_by_list):
        UnaryOp.__init__(self, operand)
        # Attribute list will be rebuild
        self._attribute_list = []
        # Values to value attributes
        self._value_dict = {}
        # List of attributes to group aggregation
        self._grouping_attribute_list = []
        # Aggregation function
        self._aggregation_function = None
        # Attribute to compute aggregation over it
        self._aggregation_attribute = None
        # Build attribute list with selected attributes
        self._build_simple_attribute_list(select_list)
        # Check if there is GROUP BY clause
        if group_by_list is not None:
            # Build aggregation structure
            self._build_aggregations(group_by_list)
        if self._aggregation_function is None:
            str_att_list = [str(att) for att in self._attribute_list]
            attributes_str = ','.join(str_att_list)
        else:
            str_att_list = [str(att) for att in self._grouping_attribute_list]
            attributes_str = ','.join(str_att_list) + ', ' + \
                self._aggregation_function + \
                '(' + str(self._aggregation_attribute) + ')'
        self._operator_name = 'PROJECT'
        self._operator_str = 'PROJECT[{a}]'\
            .format(a=attributes_str)

    def _validate_attribute_name(self, name, alias):
        '''
        Validate the attribute name
        '''
        # Check if name is empty
        if name is None:
            name = 'ATT'
        # Check if attribute was renamed
        if alias is not None:
            name = alias
        # Rename duplicated attributes
        count = 2
        while self.find_attribute(name, None) is not None:
            name = name + '_' + str(count)
            count += 1
        return name

    def _add_value_attribute(self, value, alias=None):
        '''
        Add a value as an attribute
        '''
        # Get attribute type
        expression = Expression(value, self._operand)
        att_type = expression.get_type()
        # Add attribute
        name = expression.get_name()
        name = self._validate_attribute_name(name, alias)
        att = self._add_attribute(name, att_type)
        # Set attribute expression
        self._value_dict[att] = expression

    def _build_simple_attribute_list(self, select_list):
        '''
        Build attribute list
        '''
        for term in select_list:
            # Get expression
            expression = term.get_expression()
            # Check if term is * or <table>.*
            if expression == MULTI_OP:
                term_table = term.get_all_table()
                # Term is <table>.*
                if term_table is not None:
                    att_list = []
                    for att in self._operand.get_attribute_list():
                        if att.get_table() == term_table:
                            att_list.append(att)
                # Term is *
                else:
                    att_list = self._operand.get_attribute_list()
                for att in att_list:
                    self._add_value_attribute(att, att.get_name())
            # Check if expression is _TS attribute
            elif str(expression) == TS_SYM:
                self._add_value_attribute(CURRENT_SYM, term.get_alias())
            else:
                self._add_value_attribute(expression, term.get_alias())

    def _build_aggregations(self, group_list):
        '''
        Build attribute list using group by attributes
        '''
        # Map grouping attributes
        for parsed_att in group_list:
            att = self._operand.find_attribute(parsed_att.get_name(),
                                               parsed_att.get_table())
            for proj_att, expr in self._value_dict.items():
                if att == expr.get_expression_attribute():
                    att = proj_att
            self._grouping_attribute_list.append(att)
        # Select aggregation attributes and function
        for att in self._value_dict:
            expression = self._value_dict[att]
            aggreg_func = expression.get_aggregation()
            if aggreg_func is not None:
                self._aggregation_function = aggreg_func
                self._aggregation_attribute = att
                break

    def is_consistent(self):  # IGNORE:too-many-return-statements
        if not UnaryOp.is_consistent(self) \
                or self._operand.get_result_type() != TABLE_SYM:
            return False
        # Check if some attribute or type is invalid
        for att in self._attribute_list:
            if att is None or att.get_data_type() is None:
                LOG.error('Operator %s not consistent', self)
                return False
        # Check if there is group by Clause
        if len(self._grouping_attribute_list):
            # The grouping attributes must be valid
            if None in self._grouping_attribute_list:
                LOG.error('Operator %s not consistent', self)
                LOG.error('Invalid attribute in GROUP BY clause')
                return False
            # The aggregation function must be valid
            if self._aggregation_function is None:
                LOG.error('Operator %s not consistent', self)
                LOG.error('Invalid aggregation function')
                return False
            # The aggregation attribute must be valid
            att = self._aggregation_attribute
            if att is None or att.get_data_type() is None:
                LOG.error('Operator %s not consistent', self)
                LOG.error('Invalid aggregation result')
                return False
            # All selected attributes not in aggregation function
            # must be in GROUP BY clause
            for att, expr in self._value_dict.items():
                if expr.get_aggregation() is None \
                        and att not in self._grouping_attribute_list:
                    LOG.error('Operator %s not consistent', self)
                    LOG.error('Selected attribute %s not in GROUP BY clause',
                              att)
                    return False
        # Id there no exists GROUP BY clause
        # then aggregation functions are not allowed
        else:
            for expres in self._value_dict.values():
                if expres.get_aggregation() is not None:
                    LOG.error('Operator %s not consistent', self)
                    LOG.error('Aggregation function without GROUP BY clause')
                    return False
        return True

    def _project(self, record_list):
        '''
        Map attributes of a record list to selected attributes
        '''
        result_list = []
        # Map operand record to selected attributes
        for rec in record_list:
            new_rec = {}
            for att in self._attribute_list:
                expre = self._value_dict[att]
                value = expre.calculate(rec, self._timestamp)
                new_rec[att] = value
            result_list.append(new_rec)
        return result_list

    def _group_project(self):
        '''
        Process aggregation function
        '''
        # Group dictionary
        group_dict = {}
        # For every existing record
        for rec in self._current_list:
            # New record of group attributes
            new_rec = record_projection(rec, self._grouping_attribute_list)
            # Value of aggregation attribute
            value = rec[self._aggregation_attribute]
            # Get record ID
            rec_id = tuple(new_rec.items())
            # Check if there exists this record ID
            if rec_id in group_dict:
                # Previous value
                prev_value = group_dict[rec_id]
                # Sum
                sum_value = prev_value + value
                # Count
                count = prev_value + 1
            else:
                prev_value = value
                sum_value = value
                count = 1
            # Process suitable function
            if self._aggregation_function == MAX_SYM:
                value = max([value, prev_value])
            elif self._aggregation_function == MIN_SYM:
                value = min([value, prev_value])
            elif self._aggregation_function == SUM_SYM:
                value = sum_value
            elif self._aggregation_function == COUNT_SYM:
                value = count
            # Store function result
            group_dict[rec_id] = value
        result_list = []
        # Project grouped records
        for rec_id in group_dict:
            new_rec = dict(rec_id)
            # Include aggregation function result
            new_rec[self._aggregation_attribute] = group_dict[rec_id]
            result_list.append(new_rec)
        return result_list

    def run(self, timestamp):
        if self.can_run(timestamp):
            # Usual project
            self._current_list = \
                self._project(self._operand.get_current_list())
            # Aggregation processing
            if self._aggregation_function is not None:
                self._current_list = \
                    self._group_project()
            self.debug_run()
            self.run_father(timestamp)

    def get_inserted_list(self):
        return self._project(self._operand.get_inserted_list())

    def get_deleted_list(self):
        return self._project(self._operand.get_deleted_list())


class DistinctOp(UnaryOp):
    '''
    Distinct operator
    '''
    def __init__(self, operand):
        UnaryOp.__init__(self, operand)

    def run(self, timestamp):
        if self.can_run(timestamp):
            self._current_list = \
                remove_duplicates(self._operand.get_current_list())
            self.debug_run()
            self.run_father(timestamp)


class OrderByOp(UnaryOp):  # IGNORE:abstract-method
    '''
    Order by operator
    '''
    def __init__(self, operand, attribute_list):
        UnaryOp.__init__(self, operand)
        self._sort_attribute_list = []
        self._build_sort_attribute_list(attribute_list)
        str_att_list = [str(att) for att in self._sort_attribute_list]
        attributes_str = ','.join(str_att_list)
        self._operator_name = 'ORDER BY'
        self._operator_str = 'ORDER BY[{a}]'\
            .format(a=attributes_str)

    def _build_sort_attribute_list(self, parsed_attribute_list):
        '''
        Build parsed attribute list
        '''
        for parsed_att in parsed_attribute_list:
            att = self.find_attribute(parsed_att.get_name(),
                                      parsed_att.get_table())
            self._sort_attribute_list.append(att)


class Expression(object):
    '''
    Class for arithmetic expressions
    '''
    def __init__(self, expression_list, operator):
        self._type = None
        self._operator = operator
        self._aggregation = None
        self._expression = expression_list
        if not isinstance(self._expression, list):
            self._expression = [self._expression]
        if len(self._expression) == 2 and \
                self._expression[0] in AGGREGATE_FUNCTIONS_SET:
            self._aggregation = self._expression[0]
            self._expression = self._expression[-1:]
        self._expression = self._convert(self._expression)
        type_set = self._get_type_set(self._expression)
        if len(type_set) == 1:
            self._type = type_set.pop()

    def __str__(self):
        if self._aggregation is not None:
            expr_str = self._aggregation + ': ' + str(self._expression)
        else:
            expr_str = self._expression
        return str(expr_str)

    def __repr__(self):
        return self.__str__()

    def _convert(self, expr):
        '''
        Convert parsed attributes of expr
        '''
        if isinstance(expr, ParsedAttribute):
            return self._operator.find_attribute(expr.get_name(),
                                                 expr.get_table())
        elif isinstance(expr, list):
            for index, term in enumerate(expr):
                expr[index] = self._convert(term)
        return expr

    def _get_type_set(self, expression):
        '''
        Get a set of type from terms present in the expression
        '''
        type_set = set()
        if isinstance(expression, list):
            for term in expression:
                type_set = type_set.union(self._get_type_set(term))
        else:
            if expression not in ['+', '-', '*', '/']:
                if expression == CURRENT_SYM:
                    type_set.add(INTEGER_SYM)
                elif isinstance(expression, Attribute):
                    type_set.add(expression.get_data_type())
                elif isinstance(expression, int):
                    type_set.add(INTEGER_SYM)
                elif isinstance(expression, float):
                    type_set.add(FLOAT_SYM)
                elif isinstance(expression, str):
                    type_set.add(STRING_SYM)
                else:
                    type_set.add(None)
        return type_set

    def _calc(self, expression, rec, timestamp):
        '''
        Calculate an expression
        '''
        result = None
        if expression == CURRENT_SYM:
            result = timestamp
        elif isinstance(expression, Attribute):
            result = rec[expression]
        elif isinstance(expression, int) or \
                isinstance(expression, float) or \
                isinstance(expression, str):
            result = expression
        # Expression is a list
        else:
            expr = expression[:]
            for index, term in enumerate(expr):
                expr[index] = self._calc(term, rec, timestamp)
            while len(expr) > 1:
                value1 = expr.pop(0)
                operation = expr.pop(0)
                value2 = expr.pop(0)
                if operation == '+':
                    result = value1 + value2
                elif operation == '-':
                    result = value1 - value2
                elif operation == '*':
                    result = value1 * value2
                else:
                    result = value1 / value2
                expr.insert(0, result)
            result = expr[0]
        return result

    def get_name(self):
        '''
        If expression is just one attribute, return the name of this attribute
        Else, return None
        '''
        if len(self._expression) == 1 \
                and isinstance(self._expression[0], Attribute):
            return self._expression[0].get_name()
        else:
            return None

    def get_type(self):
        '''
        Return data type of expression
        '''
        return self._type

    def get_aggregation(self):
        '''
        Return aggregation function of the expression or None
        '''
        return self._aggregation

    def calculate(self, rec, timestamp):
        '''
        Calculate an expression
        '''
        return self._calc(self._expression[:], rec, timestamp)

    def get_expression_attribute(self):
        '''
        Return the own expression if it is a single attribute
        Else return None
        '''
        if len(self._expression) == 1 and \
                isinstance(self._expression[0], Attribute):
            return self._expression[0]
        else:
            return None


def _is_valid_by_condition(record, condition, timestamp):
    '''
    Check if the record validates the condition
    '''
    # Get values and operators
    value1 = condition[0]
    operator = condition[1]
    value2 = condition[2]
    # Check if values are attribute values
    if isinstance(value1, Attribute):
        value1 = record[value1]
    elif isinstance(value1, Expression):
        value1 = value1.calculate(record, timestamp)
    if isinstance(value2, Attribute):
        value2 = record[value2]
    elif isinstance(value2, Expression):
        value2 = value2.calculate(record, timestamp)
    # Check the condition according to operator
    if operator == LESS_OP:
        return value1 < value2
    elif operator == LESS_EQUAL_OP:
        return value1 <= value2
    elif operator == GREATER_OP:
        return value1 > value2
    elif operator == GREATER_EQUAL_OP:
        return value1 >= value2
    elif operator == EQUAL_OP:
        return value1 == value2
    elif operator == DIFFERENT_OP:
        return value1 != value2


def record_projection(record, attribute_list):
    '''
    Build a new record with specified attributes over original record
    '''
    new_rec = {}
    for att in attribute_list:
        new_rec[att] = record[att]
    return new_rec


def _map_from_table(record_list, attribute_list):
    '''
    Copy a record from table e rename attributes using
    table operator name
    '''
    result_list = []
    for rec in record_list:
        new_rec = {}
        for att in attribute_list:
            table_att = Attribute(att.get_name(), att.get_data_type())
            new_rec[att] = rec[table_att]
        result_list.append(new_rec)
    return result_list


def is_value(term):
    '''
    Check if term is a literal value (integer, float or string)
    '''
    return isinstance(term, int) \
        or isinstance(term, float) \
        or isinstance(term, str)


def remove_duplicates(record_list):
    '''
    Eliminate duplicates
    '''
    new_rec_list = []
    for rec in record_list:
        if rec not in new_rec_list:
            new_rec_list.append(rec)
    return new_rec_list
