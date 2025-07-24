#!/usr/bin/env python3
"""
Main entry point for the Dataset Generation for Linguistic Relation Experiments.

This script provides a convenient way to run the experiment generation system
from the package root directory.

Usage:
    python run_experiment.py --mode generate --universes-count 5 --relation-count 3
    python run_experiment.py --mode load --universe-indices 0 1 2 --max-questions 50
"""

import sys
import os

# Add the src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

# Import and run the main experiment script
from main import main

if __name__ == "__main__":
    main()
