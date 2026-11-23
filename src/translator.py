import ontology
import knowledge as knowledge
import primitives as primitives
import math

class Translator:
    def __init__(self, kg : knowledge.WorldKG):
        self.kg = kg
        self.entities = {}
        self.spawnable_entities = []

        self.connections = []

        self.entity_constraints_map = {}
        self.tasks = []

        self.relation_handler = {
            ontology.RelationType.LOCATED_IN: self.handle_located_in,
            ontology.RelationType.LOCATED_NEAR: self.handle_located_near,
            ontology.RelationType.CONNECTS_TO: self.handle_connected,
            ontology.RelationType.AVOIDS: self.handle_avoids,
            ontology.RelationType.TRADES_WITH: self.handles_trade,
        }

    def is_spawnable_entity(self, entity):
        return entity.entity_type in ontology.SPAWNABLE and entity.scope == ontology.EntityScope.INSTANCE

    def expand_relation(self, relation) -> list: 
        source_entity = self.entities[relation['source']]

        relations = []
        
        if source_entity.scope == ontology.EntityScope.CLASS:
            for entity_id in self.expand_class(source_entity.entity_type):
                if entity_id not in self.spawnable_entities:
                    continue

                new_relation = {
                    "source": entity_id,
                    "target": relation['target'],
                    "relation_type": relation['relation_type'],
                    "properties": relation['properties']
                } 

                relations.append(new_relation)
        else:
            relations.append(relation)
      
        return relations

    def expand_class(self, entity_type : ontology.EntityType):
        entity_ids = []

        for entity_id in self.kg.get_entities_of_type(entity_type.name):
            if entity_id not in self.spawnable_entities:
                continue
            entity_ids.append(entity_id)

        return entity_ids

    def translate(self): 
        self.entities = {}
        for node_id, node_data in self.kg.graph.nodes(data=True):
            self.entities[node_id] = primitives.Entity(
                entity_id=node_id,
                entity_type=ontology.EntityType[node_data['entity_type']],
                scope=ontology.EntityScope[node_data['scope']]
            )

        self.spawnable_entities = [
                        entity_id 
                        for entity_id, entity in self.entities.items()
                        if self.is_spawnable_entity(entity)
                    ]
        
        self.entity_constraints_map = {
                    entity: []
                    for entity in self.spawnable_entities
                }
        
        self.relations = {}
        for relation in self.kg.collect_relations():
            for r in self.expand_relation(relation):
                key = (r["source"], r["target"], r["relation_type"])
                self.relations[key] = r

        self.connections = []

        for key, relation in self.relations.items():
            self.relation_handler.get(relation['relation_type'])(relation)

    def handle_located_in(self, relation):
        region_constraint = primitives.RegionConstraint(region = self.entities[relation['target']])
        entity = self.entities[relation['source']]
        self.entity_constraints_map[entity.entity_id].append(region_constraint)

    def handle_located_near(self, relation):
        proximity_constraint = primitives.ProximityConstraint(
            target = self.entities[relation['target']],
            min_distance = relation['properties']['min_distance'],
            max_distance = relation['properties']['max_distance'],
        )

        entity = self.entities[relation['source']]
        self.entity_constraints_map[entity.entity_id].append(proximity_constraint)

    def handle_connected(self, relation):
        connection_constraint = primitives.ConnectionConstraint(
            source = self.entities[relation['source']], 
            target = self.entities[relation['target']]
        )
        
        self.connections.append(connection_constraint)

    def handle_avoids(self, relation):
        proximity_constraint = primitives.ProximityConstraint(
            target = self.entities[relation['target']],
            min_distance = relation['properties']['min_distance'],
            max_distance = math.inf,
        )

        entity = self.entities[relation['source']]
       
        self.entity_constraints_map[entity.entity_id].append(proximity_constraint)

    def handles_trade(self, relation):
        proximity_constraint = primitives.ProximityConstraint(
            target = self.entities[relation['target']],
            min_distance = relation['properties']['min_distance'],
            max_distance = relation['properties']['max_distance'],
        )

        entity = self.entities[relation['source']]
        self.entity_constraints_map[entity.entity_id].append(proximity_constraint)

        connection_constraint = primitives.ConnectionConstraint(
            source = self.entities[relation['source']], 
            target = self.entities[relation['target']]
        )
                
        self.connections.append(connection_constraint)

    def handles_trade(self, relation):
        proximity_constraint = primitives.ProximityConstraint(
            target = self.entities[relation['target']],
            min_distance = relation['properties']['min_distance'],
            max_distance = relation['properties']['max_distance'],
        )

        entity = self.entities[relation['source']]
        self.entity_constraints_map[entity.entity_id].append(proximity_constraint)

        connection_constraint = primitives.ConnectionConstraint(
            source = self.entities[relation['source']], 
            target = self.entities[relation['target']]
        )
                
        self.connections.append(connection_constraint)
        
if __name__ == "__main__":
    kg = knowledge.WorldKG()
    kg.load_graph("world_knowledge.json")

    translator = Translator(kg)
    translator.translate()
    print(translator.entity_constraints_map)
  