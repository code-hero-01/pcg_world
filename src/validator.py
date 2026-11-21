from knowledge import WorldKG
from pcg import World
import ontology
from dataclasses import dataclass
from enum import Enum, auto
import primitives

class ValidationStatus(Enum):
    PASS = auto()
    FAIL = auto()
    ERROR = auto()

@dataclass
class ValidationResult:
    source: str
    relation: str
    target: str
    status: ValidationStatus
    actual_value: object = None
    expected_value: object = None

class WorldValidator:
    def __init__(self, world: World, kg: WorldKG, log_callback=None):
        self.world = world
        self.kg = kg
        self.results = []

        self.entities = {}
        for node_id, node_data in self.kg.graph.nodes(data=True):
            self.entities[node_id] = primitives.Entity(
                entity_id=node_id,
                entity_type=ontology.EntityType[node_data['entity_type']],
                scope=ontology.EntityScope[node_data['scope']]
            )

        self.log_callback = log_callback

    def _log(self, msg: str):
        print(msg)
        if self.log_callback:
            self.log_callback(msg)

    def validate(self):
        self.results.clear()
        
        self._log("Validating world...")
        
        # Iterate through KG relationships.
        # Dispatch to the appropriate validation method.
        relations = self.kg.collect_relations()
        for relation in relations:
            if relation['relation_type'] == ontology.RelationType.LOCATED_IN:
                self.validate_located_in(relation['source'], relation['target'])
            elif relation['relation_type'] == ontology.RelationType.LOCATED_NEAR:
                self.validate_located_near(relation['source'], relation['target'], relation['properties'])
            elif relation['relation_type'] == ontology.RelationType.CONNECTS_TO:
                self.validate_connects_to(relation['source'], relation['target'])
            else: # unsupported relation
                res = ValidationResult(
                    source="", 
                    target="", 
                    relation=relation['relation_type'].name, 
                    status=ValidationStatus.ERROR
                )
                
                self.results.append(res)

        return self.results

    def validate_located_in(self, source, target):
        relation = ontology.RelationType.LOCATED_IN.name
        expected_value = target
        coords = self.world.entities_info.get(source)['coords']
    
        if coords is None:
            actual_value = None
        else:
            row, col = coords
            actual_value = ontology.EntityType(self.world.biomes[row, col]).name

        if actual_value is None:
            status = ValidationStatus.ERROR
        elif expected_value.lower() == actual_value.lower():
            status = ValidationStatus.PASS
        else:
            status = ValidationStatus.FAIL

        res = ValidationResult(
                source=source,
                target=target,
                relation=relation,
                status=status,
                actual_value=actual_value,
                expected_value=expected_value
            )
        
        self.results.append(res)


    def validate_located_near(self, source, target, properties):
        relation = ontology.RelationType.LOCATED_NEAR.name
        expected_value = (properties['min_distance'], properties['max_distance'])
        source_loc = self.world.entities_info.get(source, {}).get('coords')
        
        if source_loc is None:
            status = ValidationStatus.ERROR
            actual_value = None
        else:
            actual_value = self.world.find_distance(source_loc, self.entities[target])
            
            # an actual_value of -1 means the target entity was completely unreachable or missing on the map
            if actual_value == -1:
                status = ValidationStatus.ERROR
                actual_value = None
            elif (actual_value <= properties['max_distance'] and actual_value >= properties['min_distance']):
                status = ValidationStatus.PASS
            else:
                status = ValidationStatus.FAIL

        res = ValidationResult(
            source=source,
            target=target,
            relation=relation,
            status=status,
            actual_value=actual_value,
            expected_value=expected_value
        )
                
        self.results.append(res)

    def validate_connects_to(self, source, target):
        relation = ontology.RelationType.CONNECTS_TO.name
        source_loc = self.world.entities_info.get(source, {}).get('coords')
        target_loc = self.world.entities_info.get(target, {}).get('coords')
        expected_value = "Road connecting source and target"

        if (source_loc is None or target_loc is None):
            status = ValidationStatus.ERROR
            actual_value = None
        else:
            road = self.world.road_coords.get((source, target))
            if road is None:
                status = ValidationStatus.FAIL
                actual_value = None
            else:
                status = ValidationStatus.PASS
                actual_value = len(road)

        res = ValidationResult(
                    source=source,
                    target=target,
                    relation=relation,
                    status=status,
                    expected_value=expected_value,
                    actual_value=actual_value
                )
                         
        self.results.append(res)       
            

    def generate_report(self):
        self._log("Validation Report:")
        if (len(self.results) == 0):
            self._log("Nothing to evaluate!")
            return
        
        passed = 0
        failed = 0
        error = 0
        for result in self.results:
            self._log(f"{result.relation}: {result.status.name}")
            self._log(f"source: {result.source}, target: {result.target}")
            self._log(f"expected: {result.expected_value}, actual: {result.actual_value}")
            self._log("---")

            if result.status == ValidationStatus.PASS:
                passed += 1
            elif result.status == ValidationStatus.FAIL:
                failed += 1
            elif result.status == ValidationStatus.ERROR:
                error += 1

        self._log(f"Satisfaction Rate = {passed / (passed + failed + error) * 100} %")
    
