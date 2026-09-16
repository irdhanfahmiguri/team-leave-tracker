import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime, timedelta

st.set_page_config(page_title="Team Leave Tracker", page_icon="📅", layout="wide")

DATA_FILE = "data.json"

# Fungsi untuk membaca data dari file JSON
def load_data():
    if not os.path.exists(DATA_FILE):
        initial_data = {
            "max_quota": 2,
            "users": [
                {"name": "Manager", "role": "Manager"},
                {"name": "Budi Santoso", "role": "Employee"},
                {"name": "Siti Rahma", "role": "Employee"},
                {"name": "Andi Wijaya", "role": "Employee"}
            ],
            "leaves": [
                {
                    "id": 1,
                    "user": "Budi Santoso",
                    "manager": "Manager",
                    "type": "Annual Leave",
                    "start": "2026-09-20",
                    "end": "2026-09-22",
                    "status": "Approved",
                    "reason": "Liburan Keluarga"
                }
            ]
        }
        save_data(initial_data)
        return initial_data
    with open(DATA_FILE, "r") as f:
        return json.load(f)

# Fungsi untuk menyimpan perubahan data ke file JSON
def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

# Load data aplikasi
db = load_data()

# Helper Functions
def count_leaves_on_date(check_date_str):
    return sum(1 for l in db["leaves"] if l["status"] in ["Approved", "Pending"] and l["start"] <= check_date_str <= l["end"])

def has_overlap_warning(start_date, end_date):
    curr = start_date
    while curr <= end_date:
        if count_leaves_on_date(curr.strftime("%Y-%m-%d")) >= db["max_quota"]:
            return True
        curr += timedelta(days=1)
    return False

# Sidebar - Navigasi User
st.sidebar.title("📅 Team Leave Tracker")
user_names = [u["name"] for u in db["users"]]
current_user = st.sidebar.selectbox("Pilih Pengguna / Role:", user_names)
is_manager = (current_user == "Manager")

st.sidebar.markdown("---")
st.sidebar.subheader("Form Pengajuan Cuti")

leave_types = ["Annual Leave", "Sick Leave", "Emergency Leave", "Unpaid Leave", "Work From Home", "Business Trip"]
selected_type = st.sidebar.selectbox("Tipe Cuti", leave_types)
start_date = st.sidebar.date_input("Tanggal Mulai", datetime.now())
end_date = st.sidebar.date_input("Tanggal Selesai", datetime.now())
reason = st.sidebar.text_area("Alasan", placeholder="Masukkan alasan cuti...")

if start_date <= end_date and has_overlap_warning(start_date, end_date):
    st.sidebar.warning(f"⚠️ **Peringatan Bentrok:** Kuota cuti harian ({db['max_quota']} orang) sudah penuh pada tanggal tersebut.")

if st.sidebar.button("Kirim Pengajuan Cuti", type="primary"):
    if start_date > end_date:
        st.sidebar.error("Tanggal mulai tidak boleh melebihi tanggal selesai.")
    else:
        new_leave = {
            "id": int(datetime.now().timestamp()),
            "user": current_user,
            "manager": "Manager",
            "type": selected_type,
            "start": start_date.strftime("%Y-%m-%d"),
            "end": end_date.strftime("%Y-%m-%d"),
            "status": "Pending",
            "reason": reason
        }
        db["leaves"].append(new_leave)
        save_data(db)
        st.sidebar.success("Pengajuan berhasil terkirim!")
        st.rerun()

# Sidebar Khusus Manajer (Kelola Kuota & Anggota)
if is_manager:
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Pengaturan Manajer")
    
    # Kelola Kuota
    new_quota = st.sidebar.number_input("Batas Maksimal Cuti/Hari", min_value=1, value=db["max_quota"])
    if st.sidebar.button("Simpan Batas Quota"):
        db["max_quota"] = new_quota
        save_data(db)
        st.sidebar.success("Batas quota diperbarui!")
        st.rerun()
        
    # Tambah Karyawan Baru
    st.sidebar.markdown("**Tambah Anggota Tim Baru:**")
    new_emp_name = st.sidebar.text_input("Nama Karyawan Baru")
    if st.sidebar.button("Tambah Karyawan"):
        if new_emp_name and new_emp_name not in user_names:
            db["users"].append({"name": new_emp_name, "role": "Employee"})
            save_data(db)
            st.sidebar.success(f"{new_emp_name} berhasil ditambahkan!")
            st.rerun()

# Dashboard Utama
st.title(f"Dashboard Cuti Tim — ({current_user})")

# Panel Persetujuan Manajer
if is_manager:
    pending_leaves = [l for l in db["leaves"] if l["status"] == "Pending"]
    if pending_leaves:
        st.subheader("⏳ Pengajuan Menunggu Persetujuan")
        for leave in pending_leaves:
            c1, c2, c3 = st.columns([3, 1, 1])
            with c1:
                st.write(f"**{leave['user']}** — *{leave['type']}* ({leave['start']} s/d {leave['end']})")
                if leave["reason"]: st.caption(f"Alasan: {leave['reason']}")
            with c2:
                if st.button("Setujui", key=f"app_{leave['id']}"):
                    leave["status"] = "Approved"
                    save_data(db)
                    st.rerun()
            with c3:
                if st.button("Tolak", key=f"rej_{leave['id']}"):
                    leave["status"] = "Rejected"
                    save_data(db)
                    st.rerun()
        st.markdown("---")

# Tabel Riwayat & Kalender
st.subheader("📅 Jadwal & Status Cuti Tim")
if db["leaves"]:
    df = pd.DataFrame(db["leaves"])
    st.dataframe(
        df[["user", "type", "start", "end", "status", "reason"]],
        column_config={
            "user": "Nama Karyawan", "type": "Tipe Cuti", 
            "start": "Tgl Mulai", "end": "Tgl Selesai", 
            "status": "Status", "reason": "Alasan"
        },
        use_container_width=True, hide_index=True
    )
else:
    st.info("Belum ada pengajuan cuti.")

# Ekspor CSV
if is_manager and db["leaves"]:
    st.markdown("---")
    df_export = pd.DataFrame(db["leaves"]).rename(columns={
        "user": "Employee", "manager": "Manager", "type": "Leave Type",
        "start": "Start Date", "end": "End Date", "status": "Status"
    })[["Employee", "Manager", "Leave Type", "Start Date", "End Date", "Status"]]
    st.download_button("📥 Download Data Cuti (CSV)", df_export.to_csv(index=False).encode('utf-8'), "leave_records.csv", "text/csv")