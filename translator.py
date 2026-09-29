import ontology
import pcg
import kg

class Translator:
    def __init__(self, kg : kg.WorldKG, world : pcg.World):
        self.kg = kg
        self.world = world
        self.points = {}
        
        self.traverse_graph()

    def traverse_graph(self): 
        order = self.kg.post_order_dfs()
        
        for entity in order:
            entity_type = self.kg.get_entity_type(entity)
            constraints = self.kg.get_constraints(entity)

            if ontology.SPATIAL_TYPE[entity_type] != ontology.SpatialType.POINT:
                continue
            
            self.points[entity] = {
                'entity_type' : entity_type,
                'located_in' : None,
                'located_near' : [],
                'connects_to' : None
            } 

            for constraint in constraints:
                relation = constraint['relation']
                target = constraint['target']
                if relation == ontology.Relation.LOCATED_IN:
                    self.handle_located_in(entity, target)
                if relation == ontology.Relation.LOCATED_NEAR:
                    self.handle_located_near(entity, target)
            
    def handle_located_in(self, point, target):
        self.points[point]['located_in'] = self.kg.get_entity_type(target)

    def handle_located_near(self, point, target):
            if self.points[point]['located_near'] is None:
                self.points[point]['located_near'] = []
            self.points[point]['located_near'].append((self.kg.get_entity_type(target), 10, 30))

    def place_points(self):
        for point in self.points:
            location = self.world.choose_location(
                located_in= self.points[point]['located_in'], 
                located_near= self.points[point]['located_near']
            )

            self.world.place_entity(self.points[point]['entity_type'], location)
        
