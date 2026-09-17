from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
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
            "users": [
                {"id": 1, "name": "Budi Santoso", "level": "Manager"},
                {"id": 2, "name": "Siti Rahma", "level": "Employee"},
                {"id": 3, "name": "Andi Wijaya", "level": "Employee"}
            ],
            "leaves": []
        }
        save_data(initial_data)
        return initial_data
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except Exception:
        return {"users": [], "leaves": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

class UserCreate(BaseModel):
    name: str
    level: str

class LeaveCreate(BaseModel):
    user_name: str
    type: str
    start_date: str
    end_date: str
    reason: str = ""

class LeaveAction(BaseModel):
    action: str
    manager_notes: str = ""

@app.get("/health")
def health_check():
    return {"status": "ok"}

@app.get("/api/data")
def get_all_data():
    return load_data()

# Endpoint Import / Restore Data Manual
@app.post("/api/data/restore")
def restore_data(data: dict = Body(...)):
    if "users" in data and "leaves" in data:
        save_data(data)
        return {"message": "Data berhasil dipulihkan"}
    raise HTTPException(status_code=400, detail="Format JSON tidak valid")

@app.post("/api/users")
def add_user(user: UserCreate):
    db = load_data()
    new_user = {"id": int(datetime.now().timestamp()), "name": user.name, "level": user.level}
    db["users"].append(new_user)
    save_data(db)
    return {"message": "Pengguna berhasil ditambahkan", "user": new_user}

@app.delete("/api/users/{user_id}")
def delete_user(user_id: int):
    db = load_data()
    db["users"] = [u for u in db["users"] if u["id"] != user_id]
    save_data(db)
    return {"message": "Pengguna berhasil dihapus"}

@app.post("/api/leaves")
def request_leave(leave: LeaveCreate):
    db = load_data()
    new_leave = {
        "id": int(datetime.now().timestamp()),
        "user_name": leave.user_name,
        "type": leave.type,
        "start_date": leave.start_date,
        "end_date": leave.end_date,
        "reason": leave.reason,
        "status": "Pending",
        "manager_notes": "",
        "created_at": datetime.now().strftime("%d %b %Y, %H:%M")
    }
    db["leaves"].append(new_leave)
    save_data(db)
    return {"message": "Pengajuan cuti berhasil terkirim", "leave": new_leave}

@app.post("/api/leaves/{leave_id}/action")
def process_leave_action(leave_id: int, action_data: LeaveAction):
    db = load_data()
    for leave in db["leaves"]:
        if leave["id"] == leave_id:
            leave["status"] = action_data.action
            leave["manager_notes"] = action_data.manager_notes
            save_data(db)
            return {"message": f"Pengajuan berhasil di-{action_data.action.lower()}"}
    raise HTTPException(status_code=404, detail="Data cuti tidak ditemukan")

@app.get("/", response_class=HTMLResponse)
def render_app():
    return """
    <!DOCTYPE html>
    <html lang="id">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Team Leave Tracker</title>
        <script src="https://cdn.tailwindcss.com"></script>
        <script src="https://unpkg.com/lucide@latest"></script>
        <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&display=swap" rel="stylesheet">
        <style>
            body { font-family: 'Plus Jakarta Sans', sans-serif; }
        </style>
    </head>
    <body class="bg-slate-50 text-slate-800 antialiased min-h-screen flex flex-col">

        <!-- Top Navigation -->
        <header class="bg-white border-b border-slate-200 sticky top-0 z-30">
            <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                <div class="flex items-center space-x-3">
                    <div class="bg-indigo-600 p-2 rounded-xl text-white shadow-sm shadow-indigo-200">
                        <i data-lucide="calendar-check-2" class="w-5 h-5"></i>
                    </div>
                    <div>
                        <h1 class="font-bold text-base text-slate-900 leading-none">LeaveTracker</h1>
                        <span class="text-[11px] font-medium text-slate-400">Team Availability Portal</span>
                    </div>
                </div>

                <!-- Active Role Selector & Backup Buttons -->
                <div class="flex items-center space-x-2">
                    <button onclick="downloadBackup()" title="Download Backup Data" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-semibold flex items-center space-x-1.5 transition">
                        <i data-lucide="download" class="w-3.5 h-3.5"></i>
                        <span class="hidden sm:inline">Backup Data</span>
                    </button>
                    
                    <label title="Restore Backup Data" class="bg-slate-100 hover:bg-slate-200 text-slate-700 px-3 py-1.5 rounded-xl border border-slate-200 text-xs font-semibold flex items-center space-x-1.5 cursor-pointer transition">
                        <i data-lucide="upload" class="w-3.5 h-3.5"></i>
                        <span class="hidden sm:inline">Restore Data</span>
                        <input type="file" id="restoreFileInput" accept=".json" onchange="uploadBackup(event)" class="hidden">
                    </label>

                    <div class="flex items-center space-x-2 bg-slate-100 p-1.5 rounded-xl border border-slate-200 ml-2">
                        <i data-lucide="user-check" class="w-4 h-4 text-indigo-600 ml-1"></i>
                        <select id="activeUserSelect" onchange="switchUser()" class="bg-white text-slate-800 text-xs font-semibold rounded-lg px-2.5 py-1 border border-slate-200 focus:outline-none focus:ring-2 focus:ring-indigo-500 shadow-sm">
                        </select>
                    </div>
                </div>
            </div>
        </header>

        <!-- Main Workspace -->
        <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 w-full grid grid-cols-1 lg:grid-cols-12 gap-8">
            
            <!-- Left Panel -->
            <div class="lg:col-span-4 space-y-6">
                <!-- Card 1: Form Pengajuan Cuti -->
                <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
                    <div class="flex items-center space-x-2 border-b border-slate-100 pb-3">
                        <i data-lucide="file-text" class="w-5 h-5 text-indigo-600"></i>
                        <h2 class="font-bold text-slate-900 text-sm">Ajukan Cuti Baru</h2>
                    </div>

                    <form onsubmit="handleRequestLeave(event)" class="space-y-3.5">
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Tipe Cuti</label>
                            <select id="leaveType" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-2 focus:ring-indigo-500 transition">
                                <option value="Annual Leave">Annual Leave (Cuti Tahunan)</option>
                                <option value="Sick Leave">Sick Leave (Cuti Sakit)</option>
                                <option value="Emergency Leave">Emergency Leave (Izin Darurat)</option>
                                <option value="Work From Home">Work From Home (WFH)</option>
                            </select>
                        </div>

                        <div class="grid grid-cols-2 gap-3">
                            <div>
                                <label class="block text-xs font-semibold text-slate-600 mb-1">Mulai</label>
                                <input type="date" id="startDate" required class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-2 focus:ring-indigo-500 transition">
                            </div>
                            <div>
                                <label class="block text-xs font-semibold text-slate-600 mb-1">Selesai</label>
                                <input type="date" id="endDate" required class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-2 focus:ring-indigo-500 transition">
                            </div>
                        </div>

                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Alasan Pengajuan</label>
                            <textarea id="leaveReason" rows="2" placeholder="Contoh: Keperluan keluarga..." class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-2 focus:ring-indigo-500 transition"></textarea>
                        </div>

                        <button type="submit" class="w-full bg-indigo-600 hover:bg-indigo-700 text-white font-semibold text-xs py-2.5 rounded-xl transition shadow-sm shadow-indigo-200 flex items-center justify-center space-x-2">
                            <i data-lucide="send" class="w-4 h-4"></i>
                            <span>Kirim Pengajuan</span>
                        </button>
                    </form>
                </div>

                <!-- Card 2: Kelola Karyawan -->
                <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
                    <div class="flex items-center space-x-2 border-b border-slate-100 pb-3">
                        <i data-lucide="users" class="w-5 h-5 text-indigo-600"></i>
                        <h2 class="font-bold text-slate-900 text-sm">Kelola Anggota Tim</h2>
                    </div>

                    <form onsubmit="handleAddUser(event)" class="space-y-3">
                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Nama Karyawan</label>
                            <input type="text" id="newUserName" placeholder="Masukkan nama..." required class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-2 focus:ring-indigo-500 transition">
                        </div>

                        <div>
                            <label class="block text-xs font-semibold text-slate-600 mb-1">Level / Peran</label>
                            <select id="newUserLevel" class="w-full bg-slate-50 border border-slate-200 rounded-xl px-3 py-2 text-xs font-medium focus:bg-white focus:ring-2 focus:ring-indigo-500 transition">
                                <option value="Employee">Employee</option>
                                <option value="Manager">Manager</option>
                            </select>
                        </div>

                        <button type="submit" class="w-full bg-slate-800 hover:bg-slate-900 text-white font-semibold text-xs py-2.5 rounded-xl transition flex items-center justify-center space-x-2">
                            <i data-lucide="plus-circle" class="w-4 h-4"></i>
                            <span>Tambah Karyawan</span>
                        </button>
                    </form>

                    <div class="pt-2 border-t border-slate-100">
                        <label class="block text-xs font-semibold text-slate-400 mb-2">Daftar Karyawan Terdaftar:</label>
                        <div id="userListContainer" class="space-y-1.5 max-h-48 overflow-y-auto"></div>
                    </div>
                </div>
            </div>

            <!-- Right Panel -->
            <div class="lg:col-span-8 space-y-6">
                <!-- Manager Approval Feed -->
                <div id="managerApprovalPanel" class="bg-amber-50/60 border border-amber-200 rounded-2xl p-6 shadow-sm space-y-4 hidden">
                    <div class="flex items-center justify-between border-b border-amber-200/60 pb-3">
                        <div class="flex items-center space-x-2">
                            <div class="p-1.5 bg-amber-100 text-amber-800 rounded-lg">
                                <i data-lucide="bell" class="w-4 h-4"></i>
                            </div>
                            <h2 class="font-bold text-amber-950 text-sm">Pengajuan Menunggu Persetujuan Manager</h2>
                        </div>
                        <span id="pendingBadgeCount" class="bg-amber-200 text-amber-900 text-[10px] font-bold px-2 py-0.5 rounded-full">0 Pengajuan</span>
                    </div>

                    <div id="pendingList" class="space-y-3"></div>
                </div>

                <!-- Schedule & History Table -->
                <div class="bg-white rounded-2xl p-6 border border-slate-200 shadow-sm space-y-4">
                    <div class="flex flex-col sm:flex-row sm:items-center justify-between border-b border-slate-100 pb-4 gap-3">
                        <div class="flex items-center space-x-2">
                            <i data-lucide="calendar" class="w-5 h-5 text-indigo-600"></i>
                            <h2 id="tableTitle" class="font-bold text-slate-900 text-sm">Jadwal & Status Cuti Tim</h2>
                        </div>

                        <div id="filterContainer" class="flex items-center space-x-2">
                            <span class="text-xs font-semibold text-slate-400">Filter:</span>
                            <select id="filterUser" onchange="renderApp()" class="bg-slate-50 border border-slate-200 rounded-xl px-3 py-1.5 text-xs font-semibold text-slate-700 focus:outline-none focus:ring-2 focus:ring-indigo-500">
                                <option value="ALL">Semua Anggota Tim</option>
                            </select>
                        </div>
                    </div>

                    <div class="overflow-x-auto">
                        <table class="w-full text-left text-xs text-slate-600">
                            <thead class="bg-slate-50 text-[11px] font-bold uppercase tracking-wider text-slate-400 rounded-xl">
                                <tr>
                                    <th class="p-3">Karyawan</th>
                                    <th class="p-3">Tipe Cuti</th>
                                    <th class="p-3">Tanggal</th>
                                    <th class="p-3">Status</th>
                                    <th class="p-3">Catatan Manager</th>
                                </tr>
                            </thead>
                            <tbody id="leaveTableBody" class="divide-y divide-slate-100 font-medium"></tbody>
                        </table>
                    </div>
                </div>
            </div>
        </main>

        <script>
            let appData = { users: [], leaves: [] };
            let currentUser = null;

            async function fetchData() {
                const res = await fetch('/api/data');
                appData = await res.json();
                populateUserDropdowns();
                renderUserList();
                renderApp();
            }

            function downloadBackup() {
                const dataStr = "data:text/json;charset=utf-8," + encodeURIComponent(JSON.stringify(appData, null, 4));
                const downloadAnchor = document.createElement('a');
                downloadAnchor.setAttribute("href", dataStr);
                downloadAnchor.setAttribute("download", `leave_tracker_backup_${new Date().toISOString().slice(0,10)}.json`);
                document.body.appendChild(downloadAnchor);
                downloadAnchor.click();
                downloadAnchor.remove();
            }

            async function uploadBackup(event) {
                const file = event.target.files[0];
                if (!file) return;

                const reader = new FileReader();
                reader.onload = async function(e) {
                    try {
                        const parsedData = JSON.parse(e.target.result);
                        await fetch('/api/data/restore', {
                            method: 'POST',
                            headers: {'Content-Type': 'application/json'},
                            body: JSON.stringify(parsedData)
                        });
                        alert('Data berhasil dipulihkan!');
                        fetchData();
                    } catch (err) {
                        alert('File backup JSON tidak valid.');
                    }
                };
                reader.readAsText(file);
            }

            function populateUserDropdowns() {
                const select = document.getElementById("activeUserSelect");
                const filterSelect = document.getElementById("filterUser");
                
                const currentVal = select.value;
                select.innerHTML = appData.users.map(u => `<option value="${u.name}">${u.name} (${u.level})</option>`).join("");
                
                if (currentVal) select.value = currentVal;
                if (!currentUser && appData.users.length > 0) currentUser = appData.users[0];
                else currentUser = appData.users.find(u => u.name === select.value) || appData.users[0];

                filterSelect.innerHTML = `<option value="ALL">Semua Anggota Tim</option>` + 
                    appData.users.map(u => `<option value="${u.name}">Cuti: ${u.name}</option>`).join("");
            }

            function renderUserList() {
                const container = document.getElementById("userListContainer");
                container.innerHTML = appData.users.map(u => `
                    <div class="flex items-center justify-between p-2 rounded-lg bg-slate-50 border border-slate-100 text-xs">
                        <div class="flex items-center space-x-2">
                            <span class="font-semibold text-slate-700">${u.name}</span>
                            <span class="text-[10px] text-slate-400 font-medium">(${u.level})</span>
                        </div>
                        <button onclick="handleDeleteUser(${u.id}, '${u.name}')" class="text-rose-500 hover:text-rose-700 p-1 rounded hover:bg-rose-50 transition" title="Hapus Karyawan">
                            <i data-lucide="trash-2" class="w-3.5 h-3.5"></i>
                        </button>
                    </div>
                `).join("");
                lucide.createIcons();
            }

            function switchUser() {
                const selectedName = document.getElementById("activeUserSelect").value;
                currentUser = appData.users.find(u => u.name === selectedName);
                renderApp();
            }

            function renderApp() {
                if (!currentUser) return;

                const isManager = currentUser.level === "Manager";

                document.getElementById("managerApprovalPanel").classList.toggle("hidden", !isManager);
                document.getElementById("filterContainer").classList.toggle("hidden", !isManager);
                document.getElementById("tableTitle").innerText = isManager ? "Jadwal & Status Cuti Tim" : "Riwayat Pengajuan Cuti Saya";

                if (isManager) {
                    const pending = appData.leaves.filter(l => l.status === "Pending");
                    document.getElementById("pendingBadgeCount").innerText = `${pending.length} Pengajuan`;
                    
                    const pendingContainer = document.getElementById("pendingList");
                    if (pending.length === 0) {
                        pendingContainer.innerHTML = `
                            <div class="text-center py-6 text-slate-400">
                                <i data-lucide="check-circle-2" class="w-8 h-8 mx-auto mb-2 text-amber-400"></i>
                                <p class="text-xs font-semibold">Tidak ada pengajuan cuti yang perlu diapprove.</p>
                            </div>`;
                    } else {
                        pendingContainer.innerHTML = pending.map(l => `
                            <div class="bg-white p-4 rounded-xl border border-amber-200/80 shadow-sm space-y-3">
                                <div class="flex items-center justify-between">
                                    <div class="flex items-center space-x-2">
                                        <div class="w-7 h-7 rounded-full bg-indigo-100 text-indigo-700 font-bold flex items-center justify-center text-xs">
                                            ${l.user_name.charAt(0)}
                                        </div>
                                        <div>
                                            <h3 class="font-bold text-xs text-slate-900">${l.user_name}</h3>
                                            <span class="text-[10px] text-slate-400 font-medium">${l.type}</span>
                                        </div>
                                    </div>
                                    <span class="text-[11px] font-semibold text-slate-600 bg-slate-100 px-2 py-1 rounded-lg border border-slate-200">
                                        📅 ${l.start_date} s/d ${l.end_date}
                                    </span>
                                </div>
                                ${l.reason ? `<p class="text-xs text-slate-600 italic bg-slate-50 p-2.5 rounded-lg border border-slate-100">"${l.reason}"</p>` : ''}
                                <div>
                                    <input type="text" id="note_${l.id}" placeholder="Tuliskan catatan approval/rejection untuk pemohon..." class="w-full bg-slate-50 border border-slate-200 rounded-xl p-2 text-xs font-medium focus:bg-white focus:ring-2 focus:ring-amber-500 transition">
                                </div>
                                <div class="flex space-x-2 pt-1">
                                    <button onclick="handleAction(${l.id}, 'Approved')" class="flex-1 bg-emerald-600 hover:bg-emerald-700 text-white font-semibold text-xs py-2 rounded-xl transition flex items-center justify-center space-x-1">
                                        <i data-lucide="check" class="w-3.5 h-3.5"></i>
                                        <span>Setujui (Approve)</span>
                                    </button>
                                    <button onclick="handleAction(${l.id}, 'Rejected')" class="flex-1 bg-rose-600 hover:bg-rose-700 text-white font-semibold text-xs py-2 rounded-xl transition flex items-center justify-center space-x-1">
                                        <i data-lucide="x" class="w-3.5 h-3.5"></i>
                                        <span>Tolak (Reject)</span>
                                    </button>
                                </div>
                            </div>
                        `).join("");
                    }
                }

                let filteredLeaves = [];
                if (isManager) {
                    const filterVal = document.getElementById("filterUser").value;
                    filteredLeaves = filterVal === "ALL" ? appData.leaves : appData.leaves.filter(l => l.user_name === filterVal);
                } else {
                    filteredLeaves = appData.leaves.filter(l => l.user_name === currentUser.name);
                }

                const tbody = document.getElementById("leaveTableBody");

                if (filteredLeaves.length === 0) {
                    tbody.innerHTML = `
                        <tr>
                            <td colspan="5" class="text-center py-8 text-slate-400">
                                <i data-lucide="calendar-x-2" class="w-8 h-8 mx-auto mb-2 text-slate-300"></i>
                                <p class="text-xs font-semibold">Belum ada data pengajuan cuti.</p>
                            </td>
                        </tr>`;
                } else {
                    tbody.innerHTML = filteredLeaves.map(l => `
                        <tr class="hover:bg-slate-50/80 transition">
                            <td class="p-3 font-semibold text-slate-800">${l.user_name}</td>
                            <td class="p-3 font-medium text-slate-600">${l.type}</td>
                            <td class="p-3 text-slate-500">${l.start_date} <span class="text-slate-300">s/d</span> ${l.end_date}</td>
                            <td class="p-3">
                                <span class="inline-flex items-center space-x-1 px-2.5 py-1 text-[11px] font-bold rounded-full ${
                                    l.status === 'Approved' ? 'bg-emerald-50 text-emerald-700 border border-emerald-200' :
                                    l.status === 'Pending' ? 'bg-amber-50 text-amber-700 border border-amber-200' : 
                                    'bg-rose-50 text-rose-700 border border-rose-200'
                                }">
                                    <span>${l.status === 'Approved' ? '✓' : l.status === 'Pending' ? '⏳' : '✕'}</span>
                                    <span>${l.status}</span>
                                </span>
                            </td>
                            <td class="p-3 text-slate-500 text-xs italic">${l.manager_notes || '-'}</td>
                        </tr>
                    `).join("");
                }

                lucide.createIcons();
            }

            async function handleAddUser(e) {
                e.preventDefault();
                const name = document.getElementById("newUserName").value;
                const level = document.getElementById("newUserLevel").value;
                await fetch('/api/users', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ name, level })
                });
                document.getElementById("newUserName").value = "";
                fetchData();
            }

            async function handleDeleteUser(userId, userName) {
                if (confirm(`Apakah Anda yakin ingin menghapus "${userName}" dari daftar karyawan?`)) {
                    await fetch(`/api/users/${userId}`, { method: 'DELETE' });
                    fetchData();
                }
            }

            async function handleRequestLeave(e) {
                e.preventDefault();
                const type = document.getElementById("leaveType").value;
                const start_date = document.getElementById("startDate").value;
                const end_date = document.getElementById("endDate").value;
                const reason = document.getElementById("leaveReason").value;

                await fetch('/api/leaves', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ user_name: currentUser.name, type, start_date, end_date, reason })
                });
                document.getElementById("leaveReason").value = "";
                fetchData();
            }

            async function handleAction(leaveId, action) {
                const notes = document.getElementById(`note_${leaveId}`).value;
                await fetch(`/api/leaves/${leaveId}/action`, {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({ action, manager_notes: notes })
                });
                fetchData();
            }

            fetchData();
        </script>
    </body>
    </html>
    """
