# llm_interaction.py
import json
from typing import Dict, List
from langchain.prompts import ChatPromptTemplate
from langchain.schema import HumanMessage, SystemMessage
from jsonschema import validate, ValidationError
from config import chat_model, MAX_RETRIES, MAX_SUBTASKS  # Import chat model

async def a_transform_prompt(prompt: str, schema: Dict, parent_context: str = "") -> Dict:
    schema_string = json.dumps(schema)
    system_message = SystemMessage(
        content="You are an AI assistant specialized in creating clear, concise JSON objects following a schema.")
    human_message = HumanMessage(
        content=f"Convert the following prompt into a task: {prompt}\n\nFollowing the JSON schema: {schema_string}\n\nParent context: {parent_context}\n\nFirst, provide your reasoning for how you'll approach this task conversion. Then, output the JSON representation of the task. Set subtasks to [] (empty list)\n\nFormat your response as follows:\nReasoning: [Your reasoning here]\nAction: [JSON representation of the task]\n\nOnly output the reasoning and JSON representation of the task as described above.")

    chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])

    for attempt in range(MAX_RETRIES):
        try:
            response = await chat_model.ainvoke(chat_prompt.format_messages())
            response_content = response.content
            reasoning, action = response_content.split("Action:", 1)
            task_json_string = action.strip()
            task = json.loads(task_json_string)
            validate(instance=task, schema=schema)
            return task
        except (ValidationError, json.JSONDecodeError, ValueError) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == MAX_RETRIES - 1:
                print(f"Error in task generation after {MAX_RETRIES} attempts.")
                return None #Return None if error persists

async def a_decompose_subtasks(task: Dict, schema: Dict, parent_context: str) -> List[Dict]:
    schema_string = json.dumps(schema)
    open("task.txt", "w").write(str(task))
    task_dict = json.dumps(task)
    system_message = SystemMessage(content="You are an AI assistant specialized in task decomposition.")
    human_message = HumanMessage(content=f"Given the task JSON:\n{task_dict}\nReturn a list of independent subtasks (maximum {MAX_SUBTASKS}). Avoid overly detailed steps; keep instructions general but actionable. Each subtask should be JSON formatted as follows:\n{schema_string}\n\nParent context: {parent_context}\n\nFirst, provide your reasoning for how you'll approach breaking down this task. Then, output the list of subtasks in JSON format. Each subtask JSON should have 'subtasks' set to [] (empty list).\n\nFormat your response as follows:\nReasoning: [Your reasoning here]\nAction: [JSON list of up to {MAX_SUBTASKS}subtasks]\n\nOnly output the reasoning and JSON list of subtasks as described above.")
    
    chat_prompt = ChatPromptTemplate.from_messages([system_message, human_message])
    
    for attempt in range(MAX_RETRIES): #Add retry loop
        try:
            response = await chat_model.ainvoke(chat_prompt.format_messages())
            response_content = response.content
            reasoning, action = response_content.split("Action:", 1)
            subtasks_json_string = action.strip()
            subtasks = json.loads(subtasks_json_string)
            print(f"{subtasks=}")
            # TODO: handle this exception better
            if len(subtasks) > MAX_SUBTASKS:
                raise ValueError(f"More than {MAX_SUBTASKS} subtasks generated.")
            for subtask in subtasks[:MAX_SUBTASKS]:  # Limit to MAX_SUBTASKS subtasks
                validate(instance=subtask, schema=schema)
            return subtasks[:MAX_SUBTASKS]  # Return only the first MAX_SUBTASKS subtasks
        except (ValidationError, json.JSONDecodeError, ValueError) as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == MAX_RETRIES - 1: #If max retries reached, print to log and return None
                print(f"Error in subtask decomposition after {MAX_RETRIES} attempts.")
                return None

async def a_select_tool(subtask: Dict, schema: Dict, depth: int, max_depth: int) -> str:
    schema_string = json.dumps(schema)
    print(f"{subtask['subtasks']=}")
    subtask_dict = json.dumps(subtask)
    human_message = HumanMessage(content=f"""Given the subtask JSON:
{subtask_dict}
following the schema:
{schema_string}

Current depth: {depth}
Maximum depth: {max_depth}

**Part 1: Initial Assessment and Decomposition**

1. **Task Complexity & Depth Limit:**
   - Is this task inherently complex, requiring multiple steps or diverse information sources?
   - Is the current depth less than the maximum allowed depth ({max_depth})?
   - IF YES to both: Choose "D) Mix of Tools" and explain how to decompose.
     (Decomposition Strategy: Aim to isolate components best suited for computer use agents, LLM reasoning, and deterministic code.)
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
      - Select this by default if the task is complex but we have exceeded the maximum depth.
**Decision Process (Choose ONE of A, B, C, or D based on which best fits the task after considering the above guidelines).**

Provide your reasoning for selecting the best approach, describing the pros and cons of each option. Then, output only the selected option letter.

Format your response as follows:
Reasoning: [Your detailed reasoning here, explaining WHY you chose the selected tool and why the others are less suitable]
Action: [Selected option letter]

Only output the reasoning and selected option letter as described above."""
    )
        
    chat_prompt = ChatPromptTemplate.from_messages([human_message])
        
    for attempt in range(MAX_RETRIES): #Add retry loop
        try:
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
        except ValueError as e:
            print(f"Attempt {attempt + 1} failed: {e}")
            if attempt == MAX_RETRIES - 1: #If max retries reached, print to log and return None
                print(f"Error in selecting tool after {MAX_RETRIES} attempts.")
                return None

