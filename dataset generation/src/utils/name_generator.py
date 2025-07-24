"""
Utility functions for generating names and abstract translations.
"""

import random

def generate_name(first_letter, existing_names_list):
    """
    Generate a unique name starting with a specific letter.
    
    Args:
        first_letter (str): The required first letter of the name
        existing_names_list (list): List of already used names to avoid duplicates
        
    Returns:
        str: A unique name starting with the specified letter
    """
    from faker import Faker
    fake = Faker()
    name = fake.first_name()
    while name[0].lower() != first_letter or name in existing_names_list:
        name = fake.first_name()
    return name


def generate_random_sequence(sequence_length):
    """
    Generate a random sequence of consonants.
    
    Args:
        sequence_length (int): Length of the sequence to generate
        
    Returns:
        str: Random sequence of consonants
    """
    consonants = "bcdfghklmnpqrstvwxyz"
    return ''.join(random.choices(consonants, k=sequence_length))

def generate_random_translation(existing_translations_list, sequence_length):
    """
    Generate a unique abstract translation sequence.
    
    Args:
        existing_translations_list (list): List of already used sequences to avoid duplicates
        sequence_length (int): Length of the sequence to generate
        
    Returns:
        str: Unique abstract translation sequence
    """
    new_sequence = generate_random_sequence(sequence_length)
    while new_sequence in existing_translations_list:
        new_sequence = generate_random_sequence(sequence_length)
    return new_sequence
