# -*- coding: utf-8 -*-
'''
Module to represent attributes
'''


class Attribute(object):
    '''
    Class to represent attributes
    '''
    def __init__(self, name, data_type, table=None):
        # Attribute name
        self._name = name
        # Data type
        self._data_type = data_type
        # table
        self._table = table
        # Link to another attribute (used in projection and join)
        self._link = None
        # Function (used in aggregation)
        self._function = None

    def get_name(self):
        '''
        Get the attribute name
        '''
        return self._name

    def get_table(self):
        '''
        Get the attribute table
        '''
        return self._table

    def key(self):
        '''
        Key for attribute (table.name or just name if table is None)
        '''
        if self._table is not None:
            return self._table + '.' + self._name
        else:
            return self._name

    def get_data_type(self):
        '''
        Return attribute data type
        '''
        return self._data_type

    def set_link(self, link):
        '''
        Set attribute link
        '''
        self._link = link

    def link(self):
        '''
        Get attribute link
        '''
        return self._link

    def __str__(self):
        return self.key()

    def __repr__(self):
        if self._link is None:
            return self.key()
        else:
            return self.key() + '({lin})'.format(lin=str(self._link))

    def __cmp__(self, other):
        if not isinstance(self, Attribute) or \
                not isinstance(other, Attribute):
            return 1
        else:
            return cmp(self.key(), self.key())

    def __eq__(self, other):
        return isinstance(self, Attribute) and \
            isinstance(other, Attribute) and \
            self.key() == other.key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __hash__(self):
        return hash(self.key())
