from fastapi import FastAPI, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from sqlalchemy import Column, Integer, String, create_engine, func
from sqlalchemy.orm import declarative_base, sessionmaker
import os, time

app = FastAPI(title="Analytics Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://user:password@postgres:5432/votingdb")
SECRET_KEY   = os.getenv("SECRET_KEY", "supersecretkey123")
ALGORITHM    = "HS256"

engine       = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base         = declarative_base()

CANDIDATES = {
    "candidate_a": "Alice Johnson",
    "candidate_b": "Bob Smith",
    "candidate_c": "Carol White",
}

class Vote(Base):
    __tablename__ = "votes"
    id           = Column(Integer, primary_key=True)
    username     = Column(String)
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

def verify_token(authorization: str):
    try:
        token = authorization.split(" ")[1]
        jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except (JWTError, IndexError):
        raise HTTPException(401, "Invalid token")

@app.get("/health")
def health():
    return {"status": "ok"}

@app.get("/ready")
def ready():
    return {"status": "ready"}

@app.get("/results")
def get_results(authorization: str = Header(...)):
    verify_token(authorization)
    db = SessionLocal()
    try:
        rows     = db.query(Vote.candidate_id, func.count(Vote.id)).group_by(Vote.candidate_id).all()
        vote_map = {row[0]: row[1] for row in rows}
        total    = sum(vote_map.values())
        results  = [
            {"id": cid, "name": name, "votes": vote_map.get(cid, 0)}
            for cid, name in CANDIDATES.items()
        ]
        results.sort(key=lambda x: x["votes"], reverse=True)
        return {"results": results, "total_votes": total}
    finally:
        db.close()