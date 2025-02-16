from scrapybara import Scrapybara
from scrapybara.tools import BashTool, ComputerTool, EditTool
from scrapybara.anthropic import Anthropic
from scrapybara.prompts import UBUNTU_SYSTEM_PROMPT
from enum import Enum, auto
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
import json
from pathlib import Path

class InputType(Enum):
    TEXT = "text"
    FILE = "file"
    URL = "url"

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
            try:
                self.instance = self.client.get_instances()[0]
            except:
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
                    self.context.current_prompt = f"Content from file {self.context.input_source}:\n\n{file_content}\n\nUser request: {input_data}"
            else:
                self.context.current_prompt = input_data
            
            # Create full prompt with history
            full_prompt = f"{self.context.format_history()}\n\nCurrent request: {self.context.current_prompt}"
            
            # Execute Scrapybara action
            response = self.client.act(
                model=self.model(),
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

def main():
    # Example usage
    machine = ScrapybaraStateMachine(api_key="scrapy-ba5a584d-71d5-4688-92bc-347c96a6e638")
    
    # Initialize with file input
    input_file = Path(__file__).parent / 'input.txt'
    if not machine.initialize(InputType.FILE, str(input_file)):
        print(f"Initialization failed: {machine.error_message}")
        return
    
    try:
        # Main interaction loop
        while machine.state != State.TERMINATED:
            if machine.state == State.ERROR:
                print(f"Error occurred: {machine.error_message}")
                break
                
            if machine.state in [State.READY, State.WAITING_FOR_INPUT]:
                print("\n[Enter your question or 'q' to quit]")
                user_input = input("> ")
                
                if user_input.lower() == 'q':
                    break
                    
                if not machine.process_input(user_input):
                    print(f"Processing failed: {machine.error_message}")
                    break
    
    finally:
        machine.terminate()

def execute_node(task: Task, input_content: List[str]):
    """
    node_name = Perplexity, code, or Scrapybara
    :param task: Task
    :param input_content: List[str]
    :return: Dict
    """
    if task.tool == Tool.PERPLEXITY:
        return execute_perplexity(task, input_content)
    elif task.tool == Tool.CODE:
        return execute_code(task, input_content)
    elif task.tool == Tool.SCRAPYBARA:
        return execute_scrapybara(task, input_content)
    
def execute_code(task: Task, input_content: Dict):
    """
    :param task: Task
    :param input_content: Dict
    :return: Dict
    """
    assert len(input_content) == 1
    exec(input_content["code"])
    task.completed = True
    return {"output": input_content["code"]}

def execute_perplexity(task: Task, input_content: Dict):
    """
    :param task: Task
    :param input_content: Dict
    :return: Dict
    """
    prompt = input_content["prompt"] + "\n\nInputs:\n" + str(input_content["inputs"]) + "\n\nOutputs:\n" + str()
    
    response = client.chat.completions.create(
        model="sonar-pro",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": prompt}
        ],
        max_tokens=2000
    )
    task.completed = True
    return {"output": response.choices[0].message.content}

def execute_scrapybara(task: Task, input_content: Dict):
    """
    :param task: Task
    :param input_content: Dict
    :return: Dict
    """
    machine = ScrapybaraStateMachine(api_key="scrapy-ba5a584d-71d5-4688-92bc-347c96a6e638")
    
    # Initialize with file input
    input_file = Path(__file__).parent / 'input.txt'
    if not machine.initialize(InputType.FILE, str(input_file)):
        print(f"Initialization failed: {machine.error_message}")
        return
    
    try:
        # Main interaction loop
        while machine.state != State.TERMINATED:
            if machine.state == State.ERROR:
                print(f"Error occurred: {machine.error_message}")
                break
                
            if machine.state in [State.READY, State.WAITING_FOR_INPUT]:
                print("\n[Enter your question or 'q' to quit]")
                user_input = input("> ")
                
                if user_input.lower() == 'q':
                    break
                    
                if not machine.process_input(user_input):
                    print(f"Processing failed: {machine.error_message}")
                    break
    
    finally:
        machine.terminate()
    return {"output": input_content["code"]}

if __name__ == "__main__":
    main()
