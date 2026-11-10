from pcg import World
import dearpygui.dearpygui as dpg
import numpy as np

class WorldRenderer:
    BIOME_COLORS = {
        1: "#2180c0",  # OCEAN
        2: "#e2ca9c",  # BEACH
        3: "#d1a95f",  # DESERT
        4: "#759e16",  # GRASSLAND
        5: "#177a17",  # FOREST
        6: "#255803",  # SWAMP
        7: "#915D1B",  # ROCKY_MOUNTAIN
        8: "#A3BAC9",  # TUNDRA
        9: "#FFFFFF",  # SNOWY_MOUNTAIN
    }

    def __init__(self, world: World):
        self.world = world
        self.biomes_texture_tag = "biomes_texture"

    def _hex_to_rgb(self, hex_color: str)->tuple:
        hex_color = hex_color.lstrip("#")

        return tuple(
            int(hex_color[i:i+2], 16) / 255.0
            for i in (0, 2, 4)
        )
            
    def render_biomes(self):
        biomes = self.world.biomes
        height, width = biomes.shape

        image = np.zeros((height, width, 4), dtype=np.float32)

        # Default colour for unclassified cells
        image[:, :] = (0.15, 0.15, 0.15, 1.0)

        for biome_id, hex_color in self.BIOME_COLORS.items():
            rgb = self._hex_to_rgb(hex_color)
            mask = biomes == biome_id
            image[mask] = (*rgb, 1.0)

        return image.flatten().tolist()

    def create_biomes_texture(self):
        height, width = self.world.biomes.shape

        pixel_data = self.render_biomes()

        with dpg.texture_registry():
            dpg.add_dynamic_texture(
                width=width,
                height=height,
                default_value=pixel_data,
                tag=self.biomes_texture_tag
            )

    def update_biomes_texture(self):
        pixel_data = self.render_biomes()
        dpg.set_value(self.biomes_texture_tag, pixel_data)

    def recreate_biomes_texture(self):
        # Delete the previous texture
        if dpg.does_item_exist(self.biomes_texture_tag):
            dpg.delete_item(self.biomes_texture_tag)

        # Check and remove lingering alias if it exists
        if dpg.does_alias_exist(self.biomes_texture_tag):
            dpg.remove_alias(self.biomes_texture_tag)

        # Create a new texture with the new dimensions
        self.create_biomes_texture()

        # Reassign the image widget to the new texture
        dpg.configure_item(
            "biomes_image_widget",
            texture_tag=self.biomes_texture_tag
        )
