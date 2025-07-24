"""
Functions for generating prompts for different semantic approaches and question types.
"""

from num2words import num2words

def create_intensional_prompt_part_1():
    """Create the introductory part of an intensional prompt"""
    prompt = "English phrases can be translated into formulae. Use the following translations to answer the question."
    prompt += "\n\n"
    return prompt

def create_intensional_prompt_part_2(question, universe_list, example_tuple, is_chain_of_thought):
    """
    Create the example and question part of an intensional prompt.
    
    Args:
        question (str): The question to ask
        universe_list (list): List of universe facts
        example_tuple (tuple): Example question, answer, and steps
        is_chain_of_thought (bool): Whether to request step-by-step reasoning
    """
    prompt = "\n\n"
    prompt += "Here is an example of how to get a formula for a phrase."
    prompt += "\n"
    example_question, example_answer, universe_example = example_tuple
    prompt += f"What is the formula for \"{example_question}\"?"
    prompt += "\n\n"
    prompt += "Here are the steps to arrive at the answer:"
    for i, (q, a) in enumerate(universe_example):
        prompt += f"\n{i+1}. {q} = {a}"
    prompt += "\n\n"
    prompt += f"So the answer is {example_answer}"
    prompt += "\n\n"
    prompt += f"What is the formula for \"{question}\"?"
    if is_chain_of_thought:
        prompt += " Please answer the question in the same format as the example. End with 'So the answer is [answer]'."
    return prompt


def create_extensional_prompt_part_1(question, universe_list, example_tuple, is_chain_of_thought, names_list):
    """
    Create the introductory part of an extensional prompt.
    
    Args:
        question (str): The question to ask
        universe_list (list): List of universe facts
        example_tuple (tuple): Example question, answer, and steps
        is_chain_of_thought (bool): Whether to request step-by-step reasoning
        names_list (list): List of person names in the universe
    """
    prompt = f"Imagine there are {num2words(len(names_list))} people: "
    for i in range(len(names_list)):
        if i == len(names_list) - 1:
            prompt = prompt[:-2]
            prompt += f" and {names_list[i]}."
        else:
            prompt += f"{names_list[i]}, "
    prompt += " They have the following relationships to each other:"
    prompt += "\n\n"
    return prompt

def create_extensional_prompt_part_2(question, universe_list, example_tuple, is_chain_of_thought):
    """
    Create the example and question part of an extensional prompt.
    
    Args:
        question (str): The question to ask
        universe_list (list): List of universe facts
        example_tuple (tuple): Example question, answer, and steps
        is_chain_of_thought (bool): Whether to request step-by-step reasoning
    """
    prompt = "\n"
    prompt += "Here is how to figure out the answer to the following question:"
    prompt += "\n"
    example_question, example_answer, universe_example = example_tuple
    prompt += f"Who is {example_question}?"
    prompt += "\n\n"
    prompt += "Here are the steps to arrive at the answer:"
    for i, (q, a) in enumerate(universe_example):
        prompt += f"\n{i+1}. {q} = {a}"
    prompt += "\n\n"
    prompt += f"So the answer is {example_answer}"
    prompt += "\n\n"
    prompt += f"Now answer the following question:"
    prompt += "\n"
    prompt += f"Who is {question}?"
    if is_chain_of_thought:
        prompt += " Please answer the question in the same format as the example. End with 'So the answer is [answer]'."
    return prompt


def format_table_with_columns(rows_list):
    """
    Format a table with proper column alignment.
    
    Args:
        rows_list: List of rows, where each row is a list of strings
        
    Returns:
        str: Formatted table string with aligned columns
    """
    col_widths = {}
    for row in rows_list:
        for i, col in enumerate(row):
            col_length = len(col)
            col_widths[i] = max(col_widths[i], col_length) if i in col_widths else col_length 
    
    formatted_rows = []
    for row in rows_list:
        formatted_row = ""
        for i, col in enumerate(row):
            formatted_row += col.ljust(col_widths[i] + 2)
        formatted_rows.append(formatted_row)
    
    return "\n".join(formatted_rows)
