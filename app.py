"""
CogniPace AI — Asisten Manajemen Beban Kognitif Mahasiswa
==========================================================
Tech Stack : Streamlit + Pandas + Ollama (phi3)
Fitur baru :
  - CSV dinamis (deteksi kolom otomatis)
  - Kalender interaktif JS (navigasi bulan, klik tanggal → detail tugas)
  - Tabel prioritas tugas berwarna
  - Jadwal harian AI (JSON terstruktur)
"""

import re
import json
import calendar
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import date, datetime

try:
    import ollama
    OLLAMA_TERSEDIA = True
except ImportError:
    OLLAMA_TERSEDIA = False


# ─────────────────────────────────────────────
# KONFIGURASI HALAMAN
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="CogniPace AI",
    page_icon="🧠",
    layout="wide",
)


# ═══════════════════════════════════════════════
# BAGIAN 1: DETEKSI KOLOM CSV DINAMIS
# ═══════════════════════════════════════════════

# Alias: nama kolom (lowercase) → nama internal standar
ALIAS_KOLOM = {
    # nama tugas
    "nama tugas": "tugas", "tugas": "tugas", "assignment": "tugas",
    "task": "tugas", "kerjaan": "tugas", "pekerjaan": "tugas",
    "kegiatan": "tugas", "nama pekerjaan": "tugas",
    # mata kuliah
    "mata kuliah": "matkul", "matkul": "matkul", "subject": "matkul",
    "course": "matkul", "pelajaran": "matkul", "kuliah": "matkul",
    "kelas": "matkul", "mapel": "matkul", "nama matkul": "matkul",
    # deadline
    "deadline": "deadline", "due date": "deadline", "due_date": "deadline",
    "batas waktu": "deadline", "tanggal deadline": "deadline",
    "tgl deadline": "deadline", "tanggal akhir": "deadline",
    "akhir": "deadline", "jatuh tempo": "deadline", "tgl akhir": "deadline",
    # status
    "status": "status", "kondisi": "status", "state": "status",
    "keterangan": "status",
    # tanggal diberikan (opsional)
    "tanggal diberikan": "tgl_mulai", "tanggal mulai": "tgl_mulai",
    "start": "tgl_mulai", "mulai": "tgl_mulai", "tgl diberikan": "tgl_mulai",
}


def deteksi_dan_normalisasi(df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    """
    Mendeteksi kolom CSV secara otomatis berdasarkan alias.
    Mengembalikan:
      - df_norm : DataFrame dengan kolom internal standar
      - mapping : dict {nama_kolom_asli: nama_internal}
    Kolom yang tidak dikenali tetap dipertahankan apa adanya.
    """
    mapping = {}
    rename_dict = {}

    for col in df.columns:
        key = col.strip().lower()
        if key in ALIAS_KOLOM:
            internal = ALIAS_KOLOM[key]
            # Hindari duplikat jika dua kolom map ke internal yang sama
            if internal not in rename_dict.values():
                rename_dict[col] = internal
                mapping[col] = internal

    df_norm = df.rename(columns=rename_dict)
    return df_norm, mapping


def kolom_ada(df: pd.DataFrame, nama: str) -> bool:
    """Cek apakah kolom internal ada di DataFrame."""
    return nama in df.columns


# ═══════════════════════════════════════════════
# BAGIAN 2: PEMROSESAN DATA
# ═══════════════════════════════════════════════

def parse_deadline(df: pd.DataFrame) -> pd.DataFrame:
    """
    Parse kolom 'deadline' ke datetime dengan berbagai format.
    Baris tanpa deadline yang valid dibuang.
    """
    if not kolom_ada(df, "deadline"):
        return df
    df = df.copy()
    df["deadline"] = pd.to_datetime(df["deadline"], format="mixed", dayfirst=True, errors="coerce")
    df = df.dropna(subset=["deadline"])
    return df


def filter_aktif(df: pd.DataFrame) -> pd.DataFrame:
    """
    Jika ada kolom 'status', filter hanya yang belum selesai.
    Jika tidak ada kolom status, anggap semua tugas aktif.
    """
    if not kolom_ada(df, "status"):
        return df
    selesai_kata = {"selesai", "done", "complete", "completed", "finished", "sudah"}
    mask = ~df["status"].str.strip().str.lower().isin(selesai_kata)
    return df[mask]


def hitung_beban(df: pd.DataFrame) -> dict:
    """
    Mengembalikan dict {date_str (ISO): {jumlah, tugas:[{tugas, matkul, deadline, status}]}}
    Digunakan untuk kalender JS.
    """
    df_aktif = filter_aktif(parse_deadline(df))
    beban = {}

    for _, row in df_aktif.iterrows():
        d = row["deadline"].date()
        key = str(d)  # format ISO untuk JSON/JS

        # Ambil nilai kolom opsional dengan fallback
        nama_tugas = str(row.get("tugas", "Tugas"))
        nama_matkul = str(row.get("matkul", "—"))
        status_val = str(row.get("status", "Aktif"))

        if key not in beban:
            beban[key] = {"jumlah": 0, "tugas": []}
        beban[key]["jumlah"] += 1
        beban[key]["tugas"].append({
            "tugas": nama_tugas,
            "matkul": nama_matkul,
            "deadline": key,
            "status": status_val,
        })

    return beban


def buat_tabel_prioritas(df: pd.DataFrame) -> pd.DataFrame:
    """
    Menyusun tabel prioritas tugas berdasarkan:
    skor = hari_tersisa − (tugas_bertumpuk × 0.5)
    Skor lebih kecil = prioritas lebih tinggi.
    """
    df_aktif = filter_aktif(parse_deadline(df))
    if df_aktif.empty:
        return pd.DataFrame()

    today = date.today()
    df_aktif = df_aktif.copy()

    df_aktif["hari_tersisa"] = df_aktif["deadline"].dt.date.apply(
        lambda d: (d - today).days
    )
    beban_per_hari = df_aktif.groupby(df_aktif["deadline"].dt.date).size()
    df_aktif["bertumpuk"] = df_aktif["deadline"].dt.date.map(beban_per_hari)
    df_aktif["skor"] = df_aktif["hari_tersisa"] - (df_aktif["bertumpuk"] * 0.5)

    def label_urgensi(hari):
        if hari < 0:   return "🔴 Terlambat"
        elif hari <= 2: return "🔴 Kritis"
        elif hari <= 5: return "🟠 Mendesak"
        elif hari <= 10: return "🟡 Perhatikan"
        else:           return "🟢 Aman"

    df_aktif["Urgensi"] = df_aktif["hari_tersisa"].apply(label_urgensi)

    df_out = df_aktif.sort_values("skor").reset_index(drop=True)
    df_out.index += 1

    # Siapkan kolom output (fleksibel sesuai kolom yang tersedia)
    kolom_output = {}
    if kolom_ada(df_out, "matkul"):   kolom_output["matkul"] = "Mata Kuliah"
    if kolom_ada(df_out, "tugas"):    kolom_output["tugas"] = "Nama Tugas"
    kolom_output["deadline"] = "Deadline"
    kolom_output["hari_tersisa"] = "Hari Tersisa"
    kolom_output["bertumpuk"] = "Bertumpuk"
    kolom_output["Urgensi"] = "Urgensi"

    df_out["deadline"] = df_out["deadline"].dt.strftime("%d %b %Y")

    cols_ada = [c for c in kolom_output.keys() if c in df_out.columns]
    return df_out[cols_ada].rename(columns={c: kolom_output[c] for c in cols_ada})


# ═══════════════════════════════════════════════
# BAGIAN 3: AI — OLLAMA
# ═══════════════════════════════════════════════

def panggil_ollama(df_raw: pd.DataFrame, mapping: dict) -> str:
    """
    Mengirim data ke phi3. Prompt adaptif berdasarkan kolom yang tersedia.
    """
    deskripsi_kolom = ", ".join([f"'{k}' (berarti {v})" for k, v in mapping.items()])
    data_str = df_raw.to_csv(index=False)

    prompt = f"""Kamu adalah AI Asisten Akademik yang membantu mahasiswa mengelola beban studi.

Data tugas mahasiswa (format CSV):
{data_str}

Kolom yang terdeteksi: {deskripsi_kolom}

Catatan: kolom mungkin tidak lengkap. Gunakan kolom yang ada sebaik mungkin.

Jawab dalam Bahasa Indonesia. Lakukan tepat tiga hal:

1. Prediksi skor beban kognitif (1-10, di mana 10 = sangat berat).
   Tulis HANYA angkanya: <skor>7</skor>

2. Buat rekomendasi Actionable Plan harian sebagai JSON array:
   <jadwal>[
     {{"hari_ke": 1, "tanggal": "YYYY-MM-DD", "fokus": "nama tugas", "matkul": "nama matkul", "durasi_jam": 2, "catatan": "tips pengerjaan"}},
     {{"hari_ke": 2, "tanggal": "YYYY-MM-DD", "fokus": "nama tugas", "matkul": "nama matkul", "durasi_jam": 3, "catatan": "tips pengerjaan"}}
   ]</jadwal>

3. Berikan ringkasan analisis beban dan tips manajemen waktu singkat:
   <analisis>ringkasan di sini</analisis>
"""
    response = ollama.chat(
        model="phi3",
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]


def ekstrak_tag(teks: str, tag: str) -> str:
    """Mengambil konten di antara <tag>...</tag>."""
    pola = rf"<{tag}>(.*?)</{tag}>"
    hasil = re.search(pola, teks, re.DOTALL)
    return hasil.group(1).strip() if hasil else ""


def parse_jadwal_json(respons_ai: str) -> pd.DataFrame | None:
    """Parse tag <jadwal> dari respons AI menjadi DataFrame."""
    teks = ekstrak_tag(respons_ai, "jadwal")
    if not teks:
        return None
    try:
        teks = re.sub(r"```json|```", "", teks).strip()
        data = json.loads(teks)
        return pd.DataFrame(data)
    except Exception:
        return None


# ═══════════════════════════════════════════════
# BAGIAN 4: KALENDER INTERAKTIF (HTML + JS)
# ═══════════════════════════════════════════════

def render_kalender_interaktif(beban_json: str, tahun_awal: int, bulan_awal: int) -> str:
    """
    Menghasilkan satu komponen HTML/JS berisi kalender penuh:
    - Navigasi prev/next bulan (tanpa reload Streamlit)
    - Klik tanggal → modal popup berisi daftar tugas & deadline
    - Heatmap warna berdasarkan jumlah tugas
    - Highlight hari ini
    """
    return f"""
<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: transparent; padding: 8px; }}

  /* ── Header navigasi ── */
  .cal-nav {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 16px;
  }}
  .cal-nav button {{
    background: #4a90d9; color: white; border: none; border-radius: 8px;
    padding: 8px 18px; font-size: 1rem; cursor: pointer; transition: background 0.2s;
  }}
  .cal-nav button:hover {{ background: #2c6fad; }}
  .cal-nav .month-label {{
    font-size: 1.3rem; font-weight: 700; color: #1a1a2e; letter-spacing: 0.02em;
  }}

  /* ── Grid kalender ── */
  .cal-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 5px;
  }}
  .cal-header-cell {{
    text-align: center; font-size: 0.72rem; font-weight: 700;
    color: #888; padding: 6px 0; text-transform: uppercase; letter-spacing: 0.05em;
  }}

  /* ── Sel hari ── */
  .cal-cell {{
    border-radius: 10px;
    min-height: 78px;
    padding: 7px 6px;
    position: relative;
    font-size: 0.72rem;
    transition: transform 0.15s, box-shadow 0.15s;
    border: 2px solid transparent;
  }}
  .cal-cell.has-task {{ cursor: pointer; }}
  .cal-cell.has-task:hover {{
    transform: translateY(-2px);
    box-shadow: 0 4px 14px rgba(0,0,0,0.15);
    border-color: #4a90d9;
  }}
  .cal-cell.empty {{ background: transparent; }}
  .cal-cell.no-task {{ background: #f4f5f7; color: #bbb; }}
  .cal-cell.load-1 {{ background: #fff8e1; }}
  .cal-cell.load-2 {{ background: #ffe0b2; }}
  .cal-cell.load-3 {{ background: #ffccbc; }}
  .cal-cell.load-4 {{ background: #ef9a9a; }}
  .cal-cell.load-5plus {{ background: #e53935; color: white; }}

  /* Hari ini */
  .cal-cell.today {{ outline: 3px solid #1976d2; outline-offset: -2px; }}
  .cal-cell.today .day-num {{ color: #1976d2; }}

  .day-num {{
    font-weight: 700; font-size: 0.9rem; margin-bottom: 5px;
    display: flex; justify-content: space-between; align-items: flex-start;
  }}
  .task-badge {{
    background: rgba(0,0,0,0.15); border-radius: 20px;
    padding: 0 6px; font-size: 0.65rem; font-weight: 700;
    line-height: 1.6;
  }}
  .load-5plus .task-badge {{ background: rgba(255,255,255,0.3); color: white; }}
  .task-chip {{
    display: block;
    background: rgba(0,0,0,0.08);
    border-radius: 4px; padding: 2px 5px; margin-top: 3px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    font-size: 0.63rem; max-width: 100%;
  }}
  .load-5plus .task-chip {{ background: rgba(255,255,255,0.2); color: white; }}

  /* ── Legend ── */
  .legend {{
    display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;
    margin-top: 14px; font-size: 0.72rem; color: #555;
  }}
  .leg-item {{ display: flex; align-items: center; gap: 5px; }}
  .leg-box {{
    width: 14px; height: 14px; border-radius: 4px;
    flex-shrink: 0; border: 1px solid rgba(0,0,0,0.1);
  }}

  /* ── Modal ── */
  .modal-overlay {{
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.5); z-index: 1000;
    align-items: center; justify-content: center;
  }}
  .modal-overlay.active {{ display: flex; }}
  .modal-box {{
    background: white; border-radius: 16px; padding: 24px;
    max-width: 480px; width: 90%; max-height: 80vh; overflow-y: auto;
    box-shadow: 0 20px 60px rgba(0,0,0,0.3);
    animation: slideUp 0.25s ease;
  }}
  @keyframes slideUp {{
    from {{ transform: translateY(30px); opacity: 0; }}
    to   {{ transform: translateY(0); opacity: 1; }}
  }}
  .modal-date {{
    font-size: 1.1rem; font-weight: 700; color: #1a1a2e; margin-bottom: 4px;
  }}
  .modal-count {{
    font-size: 0.8rem; color: #888; margin-bottom: 16px;
  }}
  .task-card {{
    background: #f8f9fa; border-radius: 10px; padding: 12px 14px;
    margin-bottom: 10px; border-left: 4px solid #4a90d9;
  }}
  .task-card .tc-name {{ font-weight: 700; font-size: 0.9rem; color: #1a1a2e; }}
  .task-card .tc-meta {{
    font-size: 0.78rem; color: #666; margin-top: 5px;
    display: flex; gap: 12px; flex-wrap: wrap;
  }}
  .task-card .tc-meta span {{ display: flex; align-items: center; gap: 4px; }}
  .status-badge {{
    display: inline-block; padding: 2px 8px; border-radius: 20px;
    font-size: 0.68rem; font-weight: 600; margin-top: 6px;
  }}
  .status-aktif   {{ background: #fff3e0; color: #e65100; }}
  .status-selesai {{ background: #e8f5e9; color: #2e7d32; }}
  .modal-close {{
    width: 100%; margin-top: 16px; padding: 10px;
    background: #f0f0f0; border: none; border-radius: 8px;
    font-size: 0.9rem; cursor: pointer; color: #333;
    transition: background 0.2s;
  }}
  .modal-close:hover {{ background: #e0e0e0; }}
</style>
</head>
<body>

<!-- ── Navigasi bulan ── -->
<div class="cal-nav">
  <button onclick="gantibulan(-1)">&#8592; Prev</button>
  <span class="month-label" id="label-bulan"></span>
  <button onclick="gantibulan(1)">Next &#8594;</button>
</div>

<!-- ── Grid kalender ── -->
<div class="cal-grid" id="cal-grid"></div>

<!-- ── Legend ── -->
<div class="legend">
  <div class="leg-item"><div class="leg-box" style="background:#f4f5f7"></div>Bebas</div>
  <div class="leg-item"><div class="leg-box" style="background:#fff8e1"></div>1 tugas</div>
  <div class="leg-item"><div class="leg-box" style="background:#ffe0b2"></div>2 tugas</div>
  <div class="leg-item"><div class="leg-box" style="background:#ffccbc"></div>3 tugas</div>
  <div class="leg-item"><div class="leg-box" style="background:#ef9a9a"></div>4 tugas</div>
  <div class="leg-item"><div class="leg-box" style="background:#e53935"></div>5+ tugas 🔴</div>
  <div class="leg-item">
    <div class="leg-box" style="background:white;outline:3px solid #1976d2;outline-offset:-2px"></div>
    Hari Ini
  </div>
</div>

<!-- ── Modal popup ── -->
<div class="modal-overlay" id="modal" onclick="tutupModal(event)">
  <div class="modal-box" id="modal-box">
    <div class="modal-date" id="modal-date"></div>
    <div class="modal-count" id="modal-count"></div>
    <div id="modal-tasks"></div>
    <button class="modal-close" onclick="tutupModalLangsung()">✕ Tutup</button>
  </div>
</div>

<script>
// ── Data beban dari Python ────────────────────
const BEBAN = {beban_json};

// ── State kalender ───────────────────────────
let tahunSekarang = {tahun_awal};
let bulanSekarang = {bulan_awal};  // 0-indexed untuk JS Date

const NAMA_BULAN = [
  "Januari","Februari","Maret","April","Mei","Juni",
  "Juli","Agustus","September","Oktober","November","Desember"
];
const NAMA_HARI = ["Min","Sen","Sel","Rab","Kam","Jum","Sab"];

// ── Render kalender ───────────────────────────
function renderKalender() {{
  const grid = document.getElementById("cal-grid");
  const label = document.getElementById("label-bulan");
  grid.innerHTML = "";

  label.textContent = NAMA_BULAN[bulanSekarang] + " " + tahunSekarang;

  // Header hari
  // Grid dimulai Senin (1), perlu reorder: Mon=0..Sun=6
  const headerUrutan = ["Sen","Sel","Rab","Kam","Jum","Sab","Min"];
  headerUrutan.forEach(h => {{
    const el = document.createElement("div");
    el.className = "cal-header-cell";
    el.textContent = h;
    grid.appendChild(el);
  }});

  const hari1 = new Date(tahunSekarang, bulanSekarang, 1);
  const totalHari = new Date(tahunSekarang, bulanSekarang + 1, 0).getDate();
  const today = new Date();

  // hari1.getDay(): 0=Min,1=Sen,...,6=Sab
  // Grid Senin-pertama: offset = (getDay()+6)%7
  const offset = (hari1.getDay() + 6) % 7;

  // Sel kosong sebelum hari 1
  for (let i = 0; i < offset; i++) {{
    const el = document.createElement("div");
    el.className = "cal-cell empty";
    grid.appendChild(el);
  }}

  // Render tiap hari
  for (let d = 1; d <= totalHari; d++) {{
    const dateObj = new Date(tahunSekarang, bulanSekarang, d);
    const dateKey = formatTanggal(tahunSekarang, bulanSekarang + 1, d); // YYYY-MM-DD
    const info = BEBAN[dateKey];
    const jumlah = info ? info.jumlah : 0;

    const el = document.createElement("div");

    // Tentukan kelas warna heatmap
    let kelasWarna = "no-task";
    if (jumlah === 1) kelasWarna = "load-1";
    else if (jumlah === 2) kelasWarna = "load-2";
    else if (jumlah === 3) kelasWarna = "load-3";
    else if (jumlah === 4) kelasWarna = "load-4";
    else if (jumlah >= 5) kelasWarna = "load-5plus";

    el.className = "cal-cell " + kelasWarna;
    if (jumlah > 0) el.classList.add("has-task");

    // Highlight hari ini
    const isToday = (d === today.getDate() &&
                     bulanSekarang === today.getMonth() &&
                     tahunSekarang === today.getFullYear());
    if (isToday) el.classList.add("today");

    // Isi sel: nomor + badge + chip tugas
    let badgeHtml = jumlah > 0
      ? `<span class="task-badge">${{jumlah}}</span>` : "";

    let chipsHtml = "";
    if (info) {{
      const tampil = info.tugas.slice(0, 2);
      tampil.forEach(t => {{
        const nama = t.tugas.length > 16 ? t.tugas.slice(0,16)+"…" : t.tugas;
        chipsHtml += `<span class="task-chip">📌 ${{nama}}</span>`;
      }});
      if (info.tugas.length > 2) {{
        chipsHtml += `<span class="task-chip">+${{info.tugas.length - 2}} lagi...</span>`;
      }}
    }}

    el.innerHTML = `
      <div class="day-num"><span>${{d}}</span>${{badgeHtml}}</div>
      ${{chipsHtml}}
    `;

    // Event klik untuk modal
    if (jumlah > 0) {{
      el.addEventListener("click", () => bukaModal(dateKey, info));
    }}

    grid.appendChild(el);
  }}
}}

// ── Format tanggal ke YYYY-MM-DD ─────────────
function formatTanggal(y, m, d) {{
  return y + "-" +
    String(m).padStart(2,"0") + "-" +
    String(d).padStart(2,"0");
}}

// ── Navigasi bulan ────────────────────────────
function gantibulan(arah) {{
  bulanSekarang += arah;
  if (bulanSekarang < 0)  {{ bulanSekarang = 11; tahunSekarang--; }}
  if (bulanSekarang > 11) {{ bulanSekarang = 0;  tahunSekarang++; }}
  renderKalender();
}}

// ── Modal: buka ───────────────────────────────
function bukaModal(dateKey, info) {{
  const [y, m, d] = dateKey.split("-").map(Number);
  const namaHari = ["Minggu","Senin","Selasa","Rabu","Kamis","Jumat","Sabtu"];
  const namaBulan = ["Jan","Feb","Mar","Apr","Mei","Jun",
                     "Jul","Agu","Sep","Okt","Nov","Des"];
  const hariIdx = new Date(y, m-1, d).getDay();

  document.getElementById("modal-date").textContent =
    namaHari[hariIdx] + ", " + d + " " + namaBulan[m-1] + " " + y;
  document.getElementById("modal-count").textContent =
    info.jumlah + " tugas jatuh tempo hari ini";

  let html = "";
  info.tugas.forEach((t, i) => {{
    const statusKelas = (t.status.toLowerCase().includes("selesai") ||
                         t.status.toLowerCase().includes("done"))
                        ? "status-selesai" : "status-aktif";
    const statusLabel = (t.status.toLowerCase().includes("selesai") ||
                         t.status.toLowerCase().includes("done"))
                        ? "✅ Selesai" : "⏳ Belum Selesai";
    html += `
      <div class="task-card">
        <div class="tc-name">${{i+1}}. ${{t.tugas}}</div>
        <div class="tc-meta">
          <span>📚 ${{t.matkul !== "—" ? t.matkul : "—"}}</span>
          <span>📅 Deadline: ${{t.deadline}}</span>
        </div>
        <span class="status-badge ${{statusKelas}}">${{statusLabel}}</span>
      </div>
    `;
  }});

  document.getElementById("modal-tasks").innerHTML = html;
  document.getElementById("modal").classList.add("active");
}}

// ── Modal: tutup ──────────────────────────────
function tutupModal(e) {{
  if (e.target === document.getElementById("modal")) {{
    tutupModalLangsung();
  }}
}}
function tutupModalLangsung() {{
  document.getElementById("modal").classList.remove("active");
}}

// ── Keyboard ESC menutup modal ────────────────
document.addEventListener("keydown", e => {{
  if (e.key === "Escape") tutupModalLangsung();
}});

// ── Init ──────────────────────────────────────
renderKalender();
</script>
</body>
</html>
"""


# ═══════════════════════════════════════════════
# TAMPILAN UTAMA STREAMLIT
# ═══════════════════════════════════════════════

st.title("🧠 CogniPace AI")
st.markdown(
    "**Asisten Manajemen Beban Kognitif Mahasiswa**  \n"
    "Upload CSV tugas (format apapun) → AI analisis beban, kalender interaktif, "
    "dan jadwal prioritas otomatis."
)
st.divider()

# ── File Uploader ─────────────────────────────────────────────────────────────
st.subheader("📂 Upload Data Tugas")
st.caption(
    "CSV bisa berformat apapun — minimal ada kolom **deadline/due_date/batas waktu** "
    "dan nama tugas. Kolom matkul, status, dll opsional."
)
uploaded_file = st.file_uploader("Pilih file .csv", type=["csv"])

if uploaded_file is not None:

    # Baca CSV
    df_raw = pd.read_csv(uploaded_file)

    # Deteksi & normalisasi kolom
    df_norm, mapping = deteksi_dan_normalisasi(df_raw)

    # Tampilkan hasil deteksi kolom
    st.subheader("👀 Preview Data")
    st.dataframe(df_raw.head(), use_container_width=True)

    if mapping:
        kol_info = " · ".join([f"**{k}** → `{v}`" for k, v in mapping.items()])
        st.info(f"🔍 Kolom terdeteksi: {kol_info}")
    else:
        st.warning(
            "⚠️ Tidak ada kolom yang dikenali secara otomatis. "
            "Pastikan CSV memiliki kolom seperti: "
            "`Deadline`, `Due Date`, `Nama Tugas`, `Assignment`, dll."
        )

    # Validasi: pastikan kolom deadline ada
    if not kolom_ada(df_norm, "deadline"):
        st.error(
            "❌ Kolom **deadline** tidak ditemukan. "
            "Pastikan CSV-mu memiliki kolom deadline (atau due_date, batas waktu, dst)."
        )
        st.stop()

    total_baris = len(df_norm)
    total_aktif = len(filter_aktif(parse_deadline(df_norm)))
    st.info(f"📊 {total_baris} baris data · {total_aktif} tugas aktif terdeteksi")

    st.divider()

    # ── Tombol Analisis ───────────────────────────────────────────────────────
    if st.button("🔍 Prediksi & Analisis Beban Kognitif", type="primary", use_container_width=True):

        with st.spinner("⏳ Memproses data dan berkonsultasi dengan AI..."):

            # Hitung beban per tanggal untuk kalender
            try:
                beban_dict = hitung_beban(df_norm)
                df_prioritas = buat_tabel_prioritas(df_norm)
            except Exception as e:
                st.error(f"❌ Gagal memproses data: {e}")
                st.stop()

            # Panggil Ollama
            respons_ai = None
            skor_angka = None

            if not OLLAMA_TERSEDIA:
                st.warning("⚠️ Library `ollama` tidak ditemukan. `pip install ollama`")
            else:
                try:
                    respons_ai = panggil_ollama(df_raw, mapping)
                    skor_str = ekstrak_tag(respons_ai, "skor")
                    try:
                        skor_angka = max(1, min(10, int(float(skor_str))))
                    except (ValueError, TypeError):
                        skor_angka = None
                except Exception:
                    st.error(
                        "❌ Tidak dapat terhubung ke Ollama.\n\n"
                        "```\nollama serve\nollama pull phi3\n```"
                    )

        # ═══════════════════════════════════════════
        # OUTPUT SECTION
        # ═══════════════════════════════════════════
        st.success("✅ Analisis selesai!")

        # ── Metrik ringkasan ──────────────────────────────────────────────
        col1, col2, col3 = st.columns(3)
        zona_merah_count = sum(1 for v in beban_dict.values() if v["jumlah"] >= 3)

        with col1:
            if skor_angka is not None:
                delta_txt = ("⚠️ Berat" if skor_angka >= 7
                             else ("🟡 Sedang" if skor_angka >= 4 else "🟢 Ringan"))
                st.metric("🎯 Skor Beban Kognitif", f"{skor_angka} / 10", delta_txt)
            else:
                st.metric("🎯 Skor Beban Kognitif", "N/A", "AI offline")

        with col2:
            st.metric("📋 Tugas Aktif", f"{total_aktif} tugas")

        with col3:
            st.metric("🔴 Hari Padat (3+ tugas)", f"{zona_merah_count} hari")

        st.divider()

        # ── KALENDER INTERAKTIF ───────────────────────────────────────────
        st.subheader("📅 Kalender Beban Tugas")
        st.caption(
            "Navigasi bulan dengan tombol Prev/Next · "
            "**Klik tanggal berwarna** untuk melihat detail tugas & deadline"
        )

        # Serialisasi beban_dict ke JSON untuk dimasukkan ke JS
        beban_json_str = json.dumps(beban_dict, ensure_ascii=False)

        # Tentukan bulan awal: bulan dengan tugas pertama, atau bulan ini
        if beban_dict:
            tanggal_pertama = min(beban_dict.keys())
            thn_awal = int(tanggal_pertama[:4])
            bln_awal = int(tanggal_pertama[5:7]) - 1  # 0-indexed untuk JS
        else:
            thn_awal = date.today().year
            bln_awal = date.today().month - 1

        html_kalender = render_kalender_interaktif(beban_json_str, thn_awal, bln_awal)
        components.html(html_kalender, height=520, scrolling=False)

        st.divider()

        # ── TABEL PRIORITAS ───────────────────────────────────────────────
        st.subheader("📋 Tabel Prioritas Pengerjaan Tugas")
        st.caption("Urutan dari prioritas tertinggi (kerjakan duluan) → terendah.")

        if not df_prioritas.empty:
            def warnai_baris(row):
                urgensi = row.get("Urgensi", "")
                if "Terlambat" in urgensi or "Kritis" in urgensi:
                    return ["background-color: #ffe0e0"] * len(row)
                elif "Mendesak" in urgensi:
                    return ["background-color: #fff3e0"] * len(row)
                elif "Perhatikan" in urgensi:
                    return ["background-color: #fffde7"] * len(row)
                else:
                    return ["background-color: #f1f8e9"] * len(row)

            st.dataframe(
                df_prioritas.style.apply(warnai_baris, axis=1),
                use_container_width=True,
                height=320,
            )
        else:
            st.success("🎉 Semua tugas sudah selesai!")

        st.divider()

        # ── JADWAL HARIAN AI ──────────────────────────────────────────────
        st.subheader("🗓️ Rekomendasi Jadwal Harian (AI)")

        if respons_ai:
            df_jadwal = parse_jadwal_json(respons_ai)

            if df_jadwal is not None and not df_jadwal.empty:
                rename_map = {
                    "hari_ke": "Hari ke-", "tanggal": "Tanggal",
                    "fokus": "Fokus Tugas", "matkul": "Mata Kuliah",
                    "durasi_jam": "Durasi (Jam)", "catatan": "Catatan / Tips",
                }
                df_jadwal = df_jadwal.rename(columns={k: v for k, v in rename_map.items() if k in df_jadwal.columns})
                st.success("✅ AI berhasil menyusun jadwal harian:")
                st.dataframe(df_jadwal, use_container_width=True, hide_index=True)
            else:
                st.info("Format jadwal AI tidak terstruktur. Gunakan tabel prioritas di atas.")

            # Analisis AI
            analisis = ekstrak_tag(respons_ai, "analisis")
            if analisis:
                st.markdown("**💡 Analisis AI:**")
                st.info(analisis)

            with st.expander("🛠️ Respons Mentah AI (debug)"):
                st.text(respons_ai)
        else:
            st.info(
                "💡 Jadwal AI tidak tersedia (Ollama offline). "
                "Gunakan **Tabel Prioritas** di atas sebagai panduan."
            )

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🧠 CogniPace AI · Streamlit + Pandas + Ollama (phi3) · Prototype Demo")
