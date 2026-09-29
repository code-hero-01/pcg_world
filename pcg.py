import numpy as np
import random
import noise
from dataclasses import dataclass
from collections import deque
import heapq
import ontology
import math

@dataclass
class WorldConfig:
    width: int
    length: int

    continent_scale: float = 300
    continent_octaves: int = 2
    continent_persistance: float = 0.5
    continent_lacunarity: float = 2.0

    detail_scale: float = 80
    detail_octaves: int = 6
    detail_pesistance: float = 0.5
    detail_lacunarity: float = 2.0

    moisture_scale: float = 150
    moisture_octaves: int = 6
    moisture_persistance: float = 0.5
    moisture_lacunarity: float = 2.0

    river_threshold: int = 100

class World:
    def __init__(self, config : WorldConfig, seed: int):
        random.seed(seed)

        self.config = config
        self.continent_offset = (random.uniform(0, 1000), random.uniform(0,1000))
        self.detail_offset = (random.uniform(0, 1000), random.uniform(0,1000))
        self.moisture_offset = (random.uniform(0, 1000), random.uniform(0,1000))

        self.ROWS = self.config.length
        self.COLS = self.config.width

        self.continent = np.zeros((self.ROWS, self.COLS))
        self.detail = np.zeros((self.ROWS, self.COLS))
        self.elevation = np.zeros((self.ROWS, self.COLS))
        self.moisture = np.zeros((self.ROWS, self.COLS))
        self.flow_accumulation = np.ones((self.ROWS, self.COLS))
        self.biomes = np.zeros((self.ROWS, self.COLS))
        self.distance_to = {}
        self.entities = np.full((self.ROWS, self.COLS), -1, dtype=np.int32)

        self.rivers = []

    def generate_terrain(self):
        config = self.config

        # generate noise fields
        for y in range(self.ROWS):
            for x in range(self.COLS):
                # continent (Large base shapes)
                cx = x / config.continent_scale + self.continent_offset[0]
                cy = y / config.continent_scale + self.continent_offset[1]
                self.continent[y][x] = noise.pnoise2(cx, cy, octaves=config.continent_octaves, persistence=config.continent_persistance, lacunarity=config.continent_lacunarity)

                # detail (Local mountains and roughness)
                dx = x / config.detail_scale + self.detail_offset[0]
                dy = y / config.detail_scale + self.detail_offset[1]
                self.detail[y][x] = noise.pnoise2(dx, dy, octaves=config.detail_octaves, persistence=config.detail_pesistance, lacunarity=config.detail_lacunarity)

                # moisture
                mx = x / config.moisture_scale + self.moisture_offset[0]
                my = y / config.moisture_scale + self.moisture_offset[1]
                self.moisture[y][x] = noise.pnoise2(mx, my, octaves=self.config.moisture_octaves, persistence=self.config.moisture_persistance, lacunarity=config.moisture_lacunarity)

        # normalize map to [0, 1]
        def normalize(arr):
            return (arr - arr.min()) / (arr.max() - arr.min())

        self.continent = normalize(self.continent)
        self.detail = normalize(self.detail)
        self.moisture = normalize(self.moisture)

        self.elevation = self.continent *  0.6 + self.detail * 0.4

        # apply Island Radial Mask (lowers edges to force large ocean bodies)
        center_x, center_y = self.COLS / 2.0, self.ROWS / 2.0
        max_radius = np.sqrt(center_x**2 + center_y**2) - 10
        
        y_indices, x_indices = np.indices((self.ROWS, self.COLS))
        dist_from_center = np.sqrt((x_indices - center_x)**2 + (y_indices - center_y)**2) / max_radius
        
        # Pull edges down into ocean
        self.elevation = self.elevation * (1.0 - (dist_from_center ** 2))
        self.elevation = normalize(self.elevation)
        
    def generate_biomes(self):
        conditions = [
            self.elevation < 0.30,
            self.elevation < 0.35,

            (self.elevation < 0.7) & (self.moisture < 0.2),
            (self.elevation < 0.7) & (self.moisture < 0.5),
            (self.elevation < 0.7) & (self.moisture < 0.7),
            (self.elevation < 0.7) & (self.moisture <= 1),

            (self.elevation <= 1) & (self.moisture < 0.4),
            (self.elevation <= 1) & (self.moisture < 0.6),
            (self.elevation <= 1) & (self.moisture <= 1)
        ]

        choices = [
            ontology.Biome.OCEAN.value,
            ontology.Biome.BEACH.value,
            ontology.Biome.DESERT.value,
            ontology.Biome.GRASSLAND.value,
            ontology.Biome.FOREST.value,
            ontology.Biome.SWAMP.value,
            ontology.Biome.ROCKY_MOUNTAIN.value,
            ontology.Biome.TUNDRA.value,
            ontology.Biome.SNOWY_MOUNTAIN.value
        ]

        self.biomes = np.select(conditions, choices)

    def calculate_distance_map(self, target):
        if ontology.SPATIAL_TYPE.get(target) == ontology.SpatialType.REGION:
            y_indices, x_indices = np.where(self.biomes == target.value)
        elif ontology.SPATIAL_TYPE.get(target) == ontology.SpatialType.PATH:
            y_indices, x_indices = np.where(self.entities == target.value)
        elif ontology.SPATIAL_TYPE.get(target) == ontology.SpatialType.POINT:
            y_indices, x_indices = np.where(self.entities == target.value)

        # multisource bfs
        distance_to_target = np.full((self.ROWS, self.COLS), -1, dtype=np.int32)
        queue = deque()
        
        for y, x in zip(y_indices, x_indices):
            queue.append((x, y))
            distance_to_target[y, x] = 0

        directions = [
            (-1, -1), (-1, 0), (-1, 1),
            (0, -1),           (0, 1),
            (1, -1),  (1, 0),  (1, 1)
        ]
        
        while queue:
            x, y = queue.popleft()

            for dx, dy in directions:
                nx = x + dx
                ny = y + dy
                if nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS:
                    continue
                if distance_to_target[ny, nx] != -1:
                    continue
                
                dist = 1
                # if abs(dx) == 1 and abs(dy) == 1: # add square root of 2 for diagonal movement
                    # dist = 1.414
                
                distance_to_target[ny, nx] = dist + distance_to_target[y, x]
                                        
                queue.append((nx, ny))

        return distance_to_target

    def distance_between(loc1 : tuple, loc2 : tuple) -> int:
        return math.dist(loc1, loc2)

    def astar_river(self, start: tuple):
        open_set = []
        closed_set = set()
        heapq.heappush(open_set, (0, start))

        directions = [
                    (-1, -1), (-1, 0), (-1, 1),
                    (0, -1),           (0, 1),
                    (1, -1),  (1, 0),  (1, 1)
                ]

        g_cost = {start: 0}
        came_from = {}

        while open_set:
            # get node with lowest f_cost
            current_f, current = heapq.heappop(open_set)
            x, y = current

            if current in closed_set:
                continue

            closed_set.add(current)

            if self.biomes[y, x] == ontology.Biome.OCEAN.value:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start)
                return path[::-1] # return reversed path (start to goal) 

            # explore neighbours
            for dx, dy in directions:
                nx = x + dx
                ny = y + dy
                neighbour = (nx, ny)
                if nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS:
                    continue
                if neighbour in closed_set:
                    continue

                dist = 1.414 if (abs(dx) == 1 and abs(dy) == 1) else 1.0

                # 1. ADD MICRO-TERRAIN TURMOIL NOISE
                # Use a fast noise function to create localized "pockets" of resistance.
                # This forces the river to curve organically like real topography.
                terrain_roughness = noise.pnoise2(
                    nx / 15.0, 
                    ny / 15.0, 
                    octaves=1, 
                    persistence=0.5
                ) * 5.0 # Amplify to influence path choices

                elevation_diff = self.detail[ny, nx] - self.detail[y, x]
            
                if elevation_diff > 0:
                    # Going uphill is heavily penalized
                    elevation_cost = elevation_diff * 150.0 
                elif elevation_diff == 0:
                    # Flat ground is neutral
                    elevation_cost = 0 
                else:
                    # Downhill movement is encouraged
                    elevation_cost = elevation_diff  

                # Combine costs
                movement_cost = dist + elevation_cost + abs(terrain_roughness)
                tentative_g = g_cost[current] + movement_cost

                if tentative_g < g_cost.get(neighbour, float('inf')):
                    g_cost[neighbour] = tentative_g
                    f_score = g_cost[neighbour] + 0.25 * self.distance_to[ontology.Biome.OCEAN][neighbour]   
                    came_from[neighbour] = current
                    heapq.heappush(open_set, (f_score, neighbour))      

    def find_river_starts(self, num_rivers : int) -> list:
        peaks = []
        
        # Avoid the absolute outer edge of the map to prevent index errors
        for y in range(1, self.ROWS - 1):
            for x in range(1, self.COLS - 1):
                # Apply your core biome condi
                # tions first
                if self.detail[y, x] > 0.7 and self.moisture[y, x] > 0.5:
                    
                    # Check if this cell is strictly higher than its 3x3 neighborhood
                    neighborhood = self.detail[y-1:y+2, x-1:x+2]
                    if self.detail[y, x] == np.max(neighborhood):
                        peaks.append((x, y))
        
        # If you have too many peaks, randomly select a clean subset
        if len(peaks) > num_rivers:
            peaks = random.sample(peaks, num_rivers)
        return peaks               

    def generate_rivers(self, num_rivers : int) -> list:
        river_starts = self.find_river_starts(num_rivers)
        if ontology.Biome.OCEAN not in self.distance_to:
            self.distance_to[ontology.Biome.OCEAN] = self.calculate_distance_map(ontology.Biome.OCEAN)

        for start in river_starts:
            path = self.astar_river(start)
            self.rivers.append(path)

        for river in self.rivers:
            for x, y in river:
                self.entities[y, x] = ontology.NaturalFeature.RIVER.value

    def proximity_location_map(self, place, min_distance: int, max_distance: int):
        if place not in self.distance_to:
            self.distance_to[place] = self.calculate_distance_map(place)
        
        return (self.distance_to[place] <= max_distance) & (self.distance_to[place] >= min_distance)

    def choose_location(self, located_in : ontology.Biome = None, located_near : list = None, min_distance = 1, max_distance = 10) -> tuple:
        valid_mask = (self.entities == -1)
    
        if located_in is not None:
            valid_mask &= (self.biomes == located_in.value)

        if located_near is not None:
            for place, min_dist, max_dist in located_near:
                valid_mask &= self.proximity_location_map(place, min_distance, max_distance)
  
        valid_indices = np.flatnonzero(valid_mask)

        if valid_indices.size > 0:
            random_idx = np.random.choice(valid_indices)
            
            row, col = np.unravel_index(random_idx, self.biomes.shape)
            return (int(row), int(col))
        else:
            return None

    def place_entity(self, entity_type : ontology.Location, location : tuple):
        if location is None:
            print("Warning: No valid location found for this entity!")
            return
            
        row, col = location
        
        current_biome = self.biomes[row, col]
        print(f"Placing {entity_type.name} at row={row}, col={col}, Biome = {current_biome}")
        
        self.entities[row, col] = entity_type.value
    