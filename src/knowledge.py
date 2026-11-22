import networkx as nx
from matplotlib import pyplot as plt 
import ontology as ontology
import json
import sys

class WorldKG:
    def __init__(self):
        pass

    def load_graph(self, file_path : str):
        with open(file_path, "r") as f:
            data = json.load(f)

        for node in data["nodes"]:
            if node["entity_type"] not in ontology.EntityType.__members__:
                print(f"Invalid entity type for node {node}")
                sys.exit()

        for edge in data["edges"]:
            if edge["relation_type"] not in ontology.RelationType.__members__:
                print(f"Invalid relation type for edge: {edge}")
                sys.exit()

        self.graph = nx.readwrite.json_graph.node_link_graph(
                        data, 
                        directed=True, 
                        multigraph=True,
                        key="relation_type"
                    )
        
            
    def get_entity_type(self, entity):
        return ontology.EntityType[self.graph.nodes[entity].get('entity_type')]

    def post_order_dfs(self):
        return list(nx.dfs_postorder_nodes(self.graph))

    def rename_node(self, old_id:str, new_id:str):
        self.graph = nx.relabel_nodes(self.graph, {old_id : new_id})

    def collect_relations(self):
        relations = []

        for source, target, key, data in self.graph.edges(
            keys=True, data=True
        ):
            relation = {
                "source": source,
                "target": target,
                "relation_type": ontology.RelationType[key],
                "properties": {
                    k: v for k, v in data.items()
                    if k != "relation_type"
                }
            }

            relations.append(relation)

        return relations
    
    def get_entities_of_type(self, entity_type):
        return [
            id 
            for id, data in self.graph.nodes(data=True) 
            if data.get('entity_type') == entity_type
        ]

    def get_neighbours(self, entity):
        return list(self.graph.neighbors(entity))

    def get_relations_of_entity(self, entity):
        relations = []

        for source, target, key, data in self.graph.out_edges(
            entity, keys=True, data=True
        ):
                relation = {
                    "source": source,
                    "target": target,
                    "relation_type": ontology.RelationType[key],
                    "properties": {
                        k: v for k, v in data.items()
                        if k != "relation_type"
                    }
                }

                relations.append(relation)

        return relations

    def visualize(self):
        pos = nx.spring_layout(self.graph, seed=0, k=1)

        # draw nodes and arrows
        nx.draw(
            self.graph, pos, 
            with_labels=True, 
            node_color='lightblue', 
            node_size=1500, 
            font_size=8,
            font_weight='bold',
            arrowsize=18
        )

        # draw edge labels (relationship names)
        edge_labels = {}
        for u, v, key in self.graph.edges(keys=True):
            if (u, v) in edge_labels:
                # Combine labels if multiple edges exist between the same two nodes
                edge_labels[(u, v)] += f", {key.name}"
            else:
                edge_labels[(u, v)] = str(key.name)

        nx.draw_networkx_edge_labels(
            self.graph, pos, 
            edge_labels=edge_labels, 
            font_color='red', 
            font_size=8
        )

        plt.title("Entity Constraint Knowledge Graph")
        plt.show()

    def save_graph(self, filepath: str):
        data = nx.node_link_data(self.graph, key='relation_type')
        
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                data,
                f, 
                indent=4, 
            )
            
if __name__ == "__main__":
    kg = WorldKG()
    kg.load_graph("data/world_knowledge.json")
    kg.visualize()
    kg.save_graph("kg2.json")  