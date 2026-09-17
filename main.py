from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import json
import os
from datetime import datetime

app = FastAPI()

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

# 1. Jalur Utama (Tampilan Aplikasi Web HTML)
@app.get("/", response_class=HTMLResponse)
def read_root():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Team Leave Tracker</title>
        <script src="https://cdn.tailwindcss.com"></script>
    </head>
    <body class="bg-gray-100 p-8 font-sans">
        <div class="max-w-4xl mx-auto bg-white p-6 rounded-xl shadow-md">
            <h1 class="text-2xl font-bold text-indigo-600 mb-2">📅 Team Leave Tracker</h1>
            <p class="text-gray-600 mb-6">Aplikasi Pelacak Cuti Tim siap digunakan di Substrait.</p>
            
            <div class="bg-indigo-50 border border-indigo-200 p-4 rounded-lg mb-6">
                <h2 class="font-semibold text-indigo-900">Status Server: Aktif ✅</h2>
                <p class="text-sm text-indigo-700">Jalur API /health dan /api/leaves berjalan dengan normal.</p>
            </div>

            <h3 class="font-bold text-lg mb-2">Pemeriksaan Jalur API:</h3>
            <ul class="list-disc pl-5 space-y-1 text-sm text-gray-700">
                <li><a href="/health" class="text-blue-600 underline" target="_blank">Cek Cek Kesehatan Server (/health)</a></li>
                <li><a href="/api/leaves" class="text-blue-600 underline" target="_blank">Cek Data Cuti JSON (/api/leaves)</a></li>
            </ul>
        </div>
    </body>
    </html>
    """

# 2. Jalur Wajib Kesehatan Server untuk Substrait
@app.get("/health")
def health_check():
    return {"status": "ok"}

# 3. Jalur API Cuti
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
