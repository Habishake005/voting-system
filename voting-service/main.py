from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from jose import jwt, JWTError
from sqlalchemy import Column, Integer, String, create_engine, UniqueConstraint
from sqlalchemy.orm import declarative_base, sessionmaker, Session
import redis, os, json, time

app = FastAPI(title="Voting Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/votingdb")
SECRET_KEY   = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM    = "HS256"

engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base         = declarative_base()
r            = redis.Redis(host=os.getenv("REDIS_HOST", "redis"), port=6379, decode_responses=True)

CANDIDATES = [
    {"id": "candidate_a", "name": "Alice Johnson", "party": "Progressive Party"},
    {"id": "candidate_b", "name": "Bob Smith",     "party": "Democratic Party"},
    {"id": "candidate_c", "name": "Carol White",   "party": "Reform Party"},
]

class Vote(Base):
    __tablename__ = "votes"
    __table_args__ = (UniqueConstraint("username"),)
    id           = Column(Integer, primary_key=True)
    username     = Column(String, unique=True, index=True)
    candidate_id = Column(String)

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

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def get_current_user(authorization: str = Header(...)):
    try:
        token   = authorization.split(" ")[1]
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except (JWTError, IndexError):
        raise HTTPException(401, "Invalid token")

class VoteRequest(BaseModel):
    candidate_id: str

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    return {"status": "ready"}

@app.get("/candidates")
def get_candidates(username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    has_voted = db.query(Vote).filter(Vote.username == username).first() is not None
    return {"candidates": CANDIDATES, "has_voted": has_voted}

@app.post("/cast")
def cast_vote(req: VoteRequest, username: str = Depends(get_current_user), db: Session = Depends(get_db)):
    if not any(c["id"] == req.candidate_id for c in CANDIDATES):
        raise HTTPException(400, "Invalid candidate")
    if db.query(Vote).filter(Vote.username == username).first():
        raise HTTPException(409, "You have already voted")
    db.add(Vote(username=username, candidate_id=req.candidate_id))
    db.commit()
    try:
        r.publish("votes", json.dumps({"username": username, "candidate_id": req.candidate_id}))
    except:
        pass
    return {"message": "Vote cast successfully"}