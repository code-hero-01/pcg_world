import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import random
from enum import Enum
import noise
from dataclasses import dataclass
from collections import deque
import heapq

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

    class Biome(Enum):
        OCEAN = 0
        BEACH = 1
        DESERT = 2
        GRASSLAND = 3
        FOREST = 4
        SWAMP = 5
        BARE = 6
        TUNDRA = 7
        SNOW = 8

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
        self.distance_from_ocean = np.full((self.ROWS, self.COLS), -1, dtype=np.int32)
        self.river_map = np.zeros((self.ROWS, self.COLS), dtype=bool)

        self.rivers = []

    def generate_world(self):
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
            config.Biome.OCEAN.value,
            config.Biome.BEACH.value,
            config.Biome.DESERT.value,
            config.Biome.GRASSLAND.value,
            config.Biome.FOREST.value,
            config.Biome.SWAMP.value,
            config.Biome.BARE.value,
            config.Biome.TUNDRA.value,
            config.Biome.SNOW.value
        ]

        self.biomes = np.select(conditions, choices)

        # self.accumulate_water()
        # self.rivers = self.flow_accumulation > config.river_threshold
        # self.biomes[self.rivers] = config.Biome.WATER.value

    def lowest_neighbour(self, x : int, y : int, elevation) -> tuple:
        curr_elevation = elevation[y][x]
        lowest_elevation = curr_elevation
        lowest_x = x
        lowest_y = y

        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                # current cell
                if dx == 0 and dy == 0:
                    continue
            
                nx = x + dx
                ny = y + dy

                # out of bounds
                if nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS:
                    continue

                neighbour_elevation = elevation[ny][nx]

                if neighbour_elevation < lowest_elevation:
                    lowest_elevation = neighbour_elevation
                    lowest_x = nx
                    lowest_y = ny

        return lowest_x, lowest_y

    def calculate_flow_direction(self):
        flow_x = np.full((self.ROWS, self.COLS), -1, dtype=np.int32)
        flow_y = np.full((self.ROWS, self.COLS), -1, dtype=np.int32)

        smoothed_elevation = self.detail.copy()
        for _ in range(5):
            for y in range(1, self.ROWS - 1):
                for x in range(1, self.COLS - 1):
                    if self.biomes[y, x] == self.config.Biome.OCEAN.value:
                        continue

                    # Check immediate 3x3 neighborhood
                    neighbors = smoothed_elevation[y-1:y+2, x-1:x+2]
                    min_neighbor = np.min(neighbors)
                    if smoothed_elevation[y, x] <= min_neighbor:
                        smoothed_elevation[y, x] = min_neighbor + 0.001
        
        for y in range(self.ROWS):
            for x in range(self.COLS):

                # Don't send ocean water anywhere
                if self.biomes[y, x] == self.config.Biome.OCEAN.value:
                    continue

                nx, ny = self.lowest_neighbour(x, y, smoothed_elevation)

                if nx != x or ny != y:
                    flow_x[y, x] = nx
                    flow_y[y, x] = ny

        return flow_x, flow_y

    def accumulate_water(self):
        flow_x, flow_y = self.calculate_flow_direction()
        flat_indices = np.argsort(self.detail.ravel())[::-1]

        for index in flat_indices:
            y, x = np.unravel_index(index, self.detail.shape)

            nx = flow_x[y, x]
            ny = flow_y[y, x]

            if nx != -1 and ny != -1:
                self.flow_accumulation[ny, nx] += self.flow_accumulation[y, x]

    def calculate_distance_from_ocean(self):
        # multisource bfs
        
        queue = deque()
        ocean_y_indices, ocean_x_indices = np.where(self.biomes == self.config.Biome.OCEAN.value)
        for y, x in zip(ocean_y_indices, ocean_x_indices):
            queue.append((x, y))
            self.distance_from_ocean[y, x] = 0

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
                if self.distance_from_ocean[ny, nx] != -1:
                    continue
                
                dist = 1
                if abs(dx) == 1 and abs(dy) == 1: # add square root of 2 for diagonal movement
                    dist = 1.414
                
                self.distance_from_ocean[ny, nx] = dist + self.distance_from_ocean[y, x]
                                        
                queue.append((nx, ny))


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

            if self.biomes[y, x] == self.config.Biome.OCEAN.value:
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
                    f_score = g_cost[neighbour] + 0.25 * self.distance_from_ocean[neighbour]   
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

        for start in river_starts:
            path = self.astar_river(start)
            self.rivers.append(path)

        for river in self.rivers:
            for x, y in river:
                self.river_map[y, x] = True

            
def main():
    # seed = random.randint(0, 1000)
    seed = 0
    config = WorldConfig(length = 1000, width = 1000)

    world = World(config, seed)
    world.generate_world()

    cmap = ListedColormap([
        "steelblue",
        "#e2ca9c",
        "#d1a95f",
        "#8ce662",
        "#177a17",
        "#589C47",
        "#915D1B",
        "#A3BAC9",
        "white"
    ])

    world.calculate_distance_from_ocean()
    world.generate_rivers(20)

    plt.imshow(world.biomes, cmap=cmap)

    for river in world.rivers:
        x = [point[0] for point in river]
        y = [point[1] for point in river]

        plt.plot(x, y, color="steelblue", linewidth=2)

    plt.show()
    
if __name__ == "__main__":
    main()