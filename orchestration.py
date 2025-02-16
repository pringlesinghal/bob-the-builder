from typing import Dict, List
from config import MAX_TASKS, MAX_DEPTH
from task_manager import TaskManager
from llm_interaction import a_transform_prompt, a_decompose_subtasks, a_select_tool
from task_execution import execute_task

async def a_generate_task_tree(prompt: str, schema: Dict, task_manager: TaskManager, max_depth: int = MAX_DEPTH):
    # print(f"{prompt=}, {schema=}")
    # print(f"{schema['$defs']['Task'].keys()=}")
    # TODO: clean up
    task = await a_transform_prompt(prompt, schema, "")
    if not task:
        raise Exception("Failed to generate task from user prompt")
    task_queue = [(task, 0, None, "")]
    root_task = None
    tasks_by_depth = {}

    while task_queue:
        current_task, current_depth, parent_task, parent_context = task_queue.pop(0)

        if task_manager.get_task_count() >= task_manager.max_tasks:
            break

        selected_tool = await a_select_tool(current_task, schema, current_depth, max_depth)
        if not selected_tool:
            continue

        current_task['selected_tool'] = selected_tool
        current_task['depth'] = current_depth

        if not task_manager.add_task(current_task):
            break

        if root_task is None:
            root_task = current_task

        if parent_task:
            if 'subtasks' not in parent_task:
                parent_task['subtasks'] = []
            parent_task['subtasks'].append(current_task)

        if current_depth not in tasks_by_depth:
            tasks_by_depth[current_depth] = []
        tasks_by_depth[current_depth].append(current_task)
        if selected_tool == 'D':  # Only decompose if "Mix of Tools" is selected
            subtasks = await a_decompose_subtasks(current_task, schema, parent_context)
            if subtasks:
                new_parent_context = f"{parent_context}\nParent task: {current_task['task_description']}"
                for subtask in subtasks:
                    task_queue.append((subtask, current_depth + 1, current_task, new_parent_context))
        else:
            current_task['result'] = execute_task(current_task)

    return root_task, tasks_by_depth