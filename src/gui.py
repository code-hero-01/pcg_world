import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
from renderer import WorldRenderer
from pcg import World, WorldConfig

def demo_app():
    dpg.create_context()
    dpg.create_viewport(title='My Dear PyGui', width=600, height=600)

    demo.show_demo()
    dpg.set_primary_window("__demo_id", True)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()
    dpg.destroy_context()

def app():
    dpg.create_context()

    dpg.create_viewport(
        title="WorldGen Studio",
        width=1100,
        height=750
    )

    seed = 42
    world_width = 512
    world_height = 512
    config = WorldConfig(height=world_height, width=world_width)
    world = World(config=config, seed=seed)

    renderer = WorldRenderer(world)
    renderer.render_world()

    def _on_generate(sender, app_data):
        nonlocal world

        seed = dpg.get_value("seed")
        width = dpg.get_value("width")
        height = dpg.get_value("height")
    
        config = WorldConfig(width=width, height=height)

        world = World(config=config, seed=seed)

        world.generate_terrain()
        world.create_biomes()
        world.generate_rivers(5)

        renderer.world = world

        # recreate the displayed image
        renderer.render_world()

    def _on_base_map_change(sender, app_data):
        if (dpg.does_item_exist("base_layer_widget")):
            dpg.configure_item("base_layer_widget", texture_tag=f"tex_{app_data}")

    def _on_overlay_layer_change(sender, app_data, user_data):
        layer = user_data
        if (dpg.does_item_exist(f"img_{layer}")):
            dpg.configure_item(f"img_{layer}", show=app_data)
 
    with dpg.window(label="WorldGen Studio", tag="primary_window"):
        # top bar
        with dpg.group(horizontal=True, label="top_bar"):
            dpg.add_text("Procedural World Generation Studio")
        
        # main content
        with dpg.group(horizontal=True, label="main_content"):
            with dpg.child_window(width=-260, height=-200, label="world_view"):   
                # large central panel - world view
                with dpg.group(horizontal=True):
                    dpg.add_text("World")
                    dpg.add_button(label="Generate", callback=_on_generate)

                dpg.add_separator()
                dpg.add_spacer(height=5)

                with dpg.child_window(border=False, width=-1, height=-1, label="world_viewer"):
                    with dpg.drawlist(width=512, height=512, tag="world_drawlist"):
                        pass
                
            # right panel - settings
            with dpg.child_window(width=0, height=-200, label="Settings"):
                dpg.add_text("Settings")
                dpg.add_separator()
                dpg.add_spacer(height=5)
                
                dpg.add_input_int(label="Seed", default_value=seed, width=150, tag="seed")
                dpg.add_input_int(label="World Width", default_value=world_width, width=150, tag="width")
                dpg.add_input_int(label="World Height", default_value=world_height, width=150, tag="height")

                dpg.add_separator()
                dpg.add_spacer(height=5)

                dpg.add_text("Terrain")
                dpg.add_slider_float(
                    label="Moisture",
                    min_value=0.0,
                    max_value=1.0,
                    default_value=0.5
                )

                dpg.add_separator()
                dpg.add_spacer(height=5)

                dpg.add_text("Rendering")

                dpg.add_separator()
                dpg.add_spacer(height=5)

                dpg.add_text("Base map")
                dpg.add_radio_button(
                    items=["Biomes", "Terrain", "Moisture"],
                    default_value="Biomes",
                    tag="base_layer_radio",
                    callback=_on_base_map_change
                )

                dpg.add_separator()
                dpg.add_spacer(height=5)

                dpg.add_text("Overlay layers")
                dpg.add_checkbox(label="Rivers", default_value=True, callback=_on_overlay_layer_change, user_data="Rivers", tag="check_Rivers")
                dpg.add_checkbox(label="Entities", default_value=True, callback=_on_overlay_layer_change, user_data="Entities", tag="check_Entities")
                dpg.add_checkbox(label="Roads", default_value=True, callback=_on_overlay_layer_change, user_data="Roads", tag="check_Roads")

        # bottom bar - terminal
        with dpg.child_window(width=0, height=0, label="terminal_panel"):
            dpg.add_text("Terminal")

            with dpg.tab_bar():
                with dpg.tab(label="Log"):
                    dpg.add_text("Generation output will appear here.")

                with dpg.tab(label="Results"):
                    dpg.add_text("Validation results will appear here.")
                    
    dpg.set_primary_window("primary_window", True)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()

    dpg.destroy_context()

if __name__ == "__main__":
    app()


