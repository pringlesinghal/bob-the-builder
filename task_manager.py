# task_manager.py
from config import MAX_TASKS

class TaskManager:
    def __init__(self, max_tasks=MAX_TASKS):
        self.tasks = []
        self.max_tasks = max_tasks

    def add_task(self, task):
        if len(self.tasks) < self.max_tasks:
            self.tasks.append(task)
            return True
        return False

    def get_task_count(self):
        return len(self.tasks)
