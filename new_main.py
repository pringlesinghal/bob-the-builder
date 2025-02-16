from flask import Flask, request, jsonify
from flask_cors import CORS
import asyncio #Import asyncio
import logging
from schemas import Task  # Import Task
from task_manager import TaskManager  # Import TaskManager
from orchestration import a_generate_task_tree  # Import a_generate_task_tree

# Configure logging (optional but recommended)
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

app = Flask(__name__)

# Configure CORS (Cross-Origin Resource Sharing)
# IMPORTANT: Adjust 'origins' for your actual deployment environment!
cors = CORS(
    app,
    resources={
        r"/*": {  # Apply to all routes
            "origins": ["http://localhost:3000"],  # Your React app's origin (DEVELOPMENT)
            "methods": ["GET", "POST", "OPTIONS"],  # Allowed HTTP methods
            "allow_headers": ["Content-Type"],  # Allowed headers in requests
            "supports_credentials": True,  # Allow sending cookies/credentials
        }
    },
    supports_credentials=True,  # Enable CORS for the entire app
)

# New Flask route to handle task tree generation
@app.route("/api/generate_task_tree", methods=["POST"])
def generate_task_tree_route():
    try:
        prompt = request.json.get("prompt")  # Get the prompt from the request body
        if not prompt:
            return jsonify({"error": "Prompt is required"}), 400

        # --- Your task tree generation logic here ---
        # Call a_generate_task_tree and return the root_task
        task_manager = TaskManager()

        async def generate(): # Define an async function to run the async task
            root_task, tasks_by_depth = await a_generate_task_tree(prompt, Task.model_json_schema(), task_manager)
            return root_task

        loop = asyncio.new_event_loop() #Create a new event loop
        asyncio.set_event_loop(loop) #Set the loop as the current loop
        root_task = loop.run_until_complete(generate()) # Run the async function until it is complete

        if root_task:
            return jsonify(root_task)  # Serialize and return root_task as JSON
        else:
            return jsonify({"error": "Task generation failed"}), 500

    except Exception as e:
        logger.exception("Error generating task tree")
        return jsonify({"error": str(e)}), 500


if __name__ == '__main__':
    app.run(debug=True, port=5000)


