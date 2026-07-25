"""
User routes for FastAPI application
Handles user creation and retrieval operations
"""

from fastapi import APIRouter, HTTPException, status, Depends

from typing import Optional
from pydantic import BaseModel, Field, EmailStr
import bcrypt
import jwt
from datetime import datetime, timedelta
from db.dbConnection import get_collection
from models.User import User, UserCreate, UserLogin
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

SECRET_KEY = "secret-key"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60

class UserResponse(BaseModel):
    id: str = Field(alias="_id")
    name: str
    email: EmailStr

class SignUpResponse(BaseModel):
    user: Optional[UserResponse]
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class LoginResponse(BaseModel):
    token: str
    user_id: str
    name: str
    expires_at: str
    
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)




def get_users_collection():
    """Get users collection (lazy initialization to ensure DB is connected)"""
    return get_collection("users")


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return bcrypt.checkpw(plain_password.encode('utf-8'), hashed_password.encode('utf-8'))


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


@router.post("/signup", response_model=SignUpResponse, status_code=status.HTTP_201_CREATED)
def userSignup(user: UserCreate):
    try:
        collection = get_users_collection()
        if collection.find_one({"email": user.email}):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"User with email '{user.email}' already exists"
            ) 
        hashed_password = hash_password(user.password)
        user_dict = user.model_dump(exclude={"password"})
        user_dict["password"] = hashed_password
        result = collection.insert_one(user_dict)
        user_dict['_id'] = str(result.inserted_id)
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.email, "user_id": str(result.inserted_id)}, 
            expires_delta=access_token_expires
        )
        response = SignUpResponse(
            user=UserResponse.model_validate({**{k: v for k, v in user_dict.items() if k != "password"}, "_id": user_dict["_id"]}),
            access_token=access_token,
            token_type="bearer",
            expires_in=ACCESS_TOKEN_EXPIRE_MINUTES * 60
        )
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error creating user: " + str(e)
        )


@router.post("/login", response_model=LoginResponse)
def login(payload: LoginRequest):
    user_collection = get_users_collection()
    user_doc = user_collection.find_one({"email": payload.email})

    if not user_doc:
        raise HTTPException(status_code=401, detail="Invalid credentials")

    # Verify password
    if not verify_password(payload.password, user_doc["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")

    user = User.from_mongo(user_doc)

    # Generate token
    expires_at = datetime.now() + timedelta(days=7)
    if user:
        token = jwt.encode(
            {
                "sub": user.email,
                "user_id": str(user.id),
                "exp": expires_at
            },
            SECRET_KEY,
            algorithm=ALGORITHM
        )

        return LoginResponse(
            token=token,
            user_id=str(user.id),
            name=user.name,
            expires_at=expires_at.isoformat()
        )
    
    raise HTTPException(status_code=401, detail="User not found")
    
     
security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        payload = jwt.decode(credentials.credentials, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        if email is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication credentials"
            )
        collection = get_users_collection()  # Ensure DB is connected before querying
        user_doc = collection.find_one({"email": email}) or {}
        # Exclude password from response
        current_user = User.from_mongo(user_doc)
        if current_user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        # current_user.token=credentials.credentials
        return current_user
    
    except jwt.PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired or cannot be decoded"
        )
    


@router.get("/me", response_model=UserResponse)
def get_current_user_info(current_user: User = Depends(get_current_user)):
    return UserResponse.model_validate({"_id": current_user.id, "name": current_user.name, "email": current_user.email})


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    # Optionally blacklist token in DB
    return {"message": "Logged out"}