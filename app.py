import re
import json
import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
from datetime import date, timedelta

try:
    from groq import Groq
    AI_TERSEDIA = True
except ImportError:
    AI_TERSEDIA = False

# KONFIGURASI
st.set_page_config(page_title="CogniPace AI", page_icon="🧠", layout="wide")
st.markdown("""<style>
/* ── FORCE LIGHT MODE ── */
html, body { color-scheme: light !important; background:#fff !important; }

/* App & main containers */
[data-testid="stApp"],
[data-testid="stAppViewContainer"],
[data-testid="stMain"],
[data-testid="stMainBlockContainer"],
.main, .block-container {
  background-color: #ffffff !important;
  color: #31333f !important;
}

/* Header / top bar */
[data-testid="stHeader"] {
  background-color: #ffffff !important;
  border-bottom: 1px solid #e6e9ef !important;
}

/* Sidebar */
[data-testid="stSidebar"],
[data-testid="stSidebarContent"] {
  background-color: #f0f2f6 !important;
}
[data-testid="stSidebar"] * { color: #31333f !important; }
[data-testid="stSidebar"] code,
[data-testid="stSidebar"] pre {
  background-color: #e0e3eb !important;
  color: #31333f !important;
}

/* Teks umum */
p, h1, h2, h3, h4, h5, h6, li,
.stMarkdown, [data-testid="stMarkdownContainer"] {
  color: #31333f !important;
}

/* ── UPLOAD DATA — file uploader zona & pill ── */
[data-testid="stFileUploader"] {
  background-color: #ffffff !important;
}
[data-testid="stFileUploaderDropzone"] {
  background-color: #f8f9fa !important;
  border: 2px dashed #cccccc !important;
  border-radius: 10px !important;
}
[data-testid="stFileUploaderDropzone"] *,
[data-testid="stFileUploaderDropzoneInstructions"] * {
  color: #31333f !important;
  fill: #31333f !important;
}
/* File pill container — putih bersih */
[data-testid="stFileUploaderFile"] {
  background-color: #ffffff !important;
  border: 1px solid #d0d3db !important;
  border-radius: 8px !important;
}
[data-testid="stFileUploaderFile"] > div,
[data-testid="stFileUploaderFile"] * {
  background-color: #ffffff !important;
  color: #31333f !important;
  border-color: #d0d3db !important;
}

/* ── SEMBUNYIKAN LOGO/ICON di sebelah nama file ── */
[data-testid="stFileUploaderFile"] > div > div:first-child,
[data-testid="stFileUploaderFileData"] > div:first-child,
[data-testid="stFileUploaderFile"] [class*="thumb"],
[data-testid="stFileUploaderFile"] [class*="Thumb"],
[data-testid="stFileUploaderFile"] [class*="preview"],
[data-testid="stFileUploaderFile"] [class*="Preview"],
[data-testid="stFileUploaderFile"] img {
  display: none !important;
}

/* ── TOMBOL X HAPUS FILE — selalu terlihat jelas di kedua mode ── */
[data-testid="stFileUploaderDeleteBtn"] {
  background-color: #e2e6ee !important;
  border-radius: 50% !important;
  border: 1px solid #c0c5d0 !important;
  box-shadow: none !important;
  opacity: 1 !important;
  visibility: visible !important;
  display: flex !important;
  align-items: center !important;
  justify-content: center !important;
  width: 24px !important;
  height: 24px !important;
  min-width: 24px !important;
  padding: 0 !important;
}
[data-testid="stFileUploaderDeleteBtn"]:hover {
  background-color: #f87171 !important;
  border-color: #ef4444 !important;
}
[data-testid="stFileUploaderDeleteBtn"] svg,
[data-testid="stFileUploaderDeleteBtn"] svg path,
[data-testid="stFileUploaderDeleteBtn"] * {
  fill: #31333f !important;
  color: #31333f !important;
  background-color: transparent !important;
}
[data-testid="stFileUploaderDeleteBtn"]:hover svg,
[data-testid="stFileUploaderDeleteBtn"]:hover svg path {
  fill: #ffffff !important;
}

/* Icon di dropzone */
[data-testid="stFileUploaderDropzone"] svg,
[data-testid="stFileUploaderDropzone"] svg path {
  fill: #4a5568 !important;
  color: #4a5568 !important;
}
/* Semua elemen dalam zona upload */
[data-testid="stFileUploader"] * { color: #31333f !important; }

/* Input & textarea */
input, textarea {
  background-color: #ffffff !important;
  color: #31333f !important;
}
[data-baseweb="input"], [data-baseweb="textarea"],
[data-baseweb="base-input"] {
  background-color: #ffffff !important;
  color: #31333f !important;
}

/* Selectbox */
[data-baseweb="select"] > div {
  background-color: #ffffff !important;
  color: #31333f !important;
  border-color: #cccccc !important;
}

/* Semua popup / dropdown / menu */
[data-baseweb="popover"] > div,
[data-baseweb="menu"],
[data-testid="stMainMenuPopover"],
[data-testid="stMainMenu"],
[role="listbox"],
ul[role="listbox"],
li[role="option"],
[data-baseweb="list"] {
  background-color: #ffffff !important;
  color: #31333f !important;
  border: 1px solid #e0e0e0 !important;
  box-shadow: 0 4px 16px rgba(0,0,0,.12) !important;
}
[role="option"], li[role="option"] { color: #31333f !important; }
[role="option"]:hover, li[role="option"]:hover { background-color: #f0f2f6 !important; }

/* ⋮ menu items */
[data-testid="stMainMenuPopover"] ul,
[data-testid="stMainMenuPopover"] li,
[data-testid="stMainMenuPopover"] button,
[data-testid="stMainMenuPopover"] span,
[data-testid="stMainMenuPopover"] a {
  background-color: #ffffff !important;
  color: #31333f !important;
}
[data-testid="stMainMenuPopover"] li:hover,
[data-testid="stMainMenuPopover"] button:hover { background-color: #f0f2f6 !important; }

/* ── CHAT INPUT & BOTTOM BAR ── */
[data-testid="stBottom"],
[data-testid="stBottomBlockContainer"] {
  background-color: #f0f2f6 !important;
  border-top: 1px solid #e0e0e0 !important;
}
[data-testid="stChatInput"],
[data-testid="stChatInput"] > div,
[data-testid="stChatInput"] > div > div {
  background-color: #ffffff !important;
  border: 1px solid #d0d3db !important;
  border-radius: 12px !important;
}
[data-testid="stChatInput"] textarea {
  background-color: #ffffff !important;
  color: #31333f !important;
  caret-color: #31333f !important;
}
[data-testid="stChatInput"] textarea::placeholder { color: #9ea3b0 !important; }
[data-testid="stChatInput"] * { color: #31333f !important; }

/* Chat messages bubble */
[data-testid="stChatMessage"] {
  color: #31333f !important;
  background-color: #f8f9fa !important;
  border-radius: 10px !important;
  border: 1px solid #e8eaef !important;
}
[data-testid="stChatMessage"] * { color: #31333f !important; }

/* ── AVATAR CHAT — semua varian selector Streamlit ── */
/* Varian testid lama */
[data-testid="chatAvatarIcon-user"],
[data-testid="chatAvatarIcon-assistant"],
[data-testid="chatAvatarIcon-user"] > *,
[data-testid="chatAvatarIcon-assistant"] > * {
  background-color: #ffffff !important;
  border-radius: 8px !important;
  box-shadow: none !important;
  border: 1px solid #d0d5e0 !important;
}
/* Varian testid baru */
[data-testid="stChatMessageAvatarUser"],
[data-testid="stChatMessageAvatarAssistant"],
[data-testid="stChatMessageAvatarUser"] > *,
[data-testid="stChatMessageAvatarAssistant"] > * {
  background-color: #ffffff !important;
  border-radius: 8px !important;
  box-shadow: none !important;
  border: 1px solid #d0d5e0 !important;
}
/* Brute force: elemen pertama di tiap chat message (posisi avatar) */
[data-testid="stChatMessage"] > div > div:first-child,
[data-testid="stChatMessage"] > div > div:first-child > *,
[data-testid="stChatMessage"] > div > div:first-child > * > *,
[data-testid="stChatMessage"] [class*="avatar"],
[data-testid="stChatMessage"] [class*="Avatar"],
[data-testid="stChatMessage"] [class*="icon"],
[data-testid="stChatMessage"] [class*="Icon"] {
  background-color: #ffffff !important;
  background: #ffffff !important;
  border-radius: 8px !important;
  box-shadow: none !important;
}
/* Paksa semua elemen dalam stChatMessage tidak punya background gelap */
[data-testid="stChatMessage"] span[style*="background"],
[data-testid="stChatMessage"] div[style*="background-color: rgb(14"],
[data-testid="stChatMessage"] div[style*="background-color: rgb(38"],
[data-testid="stChatMessage"] div[style*="background-color: rgb(26"] {
  background-color: #ffffff !important;
  background: #ffffff !important;
}

/* Tombol Hapus Riwayat Chat — paksa light mode */
[data-testid="baseButton-secondary"],
button[kind="secondary"] {
  background-color: #f0f2f6 !important;
  color: #31333f !important;
  border: 1px solid #d0d3db !important;
  box-shadow: none !important;
}
[data-testid="baseButton-secondary"]:hover,
button[kind="secondary"]:hover {
  background-color: #e2e6ee !important;
  color: #1a1c23 !important;
  border-color: #b0b5c0 !important;
}

/* Alert / info box */
[data-testid="stAlert"][data-baseweb="notification"] {
  background-color: #e8f4fd !important;
  color: #1a4a6b !important;
}
[data-testid="stAlert"] * { color: inherit !important; }

/* Metric */
[data-testid="metric-container"] {
  background-color: #f8f9fa !important;
  border: 1px solid #e0e0e0 !important;
  border-radius: 8px !important;
}
[data-testid="stMetric"] * { color: #31333f !important; }

/* Expander */
[data-testid="stExpander"] {
  background-color: #f8f9fa !important;
  border: 1px solid #e0e0e0 !important;
}

/* Divider & caption */
hr { border-color: #e0e0e0 !important; }
[data-testid="stCaptionContainer"] { color: #666 !important; }

/* Button secondary */
[data-testid="baseButton-secondary"] {
  background-color: #f0f2f6 !important;
  color: #31333f !important;
  border-color: #cccccc !important;
}

/* Scrollbar */
::-webkit-scrollbar { width:6px; height:6px; }
::-webkit-scrollbar-track { background:#f0f2f6; }
::-webkit-scrollbar-thumb { background:#cccccc; border-radius:3px; }
</style>""", unsafe_allow_html=True)

# Daftar model yang direkomendasikan (Groq)
MODEL_OPTIONS = [
    "llama-3.3-70b-versatile",     # Terbaik & paling pintar
    "llama-3.1-8b-instant",        # Tercepat & paling hemat
    "gemma2-9b-it",                # Alternatif ringan dari Google
]

# BAGIAN 1: DETEKSI KOLOM & PARSING DATA

ALIAS_KOLOM = {
    "nama tugas":    "tugas", "nama tugas (simulasi)": "tugas",
    "tugas":         "tugas", "assignment": "tugas", "task": "tugas",
    "kerjaan":       "tugas", "pekerjaan":  "tugas", "kegiatan": "tugas",
    "mata kuliah":   "matkul","matkul":     "matkul","subject":  "matkul",
    "course":        "matkul","pelajaran":  "matkul","mapel":    "matkul",
    "kelas":         "matkul",
    "deadline":      "deadline","due date":  "deadline","due_date": "deadline",
    "batas waktu":   "deadline","tanggal akhir":"deadline",
    "tanggal deadline":"deadline","tgl deadline":"deadline",
    "jatuh tempo":   "deadline","akhir":     "deadline",
    "prioritas":     "prioritas","priority":  "prioritas",
    "estimasi waktu":"estimasi","estimasi":  "estimasi","durasi":  "estimasi",
    "estimated time":"estimasi","time":      "estimasi",
    "status":        "status",  "kondisi":   "status","state":   "status",
    "tanggal diberikan":"tgl_mulai","tanggal mulai":"tgl_mulai",
    "mulai":         "tgl_mulai","start":    "tgl_mulai",
}

BULAN_ID = {
    "januari":1,"februari":2,"maret":3,"april":4,"mei":5,"juni":6,
    "juli":7,"agustus":8,"september":9,"oktober":10,"november":11,"desember":12,
    "jan":1,"feb":2,"mar":3,"apr":4,"jun":6,"jul":7,"agu":8,"agt":8,
    "sep":9,"okt":10,"nov":11,"des":12,
    "january":1,"february":2,"march":3,"may":5,"june":6,"july":7,
    "august":8,"october":10,"december":12,
}

def deteksi_kolom(df: pd.DataFrame) -> dict:
    mapping = {}
    for col in df.columns:
        key = col.strip().lower()
        if key in ALIAS_KOLOM:
            internal = ALIAS_KOLOM[key]
            if internal not in mapping:
                mapping[internal] = col
    return mapping

def parse_tgl(s: str, tahun_default: int = None) -> "date | None":
    if tahun_default is None: tahun_default = date.today().year
    s = str(s).strip()
    parts = s.replace(",", " ").split()
    for i, p in enumerate(parts):
        bln = BULAN_ID.get(p.lower())
        if bln:
            others = [x for j, x in enumerate(parts) if j != i]
            for o in others:
                try:
                    hr = int(o)
                    thn = tahun_default
                    for o2 in others:
                        try:
                            yy = int(o2)
                            if 2020 <= yy <= 2035:
                                thn = yy; break
                        except: pass
                    return date(thn, bln, hr)
                except: pass
    try:
        r = pd.to_datetime(s, format="mixed", dayfirst=True, errors="raise")
        if r.year >= 2020: return r.date()
    except: pass
    iso_match = re.match(r"(\d{4}-\d{2}-\d{2})", s)
    if iso_match:
        try: return date.fromisoformat(iso_match.group(1))
        except: pass
    return None

def parse_jam(s) -> int:
    if pd.isna(s): return 2
    nums = re.findall(r'\d+', str(s))
    return int(nums[0]) if nums else 2

BOBOT_PRI = {"tinggi": 0, "high": 0, "kritis": 0, "sedang": 1, "medium": 1, "normal": 1, "rendah": 2, "low": 2, "ringan": 2}

def proses_df(df: pd.DataFrame, mapping: dict) -> pd.DataFrame:
    today = date.today()
    df = df.copy()
    if "deadline" in mapping:
        df["_deadline"] = df[mapping["deadline"]].apply(parse_tgl)
    else:
        df["_deadline"] = None

    df["_hari_tersisa"] = df["_deadline"].apply(lambda d: (d - today).days if d else 9999)
    df["_jam"] = df[mapping["estimasi"]].apply(parse_jam) if "estimasi" in mapping else 2

    if "prioritas" in mapping:
        df["_bobot_pri"] = df[mapping["prioritas"]].apply(lambda x: BOBOT_PRI.get(str(x).lower().strip(), 1))
        df["_prioritas"] = df[mapping["prioritas"]].apply(lambda x: str(x).strip())
    else:
        df["_bobot_pri"] = 1; df["_prioritas"] = "Sedang"

    df["_skor"] = df["_hari_tersisa"] + df["_bobot_pri"] * 2
    df["_tugas"]  = df[mapping["tugas"]].apply(str)  if "tugas"  in mapping else "Tugas"
    df["_matkul"] = df[mapping["matkul"]].apply(str) if "matkul" in mapping else "—"

    if "status" in mapping:
        selesai_kata = {"selesai","done","complete","completed","finished","sudah"}
        df["_selesai"] = df[mapping["status"]].apply(lambda x: str(x).lower().strip() in selesai_kata)
    else:
        df["_selesai"] = False

    return df

# BAGIAN 2: PYTHON → KALENDER, TABEL, JADWAL

def bangun_beban(df: pd.DataFrame) -> dict:
    beban = {}
    for _, r in df.iterrows():
        if r["_deadline"] is None: continue
        key = str(r["_deadline"])
        if key not in beban: beban[key] = {"jumlah": 0, "tugas": []}
        beban[key]["jumlah"] += 1
        beban[key]["tugas"].append({
            "tugas":       r["_tugas"], "matkul":      r["_matkul"],
            "deadline":    key, "prioritas":   r["_prioritas"],
            "estimasi_jam":r["_jam"], "status":      "Selesai" if r["_selesai"] else "Belum Selesai",
        })
    return beban

def bangun_tabel_prioritas(df: pd.DataFrame) -> pd.DataFrame:
    df_aktif = df[~df["_selesai"] & (df["_deadline"].notna())].copy()
    if df_aktif.empty: return pd.DataFrame()
    df_aktif = df_aktif.sort_values("_skor").reset_index(drop=True)
    df_aktif.index += 1

    def urgensi(hari):
        if hari < 0:     return "🔴 Terlambat"
        elif hari <= 2:  return "🔴 Kritis"
        elif hari <= 5:  return "🟠 Mendesak"
        elif hari <= 10: return "🟡 Perhatikan"
        else:            return "🟢 Aman"

    kolom = {}
    if "_tugas"  in df_aktif.columns: kolom["_tugas"]  = "Nama Tugas"
    if "_matkul" in df_aktif.columns: kolom["_matkul"] = "Mata Kuliah"

    df_out = pd.DataFrame()
    for k, v in kolom.items(): df_out[v] = df_aktif[k].values
    df_out["Deadline"]      = df_aktif["_deadline"].apply(lambda d: d.strftime("%d %b %Y") if d else "—").values
    df_out["Hari Tersisa"]  = df_aktif["_hari_tersisa"].apply(lambda h: h if h != 9999 else "?").values
    df_out["Prioritas"]     = df_aktif["_prioritas"].values
    df_out["Estimasi"]      = df_aktif["_jam"].apply(lambda j: f"{j} jam").values
    df_out["Urgensi"]       = df_aktif["_hari_tersisa"].apply(urgensi).values
    df_out.index = range(1, len(df_out) + 1)
    return df_out

def bangun_jadwal_harian(df: pd.DataFrame) -> pd.DataFrame:
    df_aktif = df[~df["_selesai"] & (df["_deadline"].notna())].sort_values("_skor").copy()
    if df_aktif.empty: return pd.DataFrame()

    today = date.today()
    jadwal = []
    hari = today

    for _, r in df_aktif.iterrows():
        dl = r["_deadline"]
        jam = r["_jam"]
        hari_tersisa = r["_hari_tersisa"]

        if hari_tersisa < 0:
            catatan = "⚠️ Deadline sudah terlewat! Selesaikan sesegera mungkin."
            tgl_kerjakan = today
        elif hari_tersisa == 0:
            catatan = "🚨 Deadline HARI INI! Prioritaskan sekarang."
            tgl_kerjakan = today
        elif hari_tersisa <= 2:
            catatan = f"🔴 Deadline {dl.strftime('%d %b')} — kerjakan sekarang!"
            tgl_kerjakan = hari
        else:
            catatan = f"Selesaikan sebelum {dl.strftime('%d %b %Y')}"
            tgl_kerjakan = hari
            hari += timedelta(days=1)

        jadwal.append({
            "Tanggal Kerjakan": tgl_kerjakan.strftime("%d %b %Y (%a)"),
            "Nama Tugas":       r["_tugas"], "Mata Kuliah":      r["_matkul"],
            "Prioritas":        r["_prioritas"], "Estimasi":         f"{jam} jam",
            "Deadline":         dl.strftime("%d %b %Y"), "Catatan":          catatan,
        })
    return pd.DataFrame(jadwal)


# BAGIAN 3: AI — HANYA UNTUK ANALISIS TEKS

def panggil_ai_analisis(csv_str: str, kolom_info: str, model: str) -> str:
    """ AI menganalisis teks dengan tambahan pemecahan tugas (fokus) via tag XML. """
    hari_ini = date.today().strftime("%d %B %Y")

    prompt = f"""Kamu adalah AI Asisten Akademik. Hari ini {hari_ini}.

Data tugas mahasiswa:
{csv_str}

Kolom data: {kolom_info}

Berikan analisis singkat dalam Bahasa Indonesia. Jawab HANYA dengan format berikut, tidak ada teks lain:

<skor>[angka 1-10, di mana 10=sangat berat]</skor>

<ringkasan>[2-3 kalimat analisis kondisi beban mahasiswa berdasarkan data di atas]</ringkasan>

<fokus>
Tugas paling berat/menantang dari data di atas adalah [Nama Tugas]. Mulailah mengerjakannya dengan 3 langkah kecil ini:
1. [Langkah pertama]
2. [Langkah kedua]
3. [Langkah ketiga]
</fokus>

<tips>
1. [tip konkret pertama]
2. [tip konkret kedua]
3. [tip konkret ketiga]
</tips>"""

    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY belum diset di Streamlit Secrets.")

    client = Groq(api_key=api_key)
    message = client.chat.completions.create(
        model=model,
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.choices[0].message.content


def parse_ai_teks(teks: str) -> dict:
    """Parse tag XML sederhana dari respons AI."""
    def ekstrak(tag):
        m = re.search(rf"<{tag}>(.*?)</{tag}>", teks, re.DOTALL | re.IGNORECASE)
        return m.group(1).strip() if m else ""

    skor_str = ekstrak("skor")
    try:
        skor = max(1, min(10, int(float(re.sub(r"[^\d.]", "", skor_str)))))
    except:
        skor = None

    return {
        "skor":      skor,
        "ringkasan": ekstrak("ringkasan"),
        "fokus":     ekstrak("fokus"),
        "tips":      ekstrak("tips"),
    }



# BAGIAN 4: CHATBOT ASISTEN AKADEMIK

def bangun_konteks_jadwal(df_jadwal: pd.DataFrame) -> str:
    """Ubah df_jadwal menjadi teks konteks yang ringkas untuk prompt chatbot."""
    if df_jadwal.empty:
        return "Tidak ada tugas aktif saat ini."
    baris = []
    for _, r in df_jadwal.iterrows():
        baris.append(
            f"- [{r.get('Tanggal Kerjakan','?')}] {r.get('Nama Tugas','?')} "
            f"({r.get('Mata Kuliah','—')}) | Deadline: {r.get('Deadline','?')} | "
            f"Estimasi: {r.get('Estimasi','?')} | Prioritas: {r.get('Prioritas','?')} | "
            f"{r.get('Catatan','')}"
        )
    return "\n".join(baris)


def panggil_chatbot(riwayat: list, pesan_baru: str, konteks_jadwal: str, model: str) -> str:
    """
    Kirim pesan ke Groq API dengan konteks jadwal sebagai sistem prompt.
    riwayat: list of dict {"role": "user"/"assistant", "content": "..."}
    """
    hari_ini = date.today().strftime("%A, %d %B %Y")
    system_prompt = f"""Kamu adalah Asisten Akademik bernama CogniPace. Hari ini {hari_ini}.

Kamu membantu mahasiswa memahami dan merencanakan jadwal belajar mereka.
Jawab dalam Bahasa Indonesia, singkat, ramah, dan to-the-point.
Jangan mengarang informasi di luar data jadwal yang diberikan.

=== DATA JADWAL MAHASISWA (Gunakan ini sebagai sumber kebenaran) ===
{konteks_jadwal}
=== AKHIR DATA ===

Gunakan data di atas untuk menjawab pertanyaan spesifik tentang tugas, deadline, dan prioritas.
Jika pertanyaan tidak berkaitan dengan data jadwal, jawab sesuai pengetahuan umummu tentang tips belajar."""

    api_key = st.secrets.get("GROQ_API_KEY", "")
    if not api_key:
        raise ValueError("GROQ_API_KEY belum diset di Streamlit Secrets.")

    client = Groq(api_key=api_key)
    messages = [{"role": "system", "content": system_prompt}]
    for msg in riwayat:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": pesan_baru})

    response = client.chat.completions.create(
        model=model,
        max_tokens=1000,
        messages=messages,
    )
    return response.choices[0].message.content


def tampilkan_chatbot(df_jadwal: pd.DataFrame, model: str):
    """Render UI chatbot interaktif di bawah dashboard."""
    st.subheader("💬 Chatbot Asisten Akademik")
    st.caption(
        "Tanya langsung tentang jadwalmu — "
        "contoh: *\"Tugas mana yang harus dikerjakan besok?\"* atau *\"Berapa total estimasi tugas minggu ini?\"*"
    )

    # Inisialisasi session state untuk riwayat chat
    if "chat_riwayat" not in st.session_state:
        st.session_state["chat_riwayat"] = []
    if "chat_konteks" not in st.session_state:
        st.session_state["chat_konteks"] = ""

    # Perbarui konteks jika df_jadwal berubah (simpan hash sederhana)
    konteks_baru = bangun_konteks_jadwal(df_jadwal)
    if st.session_state["chat_konteks"] != konteks_baru:
        st.session_state["chat_konteks"] = konteks_baru
        # Reset riwayat jika data berubah agar tidak bingung
        if st.session_state["chat_riwayat"]:
            st.session_state["chat_riwayat"] = []
            st.info("ℹ️ Data jadwal diperbarui. Riwayat chat direset.")

    # Tampilkan riwayat percakapan
    riwayat = st.session_state["chat_riwayat"]
    if riwayat:
        for msg in riwayat:
            with st.chat_message(msg["role"], avatar="🧑‍🎓" if msg["role"] == "user" else "🤖"):
                st.markdown(msg["content"])
    else:
        st.info("👋 Belum ada percakapan. Ketik pertanyaanmu di kotak di bawah!")

    # Input pengguna
    pesan_user = st.chat_input("Tanya tentang jadwal atau tipsmu…", key="chat_input")

    if pesan_user:
        if not AI_TERSEDIA:
            st.warning(
                "⚠️ Library `groq` tidak ditemukan. "
                "Jalankan `pip install groq` lalu restart aplikasi."
            )
            return

        # Tampilkan pesan user segera
        with st.chat_message("user", avatar="🧑‍🎓"):
            st.markdown(pesan_user)

        # Panggil AI
        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("CogniPace sedang berpikir…"):
                try:
                    jawaban = panggil_chatbot(
                        riwayat=riwayat,
                        pesan_baru=pesan_user,
                        konteks_jadwal=st.session_state["chat_konteks"],
                        model=model,
                    )
                    st.markdown(jawaban)
                    # Simpan ke riwayat
                    st.session_state["chat_riwayat"].append(
                        {"role": "user", "content": pesan_user}
                    )
                    st.session_state["chat_riwayat"].append(
                        {"role": "assistant", "content": jawaban}
                    )
                except Exception as e:
                    err_msg = str(e)
                    st.warning(
                        f"⚠️ Chatbot tidak bisa menjawab saat ini. "
                        f"Pastikan GROQ_API_KEY sudah diset di Streamlit Secrets. "
                        f"Detail: {err_msg[:120]}"
                    )

    # Tombol reset riwayat
    if riwayat:
        if st.button("🗑️ Hapus Riwayat Chat", use_container_width=False, key="reset_chat"):
            st.session_state["chat_riwayat"] = []
            st.rerun()


# BAGIAN 5: KALENDER HTML+JS INTERAKTIF

def render_kalender(beban_json: str, tahun_awal: int, bulan_awal: int) -> str:
    return f"""<!DOCTYPE html>
<html lang="id">
<head><meta charset="UTF-8">
<style>
:root{{
  --bg-body:transparent;
  --c-month:#1a1a2e;
  --c-hdr:#999;
  --c-legend:#666;
  --lb-border:rgba(0,0,0,.1);
  --cell-c0-bg:#f4f5f7;--cell-c0-fg:#aaa;--cell-c0-bd:transparent;
  --cell-c1-bg:#e8f4fd;--cell-c1-fg:#1a365d;--cell-c1-bd:#b3d9f5;
  --cell-c2-bg:#fffbeb;--cell-c2-fg:#744210;--cell-c2-bd:#fcd34d;
  --cell-c3-bg:#fff3e0;--cell-c3-fg:#6d3700;--cell-c3-bd:#fb923c;
  --cell-c4-bg:#ffe4e6;--cell-c4-fg:#7f1d1d;--cell-c4-bd:#f87171;
  --cell-c5-bg:#dc2626;--cell-c5-fg:#fff;--cell-c5-bd:#991b1b;
  --today-ring:#1976d2;
  --badge-bg:rgba(0,0,0,.12);
  --chip-bg:rgba(0,0,0,.07);
  --chip-pt:#e53935;--chip-ps:#ff9800;--chip-pr:#4caf50;
  --overlay-bg:rgba(0,0,0,.5);
  --modal-bg:#fff;--modal-bd:#e2e8f0;
  --m-date:#1a1a2e;--m-sub:#718096;
  --tcard-bg:#f8f9fa;--tcard-bd:#e2e8f0;
  --tc-name:#1a1a2e;--tc-row:#555;
  --pt-bg:#fde8e8;--pt-fg:#c62828;
  --ps-bg:#fff3e0;--ps-fg:#e65100;
  --pr-bg:#e8f5e9;--pr-fg:#2e7d32;
  --sdone-bg:#e8f5e9;--sdone-fg:#2e7d32;
  --stodo-bg:#fff3e0;--stodo-fg:#e65100;
  --btn-close-bg:#f0f2f5;--btn-close-fg:#333;--btn-close-hover:#e0e2e5;
  --leg-today-bg:#fff;
}}
html.dark{{
  --c-month:#e8eaf0;--c-hdr:#8899aa;--c-legend:#8899aa;
  --lb-border:rgba(255,255,255,.1);
  --cell-c0-bg:#1e2330;--cell-c0-fg:#4a5568;--cell-c0-bd:#2d3348;
  --cell-c1-bg:#0d2137;--cell-c1-fg:#90cdf4;--cell-c1-bd:#1a4a6e;
  --cell-c2-bg:#2a2000;--cell-c2-fg:#f6e05e;--cell-c2-bd:#6b5300;
  --cell-c3-bg:#2d1800;--cell-c3-fg:#fbd38d;--cell-c3-bd:#7c3a00;
  --cell-c4-bg:#2d1200;--cell-c4-fg:#fc8181;--cell-c4-bd:#922b00;
  --cell-c5-bg:#7b0d0d;--cell-c5-fg:#fff5f5;--cell-c5-bd:#c53030;
  --today-ring:#63b3ed;--badge-bg:rgba(255,255,255,.15);--chip-bg:rgba(255,255,255,.08);
  --chip-pt:#fc8181;--chip-ps:#f6ad55;--chip-pr:#68d391;
  --overlay-bg:rgba(0,0,0,.75);--modal-bg:#1a2035;--modal-bd:#2d3a52;
  --m-date:#e2e8f0;--m-sub:#718096;--tcard-bg:#242d42;--tcard-bd:#2d3a52;
  --tc-name:#e2e8f0;--tc-row:#a0aec0;--pt-bg:#3d1515;--pt-fg:#fc8181;
  --ps-bg:#3d2a00;--ps-fg:#f6ad55;--pr-bg:#0f2d1a;--pr-fg:#68d391;
  --sdone-bg:#0f2d1a;--sdone-fg:#68d391;--stodo-bg:#3d2a00;--stodo-fg:#f6ad55;
  --btn-close-bg:#2d3748;--btn-close-fg:#e2e8f0;--btn-close-hover:#3d4a60;
  --leg-today-bg:#1a2035;
}}
*{{box-sizing:border-box;margin:0;padding:0}}
body{{font-family:'Segoe UI',sans-serif;background:var(--bg-body);padding:6px 10px}}
.cal-nav{{display:flex;align-items:center;justify-content:space-between;margin-bottom:14px}}
.cal-nav button{{background:#4a90d9;color:#fff;border:none;border-radius:8px;padding:8px 20px;
  font-size:.95rem;cursor:pointer;transition:background .2s;font-weight:600}}
.cal-nav button:hover{{background:#2c6fad}}
.month-lbl{{font-size:1.35rem;font-weight:800;color:var(--c-month)}}
.cal-grid{{display:grid;grid-template-columns:repeat(7,1fr);gap:5px}}
.hdr{{text-align:center;font-size:.68rem;font-weight:700;color:var(--c-hdr);padding:5px 0;
  letter-spacing:.05em;text-transform:uppercase}}
.cell{{border-radius:10px;min-height:78px;padding:7px 6px;border:2px solid transparent;
  transition:transform .15s,box-shadow .15s;font-size:.7rem}}
.cell.click{{cursor:pointer}}
.cell.click:hover{{transform:translateY(-3px);box-shadow:0 6px 18px rgba(0,0,0,.3);
  border-color:#4a90d9!important;z-index:2}}
.cell.empty{{background:transparent}}
.cell.c0{{background:var(--cell-c0-bg);color:var(--cell-c0-fg);border-color:var(--cell-c0-bd)}}
.cell.c1{{background:var(--cell-c1-bg);color:var(--cell-c1-fg);border-color:var(--cell-c1-bd)}}
.cell.c2{{background:var(--cell-c2-bg);color:var(--cell-c2-fg);border-color:var(--cell-c2-bd)}}
.cell.c3{{background:var(--cell-c3-bg);color:var(--cell-c3-fg);border-color:var(--cell-c3-bd)}}
.cell.c4{{background:var(--cell-c4-bg);color:var(--cell-c4-fg);border-color:var(--cell-c4-bd)}}
.cell.c5{{background:var(--cell-c5-bg);color:var(--cell-c5-fg);border-color:var(--cell-c5-bd)}}
.cell.today{{outline:3px solid var(--today-ring);outline-offset:-2px}}
.cell.today .dn{{color:var(--today-ring);font-weight:900}}
.dn{{font-size:.9rem;font-weight:700;margin-bottom:4px;display:flex;
  justify-content:space-between;align-items:center}}
.badge{{background:var(--badge-bg);border-radius:20px;padding:1px 7px;font-size:.6rem;font-weight:800}}
.chip{{display:block;background:var(--chip-bg);border-radius:5px;padding:2px 5px;
  margin-top:3px;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;font-size:.62rem}}
.chip.pt{{border-left:3px solid var(--chip-pt)}}
.chip.ps{{border-left:3px solid var(--chip-ps)}}
.chip.pr{{border-left:3px solid var(--chip-pr)}}
.legend{{display:flex;gap:10px;justify-content:center;flex-wrap:wrap;
  margin-top:14px;font-size:.7rem;color:var(--c-legend)}}
.leg{{display:flex;align-items:center;gap:5px}}
.lb{{width:14px;height:14px;border-radius:4px;border:1px solid var(--lb-border);flex-shrink:0}}
/* Modal */
.overlay{{display:none;position:fixed;inset:0;background:var(--overlay-bg);
  z-index:1000;align-items:center;justify-content:center;padding:16px}}
.overlay.on{{display:flex}}
.modal{{background:var(--modal-bg);border:1px solid var(--modal-bd);border-radius:18px;padding:26px;
  max-width:500px;width:100%;max-height:82vh;overflow-y:auto;
  box-shadow:0 24px 64px rgba(0,0,0,.4);animation:up .22s ease}}
@keyframes up{{from{{transform:translateY(24px);opacity:0}}to{{transform:translateY(0);opacity:1}}}}
.m-date{{font-size:1.05rem;font-weight:800;color:var(--m-date);margin-bottom:3px}}
.m-sub{{font-size:.78rem;color:var(--m-sub);margin-bottom:16px}}
.tcard{{background:var(--tcard-bg);border:1px solid var(--tcard-bd);border-radius:11px;padding:13px 14px;margin-bottom:10px}}
.tc-name{{font-weight:700;font-size:.92rem;color:var(--tc-name);margin-bottom:6px}}
.tc-row{{display:flex;flex-wrap:wrap;gap:6px 14px;font-size:.76rem;color:var(--tc-row)}}
.tc-row span{{display:flex;align-items:center;gap:4px}}
.pbadge{{display:inline-block;padding:2px 10px;border-radius:20px;font-size:.66rem;font-weight:700;margin-top:7px}}
.pt{{background:var(--pt-bg);color:var(--pt-fg)}}
.ps{{background:var(--ps-bg);color:var(--ps-fg)}}
.pr{{background:var(--pr-bg);color:var(--pr-fg)}}
.sdone{{background:var(--sdone-bg);color:var(--sdone-fg);font-size:.66rem;font-weight:700;
  padding:2px 10px;border-radius:20px;display:inline-block;margin-top:7px;margin-left:6px}}
.stodo{{background:var(--stodo-bg);color:var(--stodo-fg);font-size:.66rem;font-weight:700;
  padding:2px 10px;border-radius:20px;display:inline-block;margin-top:7px;margin-left:6px}}
.btn-close{{width:100%;margin-top:16px;padding:11px;background:var(--btn-close-bg);
  border:1px solid var(--modal-bd);border-radius:9px;font-size:.88rem;cursor:pointer;
  color:var(--btn-close-fg);font-weight:600;transition:background .2s}}
.btn-close:hover{{background:var(--btn-close-hover)}}
</style></head>
<body>
<div class="cal-nav">
  <button onclick="nav(-1)">&#8592; Prev</button>
  <span class="month-lbl" id="lbl"></span>
  <button onclick="nav(1)">Next &#8594;</button>
</div>
<div class="cal-grid" id="grid"></div>
<div class="legend">
  <div class="leg"><div class="lb" style="background:var(--cell-c0-bg);border-color:var(--cell-c0-bd)"></div>Bebas</div>
  <div class="leg"><div class="lb" style="background:var(--cell-c1-bg);border-color:var(--cell-c1-bd)"></div>1</div>
  <div class="leg"><div class="lb" style="background:var(--cell-c2-bg);border-color:var(--cell-c2-bd)"></div>2</div>
  <div class="leg"><div class="lb" style="background:var(--cell-c3-bg);border-color:var(--cell-c3-bd)"></div>3</div>
  <div class="leg"><div class="lb" style="background:var(--cell-c4-bg);border-color:var(--cell-c4-bd)"></div>4</div>
  <div class="leg"><div class="lb" style="background:var(--cell-c5-bg)"></div>5+ 🚨</div>
  <div class="leg"><div class="lb" style="outline:3px solid var(--today-ring);background:var(--leg-today-bg)"></div>Hari ini</div>
</div>
<div class="overlay" id="ov" onclick="closeM(event)">
  <div class="modal">
    <div class="m-date" id="md"></div>
    <div class="m-sub"  id="ms"></div>
    <div id="mb"></div>
    <button class="btn-close" onclick="closeML()">✕ Tutup</button>
  </div>
</div>
<script>
const D={beban_json};
let Y={tahun_awal},M={bulan_awal};
const BLN=["Januari","Februari","Maret","April","Mei","Juni","Juli","Agustus","September","Oktober","November","Desember"];
const HPN=["Minggu","Senin","Selasa","Rabu","Kamis","Jumat","Sabtu"];
const BS=["Jan","Feb","Mar","Apr","Mei","Jun","Jul","Agu","Sep","Okt","Nov","Des"];
function pad(n){{return String(n).padStart(2,"0")}}
function key(y,m,d){{return y+"-"+pad(m)+"-"+pad(d)}}
function render(){{
  document.getElementById("lbl").textContent=BLN[M]+" "+Y;
  const g=document.getElementById("grid");g.innerHTML="";
  ["Sen","Sel","Rab","Kam","Jum","Sab","Min"].forEach(h=>{{
    const e=document.createElement("div");e.className="hdr";e.textContent=h;g.appendChild(e);
  }});
  const today=new Date();
  const fd=new Date(Y,M,1);
  const td=new Date(Y,M+1,0).getDate();
  const off=(fd.getDay()+6)%7;
  for(let i=0;i<off;i++){{const e=document.createElement("div");e.className="cell empty";g.appendChild(e);}}
  for(let d=1;d<=td;d++){{
    const k=key(Y,M+1,d);
    const info=D[k];const n=info?info.jumlah:0;
    let cls=n===0?"c0":n===1?"c1":n===2?"c2":n===3?"c3":n===4?"c4":"c5";
    const isTd=(d===today.getDate()&&M===today.getMonth()&&Y===today.getFullYear());
    const cell=document.createElement("div");
    cell.className="cell "+cls+(isTd?" today":"")+(n>0?" click":"");
    let badge=n>0?`<span class="badge">${{n}}</span>`:"";
    let chips="";
    if(info){{
      info.tugas.slice(0,2).forEach(t=>{{
        const nm=t.tugas.length>16?t.tugas.slice(0,16)+"…":t.tugas;
        const pc=(t.prioritas||"").toLowerCase().startsWith("t")?"pt":
                 (t.prioritas||"").toLowerCase().startsWith("r")?"pr":"ps";
        chips+=`<span class="chip ${{pc}}">📌 ${{nm}}</span>`;
      }});
      if(info.tugas.length>2)chips+=`<span class="chip">+${{info.tugas.length-2}} lagi…</span>`;
    }}
    cell.innerHTML=`<div class="dn"><span>${{d}}</span>${{badge}}</div>${{chips}}`;
    if(n>0)cell.addEventListener("click",()=>openM(k,info,d));
    g.appendChild(cell);
  }}
}}
function nav(dir){{M+=dir;if(M<0){{M=11;Y--;}}if(M>11){{M=0;Y++;}}render();}}
function openM(k,info,d){{
  const pts=k.split("-");const dt=new Date(+pts[0],+pts[1]-1,+pts[2]);
  document.getElementById("md").textContent=HPN[dt.getDay()]+", "+d+" "+BS[dt.getMonth()]+" "+dt.getFullYear();
  document.getElementById("ms").textContent=info.jumlah+" tugas deadline hari ini";
  let html="";
  info.tugas.forEach((t,i)=>{{
    const pc=(t.prioritas||"").toLowerCase().startsWith("t")?"pt":
             (t.prioritas||"").toLowerCase().startsWith("r")?"pr":"ps";
    const done=(t.status||"").toLowerCase().includes("selesai")||(t.status||"").toLowerCase().includes("done");
    html+=`<div class="tcard">
      <div class="tc-name">${{i+1}}. ${{t.tugas}}</div>
      <div class="tc-row">
        ${{t.matkul&&t.matkul!=="—"?`<span>📚 ${{t.matkul}}</span>`:""}}
        <span>📅 ${{t.deadline}}</span>
        <span>⏱️ ${{t.estimasi_jam}} jam</span>
      </div>
      <span class="pbadge ${{pc}}">🎯 ${{t.prioritas||"Sedang"}}</span>
      <span class="${{done?"sdone":"stodo"}}">${{done?"✅ Selesai":"⏳ Belum Selesai"}}</span>
    </div>`;
  }});
  document.getElementById("mb").innerHTML=html;
  document.getElementById("ov").classList.add("on");
}}
function closeM(e){{if(e.target===document.getElementById("ov"))closeML();}}
function closeML(){{document.getElementById("ov").classList.remove("on");}}
document.addEventListener("keydown",e=>{{if(e.key==="Escape")closeML();}});
function applyTheme(){{
  let dark=false;
  try{{
    const app=window.parent.document.querySelector('[data-testid="stApp"]');
    if(app){{const bg=window.parent.getComputedStyle(app).backgroundColor;
      dark=bg==="rgb(14, 17, 23)"||bg==="rgb(14,17,23)";}}
  }}catch(e){{dark=window.matchMedia("(prefers-color-scheme:dark)").matches;}}
  document.documentElement.classList.toggle("dark",dark);
}}
applyTheme();
setInterval(applyTheme,600);
render();
</script>
</body></html>"""


# TAMPILAN UTAMA

# ── Sidebar: pilih model ──────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Pengaturan AI")
    model_pilihan = st.selectbox(
        "Model Groq",
        options=MODEL_OPTIONS,
        index=0,
        help="llama3.1:8b paling bagus. phi3 paling ringan tapi sering gagal JSON.",
    )
    st.caption(
        """**Rekomendasi:**
- `llama-3.3-70b-versatile` — terbaik & pintar
- `llama-3.1-8b-instant` — tercepat & hemat
- `gemma2-9b-it` — alternatif ringan
```"""
    )
    st.divider()
    st.caption("🧠 CogniPace AI")

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🧠 CogniPace AI")
st.markdown(
    "**Asisten Manajemen Beban Kognitif Mahasiswa**  \n"
    "Upload CSV tugas → Python generate kalender & jadwal → AI berikan analisis & tips"
)
st.divider()

# ── Upload ────────────────────────────────────────────────────────────────────
st.subheader("📂 Upload Data Tugas")
st.caption(
    "Format CSV bebas — minimal kolom **nama tugas** dan **deadline**. "
    "Kolom lain (prioritas, estimasi waktu, matkul, status) opsional."
)
uploaded_file = st.file_uploader("Pilih file .csv", type=["csv"])

# JS fix: sembunyikan icon file & paksa tombol X selalu terlihat
components.html("""<script>
(function(){
  function fixFilePill(){
    try {
      var doc = window.parent.document;

      // 1. Paksa seluruh file pill jadi putih bersih
      var pills = doc.querySelectorAll('[data-testid="stFileUploaderFile"]');
      pills.forEach(function(pill){
        pill.style.setProperty('background-color','#ffffff','important');
        pill.style.setProperty('border','1px solid #d0d3db','important');
        pill.style.setProperty('border-radius','8px','important');
        pill.style.setProperty('box-shadow','none','important');
        pill.style.setProperty('color','#31333f','important');

        // 2. Sembunyikan child pertama (icon/logo thumbnail)
        var firstDiv = pill.querySelector('div > div:first-child');
        if(firstDiv){
          firstDiv.style.setProperty('display','none','important');
        }

        // 3. Paksa semua child lain jadi putih
        pill.querySelectorAll('*').forEach(function(c){
          var bg = window.parent.getComputedStyle(c).backgroundColor;
          var m = bg.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
          if(m && (+m[1]+ +m[2]+ +m[3]) < 200){
            c.style.setProperty('background-color','#ffffff','important');
          }
          c.style.setProperty('color','#31333f','important');
        });
      });

      // 4. Fix tombol X hapus file — selalu bulat, abu terang, ikon gelap
      var delBtns = doc.querySelectorAll('[data-testid="stFileUploaderDeleteBtn"]');
      delBtns.forEach(function(btn){
        btn.style.setProperty('background-color','#e2e6ee','important');
        btn.style.setProperty('border-radius','50%','important');
        btn.style.setProperty('border','1px solid #c0c5d0','important');
        btn.style.setProperty('opacity','1','important');
        btn.style.setProperty('visibility','visible','important');
        btn.style.setProperty('display','flex','important');
        btn.style.setProperty('width','24px','important');
        btn.style.setProperty('height','24px','important');
        btn.style.setProperty('min-width','24px','important');
        btn.style.setProperty('padding','0','important');
        btn.style.setProperty('box-shadow','none','important');
        btn.querySelectorAll('svg, path, rect').forEach(function(s){
          s.style.setProperty('fill','#31333f','important');
          s.style.setProperty('background','transparent','important');
        });
        // Hover effect
        btn.onmouseenter = function(){ this.style.setProperty('background-color','#f87171','important'); this.querySelectorAll('svg,path').forEach(function(s){s.style.setProperty('fill','#fff','important');}); };
        btn.onmouseleave = function(){ this.style.setProperty('background-color','#e2e6ee','important'); this.querySelectorAll('svg,path').forEach(function(s){s.style.setProperty('fill','#31333f','important');}); };
      });

    } catch(e){}
  }
  fixFilePill();
  setInterval(fixFilePill, 400);
  try {
    var obs = new MutationObserver(fixFilePill);
    obs.observe(window.parent.document.body, {childList:true, subtree:true});
  } catch(e){}
})();
</script>""", height=0)

if uploaded_file is not None:
    df_raw = pd.read_csv(uploaded_file)

    st.subheader("👀 Preview Data")
    # Render sebagai HTML tabel custom (light mode penuh, tidak pakai iframe)
    def render_preview_table(df: pd.DataFrame) -> str:
        cols = list(df.columns)
        header = "".join(f"<th>{c}</th>" for c in cols)
        rows = ""
        for i, (_, row) in enumerate(df.iterrows()):
            bg = "#ffffff" if i % 2 == 0 else "#f8f9fa"
            cells = "".join(f"<td>{row[c]}</td>" for c in cols)
            rows += f'<tr style="background:{bg}">{cells}</tr>'
        return f"""<style>
.prev-wrap{{overflow-x:auto;border-radius:10px;border:1px solid #e2e8f0;background:#fff;margin-bottom:8px}}
.prev-wrap table{{width:100%;border-collapse:collapse;font-size:.83rem;font-family:'Segoe UI',sans-serif}}
.prev-wrap thead tr{{background:#f7f8fa}}
.prev-wrap th{{padding:10px 12px;color:#4a5568;font-weight:600;font-size:.78rem;
  text-align:left;border-bottom:2px solid #e2e8f0;white-space:nowrap}}
.prev-wrap td{{padding:9px 12px;color:#2d3748;border-bottom:1px solid #edf2f7}}
.prev-wrap tr:last-child td{{border-bottom:none}}
.prev-wrap tr:hover td{{background:#eef2ff!important}}
</style>
<div class="prev-wrap"><table>
<thead><tr><th>#</th>{header}</tr></thead>
<tbody>{rows}</tbody>
</table></div>"""
    st.markdown(render_preview_table(df_raw), unsafe_allow_html=True)

    # Deteksi kolom
    mapping = deteksi_kolom(df_raw)
    kolom_display = " · ".join([f"**{k}** → `{v}`" for k, v in mapping.items()])
    if mapping:
        st.info(f"🔍 Kolom terdeteksi: {kolom_display}")
    else:
        st.warning("⚠️ Tidak ada kolom standar yang dikenali. Pastikan ada kolom deadline.")

    if "deadline" not in mapping:
        st.error("❌ Kolom **deadline** tidak ditemukan. Periksa nama kolom di CSV.")
        st.stop()

    df_proc = proses_df(df_raw, mapping)
    total_valid   = df_proc["_deadline"].notna().sum()
    total_aktif   = (~df_proc["_selesai"] & df_proc["_deadline"].notna()).sum()

    st.info(f"📊 {len(df_raw)} baris · {total_valid} dengan deadline valid · {total_aktif} belum selesai")
    st.divider()

    # ── Tombol ───────────────────────────────────────────────────────────────
    if st.button("🔍 Buat Kalender & Analisis AI", type="primary", use_container_width=True):

        # ── PROSES DATA (Python, selalu berhasil) ────────────────────────────
        beban_dict  = bangun_beban(df_proc)
        df_prio     = bangun_tabel_prioritas(df_proc)
        df_jadwal   = bangun_jadwal_harian(df_proc)

        # ── PANGGIL AI (opsional, hanya untuk teks) ──────────────────────────
        ai_hasil = {"skor": None, "ringkasan": "", "fokus": "", "tips": ""}
        ai_error = None

        if not AI_TERSEDIA:
            ai_error = "Library `groq` tidak ditemukan. `pip install groq`"
        else:
            with st.spinner(f"🤖 AI ({model_pilihan}) menganalisis... (~10-20 detik)"):
                try:
                    kolom_info = ", ".join([f'"{c}"' for c in df_raw.columns])
                    respons_ai = panggil_ai_analisis(
                        df_raw.to_csv(index=False), kolom_info, model_pilihan
                    )
                    ai_hasil = parse_ai_teks(respons_ai)
                    # Simpan raw untuk debug
                    st.session_state["ai_raw"] = respons_ai
                except Exception as e:
                    ai_error = str(e)
                    st.session_state["ai_raw"] = ""

        # ── SIMPAN HASIL KE SESSION STATE agar tetap tampil saat chat re-run ─
        st.session_state["hasil_analisis"] = {
            "beban_dict":  beban_dict,
            "df_prio":     df_prio,
            "df_jadwal":   df_jadwal,
            "ai_hasil":    ai_hasil,
            "ai_error":    ai_error,
            "total_aktif": total_aktif,
        }

        st.success("✅ Kalender & jadwal siap!")

    # OUTPUT — dibaca dari session_state agar tetap tampil saat chatbot re-run
    if "hasil_analisis" not in st.session_state:
        pass  # Belum ada analisis, tidak tampilkan apa-apa
    else:
        _h          = st.session_state["hasil_analisis"]
        beban_dict  = _h["beban_dict"]
        df_prio     = _h["df_prio"]
        df_jadwal   = _h["df_jadwal"]
        ai_hasil    = _h["ai_hasil"]
        ai_error    = _h["ai_error"]
        total_aktif = _h["total_aktif"]


        # OUTPUT (sebelumnya di dalam button, sekarang di luar)

        # ── Metrik ───────────────────────────────────────────────────────────
        total_padat = sum(1 for v in beban_dict.values() if v["jumlah"] >= 3)
        c1, c2, c3 = st.columns(3)
        with c1:
            skor = ai_hasil.get("skor")
            if skor:
                delta = "⚠️ Berat" if skor >= 7 else ("🟡 Sedang" if skor >= 4 else "🟢 Ringan")
                st.metric("🎯 Skor Beban (AI)", f"{skor} / 10", delta)
            else:
                st.metric("🎯 Skor Beban (AI)", "N/A", "AI offline" if ai_error else "—")
        with c2:
            st.metric("📋 Tugas Aktif", f"{total_aktif} tugas")
        with c3:
            st.metric("🔴 Hari Padat (3+ DL)", f"{total_padat} hari")

        # AI error notice (kecil, tidak blokir output)
        if ai_error:
            st.warning(
                f"⚠️ AI tidak tersedia ({ai_error[:80]}...). "
                "Kalender & jadwal tetap ditampilkan dari data CSV."
            )

        st.divider()

        # ── Kalender ─────────────────────────────────────────────────────────
        st.subheader("📅 Kalender Beban Tugas")
        st.caption(
            "Navigasi dengan **← Prev / Next →** · "
            "**Klik tanggal berwarna** → detail tugas, prioritas & estimasi"
        )

        if beban_dict:
            tgl0    = min(beban_dict.keys())
            thn_awal = int(tgl0[:4])
            bln_awal = int(tgl0[5:7]) - 1
        else:
            thn_awal = date.today().year
            bln_awal = date.today().month - 1

        beban_js = json.dumps(beban_dict, ensure_ascii=False)
        components.html(render_kalender(beban_js, thn_awal, bln_awal), height=540, scrolling=False)

        st.divider()

        # ── Tabel prioritas ───────────────────────────────────────────────────
        st.subheader("📋 Tabel Prioritas Pengerjaan Tugas")
        st.caption("Urutan: deadline terdekat + prioritas tertinggi → kerjakan dari baris paling atas")

        if not df_prio.empty:
            TABEL_STYLE = """<style>
:root{
  --t-border:#e2e8f0;--t-head-bg:#f7f8fa;--t-head-fg:#4a5568;
  --t-row-fg:#2d3748;--t-num-fg:#a0aec0;--t-row-hover:rgba(0,0,0,.03);
  --t-kritis-bg:#fff5f5;--t-kritis-fg:#c53030;
  --t-mendesak-bg:#fffaf0;--t-mendesak-fg:#c05621;
  --t-perhatikan-bg:#fffff0;--t-perhatikan-fg:#975a16;
  --t-aman-bg:#f0fff4;--t-aman-fg:#276749;
  --t-urgent-bg:#fff5f5;--t-urgent-fg:#c53030;
  --t-warning-bg:#fffaf0;--t-warning-fg:#c05621;
  --t-normal-fg:#4a5568;
}
.tbl-wrap.dark{
  --t-border:#2d3a52;--t-head-bg:#1a2035;--t-head-fg:#a0aec0;
  --t-row-fg:#c9d1d9;--t-num-fg:#4a5568;--t-row-hover:rgba(255,255,255,.03);
  --t-kritis-bg:#3d1515;--t-kritis-fg:#fc8181;
  --t-mendesak-bg:#3d2a00;--t-mendesak-fg:#f6ad55;
  --t-perhatikan-bg:#2a2d00;--t-perhatikan-fg:#f6e05e;
  --t-aman-bg:#0f2d1a;--t-aman-fg:#68d391;
  --t-urgent-bg:#3d1515;--t-urgent-fg:#fc8181;
  --t-warning-bg:#3d2a00;--t-warning-fg:#f6ad55;
  --t-normal-fg:#8899aa;
}
.tbl-wrap{overflow-x:auto;border-radius:10px;border:1px solid var(--t-border)}
table{width:100%;border-collapse:collapse;font-size:.85rem;font-family:'Segoe UI',sans-serif}
thead tr{background:var(--t-head-bg);color:var(--t-head-fg);text-align:left}
th{padding:10px 10px;white-space:nowrap;font-weight:600;font-size:.8rem}
td{padding:9px 10px;color:var(--t-row-fg)}
tr{border-top:1px solid var(--t-border)}
tr:hover td{background:var(--t-row-hover)}
.num{color:var(--t-num-fg);width:36px}
.kritis{background:var(--t-kritis-bg)}.kritis td{color:var(--t-kritis-fg)}
.mendesak{background:var(--t-mendesak-bg)}.mendesak td{color:var(--t-mendesak-fg)}
.perhatikan{background:var(--t-perhatikan-bg)}.perhatikan td{color:var(--t-perhatikan-fg)}
.aman{background:var(--t-aman-bg)}.aman td{color:var(--t-aman-fg)}
.urgent{background:var(--t-urgent-bg)}.urgent td{color:var(--t-urgent-fg)}
.warning{background:var(--t-warning-bg)}.warning td{color:var(--t-warning-fg)}
.normal td{color:var(--t-normal-fg)}
</style>
<script>
(function(){
  function applyTheme(){
    var app=document.querySelector('[data-testid="stApp"]');
    var dark=app&&getComputedStyle(app).backgroundColor==='rgb(14, 17, 23)';
    document.querySelectorAll('.tbl-wrap').forEach(function(w){
      w.classList.toggle('dark',!!dark);
    });
  }
  applyTheme();
  setInterval(applyTheme,600);
})();
</script>"""

            def kelas_prio(row):
                u = row.get("Urgensi","")
                if "Terlambat" in u or "Kritis" in u: return "kritis"
                elif "Mendesak" in u:                 return "mendesak"
                elif "Perhatikan" in u:               return "perhatikan"
                else:                                 return "aman"

            cols_p = list(df_prio.columns)
            header_p = "".join(f'<th>{c}</th>' for c in cols_p)
            rows_p = ""
            for idx, row in df_prio.iterrows():
                kls = kelas_prio(row)
                cells = "".join(f'<td>{row[c]}</td>' for c in cols_p)
                rows_p += f'<tr class="{kls}"><td class="num">{idx}</td>{cells}</tr>'
            html_prio = f"""{TABEL_STYLE}<div class="tbl-wrap"><table>
<thead><tr><th>#</th>{header_p}</tr></thead>
<tbody>{rows_p}</tbody></table></div>"""
            st.markdown(html_prio, unsafe_allow_html=True)
        else:
            st.success("🎉 Semua tugas sudah selesai!")

        st.divider()

        # ── Jadwal harian ─────────────────────────────────────────────────────
        st.subheader("🗓️ Rekomendasi Jadwal Harian")
        st.caption("Jadwal otomatis dari algoritma Python — 1 tugas per hari, diurutkan dari yang paling mendesak")

        if not df_jadwal.empty:
            def kelas_jadwal(row):
                c = row.get("Catatan","")
                if "Deadline HARI INI" in c or "terlewat" in c: return "urgent"
                elif "🔴" in c:                                   return "warning"
                else:                                             return "normal"

            cols_j = list(df_jadwal.columns)
            header_j = "".join(f'<th>{c}</th>' for c in cols_j)
            rows_j = ""
            for _, row in df_jadwal.iterrows():
                kls = kelas_jadwal(row)
                cells = "".join(f'<td>{row[c]}</td>' for c in cols_j)
                rows_j += f'<tr class="{kls}">{cells}</tr>'
            html_jadwal = f"""{TABEL_STYLE}<div class="tbl-wrap"><table>
<thead><tr>{header_j}</tr></thead>
<tbody>{rows_j}</tbody></table></div>"""
            st.markdown(html_jadwal, unsafe_allow_html=True)
        else:
            st.info("Tidak ada tugas aktif yang perlu dijadwalkan.")

        st.divider()

        # ── Analisis & Tips AI ────────────────────────────────────────────────
        st.subheader("💡 Analisis & Tips dari AI")

        ringkasan = ai_hasil.get("ringkasan","")
        fokus     = ai_hasil.get("fokus", "") # PERUBAHAN 3: Ambil nilai fokus
        tips      = ai_hasil.get("tips","")

        if ringkasan:
            st.info(f"📊 **Analisis Kondisi:** {ringkasan}")

        # Menampilkan Pemecahan Tugas (Micro-Stepping) dalam kotak sukses
        if fokus:
            st.success(f"🎯 **Pemecahan Tugas Terberat (Micro-Stepping):**\n\n{fokus}")

        if tips:
            st.markdown("**💡 Tips Manajemen Waktu:**")
            st.markdown(tips)

        if not ringkasan and not tips and not fokus:
            if ai_error:
                st.info(
                    "💡 AI tidak tersedia. Gunakan kalender dan tabel prioritas di atas "
                    "sebagai panduan pengerjaan tugas."
                )
            else:
                st.info("AI tidak memberikan analisis untuk data ini.")

        # Debug expander
        if st.session_state.get("ai_raw"):
            with st.expander("🛠️ Respons mentah AI (debug)"):
                st.text(st.session_state["ai_raw"])

        st.divider()

        # ── Chatbot Asisten Akademik ──────────────────────────────────────────
        # JS fix avatar via components.html (benar-benar dieksekusi, bukan disanitasi)
        components.html("""<script>
(function(){
  function fixAvatars(){
    try {
      var doc = window.parent.document;
      // Target semua elemen dalam stChatMessage
      var msgs = doc.querySelectorAll('[data-testid="stChatMessage"]');
      msgs.forEach(function(msg){
        // Ambil div pertama (posisi avatar)
        var wrapper = msg.querySelector('div > div:first-child');
        if(wrapper){
          wrapper.style.setProperty('background-color','#ffffff','important');
          wrapper.style.setProperty('background','#ffffff','important');
          wrapper.style.setProperty('border-radius','8px','important');
          wrapper.style.setProperty('box-shadow','none','important');
          wrapper.style.setProperty('border','1px solid #d0d5e0','important');
          // Semua child dari wrapper
          wrapper.querySelectorAll('*').forEach(function(el){
            var bg = window.parent.getComputedStyle(el).backgroundColor;
            // Jika background gelap (rgb rendah semua), paksa putih
            var m = bg.match(/rgb\((\d+),\s*(\d+),\s*(\d+)\)/);
            if(m && (+m[1]+m[2]+m[3]) < 150){
              el.style.setProperty('background-color','#ffffff','important');
              el.style.setProperty('background','#ffffff','important');
            }
            el.style.setProperty('border-radius','6px','important');
          });
        }
      });
      // Juga target by testid langsung
      ['chatAvatarIcon-user','chatAvatarIcon-assistant',
       'stChatMessageAvatarUser','stChatMessageAvatarAssistant'].forEach(function(id){
        doc.querySelectorAll('[data-testid="'+id+'"]').forEach(function(el){
          el.style.setProperty('background-color','#ffffff','important');
          el.style.setProperty('background','#ffffff','important');
          el.style.setProperty('border','1px solid #d0d5e0','important');
          el.style.setProperty('border-radius','8px','important');
          el.style.setProperty('box-shadow','none','important');
          el.querySelectorAll('*').forEach(function(c){
            c.style.setProperty('background-color','#ffffff','important');
            c.style.setProperty('background','#ffffff','important');
          });
        });
      });
    } catch(e){}
  }
  fixAvatars();
  setInterval(fixAvatars, 300);
  var obs = new MutationObserver(fixAvatars);
  try { obs.observe(window.parent.document.body,{childList:true,subtree:true}); } catch(e){}
})();
</script>""", height=0)
        tampilkan_chatbot(df_jadwal, model_pilihan)

# ── Footer ────────────────────────────────────────────────────────────────────
st.divider()
st.caption("🧠 CogniPace AI")
