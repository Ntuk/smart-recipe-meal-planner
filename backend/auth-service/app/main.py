from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
import os
import logging
from bson import ObjectId
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from jwt.exceptions import PyJWTError

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(title="Authentication Service API", description="API for user authentication and profile management")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = os.getenv("DATABASE_NAME", "recipe_db")

# JWT settings
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key")  # Change in production
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

# MongoDB client
client = None

# Models
class PyObjectId(ObjectId):
    @classmethod
    def __get_validators__(cls):
        yield cls.validate

    @classmethod
    def validate(cls, v):
        if not ObjectId.is_valid(v):
            raise ValueError("Invalid ObjectId")
        return ObjectId(v)

    @classmethod
    def __modify_schema__(cls, field_schema):
        field_schema.update(type="string")

class UserPreferences(BaseModel):
    dietary_preferences: List[str] = []
    favorite_cuisines: List[str] = []

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    username: Optional[str] = None
    preferences: Optional[UserPreferences] = None

class User(BaseModel):
    id: PyObjectId = Field(default_factory=PyObjectId, alias="_id")
    username: str
    email: EmailStr
    hashed_password: str
    preferences: Optional[UserPreferences] = None
    created_at: Optional[str] = None
    
    class Config:
        allow_population_by_field_name = True
        arbitrary_types_allowed = True
        json_encoders = {ObjectId: str}

class UserResponse(BaseModel):
    id: str
    username: str
    email: EmailStr
    preferences: Optional[UserPreferences] = None
    created_at: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user: UserResponse

class TokenData(BaseModel):
    username: Optional[str] = None

# Database connection
@app.on_event("startup")
async def startup_db_client():
    global client
    try:
        client = AsyncIOMotorClient(MONGODB_URI)
        # Validate the connection
        await client.admin.command('ping')
        logger.info("Connected to MongoDB")
    except Exception as e:
        logger.error(f"Failed to connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    global client
    if client:
        client.close()
        logger.info("MongoDB connection closed")

# Dependency to get database
async def get_database():
    return client[DATABASE_NAME]

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(db, username: str):
    user = await db.users.find_one({"username": username})
    if user:
        return User(**user)

async def authenticate_user(db, username: str, password: str):
    user = await get_user(db, username)
    if not user:
        return False
    if not verify_password(password, user.hashed_password):
        return False
    return user

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme), db = Depends(get_database)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        token_data = TokenData(username=username)
    except PyJWTError:
        raise credentials_exception
    user = await get_user(db, username=token_data.username)
    if user is None:
        raise credentials_exception
    return user

# Routes
@app.get("/")
async def root():
    return {"message": "Authentication Service API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.post("/register", response_model=Token)
async def register_user(user_data: UserCreate, db = Depends(get_database)):
    # Check if username already exists
    existing_user = await db.users.find_one({"username": user_data.username})
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await db.users.find_one({"email": user_data.email})
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_password = get_password_hash(user_data.password)
    user_dict = {
        "username": user_data.username,
        "email": user_data.email,
        "hashed_password": hashed_password,
        "preferences": {"dietary_preferences": [], "favorite_cuisines": []},
        "created_at": datetime.now().isoformat(),
    }
    
    result = await db.users.insert_one(user_dict)
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user_data.username}, expires_delta=access_token_expires
    )
    
    # Get created user
    created_user = await db.users.find_one({"_id": result.inserted_id})
    
    # Prepare response
    user_response = {
        "id": str(created_user["_id"]),
        "username": created_user["username"],
        "email": created_user["email"],
        "preferences": created_user["preferences"],
        "created_at": created_user["created_at"],
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }

@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db = Depends(get_database)):
    user = await authenticate_user(db, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    
    # Prepare response
    user_response = {
        "id": str(user.id),
        "username": user.username,
        "email": user.email,
        "preferences": user.preferences,
        "created_at": user.created_at,
    }
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user": user_response
    }

@app.get("/profile", response_model=UserResponse)
async def get_user_profile(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "username": current_user.username,
        "email": current_user.email,
        "preferences": current_user.preferences,
        "created_at": current_user.created_at,
    }

@app.put("/profile", response_model=UserResponse)
async def update_user_profile(user_update: UserUpdate, current_user: User = Depends(get_current_user), db = Depends(get_database)):
    update_data = {}
    
    if user_update.username is not None:
        # Check if username already exists
        if user_update.username != current_user.username:
            existing_user = await db.users.find_one({"username": user_update.username})
            if existing_user:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Username already taken"
                )
        update_data["username"] = user_update.username
    
    if user_update.preferences is not None:
        update_data["preferences"] = user_update.preferences.dict()
    
    if update_data:
        await db.users.update_one(
            {"_id": current_user.id},
            {"$set": update_data}
        )
    
    # Get updated user
    updated_user = await db.users.find_one({"_id": current_user.id})
    
    return {
        "id": str(updated_user["_id"]),
        "username": updated_user["username"],
        "email": updated_user["email"],
        "preferences": updated_user["preferences"],
        "created_at": updated_user["created_at"],
    } 