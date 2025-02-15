from openai import OpenAI
import json
from dotenv import load_dotenv
import os
load_dotenv()

PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")

client = OpenAI(
    api_key=PERPLEXITY_API_KEY,
    base_url="https://api.perplexity.ai"
)

from schemas.Task import Task
from schemas.Link import Link



# given user prompt and schema, generate a task following the schema Task
# infer inputs and outputs, generate links following the schema Link
def generate_task(prompt, schema):
    schema_string = json.dumps(schema)
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Convert the following prompt into a task: " + prompt + "\n\nFollowing the JSON schema: " + schema_string + "\n\nOnly output the JSON representation of the task and nothing else."},
    ]

    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
        max_tokens=1000
    )

    task_json_string = response.choices[0].message.content
    print(task_json_string)

    messages.append({"role": "assistant", "content": task_json_string})
    messages.append({"role": "user", "content": "Given the task JSON:" + task_json_string + "\nreturn a list of independent subtasks. Each subtask should be JSON formatted as follows:\n" + schema_string + "\n\nOnly output the subtasks and nothing else."})

    response = client.chat.completions.create(
        model="sonar-pro",
        messages=messages,
        max_tokens=1000
    )

    subtasks_json_string = response.choices[0].message.content
    print(subtasks_json_string)

prompt = input("Enter a prompt: ")
generate_task(prompt, Task.model_json_schema())