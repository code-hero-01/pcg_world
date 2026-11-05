import pcg
import knowledge
from translator import Translator
from planner import Planner
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import primitives
import sys
from primitives import TaskType, GenerationTask

class Controller:
    def __init__(self, world : pcg.World, kg : knowledge.WorldKG):
        self.world = world
        self.kg = kg
        self.translator = Translator(self.kg)

    def execute_plan(self):
        planner = Planner(self.translator)  
        planner.generate_plan()
        
        for task in planner.plan:
            print(f"Executing: {task.task_id}")
            
            if task.task_type == TaskType.GENERATE_TERRAIN:
                self.world.generate_terrain()
            elif task.task_id == "task:biomes":
                self.world.create_biomes()
            elif task.task_id == "task:rivers":
                self.world.generate_rivers()
            elif task.task_type == TaskType.GENERATE_ENTITY:
                self.world.spawn_entity(task.entity, task.constraints)
            elif task.task_type == TaskType.GENERATE_CONNECTION:
                self.world.generate_connection(task.constraints[0])


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

