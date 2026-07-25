# Multi-Agent Chatroom – Scalable Implementation Plan

## Project Overview

**Vision**: A platform where users create groups with fictional/real characters and interact with them through intelligent multi-character conversations powered by LLMs.

**Tech Stack**:

- Backend: Python (FastAPI)
- Frontend: React + TypeScript
- Database: MongoDB (conversations, metadata) + Vector DB (semantic search)
- Orchestration: LangGraph (state management, multi-agent coordination)
- LLM Provider: Groq API (open-source LLMs)

---

## Architecture Principles

1. **Separation of Concerns**: Data layer, service layer, API layer, frontend—each with single responsibility
2. **Scalability**: Stateless services, async operations, horizontal scaling readiness
3. **Modularity**: Pluggable LLM providers, abstracted data access, component-based UI
4. **Testability**: Clear interfaces, dependency injection, mockable components
5. **Domain-Driven Design**: Groups, Characters, Conversations, Users as core domains

---

## Layered Architecture

```
React Frontend (UI Layer)
        ↓
    FastAPI Routes (API Layer)
        ↓
    Service Layer (Business Logic)
        ↓
    Repository Pattern (Data Access Abstraction)
        ↓
MongoDB (Conversations, Metadata) + Vector DB (Embeddings)
        ↓
External Services (Groq LLM, Embedding API)
```

---

# 6-Phase Implementation Plan

## Phase 1: Domain & Data Layer (Foundation)

**Goal**: Establish database schemas, domain models, and data abstraction layer.

### 1.1 Define MongoDB Collections & Schemas

```
users
├── _id: ObjectId
├── username: string (unique)
├── email: string (unique)
├── password_hash: string
├── created_at: datetime
└── updated_at: datetime

groups
├── _id: ObjectId
├── user_id: ObjectId (foreign key)
├── name: string
├── description: string
├── created_at: datetime
└── updated_at: datetime

characters
├── _id: ObjectId
├── group_id: ObjectId (foreign key)
├── name: string
├── description: string (personality, background)
├── traits: [string] (e.g., ["determined", "sarcastic"])
├── system_prompt: string (custom prompt for this character)
├── created_at: datetime
└── updated_at: datetime

conversations
├── _id: ObjectId
├── user_id: ObjectId (foreign key)
├── group_id: ObjectId (foreign key)
├── messages: [message_object]
│   ├── id: string (uuid)
│   ├── speaker: string (username or "user")
│   ├── content: string
│   ├── timestamp: datetime
│   └── embedding_id: string (reference to vector DB)
├── created_at: datetime
├── updated_at: datetime
└── summary: string (optional, for long conversations)

message_vectors (in Vector DB)
├── id: string (uuid, same as message.embedding_id)
├── conversation_id: ObjectId
├── message_id: string
├── speaker: string
├── content: string
├── embedding: [float] (vector, 384-1536 dimensions)
├── timestamp: datetime
└── metadata: {group_id, user_id}
```

**Indices**:

- `groups.user_id`
- `characters.group_id`
- `conversations.user_id`
- `conversations.group_id`
- `conversations.updated_at` (for sorting recent conversations)

### 1.2 Create Pydantic Domain Models

File: `src/models/domain.py`

```python
from pydantic import BaseModel, Field, validator
from datetime import datetime
from typing import List, Optional
from bson import ObjectId

class User(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    username: str
    email: str
    password_hash: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    class Config:
        populate_by_name = True

class Character(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    group_id: ObjectId
    name: str
    description: str
    traits: List[str]
    system_prompt: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Group(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    user_id: ObjectId
    name: str
    description: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

class Message(BaseModel):
    id: str  # UUID
    speaker: str
    content: str
    timestamp: datetime
    embedding_id: Optional[str] = None

class Conversation(BaseModel):
    id: Optional[ObjectId] = Field(None, alias="_id")
    user_id: ObjectId
    group_id: ObjectId
    messages: List[Message] = []
    summary: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)
```

### 1.3 Implement Repository Pattern

File: `src/data/repositories.py`

Abstractions:

- `UserRepository`: CRUD for users, fetch by username/email
- `GroupRepository`: CRUD for groups, list by user_id
- `CharacterRepository`: CRUD for characters, list by group_id
- `ConversationRepository`: CRUD for conversations, append messages, fetch paginated history

All repositories use async MongoDB driver (`motor`) for non-blocking I/O.

### 1.4 Setup Vector DB Integration

File: `src/data/vector_db.py`

- Connect to Vector DB (Pinecone, Weaviate, or MongoDB Atlas Vector Search)
- Implement `EmbeddingService`: converts text to vectors using Groq embeddings API
- Implement `VectorStore`: store/retrieve message embeddings with metadata
- Query methods: `search_similar(query_embedding, top_k)` for semantic search

### 1.5 Database Configuration

File: `src/config/database.py`

- MongoDB async connection with connection pooling
- Vector DB client initialization
- Health check endpoints

**Output**: Database abstraction layer ready for services to consume.

**Verification Checklist**:

- [ ] MongoDB collections created with indices
- [ ] All domain models validate correctly
- [ ] Repository operations (CRUD) tested with mocked MongoDB
- [ ] Vector DB connection established, embeddings stored successfully

---

## Phase 2: Service Layer & Orchestration (Core Logic)

**Goal**: Implement character orchestration, context management, and LLM integration.

### 2.1 LLM Provider Abstraction

File: `src/services/llm_provider.py`

```python
from abc import ABC, abstractmethod
from typing import List, Dict

class LLMProvider(ABC):
    @abstractmethod
    async def generate_response(self, system_prompt: str, user_message: str, conversation_history: List[Dict]) -> str:
        pass

    @abstractmethod
    async def create_embedding(self, text: str) -> List[float]:
        pass

class GroqLLMProvider(LLMProvider):
    def __init__(self, api_key: str):
        # Initialize Groq client
        pass

    async def generate_response(self, system_prompt: str, user_message: str, conversation_history: List[Dict]) -> str:
        # Call Groq API with error handling, retries, rate limiting
        pass

    async def create_embedding(self, text: str) -> List[float]:
        # Call Groq embeddings API
        pass
```

**Benefits**: Easy to swap Groq for local models, other APIs, or mocks in testing.

### 2.2 Context Manager Service

File: `src/services/context_manager.py`

Responsibilities:

- **Token Budget**: Calculate token count; ensure prompt + history stays within LLM limits (e.g., 4K tokens)
- **Sliding Window**: Keep last N messages (recent context)
- **Semantic Search**: Retrieve most relevant messages using vector embeddings + recency weighting
- **Context Compression**: Summarize irrelevant details using LLM; preserve critical facts

```python
class ContextManagerService:
    def __init__(self,
                 conversation_repo: ConversationRepository,
                 vector_store: VectorStore,
                 llm_provider: LLMProvider):
        self.conversation_repo = conversation_repo
        self.vector_store = vector_store
        self.llm_provider = llm_provider

    async def build_context(self,
                           conversation_id: ObjectId,
                           group_id: ObjectId,
                           token_limit: int = 4000) -> Dict[str, Any]:
        # 1. Fetch recent messages (sliding window, e.g., last 20)
        # 2. Calculate token count
        # 3. If over budget, use semantic search to retrieve top-K relevant messages
        # 4. Combine recency + relevance, compress if needed
        # 5. Return formatted context for LLM
        pass

    async def compress_context(self, messages: List[Message]) -> str:
        # Use LLM to summarize: "Key facts: X, Y, Z"
        pass
```

### 2.3 Character Orchestrator Service

File: `src/services/orchestrator.py`

- Takes user message, conversation state, group info, characters
- Uses Groq API to decide which character should respond (or multiple characters)
- Factors: character traits, description, conversation flow, balance (ensure each character gets turns)
- Returns: `{speaker_name: str, rationale: str}`

```python
class CharacterOrchestratorService:
    def __init__(self,
                 character_repo: CharacterRepository,
                 context_manager: ContextManagerService,
                 llm_provider: LLMProvider):
        pass

    async def select_speaker(self,
                            conversation: Conversation,
                            group: Group,
                            user_message: str) -> Dict[str, str]:
        # 1. Fetch all characters in group
        # 2. Build context using context_manager
        # 3. Create orchestration prompt with character descriptions + traits
        # 4. Call LLM to decide next speaker
        # 5. Return {speaker_name, rationale}
        pass
```

### 2.4 Character Response Service

File: `src/services/character_service.py`

- Generates response from selected character
- Uses character description + traits in system prompt
- Maintains consistency with character personality

```python
class CharacterResponseService:
    def __init__(self, llm_provider: LLMProvider):
        pass

    async def generate_response(self,
                               character: Character,
                               user_message: str,
                               conversation_context: Dict[str, Any]) -> str:
        # Build system prompt: character description, traits, tone
        # Call LLM with system prompt + context
        # Return generated response
        pass
```

### 2.5 Conversation Management Service

File: `src/services/conversation_service.py`

- Handles message storage (append to MongoDB + embed + store in vector DB)
- Retrieves conversation history with pagination
- Optional: implements conversation summarization for very long conversations

```python
class ConversationService:
    def __init__(self,
                 conversation_repo: ConversationRepository,
                 vector_store: VectorStore,
                 llm_provider: LLMProvider):
        pass

    async def add_message(self, conversation_id: ObjectId, message: Message) -> Message:
        # 1. Append to MongoDB
        # 2. Create embedding using llm_provider
        # 3. Store in vector DB with metadata
        # 4. Return stored message
        pass

    async def get_conversation_history(self,
                                      conversation_id: ObjectId,
                                      limit: int = 50,
                                      offset: int = 0) -> List[Message]:
        # Fetch from MongoDB with pagination
        pass
```

### 2.6 LangGraph Orchestrator Graph

File: `src/graph/orchestrator_graph.py`

Define LangGraph StateGraph for multi-turn conversations:

```python
from langgraph.graph import StateGraph, START, END
from typing import TypedDict, List

class ConversationState(TypedDict):
    conversation_id: str
    group_id: str
    user_id: str
    user_message: str
    context: Dict[str, Any]
    selected_speaker: str
    character_response: str
    messages: List[Message]

def build_orchestrator_graph(orchestrator_service,
                            character_service,
                            conversation_service):
    graph = StateGraph(ConversationState)

    # Node 1: Receive user message
    async def receive_message(state):
        # Validate message
        return state

    # Node 2: Build context
    async def build_context(state):
        context = await context_manager.build_context(state["conversation_id"])
        state["context"] = context
        return state

    # Node 3: Select speaker
    async def select_speaker(state):
        speaker = await orchestrator_service.select_speaker(...)
        state["selected_speaker"] = speaker
        return state

    # Node 4: Generate response
    async def generate_response(state):
        response = await character_service.generate_response(...)
        state["character_response"] = response
        return state

    # Node 5: Store messages
    async def store_messages(state):
        await conversation_service.add_message(user_message)
        await conversation_service.add_message(character_response)
        return state

    graph.add_node("receive_message", receive_message)
    graph.add_node("build_context", build_context)
    graph.add_node("select_speaker", select_speaker)
    graph.add_node("generate_response", generate_response)
    graph.add_node("store_messages", store_messages)

    graph.add_edge(START, "receive_message")
    graph.add_edge("receive_message", "build_context")
    graph.add_edge("build_context", "select_speaker")
    graph.add_edge("select_speaker", "generate_response")
    graph.add_edge("generate_response", "store_messages")
    graph.add_edge("store_messages", END)

    return graph.compile()
```

**Output**: Stateless, testable orchestration layer ready for API to invoke.

**Verification Checklist**:

- [ ] Orchestrator selects correct character given conversation state
- [ ] Context manager stays within token limits
- [ ] Character response maintains personality/traits (prompt injection resistant)
- [ ] LLM provider handles rate limits, retries, fallbacks gracefully
- [ ] All services testable with mocked LLM responses

---

## Phase 3: API Layer & Endpoints

**Goal**: Expose REST endpoints, implement authentication, integrate services.

### 3.1 Authentication & Authorization

File: `src/api/middleware/auth.py`

- JWT token generation on login
- Middleware to validate tokens on protected routes
- User context injection into request state

### 3.2 REST Endpoints

File: `src/api/routes/`

#### Auth Endpoints

- `POST /api/auth/register` - Create user account
- `POST /api/auth/login` - Generate JWT token

#### Group Endpoints

- `POST /api/groups` - Create group (auth required)
- `GET /api/groups` - List user's groups (auth required)
- `GET /api/groups/{group_id}` - Get group + characters (auth required, ownership check)
- `PUT /api/groups/{group_id}` - Update group (auth required, ownership check)
- `DELETE /api/groups/{group_id}` - Delete group (auth required, ownership check)

#### Character Endpoints

- `POST /api/groups/{group_id}/characters` - Add character (auth required, group ownership check)
- `GET /api/groups/{group_id}/characters` - List characters in group
- `PUT /api/groups/{group_id}/characters/{character_id}` - Update character (auth, ownership)
- `DELETE /api/groups/{group_id}/characters/{character_id}` - Delete character (auth, ownership)

#### Conversation Endpoints

- `POST /api/groups/{group_id}/conversations` - Start new conversation (auth required)
- `GET /api/conversations/{conversation_id}` - Get conversation metadata (auth, ownership)
- `POST /api/conversations/{conversation_id}/messages` - Send message, get response (auth, ownership)
  - Request: `{content: string}`
  - Response: `{user_message: Message, character_response: Message, speaker: string}`
- `GET /api/conversations/{conversation_id}/messages` - Get paginated messages (auth, ownership)
  - Query params: `?limit=50&offset=0`

### 3.3 Request/Response Models

File: `src/api/schemas.py`

Separate from domain models:

- `UserRegisterRequest`, `UserLoginResponse`
- `GroupCreateRequest`, `GroupResponse`
- `CharacterCreateRequest`, `CharacterResponse`
- `MessageSendRequest`, `MessageSendResponse`

All with validation (required fields, string length limits, etc.).

### 3.4 Error Handling & Logging

File: `src/api/exceptions.py`

Custom exceptions:

- `UnauthorizedException` (401)
- `ForbiddenException` (403, ownership check failed)
- `NotFoundException` (404)
- `ValidationException` (400)
- `InternalServerException` (500)

Global exception handlers return standardized error responses:

```json
{
  "error": "Not Found",
  "message": "Group not found",
  "status_code": 404
}
```

Structured logging: every request logged with user_id, endpoint, status, duration.

### 3.5 Main FastAPI App

File: `main.py` (refactor)

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.api.routes import auth, groups, conversations
from src.api.middleware import auth_middleware
from src.config.database import connect_to_db, disconnect_from_db

app = FastAPI(title="Multi-Agent Chatroom", version="1.0.0")

# CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Custom auth middleware
app.add_middleware(auth_middleware.AuthMiddleware)

# Startup/shutdown hooks
@app.on_event("startup")
async def startup():
    await connect_to_db()

@app.on_event("shutdown")
async def shutdown():
    await disconnect_from_db()

# Include routes
app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
app.include_router(groups.router, prefix="/api/groups", tags=["groups"])
app.include_router(conversations.router, prefix="/api/conversations", tags=["conversations"])

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

**Output**: Fully functional REST API with all core endpoints.

**Verification Checklist**:

- [ ] All endpoints return correct status codes
- [ ] Auth middleware rejects invalid/expired tokens
- [ ] Ownership checks prevent users accessing other users' data
- [ ] Error messages are informative (never leak sensitive data)
- [ ] Logging captures all requests with timing + user_id
- [ ] CORS configured for React frontend

---

## Phase 4: Frontend Integration (React)

**Goal**: Build UI for group creation, character management, chat interface.

### 4.1 Project Setup

```bash
npm create vite@latest frontend -- --template react
npm install axios zustand react-router-dom
```

### 4.2 Core Pages

- **Login/Register Page**: Form for authentication
- **Groups List Page**: CRUD for groups (create, view, delete)
- **Group Detail Page**: Manage characters, start/view conversations
- **Chat Interface**: Send messages, display multi-character responses in real-time

### 4.3 Components

- `CharacterCard`: Display character name, traits, avatar
- `MessageBubble`: User/character message styling
- `ChatInput`: Message submission form
- `CharacterResponse`: Display character response + speaker name
- `GroupForm`: Create/edit group
- `CharacterForm`: Create/edit character

### 4.4 State Management

Use Zustand for:

- `authStore`: current user, JWT token, login/logout
- `conversationStore`: current conversation, messages, loading state

### 4.5 API Client

File: `src/services/api.ts`

```typescript
import axios from "axios";

const API_BASE = "http://localhost:8000/api";

const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { "Content-Type": "application/json" },
});

// Interceptor for JWT
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem("token");
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

export const groupsAPI = {
  create: (data) => apiClient.post("/groups", data),
  list: () => apiClient.get("/groups"),
  get: (id) => apiClient.get(`/groups/${id}`),
  delete: (id) => apiClient.delete(`/groups/${id}`),
};

export const conversationAPI = {
  create: (groupId) => apiClient.post(`/groups/${groupId}/conversations`),
  sendMessage: (conversationId, content) =>
    apiClient.post(`/conversations/${conversationId}/messages`, { content }),
  getMessages: (conversationId, limit = 50, offset = 0) =>
    apiClient.get(`/conversations/${conversationId}/messages`, {
      params: { limit, offset },
    }),
};
```

### 4.6 Styling

- Use TailwindCSS for responsive design
- Chat bubbles styled differently for user vs. character
- Color-coded characters for easy identification

**Output**: Fully functional React frontend.

**Verification Checklist**:

- [ ] Pages load without errors
- [ ] Auth flow works (register → login → JWT stored)
- [ ] Group creation/deletion works end-to-end
- [ ] Chat sends message and displays character response
- [ ] Responsive design works on mobile

---

## Phase 5: Vector Database & Semantic Search

**Goal**: Efficiently retrieve relevant context for long conversations.

### 5.1 Embedding Pipeline

- On each message, generate embedding using `llm_provider.create_embedding(message.content)`
- Store in vector DB with metadata: `{conversation_id, speaker, timestamp, group_id, user_id}`

### 5.2 Semantic Search

In `ContextManagerService.build_context()`:

1. Fetch recent messages (last 20, sliding window)
2. If over token limit, use semantic search:
   - Create embedding of user's message
   - Query vector DB: `search_similar(embedding, top_k=10)`
   - Combine with recency weighting: `score = 0.7 * similarity + 0.3 * recency`
   - Select top-K messages by combined score

### 5.3 Context Compression

If still over token limit:

- Use LLM to compress: "Summarize key facts from conversation: [messages]"
- Return compressed summary + most recent/relevant messages

**Output**: Long conversations (1000+ messages) handled efficiently.

**Verification Checklist**:

- [ ] Embeddings generated for each message
- [ ] Semantic search returns relevant messages (manually verify)
- [ ] Context stays within token limits
- [ ] Compression preserves critical facts

---

## Phase 6: Testing & Validation

**Goal**: Ensure reliability and correctness.

### 6.1 Unit Tests

File: `tests/unit/`

- **Domain Models**: Validation, serialization
- **Repositories** (mocked MongoDB): CRUD operations
- **Services** (mocked LLM): orchestration logic, context building, response generation
- **Schemas**: validation edge cases

Target: ≥80% coverage on services.

### 6.2 Integration Tests

File: `tests/integration/`

- **E2E Flow**: Create user → create group → add characters → send message → receive response
- **API Endpoints**: All routes with test database
- **Vector Search**: Accuracy of semantic search

### 6.3 Manual Testing Checklist

- [ ] Create group + 3 characters
- [ ] Send 10+ messages in conversation
- [ ] Verify character responses are personality-consistent
- [ ] Check context retrieval works for long conversations
- [ ] Verify semantic search returns relevant messages
- [ ] Test error handling (invalid character, group not found, etc.)
- [ ] Load test: 100+ concurrent users creating conversations

---

## File Structure (Final)

```
Multi-Agent-chatroom/
├── backend/
│   ├── src/
│   │   ├── models/
│   │   │   ├── domain.py          # Domain entities (User, Group, Character, etc.)
│   │   │   └── schemas.py         # Pydantic request/response schemas
│   │   ├── data/
│   │   │   ├── repositories.py    # MongoDB CRUD abstraction
│   │   │   └── vector_db.py       # Vector DB client + semantic search
│   │   ├── services/
│   │   │   ├── orchestrator.py    # Character selection logic
│   │   │   ├── context_manager.py # Context optimization + semantic search
│   │   │   ├── character_service.py # Character response generation
│   │   │   ├── conversation_service.py # Message storage + retrieval
│   │   │   └── llm_provider.py    # LLM abstraction (Groq implementation)
│   │   ├── graph/
│   │   │   └── orchestrator_graph.py # LangGraph StateGraph definition
│   │   ├── api/
│   │   │   ├── routes/
│   │   │   │   ├── auth.py        # Auth endpoints
│   │   │   │   ├── groups.py      # Group endpoints
│   │   │   │   └── conversations.py # Conversation endpoints
│   │   │   ├── middleware/
│   │   │   │   └── auth.py        # JWT validation middleware
│   │   │   └── exceptions.py      # Custom exception classes + handlers
│   │   ├── config/
│   │   │   └── database.py        # MongoDB + Vector DB initialization
│   │   └── __init__.py
│   ├── main.py                    # FastAPI app entry point
│   ├── requirements.txt
│   ├── .env.example
│   └── tests/
│       ├── unit/
│       │   ├── test_models.py
│       │   ├── test_repositories.py
│       │   ├── test_services.py
│       │   └── test_schemas.py
│       ├── integration/
│       │   ├── test_e2e_flow.py
│       │   └── test_api_endpoints.py
│       └── fixtures/
│           └── test_data.py
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── LoginPage.tsx
│   │   │   ├── GroupsPage.tsx
│   │   │   ├── GroupDetailPage.tsx
│   │   │   └── ChatPage.tsx
│   │   ├── components/
│   │   │   ├── CharacterCard.tsx
│   │   │   ├── MessageBubble.tsx
│   │   │   ├── ChatInput.tsx
│   │   │   └── CharacterResponse.tsx
│   │   ├── hooks/
│   │   │   ├── useAuth.ts
│   │   │   └── useConversation.ts
│   │   ├── services/
│   │   │   └── api.ts
│   │   ├── store/
│   │   │   ├── authStore.ts
│   │   │   └── conversationStore.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
├── implementation.md               # This file
└── README.md                      # Project setup + onboarding
```

---

## Implementation Sequence

1. **Phase 1** → Database schemas + repositories
2. **Phase 2** → Services + LangGraph orchestration
3. **Phase 3** → FastAPI routes + endpoints
4. **Phase 4** → React UI (parallelizable with Phase 3)
5. **Phase 5** → Vector DB optimization
6. **Phase 6** → Testing + validation

Each phase has clear inputs/outputs and can be verified independently before proceeding.

---

## Key Design Decisions

| Decision                     | Rationale                                                                  |
| ---------------------------- | -------------------------------------------------------------------------- |
| **DTO Pattern**              | Separates API contracts from domain, enables versioning without DB changes |
| **LLM Provider Abstraction** | Easy to swap Groq ↔ local models ↔ other APIs; testable with mocks         |
| **Repository Pattern**       | Decouples services from MongoDB; enables swapping DB without code changes  |
| **Stateless Services**       | Enables horizontal scaling (multiple instances, load-balanced)             |
| **Async/Await**              | Non-blocking I/O; handles high concurrency efficiently                     |
| **Vector DB for Search**     | Semantic search handles long conversations without token explosion         |
| **LangGraph StateGraph**     | Testable, reproducible conversation flows; easy to add conditional logic   |

---

## Scalability Considerations

- **Database**: MongoDB indices on foreign keys (user_id, group_id); consider sharding for >1M conversations
- **LLM Rate Limiting**: Implement exponential backoff + retry queue
- **Vector Search**: Batch embedding generation; consider caching frequent queries
- **API**: Use connection pooling (MongoDB), request batching, response caching
- **Frontend**: Lazy-load conversations, paginate messages (50 per request)

---

## Not Included (Out of Scope for MVP)

- Real-time WebSockets (Phase 7, use Server-Sent Events or polling for Phase 1)
- Character voice synthesis
- Character memory/learning (adapting to user)
- Multi-language support (Phase 1: English only)
- Mobile app (use responsive React)
- Analytics/telemetry

---

## Success Criteria

✅ **Phase 1**: Database schemas defined, repositories CRUD functional  
✅ **Phase 2**: Orchestrator selects correct character, context optimized  
✅ **Phase 3**: All API endpoints return correct status codes, auth prevents unauthorized access  
✅ **Phase 4**: Chat sends/receives messages, UI renders correctly  
✅ **Phase 5**: Semantic search returns relevant messages, token limits maintained  
✅ **Phase 6**: ≥80% test coverage, E2E flow verified end-to-end
