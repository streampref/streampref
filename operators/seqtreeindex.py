# -*- coding: utf-8 -*-
'''
Module UpdateLevel classes used by incremental algorithms to get best tuples
'''
import logging

from operators.seqtreehierarchy import PreferenceDict
from operators.seqtree import SeqNode, SeqNodePruning
from control.config import SEQ_ALG_SEQTREE_PRUNING


LOG = logging.getLogger(__name__)


class SeqIndex(object):
    '''
    Class for sequence index
    '''
    def __init__(self, tcptheory, hierarchy_type):
        # Preference hierarchy type
        self._hierarchy_type = hierarchy_type
        # Preference dictionary
        self._pref_dict = PreferenceDict(tcptheory, hierarchy_type)
        # Pruning for dominated nodes
        pruning = hierarchy_type in [SEQ_ALG_SEQTREE_PRUNING]
        if pruning:
            root = SeqNodePruning(None, None, self._pref_dict)
        else:
            root = SeqNode(None, None,  # IGNORE:redefined-variable-type
                           self._pref_dict)  # IGNORE:redefined-variable-type
        self._tree = root
        # Sequence node dictionary: ID -> (sequence, node)
        self._sequence_node_dict = {}

    def _add_sequence(self, sequence):
        '''
        Add a sequence to index
        '''
        # Add sequence to tree and get node where sequence was stored
        node = self._tree.add_sequence_recursive(sequence)
        # Add entry for sequence, node into dictionary
        self._sequence_node_dict[id(sequence)] = (sequence, node)

    def update(self, sequence_list):
        '''
        Update index structure and add a list of new sequences
        '''
        # List of sequences to be inserted, moved and deleted
        insert_list = []
        tomove_list = []
        delete_list = []
        # For each existent sequence
        for seq_id in self._sequence_node_dict:
            # Get sequence and correspondent node
            sequence, node = self._sequence_node_dict[seq_id]
            # Get number of deleted positions of sequence
            deleted = sequence.restart_deleted()
            # Get number of inserted positions into sequence
            inserted = sequence.restart_inserted()
            # Check if there was deleted positions
            if deleted > 0:
                # If yes, the sequence must me deleted from current node
                delete_list.append((sequence, node))
                # If sequence is not empty, it must be inserted again
                if len(sequence):
                    insert_list.append(sequence)
            # Check if there were just insertions
            elif inserted > 0:
                # Sequence must be moved to a child branch of current node
                tomove_list.append((sequence, node))
        # For every input sequence
        for sequence in sequence_list:
            # Check if sequence is not in the index
            # Select just new sequences (those created on last instant)
            if id(sequence) not in self._sequence_node_dict:
                sequence.restart_inserted()
                insert_list.append(sequence)
        # Delete sequences
        for sequence, node in delete_list:
            seq_id = id(sequence)
            node.delete_sequence(sequence)
            del self._sequence_node_dict[seq_id]
        # Insert sequences
        for sequence in insert_list:
            self._add_sequence(sequence)
        # Reinsert sequences
        for sequence, node in tomove_list:
            seq_id = id(sequence)
            new_node = node.add_sequence_recursive(sequence)
            node.delete_sequence(sequence)
            self._sequence_node_dict[seq_id] = (sequence, new_node)
        self._tree.clean_recursive()
        self.debug()

    def get_best_sequences_recursive(self):
        '''
        Return dominant sequences in the index
        '''
        return self._tree.get_best_sequences_recursive()

    def topk_sequences(self, topk):
        '''
        Return the top-k sequences in the index
        '''
        copy_tree = self._tree.copy()
        return copy_tree.topk_sequences(topk)

    def debug(self):
        '''
        Debug Index
        '''
        if LOG.isEnabledFor(logging.DEBUG):
            str_dbg = '\nIndex information'
            str_dbg += '\nHierarchy type: ' + str(self._hierarchy_type)
            str_dbg += '\n\nIndex tree:'
            str_dbg += self._tree.get_tree_string()
            str_dbg += '\n\nHierarchy structure:'
            str_dbg += self._tree.get_hierarchy_string()
            LOG.debug(str_dbg)
