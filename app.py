"""
CogniPace AI — Asisten Manajemen Beban Kognitif Mahasiswa
==========================================================
Arsitektur baru (v3):
  1. CSV diunggah → semua kolom dikirim ke AI apa adanya
  2. AI menganalisis → mengembalikan JSON terstruktur:
       - skor beban kognitif
       - daftar tugas dengan tanggal yang sudah dinormalisasi
       - jadwal harian prioritas
       - tips & analisis
  3. JSON dari AI dirender menjadi kalender interaktif + tabel prioritas
  → Kalender & tabel 100% berdasarkan hasil analisis AI
"""

import re
import json
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import date

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
# BAGIAN 1: PARSER TANGGAL INDONESIA
# ═══════════════════════════════════════════════

BULAN_ID = {
    "januari":1,"februari":2,"maret":3,"april":4,"mei":5,"juni":6,
    "juli":7,"agustus":8,"september":9,"oktober":10,"november":11,"desember":12,
    "jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"agu":8,"agt":8,
    "sep":9,"okt":10,"nov":11,"des":12,
    "january":1,"february":2,"march":3,"may":5,"june":6,"july":7,
    "august":8,"october":10,"december":12,
}

def parse_tanggal(s: str, tahun_default: int = None) -> str | None:
    """
    Menerima string tanggal dalam berbagai format (termasuk '15 Juni')
    dan mengembalikan string ISO YYYY-MM-DD, atau None jika gagal.
    Tahun default = tahun berjalan jika tidak disebutkan.
    """
    if not tahun_default:
        tahun_default = date.today().year

    s = str(s).strip()
    parts = s.replace(",", " ").split()

    # Coba manual (nama bulan Indonesia / Inggris)
    if len(parts) >= 2:
        for i, p in enumerate(parts):
            bulan_num = BULAN_ID.get(p.lower())
            if bulan_num:
                others = [x for j, x in enumerate(parts) if j != i]
                for o in others:
                    try:
                        hari = int(o)
                        tahun = tahun_default
                        for o2 in others:
                            try:
                                y = int(o2)
                                if 2020 <= y <= 2035:
                                    tahun = y
                                    break
                            except:
                                pass
                        return f"{tahun:04d}-{bulan_num:02d}-{hari:02d}"
                    except:
                        pass

    # Fallback pandas untuk format numerik
    try:
        r = pd.to_datetime(s, format="mixed", dayfirst=True, errors="raise")
        if r.year >= 2020:
            return r.strftime("%Y-%m-%d")
    except:
        pass

    return None


# ═══════════════════════════════════════════════
# BAGIAN 2: PANGGIL AI — ARSITEKTUR BARU
# AI menerima CSV mentah dan mengembalikan JSON penuh
# ═══════════════════════════════════════════════

SCHEMA_JSON = """{
  "skor_beban": <angka 1-10>,
  "ringkasan": "<analisis singkat kondisi beban mahasiswa>",
  "tips": [
    "<tip manajemen waktu 1>",
    "<tip manajemen waktu 2>",
    "<tip manajemen waktu 3>"
  ],
  "tugas": [
    {
      "nama_tugas": "<nama tugas>",
      "matkul": "<nama mata kuliah atau kategori, tulis '-' jika tidak ada>",
      "deadline_iso": "<tanggal deadline format YYYY-MM-DD>",
      "prioritas": "<Tinggi / Sedang / Rendah>",
      "estimasi_jam": <angka jam pengerjaan, perkirakan jika tidak ada>,
      "status": "<Belum Selesai / Selesai>"
    }
  ],
  "jadwal_harian": [
    {
      "hari_ke": <nomor urut hari>,
      "tanggal": "<YYYY-MM-DD>",
      "nama_tugas": "<nama tugas yang dikerjakan hari ini>",
      "matkul": "<mata kuliah>",
      "durasi_jam": <jam>,
      "catatan": "<tips spesifik pengerjaan>"
    }
  ]
}"""


def panggil_ollama(csv_string: str, kolom_info: str) -> str:
    """
    Mengirim seluruh CSV ke AI dan meminta JSON terstruktur lengkap.
    AI bertanggung jawab:
      - Menormalisasi semua tanggal ke ISO format
      - Menentukan prioritas jika belum ada
      - Membuat jadwal harian yang logis
      - Menghitung skor beban
    """
    hari_ini = date.today().strftime("%Y-%m-%d")

    prompt = f"""Kamu adalah AI Asisten Akademik yang sangat teliti. Hari ini tanggal {hari_ini}.

Data tugas mahasiswa dari file CSV:
Kolom yang tersedia: {kolom_info}

DATA CSV:
{csv_string}

TUGASMU:
Analisis semua tugas di atas dan kembalikan HANYA satu objek JSON valid, tanpa teks lain, tanpa markdown, tanpa penjelasan apapun di luar JSON.

PENTING:
1. Konversi semua tanggal ke format ISO YYYY-MM-DD. Jika tahun tidak disebutkan, gunakan tahun {date.today().year}.
2. Untuk setiap tugas, tentukan status (Belum Selesai / Selesai) berdasarkan data. Jika tidak ada info status, anggap "Belum Selesai".
3. Buat jadwal_harian yang realistis, dimulai dari hari ini ({hari_ini}), satu tugas per hari (atau lebih jika tugas ringan), selesai sebelum deadline masing-masing.
4. Urutkan tugas_harian berdasarkan deadline terdekat dan prioritas tertinggi.
5. Skor beban 1-10: perhatikan jumlah tugas, estimasi waktu total, dan kepadatan deadline.

Format JSON yang HARUS kamu kembalikan (isi sesuai data):
{SCHEMA_JSON}

Ingat: kembalikan HANYA JSON murni, tidak ada teks lain sama sekali."""

    response = ollama.chat(
        model="phi3",
        messages=[{"role": "user", "content": prompt}],
    )
    return response["message"]["content"]


def bersihkan_dan_parse_json(teks: str) -> dict | None:
    """
    Membersihkan respons AI dan mem-parse JSON.
    Mencoba beberapa strategi jika JSON tidak sempurna.
    """
    if not teks:
        return None

    # Hapus markdown code block jika ada
    teks = re.sub(r"```json\s*", "", teks)
    teks = re.sub(r"```\s*", "", teks)
    teks = teks.strip()

    # Coba parse langsung
    try:
        return json.loads(teks)
    except json.JSONDecodeError:
        pass

    # Coba ekstrak JSON dari dalam teks (jika ada teks di luar JSON)
    pola = r'\{.*\}'
    match = re.search(pola, teks, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except json.JSONDecodeError:
            pass

    return None


# ═══════════════════════════════════════════════
# BAGIAN 3: BANGUN DATA KALENDER DARI JSON AI
# ═══════════════════════════════════════════════

def bangun_beban_dari_ai(data_ai: dict) -> dict:
    """
    Mengubah list tugas dari JSON AI menjadi dict beban kalender:
    { "YYYY-MM-DD": { "jumlah": N, "tugas": [...] } }
    """
    beban = {}
    tugas_list = data_ai.get("tugas", [])

    for t in tugas_list:
        # Gunakan deadline_iso dari AI, atau coba parse ulang
        deadline_raw = t.get("deadline_iso", "") or t.get("deadline", "")
        deadline_str = parse_tanggal(deadline_raw)

        if not deadline_str:
            continue  # Skip tugas tanpa deadline valid

        status = t.get("status", "Belum Selesai")
        # Tampilkan semua tugas di kalender (termasuk yang selesai, tapi bedakan visual)
        if deadline_str not in beban:
            beban[deadline_str] = {"jumlah": 0, "tugas": []}

        beban[deadline_str]["jumlah"] += 1
        beban[deadline_str]["tugas"].append({
            "tugas": t.get("nama_tugas", "Tugas"),
            "matkul": t.get("matkul", "—"),
            "deadline": deadline_str,
            "prioritas": t.get("prioritas", "Sedang"),
            "estimasi_jam": t.get("estimasi_jam", "?"),
            "status": status,
        })

    return beban


def bangun_tabel_prioritas(data_ai: dict) -> pd.DataFrame:
    """
    Membangun tabel prioritas dari list tugas JSON AI.
    Hanya tugas belum selesai, diurutkan: prioritas tinggi + deadline terdekat.
    """
    tugas_list = data_ai.get("tugas", [])
    if not tugas_list:
        return pd.DataFrame()

    today = date.today()
    rows = []

    BOBOT_PRIORITAS = {"Tinggi": 0, "High": 0, "Sedang": 1, "Medium": 1, "Rendah": 2, "Low": 2}

    for t in tugas_list:
        status = t.get("status", "Belum Selesai")
        if status.lower() in {"selesai", "done", "complete", "completed"}:
            continue  # Skip tugas selesai dari tabel prioritas

        deadline_raw = t.get("deadline_iso", "") or t.get("deadline", "")
        deadline_str = parse_tanggal(deadline_raw)

        if deadline_str:
            try:
                d = date.fromisoformat(deadline_str)
                hari_tersisa = (d - today).days
                deadline_display = d.strftime("%d %b %Y")
            except:
                hari_tersisa = 999
                deadline_display = deadline_raw
        else:
            hari_tersisa = 999
            deadline_display = deadline_raw

        def label_urgensi(hari):
            if hari < 0:    return "🔴 Terlambat"
            elif hari <= 2: return "🔴 Kritis"
            elif hari <= 5: return "🟠 Mendesak"
            elif hari <= 10: return "🟡 Perhatikan"
            else:           return "🟢 Aman"

        prioritas = t.get("prioritas", "Sedang")
        bobot = BOBOT_PRIORITAS.get(prioritas, 1)
        # Skor: hari_tersisa dikurangi bobot prioritas (lebih kecil = lebih urgent)
        skor = hari_tersisa + (bobot * 2)

        rows.append({
            "_skor": skor,
            "Nama Tugas": t.get("nama_tugas", "Tugas"),
            "Mata Kuliah": t.get("matkul", "—"),
            "Deadline": deadline_display,
            "Hari Tersisa": hari_tersisa if hari_tersisa != 999 else "?",
            "Prioritas": prioritas,
            "Estimasi": f"{t.get('estimasi_jam', '?')} jam",
            "Urgensi": label_urgensi(hari_tersisa),
        })

    if not rows:
        return pd.DataFrame()

    df = pd.DataFrame(rows).sort_values("_skor").drop(columns=["_skor"]).reset_index(drop=True)
    df.index += 1
    return df


def bangun_tabel_jadwal(data_ai: dict) -> pd.DataFrame:
    """Membangun tabel jadwal harian dari JSON AI."""
    jadwal = data_ai.get("jadwal_harian", [])
    if not jadwal:
        return pd.DataFrame()

    df = pd.DataFrame(jadwal)
    rename_map = {
        "hari_ke": "Hari ke-",
        "tanggal": "Tanggal",
        "nama_tugas": "Fokus Tugas",
        "matkul": "Mata Kuliah",
        "durasi_jam": "Durasi (Jam)",
        "catatan": "Catatan / Tips",
    }
    df = df.rename(columns={k: v for k, v in rename_map.items() if k in df.columns})

    # Format tanggal jika ada
    if "Tanggal" in df.columns:
        def fmt_tgl(s):
            try:
                return date.fromisoformat(str(s)).strftime("%d %b %Y")
            except:
                return s
        df["Tanggal"] = df["Tanggal"].apply(fmt_tgl)

    return df


# ═══════════════════════════════════════════════
# BAGIAN 4: KALENDER INTERAKTIF (HTML + JS)
# ═══════════════════════════════════════════════

def render_kalender(beban_json: str, tahun_awal: int, bulan_awal: int) -> str:
    """
    Komponen HTML+JS kalender interaktif:
    - Navigasi prev/next bulan tanpa reload
    - Klik tanggal → modal dengan detail lengkap tugas
    - Heatmap 5 level warna
    - Badge prioritas di dalam modal
    """
    return f"""<!DOCTYPE html>
<html lang="id">
<head>
<meta charset="UTF-8">
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', sans-serif; background: transparent; padding: 6px 10px; }}

  .cal-nav {{
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 14px;
  }}
  .cal-nav button {{
    background: #4a90d9; color: white; border: none; border-radius: 8px;
    padding: 8px 20px; font-size: 0.95rem; cursor: pointer;
    transition: background 0.2s; font-weight: 600;
  }}
  .cal-nav button:hover {{ background: #2c6fad; }}
  .month-label {{ font-size: 1.35rem; font-weight: 800; color: #1a1a2e; }}

  .cal-grid {{
    display: grid;
    grid-template-columns: repeat(7, 1fr);
    gap: 5px;
  }}
  .cal-header-cell {{
    text-align: center; font-size: 0.7rem; font-weight: 700;
    color: #999; padding: 5px 0; letter-spacing: 0.05em; text-transform: uppercase;
  }}

  .cal-cell {{
    border-radius: 10px; min-height: 80px; padding: 7px 6px;
    position: relative; font-size: 0.7rem;
    transition: transform 0.15s, box-shadow 0.15s;
    border: 2px solid transparent;
    cursor: default;
  }}
  .cal-cell.clickable {{ cursor: pointer; }}
  .cal-cell.clickable:hover {{
    transform: translateY(-3px);
    box-shadow: 0 6px 18px rgba(0,0,0,0.18);
    border-color: #4a90d9 !important;
    z-index: 2;
  }}
  .cal-cell.empty   {{ background: transparent; cursor: default; }}
  .cal-cell.c0      {{ background: #f4f5f7; color: #bbb; }}
  .cal-cell.c1      {{ background: #e8f4fd; border-color: #b3d9f5; }}
  .cal-cell.c2      {{ background: #fff3cd; border-color: #ffc107; }}
  .cal-cell.c3      {{ background: #ffe0b2; border-color: #ff9800; }}
  .cal-cell.c4      {{ background: #ffccbc; border-color: #ff5722; }}
  .cal-cell.c5plus  {{ background: #e53935; border-color: #b71c1c; color: white; }}
  .cal-cell.today   {{
    outline: 3px solid #1976d2; outline-offset: -2px;
  }}
  .cal-cell.today .day-num {{ color: #1976d2; font-weight: 900; }}

  .day-num {{
    font-size: 0.92rem; font-weight: 700; margin-bottom: 5px;
    display: flex; justify-content: space-between; align-items: center;
  }}
  .task-badge {{
    background: rgba(0,0,0,0.12); border-radius: 20px;
    padding: 1px 7px; font-size: 0.62rem; font-weight: 800;
  }}
  .c5plus .task-badge {{ background: rgba(255,255,255,0.25); }}

  .chip {{
    display: block; background: rgba(0,0,0,0.07); border-radius: 5px;
    padding: 2px 5px; margin-top: 3px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
    font-size: 0.62rem;
  }}
  .c5plus .chip {{ background: rgba(255,255,255,0.2); color: white; }}
  .chip-tinggi  {{ border-left: 3px solid #e53935; }}
  .chip-sedang  {{ border-left: 3px solid #ff9800; }}
  .chip-rendah  {{ border-left: 3px solid #4caf50; }}

  .legend {{
    display: flex; gap: 10px; justify-content: center; flex-wrap: wrap;
    margin-top: 14px; font-size: 0.7rem; color: #666;
  }}
  .leg {{ display: flex; align-items: center; gap: 5px; }}
  .leg-box {{
    width: 14px; height: 14px; border-radius: 4px;
    border: 1px solid rgba(0,0,0,0.1); flex-shrink: 0;
  }}

  /* MODAL */
  .overlay {{
    display: none; position: fixed; inset: 0;
    background: rgba(0,0,0,0.55); z-index: 1000;
    align-items: center; justify-content: center; padding: 16px;
  }}
  .overlay.on {{ display: flex; }}
  .modal {{
    background: white; border-radius: 18px; padding: 26px;
    max-width: 500px; width: 100%; max-height: 82vh; overflow-y: auto;
    box-shadow: 0 24px 64px rgba(0,0,0,0.3);
    animation: up 0.22s ease;
  }}
  @keyframes up {{
    from {{ transform: translateY(24px); opacity: 0; }}
    to   {{ transform: translateY(0); opacity: 1; }}
  }}
  .m-date {{ font-size: 1.05rem; font-weight: 800; color: #1a1a2e; margin-bottom: 3px; }}
  .m-sub  {{ font-size: 0.78rem; color: #888; margin-bottom: 16px; }}

  .task-card {{
    background: #f8f9fa; border-radius: 11px; padding: 13px 14px;
    margin-bottom: 10px;
  }}
  .tc-name {{ font-weight: 700; font-size: 0.92rem; color: #1a1a2e; margin-bottom: 6px; }}
  .tc-row  {{
    display: flex; flex-wrap: wrap; gap: 8px 16px;
    font-size: 0.76rem; color: #555;
  }}
  .tc-row span {{ display: flex; align-items: center; gap: 4px; }}
  .pri-badge {{
    display: inline-block; padding: 2px 10px; border-radius: 20px;
    font-size: 0.67rem; font-weight: 700; margin-top: 7px;
  }}
  .pri-tinggi {{ background: #fde8e8; color: #c62828; }}
  .pri-sedang {{ background: #fff3e0; color: #e65100; }}
  .pri-rendah {{ background: #e8f5e9; color: #2e7d32; }}
  .sta-done   {{ background: #e8f5e9; color: #2e7d32; font-size: 0.67rem;
                 font-weight: 700; padding: 2px 10px; border-radius: 20px;
                 display: inline-block; margin-top: 7px; margin-left: 6px; }}
  .sta-todo   {{ background: #fff3e0; color: #e65100; font-size: 0.67rem;
                 font-weight: 700; padding: 2px 10px; border-radius: 20px;
                 display: inline-block; margin-top: 7px; margin-left: 6px; }}

  .btn-close {{
    width: 100%; margin-top: 16px; padding: 11px;
    background: #f0f2f5; border: none; border-radius: 9px;
    font-size: 0.88rem; cursor: pointer; color: #333; font-weight: 600;
    transition: background 0.2s;
  }}
  .btn-close:hover {{ background: #e2e5ea; }}
</style>
</head>
<body>

<div class="cal-nav">
  <button onclick="nav(-1)">&#8592; Prev</button>
  <span class="month-label" id="lbl"></span>
  <button onclick="nav(1)">Next &#8594;</button>
</div>

<div class="cal-grid" id="grid"></div>

<div class="legend">
  <div class="leg"><div class="leg-box" style="background:#f4f5f7"></div>Bebas</div>
  <div class="leg"><div class="leg-box" style="background:#e8f4fd;border-color:#b3d9f5"></div>1 tugas</div>
  <div class="leg"><div class="leg-box" style="background:#fff3cd;border-color:#ffc107"></div>2 tugas</div>
  <div class="leg"><div class="leg-box" style="background:#ffe0b2;border-color:#ff9800"></div>3 tugas</div>
  <div class="leg"><div class="leg-box" style="background:#ffccbc;border-color:#ff5722"></div>4 tugas</div>
  <div class="leg"><div class="leg-box" style="background:#e53935"></div>5+ 🚨</div>
  <div class="leg"><div class="leg-box" style="outline:3px solid #1976d2;background:white"></div>Hari Ini</div>
</div>

<div class="overlay" id="overlay" onclick="closeM(event)">
  <div class="modal">
    <div class="m-date" id="m-date"></div>
    <div class="m-sub"  id="m-sub"></div>
    <div id="m-body"></div>
    <button class="btn-close" onclick="closeML()">✕ Tutup</button>
  </div>
</div>

<script>
const DATA = {beban_json};
let Y = {tahun_awal}, M = {bulan_awal};

const BULAN = ["Januari","Februari","Maret","April","Mei","Juni",
               "Juli","Agustus","September","Oktober","November","Desember"];
const HARI_PANJANG = ["Minggu","Senin","Selasa","Rabu","Kamis","Jumat","Sabtu"];
const BULAN_PENDEK = ["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"];

function pad(n){{ return String(n).padStart(2,"0"); }}
function isoKey(y,m,d){{ return y+"-"+pad(m)+"-"+pad(d); }}

function render() {{
  document.getElementById("lbl").textContent = BULAN[M] + " " + Y;
  const grid = document.getElementById("grid");
  grid.innerHTML = "";

  const heads = ["Sen","Sel","Rab","Kam","Jum","Sab","Min"];
  heads.forEach(h => {{
    const el = document.createElement("div");
    el.className = "cal-header-cell";
    el.textContent = h;
    grid.appendChild(el);
  }});

  const today = new Date();
  const firstDay = new Date(Y, M, 1);
  const totalDays = new Date(Y, M+1, 0).getDate();
  const offset = (firstDay.getDay() + 6) % 7; // Senin = 0

  for(let i=0;i<offset;i++) {{
    const e=document.createElement("div"); e.className="cal-cell empty"; grid.appendChild(e);
  }}

  for(let d=1;d<=totalDays;d++) {{
    const key = isoKey(Y, M+1, d);
    const info = DATA[key];
    const n = info ? info.jumlah : 0;

    let cls = "c0";
    if(n===1) cls="c1"; else if(n===2) cls="c2";
    else if(n===3) cls="c3"; else if(n===4) cls="c4";
    else if(n>=5)  cls="c5plus";

    const isToday = (d===today.getDate() && M===today.getMonth() && Y===today.getFullYear());
    const cell = document.createElement("div");
    cell.className = "cal-cell "+cls+(isToday?" today":"")+(n>0?" clickable":"");

    let badge = n>0 ? `<span class="task-badge">${{n}}</span>` : "";
    let chips = "";
    if(info) {{
      info.tugas.slice(0,2).forEach(t => {{
        const nm = t.tugas.length>17 ? t.tugas.slice(0,17)+"…" : t.tugas;
        const pCls = (t.prioritas||"").toLowerCase().startsWith("t") ? "chip-tinggi"
                   : (t.prioritas||"").toLowerCase().startsWith("r") ? "chip-rendah" : "chip-sedang";
        chips += `<span class="chip ${{pCls}}">📌 ${{nm}}</span>`;
      }});
      if(info.tugas.length>2) chips += `<span class="chip">+${{info.tugas.length-2}} lagi…</span>`;
    }}

    cell.innerHTML = `<div class="day-num"><span>${{d}}</span>${{badge}}</div>${{chips}}`;
    if(n>0) cell.addEventListener("click", ()=>openM(key,info,d));
    grid.appendChild(cell);
  }}
}}

function nav(dir) {{
  M += dir;
  if(M<0)  {{ M=11; Y--; }}
  if(M>11) {{ M=0;  Y++; }}
  render();
}}

function openM(key, info, d) {{
  const parts = key.split("-");
  const dt = new Date(+parts[0], +parts[1]-1, +parts[2]);
  document.getElementById("m-date").textContent =
    HARI_PANJANG[dt.getDay()]+", "+d+" "+BULAN_PENDEK[dt.getMonth()]+" "+dt.getFullYear();
  document.getElementById("m-sub").textContent =
    info.jumlah + " tugas jatuh tempo hari ini";

  let html = "";
  info.tugas.forEach((t,i) => {{
    const priCls = (t.prioritas||"").toLowerCase().startsWith("t") ? "pri-tinggi"
                 : (t.prioritas||"").toLowerCase().startsWith("r") ? "pri-rendah" : "pri-sedang";
    const isDone = (t.status||"").toLowerCase().includes("selesai")||
                   (t.status||"").toLowerCase().includes("done");
    html += `
    <div class="task-card">
      <div class="tc-name">${{i+1}}. ${{t.tugas}}</div>
      <div class="tc-row">
        ${{t.matkul!=="—"?`<span>📚 ${{t.matkul}}</span>`:"" }}
        <span>📅 Deadline: ${{t.deadline}}</span>
        <span>⏱️ Est: ${{t.estimasi_jam}} jam</span>
      </div>
      <span class="pri-badge ${{priCls}}">🎯 ${{t.prioritas||"Sedang"}}</span>
      <span class="${{isDone?"sta-done":"sta-todo"}}">${{isDone?"✅ Selesai":"⏳ Belum Selesai"}}</span>
    </div>`;
  }});

  document.getElementById("m-body").innerHTML = html;
  document.getElementById("overlay").classList.add("on");
}}

function closeM(e) {{ if(e.target===document.getElementById("overlay")) closeML(); }}
function closeML() {{ document.getElementById("overlay").classList.remove("on"); }}
document.addEventListener("keydown", e=>{{ if(e.key==="Escape") closeML(); }});

render();
</script>
</body>
</html>"""


# ═══════════════════════════════════════════════
# TAMPILAN UTAMA STREAMLIT
# ═══════════════════════════════════════════════

st.title("🧠 CogniPace AI")
st.markdown(
    "**Asisten Manajemen Beban Kognitif Mahasiswa**  \n"
    "Upload CSV tugas (format apapun) → AI menganalisis semua data → "
    "Kalender heatmap interaktif + Jadwal prioritas dari AI"
)
st.divider()

# ── FILE UPLOADER ─────────────────────────────────────────────────────────────
st.subheader("📂 Upload Data Tugas")
st.caption("Format CSV bebas — minimal ada kolom nama tugas dan deadline. Semua analisis dilakukan oleh AI.")
uploaded_file = st.file_uploader("Pilih file .csv", type=["csv"])

if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)

    st.subheader("👀 Preview Data")
    st.dataframe(df_raw, use_container_width=True)

    kolom_info = ", ".join([f'"{c}"' for c in df_raw.columns])
    st.info(f"📊 {len(df_raw)} baris data · Kolom: {kolom_info}")
    st.divider()

    # ── TOMBOL ANALISIS ───────────────────────────────────────────────────────
    if st.button("🔍 Analisis dengan AI & Buat Kalender", type="primary", use_container_width=True):

        if not OLLAMA_TERSEDIA:
            st.error("❌ Library `ollama` tidak ditemukan. Jalankan: `pip install ollama`")
            st.stop()

        with st.spinner("🤖 AI sedang menganalisis semua data tugas kamu... (bisa 15–30 detik)"):
            try:
                csv_string = df_raw.to_csv(index=False)
                respons_raw = panggil_ollama(csv_string, kolom_info)
            except Exception as e:
                st.error(
                    "❌ **Tidak dapat terhubung ke Ollama.**\n\n"
                    "Jalankan server Ollama dulu:\n"
                    "```\nollama serve\n```\n"
                    "Unduh model jika belum:\n"
                    "```\nollama pull phi3\n```"
                )
                st.stop()

            # Parse JSON dari AI
            data_ai = bersihkan_dan_parse_json(respons_raw)

            if not data_ai:
                st.error(
                    "⚠️ AI tidak mengembalikan JSON yang valid. "
                    "Coba klik tombol analisis lagi (model phi3 kadang tidak konsisten)."
                )
                with st.expander("🛠️ Respons mentah AI"):
                    st.text(respons_raw)
                st.stop()

        st.success("✅ Analisis AI selesai!")

        # ══════════════════════════════════════════
        # OUTPUT SECTION
        # ══════════════════════════════════════════

        # ── METRIK RINGKASAN ──────────────────────────────────────────────
        skor = data_ai.get("skor_beban", None)
        tugas_list = data_ai.get("tugas", [])
        total_aktif = sum(1 for t in tugas_list
                          if not t.get("status","").lower().startswith("selesai"))
        total_padat = 0  # dihitung setelah build beban

        beban_dict = bangun_beban_dari_ai(data_ai)
        total_padat = sum(1 for v in beban_dict.values() if v["jumlah"] >= 3)

        col1, col2, col3 = st.columns(3)
        with col1:
            if skor:
                try:
                    skor_num = int(float(str(skor)))
                    skor_num = max(1, min(10, skor_num))
                    delta = "⚠️ Berat" if skor_num >= 7 else ("🟡 Sedang" if skor_num >= 4 else "🟢 Ringan")
                    st.metric("🎯 Skor Beban Kognitif", f"{skor_num} / 10", delta)
                except:
                    st.metric("🎯 Skor Beban Kognitif", str(skor))
            else:
                st.metric("🎯 Skor Beban Kognitif", "N/A")
        with col2:
            st.metric("📋 Tugas Aktif", f"{total_aktif} tugas")
        with col3:
            st.metric("🔴 Hari Padat (3+ tugas)", f"{total_padat} hari")

        st.divider()

        # ── KALENDER INTERAKTIF ───────────────────────────────────────────
        st.subheader("📅 Kalender Beban Tugas")
        st.caption(
            "Navigasi bulan dengan **← Prev / Next →** · "
            "**Klik tanggal berwarna** untuk melihat detail tugas, prioritas, dan estimasi waktu"
        )

        if beban_dict:
            tgl_pertama = min(beban_dict.keys())
            thn_awal = int(tgl_pertama[:4])
            bln_awal = int(tgl_pertama[5:7]) - 1  # 0-indexed JS
        else:
            thn_awal = date.today().year
            bln_awal = date.today().month - 1

        beban_json_str = json.dumps(beban_dict, ensure_ascii=False)
        html_kal = render_kalender(beban_json_str, thn_awal, bln_awal)
        components.html(html_kal, height=540, scrolling=False)

        st.divider()

        # ── TABEL PRIORITAS ───────────────────────────────────────────────
        st.subheader("📋 Tabel Prioritas Pengerjaan Tugas")
        st.caption("Diurutkan otomatis: prioritas tertinggi + deadline terdekat → kerjakan dari baris paling atas")

        df_prio = bangun_tabel_prioritas(data_ai)

        if not df_prio.empty:
            def warnai(row):
                u = row.get("Urgensi", "")
                if "Terlambat" in u or "Kritis" in u:
                    return ["background-color:#ffe0e0"] * len(row)
                elif "Mendesak" in u:
                    return ["background-color:#fff3e0"] * len(row)
                elif "Perhatikan" in u:
                    return ["background-color:#fffde7"] * len(row)
                else:
                    return ["background-color:#f1f8e9"] * len(row)

            st.dataframe(
                df_prio.style.apply(warnai, axis=1),
                use_container_width=True,
                height=min(60 + len(df_prio) * 38, 400),
            )
        else:
            st.success("🎉 Semua tugas sudah selesai!")

        st.divider()

        # ── JADWAL HARIAN AI ──────────────────────────────────────────────
        st.subheader("🗓️ Rekomendasi Jadwal Harian (dari AI)")
        st.caption("Jadwal yang disusun AI berdasarkan prioritas, estimasi waktu, dan kedekatan deadline")

        df_jadwal = bangun_tabel_jadwal(data_ai)

        if not df_jadwal.empty:
            st.dataframe(df_jadwal, use_container_width=True, hide_index=True,
                         height=min(60 + len(df_jadwal) * 38, 450))
        else:
            st.info("AI tidak menghasilkan jadwal harian. Gunakan tabel prioritas di atas.")

        st.divider()

        # ── RINGKASAN & TIPS AI ───────────────────────────────────────────
        st.subheader("💡 Ringkasan & Tips dari AI")

        ringkasan = data_ai.get("ringkasan", "")
        tips_list = data_ai.get("tips", [])

        if ringkasan:
            st.info(f"📊 **Analisis AI:** {ringkasan}")

        if tips_list:
            st.markdown("**🎯 Tips Manajemen Waktu:**")
            for i, tip in enumerate(tips_list, 1):
                st.markdown(f"{i}. {tip}")

        if not ringkasan and not tips_list:
            st.info("AI tidak memberikan tips tambahan untuk data ini.")

        # Ekspander debug
        with st.expander("🛠️ Lihat JSON Mentah dari AI (debug)"):
            st.json(data_ai)

# ── FOOTER ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🧠 CogniPace AI · Streamlit + Pandas + Ollama (phi3) · v3 — AI-First Architecture")
