from dataclasses import dataclass, field
import ontology as ontology
from enum import Enum, auto

@dataclass(frozen=True)
class Entity:
    entity_id: str
    entity_type: ontology.EntityType
    instance: str

@dataclass(frozen=True)
class RegionConstraint:
    region: Entity

    def get_dependencies(self) -> tuple[str,...]:
        return ('biomes', self.region.entity_id)

@dataclass(frozen=True)
class ProximityConstraint:
    target: Entity
    min_distance: int
    max_distance: int

    def get_dependencies(self) -> tuple[str,...]:
        return (self.target.entity_id,)

@dataclass(frozen=True)
class ConnectionConstraint:
    source: Entity
    target: Entity

    def get_dependencies(self) -> tuple[str,...]:
        return ('terrain', self.source.entity_id, self.target.entity_id)

class TaskType(Enum):
    GENERATE_TERRAIN = auto()
    GENERATE_ENTITY = auto()
    GENERATE_CONNECTION = auto()


@dataclass(frozen=True)
class GenerationTask:
    task_id: str  
    task_type: TaskType

    entity: Entity = None

    constraints: list = field(default_factory=list) 

    