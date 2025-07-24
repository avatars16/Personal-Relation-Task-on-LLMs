"""
Manager for collections of universes and experiment generation.
"""

import glob
import json
import random
import csv
import os

from models.universe import Universe
from constants import Representation, SemanticApproach, Branching
from utils.prompt_generator import (
    format_table_with_columns, 
    create_extensional_prompt_part_1, 
    create_extensional_prompt_part_2,
    create_intensional_prompt_part_2,
    create_intensional_prompt_part_1
)
from utils.file_utils import get_output_directory

random.seed(3022000)  # Use consistent seed for reproducible results

class ExperimentManager:
    """
    Manages collections of universes and generates experiment datasets.
    
    This class handles multiple universes, generates questions and prompts,
    and exports data in various formats for both human and AI model evaluation.
    """
    
    def __init__(self):
        """Initialize empty experiment manager"""
        self.universes = []
        self.names_pool = []
        self.grouped = {}

    def add_universe(self, universe):
        """Add a universe to the collection and update groupings"""
        self.universes.append(universe)
        self._group_universes()

    def __iter__(self):
        return iter(self.universes)

    def __len__(self):
        return len(self.universes)
    
    def generate_names(self, universes_list=None):
        """Generate names for all universes in the collection"""
        if universes_list is None or len(universes_list) == 0:
            universes_list = self.universes
        for universe in universes_list:
            self.names_pool = universe.generate_names(self.names_pool)

    def _group_universes(self):
        """Group universes by relation count and person count"""
        self.grouped = {}
        for universe in self.universes:
            key = (universe.rel_num, len(universe.persons))
            if key not in self.grouped:
                self.grouped[key] = []
            self.grouped[key].append(universe)

    def generate_prompt_options_and_answer(self, universe, question_universe_list, example_tuple, names_list, edge_dict, representation_type, branching_type, semantic_approach, for_models=False):
        """
        Generate complete prompt with options and answer for a given question.
        
        Args:
            universe: Universe instance
            question_universe_list: List of universe facts as tuples (question, answer, relation_types)
            example_tuple: Example question, answer, and steps  
            names_list: List of person names
            edge_dict: Edge dictionary with 'path', 'relation_types', 'answer', 'start'
            representation_type (Representation): ENGLISH or ABSTRACT
            branching_type (Branching): RIGHT or LEFT
            semantic_approach (SemanticApproach): EXTENSIONAL or INTENSIONAL
            for_models (bool): Whether this is for AI models or humans
            
        Returns:
            tuple: (question, prompt_1, universe_table, prompt_2, options, answer)
        """
        question = universe.edge_to_sentence(edge_dict["path"], edge_dict["relation_types"], representation_type, branching_type)
        
        universe_table = "\n".join([f"{q} = {a}" for q, a, r in question_universe_list])  
        if representation_type == Representation.ABSTRACT:
            name_conversions = [f"{person.name} = {person.abstract_name}" for person in universe.persons]
            name_conversions = sorted(name_conversions)      
            
        if semantic_approach == SemanticApproach.EXTENSIONAL:
            universe_table = self._question_universe_to_table(question_universe_list, names_list)
            universe_table = [[f"{q} = {a}" if q else "" for (q, a, r) in row] for row in universe_table]
            if representation_type == Representation.ABSTRACT:
                universe_table = [[name, *row] for name, row in zip(name_conversions, universe_table)]
            universe_table = format_table_with_columns(universe_table)
            
            prompt_1 = create_extensional_prompt_part_1(question, question_universe_list, example_tuple, for_models, names_list)
            prompt_2 = create_extensional_prompt_part_2(question, question_universe_list, example_tuple, for_models)
            options = universe.get_names(Representation.ENGLISH)
        else:
            prompt_1 = create_intensional_prompt_part_1()
            prompt_2 = create_intensional_prompt_part_2(question, question_universe_list, example_tuple, for_models)
            options = universe.get_names(Representation.ENGLISH)
            if representation_type == Representation.ABSTRACT:
                universe_table = universe_table.split("\n")
                universe_table = [[name, row] for name, row in zip(name_conversions, universe_table)]
                universe_table = format_table_with_columns(universe_table)

        if representation_type == Representation.ABSTRACT:
            options = universe.get_names(Representation.ABSTRACT)
        
        answer = universe.edge_to_answer(edge_dict, representation_type, semantic_approach)
        
        return (question, prompt_1, universe_table, prompt_2, options, answer)

    def write_line_to_excel(self, wb, universe, edge_dict, question_universe_list, example_tuple, names_list, branching_type, representation_type, semantic_approach, question_id, for_models=False):
        """Write a single question line to Excel workbook"""            
        worksheet_name = representation_type.name.lower() + "," + semantic_approach.name.lower()
        ws = wb[worksheet_name]
        
        (question, prompt_1, universe_table, prompt_2, options, answer) = self.generate_prompt_options_and_answer(
            universe, question_universe_list, example_tuple, names_list, edge_dict, 
            representation_type, branching_type, semantic_approach, for_models
        )
        prompt = prompt_1 + "\n" + universe_table + "\n" + prompt_2
        ws.append([len(edge_dict["relation_types"])+1, str(branching_type)[10], question_id, prompt, question, answer])

    def write_line_to_csv(self, base_dir, universe, edge_dict, question_universe_list, example_tuple, names_list, branching_type, representation_type, semantic_approach, question_id, for_models=False):
        """Write a single question line to CSV file"""
        worksheet_name = f"{representation_type.name.lower()}_{semantic_approach.name.lower()}.csv"
        csv_file_path = os.path.join(base_dir, worksheet_name)
        
        (question, prompt_1, universe_table, prompt_2, options, answer) = self.generate_prompt_options_and_answer(
            universe, question_universe_list, example_tuple, names_list, edge_dict, 
            representation_type, branching_type, semantic_approach, for_models
        )
    
        prompt_universe = universe_table.replace("\t\t", "\t").replace("\t\n", "\n")
        
        # Escape newline characters for CSV
        prompt_1 = prompt_1.replace("\n", ";;")
        prompt_2 = prompt_2.replace("\n", ";;")
        question = question.replace("\n", ";;")
        prompt_universe = prompt_universe.replace("\n", ";;")
        answer = answer.replace("\n", ";;")
        options = ";;".join(options)

        write_header = not os.path.exists(csv_file_path)
        with open(csv_file_path, mode='a', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            if write_header:
                writer.writerow(["Complexity", "Branching", "Approach", "Representation", "questionId", "prompt_1", "prompt_2", "Question", "Answer", "options", "question_universe"])
            writer.writerow([
                len(edge_dict["relation_types"]) + 1, str(branching_type)[10], semantic_approach, 
                representation_type, question_id, prompt_1, prompt_2, question, answer, options, prompt_universe
            ])

    def generate_file(self, max_questions=None, for_models=False, branching_types=None, semantic_approaches=None, representation_types=None, complexity_levels=None):
        """
        Generate experiment files for either humans or AI models.
        
        Args:
            max_questions (int): Maximum number of questions per universe
            for_models (bool): Whether to generate files for AI models or humans
            batch_dir (str): Directory containing batch files for question filtering
            branching_types (list): List of Branching enum values to include
            semantic_approaches (list): List of SemanticApproach enum values to include
            representation_types (list): List of Representation enum values to include
            complexity_levels (list): List of complexity levels (path lengths) to include
        """
        # Set defaults if not provided
        if branching_types is None:
            branching_types = [Branching.RIGHT, Branching.LEFT]
        if semantic_approaches is None:
            semantic_approaches = [SemanticApproach.INTENSIONAL, SemanticApproach.EXTENSIONAL]
        if representation_types is None:
            representation_types = [Representation.ABSTRACT, Representation.ENGLISH]
        if complexity_levels is None:
            complexity_levels = [2, 3]
        user_type = "models" if for_models else "humans"
        output_directory = get_output_directory(os.path.join('csv', user_type))
        
        # Clean up old files
        for file in os.listdir(output_directory):
            os.remove(os.path.join(output_directory, file))

        # Create Excel workbook
        from openpyxl import Workbook
        wb = Workbook()
        wb.active
        for representation_type in representation_types:
            for semantic_approach in semantic_approaches:
                worksheet_name = representation_type.name.lower() + "," + semantic_approach.name.lower()
                ws = wb.create_sheet(worksheet_name)
                ws.append(["Complexity", "Branching", "QuestionId", "Prompt", "Question", "Answer"])

        for group in self.grouped.values():
            if len(group) == 0:
                print("No groups found")
                continue

            for i, universe in enumerate(group):
                print(f"Generating questions for universe {i+1}/{len(group)}")	
                names_list = universe.get_names()
                example = universe.example
                
                # Get min and max complexity from the specified levels
                min_complexity = min(complexity_levels)
                max_complexity = max(complexity_levels)
                relation_edges = universe.generate_relations(min_complexity -1, max_complexity)
                # Filter edges by complexity levels
                relation_edges = [edge for edge in relation_edges if len(edge["path"]) in complexity_levels]
                relation_edges = sorted(relation_edges, key=lambda x: len(x["path"]))
                
                # Old code, which can only create stimuli with questionId which is in openai batch file.
                # if batch_dir is not None:
                #     batch_ids = self._extract_ids_from_batch_files(batch_dir)
                #     edges_to_include = []
                #     for batch_id in batch_ids:
                #         splitted = batch_id.split("_")
                #         if len(splitted) == 3:
                #             edges_to_include.append(splitted[2])

                #     relation_edges = [edge for edge in relation_edges 
                #                     if universe.edge_to_id(edge["path"], edge["relation_types"]) in edges_to_include]
                # else:
                relation_edges = self._equalize_path_lengths(relation_edges, max_questions, universe=universe)

                edge_length_count = {}
                for edge in relation_edges:
                    edge_length = len(edge["path"])
                    edge_length_count[edge_length] = edge_length_count.get(edge_length, 0) + 1
                print(f"Edge length count: {edge_length_count}")
                
                for branching_type in branching_types:
                    for semantic_approach in semantic_approaches:
                        for representation_type in representation_types:
                            example_ready = self._get_example(example, universe, representation_type, branching_type, semantic_approach)
                            question_universe_list = self._get_question_universe(universe, representation_type, branching_type, semantic_approach)
                            universe_index = self.universes.index(universe)
                            
                            if not for_models:
                                edges = random.sample(universe.generate_intensional_universe(), 5)
                                for edge_dict in edges:
                                    for j in range(4):
                                        question_id = f"{universe_index}_{str(branching_type)[10]}_{universe.edge_to_id(edge_dict['path'], edge_dict['relation_types'])}"
                                        self.write_line_to_csv(output_directory, universe, edge_dict, question_universe_list, example_ready, names_list, branching_type, representation_type, semantic_approach, question_id, for_models)
                                        self.write_line_to_excel(wb, universe, edge_dict, question_universe_list, example_ready, names_list, branching_type, representation_type, semantic_approach, question_id, for_models)
                            
                            for edge_dict in relation_edges:
                                question_id = f"{universe_index}_{str(branching_type)[10]}_{universe.edge_to_id(edge_dict['path'], edge_dict['relation_types'])}"
                                # if batch_dir is not None and question_id not in batch_ids:
                                #     count_skipped_edges += 1
                                #     continue
                                self.write_line_to_csv(output_directory, universe, edge_dict, question_universe_list, example_ready, names_list, branching_type, representation_type, semantic_approach, question_id, for_models)
                                self.write_line_to_excel(wb, universe, edge_dict, question_universe_list, example_ready, names_list, branching_type, representation_type, semantic_approach, question_id, for_models)
        
        excel_filename = "universe_questions_models.xlsx" if for_models else "universe_questions.xlsx"
        excel_dir = get_output_directory('excel')
        wb.save(os.path.join(excel_dir, excel_filename))
        print(f"Files for {user_type} are saved in the '{output_directory}' directory.")
        print(f"Excel file saved in '{excel_dir}'.")

    def generate_all_files(self, max_questions=None,  **filter_options):
        """Generate separate files for both humans and AI models"""
        self.generate_file(max_questions, for_models=False, **filter_options)
        self.generate_file(max_questions, for_models=True,  **filter_options)

    def create_experiment_groups(self, num_splits=4):
        """Create randomized experiment groups from generated questions"""
        output_directory = get_output_directory(os.path.join('csv', 'humans'))
        csv_files = {}
        for file in os.listdir(output_directory):
            if file.endswith(".csv"):
                with open(os.path.join(output_directory, file), mode='r', newline='', encoding='utf-8') as csvfile:
                    reader = csv.reader(csvfile)
                    csv_files[file] = list(reader)
        
        # Add row numbers
        for file_name, file_rows in csv_files.items():
            for i, row in enumerate(file_rows):
                row.append(i)
        
        # Collect all rows and shuffle
        all_rows = []
        for file_rows in csv_files.values():
            all_rows.extend(file_rows[1:])  # Skip header row

        random.shuffle(all_rows)
        all_rows = sorted(all_rows, key=lambda x: (x[0], x[3], x[2], x[1]))

        # Assign groups rotationally
        num_groups = 4 * num_splits
        for i, row in enumerate(all_rows):
            group_index = i % num_groups
            row.append(group_index)
        
        # Write grouped file
        grouped_file_path = os.path.join(get_output_directory('csv'), "universe_questions_grouped.csv")
        with open(grouped_file_path, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(["Relation_Count", "Branching", "Approach", "Representation", "questionId", "prompt_1", "prompt_2", "Question", "Answer", "options", "question_universe", "row_number", "group"])
            writer.writerows(all_rows)

    def _get_example(self, example, universe, representation_type, branching_type, semantic_approach):
        """Generate example question and answer for prompts"""
        example_question = universe.edge_to_sentence(example["path"], example["relation_types"], representation_type, branching_type)
        example_answer = universe.edge_to_answer(example, representation_type, semantic_approach)
        example_universe = []
        for i in range(len(example["relation_types"])):
            if semantic_approach == SemanticApproach.EXTENSIONAL:
                question = universe.edge_to_sentence(example["path"][i:i+2], [example["relation_types"][i]], representation_type, branching_type)
                answer_edge_dict = {"path": example["path"][i:i+2], "relation_types": [example["relation_types"][i]], "answer": example["path"][i+1]}
            else: 
                question = universe.edge_to_sentence(example["path"][0:i+2], example["relation_types"][0:i+1], representation_type, branching_type)
                answer_edge_dict = {"path": example["path"][0:i+2], "relation_types": example["relation_types"][0:i+1], "answer": example["path"][-1]}
            answer = universe.edge_to_answer(answer_edge_dict, representation_type, semantic_approach)
            example_universe.append((question, answer))
        return (example_question, example_answer, example_universe)

    def _get_question_universe(self, universe, representation_type, branching_type, semantic_approach):
        """Generate the universe context for questions"""
        question_universe = []
        if semantic_approach == SemanticApproach.EXTENSIONAL:
            relations_depth_two = universe.generate_relations(1, 1, include_disabled_edges=True)
        else:
            relations_depth_two = universe.generate_intensional_universe()
        for relation in relations_depth_two:
            question = universe.edge_to_sentence(relation["path"], relation["relation_types"], Representation.ENGLISH, branching_type)
            answer = universe.edge_to_answer(relation, representation_type, semantic_approach)
            question_universe.append((question, answer, relation["relation_types"]))
        
        if semantic_approach == SemanticApproach.EXTENSIONAL:
            question_universe = sorted(question_universe, key=lambda x: (x[2], x[0]))

        return question_universe
    
    def _extract_ids_from_batch_files(self, batch_dir=None):
        """Extract question IDs from batch files"""
        if batch_dir is None:
            batch_dir = os.path.join('dataset-generation', 'output', 'batches')
        
        batch_ids = []
        batch_files = glob.glob(os.path.join(batch_dir, '*.jsonl'))
        
        for batch_file in batch_files:
            with open(batch_file, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line.strip())
                        if 'custom_id' in data:
                            batch_ids.append(data['custom_id'])
                    except json.JSONDecodeError:
                        continue
        
        return batch_ids

    def _split_by_path_length(self, data):
        """Split data by path length for equalization"""
        path_length_dict = {}
        for item in data:
            path_length = len(item['path'])
            if path_length not in path_length_dict:
                path_length_dict[path_length] = []
            path_length_dict[path_length].append(item)
        return list(path_length_dict.values())

    def _equalize_path_lengths(self, data, max_length=None, universe=None):
        """Equalize the number of relations for each path length"""
        split_data = self._split_by_path_length(data)
        min_count = min(len(sublist) for sublist in split_data)
        min_count = min(min_count, max_length) if max_length else min_count
        print(f"Equalizing to {min_count} relations per path length")
        
        equalized_data = []
        for sublist in split_data:
            equalized_data.extend(random.sample(sublist, min_count))

        return equalized_data

    def _question_universe_to_table(self, question_universe_list, names_list):
        """
        Convert question universe to a table format.
        
        Args:
            question_universe_list: List of tuples (question, answer, relation_types)
            names_list: List of names sorted alphabetically

        Returns:
            list: Table structure with columns for each relation type
        """
        relations = set()
        for q, a, r in question_universe_list:
            relations.update(r)

        # Create relation dictionary
        relation_dict = {relation: [] for relation in relations}
        for q, a, r in question_universe_list:
            relation_dict[r[0]].append((q, a, r)) 
        
        # Convert to table format
        table = []
        for i in range(len(names_list)):
            row = []
            for relation_type in ["enemy", "friend", "parent", "child"]:
                if i < len(relation_dict.get(relation_type, [])):
                    row.append(relation_dict[relation_type][i])            
            table.append(row)
        return table
