import knowledge as knowledge
from translator import Translator
import networkx as nx
import sys
import primitives as primitives
import ontology as ontology

class Planner:
    def __init__(self, translator: Translator):
        self.tasks = {}
        self.plan = []

        self.translator = translator
        translator.translate()
        self._generate_tasks()

    def _generate_tasks(self):  
        self.tasks["task:terrain"] = primitives.GenerationTask(
            task_id= "task:terrain",
            task_type= primitives.TaskType.GENERATE_TERRAIN,
            )

        self.tasks["task:biomes"] = primitives.GenerationTask(
                task_id= "task:biomes",
                task_type= primitives.TaskType.GENERATE_ENTITY
            )

        self.tasks["task:rivers"] = primitives.GenerationTask(
                task_id= "task:rivers",
                task_type= primitives.TaskType.GENERATE_ENTITY
            )
        
        for entity_id in self.translator.spawnable_entities:
            entity = self.translator.entities[entity_id]
            task_id = f"task:{entity.entity_id}"
            task = primitives.GenerationTask(
                task_id= task_id,
                task_type= primitives.TaskType.GENERATE_ENTITY,
                entity= entity,
                constraints= self.translator.entity_constraints_map.get(entity.entity_id)
            )
            
            self.tasks[task_id] = task

        for i, constraint in enumerate(self.translator.connections):
            task_id = f"task:connection_{i}"
            task = primitives.GenerationTask(
                task_id = task_id,
                task_type= primitives.TaskType.GENERATE_CONNECTION,
                constraints= [constraint]
            )

            self.tasks[task_id] = task
        self._generate_dependencies()

    def _generate_dependencies(self) -> set[tuple[str, str]]:
        dependencies = set()
        dependencies.add(("task:terrain", "task:biomes"))
        dependencies.add(("task:biomes", "task:rivers"))

        for task_id, task in self.tasks.items():
            if not task.constraints:
                continue

            for constraint in task.constraints:
                for prereq_id in constraint.get_dependencies():
                    prereq_entity = self.translator.entities.get(prereq_id)
                 
                    if prereq_entity:
                        entity_type = prereq_entity.entity_type
                        spatial_type = ontology.SPATIAL_TYPE_MAP.get(entity_type)
                        
                        if spatial_type == ontology.SpatialType.BIOME:
                            dependencies.add(("task:biomes", task_id))
                            
                        elif spatial_type == ontology.SpatialType.POINT:
                            dependencies.add((f"task:{prereq_id}", task_id))
                                                    # 💡 Rule C: Handle other features (like Rivers) if they have unique steps
                        elif entity_type == ontology.EntityType.RIVER:
                            dependencies.add(("task:rivers", task_id))
                    else:
                        if prereq_id in ["terrain", "biomes", "rivers"]:
                            dependencies.add((f"task:{prereq_id}", task_id))
                        else:
                            dependencies.add((f"task:{prereq_id}", task_id))

        return dependencies    

    def generate_plan(self):
        dependencies = self._generate_dependencies()
        G = nx.DiGraph()
        G.add_edges_from(dependencies)

        G.add_nodes_from(self.tasks.keys())

        try:
            sorted_ids  = list(nx.lexicographical_topological_sort(G))
            self.plan = [self.tasks[tid] for tid in sorted_ids] 
        except nx.NetworkXUnfeasible:
            cycle = nx.find_cycle(G)   
            print(f"Invalid knowledge graph - cycle found: {cycle}")  
            sys.exit(1)


if __name__ == "__main__":
    kg = knowledge.WorldKG()
    kg.load_graph("world_knowledge.json")

    translator = Translator(kg)

    planner = Planner(translator)
    planner.generate_plan()
    print(planner.plan)
    
   

   

