#task_execution.py
import subprocess
from typing import Dict, Any
from config import chat_model
from schemas import Task, Link
import json
from llm_interaction import a_generate_code, a_generate_llm_prompt #Add code to generate a code

async def execute_task(task: Dict) -> Any: #Changed execution format to pass in inputs
    """Executes a task based on its selected tool, handling inputs and outputs."""
    print(f"Executing task: {task['task_description']=}")
    selected_tool = task['selected_tool']
    task_description = task['task_description']
    inputs = {}
    for link in task["ingests"]:
        await link.wait_until_ready()
        inputs[link.link_name] = link.value
    try:
        if selected_tool == 'A':
            # Execute deterministic code
            print(f"inputs={inputs}")
            code = await a_generate_code(task_description, input_schema = {link["link_name"]: link["data_type"] for link in task["ingests"]}, output_schema = {link["link_name"]: link["data_type"] for link in task["produces"]})
            if not code:
                return f"Code generation failed for {task_description}" #Check if code was successful
            try:
                # Prepare code execution environment with inputs
                if inputs: #Check if safe and secure
                    input_str = json.dumps(inputs)
                    command = f'python -c "import json; inputs = json.loads(\'{input_str}\'); {code}; print(json.dumps(final_code_output_json))"'
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10).stdout #Added sandboxing
                else:
                    command = f'python -c "{code}; print(json.dumps(final_code_output_json))"'
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10).stdout #Added sandboxing
                for link in task["produces"]:
                    link.set_value(json.loads(result)[link.link_name])
                return result #If code was successful, return
            except Exception as e:
                return f"Code execution error: {e}"
        elif selected_tool == 'B':
            #Use LLM search/reasoning
            prompt = await a_generate_llm_prompt(task_description, inputs, output_schema = {link["link_name"]: link["data_type"] for link in task["produces"]})
            messages = [HumanMessage(content=prompt)]
            response =  chat_model.ainvoke(messages)
            for link in task["produces"]:
                link.set_value(json.loads(response.content)[link.link_name])
            return response.content
        elif selected_tool == 'C':
            # Use computer use agent (Scrapybara, Selenium, etc.)
            # ... [Your Scrapybara/Selenium integration code here] ...
            return "Scrapybara result" #Modify with web interaction
        else:
            return "Invalid tool selection"
    except Exception as e:
        return f"General exectution error: {e}"

