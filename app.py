import streamlit as st
import pandas as pd
from datetime import datetime, timedelta

# Konfigurasi Halaman
st.set_page_config(page_title="Team Leave Tracker", page_icon="📅", layout="wide")

# Inisialisasi Data Default (State Management)
if "max_quota" not in st.session_state:
    st.session_state.max_quota = 2

if "users" not in st.session_state:
    st.session_state.users = [
        {"name": "Manager", "role": "Manager"},
        {"name": "Budi Santoso", "role": "Employee"},
        {"name": "Siti Rahma", "role": "Employee"},
        {"name": "Andi Wijaya", "role": "Employee"}
    ]

if "leaves" not in st.session_state:
    st.session_state.leaves = [
        {
            "id": 1, 
            "user": "Budi Santoso", 
            "manager": "Manager",
            "type": "Annual Leave", 
            "start": "2026-09-20", 
            "end": "2026-09-22", 
            "status": "Approved", 
            "reason": "Liburan Keluarga"
        },
        {
            "id": 2, 
            "user": "Siti Rahma", 
            "manager": "Manager",
            "type": "Sick Leave", 
            "start": "2026-09-20", 
            "end": "2026-09-20", 
            "status": "Approved", 
            "reason": "Demam"
        }
    ]

# Helper Function: Hitung Cuti per Tanggal
def count_leaves_on_date(check_date_str):
    count = 0
    for l in st.session_state.leaves:
        if l["status"] in ["Approved", "Pending"]:
            if l["start"] <= check_date_str <= l["end"]:
                count += 1
    return count

# Helper Function: Cek Peringatan Bentrok (Overlap Warning)
def has_overlap_warning(start_date, end_date):
    curr = start_date
    while curr <= end_date:
        date_str = curr.strftime("%Y-%m-%d")
        if count_leaves_on_date(date_str) >= st.session_state.max_quota:
            return True
        curr += timedelta(days=1)
    return False

# Sidebar - User Switcher & Pengajuan Cuti
st.sidebar.title("📅 Team Leave Tracker")
user_names = [u["name"] for u in st.session_state.users]
current_user = st.sidebar.selectbox("Pilih Pengguna / Role:", user_names)
is_manager = (current_user == "Manager")

st.sidebar.markdown("---")
st.sidebar.subheader("Form Pengajuan Cuti")

leave_types = [
    "Annual Leave", 
    "Sick Leave", 
    "Emergency Leave", 
    "Unpaid Leave", 
    "Work From Home", 
    "Business Trip"
]

selected_type = st.sidebar.selectbox("Tipe Cuti", leave_types)
start_date = st.sidebar.date_input("Tanggal Mulai", datetime.now())
end_date = st.sidebar.date_input("Tanggal Selesai", datetime.now())
reason = st.sidebar.text_area("Alasan", placeholder="Masukkan alasan cuti...")

# Peringatan Bentrok Kuota
if start_date <= end_date and has_overlap_warning(start_date, end_date):
    st.sidebar.warning(f"⚠️ **Peringatan Bentrok:** Batas cuti harian ({st.session_state.max_quota} orang) sudah tercapai pada tanggal yang dipilih. Pengajuan tetap dapat dikirim.")

if st.sidebar.button("Kirim Pengajuan Cuti", type="primary"):
    if start_date > end_date:
        st.sidebar.error("Tanggal mulai tidak boleh lebih besar dari tanggal selesai.")
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
        st.session_state.leaves.append(new_leave)
        st.sidebar.success("Pengajuan berhasil dikirim! Menunggu persetujuan Manager.")
        st.rerun()

# Kontrol Manajer
if is_manager:
    st.sidebar.markdown("---")
    st.sidebar.subheader("⚙️ Pengaturan Manajer")
    new_quota = st.sidebar.number_input("Batas Maksimal Cuti/Hari", min_value=1, value=st.session_state.max_quota)
    if st.sidebar.button("Simpan Batas Quota"):
        st.session_state.max_quota = new_quota
        st.sidebar.success(f"Batas diperbarui: {new_quota} orang/hari")
        st.rerun()

# Layout Utama
st.title(f"Dashboard Cuti Tim — ({current_user})")

# Panel Persetujuan Manajer (Pending Approvals)
if is_manager:
    pending_leaves = [l for l in st.session_state.leaves if l["status"] == "Pending"]
    if pending_leaves:
        st.subheader("⏳ Pengajuan Cuti Menunggu Persetujuan")
        for leave in pending_leaves:
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"**{leave['user']}** — *{leave['type']}* ({leave['start']} s/d {leave['end']})")
                if leave["reason"]:
                    st.caption(f"Alasan: {leave['reason']}")
            with col2:
                if st.button("Setujui (Approve)", key=f"app_{leave['id']}"):
                    leave["status"] = "Approved"
                    st.success(f"Pengajuan {leave['user']} disetujui.")
                    st.rerun()
            with col3:
                if st.button("Tolak (Reject)", key=f"rej_{leave['id']}"):
                    leave["status"] = "Rejected"
                    st.error(f"Pengajuan {leave['user']} ditolak.")
                    st.rerun()
        st.markdown("---")

# Tampilan Jadwal / Kalender Ringkas
st.subheader("📅 Jadwal & Status Cuti Tim")

if st.session_state.leaves:
    df_leaves = pd.DataFrame(st.session_state.leaves)
    
    # Tampilan Tabel Interaktif
    st.dataframe(
        df_leaves[["user", "type", "start", "end", "status", "reason"]],
        column_config={
            "user": "Nama Karyawan",
            "type": "Tipe Cuti",
            "start": "Tanggal Mulai",
            "end": "Tanggal Selesai",
            "status": "Status Persetujuan",
            "reason": "Alasan"
        },
        use_container_width=True,
        hide_index=True
    )

    # Aksi Pembatalan (Untuk Pemohon jika status masih Pending)
    user_pending = [l for l in st.session_state.leaves if l["user"] == current_user and l["status"] == "Pending"]
    if user_pending:
        st.markdown("**Batalkan Pengajuan Anda:**")
        for p in user_pending:
            if st.button(f"Batalkan pengajuan {p['type']} ({p['start']})", key=f"can_{p['id']}"):
                st.session_state.leaves = [l for l in st.session_state.leaves if l["id"] != p["id"]]
                st.success("Pengajuan berhasil dibatalkan.")
                st.rerun()

else:
    st.info("Belum ada data pengajuan cuti.")

# Ekspor Data CSV (Khusus Manajer)
if is_manager:
    st.markdown("---")
    st.subheader("📥 Ekspor Data Cuti")
    df_export = pd.DataFrame(st.session_state.leaves)
    if not df_export.empty:
        df_export_clean = df_export.rename(columns={
            "user": "Employee",
            "manager": "Manager",
            "type": "Leave Type",
            "start": "Start Date",
            "end": "End Date",
            "status": "Status"
        })[["Employee", "Manager", "Leave Type", "Start Date", "End Date", "Status"]]
        
        csv_data = df_export_clean.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="Download Data Cuti (CSV)",
            data=csv_data,
            file_name="leave_records.csv",
            mime="text/csv"
        )