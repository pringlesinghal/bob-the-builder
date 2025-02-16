def print_task_tree(task, indent=""):
    selected_tool = task.get('selected_tool', 'N/A')
    print(f"{indent}Task: {task['task_name']} (Tool: {selected_tool})")
    if 'subtasks' in task and task['subtasks']:
        for subtask in task['subtasks']:
            print_task_tree(subtask, indent + " ")
    elif 'result' in task:
        print(f"{indent} Result: {task['result']}")