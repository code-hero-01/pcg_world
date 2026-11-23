from enum import Enum, auto
from dataclasses import dataclass

class EntityType(Enum):
    # biomes
    UNKOWN = 0
    OCEAN = auto()
    BEACH = auto()
    DESERT = auto()
    GRASSLAND = auto()
    FOREST = auto()
    SWAMP = auto()
    ROCKY_MOUNTAIN = auto()
    TUNDRA = auto()
    SNOWY_MOUNTAIN = auto()

    VILLAGE = auto()
    CITY = auto()
    MINE = auto()
    PORT = auto()

    RIVER = auto()

    ROAD = auto()

class RelationType(Enum):
    LOCATED_NEAR = auto()
    LOCATED_IN = auto()
    CONNECTS_TO = auto()
    AVOIDS = auto()
    SUPPLIES = auto()

class SpatialType(Enum): 
    BIOME = 0        # large regions (oceans, forests...)
    POINT = 1        # singe-cell entities (villages, cities, mines...)
    FEATURE = 2      # multi-cell entities

class EntityScope(Enum): 
    CLASS = 0        
    INSTANCE = 1      

SPATIAL_TYPE_MAP = {
    EntityType.OCEAN: SpatialType.BIOME,
    EntityType.BEACH: SpatialType.BIOME,
    EntityType.DESERT: SpatialType.BIOME,
    EntityType.GRASSLAND: SpatialType.BIOME,
    EntityType.FOREST: SpatialType.BIOME,
    EntityType.SWAMP: SpatialType.BIOME,
    EntityType.ROCKY_MOUNTAIN: SpatialType.BIOME,
    EntityType.TUNDRA: SpatialType.BIOME,
    EntityType.SNOWY_MOUNTAIN: SpatialType.BIOME,

    EntityType.VILLAGE: SpatialType.POINT,
    EntityType.CITY: SpatialType.POINT,
    EntityType.MINE: SpatialType.POINT,
    EntityType.PORT: SpatialType.POINT,

    EntityType.RIVER: SpatialType.FEATURE,
    EntityType.ROAD: SpatialType.FEATURE,
}

SPAWNABLE = {
    EntityType.VILLAGE,
    EntityType.CITY,
    EntityType.MINE,
    EntityType.PORT,
}


VALID_RELATIONS_FROM = {
    EntityType.VILLAGE : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.CONNECTS_TO, RelationType.AVOIDS},
    EntityType.CITY : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.CONNECTS_TO, RelationType.AVOIDS},
    EntityType.MINE : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.CONNECTS_TO, RelationType.AVOIDS, RelationType.SUPPLIES},
    EntityType.PORT : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.CONNECTS_TO, RelationType.AVOIDS}
}

VALID_RELATIONS_TO = {
    EntityType.OCEAN : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.AVOIDS},
    EntityType.BEACH : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.AVOIDS},
    EntityType.DESERT : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.AVOIDS},
    EntityType.GRASSLAND : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.AVOIDS},
    EntityType.FOREST : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.AVOIDS},
    EntityType.SWAMP : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.AVOIDS},
    EntityType.ROCKY_MOUNTAIN : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.AVOIDS},
    EntityType.TUNDRA : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.AVOIDS},
    EntityType.SNOWY_MOUNTAIN : {RelationType.LOCATED_NEAR, RelationType.LOCATED_IN, RelationType.AVOIDS},    
    EntityType.RIVER : {RelationType.LOCATED_NEAR, RelationType.AVOIDS},
    EntityType.ROAD : {RelationType.LOCATED_NEAR, RelationType.AVOIDS},
    EntityType.VILLAGE : {RelationType.LOCATED_NEAR, RelationType.CONNECTS_TO, RelationType.AVOIDS, RelationType.SUPPLIES},
    EntityType.CITY : {RelationType.LOCATED_NEAR, RelationType.CONNECTS_TO, RelationType.AVOIDS, RelationType.SUPPLIES},
    EntityType.PORT : {RelationType.LOCATED_NEAR, RelationType.CONNECTS_TO, RelationType.AVOIDS, RelationType.SUPPLIES},    
    EntityType.MINE : {RelationType.LOCATED_NEAR, RelationType.CONNECTS_TO, RelationType.AVOIDS},
}

RELATION_ATTRIBUTES = {
    RelationType.LOCATED_IN : {},
    RelationType.LOCATED_NEAR : {'min_distance':15.0, 'max_distance':30.0},
    RelationType.AVOIDS: {'min_distance':100},
    RelationType.CONNECTS_TO : {},
    RelationType.SUPPLIES : {'min_distance':20.0, 'max_distance':45.0},
}
