import networkx as nx
from matplotlib import pyplot as plt 
import ontology

class WorldKG:
    def __init__(self):
        self.graph = nx.DiGraph()
        self._build_rules()

    def _build_rules(self):
        # biomes
        self.graph.add_node("Forest", type=ontology.Biome.FOREST)
        self.graph.add_node("Mountain", type=ontology.Biome.ROCKY_MOUNTAIN)
        

        # Entities
        self.graph.add_node("Village_1", type=ontology.Entity.VILLAGE)
        self.graph.add_node("City_1", type=ontology.Entity.CITY)
        self.graph.add_node("River_1", type=ontology.Entity.RIVER)
        self.graph.add_node("Mine_1", type=ontology.Entity.MINE)

        # Relationships
        self.graph.add_edge("Village_1", "Forest", relation=ontology.Relation.LOCATED_IN)
        self.graph.add_edge("Village_1", "River_1", relation=ontology.Relation.LOCATED_NEAR)
        self.graph.add_edge("City_1", "Mine_1", relation=ontology.Relation.CONNECTS_TO)
        self.graph.add_edge("City_1", "Village_1", relation=ontology.Relation.CONNECTS_TO)
        self.graph.add_edge("Mine_1", "Mountain", relation=ontology.Relation.LOCATED_IN)

    def get_entities_of_type(self, entity_type):
        return [
            node 
            for node, data in self.graph.nodes(data=True) 
            if data.get('type') == entity_type
        ]

    def get_constraints(self, entity):
        constraints = []

        for neighbour in self.graph.neighbors(entity):
            constraints.append({
                'relation': self.graph[entity][neighbour]['relation'],
                'target' : neighbour
            })

        return constraints

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

kg = WorldKG()
print(kg.get_constraints('Village_1'))
