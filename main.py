import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import random
import pcg
import ontology
import translator
import kg
  
def main():
    seed = random.randint(0, 1000)
    # seed = 0
    config = pcg.WorldConfig(length = 1000, width = 1000)

    world = pcg.World(config, seed)
    world.generate_terrain()
    world.generate_biomes()

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

    plt.imshow(world.biomes, cmap=cmap)

    world.generate_rivers(20)

    for river in world.rivers:
        x = [point[0] for point in river]
        y = [point[1] for point in river]

        plt.plot(x, y, color="steelblue", linewidth=2)

    world_kg = kg.WorldKG()
    world_translator = translator.Translator(world_kg, world)

    world_translator.place_points()

    # village_count = 10
    # for _ in range(village_count):
    #     location = world.choose_location(located_in= ontology.Biome.GRASSLAND, located_near= [(ontology.NaturalFeature.RIVER, 5, 30)])
    #     world.place_entity(ontology.Location.VILLAGE, location)
    
    markers = ['o', 's', '^', 'D', 'v', '*']
    i = 0
    for location in ontology.Location:
        coords = np.argwhere(world.entities == location.value)
        y_indices = coords[:, 0]
        x_indices = coords[:, 1]
        
        plt.scatter(
            x_indices, 
            y_indices, 
            marker= markers[i % len(markers)], 
            color= "gold", 
            edgecolors= "black", 
            label= location.name
        )

        i += 1

    plt.legend()
    plt.show()
    
if __name__ == "__main__":
    main()