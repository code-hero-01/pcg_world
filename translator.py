import ontology
import knowledge
import primitives

class Translator:
    def __init__(self, kg : knowledge.WorldKG):
        self.kg = kg
        self.relations = self.kg.collect_relations()
        self.entities = {}
        self.spawnable_entities = []

        self.connections = []

        self.entity_constraints_map = {}
        self.tasks = []

        self.relation_handler = {
            ontology.RelationType.LOCATED_IN: self.handle_regional_constraint,
            ontology.RelationType.LOCATED_NEAR: self.handle_proximity_constraint,
            ontology.RelationType.CONNECTS_TO: self.handle_connection_constraint
        }

    def is_spawnable_entity(self, entity):
        entity_type = self.kg.get_entity_type(entity)
        return entity_type in ontology.SPAWNABLE

    def translate(self): 
        self.entities = {}
        for node_id, node_data in self.kg.graph.nodes(data= True):
            self.entities[node_id] = primitives.Entity(
                entity_id= node_id,
                entity_type= node_data['entity_type'],
                instance= node_data['instance']
            )

        self.spawnable_entities = [
                        entity_id 
                        for entity_id, entity in self.entities.items()
                        if self.is_spawnable_entity(entity_id)
                    ]
        
        self.entity_constraints_map = {
                    entity: []
                    for entity in self.spawnable_entities
                }

        self.connections = []

        for relation in self.relations:
            self.relation_handler.get(relation['relation_type'])(relation)


    def handle_regional_constraint(self, relation):
        region_constraint = primitives.RegionConstraint(region = self.entities[relation['target']])
        entity = self.entities[relation['source']]
        self.entity_constraints_map[entity.entity_id].append(region_constraint)

    def handle_proximity_constraint(self, relation):
        proximity_constraint = primitives.ProximityConstraint(
                                        target = self.entities[relation['target']],
                                        min_distance = relation['properties']['min_distance'],
                                        max_distance = relation['properties']['max_distance']
                                    )

        entity = self.entities[relation['source']]
        self.entity_constraints_map[entity.entity_id].append(proximity_constraint)

    def handle_connection_constraint(self, relation):
        connection_constraint = primitives.ConnectionConstraint(
            source = self.entities[relation['source']], 
            target = self.entities[relation['target']]
        )
        
        self.connections.append(connection_constraint)

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
    translator.translate()
    print(translator.entity_constraints_map)
  