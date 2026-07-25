# Backend API and Agent Documentation

This backend powers a multi-agent chatroom application built with FastAPI, MongoDB, and a LangGraph-based agent workflow. It handles authentication, group and character management, conversation storage, session memory, and streamed multi-agent responses.

## 1. Project Overview

The backend is organized into:

- routes/: FastAPI routers for API endpoints
- models/: Pydantic and MongoDB-friendly data models
- repos/: Repository helpers for data access
- db/: Database connection utilities
- agent/: LangGraph-based agent workflow and nodes

The main entry point is:

- backend/main.py

## 2. Main API Modules

### Authentication Routes

Location: routes/auth_router.py

Endpoints:

- POST /auth/signup
  - Creates a new user account
  - Hashes the password
  - Returns a JWT access token
- POST /auth/login
  - Authenticates a user with email and password
  - Returns a JWT and basic user data
- GET /auth/me
  - Returns the currently authenticated user profile
- POST /auth/logout
  - Logs out the current user (currently a placeholder response)

### Group Routes

Location: routes/group_router.py

Endpoints:

- POST /group/
  - Creates a new chat group
- GET /group/{group_id}
  - Fetches a single group by ID
- GET /group/
  - Lists all groups
- GET /group/groups_by_user
  - Lists groups created by the authenticated user
- POST /group/charMap/{grp_id}
  - Builds a character map for the group, including recent context, similar past messages, user preferences, and session memory
- POST /group/preferences
  - Stores user preferences for a specific group

### Character Routes

Location: routes/chracter_router.py

Endpoints:

- POST /character/
  - Creates a character inside a group
  - Associates the character with the group
- GET /character/{char_id}
  - Fetches a single character by ID
- DELETE /character/{char_id}
  - Deletes a character if the authenticated user owns it

### Conversation Routes

Location: routes/conversation_router.py

Endpoints:

- POST /conv/chat/stream
  - Streams a multi-agent chat response in real time
  - Uses the LangGraph agent pipeline
- POST /conv/createConv
  - Creates a new conversation record and stores the initial character responses
- POST /conv/addMessage
  - Adds a follow-up message to an existing conversation
- POST /conv/summary
  - Updates a conversation summary and embedding
- POST /conv/encode
  - Encodes conversation summaries for vector search support

### Session Routes

Location: routes/session_router.py

Endpoints:

- POST /session/create
  - Creates a new chat session for a group
- GET /session/{session_id}
  - Retrieves a session with memory and conversation IDs
- GET /session/list/{grp_id}
  - Lists all sessions for the authenticated user in a group
- POST /session/memory
  - Updates the session memory summary
- POST /session/addConv
  - Adds a conversation ID to a session
- DELETE /session/{session_id}
  - Deletes a session

## 3. Agent Workflow

The agent logic lives in backend/agent/.

### Graph Overview

The graph is defined in:

- backend/agent/graph/builder.py

The workflow executes in this order:

1. input_node
   - Fetches group character data
   - Collects recent conversation context
   - Retrieves similar past messages and user preferences
   - Prepares the state for the agent

2. orchestrator_node
   - Chooses the most suitable character to respond
   - Uses the group context, character traits, and prior conversation history

3. character_node
   - Generates the selected character's in-character response

4. review_node
   - Evaluates whether the user query has been fully addressed
   - Suggests additional characters if needed

5. api_node
   - Sends the generated response to the backend conversation APIs
   - Stores the answer in the conversation/message database

6. memory_node
   - Updates the user preference or memory summary if the conversation reveals something new

7. background_node
   - Finalizes the agent pipeline after approval

## 4. Key Agent Files

- backend/agent/graph/builder.py
  - Builds and compiles the LangGraph workflow
- backend/agent/nodes/input_node.py
  - Gathers context from the backend before the agent runs
- backend/agent/nodes/orchestrator_node.py
  - Selects the responding character
- backend/agent/nodes/character_node.py
  - Produces the character response
- backend/agent/nodes/review_node.py
  - Reviews and decides whether the response is sufficient
- backend/agent/nodes/api_node.py
  - Saves the result into the database
- backend/agent/nodes/memory_node.py
  - Maintains user memory/preferences for future chats

## 5. How the Backend Runs

Start the backend with:

```bash
python backend/main.py
```

Or run with Uvicorn:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

## 6. Notes

- Authentication uses JWT-based access tokens.
- The backend expects MongoDB connectivity through the database configuration in db/dbConnection.py.
- The conversation system supports both direct conversation storage and streaming responses.
- The agent uses LLM-based reasoning for character selection, response generation, and review.
