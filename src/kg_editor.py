from knowledge import WorldKG
import dearpygui.dearpygui as dpg
import networkx as nx
import ontology

class KG_Editor:
    def __init__(self, kg : WorldKG):
        self.kg = kg 
        self.edges = {} # (u, v, relation_name) : attributes

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
                key=relation_name,
                **attributes
            )

            link_tag = f"{source_node}|{relation_name}|{target_node}"
            dpg.add_node_link(source_attr, target_attr, parent=sender, tag=link_tag)
            self.edges[(source_node, target_node, relation_name)] = attributes

        attributes = ontology.RELATION_ATTRIBUTES.get(relation_type, {})
        self.link_attributes_input(dict(attributes), on_complete=on_attributes_ready)
               
    def edit_link(self, link_tag: str):
        u, relation_name, v = link_tag.split('|')
        attributes = self.edges.get((u, v, relation_name))
        relation_type = ontology.RelationType[relation_name]

        def on_attributes_ready(attributes):
            self.kg.graph[u][v][relation_name].clear()
            self.kg.graph[u][v][relation_name].update(attributes)

        if attributes is not None:
            self.link_attributes_input(dict(attributes), on_attributes_ready)

    def link_attributes_input(self, attributes : dict, on_complete):
        if dpg.does_item_exist("relation_attributes_input_dialog"):
            dpg.delete_item("relation_attributes_input_dialog", children_only=True)

        attributes_count = len(attributes)
        # If no attributes are needed, run the callback immediately with {}
        if attributes_count == 0:
            on_complete(attributes)
            return
        
        for attribute, val in attributes.items():
            dpg.add_input_float(
                label=attribute, 
                width=100, 
                default_value=val, 
                parent="relation_attributes_input_dialog",
                format="%.2f",
                step=1,
                tag=f"{attribute}_tag",
            )

        def _submit():
            input_tags = [
                dpg.get_item_alias(child)
                for child in dpg.get_item_children("relation_attributes_input_dialog", slot=1)
                if "mvInput" in dpg.get_item_type(child)
            ]
            
            for tag in input_tags:
                attr_name = dpg.get_item_label(tag)
                attr_val = dpg.get_value(tag)
                attributes[attr_name] = attr_val
            
            dpg.configure_item("relation_attributes_input_dialog", show=False)
            
            on_complete(attributes)

        dpg.add_spacer(height=5, parent="relation_attributes_input_dialog")
        dpg.add_button(label="OK", width=50, callback=_submit, parent="relation_attributes_input_dialog")
        dpg.configure_item("relation_attributes_input_dialog", show=True, height=attributes_count * 30 + 40)

    def edit_node(self, node_tag: int):
        if dpg.does_item_exist("edit_node_dialog"):
            dpg.delete_item("edit_node_dialog", children_only=True)

        node_label = dpg.get_item_label(node_tag)
        attributes = self.kg.graph.nodes[node_label]
        attributes_count = len(attributes)

        dpg.add_input_text(
            label="id", 
            width=100, 
            default_value=node_label, 
            parent="edit_node_dialog",
            tag=f"id_tag",
            enabled=True if attributes['scope'] == "INSTANCE" else False,
        )
        
        for attribute, val in attributes.items():
            dpg.add_input_text(
                label=attribute, 
                width=100, 
                default_value=str(val), 
                parent="edit_node_dialog",
                tag=f"{attribute}_tag",
                enabled=False if attribute in ['entity_type', 'scope'] else True
            )

        def _submit():
            input_tags = [
                dpg.get_item_alias(child)
                for child in dpg.get_item_children("edit_node_dialog", slot=1)
                if "mvInput" in dpg.get_item_type(child)
            ]
            
            for tag in input_tags:
                attr_name = dpg.get_item_label(tag)
                attr_val = dpg.get_value(tag)

                if (attr_name != "id"):
                    self.kg.graph.nodes[node_label][attr_name] = attr_val

            # rename node
            new_name = dpg.get_value("id_tag")
            if new_name not in self.kg.graph.nodes:
                self.kg.rename_node(node_label, new_name)
                dpg.configure_item(node_tag, label=new_name)
            
            dpg.configure_item("edit_node_dialog", show=False)
            
        dpg.add_spacer(height=5, parent="edit_node_dialog")
        dpg.add_button(label="OK", width=50, callback=_submit, parent="edit_node_dialog")
        dpg.configure_item("edit_node_dialog", show=True, height=attributes_count * 30 + 70)

    
    def add_node(self):
        if dpg.does_item_exist("add_node_dialog"):
            dpg.delete_item("add_node_dialog", children_only=True)

        entity_type = ontology.EntityType.VILLAGE
        scope = ontology.EntityScope.INSTANCE

        def _on_entity_type_change(sender, app_data):
            nonlocal entity_type, scope
            entity_type = ontology.EntityType[app_data]  
            if entity_type not in ontology.SPAWNABLE:
                scope = ontology.EntityScope.CLASS
                dpg.configure_item("id", default_value=entity_type.name, enabled=False)
                dpg.configure_item("scope", default_value=ontology.EntityScope.CLASS.name, enabled=False)
            else:
                dpg.configure_item("id", default_value="", enabled=True)
                dpg.configure_item("scope", default_value=ontology.EntityScope.INSTANCE.name, enabled=True)

        dpg.add_input_text(
            label="id", 
            width=100, 
            default_value="",
            parent="add_node_dialog",
            tag=f"id",
            enabled=True,
        )
        
        dpg.add_combo(
            items=[
                entity_type.name 
                for entity_type in ontology.EntityType 
                if entity_type != ontology.EntityType.UNKOWN],
            default_value=ontology.EntityType.VILLAGE.name,
            label="entity_type",
            tag="entity_type",
            parent="add_node_dialog",
            callback= _on_entity_type_change
        )

        def _on_scope_change(sender, app_data):
            nonlocal entity_type, scope
            scope = ontology.EntityScope[app_data]  
            if scope == ontology.EntityScope.CLASS:
                dpg.configure_item("id", default_value=entity_type.name, enabled=False)
                if entity_type in ontology.SPAWNABLE:
                    dpg.configure_item("count", enabled=True)
            else:
                dpg.configure_item("id", default_value="", enabled=True)

        dpg.add_combo(
            items=[scope.name for scope in ontology.EntityScope],
            default_value=ontology.EntityScope.INSTANCE.name,
            label="scope",
            tag="scope",
            parent="add_node_dialog",
            callback= _on_scope_change,
            enabled=True
        )

        dpg.add_input_int(
            label="count",
            tag="count",
            width=100,
            parent="add_node_dialog",
            default_value=1,
            enabled=False
        )
        
        # loop through and add input boxes for entity type specific attributes if any
        # TO DO

        def _submit():
            input_tags = [
                dpg.get_item_alias(child)
                for child in dpg.get_item_children("add_node_dialog", slot=1)
                if "mvInput" in dpg.get_item_type(child)
                or "mvCombo" in dpg.get_item_type(child)
            ]

            data = {}
            for tag in input_tags:
                attr_name = dpg.get_item_label(tag)
                attr_val = dpg.get_value(tag)

                data[attr_name] = attr_val
            
            # add node
            id = data.pop("id")
            self.kg.graph.add_node(id, **data)

            with dpg.node(label=id, parent="kg_editor", pos=[0,0]):
                entity_type = ontology.EntityType[data['entity_type']]

                # create unique Output attributes per relation type
                for relation_type in ontology.VALID_RELATIONS_FROM.get(entity_type, []):
                    out_tag = f"{id}-out-{relation_type.name}"
                    if not dpg.does_item_exist(out_tag):
                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Output, tag=out_tag):
                            dpg.add_text(relation_type.name)

                # create unique Input attributes per relation type
                for relation_type in ontology.VALID_RELATIONS_TO.get(entity_type, []):
                    in_tag = f"{id}-in-{relation_type.name}"
                    if not dpg.does_item_exist(in_tag):
                        with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Input, tag=in_tag):
                            dpg.add_text(relation_type.name)

            dpg.configure_item("add_node_dialog", show=False)
            
        dpg.add_spacer(height=5, parent="add_node_dialog")
        dpg.add_button(label="OK", width=50, callback=_submit, parent="add_node_dialog")
        dpg.configure_item("add_node_dialog", show=True, height= 4 * 30 + 40)
    
    
    # callback runs when user attempts to disconnect attributes
    def delink_callback(self, sender, app_data):
        # app_data -> link_id
        link_id = dpg.get_item_alias(app_data)
        u, relation_name, v = link_id.split("|")
        self.kg.graph.remove_edge(u, v, key=relation_name)
        dpg.delete_item(link_id)


    def delete_selected_nodes(self):
        # Retrieve all currently highlighted nodes in the editor
        selected_nodes = dpg.get_selected_nodes("kg_editor")
        for node_tag in selected_nodes:
            node_label = dpg.get_item_label(node_tag)
            self.kg.graph.remove_node(node_label)
        self.display_graph()

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

            with dpg.node(label=node_name, parent="kg_editor", pos=screen_pos):
                entity_type = self.kg.get_entity_type(node_name)

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
            out_tag = f"{u}-out-{relation_type}"
            in_tag = f"{v}-in-{relation_type}"
            link_tag = f"{u}|{relation_type}|{v}"
            if dpg.does_item_exist(out_tag) and dpg.does_item_exist(in_tag):
                dpg.add_node_link(out_tag, in_tag, parent="kg_editor", tag=link_tag)
                self.edges[(u, v, relation_type)] = data
    
if __name__ == "__main__":
    kg = WorldKG()
    kg.load_graph("data/world_knowledge.json")
    editor = KG_Editor(kg)
    