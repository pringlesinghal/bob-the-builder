# config.py
import os
from dotenv import load_dotenv
from langchain_community.chat_models import ChatPerplexity
from langsmith import Client

load_dotenv()

# Environment Variables
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
LANGCHAIN_TRACING_V2 = os.getenv("LANGCHAIN_TRACING_V2", "false").lower() == "true"  # Default False if not set
LANGCHAIN_ENDPOINT = os.getenv("LANGCHAIN_ENDPOINT")
LANGCHAIN_API_KEY = os.getenv("LANGCHAIN_API_KEY")

# LangSmith Client
client = Client(api_key=LANGCHAIN_API_KEY)

# Perplexity Chat Model
chat_model = ChatPerplexity(
    model="sonar-pro",
    temperature=0,
    pplx_api_key=PERPLEXITY_API_KEY,
    model_kwargs={"seed": 42},  # Set seed for reproducibility
)

# Configuration parameters (can be overwritten by command line arguments or other environment variables)
MAX_TASKS = 20
SIMILARITY_THRESHOLD = 0.8
MAX_RETRIES = 5
MAX_DEPTH = 5
MAX_SUBTASKS = 5
