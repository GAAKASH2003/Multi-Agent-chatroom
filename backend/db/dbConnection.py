"""
MongoDB Connection Manager using PyMongo
Handles synchronous connection to MongoDB with connection pooling and collection access
"""

import os
from typing import Optional
from pymongo import MongoClient
from pymongo.database import Database
from dotenv import load_dotenv

load_dotenv()


class MongoDBConnection:  
    _instance: Optional['MongoDBConnection'] = None
    _client: Optional[MongoClient] = None
    _db: Optional[Database] = None
    
    def __new__(cls) -> 'MongoDBConnection':
        """Ensure only one instance exists (Singleton pattern)"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """Initialize connection parameters from environment"""
        self.mongo_url = os.getenv(
            "MONGO_URL",
            "mongodb://localhost:27017"
        )
        self.db_name = os.getenv("MONGO_DB_NAME", "multi_agent_chatroom")

    
    def connect(self) -> None:
        """
        Establish connection to MongoDB with connection pooling.
        Call this during application startup.
        """
        if self._client is None:
            try:
                self._client = MongoClient(
                    self.mongo_url,
                    serverSelectionTimeoutMS=10000,
                    socketTimeoutMS=10000,
                    ssl=True,
                    tlsAllowInvalidCertificates=True,
                    tlsAllowInvalidHostnames=True,
                    retryWrites=False,
                )
                
                # Verify connection
                self._client.admin.command("ping")
                
                # Get database
                self._db = self._client[self.db_name]
                
                # Create indices
                self._create_indices()
                
                print(f"✓ Connected to MongoDB: {self.db_name}")
            except Exception as e:
                print(f"✗ Failed to connect to MongoDB: {e}")
                raise
    
    def disconnect(self) -> None:
        """
        Close MongoDB connection.
        Call this during application shutdown.
        """
        if self._client is not None:
            self._client.close()
            self._client = None
            self._db = None
            print("✓ Disconnected from MongoDB")
    
    
    def get_database(self) -> Database:
        """
        Get the database instance.
        
        Returns:
            Database: MongoDB database
            
        Raises:
            RuntimeError: If not connected
        """
        if self._db is None:
            raise RuntimeError(
                "MongoDB not connected. Call db.connect() first."
            )
        return self._db
    
    def get_collection(self, collection_name: str):
        """
        Get a specific collection.
        
        Args:
            collection_name: Name of the collection
            
        Returns:
            Collection: MongoDB collection
            
        Raises:
            RuntimeError: If not connected
        """
        db = self.get_database()
        return db[collection_name]
    
    def health_check(self) -> bool:
        try:
            if self._client is None:
                return False
            self._client.admin.command("ping")
            return True
        except Exception as e:
            print(f"Health check failed: {e}")
            return False
    
    def create_vector_index():
        msg_collection = db.get_collection("messages")
        msg_collection.create_search_index({
            "name": "message_vector_index",
            "type": "vectorSearch",
            "definition": {
                "fields": [
                    {
                        "type": "vector",
                        "path": "embedding",
                        "numDimensions": 768,    # ← nomic-v1 is 768
                        "similarity": "cosine"   # nomic recommends cosine
                    }
                ]
            }
        })
    
    def _create_indices(self) -> None:
        if self._db is None:
            return
        try:
            users_collection = self._db["users"]
            users_collection.create_index("email", unique=True)
            print("✓ Created indices for collections")
            # self.create_vector_index()
            
        except Exception as e:
            print(f"✗ Error creating indices: {e}")


# Global instance for easy import
db = MongoDBConnection()


# Convenience functions
def connect_db() -> None:
    """Connect to MongoDB"""
    print("Connecting to MongoDB...")
    db.connect()
    print("Connected to MongoDB...")


def disconnect_db() -> None:
    """Disconnect from MongoDB"""
    db.disconnect()


def get_db() -> Database:
    """Get database instance"""
    return db.get_database()


def get_collection(collection_name: str):
    """Get a specific collection"""
    return db.get_collection(collection_name)


if __name__ == "__main__":
    # Test connection
    connect_db()
    print("MongoDB Health Check:", db.health_check())
    disconnect_db()