"""
Main experiment script for generating linguistic relation datasets.

This script supports both loading existing universes and generating new ones,
with full command-line argument support for flexible configuration.
"""

import argparse
import os
from models.universe import Universe
from managers.experiment_manager import ExperimentManager
from utils.file_utils import get_output_directory, set_base_output_directory
from constants import Representation, SemanticApproach, Branching


def load_existing_universes(experiment_manager, universe_indices_list, max_questions_count, experiment_groups_count, **filter_options):
    """
    Load existing universes from CSV files and generate experiment files.
    
    Args:
        experiment_manager (ExperimentManager): Manager for the experiment
        universe_indices_list (list): List of universe indices to load
        max_questions_count (int): Maximum questions per universe
        batch_dir_path (str): Path to batch directory for filtering
        experiment_groups_count (int): Number of experiment groups to create
        **filter_options: Additional filtering options for experiments
    """
    for universe_idx in universe_indices_list:
        print(f"Loading universe {universe_idx}")
        universe = Universe.load_universe(f"universe_{universe_idx}.csv")
        experiment_manager.add_universe(universe)

    experiment_manager.generate_all_files(max_questions_count, **filter_options)
    experiment_manager.create_experiment_groups(experiment_groups_count)
    
    for i, universe in enumerate(experiment_manager.universes):
        universe.visualize_relations(f"universe_{i}", True)


def generate_new_universes(experiment_manager, universes_count, relation_count, person_pairs_count, max_questions_count, experiment_groups_count, output_dir, **filter_options):
    """
    Generate new universes and create experiment files.
    
    Args:
        experiment_manager (ExperimentManager): Manager for the experiment
        universes_count (int): Number of universes to generate
        relation_count (int): Number of relation types (1-4)
        person_pairs_count (int): Number of person pairs per universe
        max_questions_count (int): Maximum questions per universe
        experiment_groups_count (int): Number of experiment groups to create
        **filter_options: Additional filtering options for experiments
    """
    for i in range(universes_count):
        universe = Universe(relation_count, person_pairs_count)
        universe.generate_example()
        experiment_manager.add_universe(universe)

    experiment_manager.generate_names(experiment_manager.universes)
    experiment_manager.generate_all_files(max_questions_count, **filter_options)
    experiment_manager.create_experiment_groups(experiment_groups_count)

    for i, universe in enumerate(experiment_manager.universes):
        universe.save_universe(f"universe_{i}.csv")        
        universe.visualize_relations(f"universe_{i}", True)


def main():
    """Main function with command-line argument parsing"""
    parser = argparse.ArgumentParser(description='Generate linguistic relation experiment datasets')
    
    # General configuration
    parser.add_argument('--output-dir', type=str, default='output',
                       help='Base output directory path')
    parser.add_argument('--max-questions', type=int, default=40,
                       help='Maximum number of questions per universe')
    parser.add_argument('--experiment-groups', type=int, default=10,
                       help='Number of experiment groups to create')
    
    # Universe generation parameters
    parser.add_argument('--mode', choices=['load', 'generate'], default='load',
                       help='Mode: load existing universes or generate new ones')
    parser.add_argument('--universe-indices', type=int, nargs='+', default=[0],
                       help='Indices of universes to load (load mode only)')
    parser.add_argument('--universes-count', type=int, default=10,
                       help='Number of universes to generate (generate mode only)')
    parser.add_argument('--relation-count', type=int, default=4,
                       help='Number of relation types in universe (1-4: friend, enemy, parent, child)')
    parser.add_argument('--person-pairs', type=int, default=3,
                       help='Number of person pairs in universe')
    
    # Experiment filtering parameters
    parser.add_argument('--branching', choices=['left', 'right', 'both'], default='both',
                       help='Branching type: left, right, or both (default: both)')
    parser.add_argument('--semantic', choices=['extensional', 'intensional', 'both'], default='both',
                       help='Semantic approach: extensional, intensional, or both (default: both)')
    parser.add_argument('--representation', choices=['english', 'abstract', 'both'], default='both',
                       help='Representation type: english, abstract, or both (default: both)')
    parser.add_argument('--complexity',type=int, nargs='+', default=[3, 4],
                       help='List of complexity levels (path lengths) to include (default: 2 3)')
    
    # Batch processing
    parser.add_argument('--batch-dir', type=str, default=None,
                       help='Directory containing batch files for question filtering')
    
    args = parser.parse_args()
    print("hierooo", args.output_dir)
    # Validate arguments
    if args.relation_count < 1 or args.relation_count > 4:
        print("Error: relation-count must be between 1 and 4")
        return 1
    
    if args.person_pairs < 1:
        print("Error: person-pairs must be at least 1")
        return 1
    
    print(args.complexity)
    # Flatten complexity list if needed (action="append", nargs="+")
    if args.complexity and isinstance(args.complexity[0], list):
        args.complexity = [item for sublist in args.complexity for item in sublist]

    if not args.complexity or any(c < 3 for c in args.complexity):
        print("Error: complexity levels must be equal or higher than 3")
        return 1
    
    # Parse filter options
    filter_options = {}
    
    # Parse branching options
    if args.branching == 'both':
        filter_options['branching_types'] = [Branching.LEFT, Branching.RIGHT]
    elif args.branching == 'left':
        filter_options['branching_types'] = [Branching.LEFT]
    elif args.branching == 'right':
        filter_options['branching_types'] = [Branching.RIGHT]
    
    # Parse semantic approach options
    if args.semantic == 'both':
        filter_options['semantic_approaches'] = [SemanticApproach.EXTENSIONAL, SemanticApproach.INTENSIONAL]
    elif args.semantic == 'extensional':
        filter_options['semantic_approaches'] = [SemanticApproach.EXTENSIONAL]
    elif args.semantic == 'intensional':
        filter_options['semantic_approaches'] = [SemanticApproach.INTENSIONAL]
    
    # Parse representation type options
    if args.representation == 'both':
        filter_options['representation_types'] = [Representation.ENGLISH, Representation.ABSTRACT]
    elif args.representation == 'english':
        filter_options['representation_types'] = [Representation.ENGLISH]
    elif args.representation == 'abstract':
        filter_options['representation_types'] = [Representation.ABSTRACT]
    
    # Set complexity levels
    filter_options['complexity_levels'] = args.complexity
    
    experiment_manager = ExperimentManager()
    
    # Set the base output directory from command line argument
    set_base_output_directory(args.output_dir)
    
    # Set batch directory path if universe 0 is being loaded
    batch_dir_path = args.batch_dir
    if args.mode == 'load' and 0 in args.universe_indices and batch_dir_path is None:
        batch_dir_path = os.path.join('dataset-generation', 'output', 'batches')
    
    print(f"Starting experiment in {args.mode} mode...")
    print(f"Output directory: {args.output_dir}")
    print(f"Max questions: {args.max_questions}")
    print(f"Experiment groups: {args.experiment_groups}")
    print(f"Branching: {args.branching}")
    print(f"Semantic approach: {args.semantic}")
    print(f"Representation type: {args.representation}")
    print(f"Complexity levels: {args.complexity}")
    
    try:
        if args.mode == 'load':
            print(f"Loading universes: {args.universe_indices}")
            load_existing_universes(
                experiment_manager,
                args.universe_indices,
                args.max_questions,
                args.experiment_groups,
                **filter_options
            )
        else:
            print(f"Generating {args.universes_count} new universes with {args.relation_count} relation types")
            generate_new_universes(
                experiment_manager,
                args.universes_count,
                args.relation_count,
                args.person_pairs,
                args.max_questions,
                args.experiment_groups,
                args.output_dir,
                **filter_options
            )
        
        print("Experiment completed successfully!")
        return 0
        
    except Exception as e:
        print(f"Error during experiment: {e}")
        return 1


if __name__ == "__main__":
    exit(main())