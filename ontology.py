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

class Entities(Enum):
    VILLAGE = 0
    CITY = 1
    MINE = 2
    ROAD = 3
    RIVER = 4

class Relations(Enum):
    LOCATED_NEAR = 0
    LOCATED_IN = 1
    CONNECTS_TO = 2

valid_relations_from = {
    Entities.VILLAGE : {Relations.LOCATED_NEAR, Relations.LOCATED_IN, Relations.CONNECTS_TO},
    Entities.CITY : {Relations.LOCATED_NEAR, Relations.LOCATED_IN, Relations.CONNECTS_TO},
    Entities.MINE : {Relations.LOCATED_NEAR, Relations.LOCATED_IN, Relations.CONNECTS_TO},
}

valid_relations_to = {
    Biome.OCEAN : {Relations.LOCATED_NEAR, Relations.LOCATED_IN},
    Biome.BEACH : {Relations.LOCATED_NEAR, Relations.LOCATED_IN},
    Biome.DESERT : {Relations.LOCATED_NEAR, Relations.LOCATED_IN},
    Biome.GRASSLAND : {Relations.LOCATED_NEAR, Relations.LOCATED_IN},
    Biome.SWAMP : {Relations.LOCATED_NEAR, Relations.LOCATED_IN},
    Biome.ROCKY_MOUNTAIN : {Relations.LOCATED_NEAR, Relations.LOCATED_IN},
    Biome.TUNDRA : {Relations.LOCATED_NEAR, Relations.LOCATED_IN},
    Biome.SNOWY_MOUNTAIN : {Relations.LOCATED_NEAR, Relations.LOCATED_IN},    
    Entities.RIVER : {Relations.LOCATED_NEAR},
    Entities.RIVER: {Relations.CONNECTS_TO},
    Entities.VILLAGE : {Relations.LOCATED_NEAR, Relations.CONNECTS_TO},
    Entities.CITY : {Relations.LOCATED_NEAR, Relations.CONNECTS_TO},
    Entities.MINE : {Relations.LOCATED_NEAR, Relations.CONNECTS_TO},
}