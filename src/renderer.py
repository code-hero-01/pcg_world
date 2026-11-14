from pcg import World, WorldConfig
import dearpygui.dearpygui as dpg
import numpy as np
from ontology import EntityType
from PIL import Image

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

    RIVER_COLOR = "#2180c0"
    ROAD_COLOR = "#edd4a5"

    SPRITES = {
        EntityType.CITY: "assets/city.png",
        EntityType.VILLAGE: "assets/village.png",
        EntityType.MINE: "assets/mine.png",
    }

    def __init__(self, world: World):
        self.world = world
        self.texture_tag = "texture_tag"

        self.base_layers = ["Biomes", "Terrain", "Moisture"]
        self.overlay_layers = ["Rivers", "Roads", "Entities"]

        self.biomes_tex_tag = "tex_Biomes"
        self.terrain_tex_tag = "tex_Terrain"
        self.moisture_tex_tag = "tex_Moisture"
        self.rivers_tex_tag = "tex_Rivers"
        self.entities_tex_tag = "tex_Entities"
        self.roads_tex_tag = "tex_Roads"


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

        rgba[~mask, :3] = rgb

        return rgba.ravel().tolist()

    def _get_entities_texture(self) -> list:
        width = self.world.config.width
        height = self.world.config.height
        

        sprite_cache = {}
        # transparent canvass
        canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

        for entity_id, info in self.world.entities_info.items():
            y, x = info['coords']
            entity_type = info['entity_type']

            if entity_type not in sprite_cache:
                sprite_path = self.SPRITES.get(entity_type)
                if sprite_path is None:
                    continue
                img = Image.open(sprite_path).convert("RGBA")
                # img = img.resize((sprite_width, sprite_height), Image.Resampling.LANCZOS)
                
                # Flip vertically 
                img = img.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                
                sprite_cache[entity_type] = img

            sprite = sprite_cache[entity_type]

            sprite_width, sprite_height = sprite.size

            # Centre sprite on its world coordinate.
            left = int(x - sprite_width / 2)
            top = int(y - sprite_height / 2)

            # Clip sprites that extend beyond world boundaries.
            x1 = max(0, left)
            y1 = max(0, top)
            x2 = min(width, left + sprite_width)
            y2 = min(height, top + sprite_height)

            if x1 >= x2 or y1 >= y2:
                continue

            cropped = sprite.crop((
                x1 - left,
                y1 - top,
                x2 - left,
                y2 - top
            ))

            canvas.alpha_composite(cropped, (x1, y1))

        rgba = np.asarray(canvas, dtype=np.float32) / 255.0
        return rgba.ravel().tolist()     

    def _get_roads_texture(self) -> list:
        rgba = np.zeros((self.world.config.height, self.world.config.width, 4), dtype=np.float32)
        
        rgb = self._hex_to_rgb(self.ROAD_COLOR)
        mask = self.world.roads != -1
        rgba[mask] = (*rgb, 1.0)

        rgba[~mask, :3] = rgb

        return rgba.ravel().tolist()

    def render_world(self):
        if (dpg.does_item_exist("world_y_axis")):
            dpg.delete_item("world_y_axis", children_only=True)

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
        textures[self.entities_tex_tag] = self._get_entities_texture()
        textures[self.roads_tex_tag] = self._get_roads_texture()

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

        if dpg.does_item_exist("world_plot"):
            dpg.configure_item(
                "world_plot",
                width=self.world.config.width, 
                height=self.world.config.height
            )
                    
            active_base = dpg.get_value("base_layer_radio")
            if not dpg.does_item_exist("base_layer_widget"):
                dpg.add_image_series(
                    tag="base_layer_widget",
                    texture_tag=f"tex_{active_base}",
                    bounds_min=(0, 0),
                    bounds_max=(width, height),
                    parent="world_y_axis"
                )

                for name in self.overlay_layers:
                    dpg.add_image_series(
                        f"tex_{name}",
                        bounds_min=(0, 0),
                        bounds_max=(width, height),
                        tag=f"img_{name}",
                        show=dpg.get_value(f"check_{name}"),
                        parent="world_y_axis"
                    )

                dpg.set_axis_limits("world_x_axis", 0, width)
                dpg.set_axis_limits("world_y_axis", 0, height)

                # Release the lock on the NEXT frame so zoom and pan work immediately
                def _unlock_axes():
                    dpg.set_axis_limits_auto("world_x_axis")
                    dpg.set_axis_limits_auto("world_y_axis")

                dpg.set_frame_callback(dpg.get_frame_count() + 1, callback=_unlock_axes)

