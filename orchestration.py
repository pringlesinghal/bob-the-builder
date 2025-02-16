from typing import Dict, List
from config import MAX_TASKS, MAX_DEPTH
from task_manager import TaskManager
from llm_interaction import a_transform_prompt, a_decompose_subtasks, a_select_tool
from task_execution import execute_task

async def a_generate_task_tree(prompt: str, schema: Dict, task_manager: TaskManager, max_depth: int = MAX_DEPTH):
    task_queue = [(prompt, 0, None, "")]
    root_task = None
    tasks_by_depth = {}

    while task_queue:
        current_prompt, current_depth, parent_task, parent_context = task_queue.pop(0)

        if task_manager.get_task_count() >= task_manager.max_tasks:
            break

        task = await a_transform_prompt(current_prompt, schema, parent_context)
        if not task:
            continue

        selected_tool = await a_select_tool(task, schema, current_depth, max_depth)
        if not selected_tool:
            continue

        task['selected_tool'] = selected_tool
        task['depth'] = current_depth

        if not task_manager.add_task(task):
            break

        if root_task is None:
            root_task = task

        if parent_task:
            if 'subtasks' not in parent_task:
                parent_task['subtasks'] = []
            parent_task['subtasks'].append(task)

        if current_depth not in tasks_by_depth:
            tasks_by_depth[current_depth] = []
        tasks_by_depth[current_depth].append(task)

        if selected_tool == 'D':  # Only decompose if "Mix of Tools" is selected
            subtasks = await a_decompose_subtasks(task, schema, parent_context)
            if subtasks:
                new_parent_context = f"{parent_context}\nParent task: {task['task_description']}"
                for subtask in subtasks:
                    task_queue.append((subtask['task_description'], current_depth + 1, task, new_parent_context))
        else:
            task['result'] = execute_task(task)

    return root_task, tasks_by_depth