# from typing import Optional, List
# from bson import ObjectId
# from pymongo.collection import Collection
# from pymongo.errors import DuplicateKeyError

# from db.dbConnection import get_collection
# from models.Character import Character, CharacterCreate, CharacterUpdate
# from models.User import User

# class CharacterRepo:
#     """Repository class for Character CRUD operations"""
    
#     COLLECTION_NAME = "characters"
    
#     @staticmethod
#     def _get_collection() -> Collection:
#         """Get characters collection"""
#         return get_collection(CharacterRepo.COLLECTION_NAME)
    
#     @staticmethod
#     def createCharacter(character: CharacterCreate) -> Optional[Character]:
#         try:
#             collection = CharacterRepo._get_collection()
#             doc=character.model_dump(by_alias=True, exclude_none=True)
#             if "group" in doc and doc["group"]:
#                 doc["group"] = ObjectId(doc["group"])
#             result = collection.insert_one(doc)
#             created_doc= collection.find_one({"_id": result.inserted_id})
#             if created_doc is None:
#                 raise Exception("Error creating character: document not found after insertion")
#             return Character.from_mongo(created_doc)
#         except DuplicateKeyError:
#             raise ValueError(f"Character with name '{character.name}' already exists")
#         except Exception as e:
#             raise Exception(f"Error creating character: {str(e)}")

#     @staticmethod
#     def getCharacterById(character_id: str) -> Optional[Character]:
#         try:
#             collection = CharacterRepo._get_collection()
#             character_doc = collection.find_one({"_id": ObjectId(character_id)})
            
#             if character_doc:
#                 return Character.from_mongo(character_doc)
#             return None
            
#         except Exception as e:
#             raise Exception(f"Error fetching character by ID: {str(e)}")
    
#     @staticmethod
#     def updateCharacter(character_id: str, character_data: CharacterUpdate) -> Optional[Character]:
#         try:
#             collection = CharacterRepo._get_collection()
#             character_doc = collection.find_one({"_id": ObjectId(character_id)})  # Check if character exists
#             if not character_doc:
#                 raise ValueError(f"Character with ID '{character_id}' does not exist")
#             if collection.find_one({"name": character_data.name, "group": character_doc["group"]}):
#                 raise ValueError(f"Character with name '{character_data.name}' already exists in this group")
#             character_dict = character_data.model_dump(by_alias=True, exclude_none=True)
            
#             collection.update_one(
#                 {"_id": ObjectId(character_id)},
#                 {"$set": character_dict}
#             )
                
#             updated_character = Character.from_mongo({**character_dict, "_id": character_id})
#             if updated_character is None:
#                 raise Exception("Error updating character: failed to parse updated character")
#             return updated_character
            
#         except Exception as e:
#             raise Exception(f"Error updating character: {str(e)}")
        
#     @staticmethod
#     def deleteCharacter(character_id: str) -> bool:
#         try:
#             collection = CharacterRepo._get_collection()
#             result = collection.delete_one({"_id": ObjectId(character_id)})
#             return result.deleted_count > 0
            
#         except Exception as e:
#             raise Exception(f"Error deleting character: {str(e)}")
        
#     @staticmethod
#     def createCharacterIn