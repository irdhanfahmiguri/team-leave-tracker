from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from datetime import datetime

app = FastAPI()

# Mengizinkan koneksi dari antarmuka visual Substrait
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DATA_FILE = "data.json"

def load_data():
    if not os.path.exists(DATA_FILE):
        initial_data = {
            "max_quota": 2,
            "users": [
                {"name": "Manager", "role": "Manager"},
                {"name": "Budi Santoso", "role": "Employee"},
                {"name": "Siti Rahma", "role": "Employee"}
            ],
            "leaves": []
        }
        save_data(initial_data)
        return initial_data
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# 1. Jalur Wajib Kesehatan Server (Diminta oleh Substrait)
@app.get("/health")
def health_check():
    return {"status": "ok"}

# 2. Jalur API Cuti dengan Prefiks /api (Diminta oleh Substrait)
@app.get("/api/leaves")
def get_leaves():
    return load_data()

class LeaveRequest(BaseModel):
    user: str
    type: str
    start: str
    end: str
    reason: str = ""

@app.post("/api/leaves")
def create_leave(req: LeaveRequest):
    db = load_data()
    new_leave = {
        "id": int(datetime.now().timestamp()),
        "user": req.user,
        "manager": "Manager",
        "type": req.type,
        "start": req.start,
        "end": req.end,
        "status": "Pending",
        "reason": req.reason
    }
    db["leaves"].append(new_leave)
    save_data(db)
    return {"message": "Success", "data": new_leave}
