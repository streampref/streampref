# -*- coding: utf-8 -*-
'''
Module to represent sequences
'''
from grammar.symbols import POS_SYM, INTEGER_SYM
from control.attribute import Attribute


class Sequence(object):
    '''
    Class to represent sequences
    '''
    def __init__(self, identifier_record):
        # Identifier record
        self._identifier_record = identifier_record
        # Number of inserted positions
        self._inserted = 0
        # Number of deleted positions
        self._deleted = 0
        # Sequence position list (one record per position)
        self._position_list = []
        # List of original timestamps
        self._timestamp_list = []
        self._start_end_list = []

    def __str__(self):
        str_list = []
        for index, position in enumerate(self._position_list):
            str_list.append(str(position) + '(' +
                            str(self._timestamp_list[index]) + ')')
        return str(self._identifier_record) + '<' + ', '.join(str_list) + '>'

    def __repr__(self):
        return self.__str__()

    def __len__(self):
        return len(self._position_list)

    def __hash__(self):
        return hash(str(self._position_list))

    def get_position_list(self):
        '''
        Return the list of positions of the sequence
        '''
        return self._position_list

    def get_timestamp_list(self):
        '''
        Return the list of positions of the sequence
        '''
        return self._timestamp_list

    def get_start_end_list(self):
        '''
        Return the list of star and end valid timestamps
        '''
        return self._start_end_list

    def append_position(self, record, timestamp, start, end):
        '''
        Append a record
        '''
        self._position_list.append(record)
        self._timestamp_list.append(timestamp)
        self._start_end_list.append((start, end))
        self._inserted += 1

    def append_sequence(self, sequence):
        '''
        Append all positions of a sequence
        '''
        self._position_list += sequence.get_position_list()
        self._timestamp_list += sequence.get_timestamp_list()
        self._start_end_list += sequence.get_start_end_list()
        self._inserted += len(sequence)

    def delete_expired_positions(self, timestamp):
        '''
        Delete all positions where timestamp
        is less than start timestamp
        '''
        while True:
            if len(self._start_end_list) == 0:
                break
            (start, end) = self._start_end_list[0]
            if not start <= timestamp <= end:
                self.delete_first()
            else:
                break

    def copy(self):
        '''
        Return a copy of the sequence
        '''
        copy = Sequence(self._identifier_record)
        copy.append_sequence(self)
        copy.restart_deleted()
        copy.restart_inserted()
        return copy

    def get_first_different_position(self, other):
        '''
        Search the first different position between two sequences
        '''
        list1 = self._position_list
        list2 = other.get_position_list()
        # Consider smaller sequence
        min_length = min([len(list1), len(list2)])
        # Search for different positions starting by position 1
        for pos in range(min_length):
            if list1[pos] != list2[pos]:
                return pos
        # If no different position was found, return -1
        return -1

    def get_last_position(self):
        '''
        Return the last record of a sequence
        '''
        return self._position_list[-1]

    def get_position(self, position):
        '''
        Return a specified position of the sequence
        '''
        return self._position_list[position]

    def get_timestamp(self, position):
        '''
        Return the timestamp of a specified position of the sequence
        '''
        return self._timestamp_list[position]

    def restart_deleted(self):
        '''
        Return the number of deleted positions and restart this counter
        '''
        deleted = self._deleted
        self._deleted = 0
        return deleted

    def restart_inserted(self):
        '''
        Return the number of inserted positions and restart this counter
        '''
        inserted = self._inserted
        self._inserted = 0
        return inserted

    def get_record_list(self):
        '''
        Get the list of full records

        Full records are position records added by
        identifier plus position attribute
        '''
        result_list = []
        # For each position
        for pos, rec in enumerate(self._position_list):
            new_rec = rec.copy()
            new_rec.update(self._identifier_record)
            pos_att = Attribute(POS_SYM, INTEGER_SYM)
            new_rec[pos_att] = pos + 1
            result_list.append(new_rec)
        return result_list

    def get_ctsubsequences(self):
        '''
        Extract subsequences with consecutive timestamps
        '''
        subseq_list = []
        if len(self._timestamp_list):
            start = 0
            end = 1
            while True:
                previous_ts = self._timestamp_list[end - 1]
                # Check if all timstamps are already processed
                # or if current position has no consecutive timestamp
                if end >= len(self._timestamp_list):
                    subseq_list.append(self.subsequence(start, end - 1))
                    break
                elif self._timestamp_list[end] > previous_ts + 1:
                    subseq_list.append(self.subsequence(start, end - 1))
                    start = end
                end += 1
        return subseq_list

    def get_ep_subsequences(self):
        '''
        Extract subsequences with end positions, the returned list is
        decreasingly sorted by sequence length
        '''
        subseq_list = []
        for pos in range(len(self._position_list)):
            end = len(self)
            subseq_list.append(self.subsequence(pos, end))
        return subseq_list

    def subsequence(self, start_position, end_position):
        '''
        Get a subsequence from start position to end position
        '''
        # Backup positions
        bkp_pos_list = self._position_list[:]
        bkp_ts_list = self._timestamp_list[:]
        bkp_se_list = self._start_end_list[:]
        # Select positions
        end_position += 1
        self._position_list = self._position_list[start_position:end_position]
        self._timestamp_list = self._timestamp_list[start_position:
                                                    end_position]
        self._start_end_list = self._start_end_list[start_position:
                                                    end_position]
        # Build subsequence by copying
        subseq = self.copy()
        # Restore positions
        self._position_list = bkp_pos_list
        self._timestamp_list = bkp_ts_list
        self._start_end_list = bkp_se_list
        return subseq

    def delete_first(self, positions=1):
        '''
        Delete a specified number of positions in the beginning of the sequence
        '''
        del self._position_list[:positions]
        del self._timestamp_list[:positions]
        del self._start_end_list[:positions]
        self._deleted += positions
