import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
from renderer import WorldRenderer
from pcg import World, WorldConfig
from controller import Controller
from knowledge import WorldKG
from kg_editor import KG_Editor

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
        width=1000,
        height=800
    )

    seed = 42
    world_width = 512
    world_height = 512
    config = WorldConfig(height=world_height, width=world_width)
    world = World(config=config, seed=seed)

    kg = WorldKG()
    kg.load_graph("data/world_knowledge.json")
    
    controller = Controller(world, kg)

    renderer = WorldRenderer(world)
    renderer.render_world()

    kg_editor = KG_Editor(kg)

    def _on_generate(sender, app_data):
        nonlocal world

        seed = dpg.get_value("seed")
        width = dpg.get_value("width")
        height = dpg.get_value("height")
    
        config = WorldConfig(width=width, height=height)
        world = World(config=config, seed=seed)
        controller.world = world

        controller.execute_plan()

        renderer.world = controller.world

        # recreate the displayed image
        renderer.render_world()

    def _on_base_map_change(sender, app_data):
        if (dpg.does_item_exist("base_layer_widget")):
            dpg.configure_item("base_layer_widget", texture_tag=f"tex_{app_data}")

    def _on_overlay_layer_change(sender, app_data, user_data):
        layer = user_data
        if (dpg.does_item_exist(f"img_{layer}")):
            dpg.configure_item(f"img_{layer}", show=app_data)

    def _open_kg_editor():
        dpg.show_item("kg_editor_window")
        kg_editor.display_graph()
 
    with dpg.window(
        label="WorldGen Studio", 
        tag="primary_window",
        width=800,
        height=800
    ):
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
                    dpg.add_button(label="Knowledge Graph", callback=_open_kg_editor)

                dpg.add_separator()
                dpg.add_spacer(height=5)

                with dpg.child_window(border=False, width=-1, height=-1, label="world_viewer"):
                    with dpg.plot(width=512, height=512, tag="world_plot", equal_aspects=True):
                        dpg.add_plot_axis(dpg.mvXAxis, tag="world_x_axis")
                        dpg.add_plot_axis(dpg.mvYAxis, tag="world_y_axis", invert=True)
                
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

    
    with dpg.window(
        label="Knowledge Graph Editor",
        tag="kg_editor_window",
        width=800,
        height=700,
        show=False
    ):
        # to pbar
        with dpg.group(horizontal=True):
            dpg.add_text("Knowledge Graph")
            dpg.add_button(label="Clear", callback=kg_editor.clear_graph)
            dpg.add_button(label="Load", callback=lambda: dpg.show_item("load_dialog"))
            dpg.add_button(label="Save", callback=lambda: dpg.show_item("save_dialog"))
            dpg.add_button(label="Add Node", callback=kg_editor.add_node)
        
        # main panel - graph editor
        with dpg.node_editor(
            callback=kg_editor.link_callback, 
            delink_callback=kg_editor.delink_callback, 
            tag="kg_editor",
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight
        ):
            pass

    def on_mouse_click(sender, app_data):
        # app_data is the mouse button (0 = Left Click, 1 = Right Click)
        if app_data == dpg.mvMouseButton_Left:
            if dpg.is_item_hovered("kg_editor"):
                if len(dpg.get_selected_links('kg_editor')) > 0:
                    selected_link = dpg.get_selected_links("kg_editor")[0]
                    link_tag = dpg.get_item_alias(selected_link)
                    kg_editor.edit_link(link_tag)
                
    
    def on_mouse_double_click(sender, app_data):
        # app_data is the mouse button (0 = Left Click, 1 = Right Click)
        if app_data == dpg.mvMouseButton_Left:
            if dpg.is_item_hovered("kg_editor"):
                if len(dpg.get_selected_nodes('kg_editor')) > 0:
                    node_tag = dpg.get_selected_nodes('kg_editor')[0]
                    kg_editor.edit_node(node_tag)

    with dpg.handler_registry():
        dpg.add_mouse_click_handler(button=dpg.mvMouseButton_Left, callback=on_mouse_click)
        dpg.add_mouse_double_click_handler(button=dpg.mvMouseButton_Left, callback=on_mouse_double_click)

    with dpg.file_dialog(
        directory_selector=False, 
        show=False, 
        callback=kg_editor.load_graph, 
        id="load_dialog", 
        width=700, 
        height=400
    ):
        dpg.add_file_extension(".json")

    with dpg.file_dialog(
            directory_selector=False, 
            show=False, 
            callback=kg_editor.save_graph, 
            id="save_dialog", 
            width=700, 
            height=400
        ):
            dpg.add_file_extension(".json")


    with dpg.window(
        label="Relation Attributes",
        modal=True,
        show=False,
        tag="relation_attributes_input_dialog",
        no_resize=True,
        width=300,
        height=150,
        pos=[150, 150]
    ):
        pass

    with dpg.window(
        label="Node Attributes",
        modal=True,
        show=False,
        tag="edit_node_dialog",
        no_resize=True,
        width=300,
        height=150,
        pos=[150, 150]
    ):
        pass


    with dpg.window(
            label="Node Attributes",
            modal=True,
            show=False,
            tag="add_node_dialog",
            no_resize=True,
            width=300,
            height=150,
            pos=[150, 150]
        ):
            pass

    dpg.set_primary_window("primary_window", True)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()

    dpg.destroy_context()

if __name__ == "__main__":
    app()


