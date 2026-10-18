import networkx as nx
from matplotlib import pyplot as plt 
import ontology
import json

class WorldKG:
    def __init__(self):
        pass

    def load_graph(self, file_path : str):
        with open(file_path, "r") as f:
            data = json.load(f)

        for node in data["nodes"]:
            try:
                node["entity_type"] = ontology.EntityType[node["entity_type"]]
            except ValueError:
                print(f"Invalid entity type for node {node}")

        for edge in data["edges"]:
            try:
                edge["relation_type"] = ontology.RelationType[edge["relation_type"]]
            except ValueError:
                print(f"Invalid relation type for edge: {edge}")

        self.graph = nx.readwrite.json_graph.node_link_graph(
                        data, 
                        directed=True, 
                        multigraph=True
                    )
        
            
    def get_entity_type(self, entity):
        return self.graph.nodes[entity].get('entity_type')

    def post_order_dfs(self):
        return list(nx.dfs_postorder_nodes(self.graph))

    def collect_relations(self):
        relations = []

        for source, target, key, data in self.graph.edges(
            keys=True, data=True
        ):
            relation = {
                "source": source,
                "target": target,
                "relation_type": data["relation_type"],
                "properties": {
                    k: v for k, v in data.items()
                    if k != "relation_type"
                }
            }

            relations.append(relation)

        return relations
    
    def get_entities_of_type(self, entity_type):
        return [
            node 
            for node, data in self.graph.nodes(data=True) 
            if data.get('type') == entity_type
        ]

    def get_neighbours(self, entity):
        return list(self.graph.neighbors(entity))

    def get_relations_of_entity(self, entity):
        relations = []

        for source, target, key, data in self.graph.out_edges(
            entity, keys=True, data=True
        ):
                relatiion = {
                    "source": source,
                    "target": target,
                    "relation_type": data["relation_type"],
                    "properties": {
                        k: v for k, v in data.items()
                        if k != "relation_type"
                    }
                }

                relations.append(relatiion)

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
        edge_labels = nx.get_edge_attributes(self.graph, 'relation')
        nx.draw_networkx_edge_labels(self.graph, pos, edge_labels=edge_labels, font_color='red', font_size=8)

        plt.title("Entity Constraint Knowledge Graph")
        plt.show()


if __name__ == "__main__":
    kg = WorldKG()
    kg.load_graph("world_knowledge.json")
    kg.visualize()  