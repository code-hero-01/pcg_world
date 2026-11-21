import dearpygui.dearpygui as dpg
import dearpygui.demo as demo
from renderer import WorldRenderer
from pcg import World, WorldConfig
from controller import Controller
from knowledge import WorldKG
from kg_editor import KG_Editor
from validator import WorldValidator

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
        width=900,
        height=900
    )

    log_messages = []
    def _append_log(message):
        log_messages.append(message)

        if dpg.does_item_exist("generation_log"):
            dpg.set_value("generation_log", "\n".join(log_messages))

    results = []
    def _append_result(message):
        results.append(message)

        if dpg.does_item_exist("validation_results"):
            dpg.set_value("validation_results", "\n".join(results))

    seed = 42
    world_width = 512
    world_height = 512
    config = WorldConfig(height=world_height, width=world_width)
    world = World(config=config, seed=seed, log_callback=_append_log)

    kg = WorldKG()
    kg.load_graph("data/world_knowledge.json")
    
    controller = Controller(world, kg, _append_log)

    renderer = WorldRenderer(world)

    kg_editor = KG_Editor(kg)

    def _on_generate(sender, app_data):
        nonlocal world
        
        seed = dpg.get_value("seed")
        width = dpg.get_value("width")
        height = dpg.get_value("height")
    
        config = WorldConfig(width=width, height=height)
        world = World(config=config, seed=seed, log_callback=_append_log)
        controller.world = world

        controller.execute_plan()

        renderer.world = controller.world

        # recreate the displayed image
        renderer.render_world()

        validator = WorldValidator(world, kg, _append_result)
        validator.validate()
        validator.generate_report()

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
        tag="primary_window"
    ):
        # top bar
        with dpg.group(horizontal=True, label="top_bar"):
            dpg.add_text("Procedural World Generation Studio")
        
        # main content
        with dpg.group(horizontal=True, label="main_content"):
            with dpg.child_window(width=-250, height=-250, label="world_view"):   
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
            with dpg.child_window(width=0, height=-250, label="Settings"):
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
                    dpg.add_input_text(
                        tag="generation_log",
                        multiline=True,
                        readonly=True,
                        width=-1,
                        height=-1,
                        default_value=""
                    )

                with dpg.tab(label="Results"):
                    dpg.add_input_text(
                        tag="validation_results",
                        multiline=True,
                        readonly=True,
                        width=-1,
                        height=-1,
                        default_value=""
                    )

    
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
            dpg.add_button(label="Delete Selected Nodes", callback=kg_editor.delete_selected_nodes)
        
        # main panel - graph editor
        with dpg.node_editor(
            callback=kg_editor.link_callback, 
            delink_callback=kg_editor.delink_callback, 
            tag="kg_editor",
            minimap=True,
            minimap_location=dpg.mvNodeMiniMap_Location_BottomRight
        ):
            pass


    def _find_entity_at(mouse_x:int, mouse_y:int):
        selected_entity = None

        for entity_id, info in world.entities_info.items():
            y, x = info['coords']
            entity_type = info['entity_type']
            sprite = renderer.sprite_cache[entity_type]
            sprite_width, sprite_height = sprite.size
            x_bounds = (x - sprite_width/2, x + sprite_width/2)
            y_bounds = (y - sprite_height/2, y + sprite_height/2)

            if x_bounds[0] <= mouse_x <= x_bounds[1] and y_bounds[0] <= mouse_y <= y_bounds[1]:
                selected_entity = entity_id

        return selected_entity

    def _show_entity_info(entity_id : str, x : int, y : int):
        if dpg.does_item_exist("entity_inspector"):
            dpg.delete_item("entity_inspector", children_only=True)

        attributes = kg.graph.nodes[entity_id]
        attributes_count = len(attributes)

        dpg.add_input_text(
            label="id", 
            width=100, 
            default_value=entity_id, 
            parent="entity_inspector",
            tag=f"id_tag",
            enabled=False
        )

        for attribute, val in attributes.items():
            dpg.add_input_text(
                label=attribute, 
                width=100, 
                default_value=str(val), 
                parent="entity_inspector",
                tag=f"{attribute}_tag",
                enabled=False
            )

        
        relations = list(kg.graph.in_edges(entity_id, keys=True)) + list(kg.graph.out_edges(entity_id, keys=True))

        with dpg.table(
            header_row=True,
            hideable=True,
            scrollX=True, 
            scrollY=True, 
            freeze_rows=1,
            row_background=True,
            parent="entity_inspector"
        ):
            # define columns
            dpg.add_table_column(label="Source")
            dpg.add_table_column(label="Relation")
            dpg.add_table_column(label="Target")

            # populate rows
            for u, v, relation_type in relations:
                with dpg.table_row():
                    dpg.add_text(u)
                    dpg.add_text(relation_type)
                    dpg.add_text(v)
        
        dpg.configure_item("entity_inspector", show=True, height=attributes_count*30 + len(relations)*30, pos=[x+24, y])

    def on_mouse_click(sender, app_data):
        # app_data is the mouse button (0 = Left Click, 1 = Right Click)
        if app_data == dpg.mvMouseButton_Left:
            if dpg.is_item_hovered("kg_editor"):
                if len(dpg.get_selected_links('kg_editor')) > 0:
                    selected_link = dpg.get_selected_links("kg_editor")[0]
                    link_tag = dpg.get_item_alias(selected_link)
                    kg_editor.edit_link(link_tag)

            if dpg.is_item_hovered("world_plot"):
                if not dpg.get_value("check_Entities"):
                    dpg.configure_item("entity_inspector", show=False)
                    return

                mouse_x, mouse_y = dpg.get_plot_mouse_pos()

                entity_id = _find_entity_at(mouse_x, mouse_y)
                
                if entity_id is not None:
                    _show_entity_info(entity_id, mouse_x, mouse_y)
                else:
                    dpg.configure_item("entity_inspector", show=False)
                
    
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

    with dpg.window(
        label="Entity Inspector",
        tag="entity_inspector",
        width=320,
        height=400,
        pos=[150, 100],
        show=False
    ):
        pass

    dpg.set_primary_window("primary_window", True)

    dpg.setup_dearpygui()
    dpg.show_viewport()
    dpg.start_dearpygui()

    dpg.destroy_context()

if __name__ == "__main__":
    app()


