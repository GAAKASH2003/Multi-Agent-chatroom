"""
Example usage of UserRepo with MongoDB connection
Demonstrates how to perform CRUD operations
"""

from db.dbConnection import connect_db
from models.User import User
from routes import auth_router,group_router,character_router,conversation_router,session_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    connect_db()
    yield 

app=FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Multi-Agent Chatroom API is running"}



app.include_router(auth_router)
app.include_router(group_router)
app.include_router(character_router)
app.include_router(conversation_router)
app.include_router(session_router)



# if __name__ == "__main__":
#     import uvicorn
#     connect_db()
#     uvicorn.run("main:app", host="0.0.0.0", port=8000)

