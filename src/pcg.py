import numpy as np
import noise
from dataclasses import dataclass
from collections import deque
import heapq
import ontology as ontology
import primitives as primitives
import scipy.ndimage

@dataclass
class WorldConfig:
    width: int
    height: int

    continent_scale: float = 300
    continent_octaves: int = 2
    continent_persistance: float = 0.5
    continent_lacunarity: float = 2.0

    detail_scale: float = 80
    detail_octaves: int = 6
    detail_persistance: float = 0.5
    detail_lacunarity: float = 2.0

    moisture_scale: float = 150
    moisture_octaves: int = 6
    moisture_persistance: float = 0.5
    moisture_lacunarity: float = 2.0

    river_threshold: int = 100

def chebyshev_distance(loc1 : tuple, loc2 : tuple) -> int:
        return max(abs(p - q) for p, q in zip(loc1, loc2))

class World:
    def __init__(self, config : WorldConfig, seed: int):
        self.rng = np.random.default_rng(seed)

        self.config = config
        self.continent_offset = (self.rng.uniform(0, 1000), self.rng.uniform(0,1000))
        self.detail_offset = (self.rng.uniform(0, 1000), self.rng.uniform(0,1000))
        self.moisture_offset = (self.rng.uniform(0, 1000), self.rng.uniform(0,1000))

        self.ROWS = self.config.height
        self.COLS = self.config.width

        self.continent = np.zeros((self.ROWS, self.COLS), dtype=np.float32)
        self.detail = np.zeros((self.ROWS, self.COLS), dtype=np.float32)
        self.elevation = np.zeros((self.ROWS, self.COLS), dtype=np.float32)
        self.moisture = np.zeros((self.ROWS, self.COLS), dtype=np.float32)

        self.ridged_noise = np.zeros((self.ROWS, self.COLS), dtype=np.float32)
        # self.flow_accumulation = np.ones((self.ROWS, self.COLS))
        self.biomes = np.full((self.ROWS, self.COLS), -1, dtype=int)
        self.distance_to = {}
        self.rivers = np.full((self.ROWS, self.COLS), -1, dtype=int)
        self.roads = np.full((self.ROWS, self.COLS), -1, dtype=int) 
        self.entities = np.full((self.ROWS, self.COLS), "", dtype=object)

        self.entities_info = {}
        self.rivers_paths = []
        self.road_coords = {}

    def generate_terrain(self):
        config = self.config
       
        # generate noise fields
        for y in range(self.ROWS):
            for x in range(self.COLS):
                # continent (Large base shapes)
                cx = x / config.continent_scale + self.continent_offset[0]
                cy = y / config.continent_scale + self.continent_offset[1]
                self.continent[y][x] = noise.pnoise2(
                    cx, 
                    cy, 
                    octaves=config.continent_octaves, 
                    persistence=config.continent_persistance, 
                    lacunarity=config.continent_lacunarity)

                # detail (Local mountains and roughness)
                dx = x / config.detail_scale + self.detail_offset[0]
                dy = y / config.detail_scale + self.detail_offset[1]
                self.detail[y][x] = noise.pnoise2(
                    dx, 
                    dy, 
                    octaves=config.detail_octaves, 
                    persistence=config.detail_persistance, 
                    lacunarity=config.detail_lacunarity
                )

                # moisture
                mx = x / config.moisture_scale + self.moisture_offset[0]
                my = y / config.moisture_scale + self.moisture_offset[1]
                self.moisture[y][x] = noise.pnoise2(
                    mx, 
                    my, 
                    octaves=self.config.moisture_octaves, 
                    persistence=self.config.moisture_persistance, 
                    lacunarity=config.moisture_lacunarity
                )

                # roughness
                self.ridged_noise[y][x] = abs(
                    noise.pnoise2(
                        x/80.0 + self.detail_offset[0], 
                        y/80.0 + self.detail_offset[1], 
                        octaves=2, 
                        persistence=0.5
                    )
                )

        # normalize map to [0, 1]
        def normalize(arr):
            return (arr - arr.min()) / (arr.max() - arr.min())

        self.continent = normalize(self.continent)
        self.detail = normalize(self.detail)
        self.moisture = normalize(self.moisture)
        self.ridged_noise = normalize(self.ridged_noise)

        self.elevation = self.continent *  0.6 + self.detail * 0.4

        # apply Island Radial Mask (lowers edges to force large ocean bodies)
        center_x, center_y = self.COLS / 2.0, self.ROWS / 2.0
        max_radius = np.sqrt(center_x**2 + center_y**2) - 5
        
        y_indices, x_indices = np.indices((self.ROWS, self.COLS))
        dist_from_center = np.sqrt((x_indices - center_x)**2 + (y_indices - center_y)**2) / max_radius
        
        # Pull edges down into ocean
        self.elevation = self.elevation * np.clip((1.0 - (dist_from_center ** 2)), 0.0, 1.0)
        self.elevation = normalize(self.elevation)
        
        print("Generated terrain...")
        
    def create_biomes(self):
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
            ontology.EntityType.OCEAN.value,
            ontology.EntityType.BEACH.value,
            ontology.EntityType.DESERT.value,
            ontology.EntityType.GRASSLAND.value,
            ontology.EntityType.FOREST.value,
            ontology.EntityType.SWAMP.value,
            ontology.EntityType.ROCKY_MOUNTAIN.value,
            ontology.EntityType.TUNDRA.value,
            ontology.EntityType.SNOWY_MOUNTAIN.value,
        ]

        self.biomes = np.select(conditions, choices)

        print("Created biomes...")

    def calculate_distance_map(self, target: primitives.Entity):
        if target.instance == "Unique":
            non_target_mask = (self.entities != target.entity_id)
        elif ontology.SPATIAL_TYPE_MAP.get(target.entity_type) == ontology.SpatialType.BIOME:
            non_target_mask = (self.biomes != target.entity_type.value)
        elif ontology.SPATIAL_TYPE_MAP.get(target.entity_type) == ontology.SpatialType.FEATURE:
            if target.entity_type == ontology.EntityType.RIVER:
                non_target_mask = (self.rivers != target.entity_type.value)
            elif target.entity_type == ontology.EntityType.ROAD:
                non_target_mask = (self.roads != target.entity_type.value)
            else:
                non_target_mask = np.ones((self.ROWS, self.COLS), dtype=bool)
        elif ontology.SPATIAL_TYPE_MAP.get(target.entity_type) == ontology.SpatialType.POINT:
            non_target_mask = (self.entities == "")
        else:
            non_target_mask = np.ones((self.ROWS, self.COLS), dtype=bool)

        # handle the edge case where NO target exists on the map
        if np.all(non_target_mask):
            return np.full((self.ROWS, self.COLS), -1.0, dtype=np.float32)

        # compute exact Euclidean distance (returns float64, cast to float32 to save memory)
        distance_to_target = scipy.ndimage.distance_transform_edt(non_target_mask).astype(np.float32)

        return distance_to_target

    # def multisource_bfs(self, target: primitives.Entity):
    #     if target.instance == "Unique":
    #         y_indices, x_indices = np.where(self.entities == target.entity_id)
    #     elif ontology.SPATIAL_TYPE_MAP.get(target.entity_type) == ontology.SpatialType.BIOME:
    #         y_indices, x_indices = np.where(self.biomes == target.entity_type.value)
    #     elif ontology.SPATIAL_TYPE_MAP.get(target.entity_type) == ontology.SpatialType.FEATURE:
    #         if target.entity_type == ontology.EntityType.RIVER:
    #             y_indices, x_indices = np.where(self.rivers == target.entity_type.value)
    #         elif target.entity_type == ontology.EntityType.ROAD:
    #             y_indices, x_indices = np.where(self.roads == target.entity_type.value)
    #     elif ontology.SPATIAL_TYPE_MAP.get(target.entity_type) == ontology.SpatialType.POINT:
    #         y_indices, x_indices = np.where(self.entities != "")
    #     else:
    #         # Fallback catch-all to prevent UnboundLocalError
    #         y_indices, x_indices = np.array([]), np.array([])


    #     # multisource bfs
    #     distance_to_target = np.full((self.ROWS, self.COLS), -1, dtype=np.int32)
    #     queue = deque()
        
    #     for y, x in zip(y_indices, x_indices):
    #         queue.append((x, y))
    #         distance_to_target[y, x] = 0

    #     directions = [
    #         (-1, -1), (-1, 0), (-1, 1),
    #         (0, -1),           (0, 1),
    #         (1, -1),  (1, 0),  (1, 1)
    #     ]
        
    #     while queue:
    #         x, y = queue.popleft()

    #         for dx, dy in directions:
    #             nx = x + dx
    #             ny = y + dy
    #             if nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS:
    #                 continue
    #             if distance_to_target[ny, nx] != -1:
    #                 continue
                
    #             step = 1
    #             # if abs(dx) == 1 and abs(dy) == 1: # add square root of 2 for diagonal movement
    #                 # step = 1.414
                
    #             distance_to_target[ny, nx] = step + distance_to_target[y, x]
                                        
    #             queue.append((nx, ny))

    #     return distance_to_target

    def find_distance(self, source_loc: tuple[int, int], target: primitives.Entity):
        if target.instance == "Unique" and ontology.SPATIAL_TYPE_MAP.get(target.entity_type) == ontology.SpatialType.POINT:
            target_loc = self.entities_info.get(target.entity_id)
            return chebyshev_distance(source_loc, target_loc)
        
        if target.entity_id not in self.distance_to:
            self.distance_to[target.entity_id] = self.calculate_distance_map(target)

        row, col = source_loc
        return self.distance_to[target.entity_id][row, col]
    
    def _astar_river(self, start: tuple):
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

            if self.biomes[y, x] == ontology.EntityType.OCEAN.value:
                path = []
                while current in came_from:
                    x, y = current
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

                dist = 1.414 if (dx != 0 and dy != 0) else 1.0

                base_cost = 1.0 * dist

                elevation_diff = self.elevation[ny, nx] - self.elevation[y, x]
                if elevation_diff > 0:
                    # Going uphill is heavily penalized, while still allowing climbing out of local minima basins
                    elevation_cost = (elevation_diff ** 2) * 50000.0 
                else:
                    # Downhill movement is encouraged
                    elevation_cost = 5.0 / (1.0 + abs(elevation_diff) * 1.0)

                # ridged noise: valleys for the river to flow through
                # Higher multiplier = more meandering and oxbow-like curves
                meander_cost = (self.ridged_noise[ny, nx] ** 1.5) * 60.0

                flow_cost = base_cost + elevation_cost + meander_cost
                tentative_g = g_cost[current] + flow_cost
                
 
                if tentative_g < g_cost.get(neighbour, float('inf')):
                    g_cost[neighbour] = tentative_g
                    f_score = g_cost[neighbour] + 0.2 * self.distance_to[ontology.EntityType.OCEAN][ny, nx]   
                    came_from[neighbour] = current
                    heapq.heappush(open_set, (f_score, neighbour))     

        return None # no path to ocean found 

    def _find_river_starts(self) -> list:
        # peaks = []
        
        # # Avoid the absolute outer edge of the map to prevent index errors
        # for y in range(1, self.ROWS - 1):
        #     for x in range(1, self.COLS - 1):
        #         # Apply your core biome conditions first
        #         if self.elevation[y, x] > 0.7 and self.moisture[y, x] > 0.5:
        #             # Check if this cell is strictly higher than its 3x3 neighborhood
        #             neighborhood = self.elevation[y-1:y+2, x-1:x+2]
                    
        #             if self.elevation[y, x] == np.max(neighborhood):
        #                 peaks.append((x, y))

        # Smooth the terrain to remove tiny jagged noise

        smoothed = scipy.ndimage.gaussian_filter(self.elevation, sigma=1.5)
    
        neighborhood_size = 5   # Minimum grid spacing between peaks (5x5 window)
        min_height = 0.7        
        min_moisture = 0.5       

        # find local maxima
        local_max = (smoothed == scipy.ndimage.maximum_filter(smoothed, size=neighborhood_size))
        peaks_mask = local_max & (smoothed >= min_height) & (self.moisture >= min_moisture)

        # fandle flat plateaus (reduces multi-pixel plateaus to single center points)
        labeled, num_features = scipy.ndimage.label(peaks_mask)
        if num_features == 0:
            return []
        
        peak_coords = np.array(scipy.ndimage.center_of_mass(peaks_mask, labeled, range(1, num_features + 1)))

        # Round to integer grid indices (row, col)
        peak_indices = np.round(peak_coords).astype(int)
                
        return [(int(col), int(row)) for row, col in peak_indices]               

    def generate_rivers(self, num_rivers : int = 15) -> list:
        river_starts = self._find_river_starts()
        if len(river_starts) > num_rivers:
            river_starts = list(self.rng.choice(river_starts, num_rivers))

        if ontology.EntityType.OCEAN not in self.distance_to:
            self.distance_to[ontology.EntityType.OCEAN] = self.calculate_distance_map(
                                                                    primitives.Entity(
                                                                        entity_id="Ocean",
                                                                        entity_type=ontology.EntityType.OCEAN,
                                                                        instance="Class"
                                                                    )
                                                                )
        for start in river_starts:
            path = self._astar_river(tuple(start))
            if path is not None:
                self.rivers_paths.append(path)

        for river_path in self.rivers_paths:
            self._rasterize_river(river_path, min_radius=1, max_radius=2)

        # carve river beds into elevation
        self.elevation[self.rivers != -1] -= 0.02

        print(f"Generated {len(self.rivers_paths)} rivers...")

    def _rasterize_river(self, path:list[tuple[int, int]], min_radius:int, max_radius:int):
        random_widths = self.rng.random(len(path))

        smooth_widths = scipy.ndimage.gaussian_filter1d(random_widths, sigma=5)

        # Normalize the variation.
        low = smooth_widths.min()
        high = smooth_widths.max()

        if high > low:
            smooth_widths = (smooth_widths - low) / (high - low)
        else: # prevent devision by zero
            smooth_widths[:] = 0.5

        downstream = np.linspace(0.0, 1.0, len(path))

        width_values = (
            min_radius
            + smooth_widths * 0.5 * (max_radius - min_radius)
            + downstream * (max_radius - min_radius) * 0.5
        )

        radii = np.clip(
            np.round(width_values),
            min_radius,
            max_radius
        ).astype(int)
        
        for (x, y), radius in zip(path, radii):
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy > radius * radius:
                        continue
                    
                    nx = x + dx
                    ny = y + dy

                    if not (0 <= nx < self.COLS and 0 <= ny < self.ROWS): # out of bounds
                        continue

                    self.rivers[ny, nx] = ontology.EntityType.RIVER.value
                    

    def get_region_mask(self, constraint : primitives.RegionConstraint):
        region_mask = (self.entities == "") & (self.rivers == -1) & (self.roads == -1)

        if constraint.region is not None:
            region_mask &= (self.biomes == constraint.region.entity_type.value)

        return region_mask
    
    def get_proximity_mask(self, constraint : primitives.ProximityConstraint):
        proximity_mask = (self.entities == "") & (self.rivers == -1) & (self.roads == -1)

        if constraint.target.entity_id not in self.distance_to:
            self.distance_to[constraint.target.entity_id] = self.calculate_distance_map(constraint.target)
        
        proximity_mask &= (self.distance_to[constraint.target.entity_id] <= constraint.max_distance) & (self.distance_to[constraint.target.entity_id] >= constraint.min_distance)
        return proximity_mask


    def spawn_entity(self, entity: primitives.Entity, constraints: list):
        valid_mask = (self.entities == "") & (self.rivers == -1) & (self.roads == -1)
        
        for constraint in constraints:
            if isinstance(constraint, primitives.RegionConstraint):
                valid_mask &= self.get_region_mask(constraint)
            
            elif isinstance(constraint, primitives.ProximityConstraint):
                valid_mask &= self.get_proximity_mask(constraint)

        valid_indices = np.flatnonzero(valid_mask)

        if valid_indices.size > 0:
            random_idx = self.random_choose(valid_indices)
            
            row, col = np.unravel_index(random_idx, self.biomes.shape)
            self.place_entity(entity= entity, location= (row, col))
        else:
            print(f"Warning: No valid location found for the entity {entity}!")
        

    def place_entity(self, entity: primitives.Entity, location : tuple):
        row, col = location
        
        current_biome = ontology.EntityType(self.biomes[row, col])
        print(f"Spawned {entity.entity_id} of type {entity.entity_type.name} at row={row}, col={col}, Biome = {current_biome}")
        
        self.entities[row, col] = entity.entity_id

        self.entities_info[entity.entity_id] = {}
        self.entities_info[entity.entity_id]['coords'] = (row, col)
        self.entities_info[entity.entity_id]['entity_type'] = entity.entity_type


    def random_choose(self, arr):
        return self.rng.choice(arr)

    def is_water(self, x:int, y:int) -> bool:
        if self.biomes[y, x] == ontology.EntityType.OCEAN.value or self.rivers[y, x] != -1:
            return True
        return False

    def generate_connection(self, connection_constraint):  # a_star road
        start = connection_constraint.source.entity_id
        goal = connection_constraint.target.entity_id

        start_indices = np.where(self.entities == start)
        if len(start_indices[0]) == 0:
            print(f"Source entity {start} not found in entity_id_map")
            return
        
        goal_indices = np.where(self.entities == goal)
        if len(goal_indices[0]) == 0:
            print(f"Goal entity {goal} not found in entity_id_map")
            return

        
        start_cell = int(start_indices[1][0]), int(start_indices[0][0])

        open_set = []
        closed_set = set()
        heapq.heappush(open_set, (0, start_cell))

        directions = [
                    (-1, -1), (-1, 0), (-1, 1),
                    (0, -1),           (0, 1),
                    (1, -1),  (1, 0),  (1, 1)
                ]

        g_cost = {start_cell: 0}
        came_from = {}

        while open_set:
            # get node with lowest f_cost
            current_f, current = heapq.heappop(open_set)
            x, y = current

            if current in closed_set:
                continue

            closed_set.add(current)

            if self.entities[y, x] == goal:
                path = []
                while current in came_from:
                    path.append(current)
                    current = came_from[current]
                path.append(start_cell)
                path.reverse()

                if path is None:
                    return

                self.road_coords[(start, goal)] = path
                self._rasterize_road(path, radius=1)

                return

            # explore neighbours
            for dx, dy in directions:
                nx = x + dx
                ny = y + dy
                neighbour = (nx, ny)
                if nx < 0 or nx >= self.COLS or ny < 0 or ny >= self.ROWS:
                    continue
                if neighbour in closed_set:
                    continue
                if self.biomes[ny, nx] == ontology.EntityType.OCEAN.value:
                    continue

                dist = 1.414 if (dx != 0 and dy != 0) else 1.0
                base_cost = 1.0 * dist

                slope = abs(self.elevation[ny, nx] - self.elevation[y, x]) / dist
                slope_cost = (slope ** 2) * 20000.0

                # High penalty for river encourages going around, while still allowing bridges if necessary
                bridge_cost = 100.0 if self.rivers[ny, nx] != -1 else 0.0

                terrain_cost = 0
                if self.biomes[ny, nx] in [ontology.EntityType.SNOWY_MOUNTAIN.value, ontology.EntityType.SWAMP.value, ontology.EntityType.TUNDRA.value]:
                    terrain_cost = 300.0

                # Combine costs
                step_cost = base_cost + slope_cost + bridge_cost + terrain_cost

                # Heavily discount movement along already-generated roads
                step_cost = 0.2 * dist if self.roads[ny, nx] != -1 else step_cost

                tentative_g = g_cost[current] + step_cost
    
                if tentative_g < g_cost.get(neighbour, float('inf')):
                    g_cost[neighbour] = tentative_g

                    if goal not in self.distance_to:
                        self.distance_to[goal] = self.calculate_distance_map(connection_constraint.target)

                    f_score = g_cost[neighbour] + 0.25 * self.distance_to[goal][ny, nx]   
                    came_from[neighbour] = current
                    heapq.heappush(open_set, (f_score, neighbour))

    def _rasterize_road(self, path, radius=1):
        centerline = np.zeros((self.ROWS, self.COLS), dtype=bool)
        for x, y in path:
            centerline[y, x] = True

        # compute exact distance from every cell to the nearest centerline pixel
        distances = scipy.ndimage.distance_transform_edt(~centerline)
        
        # fill everything within the desired radius
        self.roads[distances <= radius] = ontology.EntityType.ROAD.value


    def locate(self, entity_id: str) -> tuple[int, int]:
        coords = np.argwhere(self.entities == entity_id)

        if coords.size == 0:
            return None
        
        row, col = coords[0]
        return row, col
