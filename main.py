import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import random
import pcg
  
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

    world.calculate_distance_from_ocean()
    world.generate_rivers(20)

    for river in world.rivers:
        x = [point[0] for point in river]
        y = [point[1] for point in river]

        plt.plot(x, y, color="steelblue", linewidth=2)

    plt.show()
    
if __name__ == "__main__":
    main()