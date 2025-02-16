from langchain.evaluation import load_evaluator
from config import chat_model #Import chat model
import json

def evaluate_task_decomposition(task):
    evaluator = load_evaluator("criteria",
    criteria={
    "completeness": "Does the decomposition cover all aspects of the task?",
    "actionability": "Are the subtasks concrete and actionable?",
    "independence": "Are the subtasks sufficiently independent?"
    },
    llm=chat_model # Use the ChatPerplexity model for evaluation
    )

    evaluation = evaluator.evaluate_strings(
        prediction=json.dumps(task, indent=2),
        input=task['task_description']
    )

    return evaluation