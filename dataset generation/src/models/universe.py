"""
Universe model representing a collection of people and their relationships.
"""

import random
import csv
import networkx as nx
import matplotlib.pyplot as plt
import os

from models.person import PersonNode
from constants import Representation, SemanticApproach, Branching
from utils.file_utils import get_output_directory
from utils.name_generator import generate_name, generate_random_translation

class Universe:
    """
    Represents a universe of people with defined relationships.
    
    A universe contains people connected by relationships (friend, enemy, parent, child).
    It can generate questions about these relationships and visualize the relationship graph.
    """
    
    def __init__(self, relation_count, person_pairs_count):
        """
        Initialize a new universe with the specified number of relations and people.
        
        Args:
            relation_count (int): Number of relation types (1-4: friend, enemy, parent, child)
            person_pairs_count (int): Number of person pairs to create
        """
        self.rel_num = relation_count
        self.abstract_relations_names = {r: None for r in ["friend", "enemy", "parent", "child"]}

        # Create persons
        self.persons = []
        for i in range(person_pairs_count * 2):
            self.persons.append(PersonNode(i))
        
        # Initialize relationships based on relation count
        if self.rel_num >= 1:
            self._init_relation("friend", "friend")
        if self.rel_num >= 3:
            self._init_relation("parent", "child")
        if self.rel_num >= 2:
            self._init_enemy()

    def _init_relation(self, relation1, relation2):
        """Initialize a symmetric or asymmetric relation between person pairs"""
        person_list = self.persons.copy()
        random.shuffle(person_list)
        for i in range(0, len(person_list), 2):
            if i + 1 < len(person_list):
                getattr(person_list[i], f"set_{relation1}")(person_list[i + 1])
                getattr(person_list[i + 1], f"set_{relation2}")(person_list[i])

    def _init_enemy(self):
        """Initialize enemy relations ensuring graph connectivity"""
        max_attempts = 20
        
        for attempt in range(max_attempts):
            # Reset enemy relationships
            for person in self.persons:
                person.enemy["node"] = None
                
            persons_needing_enemy = self.persons.copy()
            random.shuffle(persons_needing_enemy)
            
            success = True
            while persons_needing_enemy and success:
                success = False
                current_person = persons_needing_enemy.pop(0)
                
                if current_person.enemy["node"] is not None:
                    success = True
                    continue
                    
                # Find valid enemy candidates
                candidates = []
                for other_person in self.persons:
                    if (other_person.id == current_person.id or 
                        other_person.enemy["node"] is not None or
                        (current_person.friend["node"] is not None and current_person.friend["node"].id == other_person.id) or
                        (other_person.friend["node"] is not None and other_person.friend["node"].id == current_person.id)):
                        continue
                    candidates.append(other_person)
                
                if candidates:
                    enemy = random.choice(candidates)
                    current_person.enemy["node"] = enemy
                    enemy.enemy["node"] = current_person
                    
                    if enemy in persons_needing_enemy:
                        persons_needing_enemy.remove(enemy)
                    
                    success = True
            
            all_have_enemy = all(person.enemy["node"] is not None for person in self.persons)
            if all_have_enemy and self._is_connected_graph():
                return
                    
        print("Warning: Could not create a fully connected graph after multiple attempts")

    def _is_connected_graph(self):
        """Check if the current graph configuration is fully connected"""
        G = nx.Graph()
        
        for person in self.persons:
            G.add_node(person.id)
        
        for person in self.persons:
            relationships = [
                ('friend', person.friend),
                ('enemy', person.enemy),
                ('parent', person.parent),
                ('child', person.child)
            ]
            
            for _, relation in relationships:
                if relation["node"] is not None:
                    G.add_edge(person.id, relation["node"].id)
        
        return nx.is_connected(G)
    
    def generate_names(self, existing_names_pool, num_chars=1):
        """
        Generate names for all persons and abstract translations.
        
        Args:
            existing_names_pool (list): Pool of already used names to avoid duplicates
            num_chars (int): Number of characters for abstract names
            
        Returns:
            list: Updated names pool including new names
        """
        person_list = self.persons.copy()
        random.shuffle(person_list)
        alphabet = "abcdefghijklmnopqrstuvwxyz"
        names_list = existing_names_pool.copy()

        self.abstract_translations = [key[0:num_chars] for key in self.abstract_relations_names.keys()]
        for i in range(len(person_list)):
            person = person_list[i]
            first_letter = alphabet[i]
            person.name = generate_name(first_letter, existing_names_pool)
            names_list.append(person.name)
            self.abstract_translations.append(person.name[0:num_chars])

        for i in range(len(person_list)):
            person_list[i].abstract_name = generate_random_translation(self.abstract_translations, num_chars)
            self.abstract_translations.append(person_list[i].abstract_name)
        
        for relation_key in self.abstract_relations_names:
            self.abstract_relations_names[relation_key] = generate_random_translation(self.abstract_translations, num_chars)
            self.abstract_translations.append(self.abstract_relations_names[relation_key])
        return names_list
    
    def get_names(self, representation_type=Representation.ENGLISH):
        """
        Get the names of all persons in the universe.
        
        Args:
            representation_type (Representation): The representation type to use for names
        """
        name_prop = "name"
        if representation_type == Representation.ABSTRACT:
            name_prop = "abstract_name"
        return sorted([getattr(person, name_prop) for person in self.persons])

    def generate_example(self):
        """Generate an example relation and disable it for experimental purposes"""
        examples = self.generate_relations(2, 2, avoid_cycles=True)
        self.example = random.choice(examples)
        self.disable_edge(self.example)
    
    def disable_edge(self, edge_dict):
        """
        Disable an edge in the universe.

        Args:
            edge_dict: Dictionary with keys 'path', 'relation_types', 'answer', 'start'
        """
        for i in range(len(edge_dict["relation_types"])):
            relation_type = edge_dict["relation_types"][i]
            person_node = edge_dict["path"][i]
            person_node.friend["disabled"] = relation_type == "friend"
            person_node.enemy["disabled"] = relation_type == "enemy"
            person_node.parent["disabled"] = relation_type == "parent"
            person_node.child["disabled"] = relation_type == "child"

    def generate_relations(self, min_relations_count, max_relations_count, include_disabled_edges=False, avoid_cycles=False):
        """
        Generate relations between persons in the universe.

        Args:
            min_relations_count (int): Minimum length of relations to include
            max_relations_count (int): Maximum length of relations to include  
            include_disabled_edges (bool): Whether to include disabled edges
            avoid_cycles (bool): If True, paths will not revisit the same person

        Returns:
            list: List of edge dictionaries with relationship information
        """
        relations_list = []

        def generate_relation_recursive(current_person, person_path_list, relation_types_list, start_person):
            if current_person is None:
                return
            if len(person_path_list) > max_relations_count + 1:
                return
            if len(person_path_list) >= min_relations_count + 1:
                relations_list.append({
                    'path': person_path_list.copy(),
                    'relation_types': relation_types_list.copy(),
                    'answer': current_person,
                    'start': start_person
                })
            
            next_steps = []
            if self.rel_num >= 1:
                friend_node = current_person.get_friend(include_disabled_edges)
                if friend_node:
                    next_steps.append(('friend', friend_node))
            if self.rel_num >= 2:
                enemy_node = current_person.get_enemy(include_disabled_edges)
                if enemy_node:
                    next_steps.append(('enemy', enemy_node))
            if self.rel_num >= 3:
                child_node = current_person.get_child(include_disabled_edges)
                if child_node:
                    next_steps.append(('child', child_node))
            if self.rel_num >= 4:
                parent_node = current_person.get_parent(include_disabled_edges)
                if parent_node:
                    next_steps.append(('parent', parent_node))

            for relation_type, next_person in next_steps:
                if avoid_cycles and next_person in person_path_list:
                    continue
                generate_relation_recursive(
                    next_person,
                    person_path_list + [next_person],
                    relation_types_list + [relation_type],
                    start_person
                )

        for person in self.persons:
            generate_relation_recursive(person, [person], [], person)

        return relations_list

    def generate_intensional_universe(self):
        """Generate the intensional universe representation"""
        result = []
        for relation in range(0, 5):
            if relation + 1 >= len(self.persons):
                break
                
            relation1 = ""
            if relation == 0:
                relation1 = "friend"
            elif relation == 2:
                relation1 = "enemy"
            elif relation == 4:
                relation1 = "parent"
                
            relation2 = relation1
            if relation == 4:
                relation2 = "child"
                
            if relation1:
                dummy_person = PersonNode(-1)
                dummy_person.name = "none"
                dummy_person.abstract_name = "none"
                
                def get_relation_answer(person, relation_type):
                    if relation_type == "friend":
                        return person.friend["node"] if person.friend["node"] is not None else dummy_person
                    elif relation_type == "enemy":
                        return person.enemy["node"] if person.enemy["node"] is not None else dummy_person
                    elif relation_type == "parent":
                        return person.parent["node"] if person.parent["node"] is not None else dummy_person
                    elif relation_type == "child":
                        return person.child["node"] if person.child["node"] is not None else dummy_person
                    return dummy_person
                
                answer1 = get_relation_answer(self.persons[relation], relation1)
                answer2 = get_relation_answer(self.persons[relation + 1], relation2)
                
                if relation1:
                    result.append({
                        'path': [self.persons[relation], self.persons[relation + 1]],
                        'relation_types': [relation1],
                        'answer': answer1,
                        'start': self.persons[relation]
                    })
                if relation2:
                    result.append({
                        'path': [self.persons[relation + 1], self.persons[relation]],
                        'relation_types': [relation2],
                        'answer': answer2,
                        'start': self.persons[relation + 1]
                    })
        return result

    def edge_to_sentence(self, person_path_list, relation_types_list, representation_type, branching_type):
        """
        Convert an edge to a sentence in the given representation type.

        Args:
            person_path_list: List of PersonNode instances representing the relation path
            relation_types_list: List of relation type strings
            representation_type (Representation): The representation type to use
            branching_type (Branching): The branching type to use

        Returns:
            str: The sentence representation
        """
        if len(person_path_list) == 1:
            return person_path_list[0].name
        elif branching_type == Branching.RIGHT:
            return f"the {relation_types_list[-1]} of {self.edge_to_sentence(person_path_list[:-1], relation_types_list[:-1], representation_type, branching_type)}"
        elif branching_type == Branching.LEFT:
            return f"{self.edge_to_sentence(person_path_list[:-1], relation_types_list[:-1], representation_type, branching_type)}'s {relation_types_list[-1]}"

    def edge_to_intensional(self, person_path_list, relation_types_list, representation_type):
        """Convert an edge to an intensional representation"""
        if len(person_path_list) == 1:
            if representation_type == Representation.ENGLISH:
                return person_path_list[0].name.lower()
            elif representation_type == Representation.ABSTRACT:
                return person_path_list[0].abstract_name
        else:
            relationship_name = relation_types_list[-1]
            if representation_type == Representation.ABSTRACT:
                relationship_name = self.abstract_relations_names[relationship_name]
            return f"{relationship_name}({self.edge_to_intensional(person_path_list[:-1], relation_types_list[:-1], representation_type)})"

    def edge_to_answer(self, edge_dict, representation_type, semantic_approach):
        """Convert an edge to an answer in the given representation type and approach"""
        if semantic_approach == SemanticApproach.EXTENSIONAL:
            if representation_type == Representation.ENGLISH:
                return edge_dict['answer'].name
            elif representation_type == Representation.ABSTRACT:
                return edge_dict['answer'].abstract_name
        elif semantic_approach == SemanticApproach.INTENSIONAL:
            return self.edge_to_intensional(edge_dict['path'], edge_dict['relation_types'], representation_type)

    def edge_to_id(self, person_path_list, relation_types_list):
        """Convert edge to a unique string identifier"""
        if len(person_path_list) == 1:
            return person_path_list[0].id
        else:
            return f"{relation_types_list[-1][0]}{self.edge_to_id(person_path_list[:-1], relation_types_list[:-1])}"

    def save_universe(self, filename):
        """Save the universe to a CSV file"""
        universe_dir = get_output_directory('universes')
        filepath = os.path.join(universe_dir, filename)
        
        fieldnames = ["id", "name", "abstract_name", "friend", "enemy", "parent", "child", 
                     "friend_disabled", "enemy_disabled", "parent_disabled", "child_disabled"]
        
        for relation in self.abstract_relations_names:
            fieldnames.append(f"abstract_{relation}_name")
            
        with open(filepath, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for person in self.persons:
                row = {
                    "id": person.id,
                    "name": person.name,
                    "abstract_name": person.abstract_name,
                    "friend": person.friend["node"].id if person.friend["node"] is not None else "",
                    "enemy": person.enemy["node"].id if person.enemy["node"] is not None else "",
                    "parent": person.parent["node"].id if person.parent["node"] is not None else "",
                    "child": person.child["node"].id if person.child["node"] is not None else "",
                    "friend_disabled": person.friend["disabled"],
                    "enemy_disabled": person.enemy["disabled"],
                    "parent_disabled": person.parent["disabled"],
                    "child_disabled": person.child["disabled"]
                }
                
                for relation, abstract_name in self.abstract_relations_names.items():
                    row[f"abstract_{relation}_name"] = abstract_name
                    
                writer.writerow(row)

    @staticmethod
    def load_universe(filename):
        """Load a universe from a CSV file"""
        universe_dir = get_output_directory('universes')
        filepath = os.path.join(universe_dir, filename)
        persons_dict = {}
        rows = []
        abstract_relations_names = {}
        
        with open(filepath, newline='', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                rows.append(row)
                pid = int(row["id"])
                p = PersonNode(pid)
                p.name = row["name"]
                p.abstract_name = row["abstract_name"]
                persons_dict[pid] = p
                
                if not abstract_relations_names:
                    for column in row:
                        if column.startswith("abstract_") and column.endswith("_name"):
                            relation = column[9:-5]
                            abstract_relations_names[relation] = row[column]

        disabled_edges = []
        for row in rows:
            pid = int(row["id"])
            person = persons_dict[pid]
            if row["friend"]:
                friend_id = int(row["friend"])
                person.friend["node"] = persons_dict.get(friend_id)
                person.friend["disabled"] = row["friend_disabled"].lower() == "true"
                if person.friend["disabled"]:
                    disabled_edges.append(("friend", person, person.friend["node"]))
            if row["enemy"]:
                enemy_id = int(row["enemy"])
                person.enemy["node"] = persons_dict.get(enemy_id)
                person.enemy["disabled"] = row["enemy_disabled"].lower() == "true"
                if person.enemy["disabled"]:
                    disabled_edges.append(("enemy", person, person.enemy["node"]))
            if row["parent"]:
                parent_id = int(row["parent"])
                person.parent["node"] = persons_dict.get(parent_id)
                person.parent["disabled"] = row["parent_disabled"].lower() == "true"
                if person.parent["disabled"]:
                    disabled_edges.append(("parent", person, person.parent["node"]))
            if row["child"]:
                child_id = int(row["child"])
                person.child["node"] = persons_dict.get(child_id)
                person.child["disabled"] = row["child_disabled"].lower() == "true"
                if person.child["disabled"]:
                    disabled_edges.append(("child", person, person.child["node"]))

        universe_instance = Universe(relation_count=4, person_pairs_count=len(persons_dict) // 2)
        universe_instance.persons = list(persons_dict.values())
        
        if abstract_relations_names:
            universe_instance.abstract_relations_names = abstract_relations_names
        
        if disabled_edges:
            relation_type, start_person, end_person = disabled_edges[0]
            _, _, answer = disabled_edges[-1]
            universe_instance.example = {
                'path': [start_person],
                'relation_types': [],
                'start': start_person,
                'answer': answer
            }
            for relation_type, start_person, end_person in disabled_edges:
                universe_instance.example["path"].append(end_person)
                universe_instance.example["relation_types"].append(relation_type)
        
        return universe_instance

    def visualize_relations(self, name=None, include_disabled_edges=False):
        """Visualize the relationships as a graph with directional edges and relation labels"""
        G, edge_info = self._build_graph(include_disabled_edges)
        
        node_positions = nx.spring_layout(G, seed=5)
        fig, ax = plt.subplots(figsize=(14, 14))
        
        self._draw_nodes(G, node_positions, ax)
        self._draw_edges(G, node_positions, edge_info, ax, include_disabled_edges)
        self._draw_edge_labels(G, node_positions, edge_info['labels'])
        
        self._save_graph_image(fig, name)

    def _build_graph(self, include_disabled_edges=False):
        """Build the graph structure with nodes and edges"""
        G = nx.DiGraph()
        
        edge_info = {
            'regular': [],
            'disabled': [],
            'labels': {}
        }
        
        for person in self.persons:
            G.add_node(person.name)
        
        for person in self.persons:
            relationships = [
                ('friend', person.friend),
                ('enemy', person.enemy),
                ('parent', person.parent),
                ('child', person.child)
            ]
            
            for relation_type, relation_data in relationships:
                if relation_data["node"] is not None and (include_disabled_edges or not relation_data["disabled"]):
                    self._add_edge_to_graph(
                        G, 
                        relation_data["node"].name,
                        person.name,
                        relation_type, 
                        relation_data["disabled"], 
                        edge_info
                    )
        
        return G, edge_info

    def _add_edge_to_graph(self, graph, node1, node2, relation, is_disabled, edge_info):
        """Add or update an edge in the graph with proper labeling"""
        if graph.has_edge(node1, node2):
            current_label = graph[node1][node2]['relation']
            if relation not in current_label.split('/'):
                graph[node1][node2]['relation'] += f'/{relation}'
        else:
            graph.add_edge(node1, node2, relation=relation, disabled=is_disabled)
        
        if is_disabled:
            edge_info['disabled'].append((node1, node2))
        else:
            edge_info['regular'].append((node1, node2))
        
        edge_info['labels'][(node1, node2)] = graph[node1][node2]['relation']

    def _draw_nodes(self, G, positions, ax):
        """Draw and label the nodes"""
        nx.draw_networkx_nodes(G, pos=positions, node_size=500, node_color='skyblue', ax=ax)
        nx.draw_networkx_labels(G, pos=positions, font_size=16, font_weight='bold')

    def _draw_edges(self, G, positions, edge_info, ax, include_disabled_edges):
        """Draw regular and disabled edges with appropriate styling"""
        if edge_info['regular']:
            nx.draw_networkx_edges(
                G, pos=positions, edgelist=edge_info['regular'],
                arrowstyle='->', arrowsize=15, connectionstyle='arc3,rad=0.1',
                edge_color='blue', ax=ax
            )
        
        if include_disabled_edges and edge_info['disabled']:
            nx.draw_networkx_edges(
                G, pos=positions, edgelist=edge_info['disabled'],
                arrowstyle='->', arrowsize=15, connectionstyle='arc3,rad=0.1',
                edge_color='red', style='dashed', ax=ax
            )

    def _draw_edge_labels(self, G, positions, edge_labels):
        """Draw edge labels at optimal positions"""
        for (node1, node2), label in edge_labels.items():
            has_reverse = G.has_edge(node2, node1)
            x_pos, y_pos = self._calculate_label_position(positions, node1, node2, has_reverse)
            
            plt.text(
                x_pos, y_pos, label, fontsize=14,
                bbox=dict(facecolor='white', alpha=0.8, edgecolor='none', pad=2),
                horizontalalignment='center', verticalalignment='center'
            )

    def _calculate_label_position(self, positions, node1, node2, has_reverse=False):
        """Calculate the optimal position for an edge label"""
        x1, y1 = positions[node1]
        x2, y2 = positions[node2]
        
        mid_x = (x1 + x2) / 2
        mid_y = (y1 + y2) / 2
        
        if has_reverse:
            dx = x2 - x1
            dy = y2 - y1
            length = (dx**2 + dy**2)**0.5
            
            if length > 0:
                perpx = -dy / length
                perpy = dx / length
                
                offset_factor = 0.07
                mid_x += perpx * offset_factor * length
                mid_y += perpy * offset_factor * length
        
        return mid_x, mid_y

    def _save_graph_image(self, fig, name=None):
        """Save the graph visualization to an image file"""
        if name is None:
            from datetime import datetime
            dt_string = datetime.now().strftime("%d_%m_%Y_%H_%M_%S")
            name = f"relations-{len(self.persons)}-{dt_string}"
        
        img_dir = get_output_directory('img')
        fig.savefig(os.path.join(img_dir, f"{name}.png"), bbox_inches='tight', pad_inches=0)
        plt.close(fig)
