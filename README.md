# Multi-Agent Chatroom

In this project users create groups of custom characters and have natural, multi-character conversations. The application combines a React interface, a FastAPI/MongoDB backend, and a LangGraph workflow that selects the most relevant character, generates an in-character reply, reviews the result, and preserves conversation context.

> **Project status:** The repository contains an actively implemented backend and frontend, along with `implementation.md`, which documents planned/scalable architecture such as vector search, additional services, and expanded testing. Some documented features may require further integration before production use.

## Features

### AI-powered multi-agent conversations

- Create a group with its own name and description.
- Add characters with descriptions, traits, and personalities.
- Automatically select the best character for each user query.
- Prioritize a character when the user directly addresses them.
- Generate concise responses that stay in the selected character's voice.
- Use recent dialogue, group context, session memory, user preferences, and relevant past messages when available.
- Review generated replies and loop back to the orchestrator when the query needs another character's perspective.
- Stream chat responses through the backend conversation API.

### Conversation and memory management

- Create and manage chat sessions for groups.
- Store conversations and messages in MongoDB.
- Keep session memory and conversation summaries for future context.
- Encode summaries and retrieve semantically relevant past messages where the vector-search functionality is configured.
- Load previous session messages from the frontend sidebar.

### User and content management

- Sign up, log in, retrieve the current profile, and log out through JWT-based authentication.
- Create, view, update, and delete groups.
- Create, view, and delete characters, with ownership checks in the API.
- Save group-specific user preferences.
- Use responsive layouts with desktop and mobile sidebar navigation.

## How the agent workflow works

The LangGraph workflow in `backend/agent/graph/builder.py` follows this flow:

```text
Input/context loading
        ↓
Character orchestration
        ↓
In-character response generation
        ↓
Response review
        ↓
Conversation API persistence
        ↓
Background finalization
```

The workflow can route back to the orchestrator when the review step determines that the response needs improvement or that another character should respond. Context loading can include group characters, recent conversations, session memory, user preferences, and vector-search results.

## Tech stack

### Frontend

- React 18
- TypeScript
- Vite
- Tailwind CSS
- Zustand for client state
- Radix UI primitives and Sonner notifications

### Backend

- Python
- FastAPI and Uvicorn
- MongoDB with PyMongo
- LangGraph and LangChain
- Groq LLM integration for the multi-agent workflow
- Pydantic models and JWT authentication
- Sentence Transformers and vector-related dependencies for semantic retrieval

The repository also includes a root-level `main.py` that uses Google Gemini through `langchain-google-genai` as an earlier/alternate `/chat` implementation. The primary structured backend is under `backend/` and uses the Groq-based agent workflow.

## Repository structure

```text
Multi-Agent-chatroom/
├── backend/
│   ├── agent/
│   │   ├── graph/       LangGraph state, graph builder, and workflow setup
│   │   ├── llm/         Groq client and LLM utilities
│   │   └── nodes/       Input, orchestration, character, review, API, memory, and background nodes
│   ├── db/              MongoDB connection and database helpers
│   ├── models/          User, group, character, session, conversation, and message models
│   ├── repos/           Repository/data-access helpers
│   ├── routes/          Authentication, group, character, conversation, and session APIs
│   ├── main.py          FastAPI application entry point
│   ├── streamlit_ui.py  Streamlit-oriented backend UI module
│   └── .env.example     Backend configuration template
├── frontend/
│   ├── src/
│   │   ├── components/ Chat view, sidebar, management modal, and reusable UI components
│   │   ├── pages/      Authentication page
│   │   ├── lib/        Client store and shared TypeScript types
│   │   └── App.tsx     Main authenticated application shell
│   └── package.json
├── main.py              Alternate/simple FastAPI chat workflow
├── requirements.txt     Root Python dependencies
└── implementation.md    Detailed architecture and future implementation plan
```

## Prerequisites

- Python 3.10+
- Node.js 18+
- A running MongoDB instance
- A Groq API key for the primary backend agent workflow
- Git

## Setup

### 1. Clone the repository

```bash
git clone https://github.com/GAAKASH2003/Multi-Agent-chatroom.git
cd Multi-Agent-chatroom
```

### 2. Configure the backend

Create the backend environment file from the supplied template:

```bash
cp backend/.env.example backend/.env
```

Set at least these values in `backend/.env`:

```dotenv
MONGODB_URL=mongodb://localhost:27017
MONGODB_DB_NAME=multi_agent_chatroom
JWT_SECRET_KEY=replace-with-a-long-random-secret
GROQ_API_KEY=your-groq-api-key
```

If you use a vector provider other than MongoDB, configure its provider-specific variables as well. Do not commit `.env` or real API keys.

### 3. Install Python dependencies

For the implemented backend, install the backend dependency set:

```bash
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r backend/requirements.txt
```

The smaller root `requirements.txt` is also available for the alternate root-level workflow.

### 4. Install frontend dependencies

```bash
cd frontend
npm install
cd ..
```

## Running the application

Start MongoDB first, then run the API and frontend in separate terminals.

### Backend API

From the repository root:

```bash
uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The API is available at `http://localhost:8000`. A basic health response is available at `/`.

The backend CORS configuration allows the Vite development origins `http://localhost:5173` and `http://127.0.0.1:5173`.

### Frontend

```bash
cd frontend
npm run dev
```

Open the Vite URL shown in the terminal, normally `http://localhost:5173`.

### Alternate root workflow

The root `main.py` exposes a separate `POST /chat` endpoint and expects `GOOGLE_API_KEY` in the root environment. To run it:

```bash
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```

A request to the alternate endpoint has this general shape:

```json
{
  "user_query": "Who should lead the mission?",
  "group_name": "Explorers",
  "group_description": "A team of adventurous specialists.",
  "characters": [
    {
      "name": "Avery",
      "description": "A cautious strategist.",
      "traits": ["analytical", "calm"]
    }
  ],
  "summary": ""
}
```

## API overview

The implemented backend exposes routers for:

| Area | Example endpoints | Purpose |
|---|---|---|
| Authentication | `POST /auth/signup`, `POST /auth/login`, `GET /auth/me` | Account and JWT authentication |
| Groups | `POST /group/`, `GET /group/`, `GET /group/{group_id}` | Group creation and retrieval |
| Characters | `POST /character/`, `GET /character/{char_id}`, `DELETE /character/{char_id}` | Character management |
| Conversations | `POST /conv/chat/stream`, `POST /conv/createConv`, `POST /conv/addMessage` | Streaming and stored chat messages |
| Sessions | `POST /session/create`, `GET /session/{session_id}`, `GET /session/list/{grp_id}` | Chat-session lifecycle and memory |

See `backend/README.md` and the route modules under `backend/routes/` for request models and the complete endpoint behavior.

## Development commands

```bash
# Frontend type-check
cd frontend
npm run typecheck

# Frontend lint
npm run lint

# Frontend production build
npm run build

# Return to the repository root
cd ..
```

