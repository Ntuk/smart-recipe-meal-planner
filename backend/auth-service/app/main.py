from fastapi import FastAPI, Depends, HTTPException, status, Form
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, EmailStr, Field
from typing import Optional
from datetime import datetime, timedelta
from jose import JWTError, jwt
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
import uuid
from prometheus_client import Counter, Histogram, generate_latest, CONTENT_TYPE_LATEST
from fastapi.responses import Response
import time
from prometheus_fastapi_instrumentator import Instrumentator
import uvicorn
import threading
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Port Configuration
PORT = int(os.getenv("PORT", "8000"))
METRICS_PORT = int(os.getenv("METRICS_PORT", "9090"))

# Prometheus metrics
REQUESTS = Counter('auth_service_requests_total', 'Total requests to the auth service', ['method', 'endpoint', 'status'])
REQUEST_LATENCY = Histogram('auth_service_request_duration_seconds', 'Request latency in seconds', ['method', 'endpoint'])
LOGIN_ATTEMPTS = Counter('auth_service_login_attempts_total', 'Total login attempts', ['status'])
REGISTRATIONS = Counter('auth_service_registrations_total', 'Total user registrations', ['status'])

# Load environment variables
load_dotenv()

# JWT Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-for-development")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30

# MongoDB Configuration
MONGO_URI = os.getenv("MONGO_URI", "mongodb://admin:password@mongodb:27017")
DB_NAME = os.getenv("DB_NAME", "recipe_app")

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="login")

# Initialize FastAPI app
app = FastAPI(title="Auth Service", description="Authentication service for Smart Recipe & Meal Planner")

# Initialize metrics app
metrics_app = FastAPI()

# Initialize Prometheus instrumentation
Instrumentator().instrument(app).expose(metrics_app)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins
    allow_credentials=True,
    allow_methods=["*"],  # Allow all methods
    allow_headers=["*"],  # Allow all headers
    expose_headers=["*"],  # Expose all headers
)

# Database connection
@app.on_event("startup")
async def startup_db_client():
    try:
        # Configure MongoDB client with optimized settings
        app.mongodb_client = AsyncIOMotorClient(
            MONGO_URI,
            maxPoolSize=50,
            minPoolSize=10,
            maxIdleTimeMS=45000,
            connectTimeoutMS=2000,
            serverSelectionTimeoutMS=2000,
            heartbeatFrequencyMS=10000,
            retryWrites=True,
            w='majority',
            readPreference='secondaryPreferred'
        )
        
        app.mongodb = app.mongodb_client[DB_NAME]
        
        # Ping the database to check the connection
        await app.mongodb_client.admin.command('ping')
        logger.info("Connected to MongoDB with optimized settings")
        
        # Create indexes for users collection
        await app.mongodb["users"].create_index("email", unique=True)
        await app.mongodb["users"].create_index("username", unique=True)
    except Exception as e:
        logger.error(f"Could not connect to MongoDB: {e}")
        raise

@app.on_event("shutdown")
async def shutdown_db_client():
    app.mongodb_client.close()

# Models
class UserBase(BaseModel):
    username: str
    email: EmailStr

class UserCreate(UserBase):
    password: str

class UserInDB(UserBase):
    id: str
    hashed_password: str
    created_at: datetime
    updated_at: datetime
    preferences: Optional[dict] = None

class User(UserBase):
    id: str
    created_at: datetime
    preferences: Optional[dict] = None

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    user_id: Optional[str] = None

class UserUpdate(BaseModel):
    username: Optional[str] = None
    email: Optional[EmailStr] = None
    password: Optional[str] = None
    preferences: Optional[dict] = None

# Helper functions
def verify_password(plain_password, hashed_password):
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password):
    return pwd_context.hash(password)

async def get_user(db, user_id: str):
    user = await db["users"].find_one({"id": user_id})
    if user:
        return UserInDB(**user)

async def get_user_by_email(db, email: str):
    user = await db["users"].find_one({"email": email})
    if user:
        return UserInDB(**user)

async def authenticate_user(db, email: str, password: str):
    user = await get_user_by_email(db, email)
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
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt

async def get_current_user(token: str = Depends(oauth2_scheme)):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id: str = payload.get("sub")
        if user_id is None:
            raise credentials_exception
        token_data = TokenData(user_id=user_id)
    except JWTError:
        raise credentials_exception
    user = await get_user(app.mongodb, token_data.user_id)
    if user is None:
        raise credentials_exception
    return user

@app.middleware("http")
async def monitor_requests(request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration = time.time() - start_time
    
    REQUESTS.labels(
        method=request.method,
        endpoint=request.url.path,
        status=response.status_code
    ).inc()
    
    REQUEST_LATENCY.labels(
        method=request.method,
        endpoint=request.url.path
    ).observe(duration)
    
    return response

@app.get("/metrics")
async def metrics():
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

# Routes
@app.post("/register", response_model=Token)
async def register_user(user: UserCreate):
    try:
        # Check if user already exists
        existing_user = await app.mongodb["users"].find_one({"email": user.email})
        if existing_user:
            REGISTRATIONS.labels(status="duplicate_email").inc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        existing_username = await app.mongodb["users"].find_one({"username": user.username})
        if existing_username:
            REGISTRATIONS.labels(status="duplicate_username").inc()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Create new user
        user_id = str(uuid.uuid4())
        now = datetime.utcnow()
        
        user_in_db = UserInDB(
            id=user_id,
            username=user.username,
            email=user.email,
            hashed_password=get_password_hash(user.password),
            created_at=now,
            updated_at=now,
            preferences={}
        )
        
        await app.mongodb["users"].insert_one(user_in_db.dict())
        REGISTRATIONS.labels(status="success").inc()
        
        # Create access token
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user_id}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        REGISTRATIONS.labels(status="error").inc()
        raise e

@app.post("/login", response_model=Token)
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends()):
    try:
        user = await authenticate_user(app.mongodb, form_data.username, form_data.password)
        if not user:
            LOGIN_ATTEMPTS.labels(status="failed").inc()
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        LOGIN_ATTEMPTS.labels(status="success").inc()
        access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user.id}, expires_delta=access_token_expires
        )
        
        return {"access_token": access_token, "token_type": "bearer"}
    except Exception as e:
        LOGIN_ATTEMPTS.labels(status="error").inc()
        raise e

# JSON-based login endpoint for frontend
@app.post("/login-json", response_model=Token)
async def login_json(user_data: dict):
    user = await authenticate_user(app.mongodb, user_data.get("username"), user_data.get("password"))
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": user.id}, expires_delta=access_token_expires
    )
    
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/profile", response_model=User)
async def read_users_me(current_user: UserInDB = Depends(get_current_user)):
    return User(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        created_at=current_user.created_at,
        preferences=current_user.preferences
    )

@app.put("/profile", response_model=User)
async def update_user(
    user_update: UserUpdate,
    current_user: UserInDB = Depends(get_current_user)
):
    update_data = user_update.dict(exclude_unset=True)
    
    if "password" in update_data:
        update_data["hashed_password"] = get_password_hash(update_data.pop("password"))
    
    update_data["updated_at"] = datetime.utcnow()
    
    await app.mongodb["users"].update_one(
        {"id": current_user.id},
        {"$set": update_data}
    )
    
    updated_user = await get_user(app.mongodb, current_user.id)
    
    return User(
        id=updated_user.id,
        username=updated_user.username,
        email=updated_user.email,
        created_at=updated_user.created_at,
        preferences=updated_user.preferences
    )

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# For testing purposes
@app.get("/users", response_model=list[User])
async def get_all_users():
    users = []
    cursor = app.mongodb["users"].find({})
    async for document in cursor:
        users.append(User(
            id=document["id"],
            username=document["username"],
            email=document["email"],
            created_at=document["created_at"],
            preferences=document.get("preferences", {})
        ))
    return users

# Start metrics server in a separate thread
def run_metrics_server():
    uvicorn.run(metrics_app, host="0.0.0.0", port=METRICS_PORT)

# Start the metrics server in a background thread when the app starts
@app.on_event("startup")
async def startup_event():
    metrics_thread = threading.Thread(target=run_metrics_server, daemon=True)
    metrics_thread.start()
    logger.info(f"Metrics server started on port {METRICS_PORT}") 