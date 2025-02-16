# config.py
import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatPerplexity
from langchain_google_genai import ChatGoogleGenerativeAI
from langsmith import Client

from langchain_openai import OpenAI

load_dotenv()

# API Keys and Environment Variables
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"  # Default False if not set
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# LangSmith Client
client = Client(api_key=LANGCHAIN_API_KEY)

# Perplexity Chat Model
perplexity_model = ChatPerplexity(
    model="sonar-pro",
    temperature=0,
    pplx_api_key=PERPLEXITY_API_KEY,
    model_kwargs={"seed": 42},  # Set seed for reproducibility
)

# Gemini Chat Model
gemini_model = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-thinking-exp",
    google_api_key=GOOGLE_API_KEY
)

from langchain_core.language_models.chat_models import BaseChatModel
from langchain_core.messages import BaseMessage
from langchain_core.runnables import RunnableConfig
from typing import Any, Optional

from langchain_core.messages import AIMessage
from langchain_openai import ChatOpenAI

class CustomChatOpenAI(ChatOpenAI):
    async def ainvoke(self, input: Any, config: Optional[RunnableConfig] = None, **kwargs: Any) -> BaseMessage:
        # Call the parent class's ainvoke method
        response = await super().ainvoke(input, config, **kwargs)
        
        # Convert the string response to an AIMessage
        if isinstance(response, str):
            return AIMessage(content=response)
        elif isinstance(response, BaseMessage):
            return response
        else:
            raise ValueError(f"Unexpected response type: {type(response)}")

openai_model = CustomChatOpenAI(api_key=OPENAI_API_KEY)

chat_model = perplexity_model

# Model configurations
perplexity_config = {
    "max_tokens": 4096,
    "temperature": 0,
    "top_p": 1.0
}

gemini_config = {
    "max_tokens": 4096,
    "temperature": 0.7,
    "top_p": 0.9
}

# Configuration parameters (can be overwritten by command line arguments or other environment variables)
MAX_TASKS = 20
SIMILARITY_THRESHOLD = 0.8
MAX_RETRIES = 5
MAX_DEPTH = 5
MAX_SUBTASKS = 5


import re
import json
import regex
def clean_json(task_json_string: str) -> str:
    json_content = re.search(r'```json\n(.*?)\n```', task_json_string, re.DOTALL)
    if json_content:
        return json_content.group(1)
    else:
        pattern = r'\{(?:[^{}]|(?R))*\}'
        match = regex.search(pattern, task_json_string)
        if match:
            return match.group()
        else:
            return ""