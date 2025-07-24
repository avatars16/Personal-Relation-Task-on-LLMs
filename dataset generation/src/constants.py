"""
Constants and enumerations used throughout the linguistic relation experiment system.
"""

import os
from enum import Enum

class Representation(Enum):
    """Type of representation used in questions and answers"""
    ENGLISH = 1    # Use English names (e.g., "Alice", "Bob")
    ABSTRACT = 2   # Use abstract symbols (e.g., "a", "b")

class SemanticApproach(Enum):
    """Approach for representing semantic relationships"""
    EXTENSIONAL = 1   # Use lookup tables showing direct relationships
    INTENSIONAL = 2   # Use logical formulas and function composition

class Branching(Enum):
    """Direction for parsing relationship chains"""
    RIGHT = 1   # "the enemy of the friend of Alice" (right-branching)
    LEFT = 2    # "Alice's friend's enemy" (left-branching)

# Supported relation types in order of complexity
RELATION_TYPES = ["friend", "enemy", "parent", "child"]

# Maximum number of supported relation types
MAX_RELATION_COUNT = 4

# Default base output directory
DEFAULT_OUTPUT_DIR = os.path.join('dataset-generation', 'output')
