# """
# User Repository for CRUD operations on MongoDB
# Handles all database operations for User model
# """

# from typing import Optional, List
# from bson import ObjectId
# from pymongo.collection import Collection
# from pymongo.errors import DuplicateKeyError
# import bcrypt
# import jwt
# from db.dbConnection import get_collection
# from models.User import User, UserCreate


# class UserRepo:
#     """Repository class for User CRUD operations"""
    
#     COLLECTION_NAME = "users"
    
#     @staticmethod
#     def _get_collection() -> Collection:
#         """Get users collection"""
#         return get_collection(UserRepo.COLLECTION_NAME)
    
#     @staticmethod
#     def create_user(user_create: UserCreate) -> User:
#         try:
#             collection = UserRepo._get_collection()
#             # Convert UserCreate to User
#             user = User(name=user_create.name, email=user_create.email, password=user_create.password)
#             user_dict = user.dict(exclude_none=True)
#             result = collection.insert_one(user_dict)
#             user_dict['_id'] = result.inserted_id
#             return user
            
#         except DuplicateKeyError:
#             raise ValueError(f"User with email '{user_create.email}' already exists")
#         except Exception as e:
#             raise Exception(f"Error creating user: {str(e)}")
    
  
#     @staticmethod
#     def get_user_by_email(email: str) -> Optional[User]:
#         try:
#             collection = UserRepo._get_collection()
#             user_doc = collection.find_one({"email": email})
            
#             if user_doc:
#                 return UserRepo._parse_user(user_doc)
#             return None
            
#         except Exception as e:
#             raise Exception(f"Error fetching user by email: {str(e)}")
    
#     @staticmethod
#     def get_all_users() -> List[User]:
#         try:
#             collection = UserRepo._get_collection()
#             users = []
            
#             for user_doc in collection.find():
#                 users.append(UserRepo._parse_user(user_doc))
            
#             return users
            
#         except Exception as e:
#             raise Exception(f"Error fetching all users: {str(e)}")
    
#     @staticmethod
#     def update_user(user_id: str, update_data: dict) -> Optional[User]:
#         try:
#             if not ObjectId.is_valid(user_id):
#                 return None
            
#             collection = UserRepo._get_collection()
            
#             # Remove _id from update data if present
#             update_data.pop('_id', None)
#             update_data.pop('id', None)
            
#             result = collection.find_one_and_update(
#                 {"_id": ObjectId(user_id)},
#                 {"$set": update_data},
#                 return_document=True
#             )
            
#             if result:
#                 return UserRepo._parse_user(result)
#             return None
            
#         except Exception as e:
#             raise Exception(f"Error updating user: {str(e)}")
    
#     @staticmethod
#     def delete_user(user_id: str) -> bool:
#         try:
#             if not ObjectId.is_valid(user_id):
#                 return False
            
#             collection = UserRepo._get_collection()
#             result = collection.delete_one({"_id": ObjectId(user_id)})
            
#             return result.deleted_count > 0
            
#         except Exception as e:
#             raise Exception(f"Error deleting user: {str(e)}")
    
#     @staticmethod
#     def user_exists_by_email(email: str) -> bool:
#         try:
#             collection = UserRepo._get_collection()
#             return collection.count_documents({"email": email}) > 0
#         except Exception as e:
#             raise Exception(f"Error checking user existence: {str(e)}")
    
#     @staticmethod
#     def _parse_user(user_doc: dict) -> User:
#         if "_id" in user_doc:
#             user_doc["_id"] = str(user_doc["_id"])
#         return User(**user_doc)
    
#     @staticmethod
#     def UserLogin(email: str, password: str) -> Optional[User]:
#         try:
#             collection = UserRepo._get_collection()
            
#             if not email or not password:
#                 raise ValueError("Email and password are required for login")
            
        
#             hashed_user = collection.find_one({"email": email})
            
#             if hashed_user:
#                 hashed_password = hashed_user.get("password")      
#             if not UserRepo.verify_password(password, hashed_password):
#                 return None
            
#             user_doc = collection.find_one({"email": email, "password": password})
            
#             if user_doc:
#                 return UserRepo._parse_user(user_doc)
#             return None
            
#         except Exception as e:
#             raise Exception(f"Error logging in user: {str(e)}")

    
#     @staticmethod
#     def hash_password(password: str) -> str:
#         return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

#     @staticmethod
#     def verify_password(plain_password: str, hashed_password: str) -> bool:
#         return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))
