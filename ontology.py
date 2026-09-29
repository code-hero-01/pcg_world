from enum import Enum

class Biome(Enum):
    OCEAN = 0
    BEACH = 1
    DESERT = 2
    GRASSLAND = 3
    FOREST = 4
    SWAMP = 5
    ROCKY_MOUNTAIN = 6
    TUNDRA = 7
    SNOWY_MOUNTAIN = 8

class Location(Enum):
    VILLAGE = 100
    CITY = 101
    MINE = 102

class NaturalFeature(Enum):
    RIVER = 200

class Infrastructure(Enum):
    ROAD = 300

class Relation(Enum):
    LOCATED_NEAR = 0
    LOCATED_IN = 1
    CONNECTS_TO = 2

VALID_RELATIONS_FROM = {
    Location.VILLAGE : {Relation.LOCATED_NEAR, Relation.LOCATED_IN, Relation.CONNECTS_TO},
    Location.CITY : {Relation.LOCATED_NEAR, Relation.LOCATED_IN, Relation.CONNECTS_TO},
    Location.MINE : {Relation.LOCATED_NEAR, Relation.LOCATED_IN, Relation.CONNECTS_TO},
}

VALID_RELATIONS_TO = {
    Biome.OCEAN : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.BEACH : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.DESERT : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.GRASSLAND : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.SWAMP : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.ROCKY_MOUNTAIN : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.TUNDRA : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.SNOWY_MOUNTAIN : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},    
    NaturalFeature.RIVER : {Relation.LOCATED_NEAR},
    Infrastructure.ROAD : {Relation.CONNECTS_TO},
    Location.VILLAGE : {Relation.LOCATED_NEAR, Relation.CONNECTS_TO},
    Location.CITY : {Relation.LOCATED_NEAR, Relation.CONNECTS_TO},
    Location.MINE : {Relation.LOCATED_NEAR, Relation.CONNECTS_TO},
}

class SpatialType(Enum):
    REGION = 0       # biomes (oceans, forests...)
    POINT = 1        # entities (villages, cities, mines...)
    PATH = 2         # paths (rivers, roads...)

SPATIAL_TYPE = {
    Biome.OCEAN: SpatialType.REGION,
    Biome.BEACH: SpatialType.REGION,
    Biome.DESERT: SpatialType.REGION,
    Biome.GRASSLAND: SpatialType.REGION,
    Biome.FOREST: SpatialType.REGION,
    Biome.SWAMP: SpatialType.REGION,
    Biome.ROCKY_MOUNTAIN: SpatialType.REGION,
    Biome.TUNDRA: SpatialType.REGION,
    Biome.SNOWY_MOUNTAIN: SpatialType.REGION,

    Location.VILLAGE: SpatialType.POINT,
    Location.CITY: SpatialType.POINT,
    Location.MINE: SpatialType.POINT,

    NaturalFeature.RIVER: SpatialType.PATH,
    Infrastructure.ROAD: SpatialType.PATH,
}



