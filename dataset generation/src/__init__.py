"""
Linguistic Relation Experiment Dataset Generation Package

This package provides tools for generating datasets to test linguistic relation
understanding in AI models and humans.
"""

from .constants import Representation, SemanticApproach, Branching
from .models.universe import Universe
from .models.person import PersonNode
from .managers.experiment_manager import ExperimentManager
from .utils.file_utils import get_output_directory, set_base_output_directory

__version__ = "1.0.0"
__all__ = [
    "Representation", 
    "SemanticApproach", 
    "Branching",
    "Universe",
    "PersonNode", 
    "ExperimentManager",
    "get_output_directory",
    "set_base_output_directory"
]
