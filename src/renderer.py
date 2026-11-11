from pcg import World, WorldConfig
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

    RIVER_COLOR = "#4682B4"
    ROAD_COLOR = "#edd4a5"

    def __init__(self, world: World):
        self.world = world
        self.texture_tag = "texture_tag"

        self.base_layers = ["Biomes", "Terrain", "Moisture"]
        self.overlay_layers = ["Rivers", "Roads"]

        self.biomes_tex_tag = "tex_Biomes"
        self.terrain_tex_tag = "tex_Terrain"
        self.moisture_tex_tag = "tex_Moisture"
        self.rivers_tex_tag = "tex_Rivers"
        self.roads_tex_tag = "tex_Roads"

        height, width = self.world.config.height, self.world.config.width
        self.base_layer = np.zeros((height, width, 4), dtype=np.float32)
        self.base_layer = (0.15, 0.15, 0.15, 1.0)


    def _hex_to_rgb(self, hex_color: str)->tuple:
        hex_color = hex_color.lstrip("#")

        return tuple(
            int(hex_color[i:i+2], 16) / 255.0
            for i in (0, 2, 4)
        )

    def _get_terrain_texture(self):
        terrain = self.world.elevation

        alpha = np.ones((self.world.config.height, self.world.config.width), dtype=np.float32)
        rgba = np.dstack((terrain, terrain, terrain, alpha))

        return rgba.ravel()

    def _get_moisture_texture(self):
        blue = self.world.moisture

        red = np.zeros((self.world.config.height, self.world.config.width), dtype=np.float32)
        green = np.zeros((self.world.config.height, self.world.config.width), dtype=np.float32)
        alpha = np.ones((self.world.config.height, self.world.config.width), dtype=np.float32)

        rgba = np.dstack((red, green, blue, alpha))

        return rgba.ravel()
            
    def _get_biomes_texture(self):
        biomes = self.world.biomes

        rgba = np.zeros((self.world.config.height, self.world.config.width, 4), dtype=np.float32)

        # Default colour for unclassified cells
        rgba[:, :] = (0.15, 0.15, 0.15, 1.0)

        for biome_id, hex_color in self.BIOME_COLORS.items():
            rgb = self._hex_to_rgb(hex_color)
            mask = biomes == biome_id
            rgba[mask] = (*rgb, 1.0)

        return rgba.ravel()

    def _get_rivers_texture(self) -> list:
        rgba = np.zeros((self.world.config.height, self.world.config.width, 4), dtype=np.float32)
        rgb = self._hex_to_rgb(self.RIVER_COLOR)
        mask = self.world.rivers != -1
        rgba[mask] = (*rgb, 1.0)

        return rgba.ravel().tolist()

    def _get_roads_texture(self) -> list:
        rgba = np.zeros((self.world.config.height, self.world.config.width, 4), dtype=np.float32)
        rgb = self._hex_to_rgb(self.ROAD_COLOR)
        mask = self.world.roads != -1
        rgba[mask] = (*rgb, 1.0)

        return rgba.ravel().tolist()

    def render_world(self):
        # delete existing textures
        if (dpg.does_item_exist("world_tex_registry")):
            dpg.delete_item("world_tex_registry")

        layers = self.base_layers + self.overlay_layers
        for name in layers:
            tag = f"tex_{name}"

            if dpg.does_alias_exist(tag):
                dpg.remove_alias(tag)

        # Create a new texture
        textures = {}
        textures[self.biomes_tex_tag] = self._get_biomes_texture()
        textures[self.terrain_tex_tag] = self._get_terrain_texture()
        textures[self.moisture_tex_tag] = self._get_moisture_texture()
        textures[self.rivers_tex_tag] = self._get_rivers_texture()

        width = self.world.config.width
        height = self.world.config.height

        with dpg.texture_registry(tag="world_tex_registry"):
            for tex_tag, pixel_data in textures.items():
                dpg.add_static_texture(
                    width=width,
                    height=height,
                    default_value=pixel_data,
                    tag=tex_tag
                )

        if dpg.does_item_exist("world_drawlist"):
            dpg.configure_item(
                "world_drawlist",
                width=self.world.config.width, 
                height=self.world.config.height
            )
                    
            active_base = dpg.get_value("base_layer_radio")
            if not dpg.does_item_exist("base_layer_widget"):
                dpg.draw_image(
                    tag="base_layer_widget",
                    texture_tag=f"tex_{active_base}",
                    pmin=(0, 0),
                    pmax=(width, height),
                    parent="world_drawlist"
                )

                for name in self.overlay_layers:
                    dpg.draw_image(
                        f"tex_{name}",
                        pmin=(0, 0),
                        pmax=(width, height),
                        tag=f"img_{name}",
                        show=dpg.get_value(f"check_{name}"),
                        parent="world_drawlist"
                    )
            else:
                dpg.configure_item(
                    "base_layer_widget",
                    pmax=(self.world.config.width, self.world.config.height),
                    texture_tag=f"tex_{active_base}"
                )

                for name in self.overlay_layers:
                    print(name)
                    dpg.configure_item(f"img_{name}", texture_tag=f"tex_{name}", pmax=(width, height))
  
    # def update_overlay_layers(self):
    #     # pixel_data = self.render_base_map().ravel().tolist()
    #     # dpg.set_value(self.texture_tag, pixel_data)
