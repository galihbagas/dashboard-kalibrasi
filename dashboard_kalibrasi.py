import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import plotly.express as px

# ===== CONFIG DASHBOARD =====
st.set_page_config(page_title="Dashboard Monitoring Kalibrasi", layout="wide")

st.title("📊 Dashboard Monitoring Kalibrasi")
st.caption("Monitoring status kalibrasi peralatan secara real-time")

# ===== UPLOAD DATA =====
uploaded_file = st.file_uploader("📂 Upload Data Kalibrasi (Excel/CSV)", type=["xlsx", "csv"])

if uploaded_file:
    # Baca file
    if uploaded_file.name.endswith(".csv"):
        df = pd.read_csv(uploaded_file)
    else:
        df = pd.read_excel(uploaded_file)

    # Pastikan kolom yang dibutuhkan ada
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

    # Konversi tanggal
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

    # ===== UPDATE TANGGAL KALIBRASI =====
    st.subheader("🛠️ Update Tanggal Kalibrasi")
    alat_list = df["ID Alat"].astype(str) + " - " + df["Nama Alat"].astype(str)
    selected_alat = st.selectbox("Pilih Alat", options=alat_list)

    if selected_alat:
        selected_id = selected_alat.split(" - ")[0]
        new_date = st.date_input("Pilih Tanggal Kalibrasi Baru", value=datetime.today())
        if st.button("✅ Update Tanggal"):
            df.loc[df["ID Alat"] == selected_id, "Tanggal Kalibrasi Terakhir"] = pd.to_datetime(new_date)
            df["Due Date"] = df["Tanggal Kalibrasi Terakhir"] + pd.offsets.DateOffset(months=1) * df["Interval (bulan)"]
            df["Status"] = df["Due Date"].apply(get_status)
            st.success(f"Tanggal kalibrasi untuk {selected_alat} berhasil diperbarui!")

            # Simpan hasil update ke file baru
            updated_file = "Data_Kalibrasi_Updated.xlsx"
            df.to_excel(updated_file, index=False)
            st.download_button("💾 Download Data Terbaru", data=open(updated_file, "rb").read(), file_name=updated_file)

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

else:
    st.info("📥 Silakan upload file Excel/CSV untuk menampilkan dashboard.")
