"""
Utility functions for OpenAI batch processing
"""

import os
import json


def get_output_directory(subdir):
    """Get output directory path, creating if needed"""
    output_dir = os.path.join('output', subdir)
    os.makedirs(output_dir, exist_ok=True)
    return output_dir


def load_batch_ids(filepath):
    """Load batch IDs from a JSON file"""
    if os.path.exists(filepath):
        with open(filepath, 'r') as f:
            return json.load(f)
    return {}


def save_batch_ids(batch_ids, filepath):
    """Save batch IDs to a JSON file"""
    with open(filepath, 'w') as f:
        json.dump(batch_ids, f, indent=2)


def validate_jsonl(filepath):
    """Validate JSONL file format"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f, 1):
                if line.strip():
                    json.loads(line.strip())
        return True
    except json.JSONDecodeError as e:
        print(f"Invalid JSON at line {i}: {e}")
        return False
    except Exception as e:
        print(f"Error validating {filepath}: {e}")
        return False
