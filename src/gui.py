import dearpygui.dearpygui as dpg
import dearpygui.demo as demo

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

    with dpg.window(label="WorldGen Studio", tag="primary_window"):
        # top bar
        with dpg.group(horizontal=True, label="top_bar"):
            dpg.add_text("Procedural World Generation Studio")
        
        # main content
        with dpg.group(horizontal=True, label="main_content"):
            # large central panel - world view
            with dpg.child_window(width=-260, height=-200, label="World View"):
                with dpg.group(horizontal=True):
                    dpg.add_text("World")
                    dpg.add_button(label="Generate")

                dpg.add_separator()
                dpg.add_spacer(height=5)

                dpg.add_text("World will appear here.")

            # right panel - settings
            with dpg.child_window(width=0, height=-200, label="Settings"):
                dpg.add_text("Settings")
                dpg.add_separator()
                dpg.add_spacer(height=5)
                
                dpg.add_input_int(label="Seed", default_value=42, width=150)
                dpg.add_input_int(label="World Width", default_value=512, width=150)
                dpg.add_input_int(label="World Height", default_value=512, width=150)

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
                dpg.add_checkbox(label="Biomes", default_value=True)
                dpg.add_checkbox(label="Rivers", default_value=True)
                dpg.add_checkbox(label="Roads", default_value=True)
                dpg.add_checkbox(label="Entities", default_value=True)

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


