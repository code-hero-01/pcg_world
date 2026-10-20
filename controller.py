import pcg
import knowledge
from translator import Translator, RegionConstraint, ProximityConstraint, ConnectionConstraint
from planner import Planner
import ontology
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

class Controller:
    def __init__(self, world : pcg.World, kg : knowledge.WorldKG):
        self.world = world
        self.kg = kg
        self.translator = Translator(self.kg)

    def generate_terrain(self):
        self.world.generate_terrain()

    def create_biomes(self):
        self.world.create_biomes()

    def generate_rivers(self, count : int):
        self.world.generate_rivers(count)

    def spawn_entities(self):
        dependencies = self.translator.get_dependencies()
        spawnable_entities = self.translator.spawnable_entities
        
        planner = Planner()  
        planner.generate_plan(dependencies, spawnable_entities)

        entity_constraint_map = self.translator.translate()

        for entity in planner.plan:
            constraints = entity_constraint_map[entity]

            valid_mask = self.world.get_free_mask()
            for constraint in constraints:
                if isinstance(constraint, RegionConstraint):
                    valid_mask &= self.world.get_region_mask(constraint)
                elif isinstance(constraint, ProximityConstraint):
                    valid_mask &= self.world.get_proximity_mask(constraint)

            valid_indices = np.flatnonzero(valid_mask)

            if valid_indices.size > 0:
                random_idx = self.world.random_choose(valid_indices)
                
                row, col = np.unravel_index(random_idx, self.world.biomes.shape)
                self.world.place_entity(entity_id= entity, entity_type= self.kg.get_entity_type(entity), location= (row, col))
            else:
                print(f"Warning: No valid location found for the entity {entity}!")

    def create_connections(self):
        for constraint in self.translator.connections:
            print(f"Connecting {constraint.source} to {constraint.target}")
            self.world.generate_connection(constraint)

    def display(self):
        cmap = ListedColormap([
                "#2180c0",
                "#e2ca9c",
                "#d1a95f",
                "#759e16",
                "#177a17",
                "#255803",
                "#915D1B",
                "#A3BAC9",
                "white"
            ])
    
        plt.imshow(self.world.biomes, cmap=cmap)
    
        for river in self.world.rivers:
            x = [point[0] for point in river]
            y = [point[1] for point in river]
    
            plt.plot(x, y, color="steelblue", linewidth=2, zorder= 2)

        for road in self.world.roads:
            x = [point[0] for point in road]
            y = [point[1] for point in road]
            
            plt.plot(x, y, color="#edd4a5", linewidth=2, zorder= 3)
    
    
        # village_count = 10
        # for _ in range(village_count):
        #     location = world.choose_location(located_in= ontology.Biome.GRASSLAND, located_near= [(ontology.NaturalFeature.RIVER, 5, 30)])
        #     world.place_entity(ontology.Location.VILLAGE, location)
        
        markers = ['o', 's', '^', 'D', 'v', '*']
        i = 0
        for entity in self.translator.spawnable_entities:
            coords = np.argwhere(self.world.entity_id_map == entity)
            y_indices = coords[:, 0]
            x_indices = coords[:, 1]

          
            plt.scatter(
                x_indices, 
                y_indices, 
                marker= markers[i % len(markers)], 
                color= "gold", 
                edgecolors= "black", 
                s= 25,
                label= entity,
                zorder= 4
            )
    
            i += 1
    
        plt.legend(
            bbox_to_anchor=(1.02, 1),
            loc="upper left",
            fontsize=8
        )
        
        plt.show()
            

if __name__ == "__main__":
    seed = 42
    config = pcg.WorldConfig(length = 1000, width = 1000)    
    world = pcg.World(config, seed)

    kg = knowledge.WorldKG()
    kg.load_graph("world_knowledge.json")

    controller = Controller(world, kg)
    controller.spawn_entities()

