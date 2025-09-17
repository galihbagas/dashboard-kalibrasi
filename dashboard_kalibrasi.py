import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px
import os

# ===== CONFIG DASHBOARD =====
st.set_page_config(page_title="Dashboard Monitoring Kalibrasi", layout="wide")

st.title("📊 Dashboard Monitoring Kalibrasi")
st.caption("Monitoring status kalibrasi peralatan secara real-time")

# ===== LOAD DATA OTOMATIS DARI FILE =====
file_path = "sample_kalibrasi.xlsx"  # Pastikan nama file sama dengan yang ada di repo

if not os.path.exists(file_path):
    st.error(f"❗ File '{file_path}' tidak ditemukan di repository!")
    st.stop()

# Baca file
df = pd.read_excel(file_path)

# ===== CEK KOLOM =====
required_cols = ["Tanggal Kalibrasi Terakhir", "Interval (bulan)", "Lokasi", "Kategori"]
missing_cols = [col for col in required_cols if col not in df.columns]
if missing_cols:
    st.error(f"❗ File tidak memiliki kolom berikut: {', '.join(missing_cols)}")
    st.stop()

# Tambahkan Area & Plant jika tidak ada
if "Area" not in df.columns:
    df["Area"] = "Unknown"
if "Plant" not in df.columns:
    df["Plant"] = "Unknown"

# Konversi tanggal dan hitung due date
df["Tanggal Kalibrasi Terakhir"] = pd.to_datetime(df["Tanggal Kalibrasi Terakhir"], errors="coerce")
df["Due Date"] = df["Tanggal Kalibrasi Terakhir"] + pd.offsets.DateOffset(months=1) * df["Interval (bulan)"]

today = datetime.today()

def get_status(due_date):
    if pd.isna(due_date):
        return "❓ Belum Kalibrasi"
    elif due_date < today:
        return "❌ Overdue"
    elif due_date <= today + timedelta(days=30):
        return "⚠️ Due Soon"
    else:
        return "✅ On-Schedule"

df["Status"] = df["Due Date"].apply(get_status)

# ===== METRICS =====
col1, col2, col3, col4, col5 = st.columns(5)
col1.metric("Total Alat", len(df))
col2.metric("On-Schedule", len(df[df["Status"]=="✅ On-Schedule"]))
col3.metric("Due Soon", len(df[df["Status"]=="⚠️ Due Soon"]))
col4.metric("Overdue", len(df[df["Status"]=="❌ Overdue"]))
col5.metric("Belum Kalibrasi", len(df[df["Status"]=="❓ Belum Kalibrasi"]))

st.divider()

# ===== FILTER =====
c1, c2, c3, c4, c5 = st.columns([1, 1, 1, 1, 2])
lokasi_filter = c1.multiselect("Filter Lokasi", df["Lokasi"].dropna().unique())
area_filter = c2.multiselect("Filter Area", df["Area"].dropna().unique())
plant_filter = c3.multiselect("Filter Plant", df["Plant"].dropna().unique())
kategori_filter = c4.multiselect("Filter Kategori", df["Kategori"].dropna().unique())
search = c5.text_input("🔍 Cari alat (ID / Nama)")

filtered_df = df.copy()
if lokasi_filter:
    filtered_df = filtered_df[filtered_df["Lokasi"].isin(lokasi_filter)]
if area_filter:
    filtered_df = filtered_df[filtered_df["Area"].isin(area_filter)]
if plant_filter:
    filtered_df = filtered_df[filtered_df["Plant"].isin(plant_filter)]
if kategori_filter:
    filtered_df = filtered_df[filtered_df["Kategori"].isin(kategori_filter)]
if search:
    search_lower = search.lower()
    search_cols = [col for col in filtered_df.columns if "id" in col.lower() or "nama" in col.lower()]
    if search_cols:
        mask = filtered_df[search_cols].apply(lambda x: x.astype(str).str.lower().str.contains(search_lower)).any(axis=1)
        filtered_df = filtered_df[mask]

# ===== TABEL =====
st.subheader("📋 Daftar Alat")
st.dataframe(filtered_df, use_container_width=True)

# ===== VISUALISASI =====
col_a, col_b = st.columns(2)

with col_a:
    fig1 = px.bar(filtered_df.groupby("Status").size().reset_index(name="Jumlah"),
                  x="Status", y="Jumlah", title="Jumlah Alat per Status",
                  color="Status", text="Jumlah")
    st.plotly_chart(fig1, use_container_width=True)

with col_b:
    fig2 = px.pie(filtered_df, names="Lokasi", title="Distribusi Alat per Lokasi")
    st.plotly_chart(fig2, use_container_width=True)

