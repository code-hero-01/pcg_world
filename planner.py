from enum import Enum, auto
from dataclasses import dataclass, field
import knowledge, translator
import networkx as nx

class Planner:
    def __init__(self):
        self.plan = []
        
    def generate_plan(self, dependencies : list, spawnable_entities : list):
        G = nx.DiGraph()
        G.add_edges_from(dependencies)

        try:
            self.plan = list(nx.lexicographical_topological_sort(G))
            self.plan.reverse()
        except nx.NetworkXUnfeasible:
            cycle = nx.find_cycle(G)   
            print(f"Invalid knowledge graph - cycle found: {cycle}")  

        for entity in spawnable_entities:
            if entity not in self.plan:
                self.plan.append(entity)

if __name__ == "__main__":
    kg = knowledge.WorldKG()
    kg.load_graph("world_knowledge.json")

    translator = translator.Translator(kg)
    dependencies = translator.get_dependencies()
    spawnable_entities = translator.spawnable_entities

    planner = Planner()
    planner.generate_plan(dependencies, spawnable_entities)

    print(planner.plan)

