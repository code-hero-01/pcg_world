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

class Entity(Enum):
    VILLAGE = 0
    CITY = 1
    MINE = 2
    ROAD = 3
    RIVER = 4

class Relation(Enum):
    LOCATED_NEAR = 0
    LOCATED_IN = 1
    CONNECTS_TO = 2

valid_relations_from = {
    Entity.VILLAGE : {Relation.LOCATED_NEAR, Relation.LOCATED_IN, Relation.CONNECTS_TO},
    Entity.CITY : {Relation.LOCATED_NEAR, Relation.LOCATED_IN, Relation.CONNECTS_TO},
    Entity.MINE : {Relation.LOCATED_NEAR, Relation.LOCATED_IN, Relation.CONNECTS_TO},
}

valid_relations_to = {
    Biome.OCEAN : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.BEACH : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.DESERT : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.GRASSLAND : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.SWAMP : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.ROCKY_MOUNTAIN : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.TUNDRA : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},
    Biome.SNOWY_MOUNTAIN : {Relation.LOCATED_NEAR, Relation.LOCATED_IN},    
    Entity.RIVER : {Relation.LOCATED_NEAR},
    Entity.ROAD: {Relation.CONNECTS_TO},
    Entity.VILLAGE : {Relation.LOCATED_NEAR, Relation.CONNECTS_TO},
    Entity.CITY : {Relation.LOCATED_NEAR, Relation.CONNECTS_TO},
    Entity.MINE : {Relation.LOCATED_NEAR, Relation.CONNECTS_TO},
}