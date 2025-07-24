"""
Core data models for the linguistic relation experiment system.
"""

class PersonNode:
    """
    Represents a person in the relationship graph with connections to other persons.
    
    Each person can have relationships of type: friend, enemy, parent, child.
    Relationships can be disabled for experimental purposes.
    """
    
    def __init__(self, person_id):
        """
        Initialize a person node with empty relationships.
        
        Args:
            person_id (int): Unique identifier for this person
        """
        self.friend = {'node': None, 'disabled': False}
        self.enemy = {'node': None, 'disabled': False}
        self.parent = {'node': None, 'disabled': False}
        self.child = {'node': None, 'disabled': False}

        self.id = person_id
        self.name = None
        self.abstract_name = None
    
    def set_friend(self, friend_node):
        """Set friend relationship"""
        self.friend["node"] = friend_node
        self.friend["disabled"] = False
        
    def set_enemy(self, enemy_node):
        """Set enemy relationship"""
        self.enemy["node"] = enemy_node
        self.enemy["disabled"] = False

    def set_parent(self, parent_node):
        """Set parent relationship"""
        self.parent["node"] = parent_node
        self.parent["disabled"] = False
    
    def set_child(self, child_node):
        """Set child relationship"""
        self.child["node"] = child_node
        self.child["disabled"] = False
    
    def get_friend(self, include_disabled_edges=False):
        """Get friend node if enabled or if including disabled edges"""
        if (not include_disabled_edges) and self.friend["disabled"]:
            return None 
        return self.friend["node"]
    
    def get_enemy(self, include_disabled_edges=False):
        """Get enemy node if enabled or if including disabled edges"""
        if (not include_disabled_edges) and self.enemy["disabled"]:
            return None 
        return self.enemy["node"]
    
    def get_parent(self, include_disabled_edges=False):
        """Get parent node if enabled or if including disabled edges"""
        if (not include_disabled_edges) and self.parent["disabled"]:
            return None 
        return self.parent["node"]
    
    def get_child(self, include_disabled_edges=False):
        """Get child node if enabled or if including disabled edges"""
        if (not include_disabled_edges) and self.child["disabled"]:
            return None 
        return self.child["node"]
