import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ─────────────────────────────────────────────
#  PAGE CONFIG
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Dashboard Target Tabungan",
    page_icon="💰",
    layout="wide",
)

# ─────────────────────────────────────────────
#  CUSTOM CSS
# ─────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=Space+Mono:wght@400;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    .main { background-color: #0f1117; }
    .block-container { padding: 2rem 3rem; }

    h1, h2, h3 { font-family: 'Plus Jakarta Sans', sans-serif; font-weight: 800; }

    /* Metric Cards */
    .metric-card {
        background: linear-gradient(135deg, #1a1f2e 0%, #252b3b 100%);
        border: 1px solid #2e3650;
        border-radius: 16px;
        padding: 1.5rem;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0,0,0,0.3);
    }
    .metric-label {
        font-size: 0.75rem;
        font-weight: 600;
        letter-spacing: 0.08em;
        text-transform: uppercase;
        color: #6b7a99;
        margin-bottom: 0.5rem;
    }
    .metric-value {
        font-family: 'Space Mono', monospace;
        font-size: 1.55rem;
        font-weight: 700;
        color: #e2e8f0;
        line-height: 1.2;
    }
    .metric-value.green { color: #34d399; }
    .metric-value.blue  { color: #60a5fa; }
    .metric-value.amber { color: #fbbf24; }

    /* Section Headers */
    .section-header {
        font-size: 1.15rem;
        font-weight: 700;
        color: #cbd5e1;
        margin: 2rem 0 1rem 0;
        border-left: 4px solid #60a5fa;
        padding-left: 0.75rem;
    }

    /* Insight Box */
    .insight-box {
        background: linear-gradient(135deg, #1e2a3a 0%, #1a2535 100%);
        border: 1px solid #2d4a6e;
        border-radius: 12px;
        padding: 1rem 1.25rem;
        margin-top: 0.75rem;
        font-size: 0.88rem;
        color: #94a3b8;
        line-height: 1.7;
    }
    .insight-box b { color: #93c5fd; }

    /* Badge */
    .badge-done {
        display: inline-block;
        background: #064e3b;
        color: #34d399;
        border-radius: 999px;
        padding: 0.1rem 0.65rem;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-left: 0.4rem;
        vertical-align: middle;
    }
    .badge-pending {
        display: inline-block;
        background: #3b1a1a;
        color: #f87171;
        border-radius: 999px;
        padding: 0.1rem 0.65rem;
        font-size: 0.7rem;
        font-weight: 700;
        letter-spacing: 0.05em;
        margin-left: 0.4rem;
        vertical-align: middle;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  LOAD & CLEAN DATA
# ─────────────────────────────────────────────
@st.cache_data
def load_data(file):
    df = pd.read_excel(file)

    # Konversi kolom tanggal (Excel Serial Number)
    if df['tanggal'].dtype in ['int64', 'float64']:
        df['tanggal'] = pd.to_datetime(df['tanggal'], unit='D', origin='1899-12-30')

    # Bersihkan kolom nominal
    cols_to_fix = ['nabung_harian', 'jumlah_terkumpul', 'jumlah_target']
    for col in cols_to_fix:
        df[col] = df[col].astype(str).str.replace(r'[^\d.]', '', regex=True)
        df[col] = pd.to_numeric(df[col], errors='coerce')

    # Hapus duplikat & kolom Unnamed
    df.columns = df.columns.str.strip()
    df.drop(columns=['Unnamed: 10', 'Unnamed: 11', 'Unnamed: 12'], inplace=True, errors='ignore')
    df.drop_duplicates(inplace=True)

    # Tambah kolom bulan
    df['bulan'] = df['tanggal'].dt.to_period('M').astype(str)

    return df


# ─────────────────────────────────────────────
#  HEADER
# ─────────────────────────────────────────────
st.markdown("""
<div style='margin-bottom:1.5rem;'>
    <h1 style='color:#e2e8f0; margin-bottom:0.2rem;'>💰 Dashboard Target Tabungan</h1>
    <p style='color:#64748b; font-size:0.9rem; margin:0;'>Analisis progres, rata-rata harian, dan estimasi pencapaian target finansial</p>
</div>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
#  UPLOAD FILE
# ─────────────────────────────────────────────
uploaded_file = st.file_uploader(
    "Upload file Excel `target tabungan.xlsx`",
    type=["xlsx", "xls"],
    help="File harus memiliki kolom: tanggal, nama_target, jumlah_target, nabung_harian, jumlah_terkumpul, progres, sisa_target, status"
)

if uploaded_file is None:
    st.info("📂 Silakan upload file Excel untuk memulai analisis.")
    st.stop()

df = load_data(uploaded_file)

# ─────────────────────────────────────────────
#  SIDEBAR — FILTER
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("### 🎯 Filter Data")

    all_targets = sorted(df['nama_target'].unique())
    selected_targets = st.multiselect(
        "Pilih Target",
        options=all_targets,
        default=all_targets,
        placeholder="Semua target..."
    )

    date_min = df['tanggal'].min().date()
    date_max = df['tanggal'].max().date()
    date_range = st.date_input(
        "Rentang Tanggal",
        value=(date_min, date_max),
        min_value=date_min,
        max_value=date_max,
    )

    st.markdown("---")
    st.markdown(f"<small style='color:#64748b;'>Total data: **{len(df):,}** baris</small>", unsafe_allow_html=True)

# Terapkan filter
if len(date_range) == 2:
    d_start, d_end = pd.Timestamp(date_range[0]), pd.Timestamp(date_range[1])
else:
    d_start, d_end = df['tanggal'].min(), df['tanggal'].max()

df_filtered = df[
    (df['nama_target'].isin(selected_targets)) &
    (df['tanggal'] >= d_start) &
    (df['tanggal'] <= d_end)
]

if df_filtered.empty:
    st.warning("⚠️ Tidak ada data yang sesuai dengan filter yang dipilih.")
    st.stop()


# ─────────────────────────────────────────────
#  SUMMARY METRICS
# ─────────────────────────────────────────────
latest_data = df_filtered.groupby('nama_target').last().reset_index()
latest_data['nominal_sisa'] = (latest_data['jumlah_target'] * latest_data['sisa_target']).clip(lower=0)

total_target       = latest_data['jumlah_target'].sum()
total_terkumpul    = latest_data['jumlah_terkumpul'].sum()
total_sisa         = latest_data['nominal_sisa'].sum()
avg_harian_global  = df_filtered['nabung_harian'].mean()
n_terpenuhi        = (latest_data['progres'] >= 1.0).sum()
n_total            = len(latest_data)

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Target</div>
        <div class="metric-value blue">Rp {total_target:,.0f}</div>
    </div>""", unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total Terkumpul</div>
        <div class="metric-value green">Rp {total_terkumpul:,.0f}</div>
    </div>""", unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Sisa Keseluruhan</div>
        <div class="metric-value amber">Rp {total_sisa:,.0f}</div>
    </div>""", unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Rata-rata Harian</div>
        <div class="metric-value">Rp {avg_harian_global:,.0f}</div>
    </div>""", unsafe_allow_html=True)

st.markdown(f"""
<div class='insight-box' style='margin-top:1rem;'>
    <b>{n_terpenuhi} dari {n_total}</b> target telah berstatus <b>TERPENUHI</b>. 
    Rata-rata tabungan harian global sebesar <b>Rp {avg_harian_global:,.0f}</b>.
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  PERTANYAAN 1 — SISA NOMINAL PER TARGET
# ─────────────────────────────────────────────
st.markdown("<div class='section-header'>📌 Pertanyaan 1 — Sisa Nominal yang Masih Harus Ditabung</div>", unsafe_allow_html=True)

latest_sorted = latest_data.sort_values('nominal_sisa', ascending=True)

colors_q1 = ['#60a5fa' if v == latest_sorted['nominal_sisa'].max() else '#334155'
             for v in latest_sorted['nominal_sisa']]

fig1 = go.Figure(go.Bar(
    x=latest_sorted['nominal_sisa'],
    y=latest_sorted['nama_target'],
    orientation='h',
    marker_color=colors_q1,
    text=[f"Rp {v:,.0f}" for v in latest_sorted['nominal_sisa']],
    textposition='outside',
    textfont=dict(size=11, color='#94a3b8'),
))
fig1.update_layout(
    title=dict(text="Sisa Nominal per Target", font=dict(size=14, color='#cbd5e1')),
    xaxis=dict(
        title="Sisa (Rp)", showgrid=True, gridcolor='#1e293b',
        tickformat=',.0f', color='#64748b',
    ),
    yaxis=dict(color='#94a3b8'),
    plot_bgcolor='#0f1117',
    paper_bgcolor='#0f1117',
    font=dict(family='Plus Jakarta Sans', color='#94a3b8'),
    margin=dict(l=10, r=120, t=50, b=40),
    height=max(350, len(latest_sorted) * 45),
)
st.plotly_chart(fig1, use_container_width=True)

st.markdown("""
<div class='insight-box'>
    <b>Insight:</b> Seluruh target yang terdaftar telah mencapai progres 100% (sisa nominal Rp 0), 
    menandakan kedisiplinan yang sangat tinggi dalam menyelesaikan target finansial. 
    Tidak ada sisa nominal yang perlu ditabung — seluruh target berstatus <b>TERPENUHI</b>.
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  PERTANYAAN 2 — RATA-RATA TABUNGAN HARIAN
# ─────────────────────────────────────────────
st.markdown("<div class='section-header'>📌 Pertanyaan 2 — Rata-rata Tabungan Harian per Target</div>", unsafe_allow_html=True)

avg_daily = df_filtered.groupby('nama_target')['nabung_harian'].mean().reset_index()
avg_daily = avg_daily.sort_values('nabung_harian', ascending=True)
global_avg = df_filtered['nabung_harian'].mean()

fig2 = go.Figure()
fig2.add_trace(go.Bar(
    x=avg_daily['nabung_harian'],
    y=avg_daily['nama_target'],
    orientation='h',
    marker=dict(
        color=avg_daily['nabung_harian'],
        colorscale='Viridis',
        showscale=False,
    ),
    text=[f"Rp {v:,.0f}" for v in avg_daily['nabung_harian']],
    textposition='outside',
    textfont=dict(size=11, color='#94a3b8'),
    name='Rata-rata Harian',
))
fig2.add_vline(
    x=global_avg,
    line_dash="dash",
    line_color="#f87171",
    annotation_text=f"Rata-rata Global: Rp {global_avg:,.0f}",
    annotation_position="top right",
    annotation_font_color="#f87171",
    annotation_font_size=11,
)
fig2.update_layout(
    title=dict(text="Rata-rata Nominal Tabungan Harian per Target", font=dict(size=14, color='#cbd5e1')),
    xaxis=dict(
        title="Rata-rata (Rp)", showgrid=True, gridcolor='#1e293b',
        tickformat=',.0f', color='#64748b',
    ),
    yaxis=dict(color='#94a3b8'),
    plot_bgcolor='#0f1117',
    paper_bgcolor='#0f1117',
    font=dict(family='Plus Jakarta Sans', color='#94a3b8'),
    margin=dict(l=10, r=150, t=50, b=40),
    height=max(350, len(avg_daily) * 45),
)
st.plotly_chart(fig2, use_container_width=True)

# Top / Bottom
top_target  = avg_daily.iloc[-1]
bot_target  = avg_daily.iloc[0]
st.markdown(f"""
<div class='insight-box'>
    <b>Insight:</b> Rata-rata tabungan harian global adalah <b>Rp {global_avg:,.0f}</b>.
    Target dengan setoran harian tertinggi adalah <b>{top_target['nama_target']}</b> (Rp {top_target['nabung_harian']:,.0f}/hari),
    sementara yang terendah adalah <b>{bot_target['nama_target']}</b> (Rp {bot_target['nabung_harian']:,.0f}/hari).
    Variasi ini menunjukkan penyesuaian alokasi berdasarkan harga barang dan urgensi waktu.
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  PERTANYAAN 3 — ESTIMASI TABUNGAN 30 HARI
# ─────────────────────────────────────────────
st.markdown("<div class='section-header'>📌 Pertanyaan 3 — Estimasi Tabungan Harian agar Target Tercapai dalam 30 Hari</div>", unsafe_allow_html=True)

est_data = latest_data.copy()
est_data['target_harian_30'] = est_data['nominal_sisa'] / 30
est_data = est_data.sort_values('target_harian_30', ascending=True)

mean_target_30 = est_data['target_harian_30'].mean()

fig3 = go.Figure(go.Bar(
    x=est_data['target_harian_30'],
    y=est_data['nama_target'],
    orientation='h',
    marker=dict(
        color=est_data['target_harian_30'],
        colorscale='Reds',
        showscale=False,
    ),
    text=[f"Rp {v:,.0f}" for v in est_data['target_harian_30']],
    textposition='outside',
    textfont=dict(size=11, color='#94a3b8'),
))
if mean_target_30 > 0:
    fig3.add_vline(
        x=mean_target_30,
        line_dash="dash",
        line_color="#60a5fa",
        annotation_text=f"Rata-rata Target: Rp {mean_target_30:,.0f}",
        annotation_position="top right",
        annotation_font_color="#60a5fa",
        annotation_font_size=11,
    )
fig3.update_layout(
    title=dict(text="Estimasi Tabungan Harian per Target (30 Hari)", font=dict(size=14, color='#cbd5e1')),
    xaxis=dict(
        title="Nominal per Hari (Rp)", showgrid=True, gridcolor='#1e293b',
        tickformat=',.0f', color='#64748b',
    ),
    yaxis=dict(color='#94a3b8'),
    plot_bgcolor='#0f1117',
    paper_bgcolor='#0f1117',
    font=dict(family='Plus Jakarta Sans', color='#94a3b8'),
    margin=dict(l=10, r=150, t=50, b=40),
    height=max(350, len(est_data) * 45),
)
st.plotly_chart(fig3, use_container_width=True)

st.markdown(f"""
<div class='insight-box'>
    <b>Insight:</b> Karena seluruh target saat ini sudah lunas (sisa nominal Rp 0), 
    kebutuhan menabung harian untuk 30 hari ke depan adalah <b>Rp 0</b>. 
    Tren akumulasi tabungan menunjukkan pertumbuhan yang stabil dan linear sejak awal periode, 
    mengonfirmasi strategi menabung harian yang efektif.
</div>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────
#  ANALISIS LANJUTAN — TREN AKUMULASI BULANAN
# ─────────────────────────────────────────────
st.markdown("<div class='section-header'>📈 Analisis Lanjutan — Tren Akumulasi Tabungan Bulanan</div>", unsafe_allow_html=True)

monthly = df_filtered.groupby('bulan').agg(
    total_nabung=('nabung_harian', 'sum'),
    rata_progres=('progres', 'mean'),
    jumlah_target=('nama_target', 'nunique'),
).reset_index()

tab1, tab2 = st.tabs(["💵 Total Tabungan per Bulan", "📊 Rata-rata Progres per Bulan"])

with tab1:
    fig_m1 = px.area(
        monthly,
        x='bulan',
        y='total_nabung',
        labels={'bulan': 'Bulan', 'total_nabung': 'Total Tabungan (Rp)'},
        color_discrete_sequence=['#60a5fa'],
    )
    fig_m1.update_traces(
        fill='tozeroy',
        line=dict(width=2),
        fillcolor='rgba(96, 165, 250, 0.15)',
    )
    fig_m1.update_layout(
        plot_bgcolor='#0f1117', paper_bgcolor='#0f1117',
        font=dict(family='Plus Jakarta Sans', color='#94a3b8'),
        xaxis=dict(showgrid=False, color='#64748b', tickangle=-45),
        yaxis=dict(showgrid=True, gridcolor='#1e293b', tickformat=',.0f', color='#64748b'),
        margin=dict(l=10, r=10, t=20, b=40),
        height=350,
    )
    st.plotly_chart(fig_m1, use_container_width=True)

with tab2:
    fig_m2 = px.line(
        monthly,
        x='bulan',
        y='rata_progres',
        markers=True,
        labels={'bulan': 'Bulan', 'rata_progres': 'Rata-rata Progres'},
        color_discrete_sequence=['#34d399'],
    )
    fig_m2.update_layout(
        plot_bgcolor='#0f1117', paper_bgcolor='#0f1117',
        font=dict(family='Plus Jakarta Sans', color='#94a3b8'),
        xaxis=dict(showgrid=False, color='#64748b', tickangle=-45),
        yaxis=dict(
            showgrid=True, gridcolor='#1e293b', color='#64748b',
            tickformat='.0%', range=[0, 1.1],
        ),
        margin=dict(l=10, r=10, t=20, b=40),
        height=350,
    )
    st.plotly_chart(fig_m2, use_container_width=True)


# ─────────────────────────────────────────────
#  TABEL DETAIL PER TARGET
# ─────────────────────────────────────────────
st.markdown("<div class='section-header'>📋 Detail Status per Target</div>", unsafe_allow_html=True)

table_df = latest_data[['nama_target', 'jumlah_target', 'jumlah_terkumpul', 'nominal_sisa', 'progres', 'status']].copy()
table_df.columns = ['Nama Target', 'Jumlah Target (Rp)', 'Terkumpul (Rp)', 'Sisa (Rp)', 'Progres', 'Status']

table_df['Progres'] = (table_df['Progres'] * 100).round(1).astype(str) + '%'
for col in ['Jumlah Target (Rp)', 'Terkumpul (Rp)', 'Sisa (Rp)']:
    table_df[col] = table_df[col].apply(lambda x: f"Rp {x:,.0f}")

st.dataframe(
    table_df.reset_index(drop=True),
    use_container_width=True,
    hide_index=True,
)


# ─────────────────────────────────────────────
#  CONCLUSION & RECOMMENDATION
# ─────────────────────────────────────────────
st.markdown("<div class='section-header'>✅ Kesimpulan & Rekomendasi</div>", unsafe_allow_html=True)

col_c1, col_c2 = st.columns(2)
with col_c1:
    st.markdown("""
    <div class='insight-box'>
        <b>Kesimpulan:</b><br>
        • <b>Pertanyaan 1:</b> Seluruh target telah mencapai progres 100%. Tidak ada sisa nominal yang perlu ditabung — semua berstatus <i>TERPENUHI</i>.<br><br>
        • <b>Pertanyaan 2:</b> Rata-rata tabungan harian global sebesar <b>Rp 230.306/hari</b>. Variasi terjadi karena penyesuaian alokasi berdasarkan harga dan urgensi waktu.<br><br>
        • <b>Pertanyaan 3:</b> Karena semua target sudah lunas, kebutuhan harian untuk 30 hari ke depan adalah <b>Rp 0</b>.
    </div>
    """, unsafe_allow_html=True)

with col_c2:
    st.markdown("""
    <div class='insight-box'>
        <b>Rekomendasi:</b><br>
        • <b>Optimalisasi Alokasi:</b> Pertahankan kedisiplinan menyisihkan dana harian ~Rp 230.000 untuk target baru yang nominalnya besar.<br><br>
        • <b>Prioritas Target:</b> Fokus lebih pada target dengan sisa nominal paling tinggi agar tercapai sesuai estimasi.<br><br>
        • <b>Dana Cadangan:</b> Siapkan "tabungan ekstra" untuk menutupi kekurangan jika setoran harian terhenti karena kebutuhan mendesak.<br><br>
        • <b>Otomasi:</b> Manfaatkan sistem digital untuk mencatat otomatis setiap setoran agar progres bisa dipantau secara real-time.
    </div>
    """, unsafe_allow_html=True)

# Footer
st.markdown("""
<hr style='border-color:#1e293b; margin-top:2rem;'/>
<p style='text-align:center; color:#334155; font-size:0.78rem; margin-bottom:0;'>
    Dashboard Target Tabungan • Dibuat dengan Streamlit & Plotly
</p>
""", unsafe_allow_html=True)