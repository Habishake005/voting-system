from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from passlib.context import CryptContext
from jose import jwt
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from models import User, Base, engine, get_db
import os, time

app = FastAPI(title="Auth Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

SECRET_KEY = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM  = "HS256"
pwd_ctx    = CryptContext(schemes=["bcrypt"])

# Wait for postgres to be ready
def wait_for_db():
    for i in range(30):
        try:
            Base.metadata.create_all(bind=engine)
            print("Database connected successfully")
            return
        except Exception as e:
            print(f"Waiting for database... attempt {i+1}/30")
            time.sleep(2)
    raise Exception("Could not connect to database after 30 attempts")

wait_for_db()

class AuthRequest(BaseModel):
    username: str
    password: str

def create_token(username: str):
    expire = datetime.utcnow() + timedelta(hours=24)
    return jwt.encode({"sub": username, "exp": expire}, SECRET_KEY, algorithm=ALGORITHM)

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    return {"status": "ready"}

@app.post("/register")
def register(req: AuthRequest, db: Session = Depends(get_db)):
    if db.query(User).filter(User.username == req.username).first():
        raise HTTPException(400, "Username already exists")
    hashed = pwd_ctx.hash(req.password)
    db.add(User(username=req.username, password=hashed))
    db.commit()
    return {"message": "User registered successfully"}

@app.post("/login")
def login(req: AuthRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == req.username).first()
    if not user or not pwd_ctx.verify(req.password, user.password):
        raise HTTPException(401, "Invalid credentials")
    return {"access_token": create_token(req.username), "token_type": "bearer"}