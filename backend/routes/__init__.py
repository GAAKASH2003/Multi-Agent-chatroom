"""
Routes package for FastAPI application
"""

from .auth_router import router as auth_router
from .group_router import router as group_router
from .chracter_router import router as character_router
from .conversation_router import router as conversation_router
from .session_router import router as session_router

__all__ = ["auth_router", "group_router","character_router","conversation_router","session_router"]
