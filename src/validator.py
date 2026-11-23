from knowledge import WorldKG
from pcg import World
import ontology
from dataclasses import dataclass
from enum import Enum, auto
import primitives
from translator import Translator
import numpy as np

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
    def __init__(self, world: World, kg: WorldKG, translator: Translator, log_callback=None):
        self.world = world
        self.kg = kg
        self.translator = translator
        self.results = []

        self.log_callback = log_callback

    def _log(self, msg: str):
        print(msg)
        if self.log_callback:
            self.log_callback(msg)


    def validate(self):
        self.results.clear()
        
        self._log("Validating world...")
        
        relations = self.translator.relations

        # Iterate through KG relationships.
        # Dispatch to the appropriate validation method.
        for key, relation in relations.items():
            if relation['relation_type'] == ontology.RelationType.LOCATED_IN:
                self.validate_located_in(relation['source'], relation['target'])
            elif relation['relation_type'] == ontology.RelationType.LOCATED_NEAR:
                self.validate_located_near(relation['source'], relation['target'], relation['properties'])
            elif relation['relation_type'] == ontology.RelationType.AVOIDS:
                self.validate_avoids(relation['source'], relation['target'], relation['properties'])
            elif relation['relation_type'] == ontology.RelationType.CONNECTS_TO:
                self.validate_connects_to(relation['source'], relation['target'])
            elif relation['relation_type'] == ontology.RelationType.SUPPLIES:
                self.validate_supplies(relation['source'], relation['target'], relation['properties'])
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
        coords = self.world.entities_info.get(source, {}).get('coords')
    
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
            actual_value = self.world.find_distance(source_loc, self.translator.entities[target])
            
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
        

    def validate_avoids(self, source, target, properties):
            relation = ontology.RelationType.AVOIDS.name
            expected_value = (properties['min_distance'])
            source_loc = self.world.entities_info.get(source, {}).get('coords')
            
            if source_loc is None:
                status = ValidationStatus.ERROR
                actual_value = None
            else:
                actual_value = self.world.find_distance(source_loc, self.translator.entities[target])
                
                # an actual_value of -1 means the target entity was completely unreachable or missing on the map
                if actual_value == -1:
                    status = ValidationStatus.ERROR
                    actual_value = None
                elif (actual_value >= properties['min_distance']):
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
        if self.translator.entities[target].scope == ontology.EntityScope.INSTANCE:
            target_locs = [self.world.entities_info.get(target, {}).get('coords')]
        else:
            target_locs = np.argwhere(self.world.entity_types == self.translator.entities[target].entity_type.value)
        
        expected_value = "Road connecting source and target"

        status = ValidationStatus.FAIL
        actual_value = None
        if (source_loc is None or len(target_locs) == 0):
            status = ValidationStatus.ERROR
            actual_value = None
        else:
            for target_loc in target_locs:
                target = self.world.entities[tuple(target_loc)]
                road = self.world.road_coords.get((source, target))
                
                if road is not None:
                    status = ValidationStatus.PASS
                    actual_value = len(road)
                    break 
        
        res = ValidationResult(
            source=source,
            target=target,
            relation=relation,
            status=status,
            expected_value=expected_value,
            actual_value=actual_value
        )
                         
        self.results.append(res)     

    def validate_supplies(self, source, target, properties):
        relation = ontology.RelationType.SUPPLIES.name
        expected_value = [(properties['min_distance'], properties['max_distance']), 'connecting road']
        source_loc = self.world.entities_info.get(source, {}).get('coords')
        
        if self.translator.entities[target].scope == ontology.EntityScope.INSTANCE:
            target_locs = [self.world.entities_info.get(target, {}).get('coords')]
        else:
            target_locs = np.argwhere(self.world.entity_types == self.translator.entities[target].entity_type.value)

        status = ValidationStatus.FAIL
        if (source_loc is None or len(target_locs) == 0):
            status = ValidationStatus.ERROR
            actual_value = None
        else:
            for target_loc in target_locs:
                target = self.world.entities[tuple(target_loc)]
                road = self.world.road_coords.get((source, target))
                
                if road is not None:
                    distance = self.world.find_distance(source_loc, self.translator.entities[target])

                    if (distance <= properties['max_distance'] and distance >= properties['min_distance']):
                        status = ValidationStatus.PASS
                        actual_value = [distance, len(road)]
                    else:
                        status = ValidationStatus.FAIL
                        actual_value = [distance, len(road)]

                    break 
        
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

        self._log(f"Satisfaction Rate = {passed / (passed + failed + error) * 100 : .2f} %")
    
