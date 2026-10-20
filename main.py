import numpy as np
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
import pcg
import ontology
import translator
import knowledge
from matplotlib.colors import LightSource
from controller import Controller

def visualize_3d(elevation):
    # Keep good detail while maintaining rendering performance
    step = 1
    z = elevation[::step, ::step]

    # Normalize height for visualization, robust to outliers
    z_min, z_max = np.percentile(z, [2, 98])
    z_norm = np.clip((z - z_min) / (z_max - z_min), 0, 1)

    # Vertical exaggeration for visible relief
    z_plot = z_norm * 150

    rows, cols = z.shape
    X, Y = np.meshgrid(np.arange(cols), np.arange(rows))

    # Scientific color palette + directional hill shading
    light = LightSource(azdeg=315, altdeg=45)
    facecolors = light.shade(
        z_norm,
        cmap=plt.get_cmap("turbo"),
        vert_exag=2,
        blend_mode="soft"
    )

    fig = plt.figure(figsize=(14, 10), dpi=150)
    ax = fig.add_subplot(111, projection="3d")

    surface = ax.plot_surface(
        X, Y, z_plot,
        facecolors=facecolors,
        linewidth=0,
        antialiased=True,
        shade=False,
        rcount=rows,
        ccount=cols
    )

    ax.set_title("Procedurally Generated Elevation", pad=20)
    ax.set_xlabel("X coordinate", labelpad=10)
    ax.set_ylabel("Y coordinate", labelpad=10)
    ax.set_zlabel("Relative elevation", labelpad=10)

    ax.view_init(elev=35, azim=-55)
    ax.set_box_aspect((1, 1, 0.3))

    # Add a matching color bar
    mappable = plt.cm.ScalarMappable(
        norm=plt.Normalize(0, 1),
        cmap="turbo"
    )
    mappable.set_array([])
    fig.colorbar(
        mappable, ax=ax,
        shrink=0.55, pad=0.1,
        label="Normalized elevation"
    )

    plt.tight_layout()
    plt.savefig("terrain_3d.png", dpi=250, bbox_inches="tight")
    plt.show()

  
def main():
    # seed = random.randint(0, 1000)
    seed = 42
    config = pcg.WorldConfig(length = 512, width = 512)

    world = pcg.World(config, seed)

    kg = knowledge.WorldKG()
    kg.load_graph("world_knowledge.json")

    controller = Controller(world, kg)
    
    controller.generate_terrain()
    controller.create_biomes()
    controller.generate_rivers(20)
    controller.spawn_entities()
    controller.create_connections()

    # plt.imshow(world.elevation, cmap="Greys")
    # plt.show()    

    # plt.imshow(world.elevation, cmap="Blues")
    # plt.show()    

    # visualize_3d(world.elevation)

    controller.display()

    
if __name__ == "__main__":
    main()