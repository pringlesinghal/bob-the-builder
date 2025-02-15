import os
from typing import Dict, List
from dotenv import load_dotenv
from langchain.chat_models import ChatPerplexity
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.evaluation import load_evaluator
from langsmith import Client
from jsonschema import validate, ValidationError
import json
from langchain_core.tracers.context import tracing_v2_enabled
import asyncio

load_dotenv()

# Setup
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

client = Client()

chat_model = ChatPerplexity(
    model="sonar-pro",
    temperature=0,
    pplx_api_key=PERPLEXITY_API_KEY
)

from schemas.Task import Task
from schemas.Link import Link

class TaskManager:
    def __init__(self, max_tasks=20):
        self.tasks = []
        self.max_tasks = max_tasks

    def add_task(self, task):
        if len(self.tasks) < self.max_tasks:
            self.tasks.append(task)
            return True
        return False

    def get_task_count(self):
        return len(self.tasks)

task_manager = TaskManager()

async def a_transform_prompt(prompt: str, schema: Dict, parent_context: str = "") -> Dict:
    schema_string = json.dumps(schema)
    system_message = SystemMessage(content="You are an AI assistant specialized in task decomposition. Your goal is to break down complex tasks into manageable subtasks, ensuring each subtask is independent and actionable. Consider the overall objective and how each subtask contributes to the final goal. Provide clear, concise, and well-structured subtasks.")
    human_message = HumanMessage(content=f"Convert the following prompt into a task: {prompt}\n\nFollowing the JSON schema: {schema_string}\n\nParent context: {parent_context}\n\nFirst, provide your reasoning for how you'll approach this task conversion. Then, output the JSON representation of the task.\n\nFormat your response as follows:\nReasoning: [Your reasoning here]\nAction: [JSON representation of the task]\n\nOnly output the reasoning and JSON representation of the task as described above.")
    
    chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    
    response = await chat_model.ainvoke(chat_prompt.format_messages())
    
    response_content = response.content
    reasoning, action = response_content.split("Action:", 1)
    task_json_string = action.strip()

    try:
        task = json.loads(task_json_string)
        validate(instance=task, schema=schema)
        print(f"Task - {task['task_name']}: {task['task_description']}")
        return task
    except (ValidationError, json.JSONDecodeError) as e:
        print(f"Error in task generation: {e}")
        return None

async def a_decompose_subtasks(task: Dict, schema: Dict, parent_context: str) -> List[Dict]:
    schema_string = json.dumps(schema)
    system_message = SystemMessage(content="You are an AI assistant specialized in task decomposition.")
    human_message = HumanMessage(content=f"Given the task JSON:\n{json.dumps(task)}\nReturn a list of independent subtasks (maximum 3). Avoid overly detailed steps; keep instructions general but actionable. Each subtask should be JSON formatted as follows:\n{schema_string}\n\nParent context: {parent_context}\n\nFirst, provide your reasoning for how you'll approach breaking down this task. Then, output the list of subtasks in JSON format.\n\nFormat your response as follows:\nReasoning: [Your reasoning here]\nAction: [JSON list of subtasks]\n\nOnly output the reasoning and JSON list of subtasks as described above.")
    
    chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    
    response = await chat_model.ainvoke(chat_prompt.format_messages())
    
    response_content = response.content
    reasoning, action = response_content.split("Action:", 1)
    subtasks_json_string = action.strip()

    try:
        subtasks = json.loads(subtasks_json_string)
        for subtask in subtasks[:3]:  # Limit to 3 subtasks
            validate(instance=subtask, schema=schema)
        return subtasks[:3]  # Return only the first 3 subtasks
    except (ValidationError, json.JSONDecodeError) as e:
        print(f"Error in subtask decomposition: {e}")
        return None

async def a_select_tool(subtask: Dict, schema: Dict) -> str:
    schema_string = json.dumps(schema)
    human_message = HumanMessage(content=f"Given the subtask JSON:\n{json.dumps(subtask)}\nfollowing the schema:\n{schema_string}\n\nWhat is the best tool to solve this problem:\nA) LLM only\nB) code only\nC) computer use\nD) mix of more than one tool\n\nFirst, provide your reasoning for selecting the best tool. Then, output only the selected option letter.\n\nFormat your response as follows:\nReasoning: [Your reasoning here]\nAction: [Selected option letter]\n\nOnly output the reasoning and selected option letter as described above.")
    
    chat_prompt = ChatPromptTemplate.from_messages([human_message])
    
    response = await chat_model.ainvoke(chat_prompt.format_messages())
    
    response_content = response.content
    reasoning, action = response_content.split("Action:", 1)
    selected_tool = action.strip()
    print(f"Subtask {subtask['task_id']} - Selected tool: {selected_tool}")
    
    if selected_tool in ['A', 'B', 'C', 'D']:
        return selected_tool
    else:
        print(f"Invalid tool selection for subtask {subtask['task_id']}")
        return None

def execute_task(task: Dict):
    print(f"Executing task: {task['task_description']}")
    # Placeholder for task execution logic
    return f"Result of executing task: {task['task_description']}"

async def a_generate_task(prompt: str, schema: Dict, depth: int = 0, selected_tool: str = 'A', parent_context: str = ""):
    task = await a_transform_prompt(prompt, schema, parent_context)
    if not task or not task_manager.add_task(task):
        return None

    task['selected_tool'] = selected_tool
    task['depth'] = depth

    if task_manager.get_task_count() >= task_manager.max_tasks:
        return task

    subtasks = await a_decompose_subtasks(task, schema, parent_context)
    if not subtasks:
        return task

    all_subtasks_match_parent = True
    task["subtasks"] = []
    for i, subtask in enumerate(subtasks):
        if task_manager.get_task_count() >= task_manager.max_tasks:
            break

        subtask_tool = await a_select_tool(subtask, schema)
        if not subtask_tool:
            continue
        
        subtask['selected_tool'] = subtask_tool
        
        if subtask_tool != selected_tool:
            all_subtasks_match_parent = False

        new_parent_context = f"{parent_context}\nParent task: {task['task_description']}"
        generated_subtask = await a_generate_task(subtask["task_description"], schema, depth+1, subtask_tool, new_parent_context)
        if generated_subtask:
            task["subtasks"].append(generated_subtask)

    if all_subtasks_match_parent:
        task['result'] = execute_task(task)

    return task

def validate_task(task: Dict, schema: Dict):
    try:
        validate(instance=task, schema=schema)
        return True
    except ValidationError as e:
        print(f"Task validation error: {e}")
        return False

def print_task_tree(task, indent=""):
    print(f"{indent}Task: {task['task_name']} (Tool: {task['selected_tool']})")
    if 'subtasks' in task and task['subtasks']:
        for subtask in task['subtasks']:
            print_task_tree(subtask, indent + "  ")
    elif 'result' in task:
        print(f"{indent}  Result: {task['result']}")

def evaluate_task_decomposition(task):
    evaluator = load_evaluator("criteria", criteria={
        "completeness": "Does the decomposition cover all aspects of the task?",
        "actionability": "Are the subtasks concrete and actionable?",
        "independence": "Are the subtasks sufficiently independent?"
    })
    
    evaluation = evaluator.evaluate_strings(
        prediction=json.dumps(task, indent=2),
        input=task['task_description']
    )
    
    return evaluation

async def main():
    with tracing_v2_enabled(project_name="Task Decomposition"):
        prompt = input("Enter a prompt: ")
        full_task = await a_generate_task(prompt, Task.model_json_schema(), 0)

        if full_task and validate_task(full_task, Task.model_json_schema()):
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

if __name__ == "__main__":
    asyncio.run(main())
