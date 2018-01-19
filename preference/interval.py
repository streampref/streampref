# -*- coding: utf-8 -*-
'''
Module to manipulate intervals of values
'''

from grammar.symbols import EQUAL_OP, LESS_OP, GREATER_EQUAL_OP, \
    GREATER_OP


class Interval(object):
    '''
    Interval of values
    '''

    def __init__(self, interval_list):
        # Left and right values
        self._left_value = self._right_value = None
        # Left and right operators
        self._left_operator = self._right_operator = '<='
        # Check if format is: [<operator>, value]
        if len(interval_list) == 2:
            # [=, value]
            if interval_list[0] == '=':
                self._left_operator = self._right_operator = '='
                self._left_value = self._right_value = interval_list[1]
            # [<, value] or [<=, value]
            elif interval_list[0] in ['<', '<=']:
                self._right_operator = interval_list[0]
                self._right_value = interval_list[1]
            # [>, value] or [>=, value]
            else:
                self._left_value = interval_list[1]
                if interval_list[0] == '>':
                    self._left_operator = '<'
                else:
                    self._left_operator = '<='
        # format: [value, <operator>, <operator>, value]
        elif len(interval_list) == 4:
            self._left_value = interval_list[0]
            self._left_operator = interval_list[1]
            self._right_operator = interval_list[2]
            self._right_value = interval_list[3]
        if (self._left_value == self._right_value and
                self._left_value is not None and
                self._right_value is not None and
                self._left_operator == self._right_operator == '<='):
            self._left_operator = self._right_operator = '='

    def __str__(self):
        return str([self._left_value,
                    self._left_operator,
                    self._right_operator,
                    self._right_value])

    def __repr__(self):
        return self.__str__()

    def __cmp__(self, other):
        if not isinstance(other, Interval):
            return 1
        elif self.left_value() == other.left_value() \
                and self.left_operator() == other.left_operator() \
                and self.right_operator() == other.right_operator() \
                and self.right_value() == other.right_value():
            return 0
        elif self.left_value() < other.left_value() \
                or self.right_value() < other.right_value():
            return -1
        else:
            return 1

    def left_value(self):
        '''
        Return left limit
        '''
        return self._left_value

    def left_operator(self):
        '''
        Return left operator
        '''
        return self._left_operator

    def left_closed(self):
        '''
        Return left closed
        '''
        return self._left_operator in ['=', '<=']

    def right_value(self):
        '''
        Return right limit
        '''
        return self._right_value

    def right_operator(self):
        '''
        Return right operator
        '''
        return self._right_operator

    def right_closed(self):
        '''
        Return right closed
        '''
        return self._right_operator in ['=', '<=']

    def is_disjoint(self, other):
        '''
        Check if 'self' is_disjoint 'other'
        '''
        return other.right_inside(self) or other.left_inside(self)

    def left_inside(self, other):
        '''
        Check if 'other' left limit is inside of 'self' interval
        '''
        #  other: (X)---, ( )---
        return (other.left_value() is not None and
                # self: <---
                (self.left_value() is None or
                 # other:   ()-
                 #  self: ()---
                 self.left_value() < other.left_value() or
                 #  self: (X)---
                 # other: ( )---
                 (other.left_value() == self.left_value() and
                     not other.left_closed() and self.left_closed())) and
                # self: --->
                (self.right_value() is None or
                 # other:  ()--
                 #  self: ---()
                 self.right_value() > other.left_value() or
                 # other:   (X)--
                 #  self: --(X)
                 (self.right_value() == other.left_value() and
                     self.right_closed() and other.left_closed())))

    def right_inside(self, other):
        '''
        Check if 'other' right limit is inside of 'self' interval
        '''
        #  other: ---(X), ---( )
        return (other.right_value() is not None and
                # self: --->
                (self.right_value() is None or
                 # other:  -()
                 #  self: ---()
                 self.right_value() > other.right_value() or
                 # other: ---( )
                 #  self: ---(X)
                 (other.right_value() == self.right_value() and
                     not other.right_closed() and self.right_closed())) and
                # self: <---
                (self.left_value() is None or
                 # other:  --()
                 #  self: ()---
                 self.left_value() < other.right_value() or
                 #  self:   (X)--
                 # other: --(X)
                 (self.left_value() == other.right_value() and
                     self.left_closed() and other.right_closed())))

    def split_by_interval(self, other):
        '''
        Split 'self' if 'other' inside right side of 'self'
        '''
        interval_list = []
        # Check if 'other' left limit is inside 'self'
        # other:     |----|
        #  self: |----|
        # split: |--||--|
        if self != other \
                and self.left_inside(other):
            new_righ_operator = '<='
            if other.left_closed():
                new_righ_operator = '<'
            new_interval = Interval([self.left_value(),
                                     self.left_operator(),
                                     new_righ_operator,
                                     other.left_value()])
            interval_list.append(new_interval)
            new_interval = Interval([other.left_value(),
                                     other.left_operator(),
                                     self.right_operator(),
                                     self.right_value()])
            interval_list.append(new_interval)
        # Check if 'other' right limit is inside 'self'
        # other: |----|
        #  self:   |----|
        # split:   |--||--|
        elif self != other \
                and self.right_inside(other):
            new_left_operator = '<='
            if other.right_closed():
                new_left_operator = '<'
            new_interval = Interval([self.left_value(),
                                     self.left_operator(),
                                     other.right_operator(),
                                     other.right_value()])
            interval_list.append(new_interval)
            new_interval = Interval([other.right_value(),
                                     new_left_operator,
                                     self.right_operator(),
                                     self.right_value()])
            interval_list.append(new_interval)
        return interval_list

    def copy(self):
        '''
        Return a copy of interval
        '''
        return Interval([self.left_value(),
                         self.left_operator(),
                         self.right_operator(),
                         self.right_value()])

    def is_consistent(self):
        '''
        Return true if interval is consistent, otherwise return False
        '''
        if self._left_value is not None and self._right_value is not None and \
                self._left_operator in ['<', '<='] and \
                self._right_operator in ['<', '<='] and \
                self._left_value >= self._right_value:
            return False
        else:
            return True

    def _after_left(self, value):
        '''
        Check if value is after left interval limit
        '''
        if self.left_value() is None \
                or self.left_value() < value \
                or (self.left_value() <= value and
                    self.left_closed()):
            return True

    def _before_right(self, value):
        '''
        Check if value is before right interval limit
        '''
        if self.right_value() is None \
                or self.right_value() > value \
                or (self.right_value() >= value and
                    self.right_closed()):
            return True

    def is_inside_or_equal(self, value):
        '''
        Check if value is inside interval
        '''
        # Check if values are equal
        if isinstance(value, Interval):
            if self == value:
                return True
        # Check if value is inside interval
        elif self._after_left(value) and self._before_right(value):
            return True
        return False

    def get_string(self, key):
        '''
        Get a string in the format LV <LO> key <RO> RV
        where LV, LO, RO, RV are interval operators and
        interval values limits
        '''
        if self._left_value is None:
            return str(key) + self._right_operator + str(self._right_value)
        elif self._right_value is None:
            oper = GREATER_EQUAL_OP
            if self._left_operator == LESS_OP:
                oper = GREATER_OP
            return str(key) + oper + str(self._left_value)
        elif self._left_operator == self._right_operator == EQUAL_OP:
            return str(key) + EQUAL_OP + str(self._left_value)
        else:
            return str(self._left_value) + self._left_operator + str(key) + \
                self._right_operator + str(self._right_value)
