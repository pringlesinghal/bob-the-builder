import os
from typing import Dict, List, Tuple
from dotenv import load_dotenv
from langchain_community.chat_models import ChatPerplexity
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from langchain.evaluation import load_evaluator
from langsmith import Client
from jsonschema import validate, ValidationError
import json
from langchain_core.tracers.context import tracing_v2_enabled
import asyncio
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.feature_extraction.text import TfidfVectorizer

# Load environment variables
load_dotenv()

# Setup LangSmith tracing
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_ENDPOINT"] = "https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("LANGCHAIN_API_KEY")

# Initialize LangSmith client
client = Client()

# Configure Perplexity chat model
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
chat_model = ChatPerplexity(
    model="sonar-pro",
    temperature=0,
    pplx_api_key=PERPLEXITY_API_KEY,
    model_kwargs={"seed": 42}  # Set seed for reproducibility
)

# Import task and link schemas
from schemas.Task import Task
from schemas.Link import Link

# Task manager to limit total tasks and ensure diversity
class TaskManager:
    def __init__(self, max_tasks=20):
        self.tasks = []
        self.max_tasks = max_tasks
        self.tfidf_vectorizer = TfidfVectorizer() # Initialize TF-IDF vectorizer

    def add_task(self, task):
        if len(self.tasks) < self.max_tasks:
            self.tasks.append(task)
            self.update_tfidf() # Update TF-IDF matrix after each addition
            return True
        return False

    def get_task_count(self):
        return len(self.tasks)

    def update_tfidf(self):
         # Updates the TF-IDF matrix with the latest task descriptions
        descriptions = [task['task_description'] for task in self.tasks]
        if descriptions:  # Only fit if there are any descriptions
            self.tfidf_matrix = self.tfidf_vectorizer.fit_transform(descriptions)

    def check_similarity(self, new_task_description, threshold=0.8): # Threshold for similarity
        if not hasattr(self, 'tfidf_matrix') or self.tfidf_matrix.shape[0] == 0:
            return False  # No existing tasks to compare to

        new_vector = self.tfidf_vectorizer.transform([new_task_description])
        similarities = cosine_similarity(new_vector, self.tfidf_matrix)
        max_similarity = similarities.max()

        return max_similarity > threshold # Return True if new task is too similar

# Initialize task manager
task_manager = TaskManager()

# Helper function to assess task complexity
async def assess_complexity(task_description: str):
    prompt = f"Assess the complexity of the following task description:\n\n{task_description}\n\nRespond with 'SIMPLE' if the task is straightforward and requires no further decomposition. Respond with 'COMPLEX' if the task would benefit from further decomposition."
    messages = [HumanMessage(content=prompt)]
    response = await chat_model.ainvoke(messages)
    return response.content.strip().upper() == "COMPLEX"

# Transform the prompt into a task using an LLM
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
        #print(f"Task - {task['task_name']}: {task['task_description']}") #Removed print here
        return task
    except (ValidationError, json.JSONDecodeError) as e:
        print(f"Error in task generation: {e}")
        return None

# Decompose a task into smaller subtasks using an LLM
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

# Select the best tool for a given subtask
async def a_select_tool(subtask: Dict, schema: Dict, depth: int, max_depth: int) -> str:
    schema_string = json.dumps(schema)
    human_message = HumanMessage(content=f"""Given the subtask JSON:
{json.dumps(subtask)}
following the schema:
{schema_string}

Current depth: {depth}
Maximum depth: {max_depth}

**Part 1: Initial Assessment and Decomposition**

1. **Task Complexity & Depth Limit:**
   - Is this task inherently complex, requiring multiple steps or diverse information sources?
   - Is the current depth less than the maximum allowed depth ({max_depth})?
   - IF YES to both: Choose "D) Mix of Tools" and explain how to decompose.
     (Decomposition Strategy: Aim to isolate components best suited for computer use, LLM reasoning, and deterministic code.)
   - IF NO to either: Proceed to Part 2.

**Part 2: Tool Selection for Non-Decomposed (or Leaf) Tasks**

Now that we've assessed complexity, consider which single tool is best suited to DIRECTLY SOLVE the task (if it wasn't chosen to be decomposed). Select ONE of the following:

   A) **Deterministic Code:** (Best for precise, rule-based operations; fast & reliable)
      - Ideal for:
         - Data transformation (e.g., cleaning, formatting, calculations)
         - File manipulation (e.g., downloading, parsing, format conversion)
         - Mathematical computations & logical operations
         - API interactions where the API is well-defined and predictable.
      - Examples: Sorting a list, converting a date format, calculating statistics, extracting data with regular expressions.
      - NOT Suitable: Tasks requiring nuanced understanding of natural language, creative generation, or adapting to unpredictable environments.

   B) **LLM Search & Reasoning:** (Best for knowledge-intensive tasks, nuanced text understanding, creative generation; adaptable but can be less precise)
      - Ideal for:
         - Information retrieval from the web when the answer isn't a simple fact but requires synthesizing information from multiple sources (e.g., "What are the current trends in AI research?")
         - Complex text analysis (e.g., sentiment analysis, summarization, topic extraction)
         - Creative content generation (e.g., writing blog posts, generating marketing copy)
         - Answering questions requiring reasoning and inference (e.g., "What are the potential implications of this new technology?")
      - Examples: Researching a topic, summarizing a document, translating text, writing a creative story.
      - NOT Suitable: Tasks requiring precise calculations, structured data manipulation, or reliable interaction with specific applications.

   C) **Computer Use Agent:** (Best for interactive tasks involving websites, applications with visual interfaces, or when direct manipulation is needed; can be slow & less reliable)
      - Ideal for:
         - Interacting with websites (e.g., filling out forms, clicking buttons, scraping data that requires dynamic interaction)
         - Automating tasks within desktop applications
         - Tasks requiring continuous visual feedback or responding to changes in a UI
         - Situations where the information source is only accessible through interactive steps.
      - Examples: Booking a flight, filling out an online application, monitoring a website for changes.
      - NOT Suitable: Tasks that can be solved directly with information retrieval or deterministic code, or that don't involve interactive systems.

**Decision Process (Choose ONE of A, B, C, or D based on which best fits the task after considering the above guidelines)**

Provide your reasoning for selecting the best approach. Then, output only the selected option letter.

Format your response as follows:
Reasoning: [Your detailed reasoning here, explaining WHY you chose the selected tool and why the others are less suitable]
Action: [Selected option letter]

Only output the reasoning and selected option letter as described above."""
    )
        
    chat_prompt = ChatPromptTemplate.from_messages([human_message])
    
    response = await chat_model.ainvoke(chat_prompt.format_messages())
    
    response_content = response.content
    reasoning, action = response_content.split("Action:", 1)
    selected_tool = action.strip()
    print(f"Subtask {subtask['task_id']} - Selected tool: {selected_tool}")
    print(f"Reasoning: {reasoning.strip()}")
    
    if selected_tool in ['A', 'B', 'C', 'D']:
        return selected_tool
    else:
        print(f"Invalid tool selection for subtask {subtask['task_id']}")
        return None

# Execute a task (placeholder)
def execute_task(task: Dict):
    print(f"Executing task: {task['task_description']}")
    # Placeholder for task execution logic
    return f"Result of executing task: {task['task_description']}"

# Generate task tree in a breadth-first manner
async def a_generate_task_tree(prompt: str, schema: Dict, max_depth: int = 3):
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

        if task_manager.check_similarity(task['task_description']):
            print(f"Skipping similar task: {task['task_description']}")
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

    for depth in sorted(tasks_by_depth.keys()):
        print(f"\nTasks at Depth {depth}:")
        for task in tasks_by_depth[depth]:
            print(f"  - {task['task_name']}: {task['task_description']} (Tool: {task['selected_tool']})")

    return root_task

# Validate a task against the schema
def validate_task(task: Dict, schema: Dict):
    try:
        validate(instance=task, schema=schema)
        return True
    except ValidationError as e:
        print(f"Task validation error: {e}")
        return False

# Print the task tree for visualization
def print_task_tree(task, indent=""):
    selected_tool = task.get('selected_tool', 'N/A')
    print(f"{indent}Task: {task['task_name']} (Tool: {selected_tool})")
    if 'subtasks' in task and task['subtasks']:
        for subtask in task['subtasks']:
            print_task_tree(subtask, indent + "  ")
    elif 'result' in task:
        print(f"{indent}  Result: {task['result']}")

# Evaluate the task decomposition using criteria
def evaluate_task_decomposition(task):
    evaluator = load_evaluator("criteria", 
        criteria={
            "completeness": "Does the decomposition cover all aspects of the task?",
            "actionability": "Are the subtasks concrete and actionable?",
            "independence": "Are the subtasks sufficiently independent?"
        },
        llm=chat_model  # Use the ChatPerplexity model for evaluation
    )
    
    evaluation = evaluator.evaluate_strings(
        prediction=json.dumps(task, indent=2),
        input=task['task_description']
    )
    
    return evaluation

# Main function to orchestrate the task decomposition process
async def main():
    with tracing_v2_enabled(project_name="Task Decomposition"):
        prompt = input("Enter a prompt: ")
        full_task = await a_generate_task_tree(prompt, Task.model_json_schema(), max_depth=3)

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

# Run the main function
if __name__ == "__main__":
    asyncio.run(main())
