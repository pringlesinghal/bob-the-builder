# main.py
import asyncio
import os
from schemas import Task
from config import LANGCHAIN_TRACING_V2, chat_model
from task_manager import TaskManager
from orchestration import a_generate_task_tree
from tree_utils import print_task_tree
from evaluation import evaluate_task_decomposition
from langchain_core.tracers.context import tracing_v2_enabled
import json
from flask import Flask, jsonify
from flask_cors import CORS
from flask_socketio import SocketIO, emit

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Global variables to store the latest task tree
root_task = None
tasks_by_depth = None

@socketio.on('generate_tree')
def handle_generate_tree(message):
    global root_task, tasks_by_depth
    prompt = message['prompt']
    print(f"Received prompt: {prompt}")
    
    async def generate():
        global root_task, tasks_by_depth
        task_manager = TaskManager()
        root_task, tasks_by_depth = await a_generate_task_tree(prompt, Task.model_json_schema(), task_manager)
        return root_task

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    root_task = loop.run_until_complete(generate())
    
    if root_task:
        emit('new_task_tree', root_task.dict())
    else:
        emit('generation_failed')

if __name__ == '__main__':
    socketio.run(app, debug=True, port=5000)
