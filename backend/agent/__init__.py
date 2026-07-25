import os
import sys

# Ensure the agent directory is in the Python system path so that
# its subpackages (graph, nodes, llm) can be imported directly
# when agent is imported from external entry points (like backend/main.py).
agent_dir = os.path.dirname(os.path.abspath(__file__))
if agent_dir not in sys.path:
    sys.path.insert(0, agent_dir)
