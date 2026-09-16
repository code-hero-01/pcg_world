import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from noise import pnoise2
import random
from perlin_noise import PerlinNoise
from enum import Enum

def main():
    SEED = int(random.randint(0, 100000))
    noise_generator = PerlinNoise(octaves=3, seed=SEED)

    ROWS = 500
    COLS = 500
    FREQUENCY = 1/100

    elevation = np.zeros((ROWS, COLS))

    for y in range(ROWS):
        for x in range(COLS):
            nx = x * FREQUENCY
            ny = y * FREQUENCY
            elevation[y][x] = noise_generator([nx, ny])

    # normalize elevation to [0, 1]
    elevation = (elevation - elevation.min()) / (elevation.max() - elevation.min())
    
    class Biome(Enum):
        OCEAN = 0
        BEACH = 1
        SAVANNAH = 2
        FOREST = 3
        SNOW = 4

    conditions = [
        elevation < 0.35,
        elevation < 0.4,
        elevation < 0.6,
        elevation < 0.8,
        elevation <= 1
    ]

    choices = [
        Biome.OCEAN.value,
        Biome.BEACH.value,
        Biome.SAVANNAH.value,
        Biome.FOREST.value,
        Biome.SNOW.value
    ]

    biomes = np.select(conditions, choices)

    cmap = ListedColormap([
        "steelblue",
        "#e2ca9c",
        "#3fc23f",
        "#228b22",
        "white"
    ])

    plt.imshow(biomes, cmap=cmap)
    plt.show()

    
if __name__ == "__main__":
    main()