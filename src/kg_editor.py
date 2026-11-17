from knowledge import WorldKG
import dearpygui.dearpygui as dpg
import networkx as nx
import ontology

class KG_Editor:
    def __init__(self, kg : WorldKG):
        self.kg = kg
        self.edges = {}

    # callback runs when user attempts to connect attributes
    def link_callback(self, sender, app_data):
        # app_data -> (link_id1, link_id2)
        source_attr, target_attr = app_data

        source_node = source_attr.split('-out-')[0]
        target_node = target_attr.split('-in-')[0]
        relation_name = source_attr.split('-out-')[1]
        relation_type = ontology.RelationType[relation_name]

        def on_attributes_ready(attributes):
            self.kg.graph.add_edge(
                source_node, 
                target_node, 
                key=relation_type,
                **attributes
            )

            link_tag = f"{source_node}|{relation_name}|{target_node}"
            dpg.add_node_link(source_attr, target_attr, parent=sender, tag=link_tag)

        self.attributes_input(relation_name, on_complete=on_attributes_ready)
               

    def attributes_input(self, relation_name : str, on_complete):
        if dpg.does_item_exist("attributes_input_dialog"):
            dpg.delete_item("attributes_input_dialog", children_only=True)

        relation_type = ontology.RelationType[relation_name]
        attr_items = ontology.RELATION_ATTRIBUTES.get(relation_type, {})
        attributes_count = len(attr_items)

        attributes = {}

        # If no attributes are needed, run the callback immediately with {}
        if attributes_count == 0:
            on_complete(attributes)
            return
        
        for attribute, val in attr_items.items():
            dpg.add_input_float(
                label=attribute, 
                width=100, 
                default_value=val, 
                parent="attributes_input_dialog",
                format="%.2f",
                step=1,
                tag=f"{attribute}_tag"
            )

        def _submit_dialog():
            input_tags = [
                dpg.get_item_alias(child)
                for child in dpg.get_item_children("attributes_input_dialog", slot=1)
                if "mvInput" in dpg.get_item_type(child)
            ]
            
            for tag in input_tags:
                attr_name = dpg.get_item_label(tag)
                attr_val = dpg.get_value(tag)
                attributes[attr_name] = attr_val
            
            dpg.configure_item("attributes_input_dialog", show=False)
            
            on_complete(attributes)

        dpg.add_spacer(height=5, parent="attributes_input_dialog")
        dpg.add_button(label="OK", width=50, callback=_submit_dialog, parent="attributes_input_dialog")
        dpg.configure_item("attributes_input_dialog", show=True, height=attributes_count * 30 + 80)

    # callback runs when user attempts to disconnect attributes
    def delink_callback(self, sender, app_data):
        # app_data -> link_id
        link_id = dpg.get_item_alias(app_data)
        u, relation, v = link_id.split("|")
        relation_type = ontology.RelationType[relation]
        self.kg.graph.remove_edge(u, v, key=relation_type)
        dpg.delete_item(link_id)

    def delete_selected_nodes(self):
        # Retrieve all currently highlighted nodes in the editor
        selected_nodes = dpg.get_selected_nodes("kg_editor")
        for node in selected_nodes:
            dpg.delete_item(node)

    def clear_graph(self):
        self.kg.graph.clear()
        if dpg.does_item_exist("kg_editor"):
            dpg.delete_item("kg_editor", children_only=True)
        print("Cleared current graph")
    
    def load_graph(self, sender, app_data):
        self.kg.load_graph(app_data['file_path_name'])
        self.display_graph()
        print(f"Loaded graph from {app_data['file_path_name']}")
    
    def save_graph(self, sender, app_data):
        self.kg.save_graph(app_data['file_path_name'])
        print(f"Saved graph to {app_data['file_path_name']}")

    def rename_node(sender, app_data, user_data):
        dpg.configure_item(user_data, label=app_data)

    def display_graph(self):
        graph = self.kg.graph
        if dpg.does_item_exist("kg_editor"):
            dpg.delete_item("kg_editor", children_only=True)
        
        positions = nx.spring_layout(graph, k=1, iterations=100, scale=500, seed=42)

        # create and place nodes
        for node_name, (x, y) in positions.items():
            # Shift coordinates by +500 so they don't spawn off-screen in negative space
            screen_pos = [x, y]

            with dpg.node(label=str(node_name), parent="kg_editor", pos=screen_pos):
                entity_type = graph.nodes[node_name]['entity_type']

                # create unique Output attributes per relation type
                for relation_type in ontology.VALID_RELATIONS_FROM.get(entity_type, []):
                    out_tag = f"{node_name}-out-{relation_type.name}"
                    if not dpg.does_item_exist(out_tag):
                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, tag=out_tag):
                            dpg.add_text(relation_type.name)

                # create unique Input attributes per relation type
                for relation_type in ontology.VALID_RELATIONS_TO.get(entity_type, []):
                    in_tag = f"{node_name}-in-{relation_type.name}"
                    if not dpg.does_item_exist(in_tag):
                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, tag=in_tag):
                            dpg.add_text(relation_type.name)

        # connect the nodes with links
        for u, v, relation_type, data in graph.edges(data=True, keys=True):
            out_tag = f"{u}-out-{relation_type.name}"
            in_tag = f"{v}-in-{relation_type.name}"
            edge_tag = f"{u}|{relation_type.name}|{v}"
            if dpg.does_item_exist(out_tag) and dpg.does_item_exist(in_tag):
                dpg.add_node_link(out_tag, in_tag, parent="kg_editor", tag=edge_tag)
                self.edges[(u, v, relation_type.name)] = data

if __name__ == "__main__":
    kg = WorldKG()
    kg.load_graph("data/world_knowledge.json")
    editor = KG_Editor(kg)
    