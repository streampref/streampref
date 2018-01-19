'''
Module UpdateLevel classes used by incremental algorithms to get best tuples
'''
import logging


LOG = logging.getLogger(__name__)


class SeqNode(object):  # IGNORE:too-many-instance-attributes
    '''
    Class for tree node
    '''
    def __init__(self, sequence, father, preference_dict,
                 create_hierarchy=True):
        # Node depth is 0 for root node (no father)
        self._depth = 0
        if father is not None:
            self._depth = father.get_depth() + 1
        # Node sequence (None for root)
        self._sequence = None
        if sequence is not None:
            self._sequence = sequence.subsequence(0, self._depth-1)
        # Children nodes dictionary
        # tuple -> node
        self._child_dict = {}
        # Dictionary of sequences stored into node
        # Sequence ID -> sequence
        self._sequence_dict = {}
        # Dictionary of preference theories
        self._preference_dict = preference_dict
        # Check if hierachy must be created
        if create_hierarchy:
            # Create hierarchy
            self._hierarchy = \
                self._preference_dict.get_hierarchy(self._sequence)
        else:
            self._hierarchy = None

    def get_depth(self):
        '''
        Return node depth
        '''
        return self._depth

    def get_sequence(self):
        '''
        Return node sequence
        '''
        return self._sequence

    def get_record(self):
        '''
        Return node record
        '''
        if self._sequence is None:
            return None
        return self._sequence.get_last_position()

    def add_sequence_recursive(self, sequence):
        '''
        Insert a sequence into index
        '''
        # Check if the sequence belongs to current node
        if self._depth == len(sequence):
            # Store sequence into current
            seq_id = id(sequence)
            self._sequence_dict[seq_id] = sequence
            return self
        # Get ID for child
        node_id = get_position_id(sequence, self._depth)
        # Check if child already exists
        if node_id in self._child_dict:
            # Take the existing child
            node = self._child_dict[node_id]
        else:
            # Create a new child
            node = self._new_child(sequence, node_id)
        # Add sequence do correspondent child node
        return node.add_sequence_recursive(sequence)

    def _new_child(self, sequence, node_id):
        '''
        Create a new child using the sequence
        '''
        # Create node structure
        child = SeqNode(sequence, self, self._preference_dict)
        # Add node to children
        self._child_dict[node_id] = child
        # Get node record
        record = child.get_record()
        # Add node record to hierarchy
        self._hierarchy.add(record)
        return child

    def is_empty(self):
        '''
        Return True, if node has no sequences or child
        '''
        return not len(self._sequence_dict) and not len(self._child_dict)

    def delete_sequence(self, sequence):
        '''
        Delete a sequence from node
        '''
        # Get sequence ID
        seq_id = id(sequence)
        # Remove sequence from node
        del self._sequence_dict[seq_id]

    def get_id(self):
        '''
        Return node ID
        '''
        rec = self.get_record()
        if rec is not None:
            return tuple(rec.items())
        else:
            return None

    def _del_child(self, child):
        '''
        Remove a child node
        '''
        # Remove child node
        child_id = child.get_id()
        del self._child_dict[child_id]
        # Remove node from hierarchy
        child_rec = child.get_record()
        self._hierarchy.delete(child_rec)

    def clean_recursive(self):
        '''
        Remove empty nodes from child branches
        '''
        del_list = []
        # For every child
        for child in self._child_dict.values():
            # Recursive call
            child.clean_recursive()
            # Check if child is empty
            if child.is_empty():
                del_list.append(child)
        for child in del_list:
            # Remove child
            self._del_child(child)

    def _update_copy(self, node):
        '''
        Update node copy
        '''
        # Create a copy of sequences dictionary
        seq_dict_copy = self._sequence_dict.copy()
        # Create a copy of children dictionary
        child_dict_copy = self._child_dict.copy()
        # Copy every child of child dictionary
        for child_id, child_node in child_dict_copy.items():
            child_copy = child_node.copy()
            self._child_dict[child_id] = child_copy
        # Create a copy of hierarchy
        hierarchy_copy = None
        if self._hierarchy is not None:
            hierarchy_copy = self._hierarchy.copy()
        # Update copy
        node.__dict__.update(self.__dict__)
        # Restore previous values for children and hierarchy
        self._sequence_dict = seq_dict_copy
        self._child_dict = child_dict_copy
        self._hierarchy = hierarchy_copy
        # Return copy
        return node

    def copy(self):
        '''
        Create a copy of node
        '''
        # Create a new node
        node = SeqNode(self._sequence, None, self._preference_dict)
        return self._update_copy(node)

    def get_dominant_children(self):
        '''
        Get dominant children
        '''
        id_list = self._hierarchy.get_best()
        return [self._child_dict[child_id] for child_id in id_list]

    def get_best_sequences_recursive(self):
        '''
        Return best (dominant) sequences in the tree
        '''
        # Get sequences from current node
        seq_list = self._sequence_dict.values()
        for child in self.get_dominant_children():
            seq_list += child.get_best_sequences_recursive()
        return seq_list

    def remove_dominant_sequences(self):
        '''
        Remove and return dominant sequences
        Empty nodes are deleted during the process
        '''
        # Get sequences from current node
        seq_list = self._sequence_dict.values()[:]
        # Remove node sequences
        self._sequence_dict.clear()
        # For every dominant child node
        for child in self.get_dominant_children():
            # Recursive call
            seq_list += child.remove_dominant_sequences()
            if child.is_empty():
                self._del_child(child)
        return seq_list

    def topk_sequences(self, topk):
        '''
        Return the top-k sequences
        '''
        seq_list = []
        # Only root can get top-k sequences
        if self._sequence is None:
            # While the amount of sequence was not reached and
            # there are nodes to be explored
            while len(seq_list) < topk and len(self._child_dict):
                # Remove and get the sequences of level i
                # Next iteration the sequences of level i+1 will be get
                seq_list += self.remove_dominant_sequences()
        return seq_list[:topk]

    def get_tree_string(self):
        '''
        Return a string containing the branch starting in current node
        '''
        d_str = ' ' * (self.get_depth())
        tree_str = '\n' + d_str + 'Node: ' + str(self.get_record())
        for sequence in self._sequence_dict.values():
            tree_str += '\n' + d_str + str(sequence)
        for node in self._child_dict.values():
            tree_str += node.get_tree_string()
        return tree_str

    def get_hierarchy_string(self):
        '''
        Return a string containing the hierarchy branch starting in current
        node
        '''
        hstr = '\nNode: ' + str(self.get_id())
        child_str_list = [str(child_id) for child_id in self._child_dict]
        hstr += '\nChildren: ' + ', '.join(child_str_list)
        hstr += '\nHierarchy: '
        if self._hierarchy is None:
            hstr += 'None'
        else:
            hstr += self._hierarchy.get_string()
        for node in self._child_dict.values():
            hstr += '\n' + node.get_hierarchy_string()
        return hstr


class SeqNodePruning(SeqNode):  # IGNORE:too-many-instance-attributes
    '''
    Class for tree node
    '''
    def __init__(self, sequence, father, preference_dict):
        SeqNode.__init__(self, sequence, father,
                         preference_dict, create_hierarchy=False)
        # Suppose that node is dominant
        self._dominated = False

    def add_sequence_pruning(self, sequence, ancestor_dominated):
        '''
        Insert a sequence into index
        '''
        # Check if the sequence belongs to current node
        if self._depth == len(sequence):
            # Store sequence into current node
            seq_id = id(sequence)
            self._sequence_dict[seq_id] = sequence
            return self
        # Get ID for child
        node_id = get_position_id(sequence, self._depth)
        # Check if child already exists
        if node_id in self._child_dict:
            # Take the existing child
            node = self._child_dict[node_id]
        else:
            # Create a new child
            node = self._new_child_pruning(sequence, node_id,
                                           ancestor_dominated)
        # Update ancestor dominated
        ancestor_dominated = ancestor_dominated and node.is_dominated()
        # Add sequence do correspondent child node
        return node.add_sequence_pruning(sequence, ancestor_dominated)

    def add_sequence_recursive(self, sequence):
        '''
        Insert a sequence into index
        '''
        return self.add_sequence_pruning(sequence, self.is_dominated())

    def _new_child_pruning(self, sequence, node_id, ancestor_dominated):
        '''
        Create a new child using the sequence
        '''
        # Create node structure
        child = SeqNodePruning(sequence, self, self._preference_dict)
        # Check if node has dominated ancestor
        if ancestor_dominated:
            child.set_dominated()
            # Add node to children
            self._child_dict[node_id] = child
        else:
            # Create hierarchy if necessary
            # When there is one child and another is added
            if len(self._child_dict) == 1:
                self._restart_hierarchy()
            # Add node to children
            self._child_dict[node_id] = child
            self._add_child_to_hierarchy(child)
        return child

    def _add_child_to_hierarchy(self, child):
        '''
        Add a child to hierarchy
        '''
        # Check if node has hierarchy
        if self._hierarchy is not None:
            # Get node record
            record = child.get_record()
            # Add to hierarchy
            dominated = self._hierarchy.add(record)
            # Check if child was dominated
            if dominated:
                child.set_dominated()
            else:
                self._update_all_children()

    def _update_all_children(self):
        '''
        Update all children according to father hierarchy
        '''
        if self._hierarchy is None:
            dominant_list, dominated_list = self._child_dict.keys(), []
        else:
            # Get dominated from hierarchy
            dominant_list, dominated_list = \
                self._hierarchy.get_dominant_dominated()
        # For every dominated id
        for child_id in dominated_list:
            # Get correspondent node
            child = self._child_dict[child_id]
            child.set_dominated()
        for child_id in dominant_list:
            # Get correspondent node
            child = self._child_dict[child_id]
            child.set_dominant()

    def is_dominated(self):
        '''
        Return True if node is dominated, else return False
        '''
        return self._dominated

    def set_dominated(self):
        '''
        Set current node to dominated
        '''
        self._dominated = True
        self._hierarchy = None

    def set_dominant(self):
        '''
        Set just current node to dominant
        '''
        # Check if node was dominated
        if self._dominated:
            # Check if node has two or more children
            if len(self._child_dict) >= 2:
                # Restart hierarchy
                self._restart_hierarchy()
            # Update child because father became dominant
            self._update_all_children()
        # Set node to dominant
        self._dominated = False

    def _del_child_from_hierarchy(self, child):
        '''
        Remove a child from hierachy
        '''
        # Check if node has hierarchy
        if self._hierarchy is not None:
            # Check if remain a unique or none child
            if len(self._child_dict) <= 1:
                # Remove hierarchy
                self._hierarchy = None
            # Check if node has hierarchy
            if self._hierarchy is not None:
                # Get node record
                record = child.get_record()
                self._hierarchy.delete(record)

    def _del_child(self, child):
        '''
        Remove a child node
        '''
        # Remove child node
        child_id = child.get_id()
        del self._child_dict[child_id]
        self._del_child_from_hierarchy(child)

    def clean_recursive(self):
        '''
        Remove empty nodes from child branches
        '''
        dominant_removed = False
        del_list = []
        # For every child
        for child in self._child_dict.values():
            # Recursive call
            child.clean_recursive()
            # Check if child is empty
            if child.is_empty():
                del_list.append(child)
                # Dominant removed if aprevious child was dominant
                # or current child is dominant
                dominant_removed = dominant_removed or not child.is_dominated()
        for child in del_list:
            # Remove child
            self._del_child(child)
        if not self.is_dominated() and dominant_removed:
            self._update_all_children()

    def copy(self):
        '''
        Create a copy of node
        '''
        # Create a new node
        node = SeqNodePruning(self._sequence, None, self._preference_dict)
        return self._update_copy(node)

    def _restart_hierarchy(self):
        '''
        Restart node hierarchy
        '''
        # Create hierarchy
        self._hierarchy = \
            self._preference_dict.get_hierarchy(self._sequence)
        # Add every child to hierarchy
        for child in self._child_dict.values():
            rec = child.get_record()
            self._hierarchy.add(rec)

    def get_dominant_children(self):
        '''
        Get dominant children
        '''
        child_list = []
        for child in self._child_dict.values():
            if not child.is_dominated():
                child_list.append(child)
        return child_list

    def get_hierarchy_string(self):
        '''
        Return a string containing the hierarchy branch starting in current
        node
        '''
        hstr = '\nNode: ' + str(self.get_id())
        hstr += '\nDominated: ' + str(self.is_dominated())
        child_str_list = [str(child_id) for child_id in self._child_dict]
        hstr += '\nChildren: ' + ', '.join(child_str_list)
        hstr += '\nHierarchy: '
        if self._hierarchy is None:
            hstr += 'None'
        else:
            hstr += self._hierarchy.get_string()
        for node in self._child_dict.values():
            hstr += '\n' + node.get_hierarchy_string()
        return hstr


def get_position_id(sequence, position):
    '''
    Get a node ID for a sequence
    The ID is the string of position corresponding to depth
    '''
    rec = sequence.get_position(position)
    return tuple(rec.items())
