# Dataset Generation for Linguistic Relation Experiments

This project generates a data set of the Personal Relation Task to test on humans and LLMs

## Project Structure

```
├── run_experiment.py               # Main entry point (package root)
├── output/                        # Output data (csv, excel, images, universes)
├── requirements.txt                # Python dependencies
├── README.md                       # This file
└── src/
    ├── __init__.py                 # Package initialization
    ├── main.py                     # Main experiment runner script
    ├── constants.py                # Enums and constants (Representation, SemanticApproach, Branching)
    ├── models/
    │   ├── person.py               # PersonNode class for relationship graph
    │   └── universe.py             # Universe class for collections of people and relationships
    ├── managers/
    │   └── experiment_manager.py   # ExperimentManager for handling multiple universes
    ├── utils/
    │   ├── file_utils.py           # File I/O utilities
    │   ├── prompt_generator.py     # Functions for generating prompts and formatting
    │   ├── openai_batch_processor.py # OpenAI batch request/response processing
    │   └── name_generator.py       # Name and abstract translation generation
```

## Installation

```bash
pip install -r requirements.txt
```

## Quick Start

### Simple Usage

```bash

# Run main experiment (load or generate universes)
python run_experiment.py --mode generate --universes-count 5 --relation-count 3 --person-pairs 3
```

### Main Experiment Interface

```bash
# Load existing universe 0 and generate questions
python run_experiment.py --mode load --universe-indices 0 --max-questions 40

# Generate 5 new universes with 3 relation types
python run_experiment.py --mode generate --universes-count 5 --relation-count 3 --person-pairs 3

# Specify custom output directory
python run_experiment.py --output-dir my-output --max-questions 50
```

## Command Line Parameters

### Main Experiment Parameters

- `--mode`: Either 'load' (existing universes) or 'generate' (new universes)
- `--output-dir`: Base output directory (default: 'output')
- `--max-questions`: Maximum questions per universe (default: 40)
- `--experiment-groups`: Number of experiment groups (default: 10)
- `--universe-indices`: Which universes to load (load mode only)
- `--universes-count`: Number of universes to generate (generate mode only)
- `--relation-count`: Number of relation types (1-4: friend, enemy, parent, child)
- `--person-pairs`: Number of person pairs in each universe
- `--batch-dir`: Directory with batch files for question filtering
- `--branching`: Branching type: left, right, or both (default: both)
- `--semantic`: Semantic approach: extensional, intensional, or both (default: both)
- `--representation`: Representation type: english, abstract, or both (default: both)
- `--complexity`: List of complexity levels (path lengths) to include (default: 3 4)

## File Naming Convention

The refactored codebase follows clear naming conventions:

### Scripts (Action-oriented)

- `main.py`: Primary experiment execution
- `run_experiment.py`: Package-level entry point

### Modules (Functionality-oriented)

- `person.py`: PersonNode data model
- `universe.py`: Universe data model and operations
- `experiment_manager.py`: Multi-universe experiment coordination
- `prompt_generator.py`: Prompt creation and formatting
- `openai_batch_processor.py`: API batch processing logic
- `file_utils.py`: File I/O operations
- `name_generator.py`: Name and translation generation
- `constants.py`: Enums and constant definitions

## Data Structures

### Edge Dictionary Structure

```python
edge_dict = {
    'path': [PersonNode, ...],           # List of PersonNode instances in the relation path
    'relation_types': [str, ...],        # List of relation types ('friend', 'enemy', 'child', 'parent')
    'answer': PersonNode,                # The PersonNode who is the answer
    'start': PersonNode                  # The PersonNode who starts the relation
}
```

### PersonNode Relationship Structure

```python
person.friend = {'node': PersonNode or None, 'disabled': bool}
person.enemy = {'node': PersonNode or None, 'disabled': bool}
person.parent = {'node': PersonNode or None, 'disabled': bool}
person.child = {'node': PersonNode or None, 'disabled': bool}
```
