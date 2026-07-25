# queue_manager.py

import asyncio

class QueueManager:
    def __init__(self):
        self.queues = {}
        self.loops = {}

manager = QueueManager()