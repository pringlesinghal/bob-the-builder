#task_execution.py
import subprocess
from typing import Optional, Dict, Any, List
from config import chat_model, clean_json, MAX_RETRIES
from schemas import Task, Link
import json
from llm_interaction import a_generate_code, a_generate_llm_prompt #Add code to generate a code
from langchain.schema import HumanMessage
import re
import shlex
from config import SCRAP_API_KEY

from scrapybara import Scrapybara
from scrapybara.tools import BashTool, ComputerTool, EditTool
from scrapybara.anthropic import Anthropic
from scrapybara.prompts import UBUNTU_SYSTEM_PROMPT
from enum import Enum, auto
from dataclasses import dataclass
from pathlib import Path
import webbrowser
from jsonschema import ValidationError

async def execute_task(task: Dict) -> Any: #Changed execution format to pass in inputs
    """Executes a task based on its selected tool, handling inputs and outputs."""
    print(f"Executing task: {task['task_description']=}")
    selected_tool = task['selected_tool']
    task_description = task['task_description']
    inputs = {}
    print(task["task_name"])
    for link in task["ingests"]:
        link = Link.model_validate(link)
        print("Waiting until ready:", link.link_name)
        await link.wait_until_ready()
        print("Continuing...", link.link_name)
        inputs[link.link_name] = link.value
    try:
        if selected_tool == 'E':
            # Execute deterministic code
            print(f"inputs={inputs}")
            code = await a_generate_code(task_description, input_schema = {link["link_name"]: link["data_type"] for link in task["ingests"]}, output_schema = {link["link_name"]: link["data_type"] for link in task["produces"]})
            if not code:
                return f"Code generation failed for {task_description}" #Check if code was successful
            try:
                # Prepare code execution environment with inputs
                print(repr(code))
                print("------------")
                code = re.search(r'```python(.*?)```', code, re.DOTALL).group(1).strip()
                # code = code.replace('"', "'")
                if inputs: #Check if safe and secure
                    input_str = json.dumps(inputs)
                    full_code = f"import json; inputs = json.loads(\'{input_str}\'); {code}"
                    escaped_code = shlex.quote(full_code)
                    command = f"python -c {escaped_code}"
                    # command = f"python -c \"import json; inputs = json.loads('{input_str}'); {code}; print(json.dumps(final_code_output_json))\""
                    print("COMMAND:\n", repr(command))
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10).stdout #Added sandboxing
                else:
                    escaped_code = shlex.quote(code)
                    command = f'python -c {escaped_code}'
                    # command = f'python -c "{code}"'
                    print("COMMAND:\n", command)
                    result = subprocess.run(command, shell=True, capture_output=True, text=True, timeout=10).stdout #Added sandboxing
                for link in task["produces"]:
                    link = Link.model_validate(link)
                    link.set_value(json.loads(result)[link.link_name])
                return result #If code was successful, return
            except Exception as e:
                return f"Code execution error: {e}"
        elif selected_tool == 'B':
            #Use LLM search/reasoning
            prompt = await a_generate_llm_prompt(task_description, inputs, output_schema = {link["link_name"]: link["data_type"] for link in task["produces"]})
            messages = [HumanMessage(content=prompt)]
            for attempt in range(MAX_RETRIES): #Add retry loop
                try:
                    response =  await chat_model.ainvoke(messages)
                    for link in task["produces"]:
                        link = Link.model_validate(link)
                        val = clean_json(response.content)
                        if val == "":
                            raise ValueError(f"Badly formatted JSON string: {val}")
                        print(val)
                        link.set_value(json.loads(val)[link.link_name])
                    return response.content
                except (ValidationError, json.JSONDecodeError, ValueError) as e:
                    print(f"Attempt {attempt + 1} failed: {e}")
                    if attempt == MAX_RETRIES - 1:
                        return f"Error in tool B use after {MAX_RETRIES} attempts."
        elif selected_tool == 'A' or selected_tool == 'C':
            class InputType(Enum):
                TEXT = "text"
                FILE = "file"

            class State(Enum):
                INITIALIZING = auto()
                READY = auto()
                PROCESSING = auto()
                WAITING_FOR_INPUT = auto()
                ERROR = auto()
                TERMINATED = auto()

            @dataclass
            class ConversationContext:
                history: List[Dict[str, str]]
                current_prompt: str
                data_input_type: InputType
                input_source: Optional[str] = None
                max_history: int = 5
                
                def add_interaction(self, assistant_response: str, human_input: str):
                    self.history.append({
                        'assistant': assistant_response,
                        'human': human_input
                    })
                    # Keep only the last N turns
                    self.history = self.history[-self.max_history:]

                def format_history(self) -> str:
                    return "\n\n".join([
                        f"Assistant: {turn['assistant']}\nHuman: {turn['human']}"
                        for turn in self.history
                    ])

            class ScrapybaraStateMachine:
                def __init__(self, api_key: str):
                    self.client = Scrapybara(api_key=api_key)
                    self.instance = None
                    self.state = State.INITIALIZING
                    self.context: Optional[ConversationContext] = None
                    self.error_message: Optional[str] = None
                
                def initialize(self, data_input_type: InputType, input_source: Optional[str] = None) -> bool:
                    try:
                        # Try to get existing instance or create new one
                        # try:
                        #     self.instance = self.client.get_instances()[0]
                        # except:
                        #     self.instance = self.client.start_ubuntu(timeout_hours=1)
                        self.instance = self.client.start_ubuntu(timeout_hours=1)
                        
                        # Initialize conversation context
                        self.context = ConversationContext(
                            history=[],
                            current_prompt="",
                            data_input_type=data_input_type,
                            input_source=input_source
                        )
                        self.model = Anthropic()
                        
                        self.state = State.READY

                        webbrowser.open_new_tab(self.instance.get_stream_url().stream_url)
                        return True
                    except Exception as e:
                        self.error_message = str(e)
                        self.state = State.ERROR
                        return False

                def process_input(self, input_data: str) -> bool:
                    if self.state not in [State.READY, State.WAITING_FOR_INPUT]:
                        return False
                    
                    try:
                        self.state = State.PROCESSING
                        
                        # Handle different input types
                        if self.context.data_input_type == InputType.FILE and self.context.input_source:
                            with open(self.context.input_source, 'r') as f:
                                file_content = f.read()
                                self.instance.file.upload(
                                    path=f"~/{os.path.basename(self.context.input_source)}.txt",
                                    content=file_content
                                )
                        else:
                            self.context.current_prompt = input_data
                        
                        # Create full prompt with history
                        full_prompt = f"{self.context.format_history()}\n\nCurrent request: {self.context.current_prompt}"
                        
                        # Execute Scrapybara action
                        response = self.client.act(
                            model=self.model,
                            tools=[
                                BashTool(self.instance),
                                ComputerTool(self.instance),
                                EditTool(self.instance),
                            ],
                            system=UBUNTU_SYSTEM_PROMPT,
                            prompt=full_prompt,
                            on_step=lambda step: print(step.text),
                        )
                        
                        # Update conversation history
                        self.context.add_interaction(str(response), input_data)
                        
                        self.state = State.WAITING_FOR_INPUT
                        return True
                        
                    except Exception as e:
                        self.error_message = str(e)
                        self.state = State.ERROR
                        return False
                
                def terminate(self):
                    if self.instance:
                        try:

                            self.instance.stop()
                            self.state = State.TERMINATED
                        except Exception as e:
                            self.error_message = str(e)
                            self.state = State.ERROR

            # # Example usage
            # machine = ScrapybaraStateMachine(api_key="scrapy-ba5a584d-71d5-4688-92bc-347c96a6e638")
                
            # # Initialize with file input
            # input_file = Path(__file__).parent / 'input.txt'
            # if not machine.initialize(InputType.FILE, str(input_file)):
            #     print(f"Initialization failed: {machine.error_message}")
            #     return
            
            # try:
            #     # Main interaction loop
            #     while machine.state != State.TERMINATED:
            #         if machine.state == State.ERROR:
            #             print(f"Error occurred: {machine.error_message}")
            #             break
                        
            #         if machine.state in [State.READY, State.WAITING_FOR_INPUT]:
            #             print("\n[Enter your question or 'q' to quit]")
            #             user_input = input("> ")
                        
            #             if user_input.lower() == 'q':
            #                 break
                            
            #             if not machine.process_input(user_input):
            #                 print(f"Processing failed: {machine.error_message}")
            #                 break
            
            # finally:
            #     machine.terminate()
            machine = ScrapybaraStateMachine(api_key=SCRAP_API_KEY)
            if not machine.initialize(InputType.TEXT):
                print(f"Initialization failed: {machine.error_message}")
                return
            try:
                # Main interaction loop
                while machine.state != State.TERMINATED:
                    if machine.state == State.ERROR:
                        print(f"Error occurred: {machine.error_message}")
                        break
                    
                    if machine.state in [State.READY]:
                        # Use planning model to generate llm prompt for Scrapybara and pass it to scrapybara in process_input
                        prompt = await a_generate_llm_prompt(task_description, inputs, output_schema = {link["link_name"]: link["data_type"] for link in task["produces"]})
                        if not machine.process_input(prompt):
                            print(f"Processing failed: {machine.error_message}")
                            break
                    elif machine.state in [State.WAITING_FOR_INPUT]:
                        json_out = clean_json(machine.context.history[-1]['assistant'])
                        print(json_out)
                        if json_out != "":
                            for link in task["produces"]:
                                link = Link.model_validate(link)
                                link.set_value(json.loads(json_out)[link.link_name])
                            break
                        else:
                            print("\n[Enter your answer/instruction or 'q' to quit]")
                            user_input = input("> ")
                            
                            if user_input.lower() == 'q':
                                break
                                
                            if not machine.process_input(user_input):
                                print(f"Processing failed: {machine.error_message}")
                                break
            
            finally:
                machine.terminate()
            
            
            return machine.context.history[-1]['assistant']


                
            # def execute_scrapybara(task: Task, input_content: Dict):
            #     """
            #     :param task: Task
            #     :param input_content: Dict
            #     :return: Dict
            #     """
            #     machine = ScrapybaraStateMachine(api_key="scrapy-ba5a584d-71d5-4688-92bc-347c96a6e638")
                
            #     # Initialize with file input
            #     input_file = Path(__file__).parent / 'input.txt'
            #     if not machine.initialize(InputType.TEXT, str(input_file)):
            #         print(f"Initialization failed: {machine.error_message}")
            #         return
                
            #     try:
            #         # Main interaction loop
            #         while machine.state != State.TERMINATED:
            #             if machine.state == State.ERROR:
            #                 print(f"Error occurred: {machine.error_message}")
            #                 break
                            
            #             if machine.state in [State.READY, State.WAITING_FOR_INPUT]:
            #                 print("\n[Enter your question or 'q' to quit]")
            #                 user_input = input("> ")
                            
            #                 if user_input.lower() == 'q':
            #                     break
                                
            #                 if not machine.process_input(user_input):
            #                     print(f"Processing failed: {machine.error_message}")
            #                     break
                
            #     finally:
            #         machine.terminate()
            #     return {"output": input_content["code"]}
        else:
            return "Invalid tool selection"
    except Exception as e:
        return f"General execution error: {e}"

