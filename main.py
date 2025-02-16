# main.py
import asyncio
import os
from schemas import Task
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from config import LANGCHAIN_TRACING_V2, chat_model
from task_manager import TaskManager
from orchestration import a_generate_task_tree
from tree_utils import print_task_tree
from evaluation import evaluate_task_decomposition
from langchain_core.tracers.context import tracing_v2_enabled
import json
from typing import Dict
from jsonschema import validate, ValidationError

async def main():
    task_manager = TaskManager() #Creating task manager object here
    with tracing_v2_enabled(project_name="Task Decomposition") if LANGCHAIN_TRACING_V2 else open(os.devnull, "w") as f: # only trace if the relevant flag is turned on
        prompt = input("Enter a prompt: ")
        # TODO: How can I transform the user prompt to be more specific and actionable for the LLM?
        # system_message = SystemMessage(
        #     content="You are a computer use agent capable of doing anything. Rephrase the user's task prompt to highlight the key action verbs in the user's request and identify what needs to be done.")
        # human_message = HumanMessage(
        #     content=f"Output a very concise task prompt to help an LLM understand the user's task prompt: {prompt}.\n\nEmphasize what action verbs are specified by the user. Only output the prompt and nothing else.")

        # chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])

        # response = await chat_model.ainvoke(chat_prompt.format_messages())
        # response_content = response.content
        # print(f"{response_content=}")
        response_content = prompt

        full_task, tasks_by_depth = await a_generate_task_tree(response_content, Task.model_json_schema(), task_manager) # Passing task_manager object

        if full_task and validate_task(full_task, Task.model_json_schema()):
             # Print tasks by depth
            for depth in sorted(tasks_by_depth.keys()):
                print(f"\nTasks at Depth {depth}:")
                for task in tasks_by_depth[depth]:
                    print(f"  - {task['task_name']}: {task['task_description']} (Tool: {task.get('selected_tool', 'N/A')})")

            print("\nTask Tree Visualization:")
            print_task_tree(full_task)
            with open("out.txt", 'w') as file:
                json.dump(full_task, file, indent=4)

            evaluation = evaluate_task_decomposition(full_task)
            print("\nTask Decomposition Evaluation:")
            print(json.dumps(evaluation, indent=2))
        else:
            print("Task generation or validation failed.")

    print(f"\nTotal tasks generated: {task_manager.get_task_count()}")


def validate_task(task: Dict, schema: Dict): #Keeping this function here since it is tiny
    try:
        validate(instance=task, schema=schema)
        return True
    except ValidationError as e:
        print(f"Task validation error: {e}")
        return False

if __name__ == "__main__":
    asyncio.run(main())
