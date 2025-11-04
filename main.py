import os
from typing import List, Dict, Any
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from database import db, create_document, get_documents
from schemas import Ctfchallenge, Ctfsubmission

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def read_root():
    return {"message": "CTF backend running"}


@app.get("/test")
def test_database():
    response = {
        "backend": "✅ Running",
        "database": "❌ Not Available",
        "database_url": "✅ Set" if os.getenv("DATABASE_URL") else "❌ Not Set",
        "database_name": "✅ Set" if os.getenv("DATABASE_NAME") else "❌ Not Set",
        "connection_status": "Not Connected",
        "collections": [],
    }
    try:
        if db is not None:
            response["database"] = "✅ Available"
            response["connection_status"] = "Connected"
            try:
                collections = db.list_collection_names()
                response["collections"] = collections[:10]
                response["database"] = "✅ Connected & Working"
            except Exception as e:
                response["database"] = f"⚠️ Connected but Error: {str(e)[:80]}"
        else:
            response["database"] = "⚠️ Available but not initialized"
    except Exception as e:
        response["database"] = f"❌ Error: {str(e)[:80]}"
    return response


# ---- CTF Logic ----

# Simple difficulty to points mapping
DIFF_POINTS = {"Easy": 100, "Medium": 200, "Hard": 300}


def seed_challenges():
    """Seed default challenges; never crash server on failures."""
    try:
        if db is None:
            return
        count = db["ctfchallenge"].count_documents({})
        if count == 0:
            samples = [
                Ctfchallenge(
                    challenge_id="web-101",
                    title="Login Bypass Basics",
                    category="Web",
                    difficulty="Easy",
                    description="Bypass a weak login form using basic SQL injection techniques.",
                    hint="Try using logical operators to make a condition always true.",
                    flag="FLAG{BAS1C_SQLI}",
                    points=DIFF_POINTS["Easy"],
                ),
                Ctfchallenge(
                    challenge_id="crypto-201",
                    title="XOR Secrets",
                    category="Crypto",
                    difficulty="Medium",
                    description="Recover a plaintext by analyzing repeated-key XOR.",
                    hint="Frequency analysis on XORed text can reveal the key.",
                    flag="FLAG{X0R_K3Y}",
                    points=DIFF_POINTS["Medium"],
                ),
                Ctfchallenge(
                    challenge_id="pwn-301",
                    title="Buffer Overflow Warmup",
                    category="Pwn",
                    difficulty="Hard",
                    description="Exploit a classic stack buffer overflow to overwrite return address.",
                    hint="Understand calling conventions and NOP sleds.",
                    flag="FLAG{0V3RFL0W}",
                    points=DIFF_POINTS["Hard"],
                ),
            ]
            for s in samples:
                try:
                    create_document("ctfchallenge", s)
                except Exception:
                    # Ignore individual insert failures
                    pass
    except Exception:
        # Never raise from seeding
        pass


# Attempt to seed at startup without crashing
seed_challenges()


class SubmitPayload(BaseModel):
    challenge_id: str
    username: str
    flag: str


@app.get("/api/ctf/challenges")
def list_challenges() -> List[Dict[str, Any]]:
    """Return challenges without exposing flags. Gracefully handle DB issues."""
    docs: List[Dict[str, Any]] = []
    try:
        docs = get_documents("ctfchallenge")
    except Exception:
        # Return empty list on DB unavailability
        return []
    cleaned = []
    for d in docs:
        d.pop("flag", None)
        if "_id" in d:
            d["id"] = str(d.pop("_id"))
        cleaned.append(d)
    return cleaned


@app.get("/api/ctf/leaderboard")
def leaderboard() -> List[Dict[str, Any]]:
    """Aggregate correct submissions by username"""
    try:
        pipeline = [
            {"$match": {"correct": True}},
            {"$group": {"_id": "$username", "points": {"$sum": "$points_awarded"}}},
            {"$sort": {"points": -1}},
            {"$limit": 20},
        ]
        rows = list(db["ctfsubmission"].aggregate(pipeline)) if db else []
        return [{"user": r["_id"], "points": r["points"]} for r in rows]
    except Exception:
        return []


@app.post("/api/ctf/submit")
def submit_flag(payload: SubmitPayload):
    if db is None:
        raise HTTPException(status_code=503, detail="Database unavailable")
    ch = db["ctfchallenge"].find_one({"challenge_id": payload.challenge_id})
    if not ch:
        raise HTTPException(status_code=404, detail="Challenge not found")
    correct = payload.flag.strip() == ch.get("flag")
    points = int(ch.get("points", 0)) if correct else 0
    try:
        sub = Ctfsubmission(
            challenge_id=payload.challenge_id,
            username=payload.username.strip() or "anonymous",
            submitted_flag=payload.flag,
            correct=correct,
            points_awarded=points,
        )
        create_document("ctfsubmission", sub)
    except Exception:
        # If we cannot write, still respond with correctness so UX continues
        pass
    return {"correct": correct, "points": points}


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
