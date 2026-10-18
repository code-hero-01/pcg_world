import ontology
import pcg
import knowledge
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class RegionConstraint:
    biome: ontology.EntityType # must be a biome type

@dataclass
class ProximityConstraint:
    target: str
    target_type: ontology.EntityType
    min_distance: int
    max_distance: int

@dataclass
class ConnectionConstraint:
    source: str
    target: str

class Translator:
    def __init__(self, kg : knowledge.WorldKG):
        self.kg = kg
        self.relations = self.kg.collect_relations()
        self.spawnable_entities = [
            entity 
            for entity in self.kg.graph.nodes() 
            if self.is_spawnable_entity(entity)
        ]
        self.connections = []

    def is_spawnable_entity(self, entity):
        entity_type = self.kg.get_entity_type(entity)
        return entity_type in ontology.SPAWNABLE

    def translate(self): 
        entity_constraints_map = {
                    entity: []
                    for entity in self.spawnable_entities
                }

        for relation in self.relations:
            if relation['relation_type'] == ontology.RelationType.LOCATED_IN:
                entity_constraints_map[relation['source']].append(
                    RegionConstraint(
                        biome = self.kg.get_entity_type(relation['target'])
                    )
                )

            elif relation['relation_type'] == ontology.RelationType.LOCATED_NEAR:
                entity_constraints_map[relation['source']].append(
                    ProximityConstraint(
                        target = relation['target'],
                        target_type= self.kg.get_entity_type(relation['target']),
                        min_distance = relation['properties']['min_distance'],
                        max_distance = relation['properties']['max_distance']
                    )
                )

            elif relation['relation_type'] == ontology.RelationType.CONNECTS_TO:
                    self.connections.append(
                        ConnectionConstraint(
                            source = relation['source'],
                            target = relation['target']
                        )
                    )

        return entity_constraints_map

    def get_dependencies(self):
        dependencies = []

        for relation in self.relations:
            if relation['relation_type'] == ontology.RelationType.LOCATED_NEAR:
                target_spatial_type = ontology.SPATIAL_TYPE_MAP[self.kg.get_entity_type(relation['target'])]

                if target_spatial_type == ontology.SpatialType.POINT:
                    dependencies.append((relation['source'], relation['target']))
                
        return dependencies
        
if __name__ == "__main__":
    kg = knowledge.WorldKG()
    kg.load_graph("world_knowledge.json")

    translator = Translator(kg)
    constraints = translator.translate()
    print(constraints)