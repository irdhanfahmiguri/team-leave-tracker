from datetime import date, datetime, timedelta
from io import StringIO
import csv

from fastapi import FastAPI, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel

app = FastAPI(title="Team Leave Tracker API")

# Batas maksimal orang yang cuti per hari
max_quota = 2

users = [
    {"name": "Manager", "role": "Manager"},
    {"name": "Budi Santoso", "role": "Employee"},
    {"name": "Siti Rahma", "role": "Employee"},
    {"name": "Andi Wijaya", "role": "Employee"},
]

leaves = [
    {
        "id": 1,
        "user": "Budi Santoso",
        "manager": "Manager",
        "type": "Annual Leave",
        "start": "2026-09-20",
        "end": "2026-09-22",
        "status": "Approved",
        "reason": "Liburan Keluarga",
    },
    {
        "id": 2,
        "user": "Siti Rahma",
        "manager": "Manager",
        "type": "Sick Leave",
        "start": "2026-09-20",
        "end": "2026-09-20",
        "status": "Approved",
        "reason": "Demam",
    },
]

LEAVE_TYPES = [
    "Annual Leave",
    "Sick Leave",
    "Emergency Leave",
    "Unpaid Leave",
    "Work From Home",
    "Business Trip",
]


class LeaveRequest(BaseModel):
    user: str
    type: str
    start: date
    end: date
    reason: str = ""


class QuotaUpdate(BaseModel):
    max_quota: int


# Helper Function: Hitung Cuti per Tanggal
def count_leaves_on_date(check_date_str: str) -> int:
    return sum(
        1
        for l in leaves
        if l["status"] in ("Approved", "Pending") and l["start"] <= check_date_str <= l["end"]
    )


# Helper Function: Cek Peringatan Bentrok (Overlap Warning)
def has_overlap_warning(start_date: date, end_date: date) -> bool:
    curr = start_date
    while curr <= end_date:
        if count_leaves_on_date(curr.strftime("%Y-%m-%d")) >= max_quota:
            return True
        curr += timedelta(days=1)
    return False


def find_leave(leave_id: int) -> dict:
    for l in leaves:
        if l["id"] == leave_id:
            return l
    raise HTTPException(status_code=404, detail="Pengajuan cuti tidak ditemukan.")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/users")
def list_users():
    return users


@app.get("/api/leave-types")
def list_leave_types():
    return LEAVE_TYPES


@app.get("/api/quota")
def get_quota():
    return {"max_quota": max_quota}


@app.put("/api/quota")
def update_quota(payload: QuotaUpdate):
    global max_quota
    if payload.max_quota < 1:
        raise HTTPException(status_code=400, detail="Batas minimal 1 orang/hari.")
    max_quota = payload.max_quota
    return {"max_quota": max_quota}


@app.get("/api/leaves")
def list_leaves(user: str | None = None, status: str | None = None):
    result = leaves
    if user:
        result = [l for l in result if l["user"] == user]
    if status:
        result = [l for l in result if l["status"] == status]
    return result


@app.get("/api/leaves/overlap")
def check_overlap(start: date, end: date):
    if start > end:
        raise HTTPException(
            status_code=400, detail="Tanggal mulai tidak boleh lebih besar dari tanggal selesai."
        )
    return {"warning": has_overlap_warning(start, end), "max_quota": max_quota}


@app.post("/api/leaves", status_code=201)
def create_leave(payload: LeaveRequest):
    if payload.start > payload.end:
        raise HTTPException(
            status_code=400, detail="Tanggal mulai tidak boleh lebih besar dari tanggal selesai."
        )
    new_leave = {
        "id": int(datetime.now().timestamp()),
        "user": payload.user,
        "manager": "Manager",
        "type": payload.type,
        "start": payload.start.strftime("%Y-%m-%d"),
        "end": payload.end.strftime("%Y-%m-%d"),
        "status": "Pending",
        "reason": payload.reason,
    }
    leaves.append(new_leave)
    return new_leave


@app.post("/api/leaves/{leave_id}/approve")
def approve_leave(leave_id: int):
    leave = find_leave(leave_id)
    leave["status"] = "Approved"
    return leave


@app.post("/api/leaves/{leave_id}/reject")
def reject_leave(leave_id: int):
    leave = find_leave(leave_id)
    leave["status"] = "Rejected"
    return leave


# Aksi Pembatalan (Untuk Pemohon jika status masih Pending)
@app.delete("/api/leaves/{leave_id}")
def cancel_leave(leave_id: int):
    leave = find_leave(leave_id)
    if leave["status"] != "Pending":
        raise HTTPException(
            status_code=400, detail="Hanya pengajuan berstatus Pending yang dapat dibatalkan."
        )
    leaves.remove(leave)
    return {"deleted": leave_id}


# Ekspor Data Cuti (CSV)
@app.get("/api/leaves/export")
def export_leaves():
    buffer = StringIO()
    writer = csv.writer(buffer)
    writer.writerow(["Employee", "Manager", "Leave Type", "Start Date", "End Date", "Status"])
    for l in leaves:
        writer.writerow([l["user"], l["manager"], l["type"], l["start"], l["end"], l["status"]])
    return Response(
        content=buffer.getvalue(),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=leave_records.csv"},
    )
